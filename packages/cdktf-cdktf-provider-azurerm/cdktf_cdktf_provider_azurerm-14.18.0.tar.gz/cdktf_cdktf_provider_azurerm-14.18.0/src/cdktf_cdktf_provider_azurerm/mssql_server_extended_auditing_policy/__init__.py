r'''
# `azurerm_mssql_server_extended_auditing_policy`

Refer to the Terraform Registry for docs: [`azurerm_mssql_server_extended_auditing_policy`](https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy).
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from .._jsii import *

import cdktf as _cdktf_9a9027ec
import constructs as _constructs_77d1e7e8


class MssqlServerExtendedAuditingPolicy(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-azurerm.mssqlServerExtendedAuditingPolicy.MssqlServerExtendedAuditingPolicy",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy azurerm_mssql_server_extended_auditing_policy}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        server_id: builtins.str,
        audit_actions_and_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
        enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        id: typing.Optional[builtins.str] = None,
        log_monitoring_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        predicate_expression: typing.Optional[builtins.str] = None,
        retention_in_days: typing.Optional[jsii.Number] = None,
        storage_account_access_key: typing.Optional[builtins.str] = None,
        storage_account_access_key_is_secondary: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        storage_account_subscription_id: typing.Optional[builtins.str] = None,
        storage_endpoint: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["MssqlServerExtendedAuditingPolicyTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy azurerm_mssql_server_extended_auditing_policy} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param server_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#server_id MssqlServerExtendedAuditingPolicy#server_id}.
        :param audit_actions_and_groups: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#audit_actions_and_groups MssqlServerExtendedAuditingPolicy#audit_actions_and_groups}.
        :param enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#enabled MssqlServerExtendedAuditingPolicy#enabled}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#id MssqlServerExtendedAuditingPolicy#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param log_monitoring_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#log_monitoring_enabled MssqlServerExtendedAuditingPolicy#log_monitoring_enabled}.
        :param predicate_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#predicate_expression MssqlServerExtendedAuditingPolicy#predicate_expression}.
        :param retention_in_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#retention_in_days MssqlServerExtendedAuditingPolicy#retention_in_days}.
        :param storage_account_access_key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key MssqlServerExtendedAuditingPolicy#storage_account_access_key}.
        :param storage_account_access_key_is_secondary: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key_is_secondary MssqlServerExtendedAuditingPolicy#storage_account_access_key_is_secondary}.
        :param storage_account_subscription_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_subscription_id MssqlServerExtendedAuditingPolicy#storage_account_subscription_id}.
        :param storage_endpoint: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_endpoint MssqlServerExtendedAuditingPolicy#storage_endpoint}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#timeouts MssqlServerExtendedAuditingPolicy#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5233d0c2502193a1135c4531241d4eae5ede0736cabdcd443742415f09f3c0dc)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = MssqlServerExtendedAuditingPolicyConfig(
            server_id=server_id,
            audit_actions_and_groups=audit_actions_and_groups,
            enabled=enabled,
            id=id,
            log_monitoring_enabled=log_monitoring_enabled,
            predicate_expression=predicate_expression,
            retention_in_days=retention_in_days,
            storage_account_access_key=storage_account_access_key,
            storage_account_access_key_is_secondary=storage_account_access_key_is_secondary,
            storage_account_subscription_id=storage_account_subscription_id,
            storage_endpoint=storage_endpoint,
            timeouts=timeouts,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id_, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a MssqlServerExtendedAuditingPolicy resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the MssqlServerExtendedAuditingPolicy to import.
        :param import_from_id: The id of the existing MssqlServerExtendedAuditingPolicy that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the MssqlServerExtendedAuditingPolicy to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f6ca402bdf5abac42acc97965f05c05803983ad729a9007ca31840493ce0a8e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#create MssqlServerExtendedAuditingPolicy#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#delete MssqlServerExtendedAuditingPolicy#delete}.
        :param read: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#read MssqlServerExtendedAuditingPolicy#read}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#update MssqlServerExtendedAuditingPolicy#update}.
        '''
        value = MssqlServerExtendedAuditingPolicyTimeouts(
            create=create, delete=delete, read=read, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetAuditActionsAndGroups")
    def reset_audit_actions_and_groups(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuditActionsAndGroups", []))

    @jsii.member(jsii_name="resetEnabled")
    def reset_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnabled", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetLogMonitoringEnabled")
    def reset_log_monitoring_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLogMonitoringEnabled", []))

    @jsii.member(jsii_name="resetPredicateExpression")
    def reset_predicate_expression(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPredicateExpression", []))

    @jsii.member(jsii_name="resetRetentionInDays")
    def reset_retention_in_days(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetentionInDays", []))

    @jsii.member(jsii_name="resetStorageAccountAccessKey")
    def reset_storage_account_access_key(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStorageAccountAccessKey", []))

    @jsii.member(jsii_name="resetStorageAccountAccessKeyIsSecondary")
    def reset_storage_account_access_key_is_secondary(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStorageAccountAccessKeyIsSecondary", []))

    @jsii.member(jsii_name="resetStorageAccountSubscriptionId")
    def reset_storage_account_subscription_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStorageAccountSubscriptionId", []))

    @jsii.member(jsii_name="resetStorageEndpoint")
    def reset_storage_endpoint(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStorageEndpoint", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> "MssqlServerExtendedAuditingPolicyTimeoutsOutputReference":
        return typing.cast("MssqlServerExtendedAuditingPolicyTimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="auditActionsAndGroupsInput")
    def audit_actions_and_groups_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "auditActionsAndGroupsInput"))

    @builtins.property
    @jsii.member(jsii_name="enabledInput")
    def enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enabledInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="logMonitoringEnabledInput")
    def log_monitoring_enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "logMonitoringEnabledInput"))

    @builtins.property
    @jsii.member(jsii_name="predicateExpressionInput")
    def predicate_expression_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "predicateExpressionInput"))

    @builtins.property
    @jsii.member(jsii_name="retentionInDaysInput")
    def retention_in_days_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "retentionInDaysInput"))

    @builtins.property
    @jsii.member(jsii_name="serverIdInput")
    def server_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serverIdInput"))

    @builtins.property
    @jsii.member(jsii_name="storageAccountAccessKeyInput")
    def storage_account_access_key_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "storageAccountAccessKeyInput"))

    @builtins.property
    @jsii.member(jsii_name="storageAccountAccessKeyIsSecondaryInput")
    def storage_account_access_key_is_secondary_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "storageAccountAccessKeyIsSecondaryInput"))

    @builtins.property
    @jsii.member(jsii_name="storageAccountSubscriptionIdInput")
    def storage_account_subscription_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "storageAccountSubscriptionIdInput"))

    @builtins.property
    @jsii.member(jsii_name="storageEndpointInput")
    def storage_endpoint_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "storageEndpointInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "MssqlServerExtendedAuditingPolicyTimeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "MssqlServerExtendedAuditingPolicyTimeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="auditActionsAndGroups")
    def audit_actions_and_groups(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "auditActionsAndGroups"))

    @audit_actions_and_groups.setter
    def audit_actions_and_groups(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48d7bb272fecb47f2ba01c6318d625d4f8c6f6a9fb668456444b713c39982914)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "auditActionsAndGroups", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="enabled")
    def enabled(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "enabled"))

    @enabled.setter
    def enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__63592a51ec22fed84c8ec5f7671a4ba30451014d3c87751b3694f01aa1a529f7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dacaa2254215fb9a1aeb73c25838312779ce8e8dec911f400ca88f40b5011886)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="logMonitoringEnabled")
    def log_monitoring_enabled(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "logMonitoringEnabled"))

    @log_monitoring_enabled.setter
    def log_monitoring_enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__08652d5504944021d52ef21cf5479a82404fee043b26033bf6ce3048e18e3c63)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "logMonitoringEnabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="predicateExpression")
    def predicate_expression(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "predicateExpression"))

    @predicate_expression.setter
    def predicate_expression(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4d862a5d4914cc877200f0f34a633cffba4d8b06758e0049ad2eb0e116bd029f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "predicateExpression", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="retentionInDays")
    def retention_in_days(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "retentionInDays"))

    @retention_in_days.setter
    def retention_in_days(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa23a902cf892e3f201046e25eaa0001458c22388d94a6e378e86833c75dc6f0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "retentionInDays", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serverId")
    def server_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serverId"))

    @server_id.setter
    def server_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d81142e6be42e1388b22bb544ef19e128386dec905ca0ad40c85c179c34f1152)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serverId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageAccountAccessKey")
    def storage_account_access_key(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "storageAccountAccessKey"))

    @storage_account_access_key.setter
    def storage_account_access_key(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__34e36ea132530055aaa962c8dfab8ff625195e7df2d46a4f65b050a01b156ba5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageAccountAccessKey", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageAccountAccessKeyIsSecondary")
    def storage_account_access_key_is_secondary(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "storageAccountAccessKeyIsSecondary"))

    @storage_account_access_key_is_secondary.setter
    def storage_account_access_key_is_secondary(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cfcaec73716643d259f9fffc0a86bc03830bc293c0a4369bacfb29065607c6a5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageAccountAccessKeyIsSecondary", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageAccountSubscriptionId")
    def storage_account_subscription_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "storageAccountSubscriptionId"))

    @storage_account_subscription_id.setter
    def storage_account_subscription_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a5bf6925aa4e78cd11766c16d155f0b637d01f54195bc4c6cd478a644cd6db43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageAccountSubscriptionId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageEndpoint")
    def storage_endpoint(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "storageEndpoint"))

    @storage_endpoint.setter
    def storage_endpoint(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8699d22e91129cde2a84950bbe8f2de3ae58be109e25619a62814629e94a41b8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageEndpoint", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-azurerm.mssqlServerExtendedAuditingPolicy.MssqlServerExtendedAuditingPolicyConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "server_id": "serverId",
        "audit_actions_and_groups": "auditActionsAndGroups",
        "enabled": "enabled",
        "id": "id",
        "log_monitoring_enabled": "logMonitoringEnabled",
        "predicate_expression": "predicateExpression",
        "retention_in_days": "retentionInDays",
        "storage_account_access_key": "storageAccountAccessKey",
        "storage_account_access_key_is_secondary": "storageAccountAccessKeyIsSecondary",
        "storage_account_subscription_id": "storageAccountSubscriptionId",
        "storage_endpoint": "storageEndpoint",
        "timeouts": "timeouts",
    },
)
class MssqlServerExtendedAuditingPolicyConfig(_cdktf_9a9027ec.TerraformMetaArguments):
    def __init__(
        self,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
        server_id: builtins.str,
        audit_actions_and_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
        enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        id: typing.Optional[builtins.str] = None,
        log_monitoring_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        predicate_expression: typing.Optional[builtins.str] = None,
        retention_in_days: typing.Optional[jsii.Number] = None,
        storage_account_access_key: typing.Optional[builtins.str] = None,
        storage_account_access_key_is_secondary: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        storage_account_subscription_id: typing.Optional[builtins.str] = None,
        storage_endpoint: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["MssqlServerExtendedAuditingPolicyTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param server_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#server_id MssqlServerExtendedAuditingPolicy#server_id}.
        :param audit_actions_and_groups: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#audit_actions_and_groups MssqlServerExtendedAuditingPolicy#audit_actions_and_groups}.
        :param enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#enabled MssqlServerExtendedAuditingPolicy#enabled}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#id MssqlServerExtendedAuditingPolicy#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param log_monitoring_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#log_monitoring_enabled MssqlServerExtendedAuditingPolicy#log_monitoring_enabled}.
        :param predicate_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#predicate_expression MssqlServerExtendedAuditingPolicy#predicate_expression}.
        :param retention_in_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#retention_in_days MssqlServerExtendedAuditingPolicy#retention_in_days}.
        :param storage_account_access_key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key MssqlServerExtendedAuditingPolicy#storage_account_access_key}.
        :param storage_account_access_key_is_secondary: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key_is_secondary MssqlServerExtendedAuditingPolicy#storage_account_access_key_is_secondary}.
        :param storage_account_subscription_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_subscription_id MssqlServerExtendedAuditingPolicy#storage_account_subscription_id}.
        :param storage_endpoint: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_endpoint MssqlServerExtendedAuditingPolicy#storage_endpoint}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#timeouts MssqlServerExtendedAuditingPolicy#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(timeouts, dict):
            timeouts = MssqlServerExtendedAuditingPolicyTimeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__019c8e4b644db6612589915da8a22bef4aad30ddc7dcfeaab7e70a3106064cb7)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument server_id", value=server_id, expected_type=type_hints["server_id"])
            check_type(argname="argument audit_actions_and_groups", value=audit_actions_and_groups, expected_type=type_hints["audit_actions_and_groups"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument log_monitoring_enabled", value=log_monitoring_enabled, expected_type=type_hints["log_monitoring_enabled"])
            check_type(argname="argument predicate_expression", value=predicate_expression, expected_type=type_hints["predicate_expression"])
            check_type(argname="argument retention_in_days", value=retention_in_days, expected_type=type_hints["retention_in_days"])
            check_type(argname="argument storage_account_access_key", value=storage_account_access_key, expected_type=type_hints["storage_account_access_key"])
            check_type(argname="argument storage_account_access_key_is_secondary", value=storage_account_access_key_is_secondary, expected_type=type_hints["storage_account_access_key_is_secondary"])
            check_type(argname="argument storage_account_subscription_id", value=storage_account_subscription_id, expected_type=type_hints["storage_account_subscription_id"])
            check_type(argname="argument storage_endpoint", value=storage_endpoint, expected_type=type_hints["storage_endpoint"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "server_id": server_id,
        }
        if connection is not None:
            self._values["connection"] = connection
        if count is not None:
            self._values["count"] = count
        if depends_on is not None:
            self._values["depends_on"] = depends_on
        if for_each is not None:
            self._values["for_each"] = for_each
        if lifecycle is not None:
            self._values["lifecycle"] = lifecycle
        if provider is not None:
            self._values["provider"] = provider
        if provisioners is not None:
            self._values["provisioners"] = provisioners
        if audit_actions_and_groups is not None:
            self._values["audit_actions_and_groups"] = audit_actions_and_groups
        if enabled is not None:
            self._values["enabled"] = enabled
        if id is not None:
            self._values["id"] = id
        if log_monitoring_enabled is not None:
            self._values["log_monitoring_enabled"] = log_monitoring_enabled
        if predicate_expression is not None:
            self._values["predicate_expression"] = predicate_expression
        if retention_in_days is not None:
            self._values["retention_in_days"] = retention_in_days
        if storage_account_access_key is not None:
            self._values["storage_account_access_key"] = storage_account_access_key
        if storage_account_access_key_is_secondary is not None:
            self._values["storage_account_access_key_is_secondary"] = storage_account_access_key_is_secondary
        if storage_account_subscription_id is not None:
            self._values["storage_account_subscription_id"] = storage_account_subscription_id
        if storage_endpoint is not None:
            self._values["storage_endpoint"] = storage_endpoint
        if timeouts is not None:
            self._values["timeouts"] = timeouts

    @builtins.property
    def connection(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("connection")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]], result)

    @builtins.property
    def count(
        self,
    ) -> typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("count")
        return typing.cast(typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]], result)

    @builtins.property
    def depends_on(
        self,
    ) -> typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("depends_on")
        return typing.cast(typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]], result)

    @builtins.property
    def for_each(self) -> typing.Optional[_cdktf_9a9027ec.ITerraformIterator]:
        '''
        :stability: experimental
        '''
        result = self._values.get("for_each")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.ITerraformIterator], result)

    @builtins.property
    def lifecycle(self) -> typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle]:
        '''
        :stability: experimental
        '''
        result = self._values.get("lifecycle")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle], result)

    @builtins.property
    def provider(self) -> typing.Optional[_cdktf_9a9027ec.TerraformProvider]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provider")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformProvider], result)

    @builtins.property
    def provisioners(
        self,
    ) -> typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provisioners")
        return typing.cast(typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]], result)

    @builtins.property
    def server_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#server_id MssqlServerExtendedAuditingPolicy#server_id}.'''
        result = self._values.get("server_id")
        assert result is not None, "Required property 'server_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def audit_actions_and_groups(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#audit_actions_and_groups MssqlServerExtendedAuditingPolicy#audit_actions_and_groups}.'''
        result = self._values.get("audit_actions_and_groups")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#enabled MssqlServerExtendedAuditingPolicy#enabled}.'''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#id MssqlServerExtendedAuditingPolicy#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def log_monitoring_enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#log_monitoring_enabled MssqlServerExtendedAuditingPolicy#log_monitoring_enabled}.'''
        result = self._values.get("log_monitoring_enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def predicate_expression(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#predicate_expression MssqlServerExtendedAuditingPolicy#predicate_expression}.'''
        result = self._values.get("predicate_expression")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def retention_in_days(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#retention_in_days MssqlServerExtendedAuditingPolicy#retention_in_days}.'''
        result = self._values.get("retention_in_days")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def storage_account_access_key(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key MssqlServerExtendedAuditingPolicy#storage_account_access_key}.'''
        result = self._values.get("storage_account_access_key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def storage_account_access_key_is_secondary(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_access_key_is_secondary MssqlServerExtendedAuditingPolicy#storage_account_access_key_is_secondary}.'''
        result = self._values.get("storage_account_access_key_is_secondary")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def storage_account_subscription_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_account_subscription_id MssqlServerExtendedAuditingPolicy#storage_account_subscription_id}.'''
        result = self._values.get("storage_account_subscription_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def storage_endpoint(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#storage_endpoint MssqlServerExtendedAuditingPolicy#storage_endpoint}.'''
        result = self._values.get("storage_endpoint")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["MssqlServerExtendedAuditingPolicyTimeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#timeouts MssqlServerExtendedAuditingPolicy#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["MssqlServerExtendedAuditingPolicyTimeouts"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MssqlServerExtendedAuditingPolicyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-azurerm.mssqlServerExtendedAuditingPolicy.MssqlServerExtendedAuditingPolicyTimeouts",
    jsii_struct_bases=[],
    name_mapping={
        "create": "create",
        "delete": "delete",
        "read": "read",
        "update": "update",
    },
)
class MssqlServerExtendedAuditingPolicyTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#create MssqlServerExtendedAuditingPolicy#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#delete MssqlServerExtendedAuditingPolicy#delete}.
        :param read: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#read MssqlServerExtendedAuditingPolicy#read}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#update MssqlServerExtendedAuditingPolicy#update}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4bf406166b30202f36b0e2230c1a3222edb1aef4ede48ada21400ab4089ac48)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if read is not None:
            self._values["read"] = read
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#create MssqlServerExtendedAuditingPolicy#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#delete MssqlServerExtendedAuditingPolicy#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#read MssqlServerExtendedAuditingPolicy#read}.'''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/mssql_server_extended_auditing_policy#update MssqlServerExtendedAuditingPolicy#update}.'''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MssqlServerExtendedAuditingPolicyTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class MssqlServerExtendedAuditingPolicyTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-azurerm.mssqlServerExtendedAuditingPolicy.MssqlServerExtendedAuditingPolicyTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__30ddf6395b64a99581a2fe5f4ce7bfa12e50ecf0b99aaf3a9b5950ee680a91c6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @jsii.member(jsii_name="resetUpdate")
    def reset_update(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdate", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="updateInput")
    def update_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updateInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e87eb72d1c660d4213c8688c6c6b227030de5c68828f20457f0ebb35075d1ef)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6b0e03c013822c19e07eaa63a27bb56fcb36660c961d05c23cc146527e65fc23)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07ff1fe822c81878f7531c15c7a2738d5af12253299070656bcb50c8e11007f0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__384fd95aef9eec6ee35dec1d027dd0a2b9c6a823ac1c481175671bbcdbfb22e3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, MssqlServerExtendedAuditingPolicyTimeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, MssqlServerExtendedAuditingPolicyTimeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, MssqlServerExtendedAuditingPolicyTimeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de17c11e5552d180048560d5a38aa24af21ef51f98676e75070cab733af5e4c3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "MssqlServerExtendedAuditingPolicy",
    "MssqlServerExtendedAuditingPolicyConfig",
    "MssqlServerExtendedAuditingPolicyTimeouts",
    "MssqlServerExtendedAuditingPolicyTimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__5233d0c2502193a1135c4531241d4eae5ede0736cabdcd443742415f09f3c0dc(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    server_id: builtins.str,
    audit_actions_and_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
    enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    id: typing.Optional[builtins.str] = None,
    log_monitoring_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    predicate_expression: typing.Optional[builtins.str] = None,
    retention_in_days: typing.Optional[jsii.Number] = None,
    storage_account_access_key: typing.Optional[builtins.str] = None,
    storage_account_access_key_is_secondary: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    storage_account_subscription_id: typing.Optional[builtins.str] = None,
    storage_endpoint: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[MssqlServerExtendedAuditingPolicyTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f6ca402bdf5abac42acc97965f05c05803983ad729a9007ca31840493ce0a8e(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48d7bb272fecb47f2ba01c6318d625d4f8c6f6a9fb668456444b713c39982914(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__63592a51ec22fed84c8ec5f7671a4ba30451014d3c87751b3694f01aa1a529f7(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dacaa2254215fb9a1aeb73c25838312779ce8e8dec911f400ca88f40b5011886(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__08652d5504944021d52ef21cf5479a82404fee043b26033bf6ce3048e18e3c63(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d862a5d4914cc877200f0f34a633cffba4d8b06758e0049ad2eb0e116bd029f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa23a902cf892e3f201046e25eaa0001458c22388d94a6e378e86833c75dc6f0(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d81142e6be42e1388b22bb544ef19e128386dec905ca0ad40c85c179c34f1152(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__34e36ea132530055aaa962c8dfab8ff625195e7df2d46a4f65b050a01b156ba5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cfcaec73716643d259f9fffc0a86bc03830bc293c0a4369bacfb29065607c6a5(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a5bf6925aa4e78cd11766c16d155f0b637d01f54195bc4c6cd478a644cd6db43(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8699d22e91129cde2a84950bbe8f2de3ae58be109e25619a62814629e94a41b8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__019c8e4b644db6612589915da8a22bef4aad30ddc7dcfeaab7e70a3106064cb7(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    server_id: builtins.str,
    audit_actions_and_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
    enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    id: typing.Optional[builtins.str] = None,
    log_monitoring_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    predicate_expression: typing.Optional[builtins.str] = None,
    retention_in_days: typing.Optional[jsii.Number] = None,
    storage_account_access_key: typing.Optional[builtins.str] = None,
    storage_account_access_key_is_secondary: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    storage_account_subscription_id: typing.Optional[builtins.str] = None,
    storage_endpoint: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[MssqlServerExtendedAuditingPolicyTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e4bf406166b30202f36b0e2230c1a3222edb1aef4ede48ada21400ab4089ac48(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    read: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__30ddf6395b64a99581a2fe5f4ce7bfa12e50ecf0b99aaf3a9b5950ee680a91c6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e87eb72d1c660d4213c8688c6c6b227030de5c68828f20457f0ebb35075d1ef(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6b0e03c013822c19e07eaa63a27bb56fcb36660c961d05c23cc146527e65fc23(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07ff1fe822c81878f7531c15c7a2738d5af12253299070656bcb50c8e11007f0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__384fd95aef9eec6ee35dec1d027dd0a2b9c6a823ac1c481175671bbcdbfb22e3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de17c11e5552d180048560d5a38aa24af21ef51f98676e75070cab733af5e4c3(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, MssqlServerExtendedAuditingPolicyTimeouts]],
) -> None:
    """Type checking stubs"""
    pass
