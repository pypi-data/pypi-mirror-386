r'''
# `github_actions_organization_secret`

Refer to the Terraform Registry for docs: [`github_actions_organization_secret`](https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret).
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


class ActionsOrganizationSecret(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-github.actionsOrganizationSecret.ActionsOrganizationSecret",
):
    '''Represents a {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret github_actions_organization_secret}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        secret_name: builtins.str,
        visibility: builtins.str,
        destroy_on_drift: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        encrypted_value: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        plaintext_value: typing.Optional[builtins.str] = None,
        selected_repository_ids: typing.Optional[typing.Sequence[jsii.Number]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret github_actions_organization_secret} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param secret_name: Name of the secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#secret_name ActionsOrganizationSecret#secret_name}
        :param visibility: Configures the access that repositories have to the organization secret. Must be one of 'all', 'private', or 'selected'. 'selected_repository_ids' is required if set to 'selected'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#visibility ActionsOrganizationSecret#visibility}
        :param destroy_on_drift: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#destroy_on_drift ActionsOrganizationSecret#destroy_on_drift}.
        :param encrypted_value: Encrypted value of the secret using the GitHub public key in Base64 format. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#encrypted_value ActionsOrganizationSecret#encrypted_value}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#id ActionsOrganizationSecret#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param plaintext_value: Plaintext value of the secret to be encrypted. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#plaintext_value ActionsOrganizationSecret#plaintext_value}
        :param selected_repository_ids: An array of repository ids that can access the organization secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#selected_repository_ids ActionsOrganizationSecret#selected_repository_ids}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7773251e66c29ee287af7ba6530644936ff7820cb2ba605bc235587466e8bf89)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = ActionsOrganizationSecretConfig(
            secret_name=secret_name,
            visibility=visibility,
            destroy_on_drift=destroy_on_drift,
            encrypted_value=encrypted_value,
            id=id,
            plaintext_value=plaintext_value,
            selected_repository_ids=selected_repository_ids,
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
        '''Generates CDKTF code for importing a ActionsOrganizationSecret resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the ActionsOrganizationSecret to import.
        :param import_from_id: The id of the existing ActionsOrganizationSecret that should be imported. Refer to the {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the ActionsOrganizationSecret to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__df72695d569784b81fb7546d4918b2380ef09d030a9680e683ffabfba15f6170)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetDestroyOnDrift")
    def reset_destroy_on_drift(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDestroyOnDrift", []))

    @jsii.member(jsii_name="resetEncryptedValue")
    def reset_encrypted_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEncryptedValue", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetPlaintextValue")
    def reset_plaintext_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPlaintextValue", []))

    @jsii.member(jsii_name="resetSelectedRepositoryIds")
    def reset_selected_repository_ids(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSelectedRepositoryIds", []))

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
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="updatedAt")
    def updated_at(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "updatedAt"))

    @builtins.property
    @jsii.member(jsii_name="destroyOnDriftInput")
    def destroy_on_drift_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "destroyOnDriftInput"))

    @builtins.property
    @jsii.member(jsii_name="encryptedValueInput")
    def encrypted_value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "encryptedValueInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="plaintextValueInput")
    def plaintext_value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "plaintextValueInput"))

    @builtins.property
    @jsii.member(jsii_name="secretNameInput")
    def secret_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "secretNameInput"))

    @builtins.property
    @jsii.member(jsii_name="selectedRepositoryIdsInput")
    def selected_repository_ids_input(
        self,
    ) -> typing.Optional[typing.List[jsii.Number]]:
        return typing.cast(typing.Optional[typing.List[jsii.Number]], jsii.get(self, "selectedRepositoryIdsInput"))

    @builtins.property
    @jsii.member(jsii_name="visibilityInput")
    def visibility_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "visibilityInput"))

    @builtins.property
    @jsii.member(jsii_name="destroyOnDrift")
    def destroy_on_drift(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "destroyOnDrift"))

    @destroy_on_drift.setter
    def destroy_on_drift(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0065270697a9677d0a6f6d33ab1856647ad49e5d10abd0211d960a4135d4ab1d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "destroyOnDrift", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="encryptedValue")
    def encrypted_value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "encryptedValue"))

    @encrypted_value.setter
    def encrypted_value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc022bbe5b8a004574eb610500bcd3c3484cf0eb479a71dbcad40711338a6d84)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "encryptedValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1daed895fb26c6e4406e0ccd07bc2a7ec5c889c2e8bb3dcd87c34fadadb9b350)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="plaintextValue")
    def plaintext_value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "plaintextValue"))

    @plaintext_value.setter
    def plaintext_value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__90600238daac91037f438d3e99f7238c30d669043f4a5233d18cc7d12f98da48)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "plaintextValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="secretName")
    def secret_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretName"))

    @secret_name.setter
    def secret_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7aa82e101741f99e9df835af360c8ecfddd703a591a675946c14a173e34bbaf4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "secretName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="selectedRepositoryIds")
    def selected_repository_ids(self) -> typing.List[jsii.Number]:
        return typing.cast(typing.List[jsii.Number], jsii.get(self, "selectedRepositoryIds"))

    @selected_repository_ids.setter
    def selected_repository_ids(self, value: typing.List[jsii.Number]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7ec116a046268979f18a24f323a30303c2cfa265677a0832600a7877e52f4c2b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "selectedRepositoryIds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="visibility")
    def visibility(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "visibility"))

    @visibility.setter
    def visibility(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7a5ce86e4faa7d15890c0ad864c607ac908c1361303cfbbffaeac6960933d15)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "visibility", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-github.actionsOrganizationSecret.ActionsOrganizationSecretConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "secret_name": "secretName",
        "visibility": "visibility",
        "destroy_on_drift": "destroyOnDrift",
        "encrypted_value": "encryptedValue",
        "id": "id",
        "plaintext_value": "plaintextValue",
        "selected_repository_ids": "selectedRepositoryIds",
    },
)
class ActionsOrganizationSecretConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        secret_name: builtins.str,
        visibility: builtins.str,
        destroy_on_drift: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        encrypted_value: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        plaintext_value: typing.Optional[builtins.str] = None,
        selected_repository_ids: typing.Optional[typing.Sequence[jsii.Number]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param secret_name: Name of the secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#secret_name ActionsOrganizationSecret#secret_name}
        :param visibility: Configures the access that repositories have to the organization secret. Must be one of 'all', 'private', or 'selected'. 'selected_repository_ids' is required if set to 'selected'. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#visibility ActionsOrganizationSecret#visibility}
        :param destroy_on_drift: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#destroy_on_drift ActionsOrganizationSecret#destroy_on_drift}.
        :param encrypted_value: Encrypted value of the secret using the GitHub public key in Base64 format. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#encrypted_value ActionsOrganizationSecret#encrypted_value}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#id ActionsOrganizationSecret#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param plaintext_value: Plaintext value of the secret to be encrypted. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#plaintext_value ActionsOrganizationSecret#plaintext_value}
        :param selected_repository_ids: An array of repository ids that can access the organization secret. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#selected_repository_ids ActionsOrganizationSecret#selected_repository_ids}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61a92dbecb12ddac5f022538fb9bb4c7fb09a7cf3e6abee0b3abdd9c856d0a6a)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument secret_name", value=secret_name, expected_type=type_hints["secret_name"])
            check_type(argname="argument visibility", value=visibility, expected_type=type_hints["visibility"])
            check_type(argname="argument destroy_on_drift", value=destroy_on_drift, expected_type=type_hints["destroy_on_drift"])
            check_type(argname="argument encrypted_value", value=encrypted_value, expected_type=type_hints["encrypted_value"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument plaintext_value", value=plaintext_value, expected_type=type_hints["plaintext_value"])
            check_type(argname="argument selected_repository_ids", value=selected_repository_ids, expected_type=type_hints["selected_repository_ids"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "secret_name": secret_name,
            "visibility": visibility,
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
        if destroy_on_drift is not None:
            self._values["destroy_on_drift"] = destroy_on_drift
        if encrypted_value is not None:
            self._values["encrypted_value"] = encrypted_value
        if id is not None:
            self._values["id"] = id
        if plaintext_value is not None:
            self._values["plaintext_value"] = plaintext_value
        if selected_repository_ids is not None:
            self._values["selected_repository_ids"] = selected_repository_ids

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
    def secret_name(self) -> builtins.str:
        '''Name of the secret.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#secret_name ActionsOrganizationSecret#secret_name}
        '''
        result = self._values.get("secret_name")
        assert result is not None, "Required property 'secret_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def visibility(self) -> builtins.str:
        '''Configures the access that repositories have to the organization secret.

        Must be one of 'all', 'private', or 'selected'. 'selected_repository_ids' is required if set to 'selected'.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#visibility ActionsOrganizationSecret#visibility}
        '''
        result = self._values.get("visibility")
        assert result is not None, "Required property 'visibility' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def destroy_on_drift(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#destroy_on_drift ActionsOrganizationSecret#destroy_on_drift}.'''
        result = self._values.get("destroy_on_drift")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def encrypted_value(self) -> typing.Optional[builtins.str]:
        '''Encrypted value of the secret using the GitHub public key in Base64 format.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#encrypted_value ActionsOrganizationSecret#encrypted_value}
        '''
        result = self._values.get("encrypted_value")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#id ActionsOrganizationSecret#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plaintext_value(self) -> typing.Optional[builtins.str]:
        '''Plaintext value of the secret to be encrypted.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#plaintext_value ActionsOrganizationSecret#plaintext_value}
        '''
        result = self._values.get("plaintext_value")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def selected_repository_ids(self) -> typing.Optional[typing.List[jsii.Number]]:
        '''An array of repository ids that can access the organization secret.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/integrations/github/6.7.0/docs/resources/actions_organization_secret#selected_repository_ids ActionsOrganizationSecret#selected_repository_ids}
        '''
        result = self._values.get("selected_repository_ids")
        return typing.cast(typing.Optional[typing.List[jsii.Number]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActionsOrganizationSecretConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ActionsOrganizationSecret",
    "ActionsOrganizationSecretConfig",
]

publication.publish()

def _typecheckingstub__7773251e66c29ee287af7ba6530644936ff7820cb2ba605bc235587466e8bf89(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    secret_name: builtins.str,
    visibility: builtins.str,
    destroy_on_drift: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    encrypted_value: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    plaintext_value: typing.Optional[builtins.str] = None,
    selected_repository_ids: typing.Optional[typing.Sequence[jsii.Number]] = None,
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

def _typecheckingstub__df72695d569784b81fb7546d4918b2380ef09d030a9680e683ffabfba15f6170(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0065270697a9677d0a6f6d33ab1856647ad49e5d10abd0211d960a4135d4ab1d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc022bbe5b8a004574eb610500bcd3c3484cf0eb479a71dbcad40711338a6d84(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1daed895fb26c6e4406e0ccd07bc2a7ec5c889c2e8bb3dcd87c34fadadb9b350(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__90600238daac91037f438d3e99f7238c30d669043f4a5233d18cc7d12f98da48(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7aa82e101741f99e9df835af360c8ecfddd703a591a675946c14a173e34bbaf4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7ec116a046268979f18a24f323a30303c2cfa265677a0832600a7877e52f4c2b(
    value: typing.List[jsii.Number],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7a5ce86e4faa7d15890c0ad864c607ac908c1361303cfbbffaeac6960933d15(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__61a92dbecb12ddac5f022538fb9bb4c7fb09a7cf3e6abee0b3abdd9c856d0a6a(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    secret_name: builtins.str,
    visibility: builtins.str,
    destroy_on_drift: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    encrypted_value: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    plaintext_value: typing.Optional[builtins.str] = None,
    selected_repository_ids: typing.Optional[typing.Sequence[jsii.Number]] = None,
) -> None:
    """Type checking stubs"""
    pass
