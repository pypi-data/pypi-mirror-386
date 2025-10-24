r'''
# `aws_networkmanager_transit_gateway_connect_peer_association`

Refer to the Terraform Registry for docs: [`aws_networkmanager_transit_gateway_connect_peer_association`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association).
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


class NetworkmanagerTransitGatewayConnectPeerAssociation(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.networkmanagerTransitGatewayConnectPeerAssociation.NetworkmanagerTransitGatewayConnectPeerAssociation",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association aws_networkmanager_transit_gateway_connect_peer_association}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        device_id: builtins.str,
        global_network_id: builtins.str,
        transit_gateway_connect_peer_arn: builtins.str,
        id: typing.Optional[builtins.str] = None,
        link_id: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association aws_networkmanager_transit_gateway_connect_peer_association} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param device_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#device_id NetworkmanagerTransitGatewayConnectPeerAssociation#device_id}.
        :param global_network_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#global_network_id NetworkmanagerTransitGatewayConnectPeerAssociation#global_network_id}.
        :param transit_gateway_connect_peer_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#transit_gateway_connect_peer_arn NetworkmanagerTransitGatewayConnectPeerAssociation#transit_gateway_connect_peer_arn}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#id NetworkmanagerTransitGatewayConnectPeerAssociation#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param link_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#link_id NetworkmanagerTransitGatewayConnectPeerAssociation#link_id}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#timeouts NetworkmanagerTransitGatewayConnectPeerAssociation#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f2b09c982100f312280a30693a8d4887cba933b5b603d07486185b552e73798)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = NetworkmanagerTransitGatewayConnectPeerAssociationConfig(
            device_id=device_id,
            global_network_id=global_network_id,
            transit_gateway_connect_peer_arn=transit_gateway_connect_peer_arn,
            id=id,
            link_id=link_id,
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
        '''Generates CDKTF code for importing a NetworkmanagerTransitGatewayConnectPeerAssociation resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the NetworkmanagerTransitGatewayConnectPeerAssociation to import.
        :param import_from_id: The id of the existing NetworkmanagerTransitGatewayConnectPeerAssociation that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the NetworkmanagerTransitGatewayConnectPeerAssociation to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__49477891a7f53cae5dd9efd3baa375c496f2b9121efcde4b2a543c3471eace07)
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
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#create NetworkmanagerTransitGatewayConnectPeerAssociation#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#delete NetworkmanagerTransitGatewayConnectPeerAssociation#delete}.
        '''
        value = NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts(
            create=create, delete=delete
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetLinkId")
    def reset_link_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLinkId", []))

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
    def timeouts(
        self,
    ) -> "NetworkmanagerTransitGatewayConnectPeerAssociationTimeoutsOutputReference":
        return typing.cast("NetworkmanagerTransitGatewayConnectPeerAssociationTimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="deviceIdInput")
    def device_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deviceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="globalNetworkIdInput")
    def global_network_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "globalNetworkIdInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="linkIdInput")
    def link_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "linkIdInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="transitGatewayConnectPeerArnInput")
    def transit_gateway_connect_peer_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "transitGatewayConnectPeerArnInput"))

    @builtins.property
    @jsii.member(jsii_name="deviceId")
    def device_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "deviceId"))

    @device_id.setter
    def device_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__edf84e2d88d9490798fdd88ec315d62650dd5896dfe7d65224460ff586f94832)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deviceId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="globalNetworkId")
    def global_network_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "globalNetworkId"))

    @global_network_id.setter
    def global_network_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__00a13150b1a986fc90273c67048a216b9d69a7224afe489525b34714e38877d4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "globalNetworkId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__df5f4633aff19d0da547fdb62d44ec38dc8587cd7a01d13b89a95be5e2212da6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="linkId")
    def link_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "linkId"))

    @link_id.setter
    def link_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e10c35f1159b9080284d33da5ba8959a0e49818c9ae29366d0cef385f18c221c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "linkId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="transitGatewayConnectPeerArn")
    def transit_gateway_connect_peer_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "transitGatewayConnectPeerArn"))

    @transit_gateway_connect_peer_arn.setter
    def transit_gateway_connect_peer_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f6c186ed24337895f9c0859f9c9552c9ca5b4e04a16f35e1f7ed16a775ca2242)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "transitGatewayConnectPeerArn", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.networkmanagerTransitGatewayConnectPeerAssociation.NetworkmanagerTransitGatewayConnectPeerAssociationConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "device_id": "deviceId",
        "global_network_id": "globalNetworkId",
        "transit_gateway_connect_peer_arn": "transitGatewayConnectPeerArn",
        "id": "id",
        "link_id": "linkId",
        "timeouts": "timeouts",
    },
)
class NetworkmanagerTransitGatewayConnectPeerAssociationConfig(
    _cdktf_9a9027ec.TerraformMetaArguments,
):
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
        device_id: builtins.str,
        global_network_id: builtins.str,
        transit_gateway_connect_peer_arn: builtins.str,
        id: typing.Optional[builtins.str] = None,
        link_id: typing.Optional[builtins.str] = None,
        timeouts: typing.Optional[typing.Union["NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param device_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#device_id NetworkmanagerTransitGatewayConnectPeerAssociation#device_id}.
        :param global_network_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#global_network_id NetworkmanagerTransitGatewayConnectPeerAssociation#global_network_id}.
        :param transit_gateway_connect_peer_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#transit_gateway_connect_peer_arn NetworkmanagerTransitGatewayConnectPeerAssociation#transit_gateway_connect_peer_arn}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#id NetworkmanagerTransitGatewayConnectPeerAssociation#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param link_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#link_id NetworkmanagerTransitGatewayConnectPeerAssociation#link_id}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#timeouts NetworkmanagerTransitGatewayConnectPeerAssociation#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(timeouts, dict):
            timeouts = NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__478be6e2498fe2b8e15e7ddf0ca8ab6981f7ce77cd0257414d60f591f8c858c5)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument device_id", value=device_id, expected_type=type_hints["device_id"])
            check_type(argname="argument global_network_id", value=global_network_id, expected_type=type_hints["global_network_id"])
            check_type(argname="argument transit_gateway_connect_peer_arn", value=transit_gateway_connect_peer_arn, expected_type=type_hints["transit_gateway_connect_peer_arn"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument link_id", value=link_id, expected_type=type_hints["link_id"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "device_id": device_id,
            "global_network_id": global_network_id,
            "transit_gateway_connect_peer_arn": transit_gateway_connect_peer_arn,
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
        if link_id is not None:
            self._values["link_id"] = link_id
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
    def device_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#device_id NetworkmanagerTransitGatewayConnectPeerAssociation#device_id}.'''
        result = self._values.get("device_id")
        assert result is not None, "Required property 'device_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def global_network_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#global_network_id NetworkmanagerTransitGatewayConnectPeerAssociation#global_network_id}.'''
        result = self._values.get("global_network_id")
        assert result is not None, "Required property 'global_network_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def transit_gateway_connect_peer_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#transit_gateway_connect_peer_arn NetworkmanagerTransitGatewayConnectPeerAssociation#transit_gateway_connect_peer_arn}.'''
        result = self._values.get("transit_gateway_connect_peer_arn")
        assert result is not None, "Required property 'transit_gateway_connect_peer_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#id NetworkmanagerTransitGatewayConnectPeerAssociation#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def link_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#link_id NetworkmanagerTransitGatewayConnectPeerAssociation#link_id}.'''
        result = self._values.get("link_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def timeouts(
        self,
    ) -> typing.Optional["NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#timeouts NetworkmanagerTransitGatewayConnectPeerAssociation#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkmanagerTransitGatewayConnectPeerAssociationConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.networkmanagerTransitGatewayConnectPeerAssociation.NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts",
    jsii_struct_bases=[],
    name_mapping={"create": "create", "delete": "delete"},
)
class NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#create NetworkmanagerTransitGatewayConnectPeerAssociation#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#delete NetworkmanagerTransitGatewayConnectPeerAssociation#delete}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0139d912140bb42e301322b99710dec0f2391a6ac096dc43f809e231f99331f0)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#create NetworkmanagerTransitGatewayConnectPeerAssociation#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/networkmanager_transit_gateway_connect_peer_association#delete NetworkmanagerTransitGatewayConnectPeerAssociation#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class NetworkmanagerTransitGatewayConnectPeerAssociationTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.networkmanagerTransitGatewayConnectPeerAssociation.NetworkmanagerTransitGatewayConnectPeerAssociationTimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__08b6acda96099604ee6558d691f1da1306b562f2e61ca864b399abbca071d8e8)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__69303d67a7b3a5cf908040c4526a80ad287ec35cb7bead082a7991b9ff0c23c4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc3fe867c184ddf43ef1e3add20eb7132629e66a936f39c8c1ebe0649cd9fcad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56ea2f59b18e9e06747278b8a029cff0fc63978d775ecc358d1b4f8964857544)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "NetworkmanagerTransitGatewayConnectPeerAssociation",
    "NetworkmanagerTransitGatewayConnectPeerAssociationConfig",
    "NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts",
    "NetworkmanagerTransitGatewayConnectPeerAssociationTimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__1f2b09c982100f312280a30693a8d4887cba933b5b603d07486185b552e73798(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    device_id: builtins.str,
    global_network_id: builtins.str,
    transit_gateway_connect_peer_arn: builtins.str,
    id: typing.Optional[builtins.str] = None,
    link_id: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__49477891a7f53cae5dd9efd3baa375c496f2b9121efcde4b2a543c3471eace07(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__edf84e2d88d9490798fdd88ec315d62650dd5896dfe7d65224460ff586f94832(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__00a13150b1a986fc90273c67048a216b9d69a7224afe489525b34714e38877d4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__df5f4633aff19d0da547fdb62d44ec38dc8587cd7a01d13b89a95be5e2212da6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e10c35f1159b9080284d33da5ba8959a0e49818c9ae29366d0cef385f18c221c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f6c186ed24337895f9c0859f9c9552c9ca5b4e04a16f35e1f7ed16a775ca2242(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__478be6e2498fe2b8e15e7ddf0ca8ab6981f7ce77cd0257414d60f591f8c858c5(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    device_id: builtins.str,
    global_network_id: builtins.str,
    transit_gateway_connect_peer_arn: builtins.str,
    id: typing.Optional[builtins.str] = None,
    link_id: typing.Optional[builtins.str] = None,
    timeouts: typing.Optional[typing.Union[NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0139d912140bb42e301322b99710dec0f2391a6ac096dc43f809e231f99331f0(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__08b6acda96099604ee6558d691f1da1306b562f2e61ca864b399abbca071d8e8(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__69303d67a7b3a5cf908040c4526a80ad287ec35cb7bead082a7991b9ff0c23c4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc3fe867c184ddf43ef1e3add20eb7132629e66a936f39c8c1ebe0649cd9fcad(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56ea2f59b18e9e06747278b8a029cff0fc63978d775ecc358d1b4f8964857544(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, NetworkmanagerTransitGatewayConnectPeerAssociationTimeouts]],
) -> None:
    """Type checking stubs"""
    pass
