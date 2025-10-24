from __future__ import annotations

import importlib
import logging
import os
from collections import defaultdict
from csv import DictReader, DictWriter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

import typer
import ujson
from infrahub_sdk.async_typer import AsyncTyper
from prefect.testing.utilities import prefect_test_harness
from rich import print as rprint
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from infrahub import config
from infrahub.core import registry
from infrahub.core.graph import GRAPH_VERSION
from infrahub.core.graph.constraints import ConstraintManagerBase, ConstraintManagerMemgraph, ConstraintManagerNeo4j
from infrahub.core.graph.index import node_indexes, rel_indexes
from infrahub.core.graph.schema import (
    GRAPH_SCHEMA,
    GraphAttributeProperties,
    GraphNodeProperties,
    GraphRelationshipDefault,
    GraphRelationshipIsPartOf,
    GraphRelationshipProperties,
)
from infrahub.core.initialization import (
    first_time_initialization,
    get_root_node,
    initialization,
    initialize_registry,
)
from infrahub.core.migrations.graph import get_graph_migrations, get_migration_by_number
from infrahub.core.migrations.schema.models import SchemaApplyMigrationData
from infrahub.core.migrations.schema.tasks import schema_apply_migrations
from infrahub.core.schema import SchemaRoot, core_models, internal_schema
from infrahub.core.schema.definitions.deprecated import deprecated_models
from infrahub.core.schema.manager import SchemaManager
from infrahub.core.utils import delete_all_nodes
from infrahub.core.validators.models.validate_migration import SchemaValidateMigrationData
from infrahub.core.validators.tasks import schema_validate_migrations
from infrahub.database import DatabaseType
from infrahub.database.memgraph import IndexManagerMemgraph
from infrahub.database.neo4j import IndexManagerNeo4j
from infrahub.log import get_logger

from .constants import ERROR_BADGE, FAILED_BADGE, SUCCESS_BADGE
from .db_commands.check_inheritance import check_inheritance
from .db_commands.clean_duplicate_schema_fields import clean_duplicate_schema_fields
from .patch import patch_app


def get_timestamp_string() -> str:
    """Generate a timestamp string in the format YYYYMMDD-HHMMSS."""
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")


if TYPE_CHECKING:
    from infrahub.cli.context import CliContext
    from infrahub.core.migrations.shared import ArbitraryMigration, GraphMigration, InternalSchemaMigration
    from infrahub.database import InfrahubDatabase
    from infrahub.database.index import IndexManagerBase

app = AsyncTyper()
app.add_typer(patch_app, name="patch")

PERMISSIONS_AVAILABLE = ["read", "write", "admin"]


class ConstraintAction(str, Enum):
    SHOW = "show"
    ADD = "add"
    DROP = "drop"


class IndexAction(str, Enum):
    SHOW = "show"
    ADD = "add"
    DROP = "drop"


@app.callback()
def callback() -> None:
    """
    Manage the graph in the database.
    """


@app.command()
async def init(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "infrahub.toml", envvar="INFRAHUB_CONFIG", help="Location of the configuration file to use for Infrahub"
    ),
) -> None:
    """Erase the content of the database and initialize it with the core schema."""

    log = get_logger()

    # --------------------------------------------------
    # CLEANUP
    #  - For now we delete everything in the database
    #   TODO, if possible try to implement this in an idempotent way
    # --------------------------------------------------

    logging.getLogger("neo4j").setLevel(logging.ERROR)
    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)
    async with dbdriver.start_transaction() as db:
        log.info("Delete All Nodes")
        await delete_all_nodes(db=db)
        await first_time_initialization(db=db)

    await dbdriver.close()


