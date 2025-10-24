from __future__ import annotations

from graphene import ObjectType

from .mutations.account import (
    InfrahubAccountSelfUpdate,
    InfrahubAccountTokenCreate,
    InfrahubAccountTokenDelete,
)
from .mutations.branch import (
    BranchCreate,
    BranchDelete,
    BranchMerge,
    BranchRebase,
    BranchUpdate,
    BranchValidate,
)
from .mutations.computed_attribute import UpdateComputedAttribute
from .mutations.convert_object_type import ConvertObjectType
from .mutations.diff import DiffUpdateMutation
from .mutations.diff_conflict import ResolveDiffConflict
from .mutations.generator import GeneratorDefinitionRequestRun
from .mutations.proposed_change import (
    ProposedChangeCheckForApprovalRevoke,
    ProposedChangeMerge,
    ProposedChangeRequestRunCheck,
    ProposedChangeReview,
)
from .mutations.relationship import RelationshipAdd, RelationshipRemove
from .mutations.repository import ProcessRepository, ValidateRepositoryConnectivity
from .mutations.resource_manager import IPAddressPoolGetResource, IPPrefixPoolGetResource
from .mutations.schema import SchemaDropdownAdd, SchemaDropdownRemove, SchemaEnumAdd, SchemaEnumRemove
from .queries import (
    AccountPermissions,
    AccountToken,
    BranchQueryList,
    DeprecatedIPAddressGetNextAvailable,
    DeprecatedIPPrefixGetNextAvailable,
    InfrahubInfo,
    InfrahubIPAddressGetNextAvailable,
    InfrahubIPPrefixGetNextAvailable,
    InfrahubResourcePoolAllocated,
    InfrahubResourcePoolUtilization,
    InfrahubSearchAnywhere,
    InfrahubStatus,
    ProposedChangeAvailableActions,
    Relationship,
)
from .queries.convert_object_type_mapping import FieldsMappingTypeConversion
from .queries.diff.tree import DiffTreeQuery, DiffTreeSummaryQuery
from .queries.event import Event
from .queries.task import Task, TaskBranchStatus


class InfrahubBaseQuery(ObjectType):
    Branch = BranchQueryList
    InfrahubAccountToken = AccountToken
    InfrahubPermissions = AccountPermissions

    DiffTree = DiffTreeQuery
    DiffTreeSummary = DiffTreeSummaryQuery

    Relationship = Relationship

    InfrahubInfo = InfrahubInfo
    InfrahubStatus = InfrahubStatus

    InfrahubSearchAnywhere = InfrahubSearchAnywhere

    InfrahubTask = Task
    InfrahubEvent = Event
    InfrahubTaskBranchStatus = TaskBranchStatus

    CoreProposedChangeAvailableActions = ProposedChangeAvailableActions

    IPAddressGetNextAvailable = DeprecatedIPAddressGetNextAvailable
    IPPrefixGetNextAvailable = DeprecatedIPPrefixGetNextAvailable
    InfrahubIPAddressGetNextAvailable = InfrahubIPAddressGetNextAvailable
    InfrahubIPPrefixGetNextAvailable = InfrahubIPPrefixGetNextAvailable
    InfrahubResourcePoolAllocated = InfrahubResourcePoolAllocated
    InfrahubResourcePoolUtilization = InfrahubResourcePoolUtilization

    FieldsMappingTypeConversion = FieldsMappingTypeConversion


class InfrahubBaseMutation(ObjectType):
    InfrahubAccountTokenCreate = InfrahubAccountTokenCreate.Field()
    InfrahubAccountSelfUpdate = InfrahubAccountSelfUpdate.Field()
    InfrahubAccountTokenDelete = InfrahubAccountTokenDelete.Field()
    CoreProposedChangeRunCheck = ProposedChangeRequestRunCheck.Field()
    CoreProposedChangeMerge = ProposedChangeMerge.Field()
    CoreProposedChangeReview = ProposedChangeReview.Field()
    CoreGeneratorDefinitionRun = GeneratorDefinitionRequestRun.Field()

    InfrahubIPPrefixPoolGetResource = IPPrefixPoolGetResource.Field()
    InfrahubIPAddressPoolGetResource = IPAddressPoolGetResource.Field()
    IPPrefixPoolGetResource = IPPrefixPoolGetResource.Field(
        deprecation_reason="This mutation has been renamed to 'InfrahubIPPrefixPoolGetResource'. It will be removed in the next version of Infrahub."
    )
    IPAddressPoolGetResource = IPAddressPoolGetResource.Field(
        deprecation_reason="This mutation has been renamed to 'InfrahubIPAddressPoolGetResource'. It will be removed in the next version of Infrahub."
    )

    BranchCreate = BranchCreate.Field()
    BranchDelete = BranchDelete.Field()
    BranchRebase = BranchRebase.Field()
    BranchMerge = BranchMerge.Field()
    BranchUpdate = BranchUpdate.Field()
    BranchValidate = BranchValidate.Field()

    DiffUpdate = DiffUpdateMutation.Field()

    InfrahubRepositoryProcess = ProcessRepository.Field()
    InfrahubRepositoryConnectivity = ValidateRepositoryConnectivity.Field()
    InfrahubUpdateComputedAttribute = UpdateComputedAttribute.Field()

    RelationshipAdd = RelationshipAdd.Field()
    RelationshipRemove = RelationshipRemove.Field()
    SchemaDropdownAdd = SchemaDropdownAdd.Field()
    SchemaDropdownRemove = SchemaDropdownRemove.Field()
    SchemaEnumAdd = SchemaEnumAdd.Field()
    SchemaEnumRemove = SchemaEnumRemove.Field()
    ResolveDiffConflict = ResolveDiffConflict.Field()

    ConvertObjectType = ConvertObjectType.Field()
    CoreProposedChangeCheckForApprovalRevoke = ProposedChangeCheckForApprovalRevoke.Field()
