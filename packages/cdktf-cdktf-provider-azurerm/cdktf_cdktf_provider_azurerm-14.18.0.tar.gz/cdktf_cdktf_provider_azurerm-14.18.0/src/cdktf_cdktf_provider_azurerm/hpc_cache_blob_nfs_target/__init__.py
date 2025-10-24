r'''
# `azurerm_hpc_cache_blob_nfs_target`

Refer to the Terraform Registry for docs: [`azurerm_hpc_cache_blob_nfs_target`](https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target).
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


class HpcCacheBlobNfsTarget(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-azurerm.hpcCacheBlobNfsTarget.HpcCacheBlobNfsTarget",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target azurerm_hpc_cache_blob_nfs_target}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        cache_name: builtins.str,
        name: builtins.str,
        namespace_path: builtins.str,
        resource_group_name: builtins.str,
        storage_container_id: builtins.str,
        usage_model: builtins.str,
        access_policy_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["HpcCacheBlobNfsTargetTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        verification_timer_in_seconds: typing.Optional[jsii.Number] = None,
        write_back_timer_in_seconds: typing.Optional[jsii.Number] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target azurerm_hpc_cache_blob_nfs_target} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param cache_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#cache_name HpcCacheBlobNfsTarget#cache_name}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#name HpcCacheBlobNfsTarget#name}.
        :param namespace_path: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#namespace_path HpcCacheBlobNfsTarget#namespace_path}.
        :param resource_group_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#resource_group_name HpcCacheBlobNfsTarget#resource_group_name}.
        :param storage_container_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#storage_container_id HpcCacheBlobNfsTarget#storage_container_id}.
        :param usage_model: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#usage_model HpcCacheBlobNfsTarget#usage_model}.
        :param access_policy_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#access_policy_name HpcCacheBlobNfsTarget#access_policy_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#id HpcCacheBlobNfsTarget#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#timeouts HpcCacheBlobNfsTarget#timeouts}
        :param verification_timer_in_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#verification_timer_in_seconds HpcCacheBlobNfsTarget#verification_timer_in_seconds}.
        :param write_back_timer_in_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#write_back_timer_in_seconds HpcCacheBlobNfsTarget#write_back_timer_in_seconds}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__964b466320c55044248f9860cbf8e0589cb35cecccfa5555d0d88000a540ff9a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = HpcCacheBlobNfsTargetConfig(
            cache_name=cache_name,
            name=name,
            namespace_path=namespace_path,
            resource_group_name=resource_group_name,
            storage_container_id=storage_container_id,
            usage_model=usage_model,
            access_policy_name=access_policy_name,
            id=id,
            timeouts=timeouts,
            verification_timer_in_seconds=verification_timer_in_seconds,
            write_back_timer_in_seconds=write_back_timer_in_seconds,
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
        '''Generates CDKTF code for importing a HpcCacheBlobNfsTarget resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the HpcCacheBlobNfsTarget to import.
        :param import_from_id: The id of the existing HpcCacheBlobNfsTarget that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the HpcCacheBlobNfsTarget to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__701b7b8566f8e272419c9c3dae53dfb3d11da07a85a9198fbf7d41595fe65f5d)
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
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#create HpcCacheBlobNfsTarget#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#delete HpcCacheBlobNfsTarget#delete}.
        :param read: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#read HpcCacheBlobNfsTarget#read}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#update HpcCacheBlobNfsTarget#update}.
        '''
        value = HpcCacheBlobNfsTargetTimeouts(
            create=create, delete=delete, read=read, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetAccessPolicyName")
    def reset_access_policy_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAccessPolicyName", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="resetVerificationTimerInSeconds")
    def reset_verification_timer_in_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVerificationTimerInSeconds", []))

    @jsii.member(jsii_name="resetWriteBackTimerInSeconds")
    def reset_write_back_timer_in_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetWriteBackTimerInSeconds", []))

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
    def timeouts(self) -> "HpcCacheBlobNfsTargetTimeoutsOutputReference":
        return typing.cast("HpcCacheBlobNfsTargetTimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="accessPolicyNameInput")
    def access_policy_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "accessPolicyNameInput"))

    @builtins.property
    @jsii.member(jsii_name="cacheNameInput")
    def cache_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "cacheNameInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="namespacePathInput")
    def namespace_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespacePathInput"))

    @builtins.property
    @jsii.member(jsii_name="resourceGroupNameInput")
    def resource_group_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "resourceGroupNameInput"))

    @builtins.property
    @jsii.member(jsii_name="storageContainerIdInput")
    def storage_container_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "storageContainerIdInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "HpcCacheBlobNfsTargetTimeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "HpcCacheBlobNfsTargetTimeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="usageModelInput")
    def usage_model_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "usageModelInput"))

    @builtins.property
    @jsii.member(jsii_name="verificationTimerInSecondsInput")
    def verification_timer_in_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "verificationTimerInSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="writeBackTimerInSecondsInput")
    def write_back_timer_in_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "writeBackTimerInSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="accessPolicyName")
    def access_policy_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "accessPolicyName"))

    @access_policy_name.setter
    def access_policy_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0e769c1fa886cd1c6602034328a72523517a1bb4833b1ad92b829b9594f8082)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "accessPolicyName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="cacheName")
    def cache_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "cacheName"))

    @cache_name.setter
    def cache_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c973d9ed3be01d5ae67db7ed46306a7eac8f13f4393b9aa93fc9c1e037adbc98)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "cacheName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d4fc91e19aa6772e267d77f193dd6bfe4da768a28a19802f7d2a5ad3c21a99a1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26f75d57036e0c48a256a41b0b9ee9780d9f698372b5fc89cd2deabf7ede0859)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="namespacePath")
    def namespace_path(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "namespacePath"))

    @namespace_path.setter
    def namespace_path(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__30c7c1553b7c69113212b1b74239864891c537d137b4597c604b27c6390d9346)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "namespacePath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="resourceGroupName")
    def resource_group_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceGroupName"))

    @resource_group_name.setter
    def resource_group_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__01300a8df274e3d3210ecb168d9db30783dbc8f281fd9136708870acc8e039b2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "resourceGroupName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageContainerId")
    def storage_container_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "storageContainerId"))

    @storage_container_id.setter
    def storage_container_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6e363904e0e1b6cf4eccce86a2c4a91c5ebfdfb9ba204c8016c9149708b898d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageContainerId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="usageModel")
    def usage_model(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "usageModel"))

    @usage_model.setter
    def usage_model(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__582eb4e357b57ebf8c3b2d87f092f9a3c077eaebc089858518d963711303cff8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "usageModel", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="verificationTimerInSeconds")
    def verification_timer_in_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "verificationTimerInSeconds"))

    @verification_timer_in_seconds.setter
    def verification_timer_in_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a0428b0b72759d04e75ba7485ba123df99fe851b44fdfc5c6529909a5d077b4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "verificationTimerInSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="writeBackTimerInSeconds")
    def write_back_timer_in_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "writeBackTimerInSeconds"))

    @write_back_timer_in_seconds.setter
    def write_back_timer_in_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a66c1b94b1f183dc12f9af12b31e3c81c5a81fcdb34ab209e01daa9cf7068549)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "writeBackTimerInSeconds", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-azurerm.hpcCacheBlobNfsTarget.HpcCacheBlobNfsTargetConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "cache_name": "cacheName",
        "name": "name",
        "namespace_path": "namespacePath",
        "resource_group_name": "resourceGroupName",
        "storage_container_id": "storageContainerId",
        "usage_model": "usageModel",
        "access_policy_name": "accessPolicyName",
        "id": "id",
        "timeouts": "timeouts",
        "verification_timer_in_seconds": "verificationTimerInSeconds",
        "write_back_timer_in_seconds": "writeBackTimerInSeconds",
    },
)
class HpcCacheBlobNfsTargetConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        cache_name: builtins.str,
        name: builtins.str,
        namespace_path: builtins.str,
        resource_group_name: builtins.str,
        storage_container_id: builtins.str,
        usage_model: builtins.str,
        access_policy_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["HpcCacheBlobNfsTargetTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        verification_timer_in_seconds: typing.Optional[jsii.Number] = None,
        write_back_timer_in_seconds: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param cache_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#cache_name HpcCacheBlobNfsTarget#cache_name}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#name HpcCacheBlobNfsTarget#name}.
        :param namespace_path: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#namespace_path HpcCacheBlobNfsTarget#namespace_path}.
        :param resource_group_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#resource_group_name HpcCacheBlobNfsTarget#resource_group_name}.
        :param storage_container_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#storage_container_id HpcCacheBlobNfsTarget#storage_container_id}.
        :param usage_model: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#usage_model HpcCacheBlobNfsTarget#usage_model}.
        :param access_policy_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#access_policy_name HpcCacheBlobNfsTarget#access_policy_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#id HpcCacheBlobNfsTarget#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#timeouts HpcCacheBlobNfsTarget#timeouts}
        :param verification_timer_in_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#verification_timer_in_seconds HpcCacheBlobNfsTarget#verification_timer_in_seconds}.
        :param write_back_timer_in_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#write_back_timer_in_seconds HpcCacheBlobNfsTarget#write_back_timer_in_seconds}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(timeouts, dict):
            timeouts = HpcCacheBlobNfsTargetTimeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__27ba972d712418f2258c05a32c4e77036eb87c95d8f12b80c47095a5368bc72c)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument cache_name", value=cache_name, expected_type=type_hints["cache_name"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace_path", value=namespace_path, expected_type=type_hints["namespace_path"])
            check_type(argname="argument resource_group_name", value=resource_group_name, expected_type=type_hints["resource_group_name"])
            check_type(argname="argument storage_container_id", value=storage_container_id, expected_type=type_hints["storage_container_id"])
            check_type(argname="argument usage_model", value=usage_model, expected_type=type_hints["usage_model"])
            check_type(argname="argument access_policy_name", value=access_policy_name, expected_type=type_hints["access_policy_name"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
            check_type(argname="argument verification_timer_in_seconds", value=verification_timer_in_seconds, expected_type=type_hints["verification_timer_in_seconds"])
            check_type(argname="argument write_back_timer_in_seconds", value=write_back_timer_in_seconds, expected_type=type_hints["write_back_timer_in_seconds"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cache_name": cache_name,
            "name": name,
            "namespace_path": namespace_path,
            "resource_group_name": resource_group_name,
            "storage_container_id": storage_container_id,
            "usage_model": usage_model,
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
        if access_policy_name is not None:
            self._values["access_policy_name"] = access_policy_name
        if id is not None:
            self._values["id"] = id
        if timeouts is not None:
            self._values["timeouts"] = timeouts
        if verification_timer_in_seconds is not None:
            self._values["verification_timer_in_seconds"] = verification_timer_in_seconds
        if write_back_timer_in_seconds is not None:
            self._values["write_back_timer_in_seconds"] = write_back_timer_in_seconds

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
    def cache_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#cache_name HpcCacheBlobNfsTarget#cache_name}.'''
        result = self._values.get("cache_name")
        assert result is not None, "Required property 'cache_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#name HpcCacheBlobNfsTarget#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def namespace_path(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#namespace_path HpcCacheBlobNfsTarget#namespace_path}.'''
        result = self._values.get("namespace_path")
        assert result is not None, "Required property 'namespace_path' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_group_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#resource_group_name HpcCacheBlobNfsTarget#resource_group_name}.'''
        result = self._values.get("resource_group_name")
        assert result is not None, "Required property 'resource_group_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def storage_container_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#storage_container_id HpcCacheBlobNfsTarget#storage_container_id}.'''
        result = self._values.get("storage_container_id")
        assert result is not None, "Required property 'storage_container_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def usage_model(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#usage_model HpcCacheBlobNfsTarget#usage_model}.'''
        result = self._values.get("usage_model")
        assert result is not None, "Required property 'usage_model' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def access_policy_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#access_policy_name HpcCacheBlobNfsTarget#access_policy_name}.'''
        result = self._values.get("access_policy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#id HpcCacheBlobNfsTarget#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["HpcCacheBlobNfsTargetTimeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#timeouts HpcCacheBlobNfsTarget#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["HpcCacheBlobNfsTargetTimeouts"], result)

    @builtins.property
    def verification_timer_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#verification_timer_in_seconds HpcCacheBlobNfsTarget#verification_timer_in_seconds}.'''
        result = self._values.get("verification_timer_in_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def write_back_timer_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#write_back_timer_in_seconds HpcCacheBlobNfsTarget#write_back_timer_in_seconds}.'''
        result = self._values.get("write_back_timer_in_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "HpcCacheBlobNfsTargetConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-azurerm.hpcCacheBlobNfsTarget.HpcCacheBlobNfsTargetTimeouts",
    jsii_struct_bases=[],
    name_mapping={
        "create": "create",
        "delete": "delete",
        "read": "read",
        "update": "update",
    },
)
class HpcCacheBlobNfsTargetTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#create HpcCacheBlobNfsTarget#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#delete HpcCacheBlobNfsTarget#delete}.
        :param read: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#read HpcCacheBlobNfsTarget#read}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#update HpcCacheBlobNfsTarget#update}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4253c64e7403abbdacc17289d4de50bb9bdc072eb6c88695644a41106307e2d5)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#create HpcCacheBlobNfsTarget#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#delete HpcCacheBlobNfsTarget#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#read HpcCacheBlobNfsTarget#read}.'''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/azurerm/4.50.0/docs/resources/hpc_cache_blob_nfs_target#update HpcCacheBlobNfsTarget#update}.'''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "HpcCacheBlobNfsTargetTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class HpcCacheBlobNfsTargetTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-azurerm.hpcCacheBlobNfsTarget.HpcCacheBlobNfsTargetTimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__875fc3ec92278c23d46b86ea7251d729d074c2b7b206f9cd5a9d89f6973f645c)
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
            type_hints = typing.get_type_hints(_typecheckingstub__af4f45b11d93aca5eead578c768973585fe20fa2aa8105a68aaf1aeee316a3e0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8664bcf55aa399208423a17eec84666a302c83e0b7fbe7ea253a486dd41fd7f6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4701b9795db8a827369585cfdd884be3a74ae145a9ad9ffd72f23deda24109fc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be903b5cc639e9d283fa3a1de2d832e8ee6a4456f388a469fb137fb6376eaa5c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, HpcCacheBlobNfsTargetTimeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, HpcCacheBlobNfsTargetTimeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, HpcCacheBlobNfsTargetTimeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f76380267c8f7e4822d70f386ccc65b1b47726fb124d69c616b203897baeb612)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "HpcCacheBlobNfsTarget",
    "HpcCacheBlobNfsTargetConfig",
    "HpcCacheBlobNfsTargetTimeouts",
    "HpcCacheBlobNfsTargetTimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__964b466320c55044248f9860cbf8e0589cb35cecccfa5555d0d88000a540ff9a(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    cache_name: builtins.str,
    name: builtins.str,
    namespace_path: builtins.str,
    resource_group_name: builtins.str,
    storage_container_id: builtins.str,
    usage_model: builtins.str,
    access_policy_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[HpcCacheBlobNfsTargetTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
    verification_timer_in_seconds: typing.Optional[jsii.Number] = None,
    write_back_timer_in_seconds: typing.Optional[jsii.Number] = None,
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

def _typecheckingstub__701b7b8566f8e272419c9c3dae53dfb3d11da07a85a9198fbf7d41595fe65f5d(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0e769c1fa886cd1c6602034328a72523517a1bb4833b1ad92b829b9594f8082(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c973d9ed3be01d5ae67db7ed46306a7eac8f13f4393b9aa93fc9c1e037adbc98(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d4fc91e19aa6772e267d77f193dd6bfe4da768a28a19802f7d2a5ad3c21a99a1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26f75d57036e0c48a256a41b0b9ee9780d9f698372b5fc89cd2deabf7ede0859(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__30c7c1553b7c69113212b1b74239864891c537d137b4597c604b27c6390d9346(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__01300a8df274e3d3210ecb168d9db30783dbc8f281fd9136708870acc8e039b2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6e363904e0e1b6cf4eccce86a2c4a91c5ebfdfb9ba204c8016c9149708b898d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__582eb4e357b57ebf8c3b2d87f092f9a3c077eaebc089858518d963711303cff8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a0428b0b72759d04e75ba7485ba123df99fe851b44fdfc5c6529909a5d077b4(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a66c1b94b1f183dc12f9af12b31e3c81c5a81fcdb34ab209e01daa9cf7068549(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__27ba972d712418f2258c05a32c4e77036eb87c95d8f12b80c47095a5368bc72c(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    cache_name: builtins.str,
    name: builtins.str,
    namespace_path: builtins.str,
    resource_group_name: builtins.str,
    storage_container_id: builtins.str,
    usage_model: builtins.str,
    access_policy_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[HpcCacheBlobNfsTargetTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
    verification_timer_in_seconds: typing.Optional[jsii.Number] = None,
    write_back_timer_in_seconds: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4253c64e7403abbdacc17289d4de50bb9bdc072eb6c88695644a41106307e2d5(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    read: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__875fc3ec92278c23d46b86ea7251d729d074c2b7b206f9cd5a9d89f6973f645c(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__af4f45b11d93aca5eead578c768973585fe20fa2aa8105a68aaf1aeee316a3e0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8664bcf55aa399208423a17eec84666a302c83e0b7fbe7ea253a486dd41fd7f6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4701b9795db8a827369585cfdd884be3a74ae145a9ad9ffd72f23deda24109fc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be903b5cc639e9d283fa3a1de2d832e8ee6a4456f388a469fb137fb6376eaa5c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f76380267c8f7e4822d70f386ccc65b1b47726fb124d69c616b203897baeb612(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, HpcCacheBlobNfsTargetTimeouts]],
) -> None:
    """Type checking stubs"""
    pass
