r'''
# `data_aws_secretsmanager_secret_version`

Refer to the Terraform Registry for docs: [`data_aws_secretsmanager_secret_version`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version).
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


class DataAwsSecretsmanagerSecretVersion(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dataAwsSecretsmanagerSecretVersion.DataAwsSecretsmanagerSecretVersion",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version aws_secretsmanager_secret_version}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        secret_id: builtins.str,
        id: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
        version_id: typing.Optional[builtins.str] = None,
        version_stage: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version aws_secretsmanager_secret_version} Data Source.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param secret_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#secret_id DataAwsSecretsmanagerSecretVersion#secret_id}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#id DataAwsSecretsmanagerSecretVersion#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#region DataAwsSecretsmanagerSecretVersion#region}
        :param version_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_id DataAwsSecretsmanagerSecretVersion#version_id}.
        :param version_stage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_stage DataAwsSecretsmanagerSecretVersion#version_stage}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__728e71d67f44501776c20bdf9a11a07294fa1b159681e9568da07681efc46005)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = DataAwsSecretsmanagerSecretVersionConfig(
            secret_id=secret_id,
            id=id,
            region=region,
            version_id=version_id,
            version_stage=version_stage,
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
        '''Generates CDKTF code for importing a DataAwsSecretsmanagerSecretVersion resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataAwsSecretsmanagerSecretVersion to import.
        :param import_from_id: The id of the existing DataAwsSecretsmanagerSecretVersion that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataAwsSecretsmanagerSecretVersion to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__10f3115000d98976499483215efc36c61f6c08a2d204337aaeb1711b2dcf05d2)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetVersionId")
    def reset_version_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVersionId", []))

    @jsii.member(jsii_name="resetVersionStage")
    def reset_version_stage(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVersionStage", []))

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
    @jsii.member(jsii_name="arn")
    def arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "arn"))

    @builtins.property
    @jsii.member(jsii_name="createdDate")
    def created_date(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createdDate"))

    @builtins.property
    @jsii.member(jsii_name="secretBinary")
    def secret_binary(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretBinary"))

    @builtins.property
    @jsii.member(jsii_name="secretString")
    def secret_string(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretString"))

    @builtins.property
    @jsii.member(jsii_name="versionStages")
    def version_stages(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "versionStages"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="secretIdInput")
    def secret_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "secretIdInput"))

    @builtins.property
    @jsii.member(jsii_name="versionIdInput")
    def version_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "versionIdInput"))

    @builtins.property
    @jsii.member(jsii_name="versionStageInput")
    def version_stage_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "versionStageInput"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0c3fb0f3e6ec1c8c8403aefcf8142c2c2265608e4afcbb9b79417d886b04664)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1fa1819e1d7b2efdec6ba47f85903a53509adeddc77cb123729ac1a830bcd042)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="secretId")
    def secret_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretId"))

    @secret_id.setter
    def secret_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a7aae8709dbc7c9c0c7cec2de40dac0520235fb20bb37ebc595969f4e9959d11)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "secretId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="versionId")
    def version_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "versionId"))

    @version_id.setter
    def version_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc025fd5b443d288ce74030fe0b7cfa5d21acfed5887e8dc20a9c0a0ada9593e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "versionId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="versionStage")
    def version_stage(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "versionStage"))

    @version_stage.setter
    def version_stage(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d8fcc3aababa05e8f51bf362f8a08fde4c76146b84193445048b025d6cd1f03e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "versionStage", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dataAwsSecretsmanagerSecretVersion.DataAwsSecretsmanagerSecretVersionConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "secret_id": "secretId",
        "id": "id",
        "region": "region",
        "version_id": "versionId",
        "version_stage": "versionStage",
    },
)
class DataAwsSecretsmanagerSecretVersionConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        secret_id: builtins.str,
        id: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
        version_id: typing.Optional[builtins.str] = None,
        version_stage: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param secret_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#secret_id DataAwsSecretsmanagerSecretVersion#secret_id}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#id DataAwsSecretsmanagerSecretVersion#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#region DataAwsSecretsmanagerSecretVersion#region}
        :param version_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_id DataAwsSecretsmanagerSecretVersion#version_id}.
        :param version_stage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_stage DataAwsSecretsmanagerSecretVersion#version_stage}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e20a1e1b68a2641d61b8e687aa77d34a0a9c994c81baaa276de45cb5de62101d)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument secret_id", value=secret_id, expected_type=type_hints["secret_id"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument version_id", value=version_id, expected_type=type_hints["version_id"])
            check_type(argname="argument version_stage", value=version_stage, expected_type=type_hints["version_stage"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "secret_id": secret_id,
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
        if id is not None:
            self._values["id"] = id
        if region is not None:
            self._values["region"] = region
        if version_id is not None:
            self._values["version_id"] = version_id
        if version_stage is not None:
            self._values["version_stage"] = version_stage

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
    def secret_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#secret_id DataAwsSecretsmanagerSecretVersion#secret_id}.'''
        result = self._values.get("secret_id")
        assert result is not None, "Required property 'secret_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#id DataAwsSecretsmanagerSecretVersion#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#region DataAwsSecretsmanagerSecretVersion#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_id DataAwsSecretsmanagerSecretVersion#version_id}.'''
        result = self._values.get("version_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version_stage(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/data-sources/secretsmanager_secret_version#version_stage DataAwsSecretsmanagerSecretVersion#version_stage}.'''
        result = self._values.get("version_stage")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAwsSecretsmanagerSecretVersionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DataAwsSecretsmanagerSecretVersion",
    "DataAwsSecretsmanagerSecretVersionConfig",
]

publication.publish()

def _typecheckingstub__728e71d67f44501776c20bdf9a11a07294fa1b159681e9568da07681efc46005(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    secret_id: builtins.str,
    id: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
    version_id: typing.Optional[builtins.str] = None,
    version_stage: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__10f3115000d98976499483215efc36c61f6c08a2d204337aaeb1711b2dcf05d2(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0c3fb0f3e6ec1c8c8403aefcf8142c2c2265608e4afcbb9b79417d886b04664(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1fa1819e1d7b2efdec6ba47f85903a53509adeddc77cb123729ac1a830bcd042(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a7aae8709dbc7c9c0c7cec2de40dac0520235fb20bb37ebc595969f4e9959d11(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc025fd5b443d288ce74030fe0b7cfa5d21acfed5887e8dc20a9c0a0ada9593e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d8fcc3aababa05e8f51bf362f8a08fde4c76146b84193445048b025d6cd1f03e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e20a1e1b68a2641d61b8e687aa77d34a0a9c994c81baaa276de45cb5de62101d(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    secret_id: builtins.str,
    id: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
    version_id: typing.Optional[builtins.str] = None,
    version_stage: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
