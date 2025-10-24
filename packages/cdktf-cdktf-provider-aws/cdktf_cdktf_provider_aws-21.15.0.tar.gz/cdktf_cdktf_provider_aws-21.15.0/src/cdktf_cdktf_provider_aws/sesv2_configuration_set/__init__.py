r'''
# `aws_sesv2_configuration_set`

Refer to the Terraform Registry for docs: [`aws_sesv2_configuration_set`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set).
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


class Sesv2ConfigurationSet(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSet",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set aws_sesv2_configuration_set}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        configuration_set_name: builtins.str,
        delivery_options: typing.Optional[typing.Union["Sesv2ConfigurationSetDeliveryOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        id: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
        reputation_options: typing.Optional[typing.Union["Sesv2ConfigurationSetReputationOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        sending_options: typing.Optional[typing.Union["Sesv2ConfigurationSetSendingOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        suppression_options: typing.Optional[typing.Union["Sesv2ConfigurationSetSuppressionOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tracking_options: typing.Optional[typing.Union["Sesv2ConfigurationSetTrackingOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        vdm_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set aws_sesv2_configuration_set} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param configuration_set_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#configuration_set_name Sesv2ConfigurationSet#configuration_set_name}.
        :param delivery_options: delivery_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#delivery_options Sesv2ConfigurationSet#delivery_options}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#id Sesv2ConfigurationSet#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#region Sesv2ConfigurationSet#region}
        :param reputation_options: reputation_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_options Sesv2ConfigurationSet#reputation_options}
        :param sending_options: sending_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_options Sesv2ConfigurationSet#sending_options}
        :param suppression_options: suppression_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppression_options Sesv2ConfigurationSet#suppression_options}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags Sesv2ConfigurationSet#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags_all Sesv2ConfigurationSet#tags_all}.
        :param tracking_options: tracking_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tracking_options Sesv2ConfigurationSet#tracking_options}
        :param vdm_options: vdm_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#vdm_options Sesv2ConfigurationSet#vdm_options}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__baf007270f123048830e49301d054d2e72384c99ecec1f1e83294741f3aed33f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = Sesv2ConfigurationSetConfig(
            configuration_set_name=configuration_set_name,
            delivery_options=delivery_options,
            id=id,
            region=region,
            reputation_options=reputation_options,
            sending_options=sending_options,
            suppression_options=suppression_options,
            tags=tags,
            tags_all=tags_all,
            tracking_options=tracking_options,
            vdm_options=vdm_options,
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
        '''Generates CDKTF code for importing a Sesv2ConfigurationSet resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the Sesv2ConfigurationSet to import.
        :param import_from_id: The id of the existing Sesv2ConfigurationSet that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the Sesv2ConfigurationSet to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fe5481b3b536b4c03964649b6e1503623e652ad8c0e6f422ddbae2ce8c5ca244)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putDeliveryOptions")
    def put_delivery_options(
        self,
        *,
        max_delivery_seconds: typing.Optional[jsii.Number] = None,
        sending_pool_name: typing.Optional[builtins.str] = None,
        tls_policy: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_delivery_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#max_delivery_seconds Sesv2ConfigurationSet#max_delivery_seconds}.
        :param sending_pool_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_pool_name Sesv2ConfigurationSet#sending_pool_name}.
        :param tls_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tls_policy Sesv2ConfigurationSet#tls_policy}.
        '''
        value = Sesv2ConfigurationSetDeliveryOptions(
            max_delivery_seconds=max_delivery_seconds,
            sending_pool_name=sending_pool_name,
            tls_policy=tls_policy,
        )

        return typing.cast(None, jsii.invoke(self, "putDeliveryOptions", [value]))

    @jsii.member(jsii_name="putReputationOptions")
    def put_reputation_options(
        self,
        *,
        reputation_metrics_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param reputation_metrics_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_metrics_enabled Sesv2ConfigurationSet#reputation_metrics_enabled}.
        '''
        value = Sesv2ConfigurationSetReputationOptions(
            reputation_metrics_enabled=reputation_metrics_enabled
        )

        return typing.cast(None, jsii.invoke(self, "putReputationOptions", [value]))

    @jsii.member(jsii_name="putSendingOptions")
    def put_sending_options(
        self,
        *,
        sending_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param sending_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_enabled Sesv2ConfigurationSet#sending_enabled}.
        '''
        value = Sesv2ConfigurationSetSendingOptions(sending_enabled=sending_enabled)

        return typing.cast(None, jsii.invoke(self, "putSendingOptions", [value]))

    @jsii.member(jsii_name="putSuppressionOptions")
    def put_suppression_options(
        self,
        *,
        suppressed_reasons: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param suppressed_reasons: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppressed_reasons Sesv2ConfigurationSet#suppressed_reasons}.
        '''
        value = Sesv2ConfigurationSetSuppressionOptions(
            suppressed_reasons=suppressed_reasons
        )

        return typing.cast(None, jsii.invoke(self, "putSuppressionOptions", [value]))

    @jsii.member(jsii_name="putTrackingOptions")
    def put_tracking_options(
        self,
        *,
        custom_redirect_domain: builtins.str,
        https_policy: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param custom_redirect_domain: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#custom_redirect_domain Sesv2ConfigurationSet#custom_redirect_domain}.
        :param https_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#https_policy Sesv2ConfigurationSet#https_policy}.
        '''
        value = Sesv2ConfigurationSetTrackingOptions(
            custom_redirect_domain=custom_redirect_domain, https_policy=https_policy
        )

        return typing.cast(None, jsii.invoke(self, "putTrackingOptions", [value]))

    @jsii.member(jsii_name="putVdmOptions")
    def put_vdm_options(
        self,
        *,
        dashboard_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptionsDashboardOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        guardian_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptionsGuardianOptions", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param dashboard_options: dashboard_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#dashboard_options Sesv2ConfigurationSet#dashboard_options}
        :param guardian_options: guardian_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#guardian_options Sesv2ConfigurationSet#guardian_options}
        '''
        value = Sesv2ConfigurationSetVdmOptions(
            dashboard_options=dashboard_options, guardian_options=guardian_options
        )

        return typing.cast(None, jsii.invoke(self, "putVdmOptions", [value]))

    @jsii.member(jsii_name="resetDeliveryOptions")
    def reset_delivery_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeliveryOptions", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetReputationOptions")
    def reset_reputation_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReputationOptions", []))

    @jsii.member(jsii_name="resetSendingOptions")
    def reset_sending_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSendingOptions", []))

    @jsii.member(jsii_name="resetSuppressionOptions")
    def reset_suppression_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSuppressionOptions", []))

    @jsii.member(jsii_name="resetTags")
    def reset_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTags", []))

    @jsii.member(jsii_name="resetTagsAll")
    def reset_tags_all(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTagsAll", []))

    @jsii.member(jsii_name="resetTrackingOptions")
    def reset_tracking_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTrackingOptions", []))

    @jsii.member(jsii_name="resetVdmOptions")
    def reset_vdm_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVdmOptions", []))

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
    @jsii.member(jsii_name="deliveryOptions")
    def delivery_options(self) -> "Sesv2ConfigurationSetDeliveryOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetDeliveryOptionsOutputReference", jsii.get(self, "deliveryOptions"))

    @builtins.property
    @jsii.member(jsii_name="reputationOptions")
    def reputation_options(
        self,
    ) -> "Sesv2ConfigurationSetReputationOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetReputationOptionsOutputReference", jsii.get(self, "reputationOptions"))

    @builtins.property
    @jsii.member(jsii_name="sendingOptions")
    def sending_options(self) -> "Sesv2ConfigurationSetSendingOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetSendingOptionsOutputReference", jsii.get(self, "sendingOptions"))

    @builtins.property
    @jsii.member(jsii_name="suppressionOptions")
    def suppression_options(
        self,
    ) -> "Sesv2ConfigurationSetSuppressionOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetSuppressionOptionsOutputReference", jsii.get(self, "suppressionOptions"))

    @builtins.property
    @jsii.member(jsii_name="trackingOptions")
    def tracking_options(self) -> "Sesv2ConfigurationSetTrackingOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetTrackingOptionsOutputReference", jsii.get(self, "trackingOptions"))

    @builtins.property
    @jsii.member(jsii_name="vdmOptions")
    def vdm_options(self) -> "Sesv2ConfigurationSetVdmOptionsOutputReference":
        return typing.cast("Sesv2ConfigurationSetVdmOptionsOutputReference", jsii.get(self, "vdmOptions"))

    @builtins.property
    @jsii.member(jsii_name="configurationSetNameInput")
    def configuration_set_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "configurationSetNameInput"))

    @builtins.property
    @jsii.member(jsii_name="deliveryOptionsInput")
    def delivery_options_input(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetDeliveryOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetDeliveryOptions"], jsii.get(self, "deliveryOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="reputationOptionsInput")
    def reputation_options_input(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetReputationOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetReputationOptions"], jsii.get(self, "reputationOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="sendingOptionsInput")
    def sending_options_input(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetSendingOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetSendingOptions"], jsii.get(self, "sendingOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="suppressionOptionsInput")
    def suppression_options_input(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetSuppressionOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetSuppressionOptions"], jsii.get(self, "suppressionOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="tagsAllInput")
    def tags_all_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tagsAllInput"))

    @builtins.property
    @jsii.member(jsii_name="tagsInput")
    def tags_input(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tagsInput"))

    @builtins.property
    @jsii.member(jsii_name="trackingOptionsInput")
    def tracking_options_input(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetTrackingOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetTrackingOptions"], jsii.get(self, "trackingOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="vdmOptionsInput")
    def vdm_options_input(self) -> typing.Optional["Sesv2ConfigurationSetVdmOptions"]:
        return typing.cast(typing.Optional["Sesv2ConfigurationSetVdmOptions"], jsii.get(self, "vdmOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="configurationSetName")
    def configuration_set_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "configurationSetName"))

    @configuration_set_name.setter
    def configuration_set_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6a522c9555452bf402e838825d026641b859571401e42d823d450072a286afc8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "configurationSetName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0915bea0826e1646b317a0531caf039e47308f84ce79129d55ce8767ac14f32)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__842cceb592bb86f6e5f2ec449cfd7ad6b192d123ff117b2aab02b734d5f89b35)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__add4fcb5eb90d4b5990cdb736c1492adf59aa5ff847f50a82b9bb318c7d4bfec)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tagsAll")
    def tags_all(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tagsAll"))

    @tags_all.setter
    def tags_all(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96dbf6aff619ec9860ead3c192ab87e33d28c8f383c806e9af0de0b60b4fcb16)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tagsAll", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "configuration_set_name": "configurationSetName",
        "delivery_options": "deliveryOptions",
        "id": "id",
        "region": "region",
        "reputation_options": "reputationOptions",
        "sending_options": "sendingOptions",
        "suppression_options": "suppressionOptions",
        "tags": "tags",
        "tags_all": "tagsAll",
        "tracking_options": "trackingOptions",
        "vdm_options": "vdmOptions",
    },
)
class Sesv2ConfigurationSetConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        configuration_set_name: builtins.str,
        delivery_options: typing.Optional[typing.Union["Sesv2ConfigurationSetDeliveryOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        id: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
        reputation_options: typing.Optional[typing.Union["Sesv2ConfigurationSetReputationOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        sending_options: typing.Optional[typing.Union["Sesv2ConfigurationSetSendingOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        suppression_options: typing.Optional[typing.Union["Sesv2ConfigurationSetSuppressionOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tracking_options: typing.Optional[typing.Union["Sesv2ConfigurationSetTrackingOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        vdm_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptions", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param configuration_set_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#configuration_set_name Sesv2ConfigurationSet#configuration_set_name}.
        :param delivery_options: delivery_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#delivery_options Sesv2ConfigurationSet#delivery_options}
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#id Sesv2ConfigurationSet#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#region Sesv2ConfigurationSet#region}
        :param reputation_options: reputation_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_options Sesv2ConfigurationSet#reputation_options}
        :param sending_options: sending_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_options Sesv2ConfigurationSet#sending_options}
        :param suppression_options: suppression_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppression_options Sesv2ConfigurationSet#suppression_options}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags Sesv2ConfigurationSet#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags_all Sesv2ConfigurationSet#tags_all}.
        :param tracking_options: tracking_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tracking_options Sesv2ConfigurationSet#tracking_options}
        :param vdm_options: vdm_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#vdm_options Sesv2ConfigurationSet#vdm_options}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(delivery_options, dict):
            delivery_options = Sesv2ConfigurationSetDeliveryOptions(**delivery_options)
        if isinstance(reputation_options, dict):
            reputation_options = Sesv2ConfigurationSetReputationOptions(**reputation_options)
        if isinstance(sending_options, dict):
            sending_options = Sesv2ConfigurationSetSendingOptions(**sending_options)
        if isinstance(suppression_options, dict):
            suppression_options = Sesv2ConfigurationSetSuppressionOptions(**suppression_options)
        if isinstance(tracking_options, dict):
            tracking_options = Sesv2ConfigurationSetTrackingOptions(**tracking_options)
        if isinstance(vdm_options, dict):
            vdm_options = Sesv2ConfigurationSetVdmOptions(**vdm_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__551dd57c4e0900d691b0f51f0cb3f98b943f33c863d74b6017da5071f875bd44)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument configuration_set_name", value=configuration_set_name, expected_type=type_hints["configuration_set_name"])
            check_type(argname="argument delivery_options", value=delivery_options, expected_type=type_hints["delivery_options"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument reputation_options", value=reputation_options, expected_type=type_hints["reputation_options"])
            check_type(argname="argument sending_options", value=sending_options, expected_type=type_hints["sending_options"])
            check_type(argname="argument suppression_options", value=suppression_options, expected_type=type_hints["suppression_options"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument tags_all", value=tags_all, expected_type=type_hints["tags_all"])
            check_type(argname="argument tracking_options", value=tracking_options, expected_type=type_hints["tracking_options"])
            check_type(argname="argument vdm_options", value=vdm_options, expected_type=type_hints["vdm_options"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "configuration_set_name": configuration_set_name,
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
        if delivery_options is not None:
            self._values["delivery_options"] = delivery_options
        if id is not None:
            self._values["id"] = id
        if region is not None:
            self._values["region"] = region
        if reputation_options is not None:
            self._values["reputation_options"] = reputation_options
        if sending_options is not None:
            self._values["sending_options"] = sending_options
        if suppression_options is not None:
            self._values["suppression_options"] = suppression_options
        if tags is not None:
            self._values["tags"] = tags
        if tags_all is not None:
            self._values["tags_all"] = tags_all
        if tracking_options is not None:
            self._values["tracking_options"] = tracking_options
        if vdm_options is not None:
            self._values["vdm_options"] = vdm_options

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
    def configuration_set_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#configuration_set_name Sesv2ConfigurationSet#configuration_set_name}.'''
        result = self._values.get("configuration_set_name")
        assert result is not None, "Required property 'configuration_set_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def delivery_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetDeliveryOptions"]:
        '''delivery_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#delivery_options Sesv2ConfigurationSet#delivery_options}
        '''
        result = self._values.get("delivery_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetDeliveryOptions"], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#id Sesv2ConfigurationSet#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#region Sesv2ConfigurationSet#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def reputation_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetReputationOptions"]:
        '''reputation_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_options Sesv2ConfigurationSet#reputation_options}
        '''
        result = self._values.get("reputation_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetReputationOptions"], result)

    @builtins.property
    def sending_options(self) -> typing.Optional["Sesv2ConfigurationSetSendingOptions"]:
        '''sending_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_options Sesv2ConfigurationSet#sending_options}
        '''
        result = self._values.get("sending_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetSendingOptions"], result)

    @builtins.property
    def suppression_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetSuppressionOptions"]:
        '''suppression_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppression_options Sesv2ConfigurationSet#suppression_options}
        '''
        result = self._values.get("suppression_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetSuppressionOptions"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags Sesv2ConfigurationSet#tags}.'''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def tags_all(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tags_all Sesv2ConfigurationSet#tags_all}.'''
        result = self._values.get("tags_all")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def tracking_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetTrackingOptions"]:
        '''tracking_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tracking_options Sesv2ConfigurationSet#tracking_options}
        '''
        result = self._values.get("tracking_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetTrackingOptions"], result)

    @builtins.property
    def vdm_options(self) -> typing.Optional["Sesv2ConfigurationSetVdmOptions"]:
        '''vdm_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#vdm_options Sesv2ConfigurationSet#vdm_options}
        '''
        result = self._values.get("vdm_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetVdmOptions"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetDeliveryOptions",
    jsii_struct_bases=[],
    name_mapping={
        "max_delivery_seconds": "maxDeliverySeconds",
        "sending_pool_name": "sendingPoolName",
        "tls_policy": "tlsPolicy",
    },
)
class Sesv2ConfigurationSetDeliveryOptions:
    def __init__(
        self,
        *,
        max_delivery_seconds: typing.Optional[jsii.Number] = None,
        sending_pool_name: typing.Optional[builtins.str] = None,
        tls_policy: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_delivery_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#max_delivery_seconds Sesv2ConfigurationSet#max_delivery_seconds}.
        :param sending_pool_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_pool_name Sesv2ConfigurationSet#sending_pool_name}.
        :param tls_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tls_policy Sesv2ConfigurationSet#tls_policy}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff8cc5fa340cf0914eefdaa632b6593d50057cd870c6a1510b2843b897e0f910)
            check_type(argname="argument max_delivery_seconds", value=max_delivery_seconds, expected_type=type_hints["max_delivery_seconds"])
            check_type(argname="argument sending_pool_name", value=sending_pool_name, expected_type=type_hints["sending_pool_name"])
            check_type(argname="argument tls_policy", value=tls_policy, expected_type=type_hints["tls_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if max_delivery_seconds is not None:
            self._values["max_delivery_seconds"] = max_delivery_seconds
        if sending_pool_name is not None:
            self._values["sending_pool_name"] = sending_pool_name
        if tls_policy is not None:
            self._values["tls_policy"] = tls_policy

    @builtins.property
    def max_delivery_seconds(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#max_delivery_seconds Sesv2ConfigurationSet#max_delivery_seconds}.'''
        result = self._values.get("max_delivery_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def sending_pool_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_pool_name Sesv2ConfigurationSet#sending_pool_name}.'''
        result = self._values.get("sending_pool_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tls_policy(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#tls_policy Sesv2ConfigurationSet#tls_policy}.'''
        result = self._values.get("tls_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetDeliveryOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetDeliveryOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetDeliveryOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__351d1e43f32835167c7004ac473cf288a4b9237fd22af3963735edf645864d24)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetMaxDeliverySeconds")
    def reset_max_delivery_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxDeliverySeconds", []))

    @jsii.member(jsii_name="resetSendingPoolName")
    def reset_sending_pool_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSendingPoolName", []))

    @jsii.member(jsii_name="resetTlsPolicy")
    def reset_tls_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTlsPolicy", []))

    @builtins.property
    @jsii.member(jsii_name="maxDeliverySecondsInput")
    def max_delivery_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxDeliverySecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="sendingPoolNameInput")
    def sending_pool_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sendingPoolNameInput"))

    @builtins.property
    @jsii.member(jsii_name="tlsPolicyInput")
    def tls_policy_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tlsPolicyInput"))

    @builtins.property
    @jsii.member(jsii_name="maxDeliverySeconds")
    def max_delivery_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxDeliverySeconds"))

    @max_delivery_seconds.setter
    def max_delivery_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e18b3dc520edda55eeb4bf951c8302203ce24529cd707ab264fddc69b1c49373)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxDeliverySeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sendingPoolName")
    def sending_pool_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sendingPoolName"))

    @sending_pool_name.setter
    def sending_pool_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f7b5f7e86498db53da611738876bee0fa548782317cf2df24e2d67391e37c58)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sendingPoolName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tlsPolicy")
    def tls_policy(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tlsPolicy"))

    @tls_policy.setter
    def tls_policy(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d8b634b8414bc372db19a2e9456c48d753f6a0430b37dc012315c58144e285e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tlsPolicy", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[Sesv2ConfigurationSetDeliveryOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetDeliveryOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetDeliveryOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a4826b817264fa4e705540f08566cf1395fe51ac53a0f5a2f9f9af47a150fde3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetReputationOptions",
    jsii_struct_bases=[],
    name_mapping={"reputation_metrics_enabled": "reputationMetricsEnabled"},
)
class Sesv2ConfigurationSetReputationOptions:
    def __init__(
        self,
        *,
        reputation_metrics_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param reputation_metrics_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_metrics_enabled Sesv2ConfigurationSet#reputation_metrics_enabled}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6bcba3fe11f414e4f12765f1e56e5cfaf4bb72354d02b80feb1550a573e2624b)
            check_type(argname="argument reputation_metrics_enabled", value=reputation_metrics_enabled, expected_type=type_hints["reputation_metrics_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if reputation_metrics_enabled is not None:
            self._values["reputation_metrics_enabled"] = reputation_metrics_enabled

    @builtins.property
    def reputation_metrics_enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#reputation_metrics_enabled Sesv2ConfigurationSet#reputation_metrics_enabled}.'''
        result = self._values.get("reputation_metrics_enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetReputationOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetReputationOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetReputationOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__710105199ed1a0f9b6d5ddea24accfc9a00fc15f6d7f0347ed90aecd37f2369b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetReputationMetricsEnabled")
    def reset_reputation_metrics_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReputationMetricsEnabled", []))

    @builtins.property
    @jsii.member(jsii_name="lastFreshStart")
    def last_fresh_start(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lastFreshStart"))

    @builtins.property
    @jsii.member(jsii_name="reputationMetricsEnabledInput")
    def reputation_metrics_enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "reputationMetricsEnabledInput"))

    @builtins.property
    @jsii.member(jsii_name="reputationMetricsEnabled")
    def reputation_metrics_enabled(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "reputationMetricsEnabled"))

    @reputation_metrics_enabled.setter
    def reputation_metrics_enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d4318b2ec7b62e2c2102d7eef8ac92173b09aa744c50fa5e0269538ad3290401)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "reputationMetricsEnabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[Sesv2ConfigurationSetReputationOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetReputationOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetReputationOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__64b555a7f682b6a2c7a117d454c4ab7eaa8eb253d767303e6bfb398530601ac0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetSendingOptions",
    jsii_struct_bases=[],
    name_mapping={"sending_enabled": "sendingEnabled"},
)
class Sesv2ConfigurationSetSendingOptions:
    def __init__(
        self,
        *,
        sending_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param sending_enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_enabled Sesv2ConfigurationSet#sending_enabled}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d44d61b3d5867a54b15d366843bf346cf1a90eaa9c7f643a1821f1aa590fd58f)
            check_type(argname="argument sending_enabled", value=sending_enabled, expected_type=type_hints["sending_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if sending_enabled is not None:
            self._values["sending_enabled"] = sending_enabled

    @builtins.property
    def sending_enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#sending_enabled Sesv2ConfigurationSet#sending_enabled}.'''
        result = self._values.get("sending_enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetSendingOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetSendingOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetSendingOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__9c4a0deafe7a5411e4de0aa605a4e0b772dde74cdc23b06d06593fc3b576780a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetSendingEnabled")
    def reset_sending_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSendingEnabled", []))

    @builtins.property
    @jsii.member(jsii_name="sendingEnabledInput")
    def sending_enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "sendingEnabledInput"))

    @builtins.property
    @jsii.member(jsii_name="sendingEnabled")
    def sending_enabled(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "sendingEnabled"))

    @sending_enabled.setter
    def sending_enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3146601ef649a5fdf4e9ca7c8e74fc01870624972ed59e7878c6517eaf7975a4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sendingEnabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[Sesv2ConfigurationSetSendingOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetSendingOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetSendingOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__14400713b55efad1b57d1a8d23db4cb8f558ed1ad8d7199011ccae4f67089ef2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetSuppressionOptions",
    jsii_struct_bases=[],
    name_mapping={"suppressed_reasons": "suppressedReasons"},
)
class Sesv2ConfigurationSetSuppressionOptions:
    def __init__(
        self,
        *,
        suppressed_reasons: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param suppressed_reasons: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppressed_reasons Sesv2ConfigurationSet#suppressed_reasons}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b74634f0bd88c09883ba9cf0fae6bc6ffca892a00116ed9642f196c19a978467)
            check_type(argname="argument suppressed_reasons", value=suppressed_reasons, expected_type=type_hints["suppressed_reasons"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if suppressed_reasons is not None:
            self._values["suppressed_reasons"] = suppressed_reasons

    @builtins.property
    def suppressed_reasons(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#suppressed_reasons Sesv2ConfigurationSet#suppressed_reasons}.'''
        result = self._values.get("suppressed_reasons")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetSuppressionOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetSuppressionOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetSuppressionOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__f308b7dfe85099387f55aaaf51dc9edea1ece55562bad6cf158189f6c9baee5b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetSuppressedReasons")
    def reset_suppressed_reasons(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSuppressedReasons", []))

    @builtins.property
    @jsii.member(jsii_name="suppressedReasonsInput")
    def suppressed_reasons_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "suppressedReasonsInput"))

    @builtins.property
    @jsii.member(jsii_name="suppressedReasons")
    def suppressed_reasons(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "suppressedReasons"))

    @suppressed_reasons.setter
    def suppressed_reasons(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__179e0a3af11ef988d92f178c3dee102a5240a4cd61167ab89686f90de0855f72)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "suppressedReasons", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[Sesv2ConfigurationSetSuppressionOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetSuppressionOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetSuppressionOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b939cc8b82c3e57f756e76a61031c5dfd06504ff66d712783ca507751984c7b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetTrackingOptions",
    jsii_struct_bases=[],
    name_mapping={
        "custom_redirect_domain": "customRedirectDomain",
        "https_policy": "httpsPolicy",
    },
)
class Sesv2ConfigurationSetTrackingOptions:
    def __init__(
        self,
        *,
        custom_redirect_domain: builtins.str,
        https_policy: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param custom_redirect_domain: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#custom_redirect_domain Sesv2ConfigurationSet#custom_redirect_domain}.
        :param https_policy: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#https_policy Sesv2ConfigurationSet#https_policy}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0138bafb25f087d0f237ef2f5190819fd12dc07fd92fa84fa6876c0d76ea2041)
            check_type(argname="argument custom_redirect_domain", value=custom_redirect_domain, expected_type=type_hints["custom_redirect_domain"])
            check_type(argname="argument https_policy", value=https_policy, expected_type=type_hints["https_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "custom_redirect_domain": custom_redirect_domain,
        }
        if https_policy is not None:
            self._values["https_policy"] = https_policy

    @builtins.property
    def custom_redirect_domain(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#custom_redirect_domain Sesv2ConfigurationSet#custom_redirect_domain}.'''
        result = self._values.get("custom_redirect_domain")
        assert result is not None, "Required property 'custom_redirect_domain' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def https_policy(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#https_policy Sesv2ConfigurationSet#https_policy}.'''
        result = self._values.get("https_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetTrackingOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetTrackingOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetTrackingOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__be52f4c5f41c51c36df0a792e60fba47fadece5f237eef578f15d50c6d11be71)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetHttpsPolicy")
    def reset_https_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHttpsPolicy", []))

    @builtins.property
    @jsii.member(jsii_name="customRedirectDomainInput")
    def custom_redirect_domain_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customRedirectDomainInput"))

    @builtins.property
    @jsii.member(jsii_name="httpsPolicyInput")
    def https_policy_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "httpsPolicyInput"))

    @builtins.property
    @jsii.member(jsii_name="customRedirectDomain")
    def custom_redirect_domain(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customRedirectDomain"))

    @custom_redirect_domain.setter
    def custom_redirect_domain(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7be464b50fba85fb9af86bd25693e2bacae55ad4d72e43f859b8835b7597d459)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customRedirectDomain", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="httpsPolicy")
    def https_policy(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "httpsPolicy"))

    @https_policy.setter
    def https_policy(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5763f01eccd89bc680d887e37e0fd9e07fe252c95d49bf1dc6b4d9be2ac3fc1a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "httpsPolicy", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[Sesv2ConfigurationSetTrackingOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetTrackingOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetTrackingOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b6b3258f7b63a34deab0c74793823b03522e041eb63907412d3f30cd5767356b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptions",
    jsii_struct_bases=[],
    name_mapping={
        "dashboard_options": "dashboardOptions",
        "guardian_options": "guardianOptions",
    },
)
class Sesv2ConfigurationSetVdmOptions:
    def __init__(
        self,
        *,
        dashboard_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptionsDashboardOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        guardian_options: typing.Optional[typing.Union["Sesv2ConfigurationSetVdmOptionsGuardianOptions", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param dashboard_options: dashboard_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#dashboard_options Sesv2ConfigurationSet#dashboard_options}
        :param guardian_options: guardian_options block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#guardian_options Sesv2ConfigurationSet#guardian_options}
        '''
        if isinstance(dashboard_options, dict):
            dashboard_options = Sesv2ConfigurationSetVdmOptionsDashboardOptions(**dashboard_options)
        if isinstance(guardian_options, dict):
            guardian_options = Sesv2ConfigurationSetVdmOptionsGuardianOptions(**guardian_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e435843eb44599a2ab94b462dfa6a2113c08da358925082108c9fe907615f7b3)
            check_type(argname="argument dashboard_options", value=dashboard_options, expected_type=type_hints["dashboard_options"])
            check_type(argname="argument guardian_options", value=guardian_options, expected_type=type_hints["guardian_options"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dashboard_options is not None:
            self._values["dashboard_options"] = dashboard_options
        if guardian_options is not None:
            self._values["guardian_options"] = guardian_options

    @builtins.property
    def dashboard_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetVdmOptionsDashboardOptions"]:
        '''dashboard_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#dashboard_options Sesv2ConfigurationSet#dashboard_options}
        '''
        result = self._values.get("dashboard_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetVdmOptionsDashboardOptions"], result)

    @builtins.property
    def guardian_options(
        self,
    ) -> typing.Optional["Sesv2ConfigurationSetVdmOptionsGuardianOptions"]:
        '''guardian_options block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#guardian_options Sesv2ConfigurationSet#guardian_options}
        '''
        result = self._values.get("guardian_options")
        return typing.cast(typing.Optional["Sesv2ConfigurationSetVdmOptionsGuardianOptions"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetVdmOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptionsDashboardOptions",
    jsii_struct_bases=[],
    name_mapping={"engagement_metrics": "engagementMetrics"},
)
class Sesv2ConfigurationSetVdmOptionsDashboardOptions:
    def __init__(
        self,
        *,
        engagement_metrics: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param engagement_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#engagement_metrics Sesv2ConfigurationSet#engagement_metrics}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__59e8f26a0795ecd5157db39b31d0f939409dab2fac27a823a132fd390d823157)
            check_type(argname="argument engagement_metrics", value=engagement_metrics, expected_type=type_hints["engagement_metrics"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if engagement_metrics is not None:
            self._values["engagement_metrics"] = engagement_metrics

    @builtins.property
    def engagement_metrics(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#engagement_metrics Sesv2ConfigurationSet#engagement_metrics}.'''
        result = self._values.get("engagement_metrics")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetVdmOptionsDashboardOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetVdmOptionsDashboardOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptionsDashboardOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__2f0980874d715958297fd06f86fbeb025dc1063f3f1ad8b44f4237c8667bdc52)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetEngagementMetrics")
    def reset_engagement_metrics(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEngagementMetrics", []))

    @builtins.property
    @jsii.member(jsii_name="engagementMetricsInput")
    def engagement_metrics_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "engagementMetricsInput"))

    @builtins.property
    @jsii.member(jsii_name="engagementMetrics")
    def engagement_metrics(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "engagementMetrics"))

    @engagement_metrics.setter
    def engagement_metrics(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d8107593fcd6c38dd97d6f75829c33cf9d50b9c121275b3994b0679489e4a8b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "engagementMetrics", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a5768fab1208cc86f29c2c6a766b79094b4054116aaa44fcf1f4f3b6f63a96e0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptionsGuardianOptions",
    jsii_struct_bases=[],
    name_mapping={"optimized_shared_delivery": "optimizedSharedDelivery"},
)
class Sesv2ConfigurationSetVdmOptionsGuardianOptions:
    def __init__(
        self,
        *,
        optimized_shared_delivery: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param optimized_shared_delivery: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#optimized_shared_delivery Sesv2ConfigurationSet#optimized_shared_delivery}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1a10f712ec6bed4979c710794163f59abbef704c93bfa0155a80671ed26ffeb)
            check_type(argname="argument optimized_shared_delivery", value=optimized_shared_delivery, expected_type=type_hints["optimized_shared_delivery"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if optimized_shared_delivery is not None:
            self._values["optimized_shared_delivery"] = optimized_shared_delivery

    @builtins.property
    def optimized_shared_delivery(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#optimized_shared_delivery Sesv2ConfigurationSet#optimized_shared_delivery}.'''
        result = self._values.get("optimized_shared_delivery")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Sesv2ConfigurationSetVdmOptionsGuardianOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Sesv2ConfigurationSetVdmOptionsGuardianOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptionsGuardianOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__60b81a2bfdaccba0790d85e76914743dc0bb489f09b5bec9cc1798a7cb45735d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetOptimizedSharedDelivery")
    def reset_optimized_shared_delivery(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOptimizedSharedDelivery", []))

    @builtins.property
    @jsii.member(jsii_name="optimizedSharedDeliveryInput")
    def optimized_shared_delivery_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "optimizedSharedDeliveryInput"))

    @builtins.property
    @jsii.member(jsii_name="optimizedSharedDelivery")
    def optimized_shared_delivery(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "optimizedSharedDelivery"))

    @optimized_shared_delivery.setter
    def optimized_shared_delivery(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__29202a3c8098e96746f635ce582dc3ca2878066cd433b3cee93fd7d38d2c2dc1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "optimizedSharedDelivery", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f24b3b40ecf335e8529a3d2647268f639dbf09fbc7d6ee57bc7d1f4b29449754)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class Sesv2ConfigurationSetVdmOptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.sesv2ConfigurationSet.Sesv2ConfigurationSetVdmOptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__effd5c7b8057f24db0058df612989712d467a60c3210626fcf3d92a79e52a162)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putDashboardOptions")
    def put_dashboard_options(
        self,
        *,
        engagement_metrics: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param engagement_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#engagement_metrics Sesv2ConfigurationSet#engagement_metrics}.
        '''
        value = Sesv2ConfigurationSetVdmOptionsDashboardOptions(
            engagement_metrics=engagement_metrics
        )

        return typing.cast(None, jsii.invoke(self, "putDashboardOptions", [value]))

    @jsii.member(jsii_name="putGuardianOptions")
    def put_guardian_options(
        self,
        *,
        optimized_shared_delivery: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param optimized_shared_delivery: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/sesv2_configuration_set#optimized_shared_delivery Sesv2ConfigurationSet#optimized_shared_delivery}.
        '''
        value = Sesv2ConfigurationSetVdmOptionsGuardianOptions(
            optimized_shared_delivery=optimized_shared_delivery
        )

        return typing.cast(None, jsii.invoke(self, "putGuardianOptions", [value]))

    @jsii.member(jsii_name="resetDashboardOptions")
    def reset_dashboard_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDashboardOptions", []))

    @jsii.member(jsii_name="resetGuardianOptions")
    def reset_guardian_options(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetGuardianOptions", []))

    @builtins.property
    @jsii.member(jsii_name="dashboardOptions")
    def dashboard_options(
        self,
    ) -> Sesv2ConfigurationSetVdmOptionsDashboardOptionsOutputReference:
        return typing.cast(Sesv2ConfigurationSetVdmOptionsDashboardOptionsOutputReference, jsii.get(self, "dashboardOptions"))

    @builtins.property
    @jsii.member(jsii_name="guardianOptions")
    def guardian_options(
        self,
    ) -> Sesv2ConfigurationSetVdmOptionsGuardianOptionsOutputReference:
        return typing.cast(Sesv2ConfigurationSetVdmOptionsGuardianOptionsOutputReference, jsii.get(self, "guardianOptions"))

    @builtins.property
    @jsii.member(jsii_name="dashboardOptionsInput")
    def dashboard_options_input(
        self,
    ) -> typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions], jsii.get(self, "dashboardOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="guardianOptionsInput")
    def guardian_options_input(
        self,
    ) -> typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions], jsii.get(self, "guardianOptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[Sesv2ConfigurationSetVdmOptions]:
        return typing.cast(typing.Optional[Sesv2ConfigurationSetVdmOptions], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[Sesv2ConfigurationSetVdmOptions],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1158ce621f95d5cbce46a7113de532860fbc94d6a31913c5b4e95ef0fc424bb9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "Sesv2ConfigurationSet",
    "Sesv2ConfigurationSetConfig",
    "Sesv2ConfigurationSetDeliveryOptions",
    "Sesv2ConfigurationSetDeliveryOptionsOutputReference",
    "Sesv2ConfigurationSetReputationOptions",
    "Sesv2ConfigurationSetReputationOptionsOutputReference",
    "Sesv2ConfigurationSetSendingOptions",
    "Sesv2ConfigurationSetSendingOptionsOutputReference",
    "Sesv2ConfigurationSetSuppressionOptions",
    "Sesv2ConfigurationSetSuppressionOptionsOutputReference",
    "Sesv2ConfigurationSetTrackingOptions",
    "Sesv2ConfigurationSetTrackingOptionsOutputReference",
    "Sesv2ConfigurationSetVdmOptions",
    "Sesv2ConfigurationSetVdmOptionsDashboardOptions",
    "Sesv2ConfigurationSetVdmOptionsDashboardOptionsOutputReference",
    "Sesv2ConfigurationSetVdmOptionsGuardianOptions",
    "Sesv2ConfigurationSetVdmOptionsGuardianOptionsOutputReference",
    "Sesv2ConfigurationSetVdmOptionsOutputReference",
]

publication.publish()

def _typecheckingstub__baf007270f123048830e49301d054d2e72384c99ecec1f1e83294741f3aed33f(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    configuration_set_name: builtins.str,
    delivery_options: typing.Optional[typing.Union[Sesv2ConfigurationSetDeliveryOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    id: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
    reputation_options: typing.Optional[typing.Union[Sesv2ConfigurationSetReputationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    sending_options: typing.Optional[typing.Union[Sesv2ConfigurationSetSendingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    suppression_options: typing.Optional[typing.Union[Sesv2ConfigurationSetSuppressionOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tracking_options: typing.Optional[typing.Union[Sesv2ConfigurationSetTrackingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    vdm_options: typing.Optional[typing.Union[Sesv2ConfigurationSetVdmOptions, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__fe5481b3b536b4c03964649b6e1503623e652ad8c0e6f422ddbae2ce8c5ca244(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6a522c9555452bf402e838825d026641b859571401e42d823d450072a286afc8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0915bea0826e1646b317a0531caf039e47308f84ce79129d55ce8767ac14f32(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__842cceb592bb86f6e5f2ec449cfd7ad6b192d123ff117b2aab02b734d5f89b35(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__add4fcb5eb90d4b5990cdb736c1492adf59aa5ff847f50a82b9bb318c7d4bfec(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96dbf6aff619ec9860ead3c192ab87e33d28c8f383c806e9af0de0b60b4fcb16(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__551dd57c4e0900d691b0f51f0cb3f98b943f33c863d74b6017da5071f875bd44(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    configuration_set_name: builtins.str,
    delivery_options: typing.Optional[typing.Union[Sesv2ConfigurationSetDeliveryOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    id: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
    reputation_options: typing.Optional[typing.Union[Sesv2ConfigurationSetReputationOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    sending_options: typing.Optional[typing.Union[Sesv2ConfigurationSetSendingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    suppression_options: typing.Optional[typing.Union[Sesv2ConfigurationSetSuppressionOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tracking_options: typing.Optional[typing.Union[Sesv2ConfigurationSetTrackingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    vdm_options: typing.Optional[typing.Union[Sesv2ConfigurationSetVdmOptions, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff8cc5fa340cf0914eefdaa632b6593d50057cd870c6a1510b2843b897e0f910(
    *,
    max_delivery_seconds: typing.Optional[jsii.Number] = None,
    sending_pool_name: typing.Optional[builtins.str] = None,
    tls_policy: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__351d1e43f32835167c7004ac473cf288a4b9237fd22af3963735edf645864d24(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e18b3dc520edda55eeb4bf951c8302203ce24529cd707ab264fddc69b1c49373(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f7b5f7e86498db53da611738876bee0fa548782317cf2df24e2d67391e37c58(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d8b634b8414bc372db19a2e9456c48d753f6a0430b37dc012315c58144e285e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a4826b817264fa4e705540f08566cf1395fe51ac53a0f5a2f9f9af47a150fde3(
    value: typing.Optional[Sesv2ConfigurationSetDeliveryOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6bcba3fe11f414e4f12765f1e56e5cfaf4bb72354d02b80feb1550a573e2624b(
    *,
    reputation_metrics_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__710105199ed1a0f9b6d5ddea24accfc9a00fc15f6d7f0347ed90aecd37f2369b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d4318b2ec7b62e2c2102d7eef8ac92173b09aa744c50fa5e0269538ad3290401(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__64b555a7f682b6a2c7a117d454c4ab7eaa8eb253d767303e6bfb398530601ac0(
    value: typing.Optional[Sesv2ConfigurationSetReputationOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d44d61b3d5867a54b15d366843bf346cf1a90eaa9c7f643a1821f1aa590fd58f(
    *,
    sending_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c4a0deafe7a5411e4de0aa605a4e0b772dde74cdc23b06d06593fc3b576780a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3146601ef649a5fdf4e9ca7c8e74fc01870624972ed59e7878c6517eaf7975a4(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__14400713b55efad1b57d1a8d23db4cb8f558ed1ad8d7199011ccae4f67089ef2(
    value: typing.Optional[Sesv2ConfigurationSetSendingOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b74634f0bd88c09883ba9cf0fae6bc6ffca892a00116ed9642f196c19a978467(
    *,
    suppressed_reasons: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f308b7dfe85099387f55aaaf51dc9edea1ece55562bad6cf158189f6c9baee5b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__179e0a3af11ef988d92f178c3dee102a5240a4cd61167ab89686f90de0855f72(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b939cc8b82c3e57f756e76a61031c5dfd06504ff66d712783ca507751984c7b(
    value: typing.Optional[Sesv2ConfigurationSetSuppressionOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0138bafb25f087d0f237ef2f5190819fd12dc07fd92fa84fa6876c0d76ea2041(
    *,
    custom_redirect_domain: builtins.str,
    https_policy: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be52f4c5f41c51c36df0a792e60fba47fadece5f237eef578f15d50c6d11be71(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7be464b50fba85fb9af86bd25693e2bacae55ad4d72e43f859b8835b7597d459(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5763f01eccd89bc680d887e37e0fd9e07fe252c95d49bf1dc6b4d9be2ac3fc1a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b6b3258f7b63a34deab0c74793823b03522e041eb63907412d3f30cd5767356b(
    value: typing.Optional[Sesv2ConfigurationSetTrackingOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e435843eb44599a2ab94b462dfa6a2113c08da358925082108c9fe907615f7b3(
    *,
    dashboard_options: typing.Optional[typing.Union[Sesv2ConfigurationSetVdmOptionsDashboardOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    guardian_options: typing.Optional[typing.Union[Sesv2ConfigurationSetVdmOptionsGuardianOptions, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__59e8f26a0795ecd5157db39b31d0f939409dab2fac27a823a132fd390d823157(
    *,
    engagement_metrics: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f0980874d715958297fd06f86fbeb025dc1063f3f1ad8b44f4237c8667bdc52(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d8107593fcd6c38dd97d6f75829c33cf9d50b9c121275b3994b0679489e4a8b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a5768fab1208cc86f29c2c6a766b79094b4054116aaa44fcf1f4f3b6f63a96e0(
    value: typing.Optional[Sesv2ConfigurationSetVdmOptionsDashboardOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1a10f712ec6bed4979c710794163f59abbef704c93bfa0155a80671ed26ffeb(
    *,
    optimized_shared_delivery: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__60b81a2bfdaccba0790d85e76914743dc0bb489f09b5bec9cc1798a7cb45735d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__29202a3c8098e96746f635ce582dc3ca2878066cd433b3cee93fd7d38d2c2dc1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f24b3b40ecf335e8529a3d2647268f639dbf09fbc7d6ee57bc7d1f4b29449754(
    value: typing.Optional[Sesv2ConfigurationSetVdmOptionsGuardianOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__effd5c7b8057f24db0058df612989712d467a60c3210626fcf3d92a79e52a162(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1158ce621f95d5cbce46a7113de532860fbc94d6a31913c5b4e95ef0fc424bb9(
    value: typing.Optional[Sesv2ConfigurationSetVdmOptions],
) -> None:
    """Type checking stubs"""
    pass
