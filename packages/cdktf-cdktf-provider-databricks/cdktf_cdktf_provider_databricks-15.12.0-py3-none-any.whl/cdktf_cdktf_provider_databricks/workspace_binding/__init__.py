r'''
# `databricks_workspace_binding`

Refer to the Terraform Registry for docs: [`databricks_workspace_binding`](https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding).
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


class WorkspaceBinding(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.workspaceBinding.WorkspaceBinding",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding databricks_workspace_binding}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        workspace_id: jsii.Number,
        binding_type: typing.Optional[builtins.str] = None,
        catalog_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        securable_name: typing.Optional[builtins.str] = None,
        securable_type: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding databricks_workspace_binding} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param workspace_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#workspace_id WorkspaceBinding#workspace_id}.
        :param binding_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#binding_type WorkspaceBinding#binding_type}.
        :param catalog_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#catalog_name WorkspaceBinding#catalog_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#id WorkspaceBinding#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param securable_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_name WorkspaceBinding#securable_name}.
        :param securable_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_type WorkspaceBinding#securable_type}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff8f9d5af9fb3c73f44f2e0a2e9c7430d7647e43332fa87e9757c50ba4e04b13)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = WorkspaceBindingConfig(
            workspace_id=workspace_id,
            binding_type=binding_type,
            catalog_name=catalog_name,
            id=id,
            securable_name=securable_name,
            securable_type=securable_type,
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
        '''Generates CDKTF code for importing a WorkspaceBinding resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the WorkspaceBinding to import.
        :param import_from_id: The id of the existing WorkspaceBinding that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the WorkspaceBinding to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__72e3390e7764cd73bbbfeb00edcadfd0d8362d2e6ba53b1d42a7089bd4ab207f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetBindingType")
    def reset_binding_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBindingType", []))

    @jsii.member(jsii_name="resetCatalogName")
    def reset_catalog_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCatalogName", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetSecurableName")
    def reset_securable_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecurableName", []))

    @jsii.member(jsii_name="resetSecurableType")
    def reset_securable_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecurableType", []))

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
    @jsii.member(jsii_name="bindingTypeInput")
    def binding_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "bindingTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="catalogNameInput")
    def catalog_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "catalogNameInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="securableNameInput")
    def securable_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "securableNameInput"))

    @builtins.property
    @jsii.member(jsii_name="securableTypeInput")
    def securable_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "securableTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="workspaceIdInput")
    def workspace_id_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "workspaceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="bindingType")
    def binding_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "bindingType"))

    @binding_type.setter
    def binding_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fdb981e0658fcad6eb03d1eca7c2fb03b0baaf13c0c4e4c2019d7bf47be45a26)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "bindingType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="catalogName")
    def catalog_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "catalogName"))

    @catalog_name.setter
    def catalog_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96fd99990e14e95d5303d53556ef8bdb4f2b783b17d50fbd272cbf873d625b17)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "catalogName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8b360386bd1e3328a4eb407eb46a38650ad95457c32549e041bfd2dccf24ad66)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="securableName")
    def securable_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "securableName"))

    @securable_name.setter
    def securable_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__393ba288530c5c763718c0638bc771317086c0946bd6c3377506eb080b308a5c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "securableName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="securableType")
    def securable_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "securableType"))

    @securable_type.setter
    def securable_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__618711529f1cc63ed09e9055d275bfa925bab8201365e892b82c83151ebc4abc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "securableType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    def workspace_id(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "workspaceId"))

    @workspace_id.setter
    def workspace_id(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c24f2997d6ae5ea4a9bbb6c6daf2897c4df7732c990937dfaa31a619079226b4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "workspaceId", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.workspaceBinding.WorkspaceBindingConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "workspace_id": "workspaceId",
        "binding_type": "bindingType",
        "catalog_name": "catalogName",
        "id": "id",
        "securable_name": "securableName",
        "securable_type": "securableType",
    },
)
class WorkspaceBindingConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        workspace_id: jsii.Number,
        binding_type: typing.Optional[builtins.str] = None,
        catalog_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        securable_name: typing.Optional[builtins.str] = None,
        securable_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param workspace_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#workspace_id WorkspaceBinding#workspace_id}.
        :param binding_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#binding_type WorkspaceBinding#binding_type}.
        :param catalog_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#catalog_name WorkspaceBinding#catalog_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#id WorkspaceBinding#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param securable_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_name WorkspaceBinding#securable_name}.
        :param securable_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_type WorkspaceBinding#securable_type}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__90fd412dbfaed96eab172d7e71d07a90caad7e4ba68ad58062be3ff1dd3180ba)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
            check_type(argname="argument binding_type", value=binding_type, expected_type=type_hints["binding_type"])
            check_type(argname="argument catalog_name", value=catalog_name, expected_type=type_hints["catalog_name"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument securable_name", value=securable_name, expected_type=type_hints["securable_name"])
            check_type(argname="argument securable_type", value=securable_type, expected_type=type_hints["securable_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "workspace_id": workspace_id,
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
        if binding_type is not None:
            self._values["binding_type"] = binding_type
        if catalog_name is not None:
            self._values["catalog_name"] = catalog_name
        if id is not None:
            self._values["id"] = id
        if securable_name is not None:
            self._values["securable_name"] = securable_name
        if securable_type is not None:
            self._values["securable_type"] = securable_type

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
    def workspace_id(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#workspace_id WorkspaceBinding#workspace_id}.'''
        result = self._values.get("workspace_id")
        assert result is not None, "Required property 'workspace_id' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def binding_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#binding_type WorkspaceBinding#binding_type}.'''
        result = self._values.get("binding_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def catalog_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#catalog_name WorkspaceBinding#catalog_name}.'''
        result = self._values.get("catalog_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#id WorkspaceBinding#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def securable_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_name WorkspaceBinding#securable_name}.'''
        result = self._values.get("securable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def securable_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.95.0/docs/resources/workspace_binding#securable_type WorkspaceBinding#securable_type}.'''
        result = self._values.get("securable_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WorkspaceBindingConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "WorkspaceBinding",
    "WorkspaceBindingConfig",
]

publication.publish()

def _typecheckingstub__ff8f9d5af9fb3c73f44f2e0a2e9c7430d7647e43332fa87e9757c50ba4e04b13(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    workspace_id: jsii.Number,
    binding_type: typing.Optional[builtins.str] = None,
    catalog_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    securable_name: typing.Optional[builtins.str] = None,
    securable_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__72e3390e7764cd73bbbfeb00edcadfd0d8362d2e6ba53b1d42a7089bd4ab207f(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fdb981e0658fcad6eb03d1eca7c2fb03b0baaf13c0c4e4c2019d7bf47be45a26(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96fd99990e14e95d5303d53556ef8bdb4f2b783b17d50fbd272cbf873d625b17(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8b360386bd1e3328a4eb407eb46a38650ad95457c32549e041bfd2dccf24ad66(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__393ba288530c5c763718c0638bc771317086c0946bd6c3377506eb080b308a5c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__618711529f1cc63ed09e9055d275bfa925bab8201365e892b82c83151ebc4abc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c24f2997d6ae5ea4a9bbb6c6daf2897c4df7732c990937dfaa31a619079226b4(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__90fd412dbfaed96eab172d7e71d07a90caad7e4ba68ad58062be3ff1dd3180ba(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    workspace_id: jsii.Number,
    binding_type: typing.Optional[builtins.str] = None,
    catalog_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    securable_name: typing.Optional[builtins.str] = None,
    securable_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
