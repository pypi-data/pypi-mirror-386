r'''
# `aws_resiliencehub_resiliency_policy`

Refer to the Terraform Registry for docs: [`aws_resiliencehub_resiliency_policy`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy).
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


class ResiliencehubResiliencyPolicy(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicy",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy aws_resiliencehub_resiliency_policy}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        name: builtins.str,
        tier: builtins.str,
        data_location_constraint: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        policy: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicy", typing.Dict[builtins.str, typing.Any]]]]] = None,
        region: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union["ResiliencehubResiliencyPolicyTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy aws_resiliencehub_resiliency_policy} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param name: The name of the policy. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#name ResiliencehubResiliencyPolicy#name}
        :param tier: The tier for the resiliency policy, ranging from the highest severity (MissionCritical) to lowest (NonCritical). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tier ResiliencehubResiliencyPolicy#tier}
        :param data_location_constraint: Specifies a high-level geographical location constraint for where resilience policy data can be stored. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#data_location_constraint ResiliencehubResiliencyPolicy#data_location_constraint}
        :param description: The description for the policy. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#description ResiliencehubResiliencyPolicy#description}
        :param policy: policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#policy ResiliencehubResiliencyPolicy#policy}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#region ResiliencehubResiliencyPolicy#region}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tags ResiliencehubResiliencyPolicy#tags}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#timeouts ResiliencehubResiliencyPolicy#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c9e99c1ff36d47086ecb56d7791c244413fbf187ce9822bc5a72b8064bfccb86)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = ResiliencehubResiliencyPolicyConfig(
            name=name,
            tier=tier,
            data_location_constraint=data_location_constraint,
            description=description,
            policy=policy,
            region=region,
            tags=tags,
            timeouts=timeouts,
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
        '''Generates CDKTF code for importing a ResiliencehubResiliencyPolicy resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the ResiliencehubResiliencyPolicy to import.
        :param import_from_id: The id of the existing ResiliencehubResiliencyPolicy that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the ResiliencehubResiliencyPolicy to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3cc0b760e72e60356d0f3953280548cf558844e394cfd913cf5742baed7fdeb)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putPolicy")
    def put_policy(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicy", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6fffb7be936d59f6f45febf26e5d377d2081e82f0ff4aef35ba2459dc6455ff6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putPolicy", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#create ResiliencehubResiliencyPolicy#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#delete ResiliencehubResiliencyPolicy#delete}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#update ResiliencehubResiliencyPolicy#update}
        '''
        value = ResiliencehubResiliencyPolicyTimeouts(
            create=create, delete=delete, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetDataLocationConstraint")
    def reset_data_location_constraint(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDataLocationConstraint", []))

    @jsii.member(jsii_name="resetDescription")
    def reset_description(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDescription", []))

    @jsii.member(jsii_name="resetPolicy")
    def reset_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPolicy", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetTags")
    def reset_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTags", []))

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
    @jsii.member(jsii_name="arn")
    def arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "arn"))

    @builtins.property
    @jsii.member(jsii_name="estimatedCostTier")
    def estimated_cost_tier(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "estimatedCostTier"))

    @builtins.property
    @jsii.member(jsii_name="policy")
    def policy(self) -> "ResiliencehubResiliencyPolicyPolicyList":
        return typing.cast("ResiliencehubResiliencyPolicyPolicyList", jsii.get(self, "policy"))

    @builtins.property
    @jsii.member(jsii_name="tagsAll")
    def tags_all(self) -> _cdktf_9a9027ec.StringMap:
        return typing.cast(_cdktf_9a9027ec.StringMap, jsii.get(self, "tagsAll"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> "ResiliencehubResiliencyPolicyTimeoutsOutputReference":
        return typing.cast("ResiliencehubResiliencyPolicyTimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="dataLocationConstraintInput")
    def data_location_constraint_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "dataLocationConstraintInput"))

    @builtins.property
    @jsii.member(jsii_name="descriptionInput")
    def description_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "descriptionInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="policyInput")
    def policy_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicy"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicy"]]], jsii.get(self, "policyInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="tagsInput")
    def tags_input(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tagsInput"))

    @builtins.property
    @jsii.member(jsii_name="tierInput")
    def tier_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tierInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "ResiliencehubResiliencyPolicyTimeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "ResiliencehubResiliencyPolicyTimeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="dataLocationConstraint")
    def data_location_constraint(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "dataLocationConstraint"))

    @data_location_constraint.setter
    def data_location_constraint(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9e55d51c53720775ba8732a6483a22e6e1791a5aae43e16fb527f2935b1e2a97)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "dataLocationConstraint", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "description"))

    @description.setter
    def description(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae61b5173cb3bde2360a39dc0ac944d1589d67b891d57f7fbf5670b9f4057ec2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "description", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2cf76771c68f9b1661136f8293d6fe7b472389a93196b6ddbf8071c3ab1aee8f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f09e3c85b929c5e6c0400252320ac41b527a15fead1889a3883d4821885fe4c1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5829cf7387b89c8a4e38180b2cb66f8e204ad74b7eb8ef59c22907c83abacff9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tier")
    def tier(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tier"))

    @tier.setter
    def tier(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b92780750f5804f60f5f4f0dfa6d507b82690de7dc85bc614863d870c7715b46)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tier", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "name": "name",
        "tier": "tier",
        "data_location_constraint": "dataLocationConstraint",
        "description": "description",
        "policy": "policy",
        "region": "region",
        "tags": "tags",
        "timeouts": "timeouts",
    },
)
class ResiliencehubResiliencyPolicyConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        name: builtins.str,
        tier: builtins.str,
        data_location_constraint: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        policy: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicy", typing.Dict[builtins.str, typing.Any]]]]] = None,
        region: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union["ResiliencehubResiliencyPolicyTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param name: The name of the policy. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#name ResiliencehubResiliencyPolicy#name}
        :param tier: The tier for the resiliency policy, ranging from the highest severity (MissionCritical) to lowest (NonCritical). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tier ResiliencehubResiliencyPolicy#tier}
        :param data_location_constraint: Specifies a high-level geographical location constraint for where resilience policy data can be stored. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#data_location_constraint ResiliencehubResiliencyPolicy#data_location_constraint}
        :param description: The description for the policy. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#description ResiliencehubResiliencyPolicy#description}
        :param policy: policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#policy ResiliencehubResiliencyPolicy#policy}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#region ResiliencehubResiliencyPolicy#region}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tags ResiliencehubResiliencyPolicy#tags}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#timeouts ResiliencehubResiliencyPolicy#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(timeouts, dict):
            timeouts = ResiliencehubResiliencyPolicyTimeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f675e61147b3f18af31a4259cab39b5a06cac89b66f940390ca1596022a5ab8)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
            check_type(argname="argument data_location_constraint", value=data_location_constraint, expected_type=type_hints["data_location_constraint"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument policy", value=policy, expected_type=type_hints["policy"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "tier": tier,
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
        if data_location_constraint is not None:
            self._values["data_location_constraint"] = data_location_constraint
        if description is not None:
            self._values["description"] = description
        if policy is not None:
            self._values["policy"] = policy
        if region is not None:
            self._values["region"] = region
        if tags is not None:
            self._values["tags"] = tags
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
    def name(self) -> builtins.str:
        '''The name of the policy.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#name ResiliencehubResiliencyPolicy#name}
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def tier(self) -> builtins.str:
        '''The tier for the resiliency policy, ranging from the highest severity (MissionCritical) to lowest (NonCritical).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tier ResiliencehubResiliencyPolicy#tier}
        '''
        result = self._values.get("tier")
        assert result is not None, "Required property 'tier' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def data_location_constraint(self) -> typing.Optional[builtins.str]:
        '''Specifies a high-level geographical location constraint for where resilience policy data can be stored.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#data_location_constraint ResiliencehubResiliencyPolicy#data_location_constraint}
        '''
        result = self._values.get("data_location_constraint")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The description for the policy.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#description ResiliencehubResiliencyPolicy#description}
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def policy(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicy"]]]:
        '''policy block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#policy ResiliencehubResiliencyPolicy#policy}
        '''
        result = self._values.get("policy")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicy"]]], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#region ResiliencehubResiliencyPolicy#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#tags ResiliencehubResiliencyPolicy#tags}.'''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["ResiliencehubResiliencyPolicyTimeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#timeouts ResiliencehubResiliencyPolicy#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["ResiliencehubResiliencyPolicyTimeouts"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "az": "az",
        "hardware": "hardware",
        "region": "region",
        "software_attribute": "softwareAttribute",
    },
)
class ResiliencehubResiliencyPolicyPolicy:
    def __init__(
        self,
        *,
        az: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicyAz", typing.Dict[builtins.str, typing.Any]]]]] = None,
        hardware: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicyHardware", typing.Dict[builtins.str, typing.Any]]]]] = None,
        region: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicyRegion", typing.Dict[builtins.str, typing.Any]]]]] = None,
        software_attribute: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicySoftware", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param az: az block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#az ResiliencehubResiliencyPolicy#az}
        :param hardware: hardware block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#hardware ResiliencehubResiliencyPolicy#hardware}
        :param region: region block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#region ResiliencehubResiliencyPolicy#region}
        :param software_attribute: software block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#software ResiliencehubResiliencyPolicy#software}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dd4c505381b5a6e785622167132eb787d6afb5ef0ca19fa7da6079622f5c2c37)
            check_type(argname="argument az", value=az, expected_type=type_hints["az"])
            check_type(argname="argument hardware", value=hardware, expected_type=type_hints["hardware"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument software_attribute", value=software_attribute, expected_type=type_hints["software_attribute"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if az is not None:
            self._values["az"] = az
        if hardware is not None:
            self._values["hardware"] = hardware
        if region is not None:
            self._values["region"] = region
        if software_attribute is not None:
            self._values["software_attribute"] = software_attribute

    @builtins.property
    def az(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyAz"]]]:
        '''az block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#az ResiliencehubResiliencyPolicy#az}
        '''
        result = self._values.get("az")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyAz"]]], result)

    @builtins.property
    def hardware(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyHardware"]]]:
        '''hardware block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#hardware ResiliencehubResiliencyPolicy#hardware}
        '''
        result = self._values.get("hardware")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyHardware"]]], result)

    @builtins.property
    def region(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyRegion"]]]:
        '''region block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#region ResiliencehubResiliencyPolicy#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyRegion"]]], result)

    @builtins.property
    def software_attribute(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicySoftware"]]]:
        '''software block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#software ResiliencehubResiliencyPolicy#software}
        '''
        result = self._values.get("software_attribute")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicySoftware"]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyAz",
    jsii_struct_bases=[],
    name_mapping={"rpo": "rpo", "rto": "rto"},
)
class ResiliencehubResiliencyPolicyPolicyAz:
    def __init__(self, *, rpo: builtins.str, rto: builtins.str) -> None:
        '''
        :param rpo: Recovery Point Objective (RPO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        :param rto: Recovery Time Objective (RTO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a8655a9581fcc1e03dbec5161e8b58163d65775b97bd75dd2399d5cd9a359f4)
            check_type(argname="argument rpo", value=rpo, expected_type=type_hints["rpo"])
            check_type(argname="argument rto", value=rto, expected_type=type_hints["rto"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "rpo": rpo,
            "rto": rto,
        }

    @builtins.property
    def rpo(self) -> builtins.str:
        '''Recovery Point Objective (RPO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        '''
        result = self._values.get("rpo")
        assert result is not None, "Required property 'rpo' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rto(self) -> builtins.str:
        '''Recovery Time Objective (RTO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        result = self._values.get("rto")
        assert result is not None, "Required property 'rto' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyPolicyAz(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResiliencehubResiliencyPolicyPolicyAzList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyAzList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__679d833f5369da4f100a381b180a7be9c22c496bfdff3dd46e6232d0c6300049)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "ResiliencehubResiliencyPolicyPolicyAzOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b661547d00835fc27afbce6a71871b398df2d1b1573e6662b69efe937b7ff8e8)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("ResiliencehubResiliencyPolicyPolicyAzOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f310ff2c702620d6f57ede37685dcbf552075afec3ac58a27639a29b17b4e7f2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__814ad4c07737bc3ebef70625e3f06cea528fff2ca7c46fe100a6f2f2477354cc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__278b3f89bf3b5caaaa91a9b4fe9c38c28ee395a351c136abd80d73096db802a2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__33b3d691a828b0a56ea6c3d31f484b7b4a0100c7daee8ef4a37f5340ad1b070a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicyAzOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyAzOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2dd7838b2c0be10adaea06b31b08feb7a8e413e80979ac3a589572f4f9393009)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="rpoInput")
    def rpo_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rpoInput"))

    @builtins.property
    @jsii.member(jsii_name="rtoInput")
    def rto_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rtoInput"))

    @builtins.property
    @jsii.member(jsii_name="rpo")
    def rpo(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rpo"))

    @rpo.setter
    def rpo(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b30036d6f988f463b59121480fc860955c0281b0421b1acbd798673a5016975)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rpo", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="rto")
    def rto(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rto"))

    @rto.setter
    def rto(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68fa7f3f44e24715feaa5d3d84bc314bb22f3e219765d342a279e1a5bd9df697)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rto", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyAz]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyAz]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyAz]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4af275bfc83226a3cdc83adc2bccc44d61f1f96918aaaf70c260b196c5c5ec40)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyHardware",
    jsii_struct_bases=[],
    name_mapping={"rpo": "rpo", "rto": "rto"},
)
class ResiliencehubResiliencyPolicyPolicyHardware:
    def __init__(self, *, rpo: builtins.str, rto: builtins.str) -> None:
        '''
        :param rpo: Recovery Point Objective (RPO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        :param rto: Recovery Time Objective (RTO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d304688c7d5b31d8b67b1db80663c3a2dce1524a0addb31420491f5b851876e3)
            check_type(argname="argument rpo", value=rpo, expected_type=type_hints["rpo"])
            check_type(argname="argument rto", value=rto, expected_type=type_hints["rto"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "rpo": rpo,
            "rto": rto,
        }

    @builtins.property
    def rpo(self) -> builtins.str:
        '''Recovery Point Objective (RPO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        '''
        result = self._values.get("rpo")
        assert result is not None, "Required property 'rpo' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rto(self) -> builtins.str:
        '''Recovery Time Objective (RTO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        result = self._values.get("rto")
        assert result is not None, "Required property 'rto' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyPolicyHardware(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResiliencehubResiliencyPolicyPolicyHardwareList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyHardwareList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__db5697bc8894aa763d15aa1a0ebde740e71f53ca13c0f621428059187478004d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "ResiliencehubResiliencyPolicyPolicyHardwareOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aa0a84ebac2a6a00f64fe0df4cea04fb1eb22ff1c5b7df2d0e2586b863a3929d)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("ResiliencehubResiliencyPolicyPolicyHardwareOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5df2134bb4edacf6a0a28dd7305080e22b3dcec557d6241c78920a8919ce488)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fb3e2511b567a8ccdc8abac75910c30f44fe46a2fb038d94371d5ef3e91354dd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__80223d866aac52cb1a98bfe8c6b85fb19a60a3a88ad658c8b8b4629f5597002b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de0a060966a9c11ecb0f47e25a984b76500f8e7deeef7ccc2f0c1d0108ce9ff2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicyHardwareOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyHardwareOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf5ca04a38c3631e1fd0f00163f50823d1a238c78fa7fc690d505b2db2c82d55)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="rpoInput")
    def rpo_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rpoInput"))

    @builtins.property
    @jsii.member(jsii_name="rtoInput")
    def rto_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rtoInput"))

    @builtins.property
    @jsii.member(jsii_name="rpo")
    def rpo(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rpo"))

    @rpo.setter
    def rpo(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82cba5290eecb34e610279dbad53cc48e4ff793ad7e7c332bcca52bbcda1e272)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rpo", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="rto")
    def rto(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rto"))

    @rto.setter
    def rto(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3a4d53e3df88f25e703736d09ca2132907cc5735554e2165e2a3278a6902ff2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rto", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyHardware]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyHardware]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyHardware]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8bc763f1f4d3134b2bf66a50e81c3125dca164d718d5e54516a0a587b8bd6647)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicyList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5bf63334933e77f81b01459455c7de8ae61ceeb5ae1ad85ec496f4c600dcfe1)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "ResiliencehubResiliencyPolicyPolicyOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2043634cd03d444633261663eb0a1042c8c59be2d7308171018210a9645da3c)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("ResiliencehubResiliencyPolicyPolicyOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6eee76bf42c3a4718853e8ad788e409b7e8055429877433619071795eef9d451)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__146a690cbd68ee8ff251e63bfe29b7a3ad208125859b4c97ee2e49b83363f2e8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad9466d422482860dd651203e2eb94fe4c7cb526561801ce24d50eee1ee4327f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicy]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicy]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicy]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f08575213923f5484b3694491a749744fa778943bd97b2f5327bd0f11542faa4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicyOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13a393e81f29a7144e3b74adffe3c2b39d1ea71af98a5f4ccb727bf25df0b998)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="putAz")
    def put_az(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyAz, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7929d21b9bf0a006a7601bda6c86208dfb6218d44e48b4ea96d1a0edb4644b1c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putAz", [value]))

    @jsii.member(jsii_name="putHardware")
    def put_hardware(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyHardware, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__191222525c76721445e5654c9eda338e775208b35b836ec0419d61234a23844b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putHardware", [value]))

    @jsii.member(jsii_name="putRegion")
    def put_region(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicyRegion", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b241205e0d230ebe53db0bfec986d5d75920f9ab6bd0e7969c7b2b3845180ca)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putRegion", [value]))

    @jsii.member(jsii_name="putSoftwareAttribute")
    def put_software_attribute(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["ResiliencehubResiliencyPolicyPolicySoftware", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__14c4d3043a4234a009e51bc632761fea6bc1215841630e63ef735b205a66221b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putSoftwareAttribute", [value]))

    @jsii.member(jsii_name="resetAz")
    def reset_az(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAz", []))

    @jsii.member(jsii_name="resetHardware")
    def reset_hardware(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHardware", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetSoftwareAttribute")
    def reset_software_attribute(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSoftwareAttribute", []))

    @builtins.property
    @jsii.member(jsii_name="az")
    def az(self) -> ResiliencehubResiliencyPolicyPolicyAzList:
        return typing.cast(ResiliencehubResiliencyPolicyPolicyAzList, jsii.get(self, "az"))

    @builtins.property
    @jsii.member(jsii_name="hardware")
    def hardware(self) -> ResiliencehubResiliencyPolicyPolicyHardwareList:
        return typing.cast(ResiliencehubResiliencyPolicyPolicyHardwareList, jsii.get(self, "hardware"))

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> "ResiliencehubResiliencyPolicyPolicyRegionList":
        return typing.cast("ResiliencehubResiliencyPolicyPolicyRegionList", jsii.get(self, "region"))

    @builtins.property
    @jsii.member(jsii_name="softwareAttribute")
    def software_attribute(self) -> "ResiliencehubResiliencyPolicyPolicySoftwareList":
        return typing.cast("ResiliencehubResiliencyPolicyPolicySoftwareList", jsii.get(self, "softwareAttribute"))

    @builtins.property
    @jsii.member(jsii_name="azInput")
    def az_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]], jsii.get(self, "azInput"))

    @builtins.property
    @jsii.member(jsii_name="hardwareInput")
    def hardware_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]], jsii.get(self, "hardwareInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyRegion"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicyRegion"]]], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="softwareAttributeInput")
    def software_attribute_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicySoftware"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["ResiliencehubResiliencyPolicyPolicySoftware"]]], jsii.get(self, "softwareAttributeInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicy]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicy]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicy]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d061d2d03be3a3a1da686ce9c1b97c118e682960e191309735bf3d16e3ce8acc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyRegion",
    jsii_struct_bases=[],
    name_mapping={"rpo": "rpo", "rto": "rto"},
)
class ResiliencehubResiliencyPolicyPolicyRegion:
    def __init__(
        self,
        *,
        rpo: typing.Optional[builtins.str] = None,
        rto: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param rpo: Recovery Point Objective (RPO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        :param rto: Recovery Time Objective (RTO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__199ab28697b41234fdb3939f74a42b5b877f2ac1c2418dd1f1038d793f4509e4)
            check_type(argname="argument rpo", value=rpo, expected_type=type_hints["rpo"])
            check_type(argname="argument rto", value=rto, expected_type=type_hints["rto"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if rpo is not None:
            self._values["rpo"] = rpo
        if rto is not None:
            self._values["rto"] = rto

    @builtins.property
    def rpo(self) -> typing.Optional[builtins.str]:
        '''Recovery Point Objective (RPO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        '''
        result = self._values.get("rpo")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def rto(self) -> typing.Optional[builtins.str]:
        '''Recovery Time Objective (RTO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        result = self._values.get("rto")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyPolicyRegion(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResiliencehubResiliencyPolicyPolicyRegionList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyRegionList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7bc70747a69e7081bbfdfb522e15e8315e60ad8953a192bc3d45298274ced218)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "ResiliencehubResiliencyPolicyPolicyRegionOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__81f0eec0a2d7962c882ec653483fe47e945cd82e107c5174b51d064484953a41)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("ResiliencehubResiliencyPolicyPolicyRegionOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__30752767fd9306209e8c1b8f678509bd5ec9b2814ccd15eb526493b7cc9acad0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94d798b6e58e18fc24e70ce34e7f1f1c8e5c09f007d596979f9ccb8a4bffbb3a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aade1e452e3821d0be97a65867bc21b725191994850af8785ec4473c003d2f3a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyRegion]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyRegion]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyRegion]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f27cd9811bee2a717d1ad01d0ca9edfe02ccf814b95e516349039720c29e4f83)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicyRegionOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicyRegionOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__145f98dd670351106490f643d0ee7d25fa6ee6fde49f974c56aef88fcdb4ee56)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetRpo")
    def reset_rpo(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRpo", []))

    @jsii.member(jsii_name="resetRto")
    def reset_rto(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRto", []))

    @builtins.property
    @jsii.member(jsii_name="rpoInput")
    def rpo_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rpoInput"))

    @builtins.property
    @jsii.member(jsii_name="rtoInput")
    def rto_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rtoInput"))

    @builtins.property
    @jsii.member(jsii_name="rpo")
    def rpo(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rpo"))

    @rpo.setter
    def rpo(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b8b740e8fa7d80ab5de73a457b9f34532e6cc7bc3df5d1a2a2c48a18b274eed6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rpo", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="rto")
    def rto(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rto"))

    @rto.setter
    def rto(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__92f138c9c1c4d7c0a660387e6905fcfc6fa727a8bda2a30686c22d674a2e0748)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rto", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyRegion]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyRegion]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyRegion]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4d605a1a2ca062e34fbb453fd72e75d98243824ddd2d70b56b5df6a837115644)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicySoftware",
    jsii_struct_bases=[],
    name_mapping={"rpo": "rpo", "rto": "rto"},
)
class ResiliencehubResiliencyPolicyPolicySoftware:
    def __init__(self, *, rpo: builtins.str, rto: builtins.str) -> None:
        '''
        :param rpo: Recovery Point Objective (RPO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        :param rto: Recovery Time Objective (RTO) as a Go duration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9a1f1ec743ffb5451ab0cb59b01f9a9e8222d1abbb3811b19bbf30050490240b)
            check_type(argname="argument rpo", value=rpo, expected_type=type_hints["rpo"])
            check_type(argname="argument rto", value=rto, expected_type=type_hints["rto"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "rpo": rpo,
            "rto": rto,
        }

    @builtins.property
    def rpo(self) -> builtins.str:
        '''Recovery Point Objective (RPO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rpo ResiliencehubResiliencyPolicy#rpo}
        '''
        result = self._values.get("rpo")
        assert result is not None, "Required property 'rpo' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rto(self) -> builtins.str:
        '''Recovery Time Objective (RTO) as a Go duration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#rto ResiliencehubResiliencyPolicy#rto}
        '''
        result = self._values.get("rto")
        assert result is not None, "Required property 'rto' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyPolicySoftware(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResiliencehubResiliencyPolicyPolicySoftwareList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicySoftwareList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13e434ebf8c87de837862772e8080a3a196a82b163c3023ba7922cfed38ebc40)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "ResiliencehubResiliencyPolicyPolicySoftwareOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__058e1fa8e8467109f5782635a4b3aedcb162ba0c8f6ec35adde3893fd540ebab)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("ResiliencehubResiliencyPolicyPolicySoftwareOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1487a6de5b2e0adf3a4d72c70691a7dd5b5b483d99f37d5a16e80811fc5655a7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1b182bb8f09a8a51669938172788df50c2da099a52fec056af02f169df250af5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e9b0e99ddf9fe0769e5d422dddc3d5c95e2cb4c69de87c9dde3539779aeb1c39)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicySoftware]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicySoftware]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicySoftware]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8cd569d5b3ca73662da73c8e467ceb235edb82c373d30c236a50005e1a4b4767)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResiliencehubResiliencyPolicyPolicySoftwareOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyPolicySoftwareOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ba727e78ee36bc9d6d63f865591d99a897463550696fe23a935693cfc6f5a8e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="rpoInput")
    def rpo_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rpoInput"))

    @builtins.property
    @jsii.member(jsii_name="rtoInput")
    def rto_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "rtoInput"))

    @builtins.property
    @jsii.member(jsii_name="rpo")
    def rpo(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rpo"))

    @rpo.setter
    def rpo(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20d0a70ffff6522240a0e2d2ce552ca7fce5462ca5937e4c216a7293e2637876)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rpo", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="rto")
    def rto(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "rto"))

    @rto.setter
    def rto(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2018f4b318b88f3d4bd3af79c7d626c236cdfd61c5df452093d8d25ed8dd2d00)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "rto", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicySoftware]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicySoftware]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicySoftware]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c751604b9d2b536da3447fe73a693cdcaafe4d020b6f60f314a2c8afb25dcc22)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyTimeouts",
    jsii_struct_bases=[],
    name_mapping={"create": "create", "delete": "delete", "update": "update"},
)
class ResiliencehubResiliencyPolicyTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#create ResiliencehubResiliencyPolicy#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#delete ResiliencehubResiliencyPolicy#delete}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#update ResiliencehubResiliencyPolicy#update}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__23000807cba1bbb057fb7256d9c1de347607e1c05206217e093ce3c12c389c7c)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#create ResiliencehubResiliencyPolicy#create}
        '''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#delete ResiliencehubResiliencyPolicy#delete}
        '''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/resiliencehub_resiliency_policy#update ResiliencehubResiliencyPolicy#update}
        '''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResiliencehubResiliencyPolicyTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResiliencehubResiliencyPolicyTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.resiliencehubResiliencyPolicy.ResiliencehubResiliencyPolicyTimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a742f4edeec7e6c93c9fef9a66c1c07ae505819cacd2301484e54cf804e53bfc)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

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
            type_hints = typing.get_type_hints(_typecheckingstub__da71b7674ef191f5b50fa11d3be0cf075dc755e2ee8c90f1d38dab2dd69a65cb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f08f91985f70bc8e0ef1ca3cd28979560f549e9bd19507514a3c9ebc083a5612)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6c7e15581b051572d52cfeb715d6c001ce053e36248c618623290f639ab54b9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyTimeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyTimeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyTimeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5204e03e10428ba615913048ec8ed6bc017d661ea416ea49396e2594e0be0d7e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "ResiliencehubResiliencyPolicy",
    "ResiliencehubResiliencyPolicyConfig",
    "ResiliencehubResiliencyPolicyPolicy",
    "ResiliencehubResiliencyPolicyPolicyAz",
    "ResiliencehubResiliencyPolicyPolicyAzList",
    "ResiliencehubResiliencyPolicyPolicyAzOutputReference",
    "ResiliencehubResiliencyPolicyPolicyHardware",
    "ResiliencehubResiliencyPolicyPolicyHardwareList",
    "ResiliencehubResiliencyPolicyPolicyHardwareOutputReference",
    "ResiliencehubResiliencyPolicyPolicyList",
    "ResiliencehubResiliencyPolicyPolicyOutputReference",
    "ResiliencehubResiliencyPolicyPolicyRegion",
    "ResiliencehubResiliencyPolicyPolicyRegionList",
    "ResiliencehubResiliencyPolicyPolicyRegionOutputReference",
    "ResiliencehubResiliencyPolicyPolicySoftware",
    "ResiliencehubResiliencyPolicyPolicySoftwareList",
    "ResiliencehubResiliencyPolicyPolicySoftwareOutputReference",
    "ResiliencehubResiliencyPolicyTimeouts",
    "ResiliencehubResiliencyPolicyTimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__c9e99c1ff36d47086ecb56d7791c244413fbf187ce9822bc5a72b8064bfccb86(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    name: builtins.str,
    tier: builtins.str,
    data_location_constraint: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    policy: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicy, typing.Dict[builtins.str, typing.Any]]]]] = None,
    region: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[ResiliencehubResiliencyPolicyTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__a3cc0b760e72e60356d0f3953280548cf558844e394cfd913cf5742baed7fdeb(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6fffb7be936d59f6f45febf26e5d377d2081e82f0ff4aef35ba2459dc6455ff6(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicy, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9e55d51c53720775ba8732a6483a22e6e1791a5aae43e16fb527f2935b1e2a97(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae61b5173cb3bde2360a39dc0ac944d1589d67b891d57f7fbf5670b9f4057ec2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2cf76771c68f9b1661136f8293d6fe7b472389a93196b6ddbf8071c3ab1aee8f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f09e3c85b929c5e6c0400252320ac41b527a15fead1889a3883d4821885fe4c1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5829cf7387b89c8a4e38180b2cb66f8e204ad74b7eb8ef59c22907c83abacff9(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b92780750f5804f60f5f4f0dfa6d507b82690de7dc85bc614863d870c7715b46(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f675e61147b3f18af31a4259cab39b5a06cac89b66f940390ca1596022a5ab8(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    name: builtins.str,
    tier: builtins.str,
    data_location_constraint: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    policy: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicy, typing.Dict[builtins.str, typing.Any]]]]] = None,
    region: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[ResiliencehubResiliencyPolicyTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dd4c505381b5a6e785622167132eb787d6afb5ef0ca19fa7da6079622f5c2c37(
    *,
    az: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyAz, typing.Dict[builtins.str, typing.Any]]]]] = None,
    hardware: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyHardware, typing.Dict[builtins.str, typing.Any]]]]] = None,
    region: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyRegion, typing.Dict[builtins.str, typing.Any]]]]] = None,
    software_attribute: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicySoftware, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a8655a9581fcc1e03dbec5161e8b58163d65775b97bd75dd2399d5cd9a359f4(
    *,
    rpo: builtins.str,
    rto: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__679d833f5369da4f100a381b180a7be9c22c496bfdff3dd46e6232d0c6300049(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b661547d00835fc27afbce6a71871b398df2d1b1573e6662b69efe937b7ff8e8(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f310ff2c702620d6f57ede37685dcbf552075afec3ac58a27639a29b17b4e7f2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__814ad4c07737bc3ebef70625e3f06cea528fff2ca7c46fe100a6f2f2477354cc(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__278b3f89bf3b5caaaa91a9b4fe9c38c28ee395a351c136abd80d73096db802a2(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__33b3d691a828b0a56ea6c3d31f484b7b4a0100c7daee8ef4a37f5340ad1b070a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyAz]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2dd7838b2c0be10adaea06b31b08feb7a8e413e80979ac3a589572f4f9393009(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b30036d6f988f463b59121480fc860955c0281b0421b1acbd798673a5016975(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68fa7f3f44e24715feaa5d3d84bc314bb22f3e219765d342a279e1a5bd9df697(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4af275bfc83226a3cdc83adc2bccc44d61f1f96918aaaf70c260b196c5c5ec40(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyAz]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d304688c7d5b31d8b67b1db80663c3a2dce1524a0addb31420491f5b851876e3(
    *,
    rpo: builtins.str,
    rto: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__db5697bc8894aa763d15aa1a0ebde740e71f53ca13c0f621428059187478004d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aa0a84ebac2a6a00f64fe0df4cea04fb1eb22ff1c5b7df2d0e2586b863a3929d(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5df2134bb4edacf6a0a28dd7305080e22b3dcec557d6241c78920a8919ce488(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fb3e2511b567a8ccdc8abac75910c30f44fe46a2fb038d94371d5ef3e91354dd(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__80223d866aac52cb1a98bfe8c6b85fb19a60a3a88ad658c8b8b4629f5597002b(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de0a060966a9c11ecb0f47e25a984b76500f8e7deeef7ccc2f0c1d0108ce9ff2(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyHardware]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cf5ca04a38c3631e1fd0f00163f50823d1a238c78fa7fc690d505b2db2c82d55(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82cba5290eecb34e610279dbad53cc48e4ff793ad7e7c332bcca52bbcda1e272(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3a4d53e3df88f25e703736d09ca2132907cc5735554e2165e2a3278a6902ff2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8bc763f1f4d3134b2bf66a50e81c3125dca164d718d5e54516a0a587b8bd6647(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyHardware]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5bf63334933e77f81b01459455c7de8ae61ceeb5ae1ad85ec496f4c600dcfe1(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2043634cd03d444633261663eb0a1042c8c59be2d7308171018210a9645da3c(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6eee76bf42c3a4718853e8ad788e409b7e8055429877433619071795eef9d451(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__146a690cbd68ee8ff251e63bfe29b7a3ad208125859b4c97ee2e49b83363f2e8(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad9466d422482860dd651203e2eb94fe4c7cb526561801ce24d50eee1ee4327f(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f08575213923f5484b3694491a749744fa778943bd97b2f5327bd0f11542faa4(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicy]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13a393e81f29a7144e3b74adffe3c2b39d1ea71af98a5f4ccb727bf25df0b998(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7929d21b9bf0a006a7601bda6c86208dfb6218d44e48b4ea96d1a0edb4644b1c(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyAz, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__191222525c76721445e5654c9eda338e775208b35b836ec0419d61234a23844b(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyHardware, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b241205e0d230ebe53db0bfec986d5d75920f9ab6bd0e7969c7b2b3845180ca(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicyRegion, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__14c4d3043a4234a009e51bc632761fea6bc1215841630e63ef735b205a66221b(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[ResiliencehubResiliencyPolicyPolicySoftware, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d061d2d03be3a3a1da686ce9c1b97c118e682960e191309735bf3d16e3ce8acc(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicy]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__199ab28697b41234fdb3939f74a42b5b877f2ac1c2418dd1f1038d793f4509e4(
    *,
    rpo: typing.Optional[builtins.str] = None,
    rto: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7bc70747a69e7081bbfdfb522e15e8315e60ad8953a192bc3d45298274ced218(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__81f0eec0a2d7962c882ec653483fe47e945cd82e107c5174b51d064484953a41(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__30752767fd9306209e8c1b8f678509bd5ec9b2814ccd15eb526493b7cc9acad0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94d798b6e58e18fc24e70ce34e7f1f1c8e5c09f007d596979f9ccb8a4bffbb3a(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aade1e452e3821d0be97a65867bc21b725191994850af8785ec4473c003d2f3a(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f27cd9811bee2a717d1ad01d0ca9edfe02ccf814b95e516349039720c29e4f83(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicyRegion]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__145f98dd670351106490f643d0ee7d25fa6ee6fde49f974c56aef88fcdb4ee56(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b8b740e8fa7d80ab5de73a457b9f34532e6cc7bc3df5d1a2a2c48a18b274eed6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92f138c9c1c4d7c0a660387e6905fcfc6fa727a8bda2a30686c22d674a2e0748(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d605a1a2ca062e34fbb453fd72e75d98243824ddd2d70b56b5df6a837115644(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicyRegion]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9a1f1ec743ffb5451ab0cb59b01f9a9e8222d1abbb3811b19bbf30050490240b(
    *,
    rpo: builtins.str,
    rto: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13e434ebf8c87de837862772e8080a3a196a82b163c3023ba7922cfed38ebc40(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__058e1fa8e8467109f5782635a4b3aedcb162ba0c8f6ec35adde3893fd540ebab(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1487a6de5b2e0adf3a4d72c70691a7dd5b5b483d99f37d5a16e80811fc5655a7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1b182bb8f09a8a51669938172788df50c2da099a52fec056af02f169df250af5(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e9b0e99ddf9fe0769e5d422dddc3d5c95e2cb4c69de87c9dde3539779aeb1c39(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8cd569d5b3ca73662da73c8e467ceb235edb82c373d30c236a50005e1a4b4767(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[ResiliencehubResiliencyPolicyPolicySoftware]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ba727e78ee36bc9d6d63f865591d99a897463550696fe23a935693cfc6f5a8e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20d0a70ffff6522240a0e2d2ce552ca7fce5462ca5937e4c216a7293e2637876(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2018f4b318b88f3d4bd3af79c7d626c236cdfd61c5df452093d8d25ed8dd2d00(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c751604b9d2b536da3447fe73a693cdcaafe4d020b6f60f314a2c8afb25dcc22(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyPolicySoftware]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__23000807cba1bbb057fb7256d9c1de347607e1c05206217e093ce3c12c389c7c(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a742f4edeec7e6c93c9fef9a66c1c07ae505819cacd2301484e54cf804e53bfc(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da71b7674ef191f5b50fa11d3be0cf075dc755e2ee8c90f1d38dab2dd69a65cb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f08f91985f70bc8e0ef1ca3cd28979560f549e9bd19507514a3c9ebc083a5612(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6c7e15581b051572d52cfeb715d6c001ce053e36248c618623290f639ab54b9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5204e03e10428ba615913048ec8ed6bc017d661ea416ea49396e2594e0be0d7e(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, ResiliencehubResiliencyPolicyTimeouts]],
) -> None:
    """Type checking stubs"""
    pass
