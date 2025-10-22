r'''
# `databricks_account_federation_policy`

Refer to the Terraform Registry for docs: [`databricks_account_federation_policy`](https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy).
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


class AccountFederationPolicy(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.accountFederationPolicy.AccountFederationPolicy",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy databricks_account_federation_policy}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        description: typing.Optional[builtins.str] = None,
        oidc_policy: typing.Optional[typing.Union["AccountFederationPolicyOidcPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        policy_id: typing.Optional[builtins.str] = None,
        service_principal_id: typing.Optional[jsii.Number] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy databricks_account_federation_policy} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#description AccountFederationPolicy#description}.
        :param oidc_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#oidc_policy AccountFederationPolicy#oidc_policy}.
        :param policy_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#policy_id AccountFederationPolicy#policy_id}.
        :param service_principal_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#service_principal_id AccountFederationPolicy#service_principal_id}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4e3569c9c170b4fc31309cb1c9c810c0d71f1ecc37262689266d6c95b10a2ef)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = AccountFederationPolicyConfig(
            description=description,
            oidc_policy=oidc_policy,
            policy_id=policy_id,
            service_principal_id=service_principal_id,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a AccountFederationPolicy resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the AccountFederationPolicy to import.
        :param import_from_id: The id of the existing AccountFederationPolicy that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the AccountFederationPolicy to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e46005b60c815d10676dbf0d0a103def9aaf443d6eff4fe6d3e265b3fccfd31)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putOidcPolicy")
    def put_oidc_policy(
        self,
        *,
        audiences: typing.Optional[typing.Sequence[builtins.str]] = None,
        issuer: typing.Optional[builtins.str] = None,
        jwks_json: typing.Optional[builtins.str] = None,
        jwks_uri: typing.Optional[builtins.str] = None,
        subject: typing.Optional[builtins.str] = None,
        subject_claim: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param audiences: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#audiences AccountFederationPolicy#audiences}.
        :param issuer: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#issuer AccountFederationPolicy#issuer}.
        :param jwks_json: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_json AccountFederationPolicy#jwks_json}.
        :param jwks_uri: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_uri AccountFederationPolicy#jwks_uri}.
        :param subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject AccountFederationPolicy#subject}.
        :param subject_claim: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject_claim AccountFederationPolicy#subject_claim}.
        '''
        value = AccountFederationPolicyOidcPolicy(
            audiences=audiences,
            issuer=issuer,
            jwks_json=jwks_json,
            jwks_uri=jwks_uri,
            subject=subject,
            subject_claim=subject_claim,
        )

        return typing.cast(None, jsii.invoke(self, "putOidcPolicy", [value]))

    @jsii.member(jsii_name="resetDescription")
    def reset_description(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDescription", []))

    @jsii.member(jsii_name="resetOidcPolicy")
    def reset_oidc_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcPolicy", []))

    @jsii.member(jsii_name="resetPolicyId")
    def reset_policy_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPolicyId", []))

    @jsii.member(jsii_name="resetServicePrincipalId")
    def reset_service_principal_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServicePrincipalId", []))

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
    @jsii.member(jsii_name="createTime")
    def create_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createTime"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="oidcPolicy")
    def oidc_policy(self) -> "AccountFederationPolicyOidcPolicyOutputReference":
        return typing.cast("AccountFederationPolicyOidcPolicyOutputReference", jsii.get(self, "oidcPolicy"))

    @builtins.property
    @jsii.member(jsii_name="uid")
    def uid(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "uid"))

    @builtins.property
    @jsii.member(jsii_name="updateTime")
    def update_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "updateTime"))

    @builtins.property
    @jsii.member(jsii_name="descriptionInput")
    def description_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "descriptionInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcPolicyInput")
    def oidc_policy_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "AccountFederationPolicyOidcPolicy"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "AccountFederationPolicyOidcPolicy"]], jsii.get(self, "oidcPolicyInput"))

    @builtins.property
    @jsii.member(jsii_name="policyIdInput")
    def policy_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "policyIdInput"))

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalIdInput")
    def service_principal_id_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "servicePrincipalIdInput"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "description"))

    @description.setter
    def description(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__671b74c73931eea7bbca4ada4b209e92fe198e2b9550188ed8b52546b5b541e5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "description", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="policyId")
    def policy_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "policyId"))

    @policy_id.setter
    def policy_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6f7777c36de073abe9e8f301336a07cc9ef15ee240a783edabb2020cd864771)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "policyId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalId")
    def service_principal_id(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "servicePrincipalId"))

    @service_principal_id.setter
    def service_principal_id(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__234305b8593418b488cae90f1fbb902b03bb5efa5dc6dea0c3e2d81d0adfb606)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "servicePrincipalId", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.accountFederationPolicy.AccountFederationPolicyConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "description": "description",
        "oidc_policy": "oidcPolicy",
        "policy_id": "policyId",
        "service_principal_id": "servicePrincipalId",
    },
)
class AccountFederationPolicyConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        description: typing.Optional[builtins.str] = None,
        oidc_policy: typing.Optional[typing.Union["AccountFederationPolicyOidcPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        policy_id: typing.Optional[builtins.str] = None,
        service_principal_id: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#description AccountFederationPolicy#description}.
        :param oidc_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#oidc_policy AccountFederationPolicy#oidc_policy}.
        :param policy_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#policy_id AccountFederationPolicy#policy_id}.
        :param service_principal_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#service_principal_id AccountFederationPolicy#service_principal_id}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(oidc_policy, dict):
            oidc_policy = AccountFederationPolicyOidcPolicy(**oidc_policy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0bcbe8fa428f56724a5e988231df994b5113504700176c14d4453f54abd41509)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument oidc_policy", value=oidc_policy, expected_type=type_hints["oidc_policy"])
            check_type(argname="argument policy_id", value=policy_id, expected_type=type_hints["policy_id"])
            check_type(argname="argument service_principal_id", value=service_principal_id, expected_type=type_hints["service_principal_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
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
        if description is not None:
            self._values["description"] = description
        if oidc_policy is not None:
            self._values["oidc_policy"] = oidc_policy
        if policy_id is not None:
            self._values["policy_id"] = policy_id
        if service_principal_id is not None:
            self._values["service_principal_id"] = service_principal_id

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
    def description(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#description AccountFederationPolicy#description}.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_policy(self) -> typing.Optional["AccountFederationPolicyOidcPolicy"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#oidc_policy AccountFederationPolicy#oidc_policy}.'''
        result = self._values.get("oidc_policy")
        return typing.cast(typing.Optional["AccountFederationPolicyOidcPolicy"], result)

    @builtins.property
    def policy_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#policy_id AccountFederationPolicy#policy_id}.'''
        result = self._values.get("policy_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_principal_id(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#service_principal_id AccountFederationPolicy#service_principal_id}.'''
        result = self._values.get("service_principal_id")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AccountFederationPolicyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.accountFederationPolicy.AccountFederationPolicyOidcPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "audiences": "audiences",
        "issuer": "issuer",
        "jwks_json": "jwksJson",
        "jwks_uri": "jwksUri",
        "subject": "subject",
        "subject_claim": "subjectClaim",
    },
)
class AccountFederationPolicyOidcPolicy:
    def __init__(
        self,
        *,
        audiences: typing.Optional[typing.Sequence[builtins.str]] = None,
        issuer: typing.Optional[builtins.str] = None,
        jwks_json: typing.Optional[builtins.str] = None,
        jwks_uri: typing.Optional[builtins.str] = None,
        subject: typing.Optional[builtins.str] = None,
        subject_claim: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param audiences: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#audiences AccountFederationPolicy#audiences}.
        :param issuer: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#issuer AccountFederationPolicy#issuer}.
        :param jwks_json: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_json AccountFederationPolicy#jwks_json}.
        :param jwks_uri: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_uri AccountFederationPolicy#jwks_uri}.
        :param subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject AccountFederationPolicy#subject}.
        :param subject_claim: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject_claim AccountFederationPolicy#subject_claim}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f77ca5227405dc4aafe59d3fa9ee3a33dbc3b13a310c71a11c1d9add4feb343a)
            check_type(argname="argument audiences", value=audiences, expected_type=type_hints["audiences"])
            check_type(argname="argument issuer", value=issuer, expected_type=type_hints["issuer"])
            check_type(argname="argument jwks_json", value=jwks_json, expected_type=type_hints["jwks_json"])
            check_type(argname="argument jwks_uri", value=jwks_uri, expected_type=type_hints["jwks_uri"])
            check_type(argname="argument subject", value=subject, expected_type=type_hints["subject"])
            check_type(argname="argument subject_claim", value=subject_claim, expected_type=type_hints["subject_claim"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if audiences is not None:
            self._values["audiences"] = audiences
        if issuer is not None:
            self._values["issuer"] = issuer
        if jwks_json is not None:
            self._values["jwks_json"] = jwks_json
        if jwks_uri is not None:
            self._values["jwks_uri"] = jwks_uri
        if subject is not None:
            self._values["subject"] = subject
        if subject_claim is not None:
            self._values["subject_claim"] = subject_claim

    @builtins.property
    def audiences(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#audiences AccountFederationPolicy#audiences}.'''
        result = self._values.get("audiences")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def issuer(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#issuer AccountFederationPolicy#issuer}.'''
        result = self._values.get("issuer")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jwks_json(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_json AccountFederationPolicy#jwks_json}.'''
        result = self._values.get("jwks_json")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jwks_uri(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#jwks_uri AccountFederationPolicy#jwks_uri}.'''
        result = self._values.get("jwks_uri")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subject(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject AccountFederationPolicy#subject}.'''
        result = self._values.get("subject")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subject_claim(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.94.0/docs/resources/account_federation_policy#subject_claim AccountFederationPolicy#subject_claim}.'''
        result = self._values.get("subject_claim")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AccountFederationPolicyOidcPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AccountFederationPolicyOidcPolicyOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.accountFederationPolicy.AccountFederationPolicyOidcPolicyOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__f878ce5c14f0a3ee756d2ff330a5dcf27dd61ef18b9e49d0ae842d432a6641b6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAudiences")
    def reset_audiences(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAudiences", []))

    @jsii.member(jsii_name="resetIssuer")
    def reset_issuer(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIssuer", []))

    @jsii.member(jsii_name="resetJwksJson")
    def reset_jwks_json(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetJwksJson", []))

    @jsii.member(jsii_name="resetJwksUri")
    def reset_jwks_uri(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetJwksUri", []))

    @jsii.member(jsii_name="resetSubject")
    def reset_subject(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSubject", []))

    @jsii.member(jsii_name="resetSubjectClaim")
    def reset_subject_claim(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSubjectClaim", []))

    @builtins.property
    @jsii.member(jsii_name="audiencesInput")
    def audiences_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "audiencesInput"))

    @builtins.property
    @jsii.member(jsii_name="issuerInput")
    def issuer_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "issuerInput"))

    @builtins.property
    @jsii.member(jsii_name="jwksJsonInput")
    def jwks_json_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "jwksJsonInput"))

    @builtins.property
    @jsii.member(jsii_name="jwksUriInput")
    def jwks_uri_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "jwksUriInput"))

    @builtins.property
    @jsii.member(jsii_name="subjectClaimInput")
    def subject_claim_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "subjectClaimInput"))

    @builtins.property
    @jsii.member(jsii_name="subjectInput")
    def subject_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "subjectInput"))

    @builtins.property
    @jsii.member(jsii_name="audiences")
    def audiences(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "audiences"))

    @audiences.setter
    def audiences(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17da43bf1d415a640bbe44ed6febffb47b27f5b98a9459e3dc048217d8584513)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "audiences", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="issuer")
    def issuer(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "issuer"))

    @issuer.setter
    def issuer(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b3da3cd69a2c4951b9f305bd4e55e76c42c8209dfe4eb7bb0761f0c1e5154e1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "issuer", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="jwksJson")
    def jwks_json(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "jwksJson"))

    @jwks_json.setter
    def jwks_json(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1dc56bcf4d18a4838fb35b50be18a01278222ce43746e43da02ffadc39657297)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "jwksJson", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="jwksUri")
    def jwks_uri(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "jwksUri"))

    @jwks_uri.setter
    def jwks_uri(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0dc4adfe66e61e4da989d64a0e0e5f44ce4b8d96dfb25999b4ad3ba8c6db7b77)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "jwksUri", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="subject")
    def subject(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "subject"))

    @subject.setter
    def subject(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54940ae3ef5b35045bd38993f040b61bf99ea723517faf159341078bad150079)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "subject", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="subjectClaim")
    def subject_claim(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "subjectClaim"))

    @subject_claim.setter
    def subject_claim(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9546f6f77a36d63e8de98558dc4496abfaad75c8b437f20385aeeb73f38375e6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "subjectClaim", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AccountFederationPolicyOidcPolicy]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AccountFederationPolicyOidcPolicy]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AccountFederationPolicyOidcPolicy]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9d9919c5d1eccc57932a4ce47d331b9135f38d68fcf324a8fe74d0b47b547780)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "AccountFederationPolicy",
    "AccountFederationPolicyConfig",
    "AccountFederationPolicyOidcPolicy",
    "AccountFederationPolicyOidcPolicyOutputReference",
]

