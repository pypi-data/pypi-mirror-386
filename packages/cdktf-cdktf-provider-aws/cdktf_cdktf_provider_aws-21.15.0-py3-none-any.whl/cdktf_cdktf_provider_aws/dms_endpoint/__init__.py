r'''
# `aws_dms_endpoint`

Refer to the Terraform Registry for docs: [`aws_dms_endpoint`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint).
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


class DmsEndpoint(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpoint",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint aws_dms_endpoint}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        endpoint_id: builtins.str,
        endpoint_type: builtins.str,
        engine_name: builtins.str,
        certificate_arn: typing.Optional[builtins.str] = None,
        database_name: typing.Optional[builtins.str] = None,
        elasticsearch_settings: typing.Optional[typing.Union["DmsEndpointElasticsearchSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        extra_connection_attributes: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        kafka_settings: typing.Optional[typing.Union["DmsEndpointKafkaSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        kinesis_settings: typing.Optional[typing.Union["DmsEndpointKinesisSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        kms_key_arn: typing.Optional[builtins.str] = None,
        mongodb_settings: typing.Optional[typing.Union["DmsEndpointMongodbSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        mysql_settings: typing.Optional[typing.Union["DmsEndpointMysqlSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        oracle_settings: typing.Optional[typing.Union["DmsEndpointOracleSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        password: typing.Optional[builtins.str] = None,
        pause_replication_tasks: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        port: typing.Optional[jsii.Number] = None,
        postgres_settings: typing.Optional[typing.Union["DmsEndpointPostgresSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        redis_settings: typing.Optional[typing.Union["DmsEndpointRedisSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        redshift_settings: typing.Optional[typing.Union["DmsEndpointRedshiftSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        region: typing.Optional[builtins.str] = None,
        secrets_manager_access_role_arn: typing.Optional[builtins.str] = None,
        secrets_manager_arn: typing.Optional[builtins.str] = None,
        server_name: typing.Optional[builtins.str] = None,
        service_access_role: typing.Optional[builtins.str] = None,
        ssl_mode: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union["DmsEndpointTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        username: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint aws_dms_endpoint} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param endpoint_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_id DmsEndpoint#endpoint_id}.
        :param endpoint_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_type DmsEndpoint#endpoint_type}.
        :param engine_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#engine_name DmsEndpoint#engine_name}.
        :param certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#certificate_arn DmsEndpoint#certificate_arn}.
        :param database_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_name DmsEndpoint#database_name}.
        :param elasticsearch_settings: elasticsearch_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#elasticsearch_settings DmsEndpoint#elasticsearch_settings}
        :param extra_connection_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extra_connection_attributes DmsEndpoint#extra_connection_attributes}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#id DmsEndpoint#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param kafka_settings: kafka_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kafka_settings DmsEndpoint#kafka_settings}
        :param kinesis_settings: kinesis_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kinesis_settings DmsEndpoint#kinesis_settings}
        :param kms_key_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kms_key_arn DmsEndpoint#kms_key_arn}.
        :param mongodb_settings: mongodb_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mongodb_settings DmsEndpoint#mongodb_settings}
        :param mysql_settings: mysql_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mysql_settings DmsEndpoint#mysql_settings}
        :param oracle_settings: oracle_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#oracle_settings DmsEndpoint#oracle_settings}
        :param password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#password DmsEndpoint#password}.
        :param pause_replication_tasks: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#pause_replication_tasks DmsEndpoint#pause_replication_tasks}.
        :param port: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.
        :param postgres_settings: postgres_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#postgres_settings DmsEndpoint#postgres_settings}
        :param redis_settings: redis_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redis_settings DmsEndpoint#redis_settings}
        :param redshift_settings: redshift_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redshift_settings DmsEndpoint#redshift_settings}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#region DmsEndpoint#region}
        :param secrets_manager_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_access_role_arn DmsEndpoint#secrets_manager_access_role_arn}.
        :param secrets_manager_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_arn DmsEndpoint#secrets_manager_arn}.
        :param server_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.
        :param service_access_role: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role DmsEndpoint#service_access_role}.
        :param ssl_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_mode DmsEndpoint#ssl_mode}.
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags DmsEndpoint#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags_all DmsEndpoint#tags_all}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#timeouts DmsEndpoint#timeouts}
        :param username: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#username DmsEndpoint#username}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2192e6db95bbd3c1e222723ec4801db2d95abb842294f35cfedb741c69ea91a5)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = DmsEndpointConfig(
            endpoint_id=endpoint_id,
            endpoint_type=endpoint_type,
            engine_name=engine_name,
            certificate_arn=certificate_arn,
            database_name=database_name,
            elasticsearch_settings=elasticsearch_settings,
            extra_connection_attributes=extra_connection_attributes,
            id=id,
            kafka_settings=kafka_settings,
            kinesis_settings=kinesis_settings,
            kms_key_arn=kms_key_arn,
            mongodb_settings=mongodb_settings,
            mysql_settings=mysql_settings,
            oracle_settings=oracle_settings,
            password=password,
            pause_replication_tasks=pause_replication_tasks,
            port=port,
            postgres_settings=postgres_settings,
            redis_settings=redis_settings,
            redshift_settings=redshift_settings,
            region=region,
            secrets_manager_access_role_arn=secrets_manager_access_role_arn,
            secrets_manager_arn=secrets_manager_arn,
            server_name=server_name,
            service_access_role=service_access_role,
            ssl_mode=ssl_mode,
            tags=tags,
            tags_all=tags_all,
            timeouts=timeouts,
            username=username,
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
        '''Generates CDKTF code for importing a DmsEndpoint resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DmsEndpoint to import.
        :param import_from_id: The id of the existing DmsEndpoint that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DmsEndpoint to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8efcd06129a937ea04367e27ffe1e4ff935dd1355008430cafa827575ef27a7c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putElasticsearchSettings")
    def put_elasticsearch_settings(
        self,
        *,
        endpoint_uri: builtins.str,
        service_access_role_arn: builtins.str,
        error_retry_duration: typing.Optional[jsii.Number] = None,
        full_load_error_percentage: typing.Optional[jsii.Number] = None,
        use_new_mapping_type: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param endpoint_uri: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_uri DmsEndpoint#endpoint_uri}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param error_retry_duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#error_retry_duration DmsEndpoint#error_retry_duration}.
        :param full_load_error_percentage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#full_load_error_percentage DmsEndpoint#full_load_error_percentage}.
        :param use_new_mapping_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_new_mapping_type DmsEndpoint#use_new_mapping_type}.
        '''
        value = DmsEndpointElasticsearchSettings(
            endpoint_uri=endpoint_uri,
            service_access_role_arn=service_access_role_arn,
            error_retry_duration=error_retry_duration,
            full_load_error_percentage=full_load_error_percentage,
            use_new_mapping_type=use_new_mapping_type,
        )

        return typing.cast(None, jsii.invoke(self, "putElasticsearchSettings", [value]))

    @jsii.member(jsii_name="putKafkaSettings")
    def put_kafka_settings(
        self,
        *,
        broker: builtins.str,
        include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        message_format: typing.Optional[builtins.str] = None,
        message_max_bytes: typing.Optional[jsii.Number] = None,
        no_hex_prefix: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        sasl_mechanism: typing.Optional[builtins.str] = None,
        sasl_password: typing.Optional[builtins.str] = None,
        sasl_username: typing.Optional[builtins.str] = None,
        security_protocol: typing.Optional[builtins.str] = None,
        ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_client_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_client_key_arn: typing.Optional[builtins.str] = None,
        ssl_client_key_password: typing.Optional[builtins.str] = None,
        topic: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param broker: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#broker DmsEndpoint#broker}.
        :param include_control_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.
        :param include_null_and_empty: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.
        :param include_partition_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.
        :param include_table_alter_operations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.
        :param include_transaction_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.
        :param message_format: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.
        :param message_max_bytes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_max_bytes DmsEndpoint#message_max_bytes}.
        :param no_hex_prefix: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#no_hex_prefix DmsEndpoint#no_hex_prefix}.
        :param partition_include_schema_table: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.
        :param sasl_mechanism: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_mechanism DmsEndpoint#sasl_mechanism}.
        :param sasl_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_password DmsEndpoint#sasl_password}.
        :param sasl_username: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_username DmsEndpoint#sasl_username}.
        :param security_protocol: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#security_protocol DmsEndpoint#security_protocol}.
        :param ssl_ca_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.
        :param ssl_client_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_certificate_arn DmsEndpoint#ssl_client_certificate_arn}.
        :param ssl_client_key_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_arn DmsEndpoint#ssl_client_key_arn}.
        :param ssl_client_key_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_password DmsEndpoint#ssl_client_key_password}.
        :param topic: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#topic DmsEndpoint#topic}.
        '''
        value = DmsEndpointKafkaSettings(
            broker=broker,
            include_control_details=include_control_details,
            include_null_and_empty=include_null_and_empty,
            include_partition_value=include_partition_value,
            include_table_alter_operations=include_table_alter_operations,
            include_transaction_details=include_transaction_details,
            message_format=message_format,
            message_max_bytes=message_max_bytes,
            no_hex_prefix=no_hex_prefix,
            partition_include_schema_table=partition_include_schema_table,
            sasl_mechanism=sasl_mechanism,
            sasl_password=sasl_password,
            sasl_username=sasl_username,
            security_protocol=security_protocol,
            ssl_ca_certificate_arn=ssl_ca_certificate_arn,
            ssl_client_certificate_arn=ssl_client_certificate_arn,
            ssl_client_key_arn=ssl_client_key_arn,
            ssl_client_key_password=ssl_client_key_password,
            topic=topic,
        )

        return typing.cast(None, jsii.invoke(self, "putKafkaSettings", [value]))

    @jsii.member(jsii_name="putKinesisSettings")
    def put_kinesis_settings(
        self,
        *,
        include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        message_format: typing.Optional[builtins.str] = None,
        partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        stream_arn: typing.Optional[builtins.str] = None,
        use_large_integer_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param include_control_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.
        :param include_null_and_empty: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.
        :param include_partition_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.
        :param include_table_alter_operations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.
        :param include_transaction_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.
        :param message_format: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.
        :param partition_include_schema_table: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param stream_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#stream_arn DmsEndpoint#stream_arn}.
        :param use_large_integer_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_large_integer_value DmsEndpoint#use_large_integer_value}.
        '''
        value = DmsEndpointKinesisSettings(
            include_control_details=include_control_details,
            include_null_and_empty=include_null_and_empty,
            include_partition_value=include_partition_value,
            include_table_alter_operations=include_table_alter_operations,
            include_transaction_details=include_transaction_details,
            message_format=message_format,
            partition_include_schema_table=partition_include_schema_table,
            service_access_role_arn=service_access_role_arn,
            stream_arn=stream_arn,
            use_large_integer_value=use_large_integer_value,
        )

        return typing.cast(None, jsii.invoke(self, "putKinesisSettings", [value]))

    @jsii.member(jsii_name="putMongodbSettings")
    def put_mongodb_settings(
        self,
        *,
        auth_mechanism: typing.Optional[builtins.str] = None,
        auth_source: typing.Optional[builtins.str] = None,
        auth_type: typing.Optional[builtins.str] = None,
        docs_to_investigate: typing.Optional[builtins.str] = None,
        extract_doc_id: typing.Optional[builtins.str] = None,
        nesting_level: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param auth_mechanism: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_mechanism DmsEndpoint#auth_mechanism}.
        :param auth_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_source DmsEndpoint#auth_source}.
        :param auth_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.
        :param docs_to_investigate: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#docs_to_investigate DmsEndpoint#docs_to_investigate}.
        :param extract_doc_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extract_doc_id DmsEndpoint#extract_doc_id}.
        :param nesting_level: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#nesting_level DmsEndpoint#nesting_level}.
        '''
        value = DmsEndpointMongodbSettings(
            auth_mechanism=auth_mechanism,
            auth_source=auth_source,
            auth_type=auth_type,
            docs_to_investigate=docs_to_investigate,
            extract_doc_id=extract_doc_id,
            nesting_level=nesting_level,
        )

        return typing.cast(None, jsii.invoke(self, "putMongodbSettings", [value]))

    @jsii.member(jsii_name="putMysqlSettings")
    def put_mysql_settings(
        self,
        *,
        after_connect_script: typing.Optional[builtins.str] = None,
        authentication_method: typing.Optional[builtins.str] = None,
        clean_source_metadata_on_mismatch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        events_poll_interval: typing.Optional[jsii.Number] = None,
        execute_timeout: typing.Optional[jsii.Number] = None,
        max_file_size: typing.Optional[jsii.Number] = None,
        parallel_load_threads: typing.Optional[jsii.Number] = None,
        server_timezone: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        target_db_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param after_connect_script: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        :param clean_source_metadata_on_mismatch: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#clean_source_metadata_on_mismatch DmsEndpoint#clean_source_metadata_on_mismatch}.
        :param events_poll_interval: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#events_poll_interval DmsEndpoint#events_poll_interval}.
        :param execute_timeout: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.
        :param max_file_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.
        :param parallel_load_threads: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#parallel_load_threads DmsEndpoint#parallel_load_threads}.
        :param server_timezone: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_timezone DmsEndpoint#server_timezone}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param target_db_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#target_db_type DmsEndpoint#target_db_type}.
        '''
        value = DmsEndpointMysqlSettings(
            after_connect_script=after_connect_script,
            authentication_method=authentication_method,
            clean_source_metadata_on_mismatch=clean_source_metadata_on_mismatch,
            events_poll_interval=events_poll_interval,
            execute_timeout=execute_timeout,
            max_file_size=max_file_size,
            parallel_load_threads=parallel_load_threads,
            server_timezone=server_timezone,
            service_access_role_arn=service_access_role_arn,
            target_db_type=target_db_type,
        )

        return typing.cast(None, jsii.invoke(self, "putMysqlSettings", [value]))

    @jsii.member(jsii_name="putOracleSettings")
    def put_oracle_settings(
        self,
        *,
        authentication_method: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        '''
        value = DmsEndpointOracleSettings(authentication_method=authentication_method)

        return typing.cast(None, jsii.invoke(self, "putOracleSettings", [value]))

    @jsii.member(jsii_name="putPostgresSettings")
    def put_postgres_settings(
        self,
        *,
        after_connect_script: typing.Optional[builtins.str] = None,
        authentication_method: typing.Optional[builtins.str] = None,
        babelfish_database_name: typing.Optional[builtins.str] = None,
        capture_ddls: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        database_mode: typing.Optional[builtins.str] = None,
        ddl_artifacts_schema: typing.Optional[builtins.str] = None,
        execute_timeout: typing.Optional[jsii.Number] = None,
        fail_tasks_on_lob_truncation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        heartbeat_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        heartbeat_frequency: typing.Optional[jsii.Number] = None,
        heartbeat_schema: typing.Optional[builtins.str] = None,
        map_boolean_as_boolean: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        map_jsonb_as_clob: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        map_long_varchar_as: typing.Optional[builtins.str] = None,
        max_file_size: typing.Optional[jsii.Number] = None,
        plugin_name: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        slot_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param after_connect_script: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        :param babelfish_database_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#babelfish_database_name DmsEndpoint#babelfish_database_name}.
        :param capture_ddls: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#capture_ddls DmsEndpoint#capture_ddls}.
        :param database_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_mode DmsEndpoint#database_mode}.
        :param ddl_artifacts_schema: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ddl_artifacts_schema DmsEndpoint#ddl_artifacts_schema}.
        :param execute_timeout: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.
        :param fail_tasks_on_lob_truncation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#fail_tasks_on_lob_truncation DmsEndpoint#fail_tasks_on_lob_truncation}.
        :param heartbeat_enable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_enable DmsEndpoint#heartbeat_enable}.
        :param heartbeat_frequency: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_frequency DmsEndpoint#heartbeat_frequency}.
        :param heartbeat_schema: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_schema DmsEndpoint#heartbeat_schema}.
        :param map_boolean_as_boolean: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_boolean_as_boolean DmsEndpoint#map_boolean_as_boolean}.
        :param map_jsonb_as_clob: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_jsonb_as_clob DmsEndpoint#map_jsonb_as_clob}.
        :param map_long_varchar_as: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_long_varchar_as DmsEndpoint#map_long_varchar_as}.
        :param max_file_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.
        :param plugin_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#plugin_name DmsEndpoint#plugin_name}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param slot_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#slot_name DmsEndpoint#slot_name}.
        '''
        value = DmsEndpointPostgresSettings(
            after_connect_script=after_connect_script,
            authentication_method=authentication_method,
            babelfish_database_name=babelfish_database_name,
            capture_ddls=capture_ddls,
            database_mode=database_mode,
            ddl_artifacts_schema=ddl_artifacts_schema,
            execute_timeout=execute_timeout,
            fail_tasks_on_lob_truncation=fail_tasks_on_lob_truncation,
            heartbeat_enable=heartbeat_enable,
            heartbeat_frequency=heartbeat_frequency,
            heartbeat_schema=heartbeat_schema,
            map_boolean_as_boolean=map_boolean_as_boolean,
            map_jsonb_as_clob=map_jsonb_as_clob,
            map_long_varchar_as=map_long_varchar_as,
            max_file_size=max_file_size,
            plugin_name=plugin_name,
            service_access_role_arn=service_access_role_arn,
            slot_name=slot_name,
        )

        return typing.cast(None, jsii.invoke(self, "putPostgresSettings", [value]))

    @jsii.member(jsii_name="putRedisSettings")
    def put_redis_settings(
        self,
        *,
        auth_type: builtins.str,
        port: jsii.Number,
        server_name: builtins.str,
        auth_password: typing.Optional[builtins.str] = None,
        auth_user_name: typing.Optional[builtins.str] = None,
        ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_security_protocol: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param auth_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.
        :param port: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.
        :param server_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.
        :param auth_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_password DmsEndpoint#auth_password}.
        :param auth_user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_user_name DmsEndpoint#auth_user_name}.
        :param ssl_ca_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.
        :param ssl_security_protocol: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_security_protocol DmsEndpoint#ssl_security_protocol}.
        '''
        value = DmsEndpointRedisSettings(
            auth_type=auth_type,
            port=port,
            server_name=server_name,
            auth_password=auth_password,
            auth_user_name=auth_user_name,
            ssl_ca_certificate_arn=ssl_ca_certificate_arn,
            ssl_security_protocol=ssl_security_protocol,
        )

        return typing.cast(None, jsii.invoke(self, "putRedisSettings", [value]))

    @jsii.member(jsii_name="putRedshiftSettings")
    def put_redshift_settings(
        self,
        *,
        bucket_folder: typing.Optional[builtins.str] = None,
        bucket_name: typing.Optional[builtins.str] = None,
        encryption_mode: typing.Optional[builtins.str] = None,
        server_side_encryption_kms_key_id: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param bucket_folder: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_folder DmsEndpoint#bucket_folder}.
        :param bucket_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_name DmsEndpoint#bucket_name}.
        :param encryption_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#encryption_mode DmsEndpoint#encryption_mode}.
        :param server_side_encryption_kms_key_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_side_encryption_kms_key_id DmsEndpoint#server_side_encryption_kms_key_id}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        '''
        value = DmsEndpointRedshiftSettings(
            bucket_folder=bucket_folder,
            bucket_name=bucket_name,
            encryption_mode=encryption_mode,
            server_side_encryption_kms_key_id=server_side_encryption_kms_key_id,
            service_access_role_arn=service_access_role_arn,
        )

        return typing.cast(None, jsii.invoke(self, "putRedshiftSettings", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#create DmsEndpoint#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#delete DmsEndpoint#delete}.
        '''
        value = DmsEndpointTimeouts(create=create, delete=delete)

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetCertificateArn")
    def reset_certificate_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCertificateArn", []))

    @jsii.member(jsii_name="resetDatabaseName")
    def reset_database_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDatabaseName", []))

    @jsii.member(jsii_name="resetElasticsearchSettings")
    def reset_elasticsearch_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetElasticsearchSettings", []))

    @jsii.member(jsii_name="resetExtraConnectionAttributes")
    def reset_extra_connection_attributes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExtraConnectionAttributes", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetKafkaSettings")
    def reset_kafka_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKafkaSettings", []))

    @jsii.member(jsii_name="resetKinesisSettings")
    def reset_kinesis_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKinesisSettings", []))

    @jsii.member(jsii_name="resetKmsKeyArn")
    def reset_kms_key_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKmsKeyArn", []))

    @jsii.member(jsii_name="resetMongodbSettings")
    def reset_mongodb_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMongodbSettings", []))

    @jsii.member(jsii_name="resetMysqlSettings")
    def reset_mysql_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMysqlSettings", []))

    @jsii.member(jsii_name="resetOracleSettings")
    def reset_oracle_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOracleSettings", []))

    @jsii.member(jsii_name="resetPassword")
    def reset_password(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPassword", []))

    @jsii.member(jsii_name="resetPauseReplicationTasks")
    def reset_pause_replication_tasks(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPauseReplicationTasks", []))

    @jsii.member(jsii_name="resetPort")
    def reset_port(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPort", []))

    @jsii.member(jsii_name="resetPostgresSettings")
    def reset_postgres_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPostgresSettings", []))

    @jsii.member(jsii_name="resetRedisSettings")
    def reset_redis_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRedisSettings", []))

    @jsii.member(jsii_name="resetRedshiftSettings")
    def reset_redshift_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRedshiftSettings", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetSecretsManagerAccessRoleArn")
    def reset_secrets_manager_access_role_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecretsManagerAccessRoleArn", []))

    @jsii.member(jsii_name="resetSecretsManagerArn")
    def reset_secrets_manager_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecretsManagerArn", []))

    @jsii.member(jsii_name="resetServerName")
    def reset_server_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServerName", []))

    @jsii.member(jsii_name="resetServiceAccessRole")
    def reset_service_access_role(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServiceAccessRole", []))

    @jsii.member(jsii_name="resetSslMode")
    def reset_ssl_mode(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslMode", []))

    @jsii.member(jsii_name="resetTags")
    def reset_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTags", []))

    @jsii.member(jsii_name="resetTagsAll")
    def reset_tags_all(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTagsAll", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="resetUsername")
    def reset_username(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUsername", []))

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
    @jsii.member(jsii_name="elasticsearchSettings")
    def elasticsearch_settings(
        self,
    ) -> "DmsEndpointElasticsearchSettingsOutputReference":
        return typing.cast("DmsEndpointElasticsearchSettingsOutputReference", jsii.get(self, "elasticsearchSettings"))

    @builtins.property
    @jsii.member(jsii_name="endpointArn")
    def endpoint_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointArn"))

    @builtins.property
    @jsii.member(jsii_name="kafkaSettings")
    def kafka_settings(self) -> "DmsEndpointKafkaSettingsOutputReference":
        return typing.cast("DmsEndpointKafkaSettingsOutputReference", jsii.get(self, "kafkaSettings"))

    @builtins.property
    @jsii.member(jsii_name="kinesisSettings")
    def kinesis_settings(self) -> "DmsEndpointKinesisSettingsOutputReference":
        return typing.cast("DmsEndpointKinesisSettingsOutputReference", jsii.get(self, "kinesisSettings"))

    @builtins.property
    @jsii.member(jsii_name="mongodbSettings")
    def mongodb_settings(self) -> "DmsEndpointMongodbSettingsOutputReference":
        return typing.cast("DmsEndpointMongodbSettingsOutputReference", jsii.get(self, "mongodbSettings"))

    @builtins.property
    @jsii.member(jsii_name="mysqlSettings")
    def mysql_settings(self) -> "DmsEndpointMysqlSettingsOutputReference":
        return typing.cast("DmsEndpointMysqlSettingsOutputReference", jsii.get(self, "mysqlSettings"))

    @builtins.property
    @jsii.member(jsii_name="oracleSettings")
    def oracle_settings(self) -> "DmsEndpointOracleSettingsOutputReference":
        return typing.cast("DmsEndpointOracleSettingsOutputReference", jsii.get(self, "oracleSettings"))

    @builtins.property
    @jsii.member(jsii_name="postgresSettings")
    def postgres_settings(self) -> "DmsEndpointPostgresSettingsOutputReference":
        return typing.cast("DmsEndpointPostgresSettingsOutputReference", jsii.get(self, "postgresSettings"))

    @builtins.property
    @jsii.member(jsii_name="redisSettings")
    def redis_settings(self) -> "DmsEndpointRedisSettingsOutputReference":
        return typing.cast("DmsEndpointRedisSettingsOutputReference", jsii.get(self, "redisSettings"))

    @builtins.property
    @jsii.member(jsii_name="redshiftSettings")
    def redshift_settings(self) -> "DmsEndpointRedshiftSettingsOutputReference":
        return typing.cast("DmsEndpointRedshiftSettingsOutputReference", jsii.get(self, "redshiftSettings"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> "DmsEndpointTimeoutsOutputReference":
        return typing.cast("DmsEndpointTimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="certificateArnInput")
    def certificate_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "certificateArnInput"))

    @builtins.property
    @jsii.member(jsii_name="databaseNameInput")
    def database_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "databaseNameInput"))

    @builtins.property
    @jsii.member(jsii_name="elasticsearchSettingsInput")
    def elasticsearch_settings_input(
        self,
    ) -> typing.Optional["DmsEndpointElasticsearchSettings"]:
        return typing.cast(typing.Optional["DmsEndpointElasticsearchSettings"], jsii.get(self, "elasticsearchSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointIdInput")
    def endpoint_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointIdInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointTypeInput")
    def endpoint_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="engineNameInput")
    def engine_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "engineNameInput"))

    @builtins.property
    @jsii.member(jsii_name="extraConnectionAttributesInput")
    def extra_connection_attributes_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "extraConnectionAttributesInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="kafkaSettingsInput")
    def kafka_settings_input(self) -> typing.Optional["DmsEndpointKafkaSettings"]:
        return typing.cast(typing.Optional["DmsEndpointKafkaSettings"], jsii.get(self, "kafkaSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="kinesisSettingsInput")
    def kinesis_settings_input(self) -> typing.Optional["DmsEndpointKinesisSettings"]:
        return typing.cast(typing.Optional["DmsEndpointKinesisSettings"], jsii.get(self, "kinesisSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="kmsKeyArnInput")
    def kms_key_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "kmsKeyArnInput"))

    @builtins.property
    @jsii.member(jsii_name="mongodbSettingsInput")
    def mongodb_settings_input(self) -> typing.Optional["DmsEndpointMongodbSettings"]:
        return typing.cast(typing.Optional["DmsEndpointMongodbSettings"], jsii.get(self, "mongodbSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="mysqlSettingsInput")
    def mysql_settings_input(self) -> typing.Optional["DmsEndpointMysqlSettings"]:
        return typing.cast(typing.Optional["DmsEndpointMysqlSettings"], jsii.get(self, "mysqlSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="oracleSettingsInput")
    def oracle_settings_input(self) -> typing.Optional["DmsEndpointOracleSettings"]:
        return typing.cast(typing.Optional["DmsEndpointOracleSettings"], jsii.get(self, "oracleSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="passwordInput")
    def password_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "passwordInput"))

    @builtins.property
    @jsii.member(jsii_name="pauseReplicationTasksInput")
    def pause_replication_tasks_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "pauseReplicationTasksInput"))

    @builtins.property
    @jsii.member(jsii_name="portInput")
    def port_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "portInput"))

    @builtins.property
    @jsii.member(jsii_name="postgresSettingsInput")
    def postgres_settings_input(self) -> typing.Optional["DmsEndpointPostgresSettings"]:
        return typing.cast(typing.Optional["DmsEndpointPostgresSettings"], jsii.get(self, "postgresSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="redisSettingsInput")
    def redis_settings_input(self) -> typing.Optional["DmsEndpointRedisSettings"]:
        return typing.cast(typing.Optional["DmsEndpointRedisSettings"], jsii.get(self, "redisSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="redshiftSettingsInput")
    def redshift_settings_input(self) -> typing.Optional["DmsEndpointRedshiftSettings"]:
        return typing.cast(typing.Optional["DmsEndpointRedshiftSettings"], jsii.get(self, "redshiftSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="secretsManagerAccessRoleArnInput")
    def secrets_manager_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "secretsManagerAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="secretsManagerArnInput")
    def secrets_manager_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "secretsManagerArnInput"))

    @builtins.property
    @jsii.member(jsii_name="serverNameInput")
    def server_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serverNameInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleInput")
    def service_access_role_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleInput"))

    @builtins.property
    @jsii.member(jsii_name="sslModeInput")
    def ssl_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslModeInput"))

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
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DmsEndpointTimeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DmsEndpointTimeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="usernameInput")
    def username_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "usernameInput"))

    @builtins.property
    @jsii.member(jsii_name="certificateArn")
    def certificate_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "certificateArn"))

    @certificate_arn.setter
    def certificate_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cebc3fa4191b482073c87ab36c6537b9b139d156a3b076becc42e268a70383e4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "certificateArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="databaseName")
    def database_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "databaseName"))

    @database_name.setter
    def database_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3adffca33d9789282dfba04e7818d19fd07db031f261f3ed92a7ec1ee082fc7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "databaseName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpointId")
    def endpoint_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointId"))

    @endpoint_id.setter
    def endpoint_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__835aa38fd2b582fab4d4479d60d86f2cd3da81c3aa0b3ca2d5d64dfc1a63cda7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpointType")
    def endpoint_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointType"))

    @endpoint_type.setter
    def endpoint_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e135f511891729bd78bd62e9b36aa11457f25813fcc51ab37b888064d7632cb4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="engineName")
    def engine_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "engineName"))

    @engine_name.setter
    def engine_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d37d198f35ce56f661a88b3cea5bb794eb159955e1f0470ea337c614cfc08bb6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "engineName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="extraConnectionAttributes")
    def extra_connection_attributes(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "extraConnectionAttributes"))

    @extra_connection_attributes.setter
    def extra_connection_attributes(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8f6e473bec31336b04a394af423612cad1895d5484077251ffd9456c90746e33)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "extraConnectionAttributes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__75baa2fc42e97a8261191e0bc05381ef0e0b80a4c698a4ce81ecc190ce3706c0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="kmsKeyArn")
    def kms_key_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "kmsKeyArn"))

    @kms_key_arn.setter
    def kms_key_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__685fc18f4b03a4810c4952552326d223f2d949c850398ba510c83e12b2dec0bb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "kmsKeyArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="password")
    def password(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "password"))

    @password.setter
    def password(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d553467784269896dd783cb5e561ae83ef84d03dd4df9fa0db8f1aec88b0a19)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "password", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="pauseReplicationTasks")
    def pause_replication_tasks(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "pauseReplicationTasks"))

    @pause_replication_tasks.setter
    def pause_replication_tasks(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f626ce9d526290606ad2fc7f0df7fd40cc351c8208b958e3bbaf07b8e59a11bc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "pauseReplicationTasks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="port")
    def port(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "port"))

    @port.setter
    def port(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8f04703621e8d9841f94d1a63ba193bc33c94a2c200e4de39e40c09685e36766)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "port", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__739aec50cd48e9018e03b0e88dff9f75cb065932bb4719e3c943a3800a25c619)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="secretsManagerAccessRoleArn")
    def secrets_manager_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretsManagerAccessRoleArn"))

    @secrets_manager_access_role_arn.setter
    def secrets_manager_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99106f54f1facb2c291e0ee1720b6e7920ebf75a458ac4b57d53ca02329aea5b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "secretsManagerAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="secretsManagerArn")
    def secrets_manager_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "secretsManagerArn"))

    @secrets_manager_arn.setter
    def secrets_manager_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26e10e4cd3dbb3ada2e06b1b973469ab1883f4dd05845d74cbfd8e292de4aa13)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "secretsManagerArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serverName")
    def server_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serverName"))

    @server_name.setter
    def server_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c1af796ee69fd0136f4799081edafda89f7bbd5ce723a7ece3b48e380622254b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serverName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRole")
    def service_access_role(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRole"))

    @service_access_role.setter
    def service_access_role(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b9b3258ac4a714fc5ce58be8fae2a570646c5cf4b736297e245dadf7675726dd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRole", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslMode")
    def ssl_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslMode"))

    @ssl_mode.setter
    def ssl_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6211382e30ba6cd00299fd701ef0c819ccc5761011a2deac9cee28ecc1395cf0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dd21707b73c2ab70bf8566a32a3d595d6986164415f38793c9b306bba4ef623a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tagsAll")
    def tags_all(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tagsAll"))

    @tags_all.setter
    def tags_all(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__73ad004a62dab574dbd4a1a0d2607df02109106b4cdfdd0b52206b9422c7390d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tagsAll", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="username")
    def username(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "username"))

    @username.setter
    def username(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8aa7413373abbac26dc905582bc4eee5e21137057d4adddbc8de2f1050fd23da)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "username", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "endpoint_id": "endpointId",
        "endpoint_type": "endpointType",
        "engine_name": "engineName",
        "certificate_arn": "certificateArn",
        "database_name": "databaseName",
        "elasticsearch_settings": "elasticsearchSettings",
        "extra_connection_attributes": "extraConnectionAttributes",
        "id": "id",
        "kafka_settings": "kafkaSettings",
        "kinesis_settings": "kinesisSettings",
        "kms_key_arn": "kmsKeyArn",
        "mongodb_settings": "mongodbSettings",
        "mysql_settings": "mysqlSettings",
        "oracle_settings": "oracleSettings",
        "password": "password",
        "pause_replication_tasks": "pauseReplicationTasks",
        "port": "port",
        "postgres_settings": "postgresSettings",
        "redis_settings": "redisSettings",
        "redshift_settings": "redshiftSettings",
        "region": "region",
        "secrets_manager_access_role_arn": "secretsManagerAccessRoleArn",
        "secrets_manager_arn": "secretsManagerArn",
        "server_name": "serverName",
        "service_access_role": "serviceAccessRole",
        "ssl_mode": "sslMode",
        "tags": "tags",
        "tags_all": "tagsAll",
        "timeouts": "timeouts",
        "username": "username",
    },
)
class DmsEndpointConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        endpoint_id: builtins.str,
        endpoint_type: builtins.str,
        engine_name: builtins.str,
        certificate_arn: typing.Optional[builtins.str] = None,
        database_name: typing.Optional[builtins.str] = None,
        elasticsearch_settings: typing.Optional[typing.Union["DmsEndpointElasticsearchSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        extra_connection_attributes: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        kafka_settings: typing.Optional[typing.Union["DmsEndpointKafkaSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        kinesis_settings: typing.Optional[typing.Union["DmsEndpointKinesisSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        kms_key_arn: typing.Optional[builtins.str] = None,
        mongodb_settings: typing.Optional[typing.Union["DmsEndpointMongodbSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        mysql_settings: typing.Optional[typing.Union["DmsEndpointMysqlSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        oracle_settings: typing.Optional[typing.Union["DmsEndpointOracleSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        password: typing.Optional[builtins.str] = None,
        pause_replication_tasks: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        port: typing.Optional[jsii.Number] = None,
        postgres_settings: typing.Optional[typing.Union["DmsEndpointPostgresSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        redis_settings: typing.Optional[typing.Union["DmsEndpointRedisSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        redshift_settings: typing.Optional[typing.Union["DmsEndpointRedshiftSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        region: typing.Optional[builtins.str] = None,
        secrets_manager_access_role_arn: typing.Optional[builtins.str] = None,
        secrets_manager_arn: typing.Optional[builtins.str] = None,
        server_name: typing.Optional[builtins.str] = None,
        service_access_role: typing.Optional[builtins.str] = None,
        ssl_mode: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union["DmsEndpointTimeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        username: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param endpoint_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_id DmsEndpoint#endpoint_id}.
        :param endpoint_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_type DmsEndpoint#endpoint_type}.
        :param engine_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#engine_name DmsEndpoint#engine_name}.
        :param certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#certificate_arn DmsEndpoint#certificate_arn}.
        :param database_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_name DmsEndpoint#database_name}.
        :param elasticsearch_settings: elasticsearch_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#elasticsearch_settings DmsEndpoint#elasticsearch_settings}
        :param extra_connection_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extra_connection_attributes DmsEndpoint#extra_connection_attributes}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#id DmsEndpoint#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param kafka_settings: kafka_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kafka_settings DmsEndpoint#kafka_settings}
        :param kinesis_settings: kinesis_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kinesis_settings DmsEndpoint#kinesis_settings}
        :param kms_key_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kms_key_arn DmsEndpoint#kms_key_arn}.
        :param mongodb_settings: mongodb_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mongodb_settings DmsEndpoint#mongodb_settings}
        :param mysql_settings: mysql_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mysql_settings DmsEndpoint#mysql_settings}
        :param oracle_settings: oracle_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#oracle_settings DmsEndpoint#oracle_settings}
        :param password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#password DmsEndpoint#password}.
        :param pause_replication_tasks: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#pause_replication_tasks DmsEndpoint#pause_replication_tasks}.
        :param port: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.
        :param postgres_settings: postgres_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#postgres_settings DmsEndpoint#postgres_settings}
        :param redis_settings: redis_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redis_settings DmsEndpoint#redis_settings}
        :param redshift_settings: redshift_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redshift_settings DmsEndpoint#redshift_settings}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#region DmsEndpoint#region}
        :param secrets_manager_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_access_role_arn DmsEndpoint#secrets_manager_access_role_arn}.
        :param secrets_manager_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_arn DmsEndpoint#secrets_manager_arn}.
        :param server_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.
        :param service_access_role: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role DmsEndpoint#service_access_role}.
        :param ssl_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_mode DmsEndpoint#ssl_mode}.
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags DmsEndpoint#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags_all DmsEndpoint#tags_all}.
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#timeouts DmsEndpoint#timeouts}
        :param username: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#username DmsEndpoint#username}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(elasticsearch_settings, dict):
            elasticsearch_settings = DmsEndpointElasticsearchSettings(**elasticsearch_settings)
        if isinstance(kafka_settings, dict):
            kafka_settings = DmsEndpointKafkaSettings(**kafka_settings)
        if isinstance(kinesis_settings, dict):
            kinesis_settings = DmsEndpointKinesisSettings(**kinesis_settings)
        if isinstance(mongodb_settings, dict):
            mongodb_settings = DmsEndpointMongodbSettings(**mongodb_settings)
        if isinstance(mysql_settings, dict):
            mysql_settings = DmsEndpointMysqlSettings(**mysql_settings)
        if isinstance(oracle_settings, dict):
            oracle_settings = DmsEndpointOracleSettings(**oracle_settings)
        if isinstance(postgres_settings, dict):
            postgres_settings = DmsEndpointPostgresSettings(**postgres_settings)
        if isinstance(redis_settings, dict):
            redis_settings = DmsEndpointRedisSettings(**redis_settings)
        if isinstance(redshift_settings, dict):
            redshift_settings = DmsEndpointRedshiftSettings(**redshift_settings)
        if isinstance(timeouts, dict):
            timeouts = DmsEndpointTimeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f63b4535dcb041179f8b16b4b49939ed5db85d38d11371d703a88a03460441c)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument endpoint_id", value=endpoint_id, expected_type=type_hints["endpoint_id"])
            check_type(argname="argument endpoint_type", value=endpoint_type, expected_type=type_hints["endpoint_type"])
            check_type(argname="argument engine_name", value=engine_name, expected_type=type_hints["engine_name"])
            check_type(argname="argument certificate_arn", value=certificate_arn, expected_type=type_hints["certificate_arn"])
            check_type(argname="argument database_name", value=database_name, expected_type=type_hints["database_name"])
            check_type(argname="argument elasticsearch_settings", value=elasticsearch_settings, expected_type=type_hints["elasticsearch_settings"])
            check_type(argname="argument extra_connection_attributes", value=extra_connection_attributes, expected_type=type_hints["extra_connection_attributes"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument kafka_settings", value=kafka_settings, expected_type=type_hints["kafka_settings"])
            check_type(argname="argument kinesis_settings", value=kinesis_settings, expected_type=type_hints["kinesis_settings"])
            check_type(argname="argument kms_key_arn", value=kms_key_arn, expected_type=type_hints["kms_key_arn"])
            check_type(argname="argument mongodb_settings", value=mongodb_settings, expected_type=type_hints["mongodb_settings"])
            check_type(argname="argument mysql_settings", value=mysql_settings, expected_type=type_hints["mysql_settings"])
            check_type(argname="argument oracle_settings", value=oracle_settings, expected_type=type_hints["oracle_settings"])
            check_type(argname="argument password", value=password, expected_type=type_hints["password"])
            check_type(argname="argument pause_replication_tasks", value=pause_replication_tasks, expected_type=type_hints["pause_replication_tasks"])
            check_type(argname="argument port", value=port, expected_type=type_hints["port"])
            check_type(argname="argument postgres_settings", value=postgres_settings, expected_type=type_hints["postgres_settings"])
            check_type(argname="argument redis_settings", value=redis_settings, expected_type=type_hints["redis_settings"])
            check_type(argname="argument redshift_settings", value=redshift_settings, expected_type=type_hints["redshift_settings"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument secrets_manager_access_role_arn", value=secrets_manager_access_role_arn, expected_type=type_hints["secrets_manager_access_role_arn"])
            check_type(argname="argument secrets_manager_arn", value=secrets_manager_arn, expected_type=type_hints["secrets_manager_arn"])
            check_type(argname="argument server_name", value=server_name, expected_type=type_hints["server_name"])
            check_type(argname="argument service_access_role", value=service_access_role, expected_type=type_hints["service_access_role"])
            check_type(argname="argument ssl_mode", value=ssl_mode, expected_type=type_hints["ssl_mode"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument tags_all", value=tags_all, expected_type=type_hints["tags_all"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
            check_type(argname="argument username", value=username, expected_type=type_hints["username"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "endpoint_id": endpoint_id,
            "endpoint_type": endpoint_type,
            "engine_name": engine_name,
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
        if certificate_arn is not None:
            self._values["certificate_arn"] = certificate_arn
        if database_name is not None:
            self._values["database_name"] = database_name
        if elasticsearch_settings is not None:
            self._values["elasticsearch_settings"] = elasticsearch_settings
        if extra_connection_attributes is not None:
            self._values["extra_connection_attributes"] = extra_connection_attributes
        if id is not None:
            self._values["id"] = id
        if kafka_settings is not None:
            self._values["kafka_settings"] = kafka_settings
        if kinesis_settings is not None:
            self._values["kinesis_settings"] = kinesis_settings
        if kms_key_arn is not None:
            self._values["kms_key_arn"] = kms_key_arn
        if mongodb_settings is not None:
            self._values["mongodb_settings"] = mongodb_settings
        if mysql_settings is not None:
            self._values["mysql_settings"] = mysql_settings
        if oracle_settings is not None:
            self._values["oracle_settings"] = oracle_settings
        if password is not None:
            self._values["password"] = password
        if pause_replication_tasks is not None:
            self._values["pause_replication_tasks"] = pause_replication_tasks
        if port is not None:
            self._values["port"] = port
        if postgres_settings is not None:
            self._values["postgres_settings"] = postgres_settings
        if redis_settings is not None:
            self._values["redis_settings"] = redis_settings
        if redshift_settings is not None:
            self._values["redshift_settings"] = redshift_settings
        if region is not None:
            self._values["region"] = region
        if secrets_manager_access_role_arn is not None:
            self._values["secrets_manager_access_role_arn"] = secrets_manager_access_role_arn
        if secrets_manager_arn is not None:
            self._values["secrets_manager_arn"] = secrets_manager_arn
        if server_name is not None:
            self._values["server_name"] = server_name
        if service_access_role is not None:
            self._values["service_access_role"] = service_access_role
        if ssl_mode is not None:
            self._values["ssl_mode"] = ssl_mode
        if tags is not None:
            self._values["tags"] = tags
        if tags_all is not None:
            self._values["tags_all"] = tags_all
        if timeouts is not None:
            self._values["timeouts"] = timeouts
        if username is not None:
            self._values["username"] = username

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
    def endpoint_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_id DmsEndpoint#endpoint_id}.'''
        result = self._values.get("endpoint_id")
        assert result is not None, "Required property 'endpoint_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def endpoint_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_type DmsEndpoint#endpoint_type}.'''
        result = self._values.get("endpoint_type")
        assert result is not None, "Required property 'endpoint_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def engine_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#engine_name DmsEndpoint#engine_name}.'''
        result = self._values.get("engine_name")
        assert result is not None, "Required property 'engine_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def certificate_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#certificate_arn DmsEndpoint#certificate_arn}.'''
        result = self._values.get("certificate_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def database_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_name DmsEndpoint#database_name}.'''
        result = self._values.get("database_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def elasticsearch_settings(
        self,
    ) -> typing.Optional["DmsEndpointElasticsearchSettings"]:
        '''elasticsearch_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#elasticsearch_settings DmsEndpoint#elasticsearch_settings}
        '''
        result = self._values.get("elasticsearch_settings")
        return typing.cast(typing.Optional["DmsEndpointElasticsearchSettings"], result)

    @builtins.property
    def extra_connection_attributes(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extra_connection_attributes DmsEndpoint#extra_connection_attributes}.'''
        result = self._values.get("extra_connection_attributes")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#id DmsEndpoint#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kafka_settings(self) -> typing.Optional["DmsEndpointKafkaSettings"]:
        '''kafka_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kafka_settings DmsEndpoint#kafka_settings}
        '''
        result = self._values.get("kafka_settings")
        return typing.cast(typing.Optional["DmsEndpointKafkaSettings"], result)

    @builtins.property
    def kinesis_settings(self) -> typing.Optional["DmsEndpointKinesisSettings"]:
        '''kinesis_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kinesis_settings DmsEndpoint#kinesis_settings}
        '''
        result = self._values.get("kinesis_settings")
        return typing.cast(typing.Optional["DmsEndpointKinesisSettings"], result)

    @builtins.property
    def kms_key_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#kms_key_arn DmsEndpoint#kms_key_arn}.'''
        result = self._values.get("kms_key_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def mongodb_settings(self) -> typing.Optional["DmsEndpointMongodbSettings"]:
        '''mongodb_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mongodb_settings DmsEndpoint#mongodb_settings}
        '''
        result = self._values.get("mongodb_settings")
        return typing.cast(typing.Optional["DmsEndpointMongodbSettings"], result)

    @builtins.property
    def mysql_settings(self) -> typing.Optional["DmsEndpointMysqlSettings"]:
        '''mysql_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#mysql_settings DmsEndpoint#mysql_settings}
        '''
        result = self._values.get("mysql_settings")
        return typing.cast(typing.Optional["DmsEndpointMysqlSettings"], result)

    @builtins.property
    def oracle_settings(self) -> typing.Optional["DmsEndpointOracleSettings"]:
        '''oracle_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#oracle_settings DmsEndpoint#oracle_settings}
        '''
        result = self._values.get("oracle_settings")
        return typing.cast(typing.Optional["DmsEndpointOracleSettings"], result)

    @builtins.property
    def password(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#password DmsEndpoint#password}.'''
        result = self._values.get("password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pause_replication_tasks(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#pause_replication_tasks DmsEndpoint#pause_replication_tasks}.'''
        result = self._values.get("pause_replication_tasks")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def port(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.'''
        result = self._values.get("port")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def postgres_settings(self) -> typing.Optional["DmsEndpointPostgresSettings"]:
        '''postgres_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#postgres_settings DmsEndpoint#postgres_settings}
        '''
        result = self._values.get("postgres_settings")
        return typing.cast(typing.Optional["DmsEndpointPostgresSettings"], result)

    @builtins.property
    def redis_settings(self) -> typing.Optional["DmsEndpointRedisSettings"]:
        '''redis_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redis_settings DmsEndpoint#redis_settings}
        '''
        result = self._values.get("redis_settings")
        return typing.cast(typing.Optional["DmsEndpointRedisSettings"], result)

    @builtins.property
    def redshift_settings(self) -> typing.Optional["DmsEndpointRedshiftSettings"]:
        '''redshift_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#redshift_settings DmsEndpoint#redshift_settings}
        '''
        result = self._values.get("redshift_settings")
        return typing.cast(typing.Optional["DmsEndpointRedshiftSettings"], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#region DmsEndpoint#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def secrets_manager_access_role_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_access_role_arn DmsEndpoint#secrets_manager_access_role_arn}.'''
        result = self._values.get("secrets_manager_access_role_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def secrets_manager_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#secrets_manager_arn DmsEndpoint#secrets_manager_arn}.'''
        result = self._values.get("secrets_manager_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def server_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.'''
        result = self._values.get("server_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_access_role(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role DmsEndpoint#service_access_role}.'''
        result = self._values.get("service_access_role")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_mode(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_mode DmsEndpoint#ssl_mode}.'''
        result = self._values.get("ssl_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags DmsEndpoint#tags}.'''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def tags_all(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#tags_all DmsEndpoint#tags_all}.'''
        result = self._values.get("tags_all")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["DmsEndpointTimeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#timeouts DmsEndpoint#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["DmsEndpointTimeouts"], result)

    @builtins.property
    def username(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#username DmsEndpoint#username}.'''
        result = self._values.get("username")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointElasticsearchSettings",
    jsii_struct_bases=[],
    name_mapping={
        "endpoint_uri": "endpointUri",
        "service_access_role_arn": "serviceAccessRoleArn",
        "error_retry_duration": "errorRetryDuration",
        "full_load_error_percentage": "fullLoadErrorPercentage",
        "use_new_mapping_type": "useNewMappingType",
    },
)
class DmsEndpointElasticsearchSettings:
    def __init__(
        self,
        *,
        endpoint_uri: builtins.str,
        service_access_role_arn: builtins.str,
        error_retry_duration: typing.Optional[jsii.Number] = None,
        full_load_error_percentage: typing.Optional[jsii.Number] = None,
        use_new_mapping_type: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param endpoint_uri: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_uri DmsEndpoint#endpoint_uri}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param error_retry_duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#error_retry_duration DmsEndpoint#error_retry_duration}.
        :param full_load_error_percentage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#full_load_error_percentage DmsEndpoint#full_load_error_percentage}.
        :param use_new_mapping_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_new_mapping_type DmsEndpoint#use_new_mapping_type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__80b20329fa59319406e971f29756c823d39d08290b3116d710cb84d35635086f)
            check_type(argname="argument endpoint_uri", value=endpoint_uri, expected_type=type_hints["endpoint_uri"])
            check_type(argname="argument service_access_role_arn", value=service_access_role_arn, expected_type=type_hints["service_access_role_arn"])
            check_type(argname="argument error_retry_duration", value=error_retry_duration, expected_type=type_hints["error_retry_duration"])
            check_type(argname="argument full_load_error_percentage", value=full_load_error_percentage, expected_type=type_hints["full_load_error_percentage"])
            check_type(argname="argument use_new_mapping_type", value=use_new_mapping_type, expected_type=type_hints["use_new_mapping_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "endpoint_uri": endpoint_uri,
            "service_access_role_arn": service_access_role_arn,
        }
        if error_retry_duration is not None:
            self._values["error_retry_duration"] = error_retry_duration
        if full_load_error_percentage is not None:
            self._values["full_load_error_percentage"] = full_load_error_percentage
        if use_new_mapping_type is not None:
            self._values["use_new_mapping_type"] = use_new_mapping_type

    @builtins.property
    def endpoint_uri(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#endpoint_uri DmsEndpoint#endpoint_uri}.'''
        result = self._values.get("endpoint_uri")
        assert result is not None, "Required property 'endpoint_uri' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def service_access_role_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.'''
        result = self._values.get("service_access_role_arn")
        assert result is not None, "Required property 'service_access_role_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def error_retry_duration(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#error_retry_duration DmsEndpoint#error_retry_duration}.'''
        result = self._values.get("error_retry_duration")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def full_load_error_percentage(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#full_load_error_percentage DmsEndpoint#full_load_error_percentage}.'''
        result = self._values.get("full_load_error_percentage")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def use_new_mapping_type(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_new_mapping_type DmsEndpoint#use_new_mapping_type}.'''
        result = self._values.get("use_new_mapping_type")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointElasticsearchSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointElasticsearchSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointElasticsearchSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b38f1d1980795ca04bc8017e7b97d67ac892352fd0d698c9b9404cee51544bc3)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetErrorRetryDuration")
    def reset_error_retry_duration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetErrorRetryDuration", []))

    @jsii.member(jsii_name="resetFullLoadErrorPercentage")
    def reset_full_load_error_percentage(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetFullLoadErrorPercentage", []))

    @jsii.member(jsii_name="resetUseNewMappingType")
    def reset_use_new_mapping_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseNewMappingType", []))

    @builtins.property
    @jsii.member(jsii_name="endpointUriInput")
    def endpoint_uri_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointUriInput"))

    @builtins.property
    @jsii.member(jsii_name="errorRetryDurationInput")
    def error_retry_duration_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "errorRetryDurationInput"))

    @builtins.property
    @jsii.member(jsii_name="fullLoadErrorPercentageInput")
    def full_load_error_percentage_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "fullLoadErrorPercentageInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArnInput")
    def service_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="useNewMappingTypeInput")
    def use_new_mapping_type_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useNewMappingTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointUri")
    def endpoint_uri(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpointUri"))

    @endpoint_uri.setter
    def endpoint_uri(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9922f514b45243459312729bde5d200acb94cb53f874671c5152a9bcb62aa8ed)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpointUri", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="errorRetryDuration")
    def error_retry_duration(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "errorRetryDuration"))

    @error_retry_duration.setter
    def error_retry_duration(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37c6badd2b28bd9edc461cfd3edac36d4247b6171d5387d9b10ab7939f4d03fe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "errorRetryDuration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullLoadErrorPercentage")
    def full_load_error_percentage(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "fullLoadErrorPercentage"))

    @full_load_error_percentage.setter
    def full_load_error_percentage(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8387c3106ddda203d6b798e812360a4825b09707cde831abc5fa4d6f5f7a52e9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullLoadErrorPercentage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArn")
    def service_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRoleArn"))

    @service_access_role_arn.setter
    def service_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82e8915124061e0e9fdd03750cbbe1e3abbdd57fd4c0fb8090ed209e71e9cb89)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useNewMappingType")
    def use_new_mapping_type(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "useNewMappingType"))

    @use_new_mapping_type.setter
    def use_new_mapping_type(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d043df6b98ac5e5fab92e160f5a1e0d09579a0d0c3c9ef7066e2a3fdd25b9a4a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useNewMappingType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointElasticsearchSettings]:
        return typing.cast(typing.Optional[DmsEndpointElasticsearchSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DmsEndpointElasticsearchSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8513f0e705c2bb03f77aaf456e2750415450d06a31c1f0b32357485ebd0f9b4b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointKafkaSettings",
    jsii_struct_bases=[],
    name_mapping={
        "broker": "broker",
        "include_control_details": "includeControlDetails",
        "include_null_and_empty": "includeNullAndEmpty",
        "include_partition_value": "includePartitionValue",
        "include_table_alter_operations": "includeTableAlterOperations",
        "include_transaction_details": "includeTransactionDetails",
        "message_format": "messageFormat",
        "message_max_bytes": "messageMaxBytes",
        "no_hex_prefix": "noHexPrefix",
        "partition_include_schema_table": "partitionIncludeSchemaTable",
        "sasl_mechanism": "saslMechanism",
        "sasl_password": "saslPassword",
        "sasl_username": "saslUsername",
        "security_protocol": "securityProtocol",
        "ssl_ca_certificate_arn": "sslCaCertificateArn",
        "ssl_client_certificate_arn": "sslClientCertificateArn",
        "ssl_client_key_arn": "sslClientKeyArn",
        "ssl_client_key_password": "sslClientKeyPassword",
        "topic": "topic",
    },
)
class DmsEndpointKafkaSettings:
    def __init__(
        self,
        *,
        broker: builtins.str,
        include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        message_format: typing.Optional[builtins.str] = None,
        message_max_bytes: typing.Optional[jsii.Number] = None,
        no_hex_prefix: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        sasl_mechanism: typing.Optional[builtins.str] = None,
        sasl_password: typing.Optional[builtins.str] = None,
        sasl_username: typing.Optional[builtins.str] = None,
        security_protocol: typing.Optional[builtins.str] = None,
        ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_client_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_client_key_arn: typing.Optional[builtins.str] = None,
        ssl_client_key_password: typing.Optional[builtins.str] = None,
        topic: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param broker: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#broker DmsEndpoint#broker}.
        :param include_control_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.
        :param include_null_and_empty: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.
        :param include_partition_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.
        :param include_table_alter_operations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.
        :param include_transaction_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.
        :param message_format: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.
        :param message_max_bytes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_max_bytes DmsEndpoint#message_max_bytes}.
        :param no_hex_prefix: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#no_hex_prefix DmsEndpoint#no_hex_prefix}.
        :param partition_include_schema_table: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.
        :param sasl_mechanism: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_mechanism DmsEndpoint#sasl_mechanism}.
        :param sasl_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_password DmsEndpoint#sasl_password}.
        :param sasl_username: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_username DmsEndpoint#sasl_username}.
        :param security_protocol: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#security_protocol DmsEndpoint#security_protocol}.
        :param ssl_ca_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.
        :param ssl_client_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_certificate_arn DmsEndpoint#ssl_client_certificate_arn}.
        :param ssl_client_key_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_arn DmsEndpoint#ssl_client_key_arn}.
        :param ssl_client_key_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_password DmsEndpoint#ssl_client_key_password}.
        :param topic: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#topic DmsEndpoint#topic}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0fa6da922b4d6ea7ecf9ba280c680fdedb96557ef753a2eef2dd4f1bc20674ad)
            check_type(argname="argument broker", value=broker, expected_type=type_hints["broker"])
            check_type(argname="argument include_control_details", value=include_control_details, expected_type=type_hints["include_control_details"])
            check_type(argname="argument include_null_and_empty", value=include_null_and_empty, expected_type=type_hints["include_null_and_empty"])
            check_type(argname="argument include_partition_value", value=include_partition_value, expected_type=type_hints["include_partition_value"])
            check_type(argname="argument include_table_alter_operations", value=include_table_alter_operations, expected_type=type_hints["include_table_alter_operations"])
            check_type(argname="argument include_transaction_details", value=include_transaction_details, expected_type=type_hints["include_transaction_details"])
            check_type(argname="argument message_format", value=message_format, expected_type=type_hints["message_format"])
            check_type(argname="argument message_max_bytes", value=message_max_bytes, expected_type=type_hints["message_max_bytes"])
            check_type(argname="argument no_hex_prefix", value=no_hex_prefix, expected_type=type_hints["no_hex_prefix"])
            check_type(argname="argument partition_include_schema_table", value=partition_include_schema_table, expected_type=type_hints["partition_include_schema_table"])
            check_type(argname="argument sasl_mechanism", value=sasl_mechanism, expected_type=type_hints["sasl_mechanism"])
            check_type(argname="argument sasl_password", value=sasl_password, expected_type=type_hints["sasl_password"])
            check_type(argname="argument sasl_username", value=sasl_username, expected_type=type_hints["sasl_username"])
            check_type(argname="argument security_protocol", value=security_protocol, expected_type=type_hints["security_protocol"])
            check_type(argname="argument ssl_ca_certificate_arn", value=ssl_ca_certificate_arn, expected_type=type_hints["ssl_ca_certificate_arn"])
            check_type(argname="argument ssl_client_certificate_arn", value=ssl_client_certificate_arn, expected_type=type_hints["ssl_client_certificate_arn"])
            check_type(argname="argument ssl_client_key_arn", value=ssl_client_key_arn, expected_type=type_hints["ssl_client_key_arn"])
            check_type(argname="argument ssl_client_key_password", value=ssl_client_key_password, expected_type=type_hints["ssl_client_key_password"])
            check_type(argname="argument topic", value=topic, expected_type=type_hints["topic"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "broker": broker,
        }
        if include_control_details is not None:
            self._values["include_control_details"] = include_control_details
        if include_null_and_empty is not None:
            self._values["include_null_and_empty"] = include_null_and_empty
        if include_partition_value is not None:
            self._values["include_partition_value"] = include_partition_value
        if include_table_alter_operations is not None:
            self._values["include_table_alter_operations"] = include_table_alter_operations
        if include_transaction_details is not None:
            self._values["include_transaction_details"] = include_transaction_details
        if message_format is not None:
            self._values["message_format"] = message_format
        if message_max_bytes is not None:
            self._values["message_max_bytes"] = message_max_bytes
        if no_hex_prefix is not None:
            self._values["no_hex_prefix"] = no_hex_prefix
        if partition_include_schema_table is not None:
            self._values["partition_include_schema_table"] = partition_include_schema_table
        if sasl_mechanism is not None:
            self._values["sasl_mechanism"] = sasl_mechanism
        if sasl_password is not None:
            self._values["sasl_password"] = sasl_password
        if sasl_username is not None:
            self._values["sasl_username"] = sasl_username
        if security_protocol is not None:
            self._values["security_protocol"] = security_protocol
        if ssl_ca_certificate_arn is not None:
            self._values["ssl_ca_certificate_arn"] = ssl_ca_certificate_arn
        if ssl_client_certificate_arn is not None:
            self._values["ssl_client_certificate_arn"] = ssl_client_certificate_arn
        if ssl_client_key_arn is not None:
            self._values["ssl_client_key_arn"] = ssl_client_key_arn
        if ssl_client_key_password is not None:
            self._values["ssl_client_key_password"] = ssl_client_key_password
        if topic is not None:
            self._values["topic"] = topic

    @builtins.property
    def broker(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#broker DmsEndpoint#broker}.'''
        result = self._values.get("broker")
        assert result is not None, "Required property 'broker' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def include_control_details(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.'''
        result = self._values.get("include_control_details")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_null_and_empty(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.'''
        result = self._values.get("include_null_and_empty")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_partition_value(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.'''
        result = self._values.get("include_partition_value")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_table_alter_operations(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.'''
        result = self._values.get("include_table_alter_operations")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_transaction_details(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.'''
        result = self._values.get("include_transaction_details")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def message_format(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.'''
        result = self._values.get("message_format")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def message_max_bytes(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_max_bytes DmsEndpoint#message_max_bytes}.'''
        result = self._values.get("message_max_bytes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def no_hex_prefix(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#no_hex_prefix DmsEndpoint#no_hex_prefix}.'''
        result = self._values.get("no_hex_prefix")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def partition_include_schema_table(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.'''
        result = self._values.get("partition_include_schema_table")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def sasl_mechanism(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_mechanism DmsEndpoint#sasl_mechanism}.'''
        result = self._values.get("sasl_mechanism")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sasl_password(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_password DmsEndpoint#sasl_password}.'''
        result = self._values.get("sasl_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sasl_username(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#sasl_username DmsEndpoint#sasl_username}.'''
        result = self._values.get("sasl_username")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_protocol(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#security_protocol DmsEndpoint#security_protocol}.'''
        result = self._values.get("security_protocol")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_ca_certificate_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.'''
        result = self._values.get("ssl_ca_certificate_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_client_certificate_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_certificate_arn DmsEndpoint#ssl_client_certificate_arn}.'''
        result = self._values.get("ssl_client_certificate_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_client_key_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_arn DmsEndpoint#ssl_client_key_arn}.'''
        result = self._values.get("ssl_client_key_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_client_key_password(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_client_key_password DmsEndpoint#ssl_client_key_password}.'''
        result = self._values.get("ssl_client_key_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def topic(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#topic DmsEndpoint#topic}.'''
        result = self._values.get("topic")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointKafkaSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointKafkaSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointKafkaSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__4826dd7535cb2a7c7046fdb6d13758c081f45675a92801c27de2be1129e64f05)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIncludeControlDetails")
    def reset_include_control_details(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeControlDetails", []))

    @jsii.member(jsii_name="resetIncludeNullAndEmpty")
    def reset_include_null_and_empty(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeNullAndEmpty", []))

    @jsii.member(jsii_name="resetIncludePartitionValue")
    def reset_include_partition_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludePartitionValue", []))

    @jsii.member(jsii_name="resetIncludeTableAlterOperations")
    def reset_include_table_alter_operations(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeTableAlterOperations", []))

    @jsii.member(jsii_name="resetIncludeTransactionDetails")
    def reset_include_transaction_details(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeTransactionDetails", []))

    @jsii.member(jsii_name="resetMessageFormat")
    def reset_message_format(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMessageFormat", []))

    @jsii.member(jsii_name="resetMessageMaxBytes")
    def reset_message_max_bytes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMessageMaxBytes", []))

    @jsii.member(jsii_name="resetNoHexPrefix")
    def reset_no_hex_prefix(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNoHexPrefix", []))

    @jsii.member(jsii_name="resetPartitionIncludeSchemaTable")
    def reset_partition_include_schema_table(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPartitionIncludeSchemaTable", []))

    @jsii.member(jsii_name="resetSaslMechanism")
    def reset_sasl_mechanism(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSaslMechanism", []))

    @jsii.member(jsii_name="resetSaslPassword")
    def reset_sasl_password(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSaslPassword", []))

    @jsii.member(jsii_name="resetSaslUsername")
    def reset_sasl_username(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSaslUsername", []))

    @jsii.member(jsii_name="resetSecurityProtocol")
    def reset_security_protocol(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSecurityProtocol", []))

    @jsii.member(jsii_name="resetSslCaCertificateArn")
    def reset_ssl_ca_certificate_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslCaCertificateArn", []))

    @jsii.member(jsii_name="resetSslClientCertificateArn")
    def reset_ssl_client_certificate_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslClientCertificateArn", []))

    @jsii.member(jsii_name="resetSslClientKeyArn")
    def reset_ssl_client_key_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslClientKeyArn", []))

    @jsii.member(jsii_name="resetSslClientKeyPassword")
    def reset_ssl_client_key_password(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslClientKeyPassword", []))

    @jsii.member(jsii_name="resetTopic")
    def reset_topic(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTopic", []))

    @builtins.property
    @jsii.member(jsii_name="brokerInput")
    def broker_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "brokerInput"))

    @builtins.property
    @jsii.member(jsii_name="includeControlDetailsInput")
    def include_control_details_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeControlDetailsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeNullAndEmptyInput")
    def include_null_and_empty_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeNullAndEmptyInput"))

    @builtins.property
    @jsii.member(jsii_name="includePartitionValueInput")
    def include_partition_value_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includePartitionValueInput"))

    @builtins.property
    @jsii.member(jsii_name="includeTableAlterOperationsInput")
    def include_table_alter_operations_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeTableAlterOperationsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeTransactionDetailsInput")
    def include_transaction_details_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeTransactionDetailsInput"))

    @builtins.property
    @jsii.member(jsii_name="messageFormatInput")
    def message_format_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "messageFormatInput"))

    @builtins.property
    @jsii.member(jsii_name="messageMaxBytesInput")
    def message_max_bytes_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "messageMaxBytesInput"))

    @builtins.property
    @jsii.member(jsii_name="noHexPrefixInput")
    def no_hex_prefix_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "noHexPrefixInput"))

    @builtins.property
    @jsii.member(jsii_name="partitionIncludeSchemaTableInput")
    def partition_include_schema_table_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "partitionIncludeSchemaTableInput"))

    @builtins.property
    @jsii.member(jsii_name="saslMechanismInput")
    def sasl_mechanism_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "saslMechanismInput"))

    @builtins.property
    @jsii.member(jsii_name="saslPasswordInput")
    def sasl_password_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "saslPasswordInput"))

    @builtins.property
    @jsii.member(jsii_name="saslUsernameInput")
    def sasl_username_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "saslUsernameInput"))

    @builtins.property
    @jsii.member(jsii_name="securityProtocolInput")
    def security_protocol_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "securityProtocolInput"))

    @builtins.property
    @jsii.member(jsii_name="sslCaCertificateArnInput")
    def ssl_ca_certificate_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslCaCertificateArnInput"))

    @builtins.property
    @jsii.member(jsii_name="sslClientCertificateArnInput")
    def ssl_client_certificate_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslClientCertificateArnInput"))

    @builtins.property
    @jsii.member(jsii_name="sslClientKeyArnInput")
    def ssl_client_key_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslClientKeyArnInput"))

    @builtins.property
    @jsii.member(jsii_name="sslClientKeyPasswordInput")
    def ssl_client_key_password_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslClientKeyPasswordInput"))

    @builtins.property
    @jsii.member(jsii_name="topicInput")
    def topic_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "topicInput"))

    @builtins.property
    @jsii.member(jsii_name="broker")
    def broker(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "broker"))

    @broker.setter
    def broker(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5668c4a1246844437ce773676e3c93ab47c44fa2a6cd24aedc5210ebeebbc897)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "broker", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeControlDetails")
    def include_control_details(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeControlDetails"))

    @include_control_details.setter
    def include_control_details(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a3d99476eecbdc431c06af1e82086bcc2af58c1e36609929c679278183f0dd6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeControlDetails", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeNullAndEmpty")
    def include_null_and_empty(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeNullAndEmpty"))

    @include_null_and_empty.setter
    def include_null_and_empty(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f4b9371fc1660ef038a3f418e8b7447cb3301b0286348a81975de474a8bdb87d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeNullAndEmpty", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includePartitionValue")
    def include_partition_value(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includePartitionValue"))

    @include_partition_value.setter
    def include_partition_value(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f9015006cc78b9397936c538050def7dbe63f8fbb5a5bef520065c321bb5b67)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includePartitionValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeTableAlterOperations")
    def include_table_alter_operations(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeTableAlterOperations"))

    @include_table_alter_operations.setter
    def include_table_alter_operations(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d9022cb432b3f3d9b21491953c62ce6325adec9e5932a3729a9626205e69ead2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeTableAlterOperations", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeTransactionDetails")
    def include_transaction_details(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeTransactionDetails"))

    @include_transaction_details.setter
    def include_transaction_details(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be4b6d755c6257bcfbf6e7ee55a9dd667e163297fb1c3689a6f35b76bb257864)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeTransactionDetails", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="messageFormat")
    def message_format(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "messageFormat"))

    @message_format.setter
    def message_format(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__32d121cbb90c3c9235c32df170e318e2318fced4bbf50834ed3d808c1b10b5fc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "messageFormat", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="messageMaxBytes")
    def message_max_bytes(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "messageMaxBytes"))

    @message_max_bytes.setter
    def message_max_bytes(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__792ebb9800fba89b1aea82acab567e5a217160919f1372a688759bfee3e9d828)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "messageMaxBytes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="noHexPrefix")
    def no_hex_prefix(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "noHexPrefix"))

    @no_hex_prefix.setter
    def no_hex_prefix(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__86c867539815ce78bba16a502cf1dcf0a0fd166ca42e7a50b402cf40a60977c0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "noHexPrefix", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="partitionIncludeSchemaTable")
    def partition_include_schema_table(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "partitionIncludeSchemaTable"))

    @partition_include_schema_table.setter
    def partition_include_schema_table(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__132b8c964fd78897f67f3265460fc4a31796b094784211b7ef05f805e0c7c1f2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "partitionIncludeSchemaTable", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="saslMechanism")
    def sasl_mechanism(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "saslMechanism"))

    @sasl_mechanism.setter
    def sasl_mechanism(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eff8df4d8aaec81466c26f520e337d792cd455ef1939bc37735972cd1952b566)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "saslMechanism", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="saslPassword")
    def sasl_password(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "saslPassword"))

    @sasl_password.setter
    def sasl_password(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b21865779a02ad0580df0517bb3556cfdc4c2df35f428bef24a4f2b80c540b55)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "saslPassword", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="saslUsername")
    def sasl_username(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "saslUsername"))

    @sasl_username.setter
    def sasl_username(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b8b365dd5bf9471bc5a2a9cee7881dbbaa233d8c18e253aa28ee1deb6e926cdd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "saslUsername", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="securityProtocol")
    def security_protocol(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "securityProtocol"))

    @security_protocol.setter
    def security_protocol(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f616a5aa6cd1d9c0db4e6ba844709ef3d5a36f4fa98cc686508f08c892a2e573)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "securityProtocol", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslCaCertificateArn")
    def ssl_ca_certificate_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslCaCertificateArn"))

    @ssl_ca_certificate_arn.setter
    def ssl_ca_certificate_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c78843566af5c77923b42a4e4dc6be6378e6e3475c7f48e5abe9c76eecae6fc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslCaCertificateArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslClientCertificateArn")
    def ssl_client_certificate_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslClientCertificateArn"))

    @ssl_client_certificate_arn.setter
    def ssl_client_certificate_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dd09233debc20d0b17bb05a1e5eb7963cd5c6f9e1f224e6fbdcb745bc7b62dc8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslClientCertificateArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslClientKeyArn")
    def ssl_client_key_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslClientKeyArn"))

    @ssl_client_key_arn.setter
    def ssl_client_key_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a63f6b2974112ca8dff335cd83a0778c688d07ac325d6f65164f7d6d2ae4eae5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslClientKeyArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslClientKeyPassword")
    def ssl_client_key_password(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslClientKeyPassword"))

    @ssl_client_key_password.setter
    def ssl_client_key_password(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5bf8eed2ee037004be98c4ca7aaa6b3d76a14421441c8067bb5de0d78d5dab28)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslClientKeyPassword", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="topic")
    def topic(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "topic"))

    @topic.setter
    def topic(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e1f3cbf1f803ab73af8d78e058e1be9c06be52f61e8e28171ece24c743045e0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "topic", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointKafkaSettings]:
        return typing.cast(typing.Optional[DmsEndpointKafkaSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(self, value: typing.Optional[DmsEndpointKafkaSettings]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e3ad11f19fed72a04f196d3b05d1cf48bbcc8a313ff222636fafc572e4e4f1f9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointKinesisSettings",
    jsii_struct_bases=[],
    name_mapping={
        "include_control_details": "includeControlDetails",
        "include_null_and_empty": "includeNullAndEmpty",
        "include_partition_value": "includePartitionValue",
        "include_table_alter_operations": "includeTableAlterOperations",
        "include_transaction_details": "includeTransactionDetails",
        "message_format": "messageFormat",
        "partition_include_schema_table": "partitionIncludeSchemaTable",
        "service_access_role_arn": "serviceAccessRoleArn",
        "stream_arn": "streamArn",
        "use_large_integer_value": "useLargeIntegerValue",
    },
)
class DmsEndpointKinesisSettings:
    def __init__(
        self,
        *,
        include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        message_format: typing.Optional[builtins.str] = None,
        partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        stream_arn: typing.Optional[builtins.str] = None,
        use_large_integer_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param include_control_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.
        :param include_null_and_empty: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.
        :param include_partition_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.
        :param include_table_alter_operations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.
        :param include_transaction_details: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.
        :param message_format: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.
        :param partition_include_schema_table: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param stream_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#stream_arn DmsEndpoint#stream_arn}.
        :param use_large_integer_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_large_integer_value DmsEndpoint#use_large_integer_value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5209fde3820cb3449e83764c30d7adae484726d247a77a22d7a99732e2adf563)
            check_type(argname="argument include_control_details", value=include_control_details, expected_type=type_hints["include_control_details"])
            check_type(argname="argument include_null_and_empty", value=include_null_and_empty, expected_type=type_hints["include_null_and_empty"])
            check_type(argname="argument include_partition_value", value=include_partition_value, expected_type=type_hints["include_partition_value"])
            check_type(argname="argument include_table_alter_operations", value=include_table_alter_operations, expected_type=type_hints["include_table_alter_operations"])
            check_type(argname="argument include_transaction_details", value=include_transaction_details, expected_type=type_hints["include_transaction_details"])
            check_type(argname="argument message_format", value=message_format, expected_type=type_hints["message_format"])
            check_type(argname="argument partition_include_schema_table", value=partition_include_schema_table, expected_type=type_hints["partition_include_schema_table"])
            check_type(argname="argument service_access_role_arn", value=service_access_role_arn, expected_type=type_hints["service_access_role_arn"])
            check_type(argname="argument stream_arn", value=stream_arn, expected_type=type_hints["stream_arn"])
            check_type(argname="argument use_large_integer_value", value=use_large_integer_value, expected_type=type_hints["use_large_integer_value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if include_control_details is not None:
            self._values["include_control_details"] = include_control_details
        if include_null_and_empty is not None:
            self._values["include_null_and_empty"] = include_null_and_empty
        if include_partition_value is not None:
            self._values["include_partition_value"] = include_partition_value
        if include_table_alter_operations is not None:
            self._values["include_table_alter_operations"] = include_table_alter_operations
        if include_transaction_details is not None:
            self._values["include_transaction_details"] = include_transaction_details
        if message_format is not None:
            self._values["message_format"] = message_format
        if partition_include_schema_table is not None:
            self._values["partition_include_schema_table"] = partition_include_schema_table
        if service_access_role_arn is not None:
            self._values["service_access_role_arn"] = service_access_role_arn
        if stream_arn is not None:
            self._values["stream_arn"] = stream_arn
        if use_large_integer_value is not None:
            self._values["use_large_integer_value"] = use_large_integer_value

    @builtins.property
    def include_control_details(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_control_details DmsEndpoint#include_control_details}.'''
        result = self._values.get("include_control_details")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_null_and_empty(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_null_and_empty DmsEndpoint#include_null_and_empty}.'''
        result = self._values.get("include_null_and_empty")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_partition_value(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_partition_value DmsEndpoint#include_partition_value}.'''
        result = self._values.get("include_partition_value")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_table_alter_operations(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_table_alter_operations DmsEndpoint#include_table_alter_operations}.'''
        result = self._values.get("include_table_alter_operations")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def include_transaction_details(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#include_transaction_details DmsEndpoint#include_transaction_details}.'''
        result = self._values.get("include_transaction_details")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def message_format(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#message_format DmsEndpoint#message_format}.'''
        result = self._values.get("message_format")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def partition_include_schema_table(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#partition_include_schema_table DmsEndpoint#partition_include_schema_table}.'''
        result = self._values.get("partition_include_schema_table")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def service_access_role_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.'''
        result = self._values.get("service_access_role_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def stream_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#stream_arn DmsEndpoint#stream_arn}.'''
        result = self._values.get("stream_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def use_large_integer_value(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#use_large_integer_value DmsEndpoint#use_large_integer_value}.'''
        result = self._values.get("use_large_integer_value")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointKinesisSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointKinesisSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointKinesisSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__569f5f4cbeb2e2c9e0dd7cd6a971cbe974abea45ff897989ebd766a135c7b911)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIncludeControlDetails")
    def reset_include_control_details(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeControlDetails", []))

    @jsii.member(jsii_name="resetIncludeNullAndEmpty")
    def reset_include_null_and_empty(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeNullAndEmpty", []))

    @jsii.member(jsii_name="resetIncludePartitionValue")
    def reset_include_partition_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludePartitionValue", []))

    @jsii.member(jsii_name="resetIncludeTableAlterOperations")
    def reset_include_table_alter_operations(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeTableAlterOperations", []))

    @jsii.member(jsii_name="resetIncludeTransactionDetails")
    def reset_include_transaction_details(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeTransactionDetails", []))

    @jsii.member(jsii_name="resetMessageFormat")
    def reset_message_format(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMessageFormat", []))

    @jsii.member(jsii_name="resetPartitionIncludeSchemaTable")
    def reset_partition_include_schema_table(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPartitionIncludeSchemaTable", []))

    @jsii.member(jsii_name="resetServiceAccessRoleArn")
    def reset_service_access_role_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServiceAccessRoleArn", []))

    @jsii.member(jsii_name="resetStreamArn")
    def reset_stream_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStreamArn", []))

    @jsii.member(jsii_name="resetUseLargeIntegerValue")
    def reset_use_large_integer_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseLargeIntegerValue", []))

    @builtins.property
    @jsii.member(jsii_name="includeControlDetailsInput")
    def include_control_details_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeControlDetailsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeNullAndEmptyInput")
    def include_null_and_empty_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeNullAndEmptyInput"))

    @builtins.property
    @jsii.member(jsii_name="includePartitionValueInput")
    def include_partition_value_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includePartitionValueInput"))

    @builtins.property
    @jsii.member(jsii_name="includeTableAlterOperationsInput")
    def include_table_alter_operations_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeTableAlterOperationsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeTransactionDetailsInput")
    def include_transaction_details_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "includeTransactionDetailsInput"))

    @builtins.property
    @jsii.member(jsii_name="messageFormatInput")
    def message_format_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "messageFormatInput"))

    @builtins.property
    @jsii.member(jsii_name="partitionIncludeSchemaTableInput")
    def partition_include_schema_table_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "partitionIncludeSchemaTableInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArnInput")
    def service_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="streamArnInput")
    def stream_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "streamArnInput"))

    @builtins.property
    @jsii.member(jsii_name="useLargeIntegerValueInput")
    def use_large_integer_value_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useLargeIntegerValueInput"))

    @builtins.property
    @jsii.member(jsii_name="includeControlDetails")
    def include_control_details(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeControlDetails"))

    @include_control_details.setter
    def include_control_details(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fccc5d3ee78201301674f7eead8d54ebead0b796cf31cb8872e4fa292b6e3235)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeControlDetails", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeNullAndEmpty")
    def include_null_and_empty(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeNullAndEmpty"))

    @include_null_and_empty.setter
    def include_null_and_empty(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a2a423d56be09810e0c9abf79a40d65d88c20cf703da31ed0069050121e62f1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeNullAndEmpty", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includePartitionValue")
    def include_partition_value(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includePartitionValue"))

    @include_partition_value.setter
    def include_partition_value(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2dd636513e0a975b4a28c4e57e517ede06b7b5d4ae5b616ba416b7d81154664e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includePartitionValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeTableAlterOperations")
    def include_table_alter_operations(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeTableAlterOperations"))

    @include_table_alter_operations.setter
    def include_table_alter_operations(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__943afb398e1022bf7eafdcf4da0c0617154e85914f7e506f08d374be60138b25)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeTableAlterOperations", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeTransactionDetails")
    def include_transaction_details(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "includeTransactionDetails"))

    @include_transaction_details.setter
    def include_transaction_details(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dca559d71edec97eea849765bddb33d99d680b2d0ba43611096f683502f54ed8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeTransactionDetails", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="messageFormat")
    def message_format(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "messageFormat"))

    @message_format.setter
    def message_format(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__afe1fa1c596228d0c4398025dc81f51516b4f2931a2f3f1c7ab2f8d7b9e56458)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "messageFormat", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="partitionIncludeSchemaTable")
    def partition_include_schema_table(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "partitionIncludeSchemaTable"))

    @partition_include_schema_table.setter
    def partition_include_schema_table(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__724c575a9addb56880f1992896e22ec9ff9205d1ff0a0b268249c01673b2871b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "partitionIncludeSchemaTable", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArn")
    def service_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRoleArn"))

    @service_access_role_arn.setter
    def service_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37c19a9214fad1a14f3344f364f8a25f4475b1a05e62988f549bfbdbd1bdc403)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="streamArn")
    def stream_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "streamArn"))

    @stream_arn.setter
    def stream_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ad2034e1d5aaf2b466c780a634cd8f48f8fc509a6276af142755b7e9203ce82)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "streamArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useLargeIntegerValue")
    def use_large_integer_value(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "useLargeIntegerValue"))

    @use_large_integer_value.setter
    def use_large_integer_value(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3d1213f1c3f04cf53c4b6a0a1c2a97e92b578f68fc125cc1c922b7668033c2df)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useLargeIntegerValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointKinesisSettings]:
        return typing.cast(typing.Optional[DmsEndpointKinesisSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DmsEndpointKinesisSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__abb0fbd777f3ad3dc591f1ea06286b0c8c19694236520c5b5641bae2d6d920cf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointMongodbSettings",
    jsii_struct_bases=[],
    name_mapping={
        "auth_mechanism": "authMechanism",
        "auth_source": "authSource",
        "auth_type": "authType",
        "docs_to_investigate": "docsToInvestigate",
        "extract_doc_id": "extractDocId",
        "nesting_level": "nestingLevel",
    },
)
class DmsEndpointMongodbSettings:
    def __init__(
        self,
        *,
        auth_mechanism: typing.Optional[builtins.str] = None,
        auth_source: typing.Optional[builtins.str] = None,
        auth_type: typing.Optional[builtins.str] = None,
        docs_to_investigate: typing.Optional[builtins.str] = None,
        extract_doc_id: typing.Optional[builtins.str] = None,
        nesting_level: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param auth_mechanism: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_mechanism DmsEndpoint#auth_mechanism}.
        :param auth_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_source DmsEndpoint#auth_source}.
        :param auth_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.
        :param docs_to_investigate: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#docs_to_investigate DmsEndpoint#docs_to_investigate}.
        :param extract_doc_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extract_doc_id DmsEndpoint#extract_doc_id}.
        :param nesting_level: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#nesting_level DmsEndpoint#nesting_level}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__76da229b66ed9b2812c7f54f35b55c5a1777457b05b2a3a5d4c841ef1d42dea4)
            check_type(argname="argument auth_mechanism", value=auth_mechanism, expected_type=type_hints["auth_mechanism"])
            check_type(argname="argument auth_source", value=auth_source, expected_type=type_hints["auth_source"])
            check_type(argname="argument auth_type", value=auth_type, expected_type=type_hints["auth_type"])
            check_type(argname="argument docs_to_investigate", value=docs_to_investigate, expected_type=type_hints["docs_to_investigate"])
            check_type(argname="argument extract_doc_id", value=extract_doc_id, expected_type=type_hints["extract_doc_id"])
            check_type(argname="argument nesting_level", value=nesting_level, expected_type=type_hints["nesting_level"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if auth_mechanism is not None:
            self._values["auth_mechanism"] = auth_mechanism
        if auth_source is not None:
            self._values["auth_source"] = auth_source
        if auth_type is not None:
            self._values["auth_type"] = auth_type
        if docs_to_investigate is not None:
            self._values["docs_to_investigate"] = docs_to_investigate
        if extract_doc_id is not None:
            self._values["extract_doc_id"] = extract_doc_id
        if nesting_level is not None:
            self._values["nesting_level"] = nesting_level

    @builtins.property
    def auth_mechanism(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_mechanism DmsEndpoint#auth_mechanism}.'''
        result = self._values.get("auth_mechanism")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auth_source(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_source DmsEndpoint#auth_source}.'''
        result = self._values.get("auth_source")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auth_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.'''
        result = self._values.get("auth_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def docs_to_investigate(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#docs_to_investigate DmsEndpoint#docs_to_investigate}.'''
        result = self._values.get("docs_to_investigate")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def extract_doc_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#extract_doc_id DmsEndpoint#extract_doc_id}.'''
        result = self._values.get("extract_doc_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def nesting_level(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#nesting_level DmsEndpoint#nesting_level}.'''
        result = self._values.get("nesting_level")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointMongodbSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointMongodbSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointMongodbSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b249fcafeb0b283544326d4c654998ca301842664dfd7a3e8930c427e38dd135)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAuthMechanism")
    def reset_auth_mechanism(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthMechanism", []))

    @jsii.member(jsii_name="resetAuthSource")
    def reset_auth_source(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthSource", []))

    @jsii.member(jsii_name="resetAuthType")
    def reset_auth_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthType", []))

    @jsii.member(jsii_name="resetDocsToInvestigate")
    def reset_docs_to_investigate(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDocsToInvestigate", []))

    @jsii.member(jsii_name="resetExtractDocId")
    def reset_extract_doc_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExtractDocId", []))

    @jsii.member(jsii_name="resetNestingLevel")
    def reset_nesting_level(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNestingLevel", []))

    @builtins.property
    @jsii.member(jsii_name="authMechanismInput")
    def auth_mechanism_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authMechanismInput"))

    @builtins.property
    @jsii.member(jsii_name="authSourceInput")
    def auth_source_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authSourceInput"))

    @builtins.property
    @jsii.member(jsii_name="authTypeInput")
    def auth_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="docsToInvestigateInput")
    def docs_to_investigate_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "docsToInvestigateInput"))

    @builtins.property
    @jsii.member(jsii_name="extractDocIdInput")
    def extract_doc_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "extractDocIdInput"))

    @builtins.property
    @jsii.member(jsii_name="nestingLevelInput")
    def nesting_level_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nestingLevelInput"))

    @builtins.property
    @jsii.member(jsii_name="authMechanism")
    def auth_mechanism(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authMechanism"))

    @auth_mechanism.setter
    def auth_mechanism(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc679e242c97b652bfedf948450115cd6c20a3bf64cc72f4ccd50f527fc11b24)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authMechanism", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authSource")
    def auth_source(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authSource"))

    @auth_source.setter
    def auth_source(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5f3a79c790a8867f18b923332230ffdaa961740f6c87fa33585876b837df698)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authSource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authType")
    def auth_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authType"))

    @auth_type.setter
    def auth_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99ee30f6655c911ba73dba87573e20b9db8f532eea81952c03265b6c51164eff)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="docsToInvestigate")
    def docs_to_investigate(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "docsToInvestigate"))

    @docs_to_investigate.setter
    def docs_to_investigate(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e87292559811ffed11f0e687963d046ad7c73c15a9875704083cdc24bda8d5b5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "docsToInvestigate", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="extractDocId")
    def extract_doc_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "extractDocId"))

    @extract_doc_id.setter
    def extract_doc_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d071dc10fc63d11f8c71d787f490a58acc8d0c69d43f2defc475510f27d25086)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "extractDocId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="nestingLevel")
    def nesting_level(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "nestingLevel"))

    @nesting_level.setter
    def nesting_level(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f65bad0564d817056151aaa77309e91d0633761e523b4d46c2d0fed9b2cac60e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "nestingLevel", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointMongodbSettings]:
        return typing.cast(typing.Optional[DmsEndpointMongodbSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DmsEndpointMongodbSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c6029abf69f2d29e577590da7331ccc2abc8eacf50a254e723644d52583f715)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointMysqlSettings",
    jsii_struct_bases=[],
    name_mapping={
        "after_connect_script": "afterConnectScript",
        "authentication_method": "authenticationMethod",
        "clean_source_metadata_on_mismatch": "cleanSourceMetadataOnMismatch",
        "events_poll_interval": "eventsPollInterval",
        "execute_timeout": "executeTimeout",
        "max_file_size": "maxFileSize",
        "parallel_load_threads": "parallelLoadThreads",
        "server_timezone": "serverTimezone",
        "service_access_role_arn": "serviceAccessRoleArn",
        "target_db_type": "targetDbType",
    },
)
class DmsEndpointMysqlSettings:
    def __init__(
        self,
        *,
        after_connect_script: typing.Optional[builtins.str] = None,
        authentication_method: typing.Optional[builtins.str] = None,
        clean_source_metadata_on_mismatch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        events_poll_interval: typing.Optional[jsii.Number] = None,
        execute_timeout: typing.Optional[jsii.Number] = None,
        max_file_size: typing.Optional[jsii.Number] = None,
        parallel_load_threads: typing.Optional[jsii.Number] = None,
        server_timezone: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        target_db_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param after_connect_script: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        :param clean_source_metadata_on_mismatch: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#clean_source_metadata_on_mismatch DmsEndpoint#clean_source_metadata_on_mismatch}.
        :param events_poll_interval: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#events_poll_interval DmsEndpoint#events_poll_interval}.
        :param execute_timeout: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.
        :param max_file_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.
        :param parallel_load_threads: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#parallel_load_threads DmsEndpoint#parallel_load_threads}.
        :param server_timezone: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_timezone DmsEndpoint#server_timezone}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param target_db_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#target_db_type DmsEndpoint#target_db_type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70090e44c206ba00f455d7b9961ddd886a3ed6c5d9c2d43e300afe8509d19dad)
            check_type(argname="argument after_connect_script", value=after_connect_script, expected_type=type_hints["after_connect_script"])
            check_type(argname="argument authentication_method", value=authentication_method, expected_type=type_hints["authentication_method"])
            check_type(argname="argument clean_source_metadata_on_mismatch", value=clean_source_metadata_on_mismatch, expected_type=type_hints["clean_source_metadata_on_mismatch"])
            check_type(argname="argument events_poll_interval", value=events_poll_interval, expected_type=type_hints["events_poll_interval"])
            check_type(argname="argument execute_timeout", value=execute_timeout, expected_type=type_hints["execute_timeout"])
            check_type(argname="argument max_file_size", value=max_file_size, expected_type=type_hints["max_file_size"])
            check_type(argname="argument parallel_load_threads", value=parallel_load_threads, expected_type=type_hints["parallel_load_threads"])
            check_type(argname="argument server_timezone", value=server_timezone, expected_type=type_hints["server_timezone"])
            check_type(argname="argument service_access_role_arn", value=service_access_role_arn, expected_type=type_hints["service_access_role_arn"])
            check_type(argname="argument target_db_type", value=target_db_type, expected_type=type_hints["target_db_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if after_connect_script is not None:
            self._values["after_connect_script"] = after_connect_script
        if authentication_method is not None:
            self._values["authentication_method"] = authentication_method
        if clean_source_metadata_on_mismatch is not None:
            self._values["clean_source_metadata_on_mismatch"] = clean_source_metadata_on_mismatch
        if events_poll_interval is not None:
            self._values["events_poll_interval"] = events_poll_interval
        if execute_timeout is not None:
            self._values["execute_timeout"] = execute_timeout
        if max_file_size is not None:
            self._values["max_file_size"] = max_file_size
        if parallel_load_threads is not None:
            self._values["parallel_load_threads"] = parallel_load_threads
        if server_timezone is not None:
            self._values["server_timezone"] = server_timezone
        if service_access_role_arn is not None:
            self._values["service_access_role_arn"] = service_access_role_arn
        if target_db_type is not None:
            self._values["target_db_type"] = target_db_type

    @builtins.property
    def after_connect_script(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.'''
        result = self._values.get("after_connect_script")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def authentication_method(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.'''
        result = self._values.get("authentication_method")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def clean_source_metadata_on_mismatch(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#clean_source_metadata_on_mismatch DmsEndpoint#clean_source_metadata_on_mismatch}.'''
        result = self._values.get("clean_source_metadata_on_mismatch")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def events_poll_interval(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#events_poll_interval DmsEndpoint#events_poll_interval}.'''
        result = self._values.get("events_poll_interval")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def execute_timeout(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.'''
        result = self._values.get("execute_timeout")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_file_size(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.'''
        result = self._values.get("max_file_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def parallel_load_threads(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#parallel_load_threads DmsEndpoint#parallel_load_threads}.'''
        result = self._values.get("parallel_load_threads")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def server_timezone(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_timezone DmsEndpoint#server_timezone}.'''
        result = self._values.get("server_timezone")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_access_role_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.'''
        result = self._values.get("service_access_role_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_db_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#target_db_type DmsEndpoint#target_db_type}.'''
        result = self._values.get("target_db_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointMysqlSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointMysqlSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointMysqlSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__3c4d110f98bd7118dbbd699490efdfe979aaa783babcc167d46800392fd29ba4)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAfterConnectScript")
    def reset_after_connect_script(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAfterConnectScript", []))

    @jsii.member(jsii_name="resetAuthenticationMethod")
    def reset_authentication_method(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthenticationMethod", []))

    @jsii.member(jsii_name="resetCleanSourceMetadataOnMismatch")
    def reset_clean_source_metadata_on_mismatch(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCleanSourceMetadataOnMismatch", []))

    @jsii.member(jsii_name="resetEventsPollInterval")
    def reset_events_poll_interval(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEventsPollInterval", []))

    @jsii.member(jsii_name="resetExecuteTimeout")
    def reset_execute_timeout(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExecuteTimeout", []))

    @jsii.member(jsii_name="resetMaxFileSize")
    def reset_max_file_size(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxFileSize", []))

    @jsii.member(jsii_name="resetParallelLoadThreads")
    def reset_parallel_load_threads(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParallelLoadThreads", []))

    @jsii.member(jsii_name="resetServerTimezone")
    def reset_server_timezone(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServerTimezone", []))

    @jsii.member(jsii_name="resetServiceAccessRoleArn")
    def reset_service_access_role_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServiceAccessRoleArn", []))

    @jsii.member(jsii_name="resetTargetDbType")
    def reset_target_db_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTargetDbType", []))

    @builtins.property
    @jsii.member(jsii_name="afterConnectScriptInput")
    def after_connect_script_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "afterConnectScriptInput"))

    @builtins.property
    @jsii.member(jsii_name="authenticationMethodInput")
    def authentication_method_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authenticationMethodInput"))

    @builtins.property
    @jsii.member(jsii_name="cleanSourceMetadataOnMismatchInput")
    def clean_source_metadata_on_mismatch_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "cleanSourceMetadataOnMismatchInput"))

    @builtins.property
    @jsii.member(jsii_name="eventsPollIntervalInput")
    def events_poll_interval_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "eventsPollIntervalInput"))

    @builtins.property
    @jsii.member(jsii_name="executeTimeoutInput")
    def execute_timeout_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "executeTimeoutInput"))

    @builtins.property
    @jsii.member(jsii_name="maxFileSizeInput")
    def max_file_size_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxFileSizeInput"))

    @builtins.property
    @jsii.member(jsii_name="parallelLoadThreadsInput")
    def parallel_load_threads_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "parallelLoadThreadsInput"))

    @builtins.property
    @jsii.member(jsii_name="serverTimezoneInput")
    def server_timezone_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serverTimezoneInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArnInput")
    def service_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="targetDbTypeInput")
    def target_db_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "targetDbTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="afterConnectScript")
    def after_connect_script(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "afterConnectScript"))

    @after_connect_script.setter
    def after_connect_script(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ca2d26969522cbccdd7f93f7e7e820d12b4fcf91058c329a5d667d776388e89d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "afterConnectScript", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authenticationMethod")
    def authentication_method(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authenticationMethod"))

    @authentication_method.setter
    def authentication_method(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__896216ee1f5ea05397c1eecf15836d54fd448a6740c7bde6391b5d69c7f25c53)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authenticationMethod", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="cleanSourceMetadataOnMismatch")
    def clean_source_metadata_on_mismatch(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "cleanSourceMetadataOnMismatch"))

    @clean_source_metadata_on_mismatch.setter
    def clean_source_metadata_on_mismatch(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__41646ae3f988faf325250ddf50483b1ebefefd6961b08d4449b6c6716036b4d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "cleanSourceMetadataOnMismatch", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="eventsPollInterval")
    def events_poll_interval(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "eventsPollInterval"))

    @events_poll_interval.setter
    def events_poll_interval(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0dd018972594c5e1cb25b2ebb2fe4e3016fdcff87cec8783b2882b2fef543ddd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "eventsPollInterval", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="executeTimeout")
    def execute_timeout(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "executeTimeout"))

    @execute_timeout.setter
    def execute_timeout(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a7fa2fec1d0b57f8a9a96695761eefca4d01fd3ca7001c9863b928a7e9d95dfc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "executeTimeout", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxFileSize")
    def max_file_size(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxFileSize"))

    @max_file_size.setter
    def max_file_size(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d4fef54b3bd610acb24eb9becce8fe728df60ab06a450d405496d4610f1e1de8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxFileSize", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parallelLoadThreads")
    def parallel_load_threads(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "parallelLoadThreads"))

    @parallel_load_threads.setter
    def parallel_load_threads(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f476bb20e9229a0a400a63ae2babc048e12656047ec820de8d8b5c58cf38002)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parallelLoadThreads", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serverTimezone")
    def server_timezone(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serverTimezone"))

    @server_timezone.setter
    def server_timezone(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbffe36a2dd4e2077c86e79aa4f6abef73cdcd0a8d3ec71d4207669468cf82a9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serverTimezone", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArn")
    def service_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRoleArn"))

    @service_access_role_arn.setter
    def service_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b7ba6b01f6335313739c17f164b2b8d659ac08eb5812f3fcea26639f71402bfd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="targetDbType")
    def target_db_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "targetDbType"))

    @target_db_type.setter
    def target_db_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4be8cd109621ee6dee73bec35a8b1e2fa52e77f2db9e2ea59e6b0e6e06b94eda)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "targetDbType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointMysqlSettings]:
        return typing.cast(typing.Optional[DmsEndpointMysqlSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(self, value: typing.Optional[DmsEndpointMysqlSettings]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__459179f1edf2962bfbd3fbeaec61ef5f854c6fe3121bb0d84eff9ffc8a8bd6cc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointOracleSettings",
    jsii_struct_bases=[],
    name_mapping={"authentication_method": "authenticationMethod"},
)
class DmsEndpointOracleSettings:
    def __init__(
        self,
        *,
        authentication_method: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a085d1847dbe0dc6ee415ee7e17345a4073d1655863c96df864f0669ccf47c16)
            check_type(argname="argument authentication_method", value=authentication_method, expected_type=type_hints["authentication_method"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if authentication_method is not None:
            self._values["authentication_method"] = authentication_method

    @builtins.property
    def authentication_method(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.'''
        result = self._values.get("authentication_method")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointOracleSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointOracleSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointOracleSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d408c40a51ea85c2a6e98e630d481c8d357efdd7c50a3f32d77b52fda55a9673)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAuthenticationMethod")
    def reset_authentication_method(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthenticationMethod", []))

    @builtins.property
    @jsii.member(jsii_name="authenticationMethodInput")
    def authentication_method_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authenticationMethodInput"))

    @builtins.property
    @jsii.member(jsii_name="authenticationMethod")
    def authentication_method(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authenticationMethod"))

    @authentication_method.setter
    def authentication_method(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__718cb59dd77d31a84df7feaad9a2cc1bf3e728b265669d34cefa4001667bcfe8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authenticationMethod", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointOracleSettings]:
        return typing.cast(typing.Optional[DmsEndpointOracleSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(self, value: typing.Optional[DmsEndpointOracleSettings]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cb950905ad8c8091fb9154b4c748ee17c92ad0f8f50f069492127d83d3edbd33)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointPostgresSettings",
    jsii_struct_bases=[],
    name_mapping={
        "after_connect_script": "afterConnectScript",
        "authentication_method": "authenticationMethod",
        "babelfish_database_name": "babelfishDatabaseName",
        "capture_ddls": "captureDdls",
        "database_mode": "databaseMode",
        "ddl_artifacts_schema": "ddlArtifactsSchema",
        "execute_timeout": "executeTimeout",
        "fail_tasks_on_lob_truncation": "failTasksOnLobTruncation",
        "heartbeat_enable": "heartbeatEnable",
        "heartbeat_frequency": "heartbeatFrequency",
        "heartbeat_schema": "heartbeatSchema",
        "map_boolean_as_boolean": "mapBooleanAsBoolean",
        "map_jsonb_as_clob": "mapJsonbAsClob",
        "map_long_varchar_as": "mapLongVarcharAs",
        "max_file_size": "maxFileSize",
        "plugin_name": "pluginName",
        "service_access_role_arn": "serviceAccessRoleArn",
        "slot_name": "slotName",
    },
)
class DmsEndpointPostgresSettings:
    def __init__(
        self,
        *,
        after_connect_script: typing.Optional[builtins.str] = None,
        authentication_method: typing.Optional[builtins.str] = None,
        babelfish_database_name: typing.Optional[builtins.str] = None,
        capture_ddls: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        database_mode: typing.Optional[builtins.str] = None,
        ddl_artifacts_schema: typing.Optional[builtins.str] = None,
        execute_timeout: typing.Optional[jsii.Number] = None,
        fail_tasks_on_lob_truncation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        heartbeat_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        heartbeat_frequency: typing.Optional[jsii.Number] = None,
        heartbeat_schema: typing.Optional[builtins.str] = None,
        map_boolean_as_boolean: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        map_jsonb_as_clob: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        map_long_varchar_as: typing.Optional[builtins.str] = None,
        max_file_size: typing.Optional[jsii.Number] = None,
        plugin_name: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
        slot_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param after_connect_script: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.
        :param authentication_method: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.
        :param babelfish_database_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#babelfish_database_name DmsEndpoint#babelfish_database_name}.
        :param capture_ddls: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#capture_ddls DmsEndpoint#capture_ddls}.
        :param database_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_mode DmsEndpoint#database_mode}.
        :param ddl_artifacts_schema: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ddl_artifacts_schema DmsEndpoint#ddl_artifacts_schema}.
        :param execute_timeout: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.
        :param fail_tasks_on_lob_truncation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#fail_tasks_on_lob_truncation DmsEndpoint#fail_tasks_on_lob_truncation}.
        :param heartbeat_enable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_enable DmsEndpoint#heartbeat_enable}.
        :param heartbeat_frequency: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_frequency DmsEndpoint#heartbeat_frequency}.
        :param heartbeat_schema: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_schema DmsEndpoint#heartbeat_schema}.
        :param map_boolean_as_boolean: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_boolean_as_boolean DmsEndpoint#map_boolean_as_boolean}.
        :param map_jsonb_as_clob: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_jsonb_as_clob DmsEndpoint#map_jsonb_as_clob}.
        :param map_long_varchar_as: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_long_varchar_as DmsEndpoint#map_long_varchar_as}.
        :param max_file_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.
        :param plugin_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#plugin_name DmsEndpoint#plugin_name}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        :param slot_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#slot_name DmsEndpoint#slot_name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3857b2a7fe58b2662dbcf81b7d56645e33919fbf19652130f7fb94e86d3a8232)
            check_type(argname="argument after_connect_script", value=after_connect_script, expected_type=type_hints["after_connect_script"])
            check_type(argname="argument authentication_method", value=authentication_method, expected_type=type_hints["authentication_method"])
            check_type(argname="argument babelfish_database_name", value=babelfish_database_name, expected_type=type_hints["babelfish_database_name"])
            check_type(argname="argument capture_ddls", value=capture_ddls, expected_type=type_hints["capture_ddls"])
            check_type(argname="argument database_mode", value=database_mode, expected_type=type_hints["database_mode"])
            check_type(argname="argument ddl_artifacts_schema", value=ddl_artifacts_schema, expected_type=type_hints["ddl_artifacts_schema"])
            check_type(argname="argument execute_timeout", value=execute_timeout, expected_type=type_hints["execute_timeout"])
            check_type(argname="argument fail_tasks_on_lob_truncation", value=fail_tasks_on_lob_truncation, expected_type=type_hints["fail_tasks_on_lob_truncation"])
            check_type(argname="argument heartbeat_enable", value=heartbeat_enable, expected_type=type_hints["heartbeat_enable"])
            check_type(argname="argument heartbeat_frequency", value=heartbeat_frequency, expected_type=type_hints["heartbeat_frequency"])
            check_type(argname="argument heartbeat_schema", value=heartbeat_schema, expected_type=type_hints["heartbeat_schema"])
            check_type(argname="argument map_boolean_as_boolean", value=map_boolean_as_boolean, expected_type=type_hints["map_boolean_as_boolean"])
            check_type(argname="argument map_jsonb_as_clob", value=map_jsonb_as_clob, expected_type=type_hints["map_jsonb_as_clob"])
            check_type(argname="argument map_long_varchar_as", value=map_long_varchar_as, expected_type=type_hints["map_long_varchar_as"])
            check_type(argname="argument max_file_size", value=max_file_size, expected_type=type_hints["max_file_size"])
            check_type(argname="argument plugin_name", value=plugin_name, expected_type=type_hints["plugin_name"])
            check_type(argname="argument service_access_role_arn", value=service_access_role_arn, expected_type=type_hints["service_access_role_arn"])
            check_type(argname="argument slot_name", value=slot_name, expected_type=type_hints["slot_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if after_connect_script is not None:
            self._values["after_connect_script"] = after_connect_script
        if authentication_method is not None:
            self._values["authentication_method"] = authentication_method
        if babelfish_database_name is not None:
            self._values["babelfish_database_name"] = babelfish_database_name
        if capture_ddls is not None:
            self._values["capture_ddls"] = capture_ddls
        if database_mode is not None:
            self._values["database_mode"] = database_mode
        if ddl_artifacts_schema is not None:
            self._values["ddl_artifacts_schema"] = ddl_artifacts_schema
        if execute_timeout is not None:
            self._values["execute_timeout"] = execute_timeout
        if fail_tasks_on_lob_truncation is not None:
            self._values["fail_tasks_on_lob_truncation"] = fail_tasks_on_lob_truncation
        if heartbeat_enable is not None:
            self._values["heartbeat_enable"] = heartbeat_enable
        if heartbeat_frequency is not None:
            self._values["heartbeat_frequency"] = heartbeat_frequency
        if heartbeat_schema is not None:
            self._values["heartbeat_schema"] = heartbeat_schema
        if map_boolean_as_boolean is not None:
            self._values["map_boolean_as_boolean"] = map_boolean_as_boolean
        if map_jsonb_as_clob is not None:
            self._values["map_jsonb_as_clob"] = map_jsonb_as_clob
        if map_long_varchar_as is not None:
            self._values["map_long_varchar_as"] = map_long_varchar_as
        if max_file_size is not None:
            self._values["max_file_size"] = max_file_size
        if plugin_name is not None:
            self._values["plugin_name"] = plugin_name
        if service_access_role_arn is not None:
            self._values["service_access_role_arn"] = service_access_role_arn
        if slot_name is not None:
            self._values["slot_name"] = slot_name

    @builtins.property
    def after_connect_script(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#after_connect_script DmsEndpoint#after_connect_script}.'''
        result = self._values.get("after_connect_script")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def authentication_method(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#authentication_method DmsEndpoint#authentication_method}.'''
        result = self._values.get("authentication_method")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def babelfish_database_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#babelfish_database_name DmsEndpoint#babelfish_database_name}.'''
        result = self._values.get("babelfish_database_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def capture_ddls(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#capture_ddls DmsEndpoint#capture_ddls}.'''
        result = self._values.get("capture_ddls")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def database_mode(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#database_mode DmsEndpoint#database_mode}.'''
        result = self._values.get("database_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ddl_artifacts_schema(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ddl_artifacts_schema DmsEndpoint#ddl_artifacts_schema}.'''
        result = self._values.get("ddl_artifacts_schema")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def execute_timeout(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#execute_timeout DmsEndpoint#execute_timeout}.'''
        result = self._values.get("execute_timeout")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def fail_tasks_on_lob_truncation(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#fail_tasks_on_lob_truncation DmsEndpoint#fail_tasks_on_lob_truncation}.'''
        result = self._values.get("fail_tasks_on_lob_truncation")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def heartbeat_enable(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_enable DmsEndpoint#heartbeat_enable}.'''
        result = self._values.get("heartbeat_enable")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def heartbeat_frequency(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_frequency DmsEndpoint#heartbeat_frequency}.'''
        result = self._values.get("heartbeat_frequency")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def heartbeat_schema(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#heartbeat_schema DmsEndpoint#heartbeat_schema}.'''
        result = self._values.get("heartbeat_schema")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def map_boolean_as_boolean(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_boolean_as_boolean DmsEndpoint#map_boolean_as_boolean}.'''
        result = self._values.get("map_boolean_as_boolean")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def map_jsonb_as_clob(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_jsonb_as_clob DmsEndpoint#map_jsonb_as_clob}.'''
        result = self._values.get("map_jsonb_as_clob")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def map_long_varchar_as(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#map_long_varchar_as DmsEndpoint#map_long_varchar_as}.'''
        result = self._values.get("map_long_varchar_as")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_file_size(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#max_file_size DmsEndpoint#max_file_size}.'''
        result = self._values.get("max_file_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def plugin_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#plugin_name DmsEndpoint#plugin_name}.'''
        result = self._values.get("plugin_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_access_role_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.'''
        result = self._values.get("service_access_role_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def slot_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#slot_name DmsEndpoint#slot_name}.'''
        result = self._values.get("slot_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointPostgresSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointPostgresSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointPostgresSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b3e6ebe93f6cd8b7ff04051541046e7812e080364c76a8283877a39e74aabe53)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAfterConnectScript")
    def reset_after_connect_script(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAfterConnectScript", []))

    @jsii.member(jsii_name="resetAuthenticationMethod")
    def reset_authentication_method(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthenticationMethod", []))

    @jsii.member(jsii_name="resetBabelfishDatabaseName")
    def reset_babelfish_database_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBabelfishDatabaseName", []))

    @jsii.member(jsii_name="resetCaptureDdls")
    def reset_capture_ddls(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCaptureDdls", []))

    @jsii.member(jsii_name="resetDatabaseMode")
    def reset_database_mode(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDatabaseMode", []))

    @jsii.member(jsii_name="resetDdlArtifactsSchema")
    def reset_ddl_artifacts_schema(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDdlArtifactsSchema", []))

    @jsii.member(jsii_name="resetExecuteTimeout")
    def reset_execute_timeout(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExecuteTimeout", []))

    @jsii.member(jsii_name="resetFailTasksOnLobTruncation")
    def reset_fail_tasks_on_lob_truncation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetFailTasksOnLobTruncation", []))

    @jsii.member(jsii_name="resetHeartbeatEnable")
    def reset_heartbeat_enable(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHeartbeatEnable", []))

    @jsii.member(jsii_name="resetHeartbeatFrequency")
    def reset_heartbeat_frequency(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHeartbeatFrequency", []))

    @jsii.member(jsii_name="resetHeartbeatSchema")
    def reset_heartbeat_schema(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHeartbeatSchema", []))

    @jsii.member(jsii_name="resetMapBooleanAsBoolean")
    def reset_map_boolean_as_boolean(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMapBooleanAsBoolean", []))

    @jsii.member(jsii_name="resetMapJsonbAsClob")
    def reset_map_jsonb_as_clob(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMapJsonbAsClob", []))

    @jsii.member(jsii_name="resetMapLongVarcharAs")
    def reset_map_long_varchar_as(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMapLongVarcharAs", []))

    @jsii.member(jsii_name="resetMaxFileSize")
    def reset_max_file_size(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxFileSize", []))

    @jsii.member(jsii_name="resetPluginName")
    def reset_plugin_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPluginName", []))

    @jsii.member(jsii_name="resetServiceAccessRoleArn")
    def reset_service_access_role_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServiceAccessRoleArn", []))

    @jsii.member(jsii_name="resetSlotName")
    def reset_slot_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSlotName", []))

    @builtins.property
    @jsii.member(jsii_name="afterConnectScriptInput")
    def after_connect_script_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "afterConnectScriptInput"))

    @builtins.property
    @jsii.member(jsii_name="authenticationMethodInput")
    def authentication_method_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authenticationMethodInput"))

    @builtins.property
    @jsii.member(jsii_name="babelfishDatabaseNameInput")
    def babelfish_database_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "babelfishDatabaseNameInput"))

    @builtins.property
    @jsii.member(jsii_name="captureDdlsInput")
    def capture_ddls_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "captureDdlsInput"))

    @builtins.property
    @jsii.member(jsii_name="databaseModeInput")
    def database_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "databaseModeInput"))

    @builtins.property
    @jsii.member(jsii_name="ddlArtifactsSchemaInput")
    def ddl_artifacts_schema_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "ddlArtifactsSchemaInput"))

    @builtins.property
    @jsii.member(jsii_name="executeTimeoutInput")
    def execute_timeout_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "executeTimeoutInput"))

    @builtins.property
    @jsii.member(jsii_name="failTasksOnLobTruncationInput")
    def fail_tasks_on_lob_truncation_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "failTasksOnLobTruncationInput"))

    @builtins.property
    @jsii.member(jsii_name="heartbeatEnableInput")
    def heartbeat_enable_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "heartbeatEnableInput"))

    @builtins.property
    @jsii.member(jsii_name="heartbeatFrequencyInput")
    def heartbeat_frequency_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "heartbeatFrequencyInput"))

    @builtins.property
    @jsii.member(jsii_name="heartbeatSchemaInput")
    def heartbeat_schema_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "heartbeatSchemaInput"))

    @builtins.property
    @jsii.member(jsii_name="mapBooleanAsBooleanInput")
    def map_boolean_as_boolean_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "mapBooleanAsBooleanInput"))

    @builtins.property
    @jsii.member(jsii_name="mapJsonbAsClobInput")
    def map_jsonb_as_clob_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "mapJsonbAsClobInput"))

    @builtins.property
    @jsii.member(jsii_name="mapLongVarcharAsInput")
    def map_long_varchar_as_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "mapLongVarcharAsInput"))

    @builtins.property
    @jsii.member(jsii_name="maxFileSizeInput")
    def max_file_size_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxFileSizeInput"))

    @builtins.property
    @jsii.member(jsii_name="pluginNameInput")
    def plugin_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginNameInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArnInput")
    def service_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="slotNameInput")
    def slot_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "slotNameInput"))

    @builtins.property
    @jsii.member(jsii_name="afterConnectScript")
    def after_connect_script(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "afterConnectScript"))

    @after_connect_script.setter
    def after_connect_script(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__92693c64d786acd8b6cb30062e22510817adef0ad0f0866fab68cea7b06befec)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "afterConnectScript", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authenticationMethod")
    def authentication_method(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authenticationMethod"))

    @authentication_method.setter
    def authentication_method(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae2e1d0b6a0f5f6f7a2a24d25501ce70c80479550d2c21d2d485ab8257207bfe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authenticationMethod", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="babelfishDatabaseName")
    def babelfish_database_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "babelfishDatabaseName"))

    @babelfish_database_name.setter
    def babelfish_database_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a859a19d27cb607225bc210064bd784de5b8bf22cfb162290950f07dad12b1f3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "babelfishDatabaseName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="captureDdls")
    def capture_ddls(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "captureDdls"))

    @capture_ddls.setter
    def capture_ddls(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8d6e7e5fc7e39b6f7e5b826bd7f8b72ce5e1e1b2ed55869a32dea9975b9181a4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "captureDdls", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="databaseMode")
    def database_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "databaseMode"))

    @database_mode.setter
    def database_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6703a2e26a0aec772457e488ad3cef91b4f5a6948ac2c474bddc8e49bec3e182)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "databaseMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ddlArtifactsSchema")
    def ddl_artifacts_schema(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "ddlArtifactsSchema"))

    @ddl_artifacts_schema.setter
    def ddl_artifacts_schema(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de9d0406f0b4066fa91b12e59ed6b4201634a12e4552898e171243211ac81914)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ddlArtifactsSchema", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="executeTimeout")
    def execute_timeout(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "executeTimeout"))

    @execute_timeout.setter
    def execute_timeout(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2c2d97cb08dd5af78949323574a96c84e0ad35ecef620c4476c20c8fdcc95eee)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "executeTimeout", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="failTasksOnLobTruncation")
    def fail_tasks_on_lob_truncation(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "failTasksOnLobTruncation"))

    @fail_tasks_on_lob_truncation.setter
    def fail_tasks_on_lob_truncation(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__84724bd4e8bb2aa123125f54f5867bc4bb7de2dc01c5de9a1e17a9fe845f5ff0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "failTasksOnLobTruncation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="heartbeatEnable")
    def heartbeat_enable(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "heartbeatEnable"))

    @heartbeat_enable.setter
    def heartbeat_enable(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61f1008a944d084ed15919f6f7baba5dc30a51a8c494b99e278cf2655ab6161d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "heartbeatEnable", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="heartbeatFrequency")
    def heartbeat_frequency(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "heartbeatFrequency"))

    @heartbeat_frequency.setter
    def heartbeat_frequency(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__acf2346eb60a0c07e72aefd04879227f0340e1cade9e0ee1a00f084247f91dad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "heartbeatFrequency", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="heartbeatSchema")
    def heartbeat_schema(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "heartbeatSchema"))

    @heartbeat_schema.setter
    def heartbeat_schema(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__91fff301f2d2fa176de6cfe83b24cc25249831dd9213e8005c52c7b4234a6550)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "heartbeatSchema", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mapBooleanAsBoolean")
    def map_boolean_as_boolean(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "mapBooleanAsBoolean"))

    @map_boolean_as_boolean.setter
    def map_boolean_as_boolean(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1dd5e4aaf95dc8f7a71db298c46f6fb9c60a2652976e851e0f510e9e64830f35)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mapBooleanAsBoolean", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mapJsonbAsClob")
    def map_jsonb_as_clob(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "mapJsonbAsClob"))

    @map_jsonb_as_clob.setter
    def map_jsonb_as_clob(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d45152a4289d62b833132cda63cc98f0f6bc026530a469e279b79149ef0225c3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mapJsonbAsClob", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mapLongVarcharAs")
    def map_long_varchar_as(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "mapLongVarcharAs"))

    @map_long_varchar_as.setter
    def map_long_varchar_as(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f624a1186957b483e621e4506083b26c3f0261fadef9fe0b8fd0a21619546505)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mapLongVarcharAs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxFileSize")
    def max_file_size(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxFileSize"))

    @max_file_size.setter
    def max_file_size(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__81573b74a662f80da2f7b8fb9974e6a25760bedd416fd294744be58104fd7abe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxFileSize", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="pluginName")
    def plugin_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "pluginName"))

    @plugin_name.setter
    def plugin_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f539d09adfbf0b6c82272e9a61408f7cc9b885dcb1ce8a4c9c189cb2a555db4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "pluginName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArn")
    def service_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRoleArn"))

    @service_access_role_arn.setter
    def service_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37a4e999cd9392fa359cc421b1077c5dd7decd6018a7984db4323b0eae74a090)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="slotName")
    def slot_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "slotName"))

    @slot_name.setter
    def slot_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d2200fb4dbc800d8025702b2384c937dc4223a19cd69d3848ccfe534a6593781)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "slotName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointPostgresSettings]:
        return typing.cast(typing.Optional[DmsEndpointPostgresSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DmsEndpointPostgresSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__adc5afb90297d08f49356bf77b97ded3a0af548de6bc8671a0963f458639e32c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointRedisSettings",
    jsii_struct_bases=[],
    name_mapping={
        "auth_type": "authType",
        "port": "port",
        "server_name": "serverName",
        "auth_password": "authPassword",
        "auth_user_name": "authUserName",
        "ssl_ca_certificate_arn": "sslCaCertificateArn",
        "ssl_security_protocol": "sslSecurityProtocol",
    },
)
class DmsEndpointRedisSettings:
    def __init__(
        self,
        *,
        auth_type: builtins.str,
        port: jsii.Number,
        server_name: builtins.str,
        auth_password: typing.Optional[builtins.str] = None,
        auth_user_name: typing.Optional[builtins.str] = None,
        ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
        ssl_security_protocol: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param auth_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.
        :param port: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.
        :param server_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.
        :param auth_password: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_password DmsEndpoint#auth_password}.
        :param auth_user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_user_name DmsEndpoint#auth_user_name}.
        :param ssl_ca_certificate_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.
        :param ssl_security_protocol: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_security_protocol DmsEndpoint#ssl_security_protocol}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26d887d8a5295deeeedcb256db19314a5184ca19a7001634e8a83b67f33a33cc)
            check_type(argname="argument auth_type", value=auth_type, expected_type=type_hints["auth_type"])
            check_type(argname="argument port", value=port, expected_type=type_hints["port"])
            check_type(argname="argument server_name", value=server_name, expected_type=type_hints["server_name"])
            check_type(argname="argument auth_password", value=auth_password, expected_type=type_hints["auth_password"])
            check_type(argname="argument auth_user_name", value=auth_user_name, expected_type=type_hints["auth_user_name"])
            check_type(argname="argument ssl_ca_certificate_arn", value=ssl_ca_certificate_arn, expected_type=type_hints["ssl_ca_certificate_arn"])
            check_type(argname="argument ssl_security_protocol", value=ssl_security_protocol, expected_type=type_hints["ssl_security_protocol"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "auth_type": auth_type,
            "port": port,
            "server_name": server_name,
        }
        if auth_password is not None:
            self._values["auth_password"] = auth_password
        if auth_user_name is not None:
            self._values["auth_user_name"] = auth_user_name
        if ssl_ca_certificate_arn is not None:
            self._values["ssl_ca_certificate_arn"] = ssl_ca_certificate_arn
        if ssl_security_protocol is not None:
            self._values["ssl_security_protocol"] = ssl_security_protocol

    @builtins.property
    def auth_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_type DmsEndpoint#auth_type}.'''
        result = self._values.get("auth_type")
        assert result is not None, "Required property 'auth_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def port(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#port DmsEndpoint#port}.'''
        result = self._values.get("port")
        assert result is not None, "Required property 'port' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def server_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_name DmsEndpoint#server_name}.'''
        result = self._values.get("server_name")
        assert result is not None, "Required property 'server_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def auth_password(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_password DmsEndpoint#auth_password}.'''
        result = self._values.get("auth_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auth_user_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#auth_user_name DmsEndpoint#auth_user_name}.'''
        result = self._values.get("auth_user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_ca_certificate_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_ca_certificate_arn DmsEndpoint#ssl_ca_certificate_arn}.'''
        result = self._values.get("ssl_ca_certificate_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ssl_security_protocol(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#ssl_security_protocol DmsEndpoint#ssl_security_protocol}.'''
        result = self._values.get("ssl_security_protocol")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointRedisSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointRedisSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointRedisSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__562a9e3ec3014f20ac3b4bfd8745e897f7af5df04bb227c422951e23832917d4)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAuthPassword")
    def reset_auth_password(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthPassword", []))

    @jsii.member(jsii_name="resetAuthUserName")
    def reset_auth_user_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuthUserName", []))

    @jsii.member(jsii_name="resetSslCaCertificateArn")
    def reset_ssl_ca_certificate_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslCaCertificateArn", []))

    @jsii.member(jsii_name="resetSslSecurityProtocol")
    def reset_ssl_security_protocol(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSslSecurityProtocol", []))

    @builtins.property
    @jsii.member(jsii_name="authPasswordInput")
    def auth_password_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authPasswordInput"))

    @builtins.property
    @jsii.member(jsii_name="authTypeInput")
    def auth_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="authUserNameInput")
    def auth_user_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "authUserNameInput"))

    @builtins.property
    @jsii.member(jsii_name="portInput")
    def port_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "portInput"))

    @builtins.property
    @jsii.member(jsii_name="serverNameInput")
    def server_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serverNameInput"))

    @builtins.property
    @jsii.member(jsii_name="sslCaCertificateArnInput")
    def ssl_ca_certificate_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslCaCertificateArnInput"))

    @builtins.property
    @jsii.member(jsii_name="sslSecurityProtocolInput")
    def ssl_security_protocol_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sslSecurityProtocolInput"))

    @builtins.property
    @jsii.member(jsii_name="authPassword")
    def auth_password(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authPassword"))

    @auth_password.setter
    def auth_password(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3b23bcee791ca9db3d06a08eed485b923b242a00f27f00f484a094575102ad4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authPassword", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authType")
    def auth_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authType"))

    @auth_type.setter
    def auth_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__895393c02032c243d7b9b6907f1545d8586a54a61645194927ba50c2d470cad4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="authUserName")
    def auth_user_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "authUserName"))

    @auth_user_name.setter
    def auth_user_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__95e4b48b1d0b195796c392c497cd75d8caf2f6db5e8db63ec8c7f70d2ce7a3a8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "authUserName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="port")
    def port(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "port"))

    @port.setter
    def port(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57803493fd1b118fcb4e605b3cb31ace1ad61a4505b8842a4b1ad447a434b19f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "port", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serverName")
    def server_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serverName"))

    @server_name.setter
    def server_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5a833d9c75eb1cf9f1b9c201f34aae7ac4659e08a7170129b46f08a762543676)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serverName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslCaCertificateArn")
    def ssl_ca_certificate_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslCaCertificateArn"))

    @ssl_ca_certificate_arn.setter
    def ssl_ca_certificate_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__51c26a619c62a3b989d8c75d3bd4b7426101908fc7fa5f701df7f18492c4fab0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslCaCertificateArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sslSecurityProtocol")
    def ssl_security_protocol(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sslSecurityProtocol"))

    @ssl_security_protocol.setter
    def ssl_security_protocol(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__32d2a366b734ff596e7cb09dddeb25ec12e89bfcba3bcf4bd785bcd63bf0f62a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sslSecurityProtocol", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointRedisSettings]:
        return typing.cast(typing.Optional[DmsEndpointRedisSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(self, value: typing.Optional[DmsEndpointRedisSettings]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a13d8a349b8e5eaaeeba84832b546c64e708eafb3a550aa2e917d5a48cb23993)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointRedshiftSettings",
    jsii_struct_bases=[],
    name_mapping={
        "bucket_folder": "bucketFolder",
        "bucket_name": "bucketName",
        "encryption_mode": "encryptionMode",
        "server_side_encryption_kms_key_id": "serverSideEncryptionKmsKeyId",
        "service_access_role_arn": "serviceAccessRoleArn",
    },
)
class DmsEndpointRedshiftSettings:
    def __init__(
        self,
        *,
        bucket_folder: typing.Optional[builtins.str] = None,
        bucket_name: typing.Optional[builtins.str] = None,
        encryption_mode: typing.Optional[builtins.str] = None,
        server_side_encryption_kms_key_id: typing.Optional[builtins.str] = None,
        service_access_role_arn: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param bucket_folder: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_folder DmsEndpoint#bucket_folder}.
        :param bucket_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_name DmsEndpoint#bucket_name}.
        :param encryption_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#encryption_mode DmsEndpoint#encryption_mode}.
        :param server_side_encryption_kms_key_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_side_encryption_kms_key_id DmsEndpoint#server_side_encryption_kms_key_id}.
        :param service_access_role_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f0da139105dead4f8773f3206d271e1e0fd0188c4f5642a1d59017ad2b7706a5)
            check_type(argname="argument bucket_folder", value=bucket_folder, expected_type=type_hints["bucket_folder"])
            check_type(argname="argument bucket_name", value=bucket_name, expected_type=type_hints["bucket_name"])
            check_type(argname="argument encryption_mode", value=encryption_mode, expected_type=type_hints["encryption_mode"])
            check_type(argname="argument server_side_encryption_kms_key_id", value=server_side_encryption_kms_key_id, expected_type=type_hints["server_side_encryption_kms_key_id"])
            check_type(argname="argument service_access_role_arn", value=service_access_role_arn, expected_type=type_hints["service_access_role_arn"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if bucket_folder is not None:
            self._values["bucket_folder"] = bucket_folder
        if bucket_name is not None:
            self._values["bucket_name"] = bucket_name
        if encryption_mode is not None:
            self._values["encryption_mode"] = encryption_mode
        if server_side_encryption_kms_key_id is not None:
            self._values["server_side_encryption_kms_key_id"] = server_side_encryption_kms_key_id
        if service_access_role_arn is not None:
            self._values["service_access_role_arn"] = service_access_role_arn

    @builtins.property
    def bucket_folder(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_folder DmsEndpoint#bucket_folder}.'''
        result = self._values.get("bucket_folder")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bucket_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#bucket_name DmsEndpoint#bucket_name}.'''
        result = self._values.get("bucket_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def encryption_mode(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#encryption_mode DmsEndpoint#encryption_mode}.'''
        result = self._values.get("encryption_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def server_side_encryption_kms_key_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#server_side_encryption_kms_key_id DmsEndpoint#server_side_encryption_kms_key_id}.'''
        result = self._values.get("server_side_encryption_kms_key_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_access_role_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#service_access_role_arn DmsEndpoint#service_access_role_arn}.'''
        result = self._values.get("service_access_role_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointRedshiftSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointRedshiftSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointRedshiftSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__48ba72edc6bc6f0778c2d6f3829bbf6ee648d252e64c4e1acc46da4058b66681)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetBucketFolder")
    def reset_bucket_folder(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBucketFolder", []))

    @jsii.member(jsii_name="resetBucketName")
    def reset_bucket_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBucketName", []))

    @jsii.member(jsii_name="resetEncryptionMode")
    def reset_encryption_mode(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEncryptionMode", []))

    @jsii.member(jsii_name="resetServerSideEncryptionKmsKeyId")
    def reset_server_side_encryption_kms_key_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServerSideEncryptionKmsKeyId", []))

    @jsii.member(jsii_name="resetServiceAccessRoleArn")
    def reset_service_access_role_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServiceAccessRoleArn", []))

    @builtins.property
    @jsii.member(jsii_name="bucketFolderInput")
    def bucket_folder_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "bucketFolderInput"))

    @builtins.property
    @jsii.member(jsii_name="bucketNameInput")
    def bucket_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "bucketNameInput"))

    @builtins.property
    @jsii.member(jsii_name="encryptionModeInput")
    def encryption_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "encryptionModeInput"))

    @builtins.property
    @jsii.member(jsii_name="serverSideEncryptionKmsKeyIdInput")
    def server_side_encryption_kms_key_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serverSideEncryptionKmsKeyIdInput"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArnInput")
    def service_access_role_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceAccessRoleArnInput"))

    @builtins.property
    @jsii.member(jsii_name="bucketFolder")
    def bucket_folder(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "bucketFolder"))

    @bucket_folder.setter
    def bucket_folder(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__98ed6d12514bdefc735864e7bb30874ff9e4ad206813b0a80388f61b19e3347f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "bucketFolder", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="bucketName")
    def bucket_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "bucketName"))

    @bucket_name.setter
    def bucket_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fe4d784028e893f6f1ca135f101d20c362e4ad29b489fa2b6dbbbcd837ca2364)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "bucketName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="encryptionMode")
    def encryption_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "encryptionMode"))

    @encryption_mode.setter
    def encryption_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e46c85dfb30fd1448ed94d6440b76b573c02a723c47b62f3946a0b157e055ae)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "encryptionMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serverSideEncryptionKmsKeyId")
    def server_side_encryption_kms_key_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serverSideEncryptionKmsKeyId"))

    @server_side_encryption_kms_key_id.setter
    def server_side_encryption_kms_key_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb6e7b600d493ac6226f3875a7fcb470d85c5b8db4587154d4af9c841d408460)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serverSideEncryptionKmsKeyId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="serviceAccessRoleArn")
    def service_access_role_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccessRoleArn"))

    @service_access_role_arn.setter
    def service_access_role_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__42eff508c83d2d1691d495cd0267b6ce069fb3e3cdfc64d31d606a22cbbaaf73)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "serviceAccessRoleArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DmsEndpointRedshiftSettings]:
        return typing.cast(typing.Optional[DmsEndpointRedshiftSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DmsEndpointRedshiftSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__21929f1fff8ed970ca355c31fac86f1f074599b2cb59236705c9c75c5aa18792)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointTimeouts",
    jsii_struct_bases=[],
    name_mapping={"create": "create", "delete": "delete"},
)
class DmsEndpointTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#create DmsEndpoint#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#delete DmsEndpoint#delete}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4d87d763f58942e82905ab9060088dddf2c15d5f47a141795eda8fe0fb38d376)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#create DmsEndpoint#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/dms_endpoint#delete DmsEndpoint#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DmsEndpointTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DmsEndpointTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.dmsEndpoint.DmsEndpointTimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__c6200c827b1722f3ff987961eb48ef22a6ca7defce51f0d931f1df8cc2fbec56)
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
            type_hints = typing.get_type_hints(_typecheckingstub__2c501ed5bc82fbf1d8110302183eb4bb2a6c6afb95234903fb113fa14453d859)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04a893b3a3582e5667e13530c29ee023ca538e5701975e8ad37c6a62a8ab8e86)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DmsEndpointTimeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DmsEndpointTimeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DmsEndpointTimeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__446136d3b550d83fd505eb36e4e5ff7750a72385ba13f6519199aa81badbbeb3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DmsEndpoint",
    "DmsEndpointConfig",
    "DmsEndpointElasticsearchSettings",
    "DmsEndpointElasticsearchSettingsOutputReference",
    "DmsEndpointKafkaSettings",
    "DmsEndpointKafkaSettingsOutputReference",
    "DmsEndpointKinesisSettings",
    "DmsEndpointKinesisSettingsOutputReference",
    "DmsEndpointMongodbSettings",
    "DmsEndpointMongodbSettingsOutputReference",
    "DmsEndpointMysqlSettings",
    "DmsEndpointMysqlSettingsOutputReference",
    "DmsEndpointOracleSettings",
    "DmsEndpointOracleSettingsOutputReference",
    "DmsEndpointPostgresSettings",
    "DmsEndpointPostgresSettingsOutputReference",
    "DmsEndpointRedisSettings",
    "DmsEndpointRedisSettingsOutputReference",
    "DmsEndpointRedshiftSettings",
    "DmsEndpointRedshiftSettingsOutputReference",
    "DmsEndpointTimeouts",
    "DmsEndpointTimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__2192e6db95bbd3c1e222723ec4801db2d95abb842294f35cfedb741c69ea91a5(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    endpoint_id: builtins.str,
    endpoint_type: builtins.str,
    engine_name: builtins.str,
    certificate_arn: typing.Optional[builtins.str] = None,
    database_name: typing.Optional[builtins.str] = None,
    elasticsearch_settings: typing.Optional[typing.Union[DmsEndpointElasticsearchSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    extra_connection_attributes: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    kafka_settings: typing.Optional[typing.Union[DmsEndpointKafkaSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    kinesis_settings: typing.Optional[typing.Union[DmsEndpointKinesisSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    kms_key_arn: typing.Optional[builtins.str] = None,
    mongodb_settings: typing.Optional[typing.Union[DmsEndpointMongodbSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    mysql_settings: typing.Optional[typing.Union[DmsEndpointMysqlSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    oracle_settings: typing.Optional[typing.Union[DmsEndpointOracleSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    password: typing.Optional[builtins.str] = None,
    pause_replication_tasks: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    port: typing.Optional[jsii.Number] = None,
    postgres_settings: typing.Optional[typing.Union[DmsEndpointPostgresSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    redis_settings: typing.Optional[typing.Union[DmsEndpointRedisSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    redshift_settings: typing.Optional[typing.Union[DmsEndpointRedshiftSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    region: typing.Optional[builtins.str] = None,
    secrets_manager_access_role_arn: typing.Optional[builtins.str] = None,
    secrets_manager_arn: typing.Optional[builtins.str] = None,
    server_name: typing.Optional[builtins.str] = None,
    service_access_role: typing.Optional[builtins.str] = None,
    ssl_mode: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[DmsEndpointTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
    username: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__8efcd06129a937ea04367e27ffe1e4ff935dd1355008430cafa827575ef27a7c(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cebc3fa4191b482073c87ab36c6537b9b139d156a3b076becc42e268a70383e4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3adffca33d9789282dfba04e7818d19fd07db031f261f3ed92a7ec1ee082fc7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__835aa38fd2b582fab4d4479d60d86f2cd3da81c3aa0b3ca2d5d64dfc1a63cda7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e135f511891729bd78bd62e9b36aa11457f25813fcc51ab37b888064d7632cb4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d37d198f35ce56f661a88b3cea5bb794eb159955e1f0470ea337c614cfc08bb6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8f6e473bec31336b04a394af423612cad1895d5484077251ffd9456c90746e33(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__75baa2fc42e97a8261191e0bc05381ef0e0b80a4c698a4ce81ecc190ce3706c0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__685fc18f4b03a4810c4952552326d223f2d949c850398ba510c83e12b2dec0bb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d553467784269896dd783cb5e561ae83ef84d03dd4df9fa0db8f1aec88b0a19(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f626ce9d526290606ad2fc7f0df7fd40cc351c8208b958e3bbaf07b8e59a11bc(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8f04703621e8d9841f94d1a63ba193bc33c94a2c200e4de39e40c09685e36766(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__739aec50cd48e9018e03b0e88dff9f75cb065932bb4719e3c943a3800a25c619(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99106f54f1facb2c291e0ee1720b6e7920ebf75a458ac4b57d53ca02329aea5b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26e10e4cd3dbb3ada2e06b1b973469ab1883f4dd05845d74cbfd8e292de4aa13(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c1af796ee69fd0136f4799081edafda89f7bbd5ce723a7ece3b48e380622254b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b9b3258ac4a714fc5ce58be8fae2a570646c5cf4b736297e245dadf7675726dd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6211382e30ba6cd00299fd701ef0c819ccc5761011a2deac9cee28ecc1395cf0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dd21707b73c2ab70bf8566a32a3d595d6986164415f38793c9b306bba4ef623a(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__73ad004a62dab574dbd4a1a0d2607df02109106b4cdfdd0b52206b9422c7390d(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8aa7413373abbac26dc905582bc4eee5e21137057d4adddbc8de2f1050fd23da(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f63b4535dcb041179f8b16b4b49939ed5db85d38d11371d703a88a03460441c(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    endpoint_id: builtins.str,
    endpoint_type: builtins.str,
    engine_name: builtins.str,
    certificate_arn: typing.Optional[builtins.str] = None,
    database_name: typing.Optional[builtins.str] = None,
    elasticsearch_settings: typing.Optional[typing.Union[DmsEndpointElasticsearchSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    extra_connection_attributes: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    kafka_settings: typing.Optional[typing.Union[DmsEndpointKafkaSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    kinesis_settings: typing.Optional[typing.Union[DmsEndpointKinesisSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    kms_key_arn: typing.Optional[builtins.str] = None,
    mongodb_settings: typing.Optional[typing.Union[DmsEndpointMongodbSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    mysql_settings: typing.Optional[typing.Union[DmsEndpointMysqlSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    oracle_settings: typing.Optional[typing.Union[DmsEndpointOracleSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    password: typing.Optional[builtins.str] = None,
    pause_replication_tasks: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    port: typing.Optional[jsii.Number] = None,
    postgres_settings: typing.Optional[typing.Union[DmsEndpointPostgresSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    redis_settings: typing.Optional[typing.Union[DmsEndpointRedisSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    redshift_settings: typing.Optional[typing.Union[DmsEndpointRedshiftSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    region: typing.Optional[builtins.str] = None,
    secrets_manager_access_role_arn: typing.Optional[builtins.str] = None,
    secrets_manager_arn: typing.Optional[builtins.str] = None,
    server_name: typing.Optional[builtins.str] = None,
    service_access_role: typing.Optional[builtins.str] = None,
    ssl_mode: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[DmsEndpointTimeouts, typing.Dict[builtins.str, typing.Any]]] = None,
    username: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__80b20329fa59319406e971f29756c823d39d08290b3116d710cb84d35635086f(
    *,
    endpoint_uri: builtins.str,
    service_access_role_arn: builtins.str,
    error_retry_duration: typing.Optional[jsii.Number] = None,
    full_load_error_percentage: typing.Optional[jsii.Number] = None,
    use_new_mapping_type: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b38f1d1980795ca04bc8017e7b97d67ac892352fd0d698c9b9404cee51544bc3(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9922f514b45243459312729bde5d200acb94cb53f874671c5152a9bcb62aa8ed(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37c6badd2b28bd9edc461cfd3edac36d4247b6171d5387d9b10ab7939f4d03fe(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8387c3106ddda203d6b798e812360a4825b09707cde831abc5fa4d6f5f7a52e9(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82e8915124061e0e9fdd03750cbbe1e3abbdd57fd4c0fb8090ed209e71e9cb89(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d043df6b98ac5e5fab92e160f5a1e0d09579a0d0c3c9ef7066e2a3fdd25b9a4a(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8513f0e705c2bb03f77aaf456e2750415450d06a31c1f0b32357485ebd0f9b4b(
    value: typing.Optional[DmsEndpointElasticsearchSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0fa6da922b4d6ea7ecf9ba280c680fdedb96557ef753a2eef2dd4f1bc20674ad(
    *,
    broker: builtins.str,
    include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    message_format: typing.Optional[builtins.str] = None,
    message_max_bytes: typing.Optional[jsii.Number] = None,
    no_hex_prefix: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    sasl_mechanism: typing.Optional[builtins.str] = None,
    sasl_password: typing.Optional[builtins.str] = None,
    sasl_username: typing.Optional[builtins.str] = None,
    security_protocol: typing.Optional[builtins.str] = None,
    ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
    ssl_client_certificate_arn: typing.Optional[builtins.str] = None,
    ssl_client_key_arn: typing.Optional[builtins.str] = None,
    ssl_client_key_password: typing.Optional[builtins.str] = None,
    topic: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4826dd7535cb2a7c7046fdb6d13758c081f45675a92801c27de2be1129e64f05(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5668c4a1246844437ce773676e3c93ab47c44fa2a6cd24aedc5210ebeebbc897(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a3d99476eecbdc431c06af1e82086bcc2af58c1e36609929c679278183f0dd6(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4b9371fc1660ef038a3f418e8b7447cb3301b0286348a81975de474a8bdb87d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f9015006cc78b9397936c538050def7dbe63f8fbb5a5bef520065c321bb5b67(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d9022cb432b3f3d9b21491953c62ce6325adec9e5932a3729a9626205e69ead2(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be4b6d755c6257bcfbf6e7ee55a9dd667e163297fb1c3689a6f35b76bb257864(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__32d121cbb90c3c9235c32df170e318e2318fced4bbf50834ed3d808c1b10b5fc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__792ebb9800fba89b1aea82acab567e5a217160919f1372a688759bfee3e9d828(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__86c867539815ce78bba16a502cf1dcf0a0fd166ca42e7a50b402cf40a60977c0(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__132b8c964fd78897f67f3265460fc4a31796b094784211b7ef05f805e0c7c1f2(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eff8df4d8aaec81466c26f520e337d792cd455ef1939bc37735972cd1952b566(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b21865779a02ad0580df0517bb3556cfdc4c2df35f428bef24a4f2b80c540b55(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b8b365dd5bf9471bc5a2a9cee7881dbbaa233d8c18e253aa28ee1deb6e926cdd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f616a5aa6cd1d9c0db4e6ba844709ef3d5a36f4fa98cc686508f08c892a2e573(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c78843566af5c77923b42a4e4dc6be6378e6e3475c7f48e5abe9c76eecae6fc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dd09233debc20d0b17bb05a1e5eb7963cd5c6f9e1f224e6fbdcb745bc7b62dc8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a63f6b2974112ca8dff335cd83a0778c688d07ac325d6f65164f7d6d2ae4eae5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5bf8eed2ee037004be98c4ca7aaa6b3d76a14421441c8067bb5de0d78d5dab28(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0e1f3cbf1f803ab73af8d78e058e1be9c06be52f61e8e28171ece24c743045e0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e3ad11f19fed72a04f196d3b05d1cf48bbcc8a313ff222636fafc572e4e4f1f9(
    value: typing.Optional[DmsEndpointKafkaSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5209fde3820cb3449e83764c30d7adae484726d247a77a22d7a99732e2adf563(
    *,
    include_control_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_null_and_empty: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_partition_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_table_alter_operations: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    include_transaction_details: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    message_format: typing.Optional[builtins.str] = None,
    partition_include_schema_table: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    service_access_role_arn: typing.Optional[builtins.str] = None,
    stream_arn: typing.Optional[builtins.str] = None,
    use_large_integer_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__569f5f4cbeb2e2c9e0dd7cd6a971cbe974abea45ff897989ebd766a135c7b911(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fccc5d3ee78201301674f7eead8d54ebead0b796cf31cb8872e4fa292b6e3235(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a2a423d56be09810e0c9abf79a40d65d88c20cf703da31ed0069050121e62f1(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2dd636513e0a975b4a28c4e57e517ede06b7b5d4ae5b616ba416b7d81154664e(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__943afb398e1022bf7eafdcf4da0c0617154e85914f7e506f08d374be60138b25(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dca559d71edec97eea849765bddb33d99d680b2d0ba43611096f683502f54ed8(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__afe1fa1c596228d0c4398025dc81f51516b4f2931a2f3f1c7ab2f8d7b9e56458(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__724c575a9addb56880f1992896e22ec9ff9205d1ff0a0b268249c01673b2871b(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37c19a9214fad1a14f3344f364f8a25f4475b1a05e62988f549bfbdbd1bdc403(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ad2034e1d5aaf2b466c780a634cd8f48f8fc509a6276af142755b7e9203ce82(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d1213f1c3f04cf53c4b6a0a1c2a97e92b578f68fc125cc1c922b7668033c2df(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__abb0fbd777f3ad3dc591f1ea06286b0c8c19694236520c5b5641bae2d6d920cf(
    value: typing.Optional[DmsEndpointKinesisSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__76da229b66ed9b2812c7f54f35b55c5a1777457b05b2a3a5d4c841ef1d42dea4(
    *,
    auth_mechanism: typing.Optional[builtins.str] = None,
    auth_source: typing.Optional[builtins.str] = None,
    auth_type: typing.Optional[builtins.str] = None,
    docs_to_investigate: typing.Optional[builtins.str] = None,
    extract_doc_id: typing.Optional[builtins.str] = None,
    nesting_level: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b249fcafeb0b283544326d4c654998ca301842664dfd7a3e8930c427e38dd135(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc679e242c97b652bfedf948450115cd6c20a3bf64cc72f4ccd50f527fc11b24(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5f3a79c790a8867f18b923332230ffdaa961740f6c87fa33585876b837df698(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99ee30f6655c911ba73dba87573e20b9db8f532eea81952c03265b6c51164eff(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e87292559811ffed11f0e687963d046ad7c73c15a9875704083cdc24bda8d5b5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d071dc10fc63d11f8c71d787f490a58acc8d0c69d43f2defc475510f27d25086(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f65bad0564d817056151aaa77309e91d0633761e523b4d46c2d0fed9b2cac60e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c6029abf69f2d29e577590da7331ccc2abc8eacf50a254e723644d52583f715(
    value: typing.Optional[DmsEndpointMongodbSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70090e44c206ba00f455d7b9961ddd886a3ed6c5d9c2d43e300afe8509d19dad(
    *,
    after_connect_script: typing.Optional[builtins.str] = None,
    authentication_method: typing.Optional[builtins.str] = None,
    clean_source_metadata_on_mismatch: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    events_poll_interval: typing.Optional[jsii.Number] = None,
    execute_timeout: typing.Optional[jsii.Number] = None,
    max_file_size: typing.Optional[jsii.Number] = None,
    parallel_load_threads: typing.Optional[jsii.Number] = None,
    server_timezone: typing.Optional[builtins.str] = None,
    service_access_role_arn: typing.Optional[builtins.str] = None,
    target_db_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c4d110f98bd7118dbbd699490efdfe979aaa783babcc167d46800392fd29ba4(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ca2d26969522cbccdd7f93f7e7e820d12b4fcf91058c329a5d667d776388e89d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__896216ee1f5ea05397c1eecf15836d54fd448a6740c7bde6391b5d69c7f25c53(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__41646ae3f988faf325250ddf50483b1ebefefd6961b08d4449b6c6716036b4d6(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0dd018972594c5e1cb25b2ebb2fe4e3016fdcff87cec8783b2882b2fef543ddd(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a7fa2fec1d0b57f8a9a96695761eefca4d01fd3ca7001c9863b928a7e9d95dfc(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d4fef54b3bd610acb24eb9becce8fe728df60ab06a450d405496d4610f1e1de8(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f476bb20e9229a0a400a63ae2babc048e12656047ec820de8d8b5c58cf38002(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dbffe36a2dd4e2077c86e79aa4f6abef73cdcd0a8d3ec71d4207669468cf82a9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b7ba6b01f6335313739c17f164b2b8d659ac08eb5812f3fcea26639f71402bfd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4be8cd109621ee6dee73bec35a8b1e2fa52e77f2db9e2ea59e6b0e6e06b94eda(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__459179f1edf2962bfbd3fbeaec61ef5f854c6fe3121bb0d84eff9ffc8a8bd6cc(
    value: typing.Optional[DmsEndpointMysqlSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a085d1847dbe0dc6ee415ee7e17345a4073d1655863c96df864f0669ccf47c16(
    *,
    authentication_method: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d408c40a51ea85c2a6e98e630d481c8d357efdd7c50a3f32d77b52fda55a9673(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__718cb59dd77d31a84df7feaad9a2cc1bf3e728b265669d34cefa4001667bcfe8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cb950905ad8c8091fb9154b4c748ee17c92ad0f8f50f069492127d83d3edbd33(
    value: typing.Optional[DmsEndpointOracleSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3857b2a7fe58b2662dbcf81b7d56645e33919fbf19652130f7fb94e86d3a8232(
    *,
    after_connect_script: typing.Optional[builtins.str] = None,
    authentication_method: typing.Optional[builtins.str] = None,
    babelfish_database_name: typing.Optional[builtins.str] = None,
    capture_ddls: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    database_mode: typing.Optional[builtins.str] = None,
    ddl_artifacts_schema: typing.Optional[builtins.str] = None,
    execute_timeout: typing.Optional[jsii.Number] = None,
    fail_tasks_on_lob_truncation: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    heartbeat_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    heartbeat_frequency: typing.Optional[jsii.Number] = None,
    heartbeat_schema: typing.Optional[builtins.str] = None,
    map_boolean_as_boolean: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    map_jsonb_as_clob: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    map_long_varchar_as: typing.Optional[builtins.str] = None,
    max_file_size: typing.Optional[jsii.Number] = None,
    plugin_name: typing.Optional[builtins.str] = None,
    service_access_role_arn: typing.Optional[builtins.str] = None,
    slot_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b3e6ebe93f6cd8b7ff04051541046e7812e080364c76a8283877a39e74aabe53(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92693c64d786acd8b6cb30062e22510817adef0ad0f0866fab68cea7b06befec(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae2e1d0b6a0f5f6f7a2a24d25501ce70c80479550d2c21d2d485ab8257207bfe(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a859a19d27cb607225bc210064bd784de5b8bf22cfb162290950f07dad12b1f3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8d6e7e5fc7e39b6f7e5b826bd7f8b72ce5e1e1b2ed55869a32dea9975b9181a4(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6703a2e26a0aec772457e488ad3cef91b4f5a6948ac2c474bddc8e49bec3e182(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de9d0406f0b4066fa91b12e59ed6b4201634a12e4552898e171243211ac81914(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c2d97cb08dd5af78949323574a96c84e0ad35ecef620c4476c20c8fdcc95eee(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__84724bd4e8bb2aa123125f54f5867bc4bb7de2dc01c5de9a1e17a9fe845f5ff0(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__61f1008a944d084ed15919f6f7baba5dc30a51a8c494b99e278cf2655ab6161d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__acf2346eb60a0c07e72aefd04879227f0340e1cade9e0ee1a00f084247f91dad(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91fff301f2d2fa176de6cfe83b24cc25249831dd9213e8005c52c7b4234a6550(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1dd5e4aaf95dc8f7a71db298c46f6fb9c60a2652976e851e0f510e9e64830f35(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d45152a4289d62b833132cda63cc98f0f6bc026530a469e279b79149ef0225c3(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f624a1186957b483e621e4506083b26c3f0261fadef9fe0b8fd0a21619546505(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__81573b74a662f80da2f7b8fb9974e6a25760bedd416fd294744be58104fd7abe(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f539d09adfbf0b6c82272e9a61408f7cc9b885dcb1ce8a4c9c189cb2a555db4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37a4e999cd9392fa359cc421b1077c5dd7decd6018a7984db4323b0eae74a090(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d2200fb4dbc800d8025702b2384c937dc4223a19cd69d3848ccfe534a6593781(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__adc5afb90297d08f49356bf77b97ded3a0af548de6bc8671a0963f458639e32c(
    value: typing.Optional[DmsEndpointPostgresSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26d887d8a5295deeeedcb256db19314a5184ca19a7001634e8a83b67f33a33cc(
    *,
    auth_type: builtins.str,
    port: jsii.Number,
    server_name: builtins.str,
    auth_password: typing.Optional[builtins.str] = None,
    auth_user_name: typing.Optional[builtins.str] = None,
    ssl_ca_certificate_arn: typing.Optional[builtins.str] = None,
    ssl_security_protocol: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__562a9e3ec3014f20ac3b4bfd8745e897f7af5df04bb227c422951e23832917d4(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3b23bcee791ca9db3d06a08eed485b923b242a00f27f00f484a094575102ad4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__895393c02032c243d7b9b6907f1545d8586a54a61645194927ba50c2d470cad4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__95e4b48b1d0b195796c392c497cd75d8caf2f6db5e8db63ec8c7f70d2ce7a3a8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57803493fd1b118fcb4e605b3cb31ace1ad61a4505b8842a4b1ad447a434b19f(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a833d9c75eb1cf9f1b9c201f34aae7ac4659e08a7170129b46f08a762543676(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__51c26a619c62a3b989d8c75d3bd4b7426101908fc7fa5f701df7f18492c4fab0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__32d2a366b734ff596e7cb09dddeb25ec12e89bfcba3bcf4bd785bcd63bf0f62a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a13d8a349b8e5eaaeeba84832b546c64e708eafb3a550aa2e917d5a48cb23993(
    value: typing.Optional[DmsEndpointRedisSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f0da139105dead4f8773f3206d271e1e0fd0188c4f5642a1d59017ad2b7706a5(
    *,
    bucket_folder: typing.Optional[builtins.str] = None,
    bucket_name: typing.Optional[builtins.str] = None,
    encryption_mode: typing.Optional[builtins.str] = None,
    server_side_encryption_kms_key_id: typing.Optional[builtins.str] = None,
    service_access_role_arn: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48ba72edc6bc6f0778c2d6f3829bbf6ee648d252e64c4e1acc46da4058b66681(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__98ed6d12514bdefc735864e7bb30874ff9e4ad206813b0a80388f61b19e3347f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe4d784028e893f6f1ca135f101d20c362e4ad29b489fa2b6dbbbcd837ca2364(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e46c85dfb30fd1448ed94d6440b76b573c02a723c47b62f3946a0b157e055ae(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb6e7b600d493ac6226f3875a7fcb470d85c5b8db4587154d4af9c841d408460(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__42eff508c83d2d1691d495cd0267b6ce069fb3e3cdfc64d31d606a22cbbaaf73(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__21929f1fff8ed970ca355c31fac86f1f074599b2cb59236705c9c75c5aa18792(
    value: typing.Optional[DmsEndpointRedshiftSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d87d763f58942e82905ab9060088dddf2c15d5f47a141795eda8fe0fb38d376(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c6200c827b1722f3ff987961eb48ef22a6ca7defce51f0d931f1df8cc2fbec56(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c501ed5bc82fbf1d8110302183eb4bb2a6c6afb95234903fb113fa14453d859(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04a893b3a3582e5667e13530c29ee023ca538e5701975e8ad37c6a62a8ab8e86(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__446136d3b550d83fd505eb36e4e5ff7750a72385ba13f6519199aa81badbbeb3(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DmsEndpointTimeouts]],
) -> None:
    """Type checking stubs"""
    pass