@app.command()
async def load_test_data(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "infrahub.toml", envvar="INFRAHUB_CONFIG", help="Location of the configuration file to use for Infrahub"
    ),
    dataset: str = "dataset01",
) -> None:
    """Load test data into the database from the `test_data` directory."""

    logging.getLogger("neo4j").setLevel(logging.ERROR)
    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    async with dbdriver.start_session() as db:
        await initialization(db=db)

        log_level = "DEBUG"

        FORMAT = "%(message)s"
        logging.basicConfig(level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
        logging.getLogger("infrahub")

        dataset_module = importlib.import_module(f"infrahub.test_data.{dataset}")
        await dataset_module.load_data(db=db)

    await dbdriver.close()


@app.command(name="migrate")
async def migrate_cmd(
    ctx: typer.Context,
    check: bool = typer.Option(False, help="Check the state of the database without applying the migrations."),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
    migration_number: int | None = typer.Option(None, help="Apply a specific migration by number"),
) -> None:
    """Check the current format of the internal graph and apply the necessary migrations"""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    await migrate_database(db=dbdriver, initialize=True, check=check, migration_number=migration_number)

    await dbdriver.close()


@app.command(name="check-inheritance")
async def check_inheritance_cmd(
    ctx: typer.Context,
    fix: bool = typer.Option(False, help="Fix the inheritance of any invalid nodes."),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Check the database for any vertices with incorrect inheritance"""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)
    await initialize_registry(db=dbdriver)

    success = await check_inheritance(db=dbdriver, fix=fix)
    if not success:
        raise typer.Exit(code=1)

    await dbdriver.close()


@app.command(name="check-duplicate-schema-fields")
async def check_duplicate_schema_fields_cmd(
    ctx: typer.Context,
    fix: bool = typer.Option(False, help="Fix the duplicate schema fields on the default branch."),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Check for any duplicate schema attributes or relationships on the default branch"""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    success = await clean_duplicate_schema_fields(db=dbdriver, fix=fix)
    if not success:
        raise typer.Exit(code=1)

    await dbdriver.close()


@app.command(name="update-core-schema")
async def update_core_schema_cmd(
    ctx: typer.Context,
    debug: bool = typer.Option(False, help="Enable advanced logging and troubleshooting"),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Check the current format of the internal graph and apply the necessary migrations"""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)
    os.environ["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    with prefect_test_harness():
        await update_core_schema(db=dbdriver, initialize=True, debug=debug)

    await dbdriver.close()


@app.command()
async def constraint(
    ctx: typer.Context,
    action: ConstraintAction = typer.Argument(ConstraintAction.SHOW),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Manage Database Constraints"""
    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    manager: ConstraintManagerBase | None = None
    if dbdriver.db_type == DatabaseType.NEO4J:
        manager = ConstraintManagerNeo4j.from_graph_schema(db=dbdriver, schema=GRAPH_SCHEMA)
    elif dbdriver.db_type == DatabaseType.MEMGRAPH:
        manager = ConstraintManagerMemgraph.from_graph_schema(db=dbdriver, schema=GRAPH_SCHEMA)
    else:
        print(f"Database type not supported : {dbdriver.db_type}")
        raise typer.Exit(1)

    if action == ConstraintAction.ADD:
        await manager.add()
    elif action == ConstraintAction.DROP:
        await manager.drop()

    constraints = await manager.list()

    console = Console()

    table = Table(title="Database Constraints")

    table.add_column("Name", justify="right", style="cyan", no_wrap=True)
    table.add_column("Label")
    table.add_column("Property")

    for item in constraints:
        table.add_row(item.item_name, item.item_label, item.property)

    console.print(table)

    await dbdriver.close()


@app.command()
async def index(
    ctx: typer.Context,
    action: IndexAction = typer.Argument(IndexAction.SHOW),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Manage Database Indexes"""
    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)
    if dbdriver.db_type is DatabaseType.MEMGRAPH:
        index_manager: IndexManagerBase = IndexManagerMemgraph(db=dbdriver)
    index_manager = IndexManagerNeo4j(db=dbdriver)

    index_manager.init(nodes=node_indexes, rels=rel_indexes)

    if action == IndexAction.ADD:
        await index_manager.add()
    elif action == IndexAction.DROP:
        await index_manager.drop()

    indexes = await index_manager.list()

    console = Console()

    table = Table(title="Database Indexes")

    table.add_column("Name", justify="right", style="cyan", no_wrap=True)
    table.add_column("Label")
    table.add_column("Property")
    table.add_column("Type")
    table.add_column("Entity Type")

    for item in indexes:
        table.add_row(
            item.name, item.label, ", ".join(item.properties), item.type.value.upper(), item.entity_type.value.upper()
        )

    console.print(table)

    await dbdriver.close()


async def migrate_database(
    db: InfrahubDatabase, initialize: bool = False, check: bool = False, migration_number: int | str | None = None
) -> bool:
    """Apply the latest migrations to the database, this function will print the status directly in the console.

    Returns a boolean indicating whether a migration failed or if all migrations succeeded.

    Args:
        db: The database object.
        check: If True, the function will only check the status of the database and not apply the migrations. Defaults to False.
        migration_number: If provided, the function will only apply the migration with the given number. Defaults to None.
    """
    rprint("Checking current state of the Database")

    if initialize:
        await initialize_registry(db=db)

    root_node = await get_root_node(db=db)
    if migration_number:
        migration = get_migration_by_number(migration_number)
        migrations: Sequence[GraphMigration | InternalSchemaMigration | ArbitraryMigration] = [migration]
        if check:
            if root_node.graph_version > migration.minimum_version:
                rprint(
                    f"Migration {migration_number} already applied. To apply again, run the command without the --check flag."
                )
                return True
            rprint(
                f"Migration {migration_number} needs to be applied. Run `infrahub db migrate` to apply all outstanding migrations."
            )
            return False
    else:
        migrations = await get_graph_migrations(root=root_node)
        if not migrations:
            rprint(f"Database up-to-date (v{root_node.graph_version}), no migration to execute.")
            return True

        rprint(
            f"Database needs to be updated (v{root_node.graph_version} -> v{GRAPH_VERSION}), {len(migrations)} migrations pending"
        )

    if check:
        return True

    for migration in migrations:
        execution_result = await migration.execute(db=db)
        validation_result = None

        if execution_result.success:
            validation_result = await migration.validate_migration(db=db)
            if validation_result.success:
                rprint(f"Migration: {migration.name} {SUCCESS_BADGE}")
                root_node.graph_version = migration.minimum_version + 1
                await root_node.save(db=db)

        if not execution_result.success or (validation_result and not validation_result.success):
            rprint(f"Migration: {migration.name} {FAILED_BADGE}")
            for error in execution_result.errors:
                rprint(f"  {error}")
            if validation_result and not validation_result.success:
                for error in validation_result.errors:
                    rprint(f"  {error}")
            return False

    return True


async def initialize_internal_schema() -> None:
    registry.schema = SchemaManager()
    schema = SchemaRoot(**internal_schema)
    registry.schema.register_schema(schema=schema)


async def update_core_schema(db: InfrahubDatabase, initialize: bool = True, debug: bool = False) -> None:
    """Update the core schema of Infrahub to the latest version"""
    # ----------------------------------------------------------
    # Initialize Schema and Registry
    # ----------------------------------------------------------
    if initialize:
        await initialize_registry(db=db)
        await initialize_internal_schema()

    default_branch = registry.get_branch_from_registry(branch=registry.default_branch)

    # ----------------------------------------------------------
    # Load Current Schema from the database
    # ----------------------------------------------------------
    schema_default_branch = await registry.schema.load_schema_from_db(db=db, branch=default_branch)
    registry.schema.set_schema_branch(name=default_branch.name, schema=schema_default_branch)
    branch_schema = registry.schema.get_schema_branch(name=registry.default_branch)

    candidate_schema = branch_schema.duplicate()
    candidate_schema.load_schema(schema=SchemaRoot(**internal_schema))
    candidate_schema.load_schema(schema=SchemaRoot(**core_models))
    candidate_schema.load_schema(schema=SchemaRoot(**deprecated_models))
    candidate_schema.process()

    schema_diff = branch_schema.diff(other=candidate_schema)
    branch_schema.validate_node_deletions(diff=schema_diff)
    result = branch_schema.validate_update(other=candidate_schema, diff=schema_diff, enforce_update_support=False)
    if result.errors:
        rprint(f"{ERROR_BADGE} | Unable to update the schema, due to failed validations")
        for error in result.errors:
            rprint(error.to_string())
        raise typer.Exit(1)

    if not result.diff.all:
        rprint("Core Schema Up to date, nothing to update")
        return

    rprint("Core Schema has diff, will need to be updated")
    if debug:
        result.diff.print()

    # ----------------------------------------------------------
    # Validate if the new schema is valid with the content of the database
    # ----------------------------------------------------------
    validate_migration_data = SchemaValidateMigrationData(
        branch=default_branch,
        schema_branch=candidate_schema,
        constraints=result.constraints,
    )
    responses = await schema_validate_migrations(message=validate_migration_data)
    error_messages = [violation.message for response in responses for violation in response.violations]
    if error_messages:
        rprint(f"{ERROR_BADGE} | Unable to update the schema, due to failed validations")
        for message in error_messages:
            rprint(message)
        raise typer.Exit(1)

    # ----------------------------------------------------------
    # Update the schema
    # ----------------------------------------------------------
    origin_schema = branch_schema.duplicate()

    # Update the internal schema
    schema_default_branch.load_schema(schema=SchemaRoot(**internal_schema))
    schema_default_branch.process()
    registry.schema.set_schema_branch(name=default_branch.name, schema=schema_default_branch)

    async with db.start_transaction() as dbt:
        await registry.schema.update_schema_branch(
            schema=candidate_schema,
            db=dbt,
            branch=default_branch.name,
            diff=result.diff,
            limit=result.diff.all,
            update_db=True,
        )
        default_branch.update_schema_hash()
        rprint("The Core Schema has been updated, make sure to rebase any open branches after the upgrade")
        if debug:
            rprint(f"New schema hash: {default_branch.active_schema_hash.main}")
        await default_branch.save(db=dbt)

    # ----------------------------------------------------------
    # Run the migrations
    # ----------------------------------------------------------
    apply_migration_data = SchemaApplyMigrationData(
        branch=default_branch,
        new_schema=candidate_schema,
        previous_schema=origin_schema,
        migrations=result.migrations,
    )
    migration_error_msgs = await schema_apply_migrations(message=apply_migration_data)

    if migration_error_msgs:
        rprint(f"{ERROR_BADGE} | Some error(s) happened while running the schema migrations")
        for message in migration_error_msgs:
            rprint(message)
        raise typer.Exit(1)


@app.command(name="selected-export")
async def selected_export_cmd(
    ctx: typer.Context,
    kinds: list[str] = typer.Option([], help="Node kinds to export"),  # noqa: B008
    uuids: list[str] = typer.Option([], help="UUIDs of nodes to export"),  # noqa: B008
    query_limit: int = typer.Option(1000, help="Maximum batch size of export query"),
    export_dir: Path = typer.Option(Path("infrahub-exports"), help="Path of directory to save exports"),  # noqa: B008
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """Export database structure of selected nodes from the database without any actual data"""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    await selected_export(db=dbdriver, kinds=kinds, uuids=uuids, export_dir=export_dir, query_limit=query_limit)

    await dbdriver.close()


async def selected_export(
    db: InfrahubDatabase,
    kinds: list[str],
    uuids: list[str],
    export_dir: Path,
    query_limit: int = 1000,
) -> Path:
    query = """
// --------------
// filter nodes
// --------------
MATCH (n:Node)
WHERE ($kinds IS NULL OR size($kinds) = 0 OR any(l IN labels(n) WHERE l in $kinds))
AND ($uuids IS NULL OR size($uuids) = 0 OR n.uuid IN $uuids)
WITH n
// --------------
// pagination
// --------------
ORDER BY %(id_func)s(n)
SKIP toInteger($offset)
LIMIT toInteger($limit)
CALL (n) {
    // --------------
    // get all the nodes and edges linked to this node up to 2 steps away, excluding IS_PART_OF
    // --------------
    MATCH (n)-[r1]-(v1)-[r2]-(v2)
    WHERE type(r1) <> "IS_PART_OF"
    WITH collect([v1, v2]) AS vertex_pairs, collect([r1, r2]) AS edge_pairs
    WITH reduce(
        vertices = [], v_pair IN vertex_pairs |
        CASE
            WHEN NOT v_pair[0] IN vertices AND NOT v_pair[1] IN vertices THEN vertices + v_pair
            WHEN NOT v_pair[0] IN vertices THEN vertices + [v_pair[0]]
            WHEN NOT v_pair[1] IN vertices THEN vertices + [v_pair[1]]
            ELSE vertices
        END
    ) AS vertices,
    reduce(
        edges = [], e_pair IN edge_pairs |
        CASE
            WHEN NOT e_pair[0] IN edges AND NOT e_pair[1] IN edges THEN edges + e_pair
            WHEN NOT e_pair[0] IN edges THEN edges + [e_pair[0]]
            WHEN NOT e_pair[1] IN edges THEN edges + [e_pair[1]]
            ELSE edges
        END
    ) AS edges
    RETURN vertices, edges
}
// --------------
// include the root and IS_PART_OF edges
// --------------
OPTIONAL MATCH (n)-[root_edge:IS_PART_OF]->(root:Root)
WITH n, vertices, edges, root, collect(root_edge) AS root_edges
WITH n, edges + root_edges AS edges, CASE
    WHEN root IS NOT NULL THEN vertices + [n, root]
    ELSE vertices + [n]
END AS vertices
RETURN vertices, edges
    """ % {"id_func": db.get_id_function_name()}
    timestamp_str = get_timestamp_string()
    export_dir /= Path(f"export-{timestamp_str}")
    if not export_dir.exists():
        export_dir.mkdir(parents=True)
    vertex_path = export_dir / Path("vertices.csv")
    vertex_path.touch(exist_ok=True)
    edge_path = export_dir / Path("edges.csv")
    edge_path.touch(exist_ok=True)

    graph_node_schemas = [GraphNodeProperties, GraphRelationshipProperties, GraphAttributeProperties]
    graph_vertex_properties = set()
    for graph_schema in graph_node_schemas:
        for field_name, field_info in graph_schema.model_fields.items():
            property_name = field_info.alias or field_name
            graph_vertex_properties.add(property_name)

    graph_edge_schemas = [GraphRelationshipIsPartOf, GraphRelationshipDefault]
    graph_edge_properties = set()
    for graph_schema in graph_edge_schemas:
        for field_name, field_info in graph_schema.model_fields.items():
            property_name = field_info.alias or field_name
            graph_edge_properties.add(property_name)

    all_db_ids: set[str] = set()
    has_more_data = True
    limit = query_limit
    offset = 0

    with vertex_path.open(mode="w") as vertex_file, edge_path.open(mode="w") as edge_file:
        vertex_field_names = ["db_id", "labels"] + sorted(graph_vertex_properties)
        vertex_csv_writer = DictWriter(vertex_file, fieldnames=vertex_field_names)
        vertex_csv_writer.writeheader()
        edge_field_names = ["db_id", "edge_type", "start_node_id", "end_node_id"] + sorted(graph_edge_properties)
        edge_csv_writer = DictWriter(edge_file, fieldnames=edge_field_names)
        edge_csv_writer.writeheader()

        while has_more_data:
            rprint("Retrieving batch of vertices and edges...", end="")
            results = await db.execute_query(
                query=query,
                params={"kinds": kinds, "uuids": uuids, "limit": limit, "offset": offset},
            )
            rprint("done. ", end="")
            has_more_data = len(results) >= limit
            offset += limit

            rprint("Writing batch to export files...", end="")
            for result in results:
                vertices = result.get("vertices")
                for vertex in vertices:
                    if vertex.element_id in all_db_ids:
                        continue
                    serial_vertex = {
                        "db_id": vertex.element_id,
                        "labels": ujson.dumps(list(vertex.labels)),
                    }
                    for property_name in graph_vertex_properties:
                        if value := vertex.get(property_name):
                            serial_vertex[property_name] = value
                    vertex_csv_writer.writerow(serial_vertex)
                    all_db_ids.add(vertex.element_id)

                edges = result.get("edges")
                for edge in edges:
                    if edge.element_id in all_db_ids:
                        continue
                    serial_edge = {
                        "db_id": edge.element_id,
                        "edge_type": edge.type,
                        "start_node_id": edge.start_node.element_id,
                        "end_node_id": edge.end_node.element_id,
                    }
                    for property_name in graph_edge_properties:
                        if value := edge.get(property_name):
                            serial_edge[property_name] = value
                    edge_csv_writer.writerow(serial_edge)
                    all_db_ids.add(edge.element_id)
            rprint("done.")

    rprint(f"{SUCCESS_BADGE} Export complete")
    rprint(f"Export directory is here: {export_dir.absolute()}")
    return export_dir


@app.command(name="load-export", hidden=True)
async def load_export_cmd(
    ctx: typer.Context,
    export_dir: Path = typer.Argument(help="Path to export directory"),
    query_limit: int = typer.Option(1000, help="Maximum batch size of import query"),
    config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG"),
) -> None:
    """
    Cannot be used for backup/restore functionality.
    Loads an anonymized export into Neo4j.
    Only used for analysis of output of the selected-export command.
    """
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    await load_export(db=dbdriver, export_dir=export_dir, query_limit=query_limit)

    await dbdriver.close()


async def load_vertices(
    db: InfrahubDatabase, vertex_labels: list[str], vertex_dicts: list[dict[str, str | int | bool | None]]
) -> None:
    vertex_import_query = """
UNWIND $vertices AS vertex
CREATE (v:ImportNode:%(node_labels)s {db_id: vertex.db_id})
SET v = vertex
    """ % {"node_labels": ":".join(vertex_labels)}
    rprint(f"Loading {len(vertex_dicts)} {vertex_labels} nodes...", end="")
    await db.execute_query(query=vertex_import_query, params={"vertices": vertex_dicts})
    rprint("done")


async def load_edges(
    db: InfrahubDatabase, edge_type: str, edge_dicts: list[dict[str, str | int | bool | None]]
) -> None:
    edges_import_query = """
UNWIND $edges AS edge
MATCH (a:ImportNode) WHERE a.db_id = toString(edge.start_node_id)
MATCH (b:ImportNode) WHERE b.db_id = toString(edge.end_node_id)
CREATE (a)-[e:%(edge_type)s]->(b)
SET e = edge.properties
    """ % {"edge_type": edge_type}
    rprint(f"Loading {len(edge_dicts)} {edge_type} edges...", end="")
    await db.execute_query(query=edges_import_query, params={"edges": edge_dicts})
    rprint("done")


async def load_export(db: InfrahubDatabase, export_dir: Path, query_limit: int = 1000) -> None:
    if not export_dir.exists():
        rprint(f"{ERROR_BADGE} {export_dir} does not exist")
        raise typer.Exit(1)
    if not export_dir.is_dir():
        rprint(f"{ERROR_BADGE} {export_dir} is not a directory")
        raise typer.Exit(1)
    vertex_file: Path | None = None
    edge_file: Path | None = None

    for export_file in export_dir.glob("*.csv"):
        if export_file.name == "vertices.csv":
            vertex_file = export_file
        elif export_file.name == "edges.csv":
            edge_file = export_file
    if not vertex_file or not vertex_file.exists() or not vertex_file.is_file():
        rprint(f"{ERROR_BADGE} File 'vertices.csv' does not exist in the export directory")
        raise typer.Exit(1)
    if not edge_file or not edge_file.exists() or not edge_file.is_file():
        rprint(f"{ERROR_BADGE} File 'edges.csv' does not exist in the export directory")
        raise typer.Exit(1)

    # index massively improves time required to load a large export
    create_index_query = "CREATE RANGE INDEX import_node_db_id IF NOT EXISTS FOR (v:ImportNode) ON (v.db_id)"
    await db.execute_query(query=create_index_query)

    rprint("Loading vertices...")
    vertices_by_labels_map: dict[frozenset[str], list[dict[str, Any]]] = defaultdict(list)
    with vertex_file.open() as file:
        csv_reader = DictReader(file)
        for vertex_row in csv_reader:
            labels = frozenset(ujson.loads(vertex_row["labels"]))
            cleaned_row = {k: v for k, v in vertex_row.items() if k != "labels" and v}
            vertices_by_labels_map[labels].append(cleaned_row)
            # once a group of vertices meets the query_limit, save them to the database and delete them from memory
            if len(vertices_by_labels_map[labels]) >= query_limit:
                await load_vertices(db=db, vertex_labels=list(labels), vertex_dicts=vertices_by_labels_map[labels])
                vertices_by_labels_map[labels] = []

        for labels, vertex_rows in vertices_by_labels_map.items():
            await load_vertices(db=db, vertex_labels=list(labels), vertex_dicts=vertex_rows)
    rprint("Vertices loaded")

    rprint("Loading edges...")
    edges_by_type_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with edge_file.open() as file:
        csv_reader = DictReader(file)
        for edge_row in csv_reader:
            edge_type = edge_row["edge_type"]

            edge_properties = {}
            edge_dict = {}
            for k, v in edge_row.items():
                if k == "edge_type" or not v:
                    continue
                if k in ["start_node_id", "end_node_id"]:
                    edge_dict[k] = v
                else:
                    edge_properties[k] = v
            edge_dict["properties"] = edge_properties
            edges_by_type_map[edge_type].append(edge_dict)
            # once a group of edges meets the query_limit, save them to the database and delete them from memory
            if len(edges_by_type_map[edge_type]) >= query_limit:
                await load_edges(db=db, edge_type=edge_type, edge_dicts=edges_by_type_map[edge_type])
                edges_by_type_map[edge_type] = []

        for edge_type, edge_dicts in edges_by_type_map.items():
            await load_edges(db=db, edge_type=edge_type, edge_dicts=edge_dicts)
    rprint("Edges loaded")
    rprint(f"{SUCCESS_BADGE} Export loaded")


@app.command(name="check")
async def check_cmd(
    ctx: typer.Context,
    output_dir: Path = typer.Option(  # noqa: B008
        None, help="Directory to save detailed check results (defaults to infrahub_db_check_YYYYMMDD-HHMMSS)"
    ),
    config_file: str = typer.Option(
        "infrahub.toml", envvar="INFRAHUB_CONFIG", help="Location of the configuration file to use for Infrahub"
    ),
) -> None:
    """Run database sanity checks and output the results to the CSV files."""
    logging.getLogger("infrahub").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    logging.getLogger("prefect").setLevel(logging.ERROR)

    config.load_and_exit(config_file_name=config_file)

    # Create output directory if not specified
    if output_dir is None:
        timestamp_str = get_timestamp_string()
        output_dir = Path(f"infrahub_db_check_{timestamp_str}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    context: CliContext = ctx.obj
    dbdriver = await context.init_db(retry=1)

    await run_database_checks(db=dbdriver, output_dir=output_dir)

    await dbdriver.close()


async def run_database_checks(db: InfrahubDatabase, output_dir: Path) -> None:
    """Run a series of database health checks and output the results to the terminal.

    Args:
        db: The database object.
        output_dir: Directory to save detailed check results.
    """
    rprint("Running database health checks...")

    # Check 1: Duplicate active relationships
    rprint("\n[bold cyan]Check 1: Duplicate Active Relationships[/bold cyan]")
    duplicate_active_rels_query = """
    MATCH (a:Node)-[e1:IS_RELATED {status: "active"}]-(r:Relationship)-[e2:IS_RELATED {branch: e1.branch, status: "active"}]-(b:Node)
    WHERE a.uuid < b.uuid
    AND e1.to IS NULL
    AND e2.to IS NULL
    WITH DISTINCT a.uuid AS a_uuid,
        b.uuid AS b_uuid,
        r.name AS r_name,
        e1.branch AS branch,
        CASE
        WHEN startNode(e1) = a AND startNode(e2) = r THEN "out"
            WHEN startNode(e1) = r AND startNode(e2) = b THEN "in"
            ELSE "bidir"
        END AS direction,
        count(*) AS num_paths,
        collect(DISTINCT a.kind) AS a_kinds,
        collect(DISTINCT b.kind) AS b_kinds
    WHERE num_paths > 1
    RETURN a_uuid, a_kinds, b_uuid, b_kinds, r_name, branch, direction, num_paths
    """

    results = await db.execute_query(query=duplicate_active_rels_query)
    if results:
        rprint(f"[red]Found {len(results)} duplicate active relationships[/red]")
        # Write detailed results to file
        output_file = output_dir / "duplicate_active_relationships.csv"
        with output_file.open(mode="w", newline="") as f:
            writer = DictWriter(
                f, fieldnames=["a_uuid", "a_kinds", "b_uuid", "b_kinds", "r_name", "branch", "direction", "num_paths"]
            )
            writer.writeheader()
            for result in results:
                writer.writerow(dict(result))
        rprint(f"  Detailed results written to: {output_file}")
    else:
        rprint(f"{SUCCESS_BADGE} No duplicate active relationships found")

    # Check 2: Duplicated relationship nodes
    rprint("\n[bold cyan]Check 2: Duplicated Relationship Nodes[/bold cyan]")
    duplicate_rel_nodes_query = """
    MATCH (r:Relationship)
    WITH r.uuid AS r_uuid, COUNT(*) AS num_rels
    WHERE num_rels > 1
    MATCH (n:Node)-[:IS_RELATED]-(r:Relationship {uuid: r_uuid})
    WITH DISTINCT r_uuid, n.uuid AS n_uuid, n.kind AS n_kind
    WITH r_uuid, collect([n_uuid, n_kind]) AS node_details
    RETURN r_uuid, node_details
    """

    results = await db.execute_query(query=duplicate_rel_nodes_query)
    if results:
        rprint(f"[red]Found {len(results)} duplicated relationship nodes[/red]")
        # Write detailed results to file
        output_file = output_dir / "duplicated_relationship_nodes.csv"
        with output_file.open(mode="w", newline="") as f:
            writer = DictWriter(f, fieldnames=["r_uuid", "node_details"])
            writer.writeheader()
            for result in results:
                writer.writerow(dict(result))
        rprint(f"  Detailed results written to: {output_file}")
    else:
        rprint(f"{SUCCESS_BADGE} No duplicated relationship nodes found")

    # Check 3: Duplicated edges
    rprint("\n[bold cyan]Check 3: Duplicated Edges[/bold cyan]")
    duplicate_edges_query = """
    MATCH (a)
    CALL (a) {
        MATCH (a)-[e]->(b)
        WHERE elementId(a) < elementId(b)
        WITH DISTINCT a, b, type(e) AS e_type, count(*) AS total_num_edges
        WHERE total_num_edges > 1
        MATCH (a)-[e]->(b)
        WHERE type(e) = e_type
        WITH
            elementId(a) AS a_id,
            labels(a) AS a_labels,
            elementId(b) AS b_id,
            labels(b) AS b_labels,
            type(e) AS e_type,
            e.branch AS branch,
            e.status AS status,
            e.from AS time,
            collect(e) AS edges
        WITH a_id, a_labels, b_id, b_labels, e_type, branch, status, time, size(edges) AS num_edges
        WHERE num_edges > 1
        WITH a_id, a_labels, b_id, b_labels, e_type, branch, status, time, num_edges
        RETURN a_id, a_labels, b_id, b_labels, e_type, branch, status, time, num_edges
    }
    RETURN a_id, a_labels, b_id, b_labels, e_type, branch, status, time, num_edges
    """

    results = await db.execute_query(query=duplicate_edges_query)
    if results:
        rprint(f"[red]Found {len(results)} sets of duplicated edges[/red]")
        # Write detailed results to file
        output_file = output_dir / "duplicated_edges.csv"
        with output_file.open(mode="w", newline="") as f:
            writer = DictWriter(
                f,
                fieldnames=["a_id", "a_labels", "b_id", "b_labels", "e_type", "branch", "status", "time", "num_edges"],
            )
            writer.writeheader()
            for result in results:
                writer.writerow(dict(result))
        rprint(f"  Detailed results written to: {output_file}")
    else:
        rprint(f"{SUCCESS_BADGE} No duplicated edges found")

    # Check 4: Orphaned Relationships
    rprint("\n[bold cyan]Check 4: Orphaned Relationships[/bold cyan]")
    orphaned_rels_query = """
    MATCH (r:Relationship)-[:IS_RELATED]-(peer:Node)
    WITH DISTINCT r, peer
    WITH r, count(*) AS num_peers
    WHERE num_peers < 2
    MATCH (r)-[e:IS_RELATED]-(peer:Node)
    RETURN DISTINCT
        r.name AS r_name,
        e.branch AS branch,
        e.status AS status,
        e.from AS from_time,
        e.to AS to_time,
        peer.uuid AS peer_uuid,
        peer.kind AS peer_kind
    """
    results = await db.execute_query(query=orphaned_rels_query)
    if results:
        rprint(f"[red]Found {len(results)} orphaned Relationships[/red]")
        # Write detailed results to file
        output_file = output_dir / "orphaned_relationships.csv"
        with output_file.open(mode="w", newline="") as f:
            writer = DictWriter(
                f,
                fieldnames=["r_name", "branch", "status", "from_time", "to_time", "peer_uuid", "peer_kind"],
            )
            writer.writeheader()
            for result in results:
                writer.writerow(dict(result))
        rprint(f"  Detailed results written to: {output_file}")
    else:
        rprint(f"{SUCCESS_BADGE} No orphaned relationships found")

    rprint(f"\n{SUCCESS_BADGE} Database health checks completed")
    rprint(f"Detailed results saved to: {output_dir.absolute()}")