publication.publish()

def _typecheckingstub__e4e3569c9c170b4fc31309cb1c9c810c0d71f1ecc37262689266d6c95b10a2ef(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    description: typing.Optional[builtins.str] = None,
    oidc_policy: typing.Optional[typing.Union[AccountFederationPolicyOidcPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    policy_id: typing.Optional[builtins.str] = None,
    service_principal_id: typing.Optional[jsii.Number] = None,
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

def _typecheckingstub__8e46005b60c815d10676dbf0d0a103def9aaf443d6eff4fe6d3e265b3fccfd31(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__671b74c73931eea7bbca4ada4b209e92fe198e2b9550188ed8b52546b5b541e5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6f7777c36de073abe9e8f301336a07cc9ef15ee240a783edabb2020cd864771(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__234305b8593418b488cae90f1fbb902b03bb5efa5dc6dea0c3e2d81d0adfb606(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0bcbe8fa428f56724a5e988231df994b5113504700176c14d4453f54abd41509(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    description: typing.Optional[builtins.str] = None,
    oidc_policy: typing.Optional[typing.Union[AccountFederationPolicyOidcPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    policy_id: typing.Optional[builtins.str] = None,
    service_principal_id: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f77ca5227405dc4aafe59d3fa9ee3a33dbc3b13a310c71a11c1d9add4feb343a(
    *,
    audiences: typing.Optional[typing.Sequence[builtins.str]] = None,
    issuer: typing.Optional[builtins.str] = None,
    jwks_json: typing.Optional[builtins.str] = None,
    jwks_uri: typing.Optional[builtins.str] = None,
    subject: typing.Optional[builtins.str] = None,
    subject_claim: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f878ce5c14f0a3ee756d2ff330a5dcf27dd61ef18b9e49d0ae842d432a6641b6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17da43bf1d415a640bbe44ed6febffb47b27f5b98a9459e3dc048217d8584513(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b3da3cd69a2c4951b9f305bd4e55e76c42c8209dfe4eb7bb0761f0c1e5154e1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1dc56bcf4d18a4838fb35b50be18a01278222ce43746e43da02ffadc39657297(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0dc4adfe66e61e4da989d64a0e0e5f44ce4b8d96dfb25999b4ad3ba8c6db7b77(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54940ae3ef5b35045bd38993f040b61bf99ea723517faf159341078bad150079(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9546f6f77a36d63e8de98558dc4496abfaad75c8b437f20385aeeb73f38375e6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9d9919c5d1eccc57932a4ce47d331b9135f38d68fcf324a8fe74d0b47b547780(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AccountFederationPolicyOidcPolicy]],
) -> None:
    """Type checking stubs"""
    pass
