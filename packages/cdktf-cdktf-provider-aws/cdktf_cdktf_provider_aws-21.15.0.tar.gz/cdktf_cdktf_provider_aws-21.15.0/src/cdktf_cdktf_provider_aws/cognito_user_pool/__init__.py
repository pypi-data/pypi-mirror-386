r'''
# `aws_cognito_user_pool`

Refer to the Terraform Registry for docs: [`aws_cognito_user_pool`](https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool).
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


class CognitoUserPool(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPool",
):
    '''Represents a {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool aws_cognito_user_pool}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        name: builtins.str,
        account_recovery_setting: typing.Optional[typing.Union["CognitoUserPoolAccountRecoverySetting", typing.Dict[builtins.str, typing.Any]]] = None,
        admin_create_user_config: typing.Optional[typing.Union["CognitoUserPoolAdminCreateUserConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        alias_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        auto_verified_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        deletion_protection: typing.Optional[builtins.str] = None,
        device_configuration: typing.Optional[typing.Union["CognitoUserPoolDeviceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_configuration: typing.Optional[typing.Union["CognitoUserPoolEmailConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_mfa_configuration: typing.Optional[typing.Union["CognitoUserPoolEmailMfaConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_verification_message: typing.Optional[builtins.str] = None,
        email_verification_subject: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        lambda_config: typing.Optional[typing.Union["CognitoUserPoolLambdaConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        mfa_configuration: typing.Optional[builtins.str] = None,
        password_policy: typing.Optional[typing.Union["CognitoUserPoolPasswordPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        region: typing.Optional[builtins.str] = None,
        schema: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolSchema", typing.Dict[builtins.str, typing.Any]]]]] = None,
        sign_in_policy: typing.Optional[typing.Union["CognitoUserPoolSignInPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        sms_authentication_message: typing.Optional[builtins.str] = None,
        sms_configuration: typing.Optional[typing.Union["CognitoUserPoolSmsConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        sms_verification_message: typing.Optional[builtins.str] = None,
        software_token_mfa_configuration: typing.Optional[typing.Union["CognitoUserPoolSoftwareTokenMfaConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        user_attribute_update_settings: typing.Optional[typing.Union["CognitoUserPoolUserAttributeUpdateSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        username_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        username_configuration: typing.Optional[typing.Union["CognitoUserPoolUsernameConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        user_pool_add_ons: typing.Optional[typing.Union["CognitoUserPoolUserPoolAddOns", typing.Dict[builtins.str, typing.Any]]] = None,
        user_pool_tier: typing.Optional[builtins.str] = None,
        verification_message_template: typing.Optional[typing.Union["CognitoUserPoolVerificationMessageTemplate", typing.Dict[builtins.str, typing.Any]]] = None,
        web_authn_configuration: typing.Optional[typing.Union["CognitoUserPoolWebAuthnConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool aws_cognito_user_pool} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.
        :param account_recovery_setting: account_recovery_setting block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#account_recovery_setting CognitoUserPool#account_recovery_setting}
        :param admin_create_user_config: admin_create_user_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#admin_create_user_config CognitoUserPool#admin_create_user_config}
        :param alias_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#alias_attributes CognitoUserPool#alias_attributes}.
        :param auto_verified_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#auto_verified_attributes CognitoUserPool#auto_verified_attributes}.
        :param deletion_protection: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#deletion_protection CognitoUserPool#deletion_protection}.
        :param device_configuration: device_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_configuration CognitoUserPool#device_configuration}
        :param email_configuration: email_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_configuration CognitoUserPool#email_configuration}
        :param email_mfa_configuration: email_mfa_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_mfa_configuration CognitoUserPool#email_mfa_configuration}
        :param email_verification_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_message CognitoUserPool#email_verification_message}.
        :param email_verification_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_subject CognitoUserPool#email_verification_subject}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#id CognitoUserPool#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param lambda_config: lambda_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_config CognitoUserPool#lambda_config}
        :param mfa_configuration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#mfa_configuration CognitoUserPool#mfa_configuration}.
        :param password_policy: password_policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_policy CognitoUserPool#password_policy}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#region CognitoUserPool#region}
        :param schema: schema block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#schema CognitoUserPool#schema}
        :param sign_in_policy: sign_in_policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sign_in_policy CognitoUserPool#sign_in_policy}
        :param sms_authentication_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_authentication_message CognitoUserPool#sms_authentication_message}.
        :param sms_configuration: sms_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_configuration CognitoUserPool#sms_configuration}
        :param sms_verification_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_verification_message CognitoUserPool#sms_verification_message}.
        :param software_token_mfa_configuration: software_token_mfa_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#software_token_mfa_configuration CognitoUserPool#software_token_mfa_configuration}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags CognitoUserPool#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags_all CognitoUserPool#tags_all}.
        :param user_attribute_update_settings: user_attribute_update_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_attribute_update_settings CognitoUserPool#user_attribute_update_settings}
        :param username_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_attributes CognitoUserPool#username_attributes}.
        :param username_configuration: username_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_configuration CognitoUserPool#username_configuration}
        :param user_pool_add_ons: user_pool_add_ons block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_add_ons CognitoUserPool#user_pool_add_ons}
        :param user_pool_tier: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_tier CognitoUserPool#user_pool_tier}.
        :param verification_message_template: verification_message_template block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verification_message_template CognitoUserPool#verification_message_template}
        :param web_authn_configuration: web_authn_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#web_authn_configuration CognitoUserPool#web_authn_configuration}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__df240343676b855452fad7604d73009e4e700668f14d3349a7b0a18dd56eb538)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = CognitoUserPoolConfig(
            name=name,
            account_recovery_setting=account_recovery_setting,
            admin_create_user_config=admin_create_user_config,
            alias_attributes=alias_attributes,
            auto_verified_attributes=auto_verified_attributes,
            deletion_protection=deletion_protection,
            device_configuration=device_configuration,
            email_configuration=email_configuration,
            email_mfa_configuration=email_mfa_configuration,
            email_verification_message=email_verification_message,
            email_verification_subject=email_verification_subject,
            id=id,
            lambda_config=lambda_config,
            mfa_configuration=mfa_configuration,
            password_policy=password_policy,
            region=region,
            schema=schema,
            sign_in_policy=sign_in_policy,
            sms_authentication_message=sms_authentication_message,
            sms_configuration=sms_configuration,
            sms_verification_message=sms_verification_message,
            software_token_mfa_configuration=software_token_mfa_configuration,
            tags=tags,
            tags_all=tags_all,
            user_attribute_update_settings=user_attribute_update_settings,
            username_attributes=username_attributes,
            username_configuration=username_configuration,
            user_pool_add_ons=user_pool_add_ons,
            user_pool_tier=user_pool_tier,
            verification_message_template=verification_message_template,
            web_authn_configuration=web_authn_configuration,
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
        '''Generates CDKTF code for importing a CognitoUserPool resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the CognitoUserPool to import.
        :param import_from_id: The id of the existing CognitoUserPool that should be imported. Refer to the {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the CognitoUserPool to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da4182bd7d22389615b86ac1d38af4244548fb62e233d453b13a6ceeb876f56a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putAccountRecoverySetting")
    def put_account_recovery_setting(
        self,
        *,
        recovery_mechanism: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolAccountRecoverySettingRecoveryMechanism", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param recovery_mechanism: recovery_mechanism block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#recovery_mechanism CognitoUserPool#recovery_mechanism}
        '''
        value = CognitoUserPoolAccountRecoverySetting(
            recovery_mechanism=recovery_mechanism
        )

        return typing.cast(None, jsii.invoke(self, "putAccountRecoverySetting", [value]))

    @jsii.member(jsii_name="putAdminCreateUserConfig")
    def put_admin_create_user_config(
        self,
        *,
        allow_admin_create_user_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        invite_message_template: typing.Optional[typing.Union["CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param allow_admin_create_user_only: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allow_admin_create_user_only CognitoUserPool#allow_admin_create_user_only}.
        :param invite_message_template: invite_message_template block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#invite_message_template CognitoUserPool#invite_message_template}
        '''
        value = CognitoUserPoolAdminCreateUserConfig(
            allow_admin_create_user_only=allow_admin_create_user_only,
            invite_message_template=invite_message_template,
        )

        return typing.cast(None, jsii.invoke(self, "putAdminCreateUserConfig", [value]))

    @jsii.member(jsii_name="putDeviceConfiguration")
    def put_device_configuration(
        self,
        *,
        challenge_required_on_new_device: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        device_only_remembered_on_user_prompt: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param challenge_required_on_new_device: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#challenge_required_on_new_device CognitoUserPool#challenge_required_on_new_device}.
        :param device_only_remembered_on_user_prompt: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_only_remembered_on_user_prompt CognitoUserPool#device_only_remembered_on_user_prompt}.
        '''
        value = CognitoUserPoolDeviceConfiguration(
            challenge_required_on_new_device=challenge_required_on_new_device,
            device_only_remembered_on_user_prompt=device_only_remembered_on_user_prompt,
        )

        return typing.cast(None, jsii.invoke(self, "putDeviceConfiguration", [value]))

    @jsii.member(jsii_name="putEmailConfiguration")
    def put_email_configuration(
        self,
        *,
        configuration_set: typing.Optional[builtins.str] = None,
        email_sending_account: typing.Optional[builtins.str] = None,
        from_email_address: typing.Optional[builtins.str] = None,
        reply_to_email_address: typing.Optional[builtins.str] = None,
        source_arn: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param configuration_set: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#configuration_set CognitoUserPool#configuration_set}.
        :param email_sending_account: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_sending_account CognitoUserPool#email_sending_account}.
        :param from_email_address: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#from_email_address CognitoUserPool#from_email_address}.
        :param reply_to_email_address: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#reply_to_email_address CognitoUserPool#reply_to_email_address}.
        :param source_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#source_arn CognitoUserPool#source_arn}.
        '''
        value = CognitoUserPoolEmailConfiguration(
            configuration_set=configuration_set,
            email_sending_account=email_sending_account,
            from_email_address=from_email_address,
            reply_to_email_address=reply_to_email_address,
            source_arn=source_arn,
        )

        return typing.cast(None, jsii.invoke(self, "putEmailConfiguration", [value]))

    @jsii.member(jsii_name="putEmailMfaConfiguration")
    def put_email_mfa_configuration(
        self,
        *,
        message: typing.Optional[builtins.str] = None,
        subject: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#message CognitoUserPool#message}.
        :param subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#subject CognitoUserPool#subject}.
        '''
        value = CognitoUserPoolEmailMfaConfiguration(message=message, subject=subject)

        return typing.cast(None, jsii.invoke(self, "putEmailMfaConfiguration", [value]))

    @jsii.member(jsii_name="putLambdaConfig")
    def put_lambda_config(
        self,
        *,
        create_auth_challenge: typing.Optional[builtins.str] = None,
        custom_email_sender: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigCustomEmailSender", typing.Dict[builtins.str, typing.Any]]] = None,
        custom_message: typing.Optional[builtins.str] = None,
        custom_sms_sender: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigCustomSmsSender", typing.Dict[builtins.str, typing.Any]]] = None,
        define_auth_challenge: typing.Optional[builtins.str] = None,
        kms_key_id: typing.Optional[builtins.str] = None,
        post_authentication: typing.Optional[builtins.str] = None,
        post_confirmation: typing.Optional[builtins.str] = None,
        pre_authentication: typing.Optional[builtins.str] = None,
        pre_sign_up: typing.Optional[builtins.str] = None,
        pre_token_generation: typing.Optional[builtins.str] = None,
        pre_token_generation_config: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigPreTokenGenerationConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        user_migration: typing.Optional[builtins.str] = None,
        verify_auth_challenge_response: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create_auth_challenge: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#create_auth_challenge CognitoUserPool#create_auth_challenge}.
        :param custom_email_sender: custom_email_sender block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_email_sender CognitoUserPool#custom_email_sender}
        :param custom_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_message CognitoUserPool#custom_message}.
        :param custom_sms_sender: custom_sms_sender block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_sms_sender CognitoUserPool#custom_sms_sender}
        :param define_auth_challenge: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#define_auth_challenge CognitoUserPool#define_auth_challenge}.
        :param kms_key_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#kms_key_id CognitoUserPool#kms_key_id}.
        :param post_authentication: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_authentication CognitoUserPool#post_authentication}.
        :param post_confirmation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_confirmation CognitoUserPool#post_confirmation}.
        :param pre_authentication: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_authentication CognitoUserPool#pre_authentication}.
        :param pre_sign_up: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_sign_up CognitoUserPool#pre_sign_up}.
        :param pre_token_generation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation CognitoUserPool#pre_token_generation}.
        :param pre_token_generation_config: pre_token_generation_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation_config CognitoUserPool#pre_token_generation_config}
        :param user_migration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_migration CognitoUserPool#user_migration}.
        :param verify_auth_challenge_response: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verify_auth_challenge_response CognitoUserPool#verify_auth_challenge_response}.
        '''
        value = CognitoUserPoolLambdaConfig(
            create_auth_challenge=create_auth_challenge,
            custom_email_sender=custom_email_sender,
            custom_message=custom_message,
            custom_sms_sender=custom_sms_sender,
            define_auth_challenge=define_auth_challenge,
            kms_key_id=kms_key_id,
            post_authentication=post_authentication,
            post_confirmation=post_confirmation,
            pre_authentication=pre_authentication,
            pre_sign_up=pre_sign_up,
            pre_token_generation=pre_token_generation,
            pre_token_generation_config=pre_token_generation_config,
            user_migration=user_migration,
            verify_auth_challenge_response=verify_auth_challenge_response,
        )

        return typing.cast(None, jsii.invoke(self, "putLambdaConfig", [value]))

    @jsii.member(jsii_name="putPasswordPolicy")
    def put_password_policy(
        self,
        *,
        minimum_length: typing.Optional[jsii.Number] = None,
        password_history_size: typing.Optional[jsii.Number] = None,
        require_lowercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_numbers: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_symbols: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_uppercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        temporary_password_validity_days: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param minimum_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#minimum_length CognitoUserPool#minimum_length}.
        :param password_history_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_history_size CognitoUserPool#password_history_size}.
        :param require_lowercase: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_lowercase CognitoUserPool#require_lowercase}.
        :param require_numbers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_numbers CognitoUserPool#require_numbers}.
        :param require_symbols: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_symbols CognitoUserPool#require_symbols}.
        :param require_uppercase: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_uppercase CognitoUserPool#require_uppercase}.
        :param temporary_password_validity_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#temporary_password_validity_days CognitoUserPool#temporary_password_validity_days}.
        '''
        value = CognitoUserPoolPasswordPolicy(
            minimum_length=minimum_length,
            password_history_size=password_history_size,
            require_lowercase=require_lowercase,
            require_numbers=require_numbers,
            require_symbols=require_symbols,
            require_uppercase=require_uppercase,
            temporary_password_validity_days=temporary_password_validity_days,
        )

        return typing.cast(None, jsii.invoke(self, "putPasswordPolicy", [value]))

    @jsii.member(jsii_name="putSchema")
    def put_schema(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolSchema", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3df549de1be02fcca6b32888adb3deaadf042cd53bc95b91306521b378014671)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putSchema", [value]))

    @jsii.member(jsii_name="putSignInPolicy")
    def put_sign_in_policy(
        self,
        *,
        allowed_first_auth_factors: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param allowed_first_auth_factors: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allowed_first_auth_factors CognitoUserPool#allowed_first_auth_factors}.
        '''
        value = CognitoUserPoolSignInPolicy(
            allowed_first_auth_factors=allowed_first_auth_factors
        )

        return typing.cast(None, jsii.invoke(self, "putSignInPolicy", [value]))

    @jsii.member(jsii_name="putSmsConfiguration")
    def put_sms_configuration(
        self,
        *,
        external_id: builtins.str,
        sns_caller_arn: builtins.str,
        sns_region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param external_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#external_id CognitoUserPool#external_id}.
        :param sns_caller_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_caller_arn CognitoUserPool#sns_caller_arn}.
        :param sns_region: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_region CognitoUserPool#sns_region}.
        '''
        value = CognitoUserPoolSmsConfiguration(
            external_id=external_id,
            sns_caller_arn=sns_caller_arn,
            sns_region=sns_region,
        )

        return typing.cast(None, jsii.invoke(self, "putSmsConfiguration", [value]))

    @jsii.member(jsii_name="putSoftwareTokenMfaConfiguration")
    def put_software_token_mfa_configuration(
        self,
        *,
        enabled: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        '''
        :param enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#enabled CognitoUserPool#enabled}.
        '''
        value = CognitoUserPoolSoftwareTokenMfaConfiguration(enabled=enabled)

        return typing.cast(None, jsii.invoke(self, "putSoftwareTokenMfaConfiguration", [value]))

    @jsii.member(jsii_name="putUserAttributeUpdateSettings")
    def put_user_attribute_update_settings(
        self,
        *,
        attributes_require_verification_before_update: typing.Sequence[builtins.str],
    ) -> None:
        '''
        :param attributes_require_verification_before_update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#attributes_require_verification_before_update CognitoUserPool#attributes_require_verification_before_update}.
        '''
        value = CognitoUserPoolUserAttributeUpdateSettings(
            attributes_require_verification_before_update=attributes_require_verification_before_update,
        )

        return typing.cast(None, jsii.invoke(self, "putUserAttributeUpdateSettings", [value]))

    @jsii.member(jsii_name="putUsernameConfiguration")
    def put_username_configuration(
        self,
        *,
        case_sensitive: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param case_sensitive: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#case_sensitive CognitoUserPool#case_sensitive}.
        '''
        value = CognitoUserPoolUsernameConfiguration(case_sensitive=case_sensitive)

        return typing.cast(None, jsii.invoke(self, "putUsernameConfiguration", [value]))

    @jsii.member(jsii_name="putUserPoolAddOns")
    def put_user_pool_add_ons(
        self,
        *,
        advanced_security_mode: builtins.str,
        advanced_security_additional_flows: typing.Optional[typing.Union["CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param advanced_security_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_mode CognitoUserPool#advanced_security_mode}.
        :param advanced_security_additional_flows: advanced_security_additional_flows block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_additional_flows CognitoUserPool#advanced_security_additional_flows}
        '''
        value = CognitoUserPoolUserPoolAddOns(
            advanced_security_mode=advanced_security_mode,
            advanced_security_additional_flows=advanced_security_additional_flows,
        )

        return typing.cast(None, jsii.invoke(self, "putUserPoolAddOns", [value]))

    @jsii.member(jsii_name="putVerificationMessageTemplate")
    def put_verification_message_template(
        self,
        *,
        default_email_option: typing.Optional[builtins.str] = None,
        email_message: typing.Optional[builtins.str] = None,
        email_message_by_link: typing.Optional[builtins.str] = None,
        email_subject: typing.Optional[builtins.str] = None,
        email_subject_by_link: typing.Optional[builtins.str] = None,
        sms_message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param default_email_option: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#default_email_option CognitoUserPool#default_email_option}.
        :param email_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.
        :param email_message_by_link: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message_by_link CognitoUserPool#email_message_by_link}.
        :param email_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.
        :param email_subject_by_link: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject_by_link CognitoUserPool#email_subject_by_link}.
        :param sms_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.
        '''
        value = CognitoUserPoolVerificationMessageTemplate(
            default_email_option=default_email_option,
            email_message=email_message,
            email_message_by_link=email_message_by_link,
            email_subject=email_subject,
            email_subject_by_link=email_subject_by_link,
            sms_message=sms_message,
        )

        return typing.cast(None, jsii.invoke(self, "putVerificationMessageTemplate", [value]))

    @jsii.member(jsii_name="putWebAuthnConfiguration")
    def put_web_authn_configuration(
        self,
        *,
        relying_party_id: typing.Optional[builtins.str] = None,
        user_verification: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param relying_party_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#relying_party_id CognitoUserPool#relying_party_id}.
        :param user_verification: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_verification CognitoUserPool#user_verification}.
        '''
        value = CognitoUserPoolWebAuthnConfiguration(
            relying_party_id=relying_party_id, user_verification=user_verification
        )

        return typing.cast(None, jsii.invoke(self, "putWebAuthnConfiguration", [value]))

    @jsii.member(jsii_name="resetAccountRecoverySetting")
    def reset_account_recovery_setting(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAccountRecoverySetting", []))

    @jsii.member(jsii_name="resetAdminCreateUserConfig")
    def reset_admin_create_user_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAdminCreateUserConfig", []))

    @jsii.member(jsii_name="resetAliasAttributes")
    def reset_alias_attributes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAliasAttributes", []))

    @jsii.member(jsii_name="resetAutoVerifiedAttributes")
    def reset_auto_verified_attributes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAutoVerifiedAttributes", []))

    @jsii.member(jsii_name="resetDeletionProtection")
    def reset_deletion_protection(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeletionProtection", []))

    @jsii.member(jsii_name="resetDeviceConfiguration")
    def reset_device_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeviceConfiguration", []))

    @jsii.member(jsii_name="resetEmailConfiguration")
    def reset_email_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailConfiguration", []))

    @jsii.member(jsii_name="resetEmailMfaConfiguration")
    def reset_email_mfa_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailMfaConfiguration", []))

    @jsii.member(jsii_name="resetEmailVerificationMessage")
    def reset_email_verification_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailVerificationMessage", []))

    @jsii.member(jsii_name="resetEmailVerificationSubject")
    def reset_email_verification_subject(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailVerificationSubject", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetLambdaConfig")
    def reset_lambda_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLambdaConfig", []))

    @jsii.member(jsii_name="resetMfaConfiguration")
    def reset_mfa_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMfaConfiguration", []))

    @jsii.member(jsii_name="resetPasswordPolicy")
    def reset_password_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPasswordPolicy", []))

    @jsii.member(jsii_name="resetRegion")
    def reset_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRegion", []))

    @jsii.member(jsii_name="resetSchema")
    def reset_schema(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchema", []))

    @jsii.member(jsii_name="resetSignInPolicy")
    def reset_sign_in_policy(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSignInPolicy", []))

    @jsii.member(jsii_name="resetSmsAuthenticationMessage")
    def reset_sms_authentication_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSmsAuthenticationMessage", []))

    @jsii.member(jsii_name="resetSmsConfiguration")
    def reset_sms_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSmsConfiguration", []))

    @jsii.member(jsii_name="resetSmsVerificationMessage")
    def reset_sms_verification_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSmsVerificationMessage", []))

    @jsii.member(jsii_name="resetSoftwareTokenMfaConfiguration")
    def reset_software_token_mfa_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSoftwareTokenMfaConfiguration", []))

    @jsii.member(jsii_name="resetTags")
    def reset_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTags", []))

    @jsii.member(jsii_name="resetTagsAll")
    def reset_tags_all(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTagsAll", []))

    @jsii.member(jsii_name="resetUserAttributeUpdateSettings")
    def reset_user_attribute_update_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserAttributeUpdateSettings", []))

    @jsii.member(jsii_name="resetUsernameAttributes")
    def reset_username_attributes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUsernameAttributes", []))

    @jsii.member(jsii_name="resetUsernameConfiguration")
    def reset_username_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUsernameConfiguration", []))

    @jsii.member(jsii_name="resetUserPoolAddOns")
    def reset_user_pool_add_ons(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserPoolAddOns", []))

    @jsii.member(jsii_name="resetUserPoolTier")
    def reset_user_pool_tier(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserPoolTier", []))

    @jsii.member(jsii_name="resetVerificationMessageTemplate")
    def reset_verification_message_template(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVerificationMessageTemplate", []))

    @jsii.member(jsii_name="resetWebAuthnConfiguration")
    def reset_web_authn_configuration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetWebAuthnConfiguration", []))

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
    @jsii.member(jsii_name="accountRecoverySetting")
    def account_recovery_setting(
        self,
    ) -> "CognitoUserPoolAccountRecoverySettingOutputReference":
        return typing.cast("CognitoUserPoolAccountRecoverySettingOutputReference", jsii.get(self, "accountRecoverySetting"))

    @builtins.property
    @jsii.member(jsii_name="adminCreateUserConfig")
    def admin_create_user_config(
        self,
    ) -> "CognitoUserPoolAdminCreateUserConfigOutputReference":
        return typing.cast("CognitoUserPoolAdminCreateUserConfigOutputReference", jsii.get(self, "adminCreateUserConfig"))

    @builtins.property
    @jsii.member(jsii_name="arn")
    def arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "arn"))

    @builtins.property
    @jsii.member(jsii_name="creationDate")
    def creation_date(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "creationDate"))

    @builtins.property
    @jsii.member(jsii_name="customDomain")
    def custom_domain(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customDomain"))

    @builtins.property
    @jsii.member(jsii_name="deviceConfiguration")
    def device_configuration(
        self,
    ) -> "CognitoUserPoolDeviceConfigurationOutputReference":
        return typing.cast("CognitoUserPoolDeviceConfigurationOutputReference", jsii.get(self, "deviceConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="domain")
    def domain(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "domain"))

    @builtins.property
    @jsii.member(jsii_name="emailConfiguration")
    def email_configuration(self) -> "CognitoUserPoolEmailConfigurationOutputReference":
        return typing.cast("CognitoUserPoolEmailConfigurationOutputReference", jsii.get(self, "emailConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="emailMfaConfiguration")
    def email_mfa_configuration(
        self,
    ) -> "CognitoUserPoolEmailMfaConfigurationOutputReference":
        return typing.cast("CognitoUserPoolEmailMfaConfigurationOutputReference", jsii.get(self, "emailMfaConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="endpoint")
    def endpoint(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "endpoint"))

    @builtins.property
    @jsii.member(jsii_name="estimatedNumberOfUsers")
    def estimated_number_of_users(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "estimatedNumberOfUsers"))

    @builtins.property
    @jsii.member(jsii_name="lambdaConfig")
    def lambda_config(self) -> "CognitoUserPoolLambdaConfigOutputReference":
        return typing.cast("CognitoUserPoolLambdaConfigOutputReference", jsii.get(self, "lambdaConfig"))

    @builtins.property
    @jsii.member(jsii_name="lastModifiedDate")
    def last_modified_date(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lastModifiedDate"))

    @builtins.property
    @jsii.member(jsii_name="passwordPolicy")
    def password_policy(self) -> "CognitoUserPoolPasswordPolicyOutputReference":
        return typing.cast("CognitoUserPoolPasswordPolicyOutputReference", jsii.get(self, "passwordPolicy"))

    @builtins.property
    @jsii.member(jsii_name="schema")
    def schema(self) -> "CognitoUserPoolSchemaList":
        return typing.cast("CognitoUserPoolSchemaList", jsii.get(self, "schema"))

    @builtins.property
    @jsii.member(jsii_name="signInPolicy")
    def sign_in_policy(self) -> "CognitoUserPoolSignInPolicyOutputReference":
        return typing.cast("CognitoUserPoolSignInPolicyOutputReference", jsii.get(self, "signInPolicy"))

    @builtins.property
    @jsii.member(jsii_name="smsConfiguration")
    def sms_configuration(self) -> "CognitoUserPoolSmsConfigurationOutputReference":
        return typing.cast("CognitoUserPoolSmsConfigurationOutputReference", jsii.get(self, "smsConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="softwareTokenMfaConfiguration")
    def software_token_mfa_configuration(
        self,
    ) -> "CognitoUserPoolSoftwareTokenMfaConfigurationOutputReference":
        return typing.cast("CognitoUserPoolSoftwareTokenMfaConfigurationOutputReference", jsii.get(self, "softwareTokenMfaConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="userAttributeUpdateSettings")
    def user_attribute_update_settings(
        self,
    ) -> "CognitoUserPoolUserAttributeUpdateSettingsOutputReference":
        return typing.cast("CognitoUserPoolUserAttributeUpdateSettingsOutputReference", jsii.get(self, "userAttributeUpdateSettings"))

    @builtins.property
    @jsii.member(jsii_name="usernameConfiguration")
    def username_configuration(
        self,
    ) -> "CognitoUserPoolUsernameConfigurationOutputReference":
        return typing.cast("CognitoUserPoolUsernameConfigurationOutputReference", jsii.get(self, "usernameConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="userPoolAddOns")
    def user_pool_add_ons(self) -> "CognitoUserPoolUserPoolAddOnsOutputReference":
        return typing.cast("CognitoUserPoolUserPoolAddOnsOutputReference", jsii.get(self, "userPoolAddOns"))

    @builtins.property
    @jsii.member(jsii_name="verificationMessageTemplate")
    def verification_message_template(
        self,
    ) -> "CognitoUserPoolVerificationMessageTemplateOutputReference":
        return typing.cast("CognitoUserPoolVerificationMessageTemplateOutputReference", jsii.get(self, "verificationMessageTemplate"))

    @builtins.property
    @jsii.member(jsii_name="webAuthnConfiguration")
    def web_authn_configuration(
        self,
    ) -> "CognitoUserPoolWebAuthnConfigurationOutputReference":
        return typing.cast("CognitoUserPoolWebAuthnConfigurationOutputReference", jsii.get(self, "webAuthnConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="accountRecoverySettingInput")
    def account_recovery_setting_input(
        self,
    ) -> typing.Optional["CognitoUserPoolAccountRecoverySetting"]:
        return typing.cast(typing.Optional["CognitoUserPoolAccountRecoverySetting"], jsii.get(self, "accountRecoverySettingInput"))

    @builtins.property
    @jsii.member(jsii_name="adminCreateUserConfigInput")
    def admin_create_user_config_input(
        self,
    ) -> typing.Optional["CognitoUserPoolAdminCreateUserConfig"]:
        return typing.cast(typing.Optional["CognitoUserPoolAdminCreateUserConfig"], jsii.get(self, "adminCreateUserConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="aliasAttributesInput")
    def alias_attributes_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "aliasAttributesInput"))

    @builtins.property
    @jsii.member(jsii_name="autoVerifiedAttributesInput")
    def auto_verified_attributes_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "autoVerifiedAttributesInput"))

    @builtins.property
    @jsii.member(jsii_name="deletionProtectionInput")
    def deletion_protection_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deletionProtectionInput"))

    @builtins.property
    @jsii.member(jsii_name="deviceConfigurationInput")
    def device_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolDeviceConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolDeviceConfiguration"], jsii.get(self, "deviceConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="emailConfigurationInput")
    def email_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolEmailConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolEmailConfiguration"], jsii.get(self, "emailConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="emailMfaConfigurationInput")
    def email_mfa_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolEmailMfaConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolEmailMfaConfiguration"], jsii.get(self, "emailMfaConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="emailVerificationMessageInput")
    def email_verification_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailVerificationMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="emailVerificationSubjectInput")
    def email_verification_subject_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailVerificationSubjectInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaConfigInput")
    def lambda_config_input(self) -> typing.Optional["CognitoUserPoolLambdaConfig"]:
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfig"], jsii.get(self, "lambdaConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="mfaConfigurationInput")
    def mfa_configuration_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "mfaConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="passwordPolicyInput")
    def password_policy_input(self) -> typing.Optional["CognitoUserPoolPasswordPolicy"]:
        return typing.cast(typing.Optional["CognitoUserPoolPasswordPolicy"], jsii.get(self, "passwordPolicyInput"))

    @builtins.property
    @jsii.member(jsii_name="regionInput")
    def region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "regionInput"))

    @builtins.property
    @jsii.member(jsii_name="schemaInput")
    def schema_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolSchema"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolSchema"]]], jsii.get(self, "schemaInput"))

    @builtins.property
    @jsii.member(jsii_name="signInPolicyInput")
    def sign_in_policy_input(self) -> typing.Optional["CognitoUserPoolSignInPolicy"]:
        return typing.cast(typing.Optional["CognitoUserPoolSignInPolicy"], jsii.get(self, "signInPolicyInput"))

    @builtins.property
    @jsii.member(jsii_name="smsAuthenticationMessageInput")
    def sms_authentication_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "smsAuthenticationMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="smsConfigurationInput")
    def sms_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolSmsConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolSmsConfiguration"], jsii.get(self, "smsConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="smsVerificationMessageInput")
    def sms_verification_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "smsVerificationMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="softwareTokenMfaConfigurationInput")
    def software_token_mfa_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolSoftwareTokenMfaConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolSoftwareTokenMfaConfiguration"], jsii.get(self, "softwareTokenMfaConfigurationInput"))

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
    @jsii.member(jsii_name="userAttributeUpdateSettingsInput")
    def user_attribute_update_settings_input(
        self,
    ) -> typing.Optional["CognitoUserPoolUserAttributeUpdateSettings"]:
        return typing.cast(typing.Optional["CognitoUserPoolUserAttributeUpdateSettings"], jsii.get(self, "userAttributeUpdateSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="usernameAttributesInput")
    def username_attributes_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "usernameAttributesInput"))

    @builtins.property
    @jsii.member(jsii_name="usernameConfigurationInput")
    def username_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolUsernameConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolUsernameConfiguration"], jsii.get(self, "usernameConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="userPoolAddOnsInput")
    def user_pool_add_ons_input(
        self,
    ) -> typing.Optional["CognitoUserPoolUserPoolAddOns"]:
        return typing.cast(typing.Optional["CognitoUserPoolUserPoolAddOns"], jsii.get(self, "userPoolAddOnsInput"))

    @builtins.property
    @jsii.member(jsii_name="userPoolTierInput")
    def user_pool_tier_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userPoolTierInput"))

    @builtins.property
    @jsii.member(jsii_name="verificationMessageTemplateInput")
    def verification_message_template_input(
        self,
    ) -> typing.Optional["CognitoUserPoolVerificationMessageTemplate"]:
        return typing.cast(typing.Optional["CognitoUserPoolVerificationMessageTemplate"], jsii.get(self, "verificationMessageTemplateInput"))

    @builtins.property
    @jsii.member(jsii_name="webAuthnConfigurationInput")
    def web_authn_configuration_input(
        self,
    ) -> typing.Optional["CognitoUserPoolWebAuthnConfiguration"]:
        return typing.cast(typing.Optional["CognitoUserPoolWebAuthnConfiguration"], jsii.get(self, "webAuthnConfigurationInput"))

    @builtins.property
    @jsii.member(jsii_name="aliasAttributes")
    def alias_attributes(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "aliasAttributes"))

    @alias_attributes.setter
    def alias_attributes(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5761158faf48575e28b76ced29481fc7995d21870c91d3675301eac7e62c93d3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "aliasAttributes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="autoVerifiedAttributes")
    def auto_verified_attributes(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "autoVerifiedAttributes"))

    @auto_verified_attributes.setter
    def auto_verified_attributes(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__812379b6ac56f8afbe78658f70d43d897d068bdaf5956b89851359ed8329b82c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "autoVerifiedAttributes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="deletionProtection")
    def deletion_protection(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "deletionProtection"))

    @deletion_protection.setter
    def deletion_protection(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04609a36de3026862a1ec7d5557f7e06442eafb1241df56da4c88e4ce0107f16)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deletionProtection", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailVerificationMessage")
    def email_verification_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailVerificationMessage"))

    @email_verification_message.setter
    def email_verification_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9cff28db1c5219a513496e9df5e900d9a7405cc558bf23d26e9312c67e25f14a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailVerificationMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailVerificationSubject")
    def email_verification_subject(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailVerificationSubject"))

    @email_verification_subject.setter
    def email_verification_subject(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b5e7496321573db876e51e7f5ccbb5f94397b052e2ab21b1805a76111ed5efd9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailVerificationSubject", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bb92134127d67495aae809ad29ee96723ae307bed2c8f8ca0348a2c90eb1754b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mfaConfiguration")
    def mfa_configuration(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "mfaConfiguration"))

    @mfa_configuration.setter
    def mfa_configuration(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__88427b200ad90bec3f0546096e59abae3c4df05d3645c938f852b727efcc2147)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mfaConfiguration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__358eee877ebe44397e7b2c50717c9bc5c5beb08aeab1de739703605a37bdb67d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @region.setter
    def region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec237e81a8820b85ba45473f5c871f4d1021331faaf66af0dd56f23e320669ba)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "region", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="smsAuthenticationMessage")
    def sms_authentication_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "smsAuthenticationMessage"))

    @sms_authentication_message.setter
    def sms_authentication_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7b18415ebe9fd02c9d3f2b65769ab8dd6f29b2d7398c51b1e88b400b3c9e4834)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "smsAuthenticationMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="smsVerificationMessage")
    def sms_verification_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "smsVerificationMessage"))

    @sms_verification_message.setter
    def sms_verification_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__521276d5268b6b2fe5ab1f221633d818acd5af228af69dc014c64ed004417da3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "smsVerificationMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1fea4288ef68c5d7b6475308f2cd89f9e65793b74bbb9620edd2f21d20c510da)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tagsAll")
    def tags_all(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tagsAll"))

    @tags_all.setter
    def tags_all(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__592e398830927c091a21273c9aabd962496de4284ce3b1d3fd6b4ea0c6f38290)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tagsAll", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="usernameAttributes")
    def username_attributes(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "usernameAttributes"))

    @username_attributes.setter
    def username_attributes(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17a1ef1384bd83a0de8b95c3cf2a233a611fa51a3fecf1ef7d6890e7dbbc4c7f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "usernameAttributes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userPoolTier")
    def user_pool_tier(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userPoolTier"))

    @user_pool_tier.setter
    def user_pool_tier(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__139b1f8abdf690aa2fce25679c7293c50b77891a877b76204737b91f9aada0f6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userPoolTier", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAccountRecoverySetting",
    jsii_struct_bases=[],
    name_mapping={"recovery_mechanism": "recoveryMechanism"},
)
class CognitoUserPoolAccountRecoverySetting:
    def __init__(
        self,
        *,
        recovery_mechanism: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolAccountRecoverySettingRecoveryMechanism", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param recovery_mechanism: recovery_mechanism block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#recovery_mechanism CognitoUserPool#recovery_mechanism}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__01d316b6cc0ef169f2fbb7c8a1ee57daa6fe8a64b3e77000917e9166f1c2664c)
            check_type(argname="argument recovery_mechanism", value=recovery_mechanism, expected_type=type_hints["recovery_mechanism"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if recovery_mechanism is not None:
            self._values["recovery_mechanism"] = recovery_mechanism

    @builtins.property
    def recovery_mechanism(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolAccountRecoverySettingRecoveryMechanism"]]]:
        '''recovery_mechanism block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#recovery_mechanism CognitoUserPool#recovery_mechanism}
        '''
        result = self._values.get("recovery_mechanism")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolAccountRecoverySettingRecoveryMechanism"]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolAccountRecoverySetting(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolAccountRecoverySettingOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAccountRecoverySettingOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__95c0f18485affdb8d77c449f2bb65e40cce486fcbbb20681592d418ab3775a80)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putRecoveryMechanism")
    def put_recovery_mechanism(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolAccountRecoverySettingRecoveryMechanism", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6b6e8dd7574be4a488925c472bc36e33aeb7291c4d1443bc5e7ab6ba5601a7a5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putRecoveryMechanism", [value]))

    @jsii.member(jsii_name="resetRecoveryMechanism")
    def reset_recovery_mechanism(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRecoveryMechanism", []))

    @builtins.property
    @jsii.member(jsii_name="recoveryMechanism")
    def recovery_mechanism(
        self,
    ) -> "CognitoUserPoolAccountRecoverySettingRecoveryMechanismList":
        return typing.cast("CognitoUserPoolAccountRecoverySettingRecoveryMechanismList", jsii.get(self, "recoveryMechanism"))

    @builtins.property
    @jsii.member(jsii_name="recoveryMechanismInput")
    def recovery_mechanism_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolAccountRecoverySettingRecoveryMechanism"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolAccountRecoverySettingRecoveryMechanism"]]], jsii.get(self, "recoveryMechanismInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolAccountRecoverySetting]:
        return typing.cast(typing.Optional[CognitoUserPoolAccountRecoverySetting], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolAccountRecoverySetting],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b0493289df5643906f8281fc5bafa23b5e688b9b03fcbc85d64af7d8616bac1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAccountRecoverySettingRecoveryMechanism",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "priority": "priority"},
)
class CognitoUserPoolAccountRecoverySettingRecoveryMechanism:
    def __init__(self, *, name: builtins.str, priority: jsii.Number) -> None:
        '''
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.
        :param priority: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#priority CognitoUserPool#priority}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__06b536da76a1bdf3fe49c8e531d5cd2c1e1116015d7b5f07173f8663e613ee49)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "priority": priority,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def priority(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#priority CognitoUserPool#priority}.'''
        result = self._values.get("priority")
        assert result is not None, "Required property 'priority' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolAccountRecoverySettingRecoveryMechanism(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolAccountRecoverySettingRecoveryMechanismList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAccountRecoverySettingRecoveryMechanismList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__5a0d4ff5e7917b4cbc435960968bf4353c142b5d8f9cf02e9b8aaf2ca9d1318b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "CognitoUserPoolAccountRecoverySettingRecoveryMechanismOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54b5d9d424b4a821aa4e425d3d59b0504a2b35136f64010c613357ce2ed91f38)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("CognitoUserPoolAccountRecoverySettingRecoveryMechanismOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7128bd667a6a4414db0c3db02de635878aa88d93da5ac1dcf551112289c635a1)
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
            type_hints = typing.get_type_hints(_typecheckingstub__f026757f40dd87c0e52beb91c3a1937768d633130970668a96399362a9e8089a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__95a149622ba53a95a973b92d1ec238e20afc7f427c513033f00bb76cdf63256a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolAccountRecoverySettingRecoveryMechanism]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolAccountRecoverySettingRecoveryMechanism]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolAccountRecoverySettingRecoveryMechanism]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a902a3a4252bad61489c416f3bf79c662e0b64d5476b0dd1116d16ff627c7737)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class CognitoUserPoolAccountRecoverySettingRecoveryMechanismOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAccountRecoverySettingRecoveryMechanismOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a664771da8e1028822db16625f6edaeaf3d523a275af50b0377227eb8740096e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="priorityInput")
    def priority_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "priorityInput"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a50aab5f5dd2bf66bdb28242bcd63e61681390fdd0e64deb34728b414d12fc6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="priority")
    def priority(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "priority"))

    @priority.setter
    def priority(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__75a0aa44e7bf8b7b84c28e36e1f4eb9406b958ea588480a86e00c04743464cba)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "priority", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolAccountRecoverySettingRecoveryMechanism]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolAccountRecoverySettingRecoveryMechanism]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolAccountRecoverySettingRecoveryMechanism]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__15d4f37fe6c6f39cd9dc816affd7510d7c8e3162b9bfa5cccd9db9a94e8aa0ce)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAdminCreateUserConfig",
    jsii_struct_bases=[],
    name_mapping={
        "allow_admin_create_user_only": "allowAdminCreateUserOnly",
        "invite_message_template": "inviteMessageTemplate",
    },
)
class CognitoUserPoolAdminCreateUserConfig:
    def __init__(
        self,
        *,
        allow_admin_create_user_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        invite_message_template: typing.Optional[typing.Union["CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param allow_admin_create_user_only: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allow_admin_create_user_only CognitoUserPool#allow_admin_create_user_only}.
        :param invite_message_template: invite_message_template block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#invite_message_template CognitoUserPool#invite_message_template}
        '''
        if isinstance(invite_message_template, dict):
            invite_message_template = CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate(**invite_message_template)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f1c43b01a94e36046f210602b39032377befeeb35319139a902fea6aef7e374)
            check_type(argname="argument allow_admin_create_user_only", value=allow_admin_create_user_only, expected_type=type_hints["allow_admin_create_user_only"])
            check_type(argname="argument invite_message_template", value=invite_message_template, expected_type=type_hints["invite_message_template"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allow_admin_create_user_only is not None:
            self._values["allow_admin_create_user_only"] = allow_admin_create_user_only
        if invite_message_template is not None:
            self._values["invite_message_template"] = invite_message_template

    @builtins.property
    def allow_admin_create_user_only(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allow_admin_create_user_only CognitoUserPool#allow_admin_create_user_only}.'''
        result = self._values.get("allow_admin_create_user_only")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def invite_message_template(
        self,
    ) -> typing.Optional["CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate"]:
        '''invite_message_template block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#invite_message_template CognitoUserPool#invite_message_template}
        '''
        result = self._values.get("invite_message_template")
        return typing.cast(typing.Optional["CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolAdminCreateUserConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate",
    jsii_struct_bases=[],
    name_mapping={
        "email_message": "emailMessage",
        "email_subject": "emailSubject",
        "sms_message": "smsMessage",
    },
)
class CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate:
    def __init__(
        self,
        *,
        email_message: typing.Optional[builtins.str] = None,
        email_subject: typing.Optional[builtins.str] = None,
        sms_message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param email_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.
        :param email_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.
        :param sms_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__faccb36c29a7922678da7fc15b24d561753eedb0d21bb7b69a4d0fcd30f72cff)
            check_type(argname="argument email_message", value=email_message, expected_type=type_hints["email_message"])
            check_type(argname="argument email_subject", value=email_subject, expected_type=type_hints["email_subject"])
            check_type(argname="argument sms_message", value=sms_message, expected_type=type_hints["sms_message"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if email_message is not None:
            self._values["email_message"] = email_message
        if email_subject is not None:
            self._values["email_subject"] = email_subject
        if sms_message is not None:
            self._values["sms_message"] = sms_message

    @builtins.property
    def email_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.'''
        result = self._values.get("email_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_subject(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.'''
        result = self._values.get("email_subject")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sms_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.'''
        result = self._values.get("sms_message")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolAdminCreateUserConfigInviteMessageTemplateOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAdminCreateUserConfigInviteMessageTemplateOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__9fb7e398445292a8e32b1838bab38fc0510b79da4ed94f452b4367ff38493cb8)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetEmailMessage")
    def reset_email_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailMessage", []))

    @jsii.member(jsii_name="resetEmailSubject")
    def reset_email_subject(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailSubject", []))

    @jsii.member(jsii_name="resetSmsMessage")
    def reset_sms_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSmsMessage", []))

    @builtins.property
    @jsii.member(jsii_name="emailMessageInput")
    def email_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="emailSubjectInput")
    def email_subject_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailSubjectInput"))

    @builtins.property
    @jsii.member(jsii_name="smsMessageInput")
    def sms_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "smsMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="emailMessage")
    def email_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailMessage"))

    @email_message.setter
    def email_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eab063466194b9d8703150ecdd79c7cf5a86503e9fb13f50cefead8ea698885c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailSubject")
    def email_subject(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailSubject"))

    @email_subject.setter
    def email_subject(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__081f45676b3efdc9eee3e41e3157a70b644ba58eeb0356b1a702babbe459c333)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailSubject", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="smsMessage")
    def sms_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "smsMessage"))

    @sms_message.setter
    def sms_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__999b4ed36ccfddf5ecce0787d9ca354544702db8e510d66cf6ce90094d488ec9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "smsMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate]:
        return typing.cast(typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dac387f3b27627a9283473866225cf17e502b8f92d88a5f52229cb2b78748aec)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class CognitoUserPoolAdminCreateUserConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolAdminCreateUserConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__75efe294c70cf57e39b12f0e41241d800d36a954ca5089eb761588d8b2f1dcaf)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putInviteMessageTemplate")
    def put_invite_message_template(
        self,
        *,
        email_message: typing.Optional[builtins.str] = None,
        email_subject: typing.Optional[builtins.str] = None,
        sms_message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param email_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.
        :param email_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.
        :param sms_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.
        '''
        value = CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate(
            email_message=email_message,
            email_subject=email_subject,
            sms_message=sms_message,
        )

        return typing.cast(None, jsii.invoke(self, "putInviteMessageTemplate", [value]))

    @jsii.member(jsii_name="resetAllowAdminCreateUserOnly")
    def reset_allow_admin_create_user_only(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAllowAdminCreateUserOnly", []))

    @jsii.member(jsii_name="resetInviteMessageTemplate")
    def reset_invite_message_template(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetInviteMessageTemplate", []))

    @builtins.property
    @jsii.member(jsii_name="inviteMessageTemplate")
    def invite_message_template(
        self,
    ) -> CognitoUserPoolAdminCreateUserConfigInviteMessageTemplateOutputReference:
        return typing.cast(CognitoUserPoolAdminCreateUserConfigInviteMessageTemplateOutputReference, jsii.get(self, "inviteMessageTemplate"))

    @builtins.property
    @jsii.member(jsii_name="allowAdminCreateUserOnlyInput")
    def allow_admin_create_user_only_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "allowAdminCreateUserOnlyInput"))

    @builtins.property
    @jsii.member(jsii_name="inviteMessageTemplateInput")
    def invite_message_template_input(
        self,
    ) -> typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate]:
        return typing.cast(typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate], jsii.get(self, "inviteMessageTemplateInput"))

    @builtins.property
    @jsii.member(jsii_name="allowAdminCreateUserOnly")
    def allow_admin_create_user_only(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "allowAdminCreateUserOnly"))

    @allow_admin_create_user_only.setter
    def allow_admin_create_user_only(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8763ec7278e3c89370e152982b89839d49a1f8e05f5fcaa0cf2eb732c934b89d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "allowAdminCreateUserOnly", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolAdminCreateUserConfig]:
        return typing.cast(typing.Optional[CognitoUserPoolAdminCreateUserConfig], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolAdminCreateUserConfig],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c6f43ca06e29cd4d2c8ccfc0eb3437312c6c0a8ded2e40b7b2235b2bea0d4584)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolConfig",
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
        "account_recovery_setting": "accountRecoverySetting",
        "admin_create_user_config": "adminCreateUserConfig",
        "alias_attributes": "aliasAttributes",
        "auto_verified_attributes": "autoVerifiedAttributes",
        "deletion_protection": "deletionProtection",
        "device_configuration": "deviceConfiguration",
        "email_configuration": "emailConfiguration",
        "email_mfa_configuration": "emailMfaConfiguration",
        "email_verification_message": "emailVerificationMessage",
        "email_verification_subject": "emailVerificationSubject",
        "id": "id",
        "lambda_config": "lambdaConfig",
        "mfa_configuration": "mfaConfiguration",
        "password_policy": "passwordPolicy",
        "region": "region",
        "schema": "schema",
        "sign_in_policy": "signInPolicy",
        "sms_authentication_message": "smsAuthenticationMessage",
        "sms_configuration": "smsConfiguration",
        "sms_verification_message": "smsVerificationMessage",
        "software_token_mfa_configuration": "softwareTokenMfaConfiguration",
        "tags": "tags",
        "tags_all": "tagsAll",
        "user_attribute_update_settings": "userAttributeUpdateSettings",
        "username_attributes": "usernameAttributes",
        "username_configuration": "usernameConfiguration",
        "user_pool_add_ons": "userPoolAddOns",
        "user_pool_tier": "userPoolTier",
        "verification_message_template": "verificationMessageTemplate",
        "web_authn_configuration": "webAuthnConfiguration",
    },
)
class CognitoUserPoolConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        account_recovery_setting: typing.Optional[typing.Union[CognitoUserPoolAccountRecoverySetting, typing.Dict[builtins.str, typing.Any]]] = None,
        admin_create_user_config: typing.Optional[typing.Union[CognitoUserPoolAdminCreateUserConfig, typing.Dict[builtins.str, typing.Any]]] = None,
        alias_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        auto_verified_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        deletion_protection: typing.Optional[builtins.str] = None,
        device_configuration: typing.Optional[typing.Union["CognitoUserPoolDeviceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_configuration: typing.Optional[typing.Union["CognitoUserPoolEmailConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_mfa_configuration: typing.Optional[typing.Union["CognitoUserPoolEmailMfaConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        email_verification_message: typing.Optional[builtins.str] = None,
        email_verification_subject: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        lambda_config: typing.Optional[typing.Union["CognitoUserPoolLambdaConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        mfa_configuration: typing.Optional[builtins.str] = None,
        password_policy: typing.Optional[typing.Union["CognitoUserPoolPasswordPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        region: typing.Optional[builtins.str] = None,
        schema: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["CognitoUserPoolSchema", typing.Dict[builtins.str, typing.Any]]]]] = None,
        sign_in_policy: typing.Optional[typing.Union["CognitoUserPoolSignInPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        sms_authentication_message: typing.Optional[builtins.str] = None,
        sms_configuration: typing.Optional[typing.Union["CognitoUserPoolSmsConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        sms_verification_message: typing.Optional[builtins.str] = None,
        software_token_mfa_configuration: typing.Optional[typing.Union["CognitoUserPoolSoftwareTokenMfaConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        user_attribute_update_settings: typing.Optional[typing.Union["CognitoUserPoolUserAttributeUpdateSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        username_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
        username_configuration: typing.Optional[typing.Union["CognitoUserPoolUsernameConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        user_pool_add_ons: typing.Optional[typing.Union["CognitoUserPoolUserPoolAddOns", typing.Dict[builtins.str, typing.Any]]] = None,
        user_pool_tier: typing.Optional[builtins.str] = None,
        verification_message_template: typing.Optional[typing.Union["CognitoUserPoolVerificationMessageTemplate", typing.Dict[builtins.str, typing.Any]]] = None,
        web_authn_configuration: typing.Optional[typing.Union["CognitoUserPoolWebAuthnConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.
        :param account_recovery_setting: account_recovery_setting block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#account_recovery_setting CognitoUserPool#account_recovery_setting}
        :param admin_create_user_config: admin_create_user_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#admin_create_user_config CognitoUserPool#admin_create_user_config}
        :param alias_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#alias_attributes CognitoUserPool#alias_attributes}.
        :param auto_verified_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#auto_verified_attributes CognitoUserPool#auto_verified_attributes}.
        :param deletion_protection: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#deletion_protection CognitoUserPool#deletion_protection}.
        :param device_configuration: device_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_configuration CognitoUserPool#device_configuration}
        :param email_configuration: email_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_configuration CognitoUserPool#email_configuration}
        :param email_mfa_configuration: email_mfa_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_mfa_configuration CognitoUserPool#email_mfa_configuration}
        :param email_verification_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_message CognitoUserPool#email_verification_message}.
        :param email_verification_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_subject CognitoUserPool#email_verification_subject}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#id CognitoUserPool#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param lambda_config: lambda_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_config CognitoUserPool#lambda_config}
        :param mfa_configuration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#mfa_configuration CognitoUserPool#mfa_configuration}.
        :param password_policy: password_policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_policy CognitoUserPool#password_policy}
        :param region: Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#region CognitoUserPool#region}
        :param schema: schema block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#schema CognitoUserPool#schema}
        :param sign_in_policy: sign_in_policy block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sign_in_policy CognitoUserPool#sign_in_policy}
        :param sms_authentication_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_authentication_message CognitoUserPool#sms_authentication_message}.
        :param sms_configuration: sms_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_configuration CognitoUserPool#sms_configuration}
        :param sms_verification_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_verification_message CognitoUserPool#sms_verification_message}.
        :param software_token_mfa_configuration: software_token_mfa_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#software_token_mfa_configuration CognitoUserPool#software_token_mfa_configuration}
        :param tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags CognitoUserPool#tags}.
        :param tags_all: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags_all CognitoUserPool#tags_all}.
        :param user_attribute_update_settings: user_attribute_update_settings block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_attribute_update_settings CognitoUserPool#user_attribute_update_settings}
        :param username_attributes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_attributes CognitoUserPool#username_attributes}.
        :param username_configuration: username_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_configuration CognitoUserPool#username_configuration}
        :param user_pool_add_ons: user_pool_add_ons block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_add_ons CognitoUserPool#user_pool_add_ons}
        :param user_pool_tier: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_tier CognitoUserPool#user_pool_tier}.
        :param verification_message_template: verification_message_template block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verification_message_template CognitoUserPool#verification_message_template}
        :param web_authn_configuration: web_authn_configuration block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#web_authn_configuration CognitoUserPool#web_authn_configuration}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(account_recovery_setting, dict):
            account_recovery_setting = CognitoUserPoolAccountRecoverySetting(**account_recovery_setting)
        if isinstance(admin_create_user_config, dict):
            admin_create_user_config = CognitoUserPoolAdminCreateUserConfig(**admin_create_user_config)
        if isinstance(device_configuration, dict):
            device_configuration = CognitoUserPoolDeviceConfiguration(**device_configuration)
        if isinstance(email_configuration, dict):
            email_configuration = CognitoUserPoolEmailConfiguration(**email_configuration)
        if isinstance(email_mfa_configuration, dict):
            email_mfa_configuration = CognitoUserPoolEmailMfaConfiguration(**email_mfa_configuration)
        if isinstance(lambda_config, dict):
            lambda_config = CognitoUserPoolLambdaConfig(**lambda_config)
        if isinstance(password_policy, dict):
            password_policy = CognitoUserPoolPasswordPolicy(**password_policy)
        if isinstance(sign_in_policy, dict):
            sign_in_policy = CognitoUserPoolSignInPolicy(**sign_in_policy)
        if isinstance(sms_configuration, dict):
            sms_configuration = CognitoUserPoolSmsConfiguration(**sms_configuration)
        if isinstance(software_token_mfa_configuration, dict):
            software_token_mfa_configuration = CognitoUserPoolSoftwareTokenMfaConfiguration(**software_token_mfa_configuration)
        if isinstance(user_attribute_update_settings, dict):
            user_attribute_update_settings = CognitoUserPoolUserAttributeUpdateSettings(**user_attribute_update_settings)
        if isinstance(username_configuration, dict):
            username_configuration = CognitoUserPoolUsernameConfiguration(**username_configuration)
        if isinstance(user_pool_add_ons, dict):
            user_pool_add_ons = CognitoUserPoolUserPoolAddOns(**user_pool_add_ons)
        if isinstance(verification_message_template, dict):
            verification_message_template = CognitoUserPoolVerificationMessageTemplate(**verification_message_template)
        if isinstance(web_authn_configuration, dict):
            web_authn_configuration = CognitoUserPoolWebAuthnConfiguration(**web_authn_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94bb316ae165be77901cf0a4fa060ea14afbce11881d59a4cd529d610caf01e1)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument account_recovery_setting", value=account_recovery_setting, expected_type=type_hints["account_recovery_setting"])
            check_type(argname="argument admin_create_user_config", value=admin_create_user_config, expected_type=type_hints["admin_create_user_config"])
            check_type(argname="argument alias_attributes", value=alias_attributes, expected_type=type_hints["alias_attributes"])
            check_type(argname="argument auto_verified_attributes", value=auto_verified_attributes, expected_type=type_hints["auto_verified_attributes"])
            check_type(argname="argument deletion_protection", value=deletion_protection, expected_type=type_hints["deletion_protection"])
            check_type(argname="argument device_configuration", value=device_configuration, expected_type=type_hints["device_configuration"])
            check_type(argname="argument email_configuration", value=email_configuration, expected_type=type_hints["email_configuration"])
            check_type(argname="argument email_mfa_configuration", value=email_mfa_configuration, expected_type=type_hints["email_mfa_configuration"])
            check_type(argname="argument email_verification_message", value=email_verification_message, expected_type=type_hints["email_verification_message"])
            check_type(argname="argument email_verification_subject", value=email_verification_subject, expected_type=type_hints["email_verification_subject"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument lambda_config", value=lambda_config, expected_type=type_hints["lambda_config"])
            check_type(argname="argument mfa_configuration", value=mfa_configuration, expected_type=type_hints["mfa_configuration"])
            check_type(argname="argument password_policy", value=password_policy, expected_type=type_hints["password_policy"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument schema", value=schema, expected_type=type_hints["schema"])
            check_type(argname="argument sign_in_policy", value=sign_in_policy, expected_type=type_hints["sign_in_policy"])
            check_type(argname="argument sms_authentication_message", value=sms_authentication_message, expected_type=type_hints["sms_authentication_message"])
            check_type(argname="argument sms_configuration", value=sms_configuration, expected_type=type_hints["sms_configuration"])
            check_type(argname="argument sms_verification_message", value=sms_verification_message, expected_type=type_hints["sms_verification_message"])
            check_type(argname="argument software_token_mfa_configuration", value=software_token_mfa_configuration, expected_type=type_hints["software_token_mfa_configuration"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument tags_all", value=tags_all, expected_type=type_hints["tags_all"])
            check_type(argname="argument user_attribute_update_settings", value=user_attribute_update_settings, expected_type=type_hints["user_attribute_update_settings"])
            check_type(argname="argument username_attributes", value=username_attributes, expected_type=type_hints["username_attributes"])
            check_type(argname="argument username_configuration", value=username_configuration, expected_type=type_hints["username_configuration"])
            check_type(argname="argument user_pool_add_ons", value=user_pool_add_ons, expected_type=type_hints["user_pool_add_ons"])
            check_type(argname="argument user_pool_tier", value=user_pool_tier, expected_type=type_hints["user_pool_tier"])
            check_type(argname="argument verification_message_template", value=verification_message_template, expected_type=type_hints["verification_message_template"])
            check_type(argname="argument web_authn_configuration", value=web_authn_configuration, expected_type=type_hints["web_authn_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
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
        if account_recovery_setting is not None:
            self._values["account_recovery_setting"] = account_recovery_setting
        if admin_create_user_config is not None:
            self._values["admin_create_user_config"] = admin_create_user_config
        if alias_attributes is not None:
            self._values["alias_attributes"] = alias_attributes
        if auto_verified_attributes is not None:
            self._values["auto_verified_attributes"] = auto_verified_attributes
        if deletion_protection is not None:
            self._values["deletion_protection"] = deletion_protection
        if device_configuration is not None:
            self._values["device_configuration"] = device_configuration
        if email_configuration is not None:
            self._values["email_configuration"] = email_configuration
        if email_mfa_configuration is not None:
            self._values["email_mfa_configuration"] = email_mfa_configuration
        if email_verification_message is not None:
            self._values["email_verification_message"] = email_verification_message
        if email_verification_subject is not None:
            self._values["email_verification_subject"] = email_verification_subject
        if id is not None:
            self._values["id"] = id
        if lambda_config is not None:
            self._values["lambda_config"] = lambda_config
        if mfa_configuration is not None:
            self._values["mfa_configuration"] = mfa_configuration
        if password_policy is not None:
            self._values["password_policy"] = password_policy
        if region is not None:
            self._values["region"] = region
        if schema is not None:
            self._values["schema"] = schema
        if sign_in_policy is not None:
            self._values["sign_in_policy"] = sign_in_policy
        if sms_authentication_message is not None:
            self._values["sms_authentication_message"] = sms_authentication_message
        if sms_configuration is not None:
            self._values["sms_configuration"] = sms_configuration
        if sms_verification_message is not None:
            self._values["sms_verification_message"] = sms_verification_message
        if software_token_mfa_configuration is not None:
            self._values["software_token_mfa_configuration"] = software_token_mfa_configuration
        if tags is not None:
            self._values["tags"] = tags
        if tags_all is not None:
            self._values["tags_all"] = tags_all
        if user_attribute_update_settings is not None:
            self._values["user_attribute_update_settings"] = user_attribute_update_settings
        if username_attributes is not None:
            self._values["username_attributes"] = username_attributes
        if username_configuration is not None:
            self._values["username_configuration"] = username_configuration
        if user_pool_add_ons is not None:
            self._values["user_pool_add_ons"] = user_pool_add_ons
        if user_pool_tier is not None:
            self._values["user_pool_tier"] = user_pool_tier
        if verification_message_template is not None:
            self._values["verification_message_template"] = verification_message_template
        if web_authn_configuration is not None:
            self._values["web_authn_configuration"] = web_authn_configuration

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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def account_recovery_setting(
        self,
    ) -> typing.Optional[CognitoUserPoolAccountRecoverySetting]:
        '''account_recovery_setting block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#account_recovery_setting CognitoUserPool#account_recovery_setting}
        '''
        result = self._values.get("account_recovery_setting")
        return typing.cast(typing.Optional[CognitoUserPoolAccountRecoverySetting], result)

    @builtins.property
    def admin_create_user_config(
        self,
    ) -> typing.Optional[CognitoUserPoolAdminCreateUserConfig]:
        '''admin_create_user_config block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#admin_create_user_config CognitoUserPool#admin_create_user_config}
        '''
        result = self._values.get("admin_create_user_config")
        return typing.cast(typing.Optional[CognitoUserPoolAdminCreateUserConfig], result)

    @builtins.property
    def alias_attributes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#alias_attributes CognitoUserPool#alias_attributes}.'''
        result = self._values.get("alias_attributes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def auto_verified_attributes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#auto_verified_attributes CognitoUserPool#auto_verified_attributes}.'''
        result = self._values.get("auto_verified_attributes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def deletion_protection(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#deletion_protection CognitoUserPool#deletion_protection}.'''
        result = self._values.get("deletion_protection")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def device_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolDeviceConfiguration"]:
        '''device_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_configuration CognitoUserPool#device_configuration}
        '''
        result = self._values.get("device_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolDeviceConfiguration"], result)

    @builtins.property
    def email_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolEmailConfiguration"]:
        '''email_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_configuration CognitoUserPool#email_configuration}
        '''
        result = self._values.get("email_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolEmailConfiguration"], result)

    @builtins.property
    def email_mfa_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolEmailMfaConfiguration"]:
        '''email_mfa_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_mfa_configuration CognitoUserPool#email_mfa_configuration}
        '''
        result = self._values.get("email_mfa_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolEmailMfaConfiguration"], result)

    @builtins.property
    def email_verification_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_message CognitoUserPool#email_verification_message}.'''
        result = self._values.get("email_verification_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_verification_subject(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_verification_subject CognitoUserPool#email_verification_subject}.'''
        result = self._values.get("email_verification_subject")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#id CognitoUserPool#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def lambda_config(self) -> typing.Optional["CognitoUserPoolLambdaConfig"]:
        '''lambda_config block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_config CognitoUserPool#lambda_config}
        '''
        result = self._values.get("lambda_config")
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfig"], result)

    @builtins.property
    def mfa_configuration(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#mfa_configuration CognitoUserPool#mfa_configuration}.'''
        result = self._values.get("mfa_configuration")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def password_policy(self) -> typing.Optional["CognitoUserPoolPasswordPolicy"]:
        '''password_policy block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_policy CognitoUserPool#password_policy}
        '''
        result = self._values.get("password_policy")
        return typing.cast(typing.Optional["CognitoUserPoolPasswordPolicy"], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''Region where this resource will be `managed <https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints>`_. Defaults to the Region set in the `provider configuration <https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#region CognitoUserPool#region}
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolSchema"]]]:
        '''schema block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#schema CognitoUserPool#schema}
        '''
        result = self._values.get("schema")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["CognitoUserPoolSchema"]]], result)

    @builtins.property
    def sign_in_policy(self) -> typing.Optional["CognitoUserPoolSignInPolicy"]:
        '''sign_in_policy block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sign_in_policy CognitoUserPool#sign_in_policy}
        '''
        result = self._values.get("sign_in_policy")
        return typing.cast(typing.Optional["CognitoUserPoolSignInPolicy"], result)

    @builtins.property
    def sms_authentication_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_authentication_message CognitoUserPool#sms_authentication_message}.'''
        result = self._values.get("sms_authentication_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sms_configuration(self) -> typing.Optional["CognitoUserPoolSmsConfiguration"]:
        '''sms_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_configuration CognitoUserPool#sms_configuration}
        '''
        result = self._values.get("sms_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolSmsConfiguration"], result)

    @builtins.property
    def sms_verification_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_verification_message CognitoUserPool#sms_verification_message}.'''
        result = self._values.get("sms_verification_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def software_token_mfa_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolSoftwareTokenMfaConfiguration"]:
        '''software_token_mfa_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#software_token_mfa_configuration CognitoUserPool#software_token_mfa_configuration}
        '''
        result = self._values.get("software_token_mfa_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolSoftwareTokenMfaConfiguration"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags CognitoUserPool#tags}.'''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def tags_all(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#tags_all CognitoUserPool#tags_all}.'''
        result = self._values.get("tags_all")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def user_attribute_update_settings(
        self,
    ) -> typing.Optional["CognitoUserPoolUserAttributeUpdateSettings"]:
        '''user_attribute_update_settings block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_attribute_update_settings CognitoUserPool#user_attribute_update_settings}
        '''
        result = self._values.get("user_attribute_update_settings")
        return typing.cast(typing.Optional["CognitoUserPoolUserAttributeUpdateSettings"], result)

    @builtins.property
    def username_attributes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_attributes CognitoUserPool#username_attributes}.'''
        result = self._values.get("username_attributes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def username_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolUsernameConfiguration"]:
        '''username_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#username_configuration CognitoUserPool#username_configuration}
        '''
        result = self._values.get("username_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolUsernameConfiguration"], result)

    @builtins.property
    def user_pool_add_ons(self) -> typing.Optional["CognitoUserPoolUserPoolAddOns"]:
        '''user_pool_add_ons block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_add_ons CognitoUserPool#user_pool_add_ons}
        '''
        result = self._values.get("user_pool_add_ons")
        return typing.cast(typing.Optional["CognitoUserPoolUserPoolAddOns"], result)

    @builtins.property
    def user_pool_tier(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_pool_tier CognitoUserPool#user_pool_tier}.'''
        result = self._values.get("user_pool_tier")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def verification_message_template(
        self,
    ) -> typing.Optional["CognitoUserPoolVerificationMessageTemplate"]:
        '''verification_message_template block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verification_message_template CognitoUserPool#verification_message_template}
        '''
        result = self._values.get("verification_message_template")
        return typing.cast(typing.Optional["CognitoUserPoolVerificationMessageTemplate"], result)

    @builtins.property
    def web_authn_configuration(
        self,
    ) -> typing.Optional["CognitoUserPoolWebAuthnConfiguration"]:
        '''web_authn_configuration block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#web_authn_configuration CognitoUserPool#web_authn_configuration}
        '''
        result = self._values.get("web_authn_configuration")
        return typing.cast(typing.Optional["CognitoUserPoolWebAuthnConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolDeviceConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "challenge_required_on_new_device": "challengeRequiredOnNewDevice",
        "device_only_remembered_on_user_prompt": "deviceOnlyRememberedOnUserPrompt",
    },
)
class CognitoUserPoolDeviceConfiguration:
    def __init__(
        self,
        *,
        challenge_required_on_new_device: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        device_only_remembered_on_user_prompt: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param challenge_required_on_new_device: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#challenge_required_on_new_device CognitoUserPool#challenge_required_on_new_device}.
        :param device_only_remembered_on_user_prompt: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_only_remembered_on_user_prompt CognitoUserPool#device_only_remembered_on_user_prompt}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6deb8e1117374362615ebc0a7b7f84fa98a0421f452923c0ed2dce4e1f8fedcd)
            check_type(argname="argument challenge_required_on_new_device", value=challenge_required_on_new_device, expected_type=type_hints["challenge_required_on_new_device"])
            check_type(argname="argument device_only_remembered_on_user_prompt", value=device_only_remembered_on_user_prompt, expected_type=type_hints["device_only_remembered_on_user_prompt"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if challenge_required_on_new_device is not None:
            self._values["challenge_required_on_new_device"] = challenge_required_on_new_device
        if device_only_remembered_on_user_prompt is not None:
            self._values["device_only_remembered_on_user_prompt"] = device_only_remembered_on_user_prompt

    @builtins.property
    def challenge_required_on_new_device(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#challenge_required_on_new_device CognitoUserPool#challenge_required_on_new_device}.'''
        result = self._values.get("challenge_required_on_new_device")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def device_only_remembered_on_user_prompt(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#device_only_remembered_on_user_prompt CognitoUserPool#device_only_remembered_on_user_prompt}.'''
        result = self._values.get("device_only_remembered_on_user_prompt")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolDeviceConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolDeviceConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolDeviceConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__0041979c2a1b82b3ec1e6d7cd14f83882bd83af0eee20a3b00f2564aa4c70079)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetChallengeRequiredOnNewDevice")
    def reset_challenge_required_on_new_device(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetChallengeRequiredOnNewDevice", []))

    @jsii.member(jsii_name="resetDeviceOnlyRememberedOnUserPrompt")
    def reset_device_only_remembered_on_user_prompt(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeviceOnlyRememberedOnUserPrompt", []))

    @builtins.property
    @jsii.member(jsii_name="challengeRequiredOnNewDeviceInput")
    def challenge_required_on_new_device_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "challengeRequiredOnNewDeviceInput"))

    @builtins.property
    @jsii.member(jsii_name="deviceOnlyRememberedOnUserPromptInput")
    def device_only_remembered_on_user_prompt_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "deviceOnlyRememberedOnUserPromptInput"))

    @builtins.property
    @jsii.member(jsii_name="challengeRequiredOnNewDevice")
    def challenge_required_on_new_device(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "challengeRequiredOnNewDevice"))

    @challenge_required_on_new_device.setter
    def challenge_required_on_new_device(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c3a776eb6f067cd2ef34376bb526e9484dd0eec5be9c8f2047ce7bc706e44047)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "challengeRequiredOnNewDevice", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="deviceOnlyRememberedOnUserPrompt")
    def device_only_remembered_on_user_prompt(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "deviceOnlyRememberedOnUserPrompt"))

    @device_only_remembered_on_user_prompt.setter
    def device_only_remembered_on_user_prompt(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eaa77464742c9bb4a379c2de01e91c90879bf5c724ae8d1b73763020685086bc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deviceOnlyRememberedOnUserPrompt", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolDeviceConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolDeviceConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolDeviceConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8b0009f51eca5e804eb802fa1b5e100585a26f9d3400023697ebea6df57529fe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolEmailConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "configuration_set": "configurationSet",
        "email_sending_account": "emailSendingAccount",
        "from_email_address": "fromEmailAddress",
        "reply_to_email_address": "replyToEmailAddress",
        "source_arn": "sourceArn",
    },
)
class CognitoUserPoolEmailConfiguration:
    def __init__(
        self,
        *,
        configuration_set: typing.Optional[builtins.str] = None,
        email_sending_account: typing.Optional[builtins.str] = None,
        from_email_address: typing.Optional[builtins.str] = None,
        reply_to_email_address: typing.Optional[builtins.str] = None,
        source_arn: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param configuration_set: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#configuration_set CognitoUserPool#configuration_set}.
        :param email_sending_account: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_sending_account CognitoUserPool#email_sending_account}.
        :param from_email_address: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#from_email_address CognitoUserPool#from_email_address}.
        :param reply_to_email_address: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#reply_to_email_address CognitoUserPool#reply_to_email_address}.
        :param source_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#source_arn CognitoUserPool#source_arn}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__af9a089de62fc519ccb0f39c0d75830a689c4b0f7f03b195ffa38fbb4b3c11a3)
            check_type(argname="argument configuration_set", value=configuration_set, expected_type=type_hints["configuration_set"])
            check_type(argname="argument email_sending_account", value=email_sending_account, expected_type=type_hints["email_sending_account"])
            check_type(argname="argument from_email_address", value=from_email_address, expected_type=type_hints["from_email_address"])
            check_type(argname="argument reply_to_email_address", value=reply_to_email_address, expected_type=type_hints["reply_to_email_address"])
            check_type(argname="argument source_arn", value=source_arn, expected_type=type_hints["source_arn"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if configuration_set is not None:
            self._values["configuration_set"] = configuration_set
        if email_sending_account is not None:
            self._values["email_sending_account"] = email_sending_account
        if from_email_address is not None:
            self._values["from_email_address"] = from_email_address
        if reply_to_email_address is not None:
            self._values["reply_to_email_address"] = reply_to_email_address
        if source_arn is not None:
            self._values["source_arn"] = source_arn

    @builtins.property
    def configuration_set(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#configuration_set CognitoUserPool#configuration_set}.'''
        result = self._values.get("configuration_set")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_sending_account(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_sending_account CognitoUserPool#email_sending_account}.'''
        result = self._values.get("email_sending_account")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def from_email_address(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#from_email_address CognitoUserPool#from_email_address}.'''
        result = self._values.get("from_email_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def reply_to_email_address(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#reply_to_email_address CognitoUserPool#reply_to_email_address}.'''
        result = self._values.get("reply_to_email_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_arn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#source_arn CognitoUserPool#source_arn}.'''
        result = self._values.get("source_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolEmailConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolEmailConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolEmailConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__8d3d63a5174e6335b7ff1303256464c74e2e0764235d1f4b815fc0d77a9d3f8a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetConfigurationSet")
    def reset_configuration_set(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetConfigurationSet", []))

    @jsii.member(jsii_name="resetEmailSendingAccount")
    def reset_email_sending_account(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailSendingAccount", []))

    @jsii.member(jsii_name="resetFromEmailAddress")
    def reset_from_email_address(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetFromEmailAddress", []))

    @jsii.member(jsii_name="resetReplyToEmailAddress")
    def reset_reply_to_email_address(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReplyToEmailAddress", []))

    @jsii.member(jsii_name="resetSourceArn")
    def reset_source_arn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSourceArn", []))

    @builtins.property
    @jsii.member(jsii_name="configurationSetInput")
    def configuration_set_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "configurationSetInput"))

    @builtins.property
    @jsii.member(jsii_name="emailSendingAccountInput")
    def email_sending_account_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailSendingAccountInput"))

    @builtins.property
    @jsii.member(jsii_name="fromEmailAddressInput")
    def from_email_address_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "fromEmailAddressInput"))

    @builtins.property
    @jsii.member(jsii_name="replyToEmailAddressInput")
    def reply_to_email_address_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "replyToEmailAddressInput"))

    @builtins.property
    @jsii.member(jsii_name="sourceArnInput")
    def source_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "sourceArnInput"))

    @builtins.property
    @jsii.member(jsii_name="configurationSet")
    def configuration_set(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "configurationSet"))

    @configuration_set.setter
    def configuration_set(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e4dab689cd637a1993e6cda8fae3f7725561ee49f5b917637c41e308fdd972b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "configurationSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailSendingAccount")
    def email_sending_account(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailSendingAccount"))

    @email_sending_account.setter
    def email_sending_account(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a8711396f7a6886020a90aed8d68d8121b11663e20763714eff51b46e2eea75b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailSendingAccount", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fromEmailAddress")
    def from_email_address(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fromEmailAddress"))

    @from_email_address.setter
    def from_email_address(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3c28a226eb8bdb726894ffe35ec5c8686a09772b7a0644ab794598a25993be3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fromEmailAddress", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="replyToEmailAddress")
    def reply_to_email_address(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "replyToEmailAddress"))

    @reply_to_email_address.setter
    def reply_to_email_address(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__526a7a3e4e1c434db42ce62ce35f42425cb0ff3ad596c4f2239c49c701ef1186)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "replyToEmailAddress", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sourceArn")
    def source_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "sourceArn"))

    @source_arn.setter
    def source_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4566c62c29a3ad4a285f60f598973552df5190b42ff3ee3b172ea4f2f2ffe9f6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sourceArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolEmailConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolEmailConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolEmailConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a4bd736f8f2200fde0bf6648a820679aa2c20d183ab4c65ec4c6fb3069bd1079)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolEmailMfaConfiguration",
    jsii_struct_bases=[],
    name_mapping={"message": "message", "subject": "subject"},
)
class CognitoUserPoolEmailMfaConfiguration:
    def __init__(
        self,
        *,
        message: typing.Optional[builtins.str] = None,
        subject: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#message CognitoUserPool#message}.
        :param subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#subject CognitoUserPool#subject}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a57d909da54e842ec409459d231409dc1686890d6c6173265e9511abda63f717)
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
            check_type(argname="argument subject", value=subject, expected_type=type_hints["subject"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if message is not None:
            self._values["message"] = message
        if subject is not None:
            self._values["subject"] = subject

    @builtins.property
    def message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#message CognitoUserPool#message}.'''
        result = self._values.get("message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subject(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#subject CognitoUserPool#subject}.'''
        result = self._values.get("subject")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolEmailMfaConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolEmailMfaConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolEmailMfaConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__66998ee793a843228eec17bf80bc4190e0e97d5e08e8773b8ce1635d11115fad)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetMessage")
    def reset_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMessage", []))

    @jsii.member(jsii_name="resetSubject")
    def reset_subject(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSubject", []))

    @builtins.property
    @jsii.member(jsii_name="messageInput")
    def message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "messageInput"))

    @builtins.property
    @jsii.member(jsii_name="subjectInput")
    def subject_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "subjectInput"))

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @message.setter
    def message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__42e5a13b1887a17186f6f7362c05f7ad47e41ebc8863368d373bb6b917e4f8bd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "message", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="subject")
    def subject(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "subject"))

    @subject.setter
    def subject(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d79cc3719c106a1cb7e15a798c192e0570eca22e11cb9e73d0754d6dfb059ac9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "subject", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolEmailMfaConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolEmailMfaConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolEmailMfaConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cb9c40ca51b42d99935c2990260202028ecd43b9de656e2bf744ccbabf04cc45)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfig",
    jsii_struct_bases=[],
    name_mapping={
        "create_auth_challenge": "createAuthChallenge",
        "custom_email_sender": "customEmailSender",
        "custom_message": "customMessage",
        "custom_sms_sender": "customSmsSender",
        "define_auth_challenge": "defineAuthChallenge",
        "kms_key_id": "kmsKeyId",
        "post_authentication": "postAuthentication",
        "post_confirmation": "postConfirmation",
        "pre_authentication": "preAuthentication",
        "pre_sign_up": "preSignUp",
        "pre_token_generation": "preTokenGeneration",
        "pre_token_generation_config": "preTokenGenerationConfig",
        "user_migration": "userMigration",
        "verify_auth_challenge_response": "verifyAuthChallengeResponse",
    },
)
class CognitoUserPoolLambdaConfig:
    def __init__(
        self,
        *,
        create_auth_challenge: typing.Optional[builtins.str] = None,
        custom_email_sender: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigCustomEmailSender", typing.Dict[builtins.str, typing.Any]]] = None,
        custom_message: typing.Optional[builtins.str] = None,
        custom_sms_sender: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigCustomSmsSender", typing.Dict[builtins.str, typing.Any]]] = None,
        define_auth_challenge: typing.Optional[builtins.str] = None,
        kms_key_id: typing.Optional[builtins.str] = None,
        post_authentication: typing.Optional[builtins.str] = None,
        post_confirmation: typing.Optional[builtins.str] = None,
        pre_authentication: typing.Optional[builtins.str] = None,
        pre_sign_up: typing.Optional[builtins.str] = None,
        pre_token_generation: typing.Optional[builtins.str] = None,
        pre_token_generation_config: typing.Optional[typing.Union["CognitoUserPoolLambdaConfigPreTokenGenerationConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        user_migration: typing.Optional[builtins.str] = None,
        verify_auth_challenge_response: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create_auth_challenge: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#create_auth_challenge CognitoUserPool#create_auth_challenge}.
        :param custom_email_sender: custom_email_sender block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_email_sender CognitoUserPool#custom_email_sender}
        :param custom_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_message CognitoUserPool#custom_message}.
        :param custom_sms_sender: custom_sms_sender block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_sms_sender CognitoUserPool#custom_sms_sender}
        :param define_auth_challenge: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#define_auth_challenge CognitoUserPool#define_auth_challenge}.
        :param kms_key_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#kms_key_id CognitoUserPool#kms_key_id}.
        :param post_authentication: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_authentication CognitoUserPool#post_authentication}.
        :param post_confirmation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_confirmation CognitoUserPool#post_confirmation}.
        :param pre_authentication: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_authentication CognitoUserPool#pre_authentication}.
        :param pre_sign_up: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_sign_up CognitoUserPool#pre_sign_up}.
        :param pre_token_generation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation CognitoUserPool#pre_token_generation}.
        :param pre_token_generation_config: pre_token_generation_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation_config CognitoUserPool#pre_token_generation_config}
        :param user_migration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_migration CognitoUserPool#user_migration}.
        :param verify_auth_challenge_response: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verify_auth_challenge_response CognitoUserPool#verify_auth_challenge_response}.
        '''
        if isinstance(custom_email_sender, dict):
            custom_email_sender = CognitoUserPoolLambdaConfigCustomEmailSender(**custom_email_sender)
        if isinstance(custom_sms_sender, dict):
            custom_sms_sender = CognitoUserPoolLambdaConfigCustomSmsSender(**custom_sms_sender)
        if isinstance(pre_token_generation_config, dict):
            pre_token_generation_config = CognitoUserPoolLambdaConfigPreTokenGenerationConfig(**pre_token_generation_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__60ce4783a7ebfe2aa03fcd1638b963b78e9f61357ec1970f574c47129e7d2822)
            check_type(argname="argument create_auth_challenge", value=create_auth_challenge, expected_type=type_hints["create_auth_challenge"])
            check_type(argname="argument custom_email_sender", value=custom_email_sender, expected_type=type_hints["custom_email_sender"])
            check_type(argname="argument custom_message", value=custom_message, expected_type=type_hints["custom_message"])
            check_type(argname="argument custom_sms_sender", value=custom_sms_sender, expected_type=type_hints["custom_sms_sender"])
            check_type(argname="argument define_auth_challenge", value=define_auth_challenge, expected_type=type_hints["define_auth_challenge"])
            check_type(argname="argument kms_key_id", value=kms_key_id, expected_type=type_hints["kms_key_id"])
            check_type(argname="argument post_authentication", value=post_authentication, expected_type=type_hints["post_authentication"])
            check_type(argname="argument post_confirmation", value=post_confirmation, expected_type=type_hints["post_confirmation"])
            check_type(argname="argument pre_authentication", value=pre_authentication, expected_type=type_hints["pre_authentication"])
            check_type(argname="argument pre_sign_up", value=pre_sign_up, expected_type=type_hints["pre_sign_up"])
            check_type(argname="argument pre_token_generation", value=pre_token_generation, expected_type=type_hints["pre_token_generation"])
            check_type(argname="argument pre_token_generation_config", value=pre_token_generation_config, expected_type=type_hints["pre_token_generation_config"])
            check_type(argname="argument user_migration", value=user_migration, expected_type=type_hints["user_migration"])
            check_type(argname="argument verify_auth_challenge_response", value=verify_auth_challenge_response, expected_type=type_hints["verify_auth_challenge_response"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_auth_challenge is not None:
            self._values["create_auth_challenge"] = create_auth_challenge
        if custom_email_sender is not None:
            self._values["custom_email_sender"] = custom_email_sender
        if custom_message is not None:
            self._values["custom_message"] = custom_message
        if custom_sms_sender is not None:
            self._values["custom_sms_sender"] = custom_sms_sender
        if define_auth_challenge is not None:
            self._values["define_auth_challenge"] = define_auth_challenge
        if kms_key_id is not None:
            self._values["kms_key_id"] = kms_key_id
        if post_authentication is not None:
            self._values["post_authentication"] = post_authentication
        if post_confirmation is not None:
            self._values["post_confirmation"] = post_confirmation
        if pre_authentication is not None:
            self._values["pre_authentication"] = pre_authentication
        if pre_sign_up is not None:
            self._values["pre_sign_up"] = pre_sign_up
        if pre_token_generation is not None:
            self._values["pre_token_generation"] = pre_token_generation
        if pre_token_generation_config is not None:
            self._values["pre_token_generation_config"] = pre_token_generation_config
        if user_migration is not None:
            self._values["user_migration"] = user_migration
        if verify_auth_challenge_response is not None:
            self._values["verify_auth_challenge_response"] = verify_auth_challenge_response

    @builtins.property
    def create_auth_challenge(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#create_auth_challenge CognitoUserPool#create_auth_challenge}.'''
        result = self._values.get("create_auth_challenge")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_email_sender(
        self,
    ) -> typing.Optional["CognitoUserPoolLambdaConfigCustomEmailSender"]:
        '''custom_email_sender block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_email_sender CognitoUserPool#custom_email_sender}
        '''
        result = self._values.get("custom_email_sender")
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfigCustomEmailSender"], result)

    @builtins.property
    def custom_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_message CognitoUserPool#custom_message}.'''
        result = self._values.get("custom_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_sms_sender(
        self,
    ) -> typing.Optional["CognitoUserPoolLambdaConfigCustomSmsSender"]:
        '''custom_sms_sender block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_sms_sender CognitoUserPool#custom_sms_sender}
        '''
        result = self._values.get("custom_sms_sender")
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfigCustomSmsSender"], result)

    @builtins.property
    def define_auth_challenge(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#define_auth_challenge CognitoUserPool#define_auth_challenge}.'''
        result = self._values.get("define_auth_challenge")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kms_key_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#kms_key_id CognitoUserPool#kms_key_id}.'''
        result = self._values.get("kms_key_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def post_authentication(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_authentication CognitoUserPool#post_authentication}.'''
        result = self._values.get("post_authentication")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def post_confirmation(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#post_confirmation CognitoUserPool#post_confirmation}.'''
        result = self._values.get("post_confirmation")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pre_authentication(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_authentication CognitoUserPool#pre_authentication}.'''
        result = self._values.get("pre_authentication")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pre_sign_up(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_sign_up CognitoUserPool#pre_sign_up}.'''
        result = self._values.get("pre_sign_up")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pre_token_generation(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation CognitoUserPool#pre_token_generation}.'''
        result = self._values.get("pre_token_generation")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pre_token_generation_config(
        self,
    ) -> typing.Optional["CognitoUserPoolLambdaConfigPreTokenGenerationConfig"]:
        '''pre_token_generation_config block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#pre_token_generation_config CognitoUserPool#pre_token_generation_config}
        '''
        result = self._values.get("pre_token_generation_config")
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfigPreTokenGenerationConfig"], result)

    @builtins.property
    def user_migration(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_migration CognitoUserPool#user_migration}.'''
        result = self._values.get("user_migration")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def verify_auth_challenge_response(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#verify_auth_challenge_response CognitoUserPool#verify_auth_challenge_response}.'''
        result = self._values.get("verify_auth_challenge_response")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolLambdaConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigCustomEmailSender",
    jsii_struct_bases=[],
    name_mapping={"lambda_arn": "lambdaArn", "lambda_version": "lambdaVersion"},
)
class CognitoUserPoolLambdaConfigCustomEmailSender:
    def __init__(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__32954a28110eb8412cf1f25dbe1d02f3975d0f1df4396ae6543def087f085e22)
            check_type(argname="argument lambda_arn", value=lambda_arn, expected_type=type_hints["lambda_arn"])
            check_type(argname="argument lambda_version", value=lambda_version, expected_type=type_hints["lambda_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "lambda_arn": lambda_arn,
            "lambda_version": lambda_version,
        }

    @builtins.property
    def lambda_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.'''
        result = self._values.get("lambda_arn")
        assert result is not None, "Required property 'lambda_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def lambda_version(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.'''
        result = self._values.get("lambda_version")
        assert result is not None, "Required property 'lambda_version' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolLambdaConfigCustomEmailSender(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolLambdaConfigCustomEmailSenderOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigCustomEmailSenderOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__f3abdc2877f678c48a97131c2ad5b08d74f74f084a647ed4118f61715cee9133)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="lambdaArnInput")
    def lambda_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaArnInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaVersionInput")
    def lambda_version_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaVersionInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaArn")
    def lambda_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaArn"))

    @lambda_arn.setter
    def lambda_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb9ff17acec8885dcc85535c1a33d1579a3d5eb1823c40e85c6d6148918f7ec7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="lambdaVersion")
    def lambda_version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaVersion"))

    @lambda_version.setter
    def lambda_version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04105a2fe25c4d1c71c3c901787b3dc28e2ac4adb4b7f875f4296de107b21f5d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__450240547b4d5a97c6a33dd4dfdd25d730e1988959c2a9481b4e0e2ca7eec28b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigCustomSmsSender",
    jsii_struct_bases=[],
    name_mapping={"lambda_arn": "lambdaArn", "lambda_version": "lambdaVersion"},
)
class CognitoUserPoolLambdaConfigCustomSmsSender:
    def __init__(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__83fb63b7b3b720a5ec597135c314d10891c44b71446e8e4793145d03cf5d6eb8)
            check_type(argname="argument lambda_arn", value=lambda_arn, expected_type=type_hints["lambda_arn"])
            check_type(argname="argument lambda_version", value=lambda_version, expected_type=type_hints["lambda_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "lambda_arn": lambda_arn,
            "lambda_version": lambda_version,
        }

    @builtins.property
    def lambda_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.'''
        result = self._values.get("lambda_arn")
        assert result is not None, "Required property 'lambda_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def lambda_version(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.'''
        result = self._values.get("lambda_version")
        assert result is not None, "Required property 'lambda_version' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolLambdaConfigCustomSmsSender(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolLambdaConfigCustomSmsSenderOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigCustomSmsSenderOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__ce0a94ecebe029f57704bcbfd4be03beb8e0561df40dbab44e89db83bfebc7ae)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="lambdaArnInput")
    def lambda_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaArnInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaVersionInput")
    def lambda_version_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaVersionInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaArn")
    def lambda_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaArn"))

    @lambda_arn.setter
    def lambda_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec1db8cbd9058bccce72d5573276080b5c5f821742ae328f2c6ec756da65e495)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="lambdaVersion")
    def lambda_version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaVersion"))

    @lambda_version.setter
    def lambda_version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dfbaf96994229d0c184d0b9aab04471a32c6a70be0dcf4997cf58114ee93c9d9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d23037ddd71d0f77a8520042931bb4f58118d96aa18187ae85e6b2f55df1359)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class CognitoUserPoolLambdaConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__8c65c34d46d64b75eb55e4d7da2b43c07d80e261638d601f66d5cd4f144d6e30)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putCustomEmailSender")
    def put_custom_email_sender(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        value = CognitoUserPoolLambdaConfigCustomEmailSender(
            lambda_arn=lambda_arn, lambda_version=lambda_version
        )

        return typing.cast(None, jsii.invoke(self, "putCustomEmailSender", [value]))

    @jsii.member(jsii_name="putCustomSmsSender")
    def put_custom_sms_sender(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        value = CognitoUserPoolLambdaConfigCustomSmsSender(
            lambda_arn=lambda_arn, lambda_version=lambda_version
        )

        return typing.cast(None, jsii.invoke(self, "putCustomSmsSender", [value]))

    @jsii.member(jsii_name="putPreTokenGenerationConfig")
    def put_pre_token_generation_config(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        value = CognitoUserPoolLambdaConfigPreTokenGenerationConfig(
            lambda_arn=lambda_arn, lambda_version=lambda_version
        )

        return typing.cast(None, jsii.invoke(self, "putPreTokenGenerationConfig", [value]))

    @jsii.member(jsii_name="resetCreateAuthChallenge")
    def reset_create_auth_challenge(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreateAuthChallenge", []))

    @jsii.member(jsii_name="resetCustomEmailSender")
    def reset_custom_email_sender(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomEmailSender", []))

    @jsii.member(jsii_name="resetCustomMessage")
    def reset_custom_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomMessage", []))

    @jsii.member(jsii_name="resetCustomSmsSender")
    def reset_custom_sms_sender(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomSmsSender", []))

    @jsii.member(jsii_name="resetDefineAuthChallenge")
    def reset_define_auth_challenge(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefineAuthChallenge", []))

    @jsii.member(jsii_name="resetKmsKeyId")
    def reset_kms_key_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKmsKeyId", []))

    @jsii.member(jsii_name="resetPostAuthentication")
    def reset_post_authentication(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPostAuthentication", []))

    @jsii.member(jsii_name="resetPostConfirmation")
    def reset_post_confirmation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPostConfirmation", []))

    @jsii.member(jsii_name="resetPreAuthentication")
    def reset_pre_authentication(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPreAuthentication", []))

    @jsii.member(jsii_name="resetPreSignUp")
    def reset_pre_sign_up(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPreSignUp", []))

    @jsii.member(jsii_name="resetPreTokenGeneration")
    def reset_pre_token_generation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPreTokenGeneration", []))

    @jsii.member(jsii_name="resetPreTokenGenerationConfig")
    def reset_pre_token_generation_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPreTokenGenerationConfig", []))

    @jsii.member(jsii_name="resetUserMigration")
    def reset_user_migration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserMigration", []))

    @jsii.member(jsii_name="resetVerifyAuthChallengeResponse")
    def reset_verify_auth_challenge_response(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVerifyAuthChallengeResponse", []))

    @builtins.property
    @jsii.member(jsii_name="customEmailSender")
    def custom_email_sender(
        self,
    ) -> CognitoUserPoolLambdaConfigCustomEmailSenderOutputReference:
        return typing.cast(CognitoUserPoolLambdaConfigCustomEmailSenderOutputReference, jsii.get(self, "customEmailSender"))

    @builtins.property
    @jsii.member(jsii_name="customSmsSender")
    def custom_sms_sender(
        self,
    ) -> CognitoUserPoolLambdaConfigCustomSmsSenderOutputReference:
        return typing.cast(CognitoUserPoolLambdaConfigCustomSmsSenderOutputReference, jsii.get(self, "customSmsSender"))

    @builtins.property
    @jsii.member(jsii_name="preTokenGenerationConfig")
    def pre_token_generation_config(
        self,
    ) -> "CognitoUserPoolLambdaConfigPreTokenGenerationConfigOutputReference":
        return typing.cast("CognitoUserPoolLambdaConfigPreTokenGenerationConfigOutputReference", jsii.get(self, "preTokenGenerationConfig"))

    @builtins.property
    @jsii.member(jsii_name="createAuthChallengeInput")
    def create_auth_challenge_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createAuthChallengeInput"))

    @builtins.property
    @jsii.member(jsii_name="customEmailSenderInput")
    def custom_email_sender_input(
        self,
    ) -> typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender], jsii.get(self, "customEmailSenderInput"))

    @builtins.property
    @jsii.member(jsii_name="customMessageInput")
    def custom_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="customSmsSenderInput")
    def custom_sms_sender_input(
        self,
    ) -> typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender], jsii.get(self, "customSmsSenderInput"))

    @builtins.property
    @jsii.member(jsii_name="defineAuthChallengeInput")
    def define_auth_challenge_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defineAuthChallengeInput"))

    @builtins.property
    @jsii.member(jsii_name="kmsKeyIdInput")
    def kms_key_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "kmsKeyIdInput"))

    @builtins.property
    @jsii.member(jsii_name="postAuthenticationInput")
    def post_authentication_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "postAuthenticationInput"))

    @builtins.property
    @jsii.member(jsii_name="postConfirmationInput")
    def post_confirmation_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "postConfirmationInput"))

    @builtins.property
    @jsii.member(jsii_name="preAuthenticationInput")
    def pre_authentication_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "preAuthenticationInput"))

    @builtins.property
    @jsii.member(jsii_name="preSignUpInput")
    def pre_sign_up_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "preSignUpInput"))

    @builtins.property
    @jsii.member(jsii_name="preTokenGenerationConfigInput")
    def pre_token_generation_config_input(
        self,
    ) -> typing.Optional["CognitoUserPoolLambdaConfigPreTokenGenerationConfig"]:
        return typing.cast(typing.Optional["CognitoUserPoolLambdaConfigPreTokenGenerationConfig"], jsii.get(self, "preTokenGenerationConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="preTokenGenerationInput")
    def pre_token_generation_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "preTokenGenerationInput"))

    @builtins.property
    @jsii.member(jsii_name="userMigrationInput")
    def user_migration_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userMigrationInput"))

    @builtins.property
    @jsii.member(jsii_name="verifyAuthChallengeResponseInput")
    def verify_auth_challenge_response_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "verifyAuthChallengeResponseInput"))

    @builtins.property
    @jsii.member(jsii_name="createAuthChallenge")
    def create_auth_challenge(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createAuthChallenge"))

    @create_auth_challenge.setter
    def create_auth_challenge(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a41f0873951eef36d9c4fd0933eeff6db4cccb899ce841506609d6975e22979)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createAuthChallenge", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="customMessage")
    def custom_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customMessage"))

    @custom_message.setter
    def custom_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04d9b61706477b18a579f37aa5b0f4c26044ce7f165220b17e96644d3977c735)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defineAuthChallenge")
    def define_auth_challenge(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "defineAuthChallenge"))

    @define_auth_challenge.setter
    def define_auth_challenge(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee4c396b776a36a3faa783d4e041af813847cc30e1b669f8f3239991de91993a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defineAuthChallenge", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="kmsKeyId")
    def kms_key_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "kmsKeyId"))

    @kms_key_id.setter
    def kms_key_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4a5667dce77f54c66dc7ee44c7230e25750a12c39c29e07980080f8030389533)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "kmsKeyId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="postAuthentication")
    def post_authentication(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "postAuthentication"))

    @post_authentication.setter
    def post_authentication(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d2202e3bfba0354c245b9d6fa35814de4f3288cff1c7644d690a342fd9739ef)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "postAuthentication", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="postConfirmation")
    def post_confirmation(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "postConfirmation"))

    @post_confirmation.setter
    def post_confirmation(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__41b546c3f94339d3734bd79cc102e555bf6ec41eb7187458ed11f6ceea656ca1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "postConfirmation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="preAuthentication")
    def pre_authentication(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "preAuthentication"))

    @pre_authentication.setter
    def pre_authentication(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cb3881906cc6f67522ce323b46c15810bbc098b3b42f992b12cf8fba3b3f79f8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "preAuthentication", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="preSignUp")
    def pre_sign_up(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "preSignUp"))

    @pre_sign_up.setter
    def pre_sign_up(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8bff3b03b37b6d549c96cce69cb6397354d3f52201c70c620f062005d7936580)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "preSignUp", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="preTokenGeneration")
    def pre_token_generation(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "preTokenGeneration"))

    @pre_token_generation.setter
    def pre_token_generation(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4e1cb2acf587d8ef3a61df099341dff0728ae0419a6bcf59b8ddf53db3c58449)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "preTokenGeneration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userMigration")
    def user_migration(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userMigration"))

    @user_migration.setter
    def user_migration(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f7da50c87e20720d550a7e9eb58051d931d07e96eeff3b635ad4f91c9fcfaa7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userMigration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="verifyAuthChallengeResponse")
    def verify_auth_challenge_response(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "verifyAuthChallengeResponse"))

    @verify_auth_challenge_response.setter
    def verify_auth_challenge_response(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ded3ef2c17f8a3a672617c66e26030a90ea49f87530c8c1c7fe5e19e91e8aa59)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "verifyAuthChallengeResponse", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolLambdaConfig]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfig], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolLambdaConfig],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bceffa3f5e30c89b485c4e47ca30e39fb173d7b1ac5a1e9d411595e5973333be)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigPreTokenGenerationConfig",
    jsii_struct_bases=[],
    name_mapping={"lambda_arn": "lambdaArn", "lambda_version": "lambdaVersion"},
)
class CognitoUserPoolLambdaConfigPreTokenGenerationConfig:
    def __init__(
        self,
        *,
        lambda_arn: builtins.str,
        lambda_version: builtins.str,
    ) -> None:
        '''
        :param lambda_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.
        :param lambda_version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b30bd6e85f60789417764d86c167a555093880112f253f73dada4e3fee0e566e)
            check_type(argname="argument lambda_arn", value=lambda_arn, expected_type=type_hints["lambda_arn"])
            check_type(argname="argument lambda_version", value=lambda_version, expected_type=type_hints["lambda_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "lambda_arn": lambda_arn,
            "lambda_version": lambda_version,
        }

    @builtins.property
    def lambda_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_arn CognitoUserPool#lambda_arn}.'''
        result = self._values.get("lambda_arn")
        assert result is not None, "Required property 'lambda_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def lambda_version(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#lambda_version CognitoUserPool#lambda_version}.'''
        result = self._values.get("lambda_version")
        assert result is not None, "Required property 'lambda_version' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolLambdaConfigPreTokenGenerationConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolLambdaConfigPreTokenGenerationConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolLambdaConfigPreTokenGenerationConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__f1375f7ccbef0898c067a70c708a1dc5b5da254f6c35b7c96f2bc14cd95da2ac)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="lambdaArnInput")
    def lambda_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaArnInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaVersionInput")
    def lambda_version_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lambdaVersionInput"))

    @builtins.property
    @jsii.member(jsii_name="lambdaArn")
    def lambda_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaArn"))

    @lambda_arn.setter
    def lambda_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf247518d7cf37a0f4f4e8cf8f209553f81e64648bc4d3e8d98bb4c4bdc3790d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="lambdaVersion")
    def lambda_version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lambdaVersion"))

    @lambda_version.setter
    def lambda_version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__547735dd9f63b8dfb36727da8a116585202346bb460d66688f727701b943a666)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lambdaVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolLambdaConfigPreTokenGenerationConfig]:
        return typing.cast(typing.Optional[CognitoUserPoolLambdaConfigPreTokenGenerationConfig], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolLambdaConfigPreTokenGenerationConfig],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__18f459ec1768d95a3396cc6c34918f2a458c84a82ca170c91027df447f6eaf7d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolPasswordPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "minimum_length": "minimumLength",
        "password_history_size": "passwordHistorySize",
        "require_lowercase": "requireLowercase",
        "require_numbers": "requireNumbers",
        "require_symbols": "requireSymbols",
        "require_uppercase": "requireUppercase",
        "temporary_password_validity_days": "temporaryPasswordValidityDays",
    },
)
class CognitoUserPoolPasswordPolicy:
    def __init__(
        self,
        *,
        minimum_length: typing.Optional[jsii.Number] = None,
        password_history_size: typing.Optional[jsii.Number] = None,
        require_lowercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_numbers: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_symbols: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        require_uppercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        temporary_password_validity_days: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param minimum_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#minimum_length CognitoUserPool#minimum_length}.
        :param password_history_size: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_history_size CognitoUserPool#password_history_size}.
        :param require_lowercase: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_lowercase CognitoUserPool#require_lowercase}.
        :param require_numbers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_numbers CognitoUserPool#require_numbers}.
        :param require_symbols: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_symbols CognitoUserPool#require_symbols}.
        :param require_uppercase: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_uppercase CognitoUserPool#require_uppercase}.
        :param temporary_password_validity_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#temporary_password_validity_days CognitoUserPool#temporary_password_validity_days}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__631a46f60f7494ed7d5ef6ba5879ce6ecc7723e2d9b0d704c26e243c14b05073)
            check_type(argname="argument minimum_length", value=minimum_length, expected_type=type_hints["minimum_length"])
            check_type(argname="argument password_history_size", value=password_history_size, expected_type=type_hints["password_history_size"])
            check_type(argname="argument require_lowercase", value=require_lowercase, expected_type=type_hints["require_lowercase"])
            check_type(argname="argument require_numbers", value=require_numbers, expected_type=type_hints["require_numbers"])
            check_type(argname="argument require_symbols", value=require_symbols, expected_type=type_hints["require_symbols"])
            check_type(argname="argument require_uppercase", value=require_uppercase, expected_type=type_hints["require_uppercase"])
            check_type(argname="argument temporary_password_validity_days", value=temporary_password_validity_days, expected_type=type_hints["temporary_password_validity_days"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if minimum_length is not None:
            self._values["minimum_length"] = minimum_length
        if password_history_size is not None:
            self._values["password_history_size"] = password_history_size
        if require_lowercase is not None:
            self._values["require_lowercase"] = require_lowercase
        if require_numbers is not None:
            self._values["require_numbers"] = require_numbers
        if require_symbols is not None:
            self._values["require_symbols"] = require_symbols
        if require_uppercase is not None:
            self._values["require_uppercase"] = require_uppercase
        if temporary_password_validity_days is not None:
            self._values["temporary_password_validity_days"] = temporary_password_validity_days

    @builtins.property
    def minimum_length(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#minimum_length CognitoUserPool#minimum_length}.'''
        result = self._values.get("minimum_length")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def password_history_size(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#password_history_size CognitoUserPool#password_history_size}.'''
        result = self._values.get("password_history_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def require_lowercase(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_lowercase CognitoUserPool#require_lowercase}.'''
        result = self._values.get("require_lowercase")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def require_numbers(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_numbers CognitoUserPool#require_numbers}.'''
        result = self._values.get("require_numbers")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def require_symbols(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_symbols CognitoUserPool#require_symbols}.'''
        result = self._values.get("require_symbols")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def require_uppercase(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#require_uppercase CognitoUserPool#require_uppercase}.'''
        result = self._values.get("require_uppercase")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def temporary_password_validity_days(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#temporary_password_validity_days CognitoUserPool#temporary_password_validity_days}.'''
        result = self._values.get("temporary_password_validity_days")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolPasswordPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolPasswordPolicyOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolPasswordPolicyOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__83e9dda3ed2fb16e9180ae7124628863a14e7586b6bc52e29ab121fec41df344)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetMinimumLength")
    def reset_minimum_length(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMinimumLength", []))

    @jsii.member(jsii_name="resetPasswordHistorySize")
    def reset_password_history_size(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPasswordHistorySize", []))

    @jsii.member(jsii_name="resetRequireLowercase")
    def reset_require_lowercase(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRequireLowercase", []))

    @jsii.member(jsii_name="resetRequireNumbers")
    def reset_require_numbers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRequireNumbers", []))

    @jsii.member(jsii_name="resetRequireSymbols")
    def reset_require_symbols(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRequireSymbols", []))

    @jsii.member(jsii_name="resetRequireUppercase")
    def reset_require_uppercase(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRequireUppercase", []))

    @jsii.member(jsii_name="resetTemporaryPasswordValidityDays")
    def reset_temporary_password_validity_days(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTemporaryPasswordValidityDays", []))

    @builtins.property
    @jsii.member(jsii_name="minimumLengthInput")
    def minimum_length_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minimumLengthInput"))

    @builtins.property
    @jsii.member(jsii_name="passwordHistorySizeInput")
    def password_history_size_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "passwordHistorySizeInput"))

    @builtins.property
    @jsii.member(jsii_name="requireLowercaseInput")
    def require_lowercase_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "requireLowercaseInput"))

    @builtins.property
    @jsii.member(jsii_name="requireNumbersInput")
    def require_numbers_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "requireNumbersInput"))

    @builtins.property
    @jsii.member(jsii_name="requireSymbolsInput")
    def require_symbols_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "requireSymbolsInput"))

    @builtins.property
    @jsii.member(jsii_name="requireUppercaseInput")
    def require_uppercase_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "requireUppercaseInput"))

    @builtins.property
    @jsii.member(jsii_name="temporaryPasswordValidityDaysInput")
    def temporary_password_validity_days_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "temporaryPasswordValidityDaysInput"))

    @builtins.property
    @jsii.member(jsii_name="minimumLength")
    def minimum_length(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "minimumLength"))

    @minimum_length.setter
    def minimum_length(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__007f59030a469416aa8cd065cefba864fd39f60347a29a11dd07d4bb8c536d43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "minimumLength", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="passwordHistorySize")
    def password_history_size(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "passwordHistorySize"))

    @password_history_size.setter
    def password_history_size(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8871e155b8b666da538fff4776281fed63f105d290c4cca92fd55193c47b91b2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "passwordHistorySize", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="requireLowercase")
    def require_lowercase(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "requireLowercase"))

    @require_lowercase.setter
    def require_lowercase(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c371dbec963cb05ca4e3343f76c36854f321669bf86bddcc91e1483be5ba35ab)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "requireLowercase", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="requireNumbers")
    def require_numbers(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "requireNumbers"))

    @require_numbers.setter
    def require_numbers(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b122c77f73f9328f8699075a3b4cfd12eb6e5a2b5225d272ee07686bdbe0186d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "requireNumbers", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="requireSymbols")
    def require_symbols(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "requireSymbols"))

    @require_symbols.setter
    def require_symbols(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d27f50051cac084d561cf60727af25a0f4ae5413cbf04101b6b26f8cc28c8d50)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "requireSymbols", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="requireUppercase")
    def require_uppercase(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "requireUppercase"))

    @require_uppercase.setter
    def require_uppercase(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__356214cf60070ea22d866ac913062f67cfb9da1816ae259a8a14f6172891a788)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "requireUppercase", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="temporaryPasswordValidityDays")
    def temporary_password_validity_days(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "temporaryPasswordValidityDays"))

    @temporary_password_validity_days.setter
    def temporary_password_validity_days(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e47d3a12bb72e93aab94419acff015f2779e584422e9ef2bb42bfa11a54664d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "temporaryPasswordValidityDays", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolPasswordPolicy]:
        return typing.cast(typing.Optional[CognitoUserPoolPasswordPolicy], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolPasswordPolicy],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__411118f0bed8f2622fa78e7be9c91d373cd44197eb1d5e45bb3e543dd77613bf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchema",
    jsii_struct_bases=[],
    name_mapping={
        "attribute_data_type": "attributeDataType",
        "name": "name",
        "developer_only_attribute": "developerOnlyAttribute",
        "mutable": "mutable",
        "number_attribute_constraints": "numberAttributeConstraints",
        "required": "required",
        "string_attribute_constraints": "stringAttributeConstraints",
    },
)
class CognitoUserPoolSchema:
    def __init__(
        self,
        *,
        attribute_data_type: builtins.str,
        name: builtins.str,
        developer_only_attribute: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        mutable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        number_attribute_constraints: typing.Optional[typing.Union["CognitoUserPoolSchemaNumberAttributeConstraints", typing.Dict[builtins.str, typing.Any]]] = None,
        required: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        string_attribute_constraints: typing.Optional[typing.Union["CognitoUserPoolSchemaStringAttributeConstraints", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param attribute_data_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#attribute_data_type CognitoUserPool#attribute_data_type}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.
        :param developer_only_attribute: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#developer_only_attribute CognitoUserPool#developer_only_attribute}.
        :param mutable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#mutable CognitoUserPool#mutable}.
        :param number_attribute_constraints: number_attribute_constraints block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#number_attribute_constraints CognitoUserPool#number_attribute_constraints}
        :param required: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#required CognitoUserPool#required}.
        :param string_attribute_constraints: string_attribute_constraints block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#string_attribute_constraints CognitoUserPool#string_attribute_constraints}
        '''
        if isinstance(number_attribute_constraints, dict):
            number_attribute_constraints = CognitoUserPoolSchemaNumberAttributeConstraints(**number_attribute_constraints)
        if isinstance(string_attribute_constraints, dict):
            string_attribute_constraints = CognitoUserPoolSchemaStringAttributeConstraints(**string_attribute_constraints)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f4ac428a45c7eedbd44d04a1f9cc9afb69a23417beeead59d53553ce735a8c69)
            check_type(argname="argument attribute_data_type", value=attribute_data_type, expected_type=type_hints["attribute_data_type"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument developer_only_attribute", value=developer_only_attribute, expected_type=type_hints["developer_only_attribute"])
            check_type(argname="argument mutable", value=mutable, expected_type=type_hints["mutable"])
            check_type(argname="argument number_attribute_constraints", value=number_attribute_constraints, expected_type=type_hints["number_attribute_constraints"])
            check_type(argname="argument required", value=required, expected_type=type_hints["required"])
            check_type(argname="argument string_attribute_constraints", value=string_attribute_constraints, expected_type=type_hints["string_attribute_constraints"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "attribute_data_type": attribute_data_type,
            "name": name,
        }
        if developer_only_attribute is not None:
            self._values["developer_only_attribute"] = developer_only_attribute
        if mutable is not None:
            self._values["mutable"] = mutable
        if number_attribute_constraints is not None:
            self._values["number_attribute_constraints"] = number_attribute_constraints
        if required is not None:
            self._values["required"] = required
        if string_attribute_constraints is not None:
            self._values["string_attribute_constraints"] = string_attribute_constraints

    @builtins.property
    def attribute_data_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#attribute_data_type CognitoUserPool#attribute_data_type}.'''
        result = self._values.get("attribute_data_type")
        assert result is not None, "Required property 'attribute_data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#name CognitoUserPool#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def developer_only_attribute(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#developer_only_attribute CognitoUserPool#developer_only_attribute}.'''
        result = self._values.get("developer_only_attribute")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def mutable(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#mutable CognitoUserPool#mutable}.'''
        result = self._values.get("mutable")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def number_attribute_constraints(
        self,
    ) -> typing.Optional["CognitoUserPoolSchemaNumberAttributeConstraints"]:
        '''number_attribute_constraints block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#number_attribute_constraints CognitoUserPool#number_attribute_constraints}
        '''
        result = self._values.get("number_attribute_constraints")
        return typing.cast(typing.Optional["CognitoUserPoolSchemaNumberAttributeConstraints"], result)

    @builtins.property
    def required(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#required CognitoUserPool#required}.'''
        result = self._values.get("required")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def string_attribute_constraints(
        self,
    ) -> typing.Optional["CognitoUserPoolSchemaStringAttributeConstraints"]:
        '''string_attribute_constraints block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#string_attribute_constraints CognitoUserPool#string_attribute_constraints}
        '''
        result = self._values.get("string_attribute_constraints")
        return typing.cast(typing.Optional["CognitoUserPoolSchemaStringAttributeConstraints"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSchema(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSchemaList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__ad76fd9610f1b6fe0faefce60ba0bc305e470c43f1bceab59bfc8bb6e82595d2)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "CognitoUserPoolSchemaOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4565a2ed22310b1aa3b8ce1a17402e75b45e6e0b41495539e8b1c02f08c5f142)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("CognitoUserPoolSchemaOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__771ce5e3ff8fca87c9a5742aa9a3195ba6a1db8347cd9810e4638c101b94ee0d)
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
            type_hints = typing.get_type_hints(_typecheckingstub__2c6493e42346562296ff295fa3615d72f0a6f8bf3cd922fbb3ea45cceaae47c4)
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
            type_hints = typing.get_type_hints(_typecheckingstub__9e9b19ed23c37f7c3f87fea35e546009b2741d7ba372b7dc38b7e62a2424d009)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolSchema]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolSchema]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolSchema]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__067cd7ee6915dcabbedfada1cb549ac3208f9ba9388df5ad44f64b25bf074728)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaNumberAttributeConstraints",
    jsii_struct_bases=[],
    name_mapping={"max_value": "maxValue", "min_value": "minValue"},
)
class CognitoUserPoolSchemaNumberAttributeConstraints:
    def __init__(
        self,
        *,
        max_value: typing.Optional[builtins.str] = None,
        min_value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_value CognitoUserPool#max_value}.
        :param min_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_value CognitoUserPool#min_value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7cb7eee32db8cce6e32749e30825a808d9b036dc3f55e24c01b250deb7131310)
            check_type(argname="argument max_value", value=max_value, expected_type=type_hints["max_value"])
            check_type(argname="argument min_value", value=min_value, expected_type=type_hints["min_value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if max_value is not None:
            self._values["max_value"] = max_value
        if min_value is not None:
            self._values["min_value"] = min_value

    @builtins.property
    def max_value(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_value CognitoUserPool#max_value}.'''
        result = self._values.get("max_value")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def min_value(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_value CognitoUserPool#min_value}.'''
        result = self._values.get("min_value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSchemaNumberAttributeConstraints(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSchemaNumberAttributeConstraintsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaNumberAttributeConstraintsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__6cdf511dee892ae69f5300f6f038832e62179a29ef77cc6e77b246853f9397b3)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetMaxValue")
    def reset_max_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxValue", []))

    @jsii.member(jsii_name="resetMinValue")
    def reset_min_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMinValue", []))

    @builtins.property
    @jsii.member(jsii_name="maxValueInput")
    def max_value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "maxValueInput"))

    @builtins.property
    @jsii.member(jsii_name="minValueInput")
    def min_value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "minValueInput"))

    @builtins.property
    @jsii.member(jsii_name="maxValue")
    def max_value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "maxValue"))

    @max_value.setter
    def max_value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f528f2bbac0627208bfd228b155dac06f19d5fb8a0b62237c0a9e16f8f0ac002)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="minValue")
    def min_value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "minValue"))

    @min_value.setter
    def min_value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eac49b032239e6643a473752787efb237a1da162a9738db44813974a61e345a4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "minValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints]:
        return typing.cast(typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__15aa5c3b961638d330289b28774de20c3609fb8ee89989f853b873fef10974ef)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class CognitoUserPoolSchemaOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__aa2a92c9b6042d284b8672dd7a278989488abbbbc3c137f1a176461c74af04cf)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="putNumberAttributeConstraints")
    def put_number_attribute_constraints(
        self,
        *,
        max_value: typing.Optional[builtins.str] = None,
        min_value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_value CognitoUserPool#max_value}.
        :param min_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_value CognitoUserPool#min_value}.
        '''
        value = CognitoUserPoolSchemaNumberAttributeConstraints(
            max_value=max_value, min_value=min_value
        )

        return typing.cast(None, jsii.invoke(self, "putNumberAttributeConstraints", [value]))

    @jsii.member(jsii_name="putStringAttributeConstraints")
    def put_string_attribute_constraints(
        self,
        *,
        max_length: typing.Optional[builtins.str] = None,
        min_length: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_length CognitoUserPool#max_length}.
        :param min_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_length CognitoUserPool#min_length}.
        '''
        value = CognitoUserPoolSchemaStringAttributeConstraints(
            max_length=max_length, min_length=min_length
        )

        return typing.cast(None, jsii.invoke(self, "putStringAttributeConstraints", [value]))

    @jsii.member(jsii_name="resetDeveloperOnlyAttribute")
    def reset_developer_only_attribute(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeveloperOnlyAttribute", []))

    @jsii.member(jsii_name="resetMutable")
    def reset_mutable(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMutable", []))

    @jsii.member(jsii_name="resetNumberAttributeConstraints")
    def reset_number_attribute_constraints(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNumberAttributeConstraints", []))

    @jsii.member(jsii_name="resetRequired")
    def reset_required(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRequired", []))

    @jsii.member(jsii_name="resetStringAttributeConstraints")
    def reset_string_attribute_constraints(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStringAttributeConstraints", []))

    @builtins.property
    @jsii.member(jsii_name="numberAttributeConstraints")
    def number_attribute_constraints(
        self,
    ) -> CognitoUserPoolSchemaNumberAttributeConstraintsOutputReference:
        return typing.cast(CognitoUserPoolSchemaNumberAttributeConstraintsOutputReference, jsii.get(self, "numberAttributeConstraints"))

    @builtins.property
    @jsii.member(jsii_name="stringAttributeConstraints")
    def string_attribute_constraints(
        self,
    ) -> "CognitoUserPoolSchemaStringAttributeConstraintsOutputReference":
        return typing.cast("CognitoUserPoolSchemaStringAttributeConstraintsOutputReference", jsii.get(self, "stringAttributeConstraints"))

    @builtins.property
    @jsii.member(jsii_name="attributeDataTypeInput")
    def attribute_data_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "attributeDataTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="developerOnlyAttributeInput")
    def developer_only_attribute_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "developerOnlyAttributeInput"))

    @builtins.property
    @jsii.member(jsii_name="mutableInput")
    def mutable_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "mutableInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="numberAttributeConstraintsInput")
    def number_attribute_constraints_input(
        self,
    ) -> typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints]:
        return typing.cast(typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints], jsii.get(self, "numberAttributeConstraintsInput"))

    @builtins.property
    @jsii.member(jsii_name="requiredInput")
    def required_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "requiredInput"))

    @builtins.property
    @jsii.member(jsii_name="stringAttributeConstraintsInput")
    def string_attribute_constraints_input(
        self,
    ) -> typing.Optional["CognitoUserPoolSchemaStringAttributeConstraints"]:
        return typing.cast(typing.Optional["CognitoUserPoolSchemaStringAttributeConstraints"], jsii.get(self, "stringAttributeConstraintsInput"))

    @builtins.property
    @jsii.member(jsii_name="attributeDataType")
    def attribute_data_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "attributeDataType"))

    @attribute_data_type.setter
    def attribute_data_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1ff4648e1e648f7051f46a4c31047bcd31a7261979fe8527e606411e76a412b1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "attributeDataType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="developerOnlyAttribute")
    def developer_only_attribute(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "developerOnlyAttribute"))

    @developer_only_attribute.setter
    def developer_only_attribute(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e045fb62b5880e6658c8070518a7fa13d3cbd55a10ed0e7964bccffe9334a34)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "developerOnlyAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="mutable")
    def mutable(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "mutable"))

    @mutable.setter
    def mutable(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d1928a11737882c0689b8a99194095fd313932f5025f3cad5a5f0399bb631e0e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "mutable", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2badf4cb530da930cbc79d29d51f44a1e1a8c066f649274c5796336972e04165)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="required")
    def required(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "required"))

    @required.setter
    def required(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2cef8c93eb8dd9f03170e5690e6bf60a6e9a59bf09d5f72ba709c0e71ae07b08)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "required", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolSchema]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolSchema]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolSchema]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__25c2df1b32bd9b8ce4a9be1fb731bad17eb7aeeffec67007461ac91170977072)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaStringAttributeConstraints",
    jsii_struct_bases=[],
    name_mapping={"max_length": "maxLength", "min_length": "minLength"},
)
class CognitoUserPoolSchemaStringAttributeConstraints:
    def __init__(
        self,
        *,
        max_length: typing.Optional[builtins.str] = None,
        min_length: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param max_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_length CognitoUserPool#max_length}.
        :param min_length: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_length CognitoUserPool#min_length}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0164f8aca70fbc1cdf462a19b4c8e2003c0c5c081d20931247a25514de66be7)
            check_type(argname="argument max_length", value=max_length, expected_type=type_hints["max_length"])
            check_type(argname="argument min_length", value=min_length, expected_type=type_hints["min_length"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if max_length is not None:
            self._values["max_length"] = max_length
        if min_length is not None:
            self._values["min_length"] = min_length

    @builtins.property
    def max_length(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#max_length CognitoUserPool#max_length}.'''
        result = self._values.get("max_length")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def min_length(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#min_length CognitoUserPool#min_length}.'''
        result = self._values.get("min_length")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSchemaStringAttributeConstraints(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSchemaStringAttributeConstraintsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSchemaStringAttributeConstraintsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__eb1171489c0fb9ca819d0f4ffca2043ad6c0e1155cca6665508f80402c3d1099)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetMaxLength")
    def reset_max_length(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxLength", []))

    @jsii.member(jsii_name="resetMinLength")
    def reset_min_length(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMinLength", []))

    @builtins.property
    @jsii.member(jsii_name="maxLengthInput")
    def max_length_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "maxLengthInput"))

    @builtins.property
    @jsii.member(jsii_name="minLengthInput")
    def min_length_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "minLengthInput"))

    @builtins.property
    @jsii.member(jsii_name="maxLength")
    def max_length(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "maxLength"))

    @max_length.setter
    def max_length(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__236d3e61948af380022a243f2eb73a9f0330b66e40fba23da816e4c711da11c5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxLength", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="minLength")
    def min_length(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "minLength"))

    @min_length.setter
    def min_length(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d4222efbcd7cca9e9eaec7a663e69ba2b8e7a7600e345a3be02e03595a9c2a4c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "minLength", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolSchemaStringAttributeConstraints]:
        return typing.cast(typing.Optional[CognitoUserPoolSchemaStringAttributeConstraints], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolSchemaStringAttributeConstraints],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__890fe6dbfc0ad939efa83e4e2791a643223bdb12873558e33b042fc422716d12)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSignInPolicy",
    jsii_struct_bases=[],
    name_mapping={"allowed_first_auth_factors": "allowedFirstAuthFactors"},
)
class CognitoUserPoolSignInPolicy:
    def __init__(
        self,
        *,
        allowed_first_auth_factors: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param allowed_first_auth_factors: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allowed_first_auth_factors CognitoUserPool#allowed_first_auth_factors}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40399343ba18eb846c16e68fb429760c59f71a7a01aa95040f180c0c621ddc0a)
            check_type(argname="argument allowed_first_auth_factors", value=allowed_first_auth_factors, expected_type=type_hints["allowed_first_auth_factors"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allowed_first_auth_factors is not None:
            self._values["allowed_first_auth_factors"] = allowed_first_auth_factors

    @builtins.property
    def allowed_first_auth_factors(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#allowed_first_auth_factors CognitoUserPool#allowed_first_auth_factors}.'''
        result = self._values.get("allowed_first_auth_factors")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSignInPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSignInPolicyOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSignInPolicyOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d113e5c0ee6f6fbc750ab47bfd7ae9198c1b01ed2692673f5509bd89722931a6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAllowedFirstAuthFactors")
    def reset_allowed_first_auth_factors(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAllowedFirstAuthFactors", []))

    @builtins.property
    @jsii.member(jsii_name="allowedFirstAuthFactorsInput")
    def allowed_first_auth_factors_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "allowedFirstAuthFactorsInput"))

    @builtins.property
    @jsii.member(jsii_name="allowedFirstAuthFactors")
    def allowed_first_auth_factors(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "allowedFirstAuthFactors"))

    @allowed_first_auth_factors.setter
    def allowed_first_auth_factors(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__87f076bc345f75d85e627c53c7a530211fdd23b5be71c8f63419e53ab89e4534)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "allowedFirstAuthFactors", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolSignInPolicy]:
        return typing.cast(typing.Optional[CognitoUserPoolSignInPolicy], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolSignInPolicy],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__44f25df28ff137231337683e8d69a2f1e47c84d2e792b4c7bf12ae679f424949)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSmsConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "external_id": "externalId",
        "sns_caller_arn": "snsCallerArn",
        "sns_region": "snsRegion",
    },
)
class CognitoUserPoolSmsConfiguration:
    def __init__(
        self,
        *,
        external_id: builtins.str,
        sns_caller_arn: builtins.str,
        sns_region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param external_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#external_id CognitoUserPool#external_id}.
        :param sns_caller_arn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_caller_arn CognitoUserPool#sns_caller_arn}.
        :param sns_region: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_region CognitoUserPool#sns_region}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__098b42fa7a0f77d8ce0802e08befdfefe8fdde139ec7ec4cfee931d8570dd080)
            check_type(argname="argument external_id", value=external_id, expected_type=type_hints["external_id"])
            check_type(argname="argument sns_caller_arn", value=sns_caller_arn, expected_type=type_hints["sns_caller_arn"])
            check_type(argname="argument sns_region", value=sns_region, expected_type=type_hints["sns_region"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "external_id": external_id,
            "sns_caller_arn": sns_caller_arn,
        }
        if sns_region is not None:
            self._values["sns_region"] = sns_region

    @builtins.property
    def external_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#external_id CognitoUserPool#external_id}.'''
        result = self._values.get("external_id")
        assert result is not None, "Required property 'external_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def sns_caller_arn(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_caller_arn CognitoUserPool#sns_caller_arn}.'''
        result = self._values.get("sns_caller_arn")
        assert result is not None, "Required property 'sns_caller_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def sns_region(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sns_region CognitoUserPool#sns_region}.'''
        result = self._values.get("sns_region")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSmsConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSmsConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSmsConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__70123940b5a0f22222de00ecff9eeb5d6b3e81563bed4abcc65223bede4e4053)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetSnsRegion")
    def reset_sns_region(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSnsRegion", []))

    @builtins.property
    @jsii.member(jsii_name="externalIdInput")
    def external_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "externalIdInput"))

    @builtins.property
    @jsii.member(jsii_name="snsCallerArnInput")
    def sns_caller_arn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "snsCallerArnInput"))

    @builtins.property
    @jsii.member(jsii_name="snsRegionInput")
    def sns_region_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "snsRegionInput"))

    @builtins.property
    @jsii.member(jsii_name="externalId")
    def external_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "externalId"))

    @external_id.setter
    def external_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a2df6638131dd5324b9c85abb20b5899d59b8a46e8de518f576086226442c1d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "externalId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="snsCallerArn")
    def sns_caller_arn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "snsCallerArn"))

    @sns_caller_arn.setter
    def sns_caller_arn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f7007ff3da4456bc7b31f4f332989befc14cbb545629cc1c210d357d26354e22)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "snsCallerArn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="snsRegion")
    def sns_region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "snsRegion"))

    @sns_region.setter
    def sns_region(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c23c63ce7632ce9d6d4f7f53a1618c59c7a12015d84bb7844176bb5d31c2968)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "snsRegion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolSmsConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolSmsConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolSmsConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__85a6ad7b5a969f6f9c24d070f00709814e42176ca3f0e8121444867a0154b915)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSoftwareTokenMfaConfiguration",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class CognitoUserPoolSoftwareTokenMfaConfiguration:
    def __init__(
        self,
        *,
        enabled: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        '''
        :param enabled: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#enabled CognitoUserPool#enabled}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa997d41c5680ae0a4860a332ba7be63a079caeea0a56b28692b4ec2be9fcdfa)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "enabled": enabled,
        }

    @builtins.property
    def enabled(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#enabled CognitoUserPool#enabled}.'''
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolSoftwareTokenMfaConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolSoftwareTokenMfaConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolSoftwareTokenMfaConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1e38b13b3d04c6e50b5f1b7d6e21c1cbbf534b47c09df723ff2e32c1f8747710)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="enabledInput")
    def enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enabledInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__81175d239f9439e94d912d4147866217125b196d372cde9fc3359239625a6022)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolSoftwareTokenMfaConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolSoftwareTokenMfaConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolSoftwareTokenMfaConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5abd8988d319a272038bb3c171ba4ab8869ee0d4ccf35194b6ee03d8b1a6a56a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserAttributeUpdateSettings",
    jsii_struct_bases=[],
    name_mapping={
        "attributes_require_verification_before_update": "attributesRequireVerificationBeforeUpdate",
    },
)
class CognitoUserPoolUserAttributeUpdateSettings:
    def __init__(
        self,
        *,
        attributes_require_verification_before_update: typing.Sequence[builtins.str],
    ) -> None:
        '''
        :param attributes_require_verification_before_update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#attributes_require_verification_before_update CognitoUserPool#attributes_require_verification_before_update}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2eac78eb7a3ffe7c99bc37d96361b490f95178d3cf97311500388ddc278ac0b6)
            check_type(argname="argument attributes_require_verification_before_update", value=attributes_require_verification_before_update, expected_type=type_hints["attributes_require_verification_before_update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "attributes_require_verification_before_update": attributes_require_verification_before_update,
        }

    @builtins.property
    def attributes_require_verification_before_update(
        self,
    ) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#attributes_require_verification_before_update CognitoUserPool#attributes_require_verification_before_update}.'''
        result = self._values.get("attributes_require_verification_before_update")
        assert result is not None, "Required property 'attributes_require_verification_before_update' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolUserAttributeUpdateSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolUserAttributeUpdateSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserAttributeUpdateSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b87db15acbcfd810d48fc890aeb522ac4ee652599de90ebb476a674268fec049)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="attributesRequireVerificationBeforeUpdateInput")
    def attributes_require_verification_before_update_input(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "attributesRequireVerificationBeforeUpdateInput"))

    @builtins.property
    @jsii.member(jsii_name="attributesRequireVerificationBeforeUpdate")
    def attributes_require_verification_before_update(
        self,
    ) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "attributesRequireVerificationBeforeUpdate"))

    @attributes_require_verification_before_update.setter
    def attributes_require_verification_before_update(
        self,
        value: typing.List[builtins.str],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__365edbfd2ce875b81cb77dc8dd99b502a21c268c65e0cafe58d00f0619b3942a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "attributesRequireVerificationBeforeUpdate", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolUserAttributeUpdateSettings]:
        return typing.cast(typing.Optional[CognitoUserPoolUserAttributeUpdateSettings], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolUserAttributeUpdateSettings],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b09fbad1e9b7e4919b836a8a10fff35f3afca0231a4d585b5f4823db2688fd22)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserPoolAddOns",
    jsii_struct_bases=[],
    name_mapping={
        "advanced_security_mode": "advancedSecurityMode",
        "advanced_security_additional_flows": "advancedSecurityAdditionalFlows",
    },
)
class CognitoUserPoolUserPoolAddOns:
    def __init__(
        self,
        *,
        advanced_security_mode: builtins.str,
        advanced_security_additional_flows: typing.Optional[typing.Union["CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param advanced_security_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_mode CognitoUserPool#advanced_security_mode}.
        :param advanced_security_additional_flows: advanced_security_additional_flows block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_additional_flows CognitoUserPool#advanced_security_additional_flows}
        '''
        if isinstance(advanced_security_additional_flows, dict):
            advanced_security_additional_flows = CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows(**advanced_security_additional_flows)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a981ae45e5c2957680ce1240804ceb84b62f1cabbe4978884b986b2d88d30ce)
            check_type(argname="argument advanced_security_mode", value=advanced_security_mode, expected_type=type_hints["advanced_security_mode"])
            check_type(argname="argument advanced_security_additional_flows", value=advanced_security_additional_flows, expected_type=type_hints["advanced_security_additional_flows"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "advanced_security_mode": advanced_security_mode,
        }
        if advanced_security_additional_flows is not None:
            self._values["advanced_security_additional_flows"] = advanced_security_additional_flows

    @builtins.property
    def advanced_security_mode(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_mode CognitoUserPool#advanced_security_mode}.'''
        result = self._values.get("advanced_security_mode")
        assert result is not None, "Required property 'advanced_security_mode' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def advanced_security_additional_flows(
        self,
    ) -> typing.Optional["CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows"]:
        '''advanced_security_additional_flows block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#advanced_security_additional_flows CognitoUserPool#advanced_security_additional_flows}
        '''
        result = self._values.get("advanced_security_additional_flows")
        return typing.cast(typing.Optional["CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolUserPoolAddOns(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows",
    jsii_struct_bases=[],
    name_mapping={"custom_auth_mode": "customAuthMode"},
)
class CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows:
    def __init__(
        self,
        *,
        custom_auth_mode: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param custom_auth_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_auth_mode CognitoUserPool#custom_auth_mode}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b09ed9ee763732398a9b7a22ec2984722142eb8394ab12c0e0700fb14bead1e5)
            check_type(argname="argument custom_auth_mode", value=custom_auth_mode, expected_type=type_hints["custom_auth_mode"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if custom_auth_mode is not None:
            self._values["custom_auth_mode"] = custom_auth_mode

    @builtins.property
    def custom_auth_mode(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_auth_mode CognitoUserPool#custom_auth_mode}.'''
        result = self._values.get("custom_auth_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlowsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlowsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__2b0f910675c3caeae1aa34a1b1da817f562401e589054c9b5986206da14c1058)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCustomAuthMode")
    def reset_custom_auth_mode(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomAuthMode", []))

    @builtins.property
    @jsii.member(jsii_name="customAuthModeInput")
    def custom_auth_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customAuthModeInput"))

    @builtins.property
    @jsii.member(jsii_name="customAuthMode")
    def custom_auth_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customAuthMode"))

    @custom_auth_mode.setter
    def custom_auth_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3acd0cdf37afae2efbee5578c3f70f94d07a353f11a9a335b59989aefc62ae8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customAuthMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows]:
        return typing.cast(typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6bc995e031f6b7c90945da6a168ece90026b0e396662a77cf2780fe12c8eaa3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class CognitoUserPoolUserPoolAddOnsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUserPoolAddOnsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1b7b7850d0043fb6afb29ac123ac726f52c7c47ebd08ddf518aea9a9f74a219d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putAdvancedSecurityAdditionalFlows")
    def put_advanced_security_additional_flows(
        self,
        *,
        custom_auth_mode: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param custom_auth_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#custom_auth_mode CognitoUserPool#custom_auth_mode}.
        '''
        value = CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows(
            custom_auth_mode=custom_auth_mode
        )

        return typing.cast(None, jsii.invoke(self, "putAdvancedSecurityAdditionalFlows", [value]))

    @jsii.member(jsii_name="resetAdvancedSecurityAdditionalFlows")
    def reset_advanced_security_additional_flows(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAdvancedSecurityAdditionalFlows", []))

    @builtins.property
    @jsii.member(jsii_name="advancedSecurityAdditionalFlows")
    def advanced_security_additional_flows(
        self,
    ) -> CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlowsOutputReference:
        return typing.cast(CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlowsOutputReference, jsii.get(self, "advancedSecurityAdditionalFlows"))

    @builtins.property
    @jsii.member(jsii_name="advancedSecurityAdditionalFlowsInput")
    def advanced_security_additional_flows_input(
        self,
    ) -> typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows]:
        return typing.cast(typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows], jsii.get(self, "advancedSecurityAdditionalFlowsInput"))

    @builtins.property
    @jsii.member(jsii_name="advancedSecurityModeInput")
    def advanced_security_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "advancedSecurityModeInput"))

    @builtins.property
    @jsii.member(jsii_name="advancedSecurityMode")
    def advanced_security_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "advancedSecurityMode"))

    @advanced_security_mode.setter
    def advanced_security_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8d3259d4d4693813d36e6a3998ac3d0bc1b7e232d58007876cb6295d6a0711ee)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "advancedSecurityMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolUserPoolAddOns]:
        return typing.cast(typing.Optional[CognitoUserPoolUserPoolAddOns], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolUserPoolAddOns],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__81efa429d0217a3d53677b830bdd710bbb9d35c7263e539c6419fd255a4fc054)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUsernameConfiguration",
    jsii_struct_bases=[],
    name_mapping={"case_sensitive": "caseSensitive"},
)
class CognitoUserPoolUsernameConfiguration:
    def __init__(
        self,
        *,
        case_sensitive: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param case_sensitive: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#case_sensitive CognitoUserPool#case_sensitive}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b777c2bec6187ebc8aec5ead04cb1bbed70d9024c16ac25f267b07a9fc0353bf)
            check_type(argname="argument case_sensitive", value=case_sensitive, expected_type=type_hints["case_sensitive"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if case_sensitive is not None:
            self._values["case_sensitive"] = case_sensitive

    @builtins.property
    def case_sensitive(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#case_sensitive CognitoUserPool#case_sensitive}.'''
        result = self._values.get("case_sensitive")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolUsernameConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolUsernameConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolUsernameConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__aec4823f30ba1503a0adf3aafb506c44464ccf81fcb3ed82202a52b3f902b829)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCaseSensitive")
    def reset_case_sensitive(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCaseSensitive", []))

    @builtins.property
    @jsii.member(jsii_name="caseSensitiveInput")
    def case_sensitive_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "caseSensitiveInput"))

    @builtins.property
    @jsii.member(jsii_name="caseSensitive")
    def case_sensitive(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "caseSensitive"))

    @case_sensitive.setter
    def case_sensitive(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f91fe19e63950227a47ac4c1285901de82e133836f8aef8bca4362f1ade892c1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "caseSensitive", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolUsernameConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolUsernameConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolUsernameConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5036ebf0f2e82a8764c6c7376744b8a1bd5896a03330002fafa69c1d3c6ca9db)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolVerificationMessageTemplate",
    jsii_struct_bases=[],
    name_mapping={
        "default_email_option": "defaultEmailOption",
        "email_message": "emailMessage",
        "email_message_by_link": "emailMessageByLink",
        "email_subject": "emailSubject",
        "email_subject_by_link": "emailSubjectByLink",
        "sms_message": "smsMessage",
    },
)
class CognitoUserPoolVerificationMessageTemplate:
    def __init__(
        self,
        *,
        default_email_option: typing.Optional[builtins.str] = None,
        email_message: typing.Optional[builtins.str] = None,
        email_message_by_link: typing.Optional[builtins.str] = None,
        email_subject: typing.Optional[builtins.str] = None,
        email_subject_by_link: typing.Optional[builtins.str] = None,
        sms_message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param default_email_option: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#default_email_option CognitoUserPool#default_email_option}.
        :param email_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.
        :param email_message_by_link: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message_by_link CognitoUserPool#email_message_by_link}.
        :param email_subject: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.
        :param email_subject_by_link: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject_by_link CognitoUserPool#email_subject_by_link}.
        :param sms_message: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__19efb34d8c350cff53b4edbb81193aa640ec20273ccbc2d97a25d3f22a5c7c0a)
            check_type(argname="argument default_email_option", value=default_email_option, expected_type=type_hints["default_email_option"])
            check_type(argname="argument email_message", value=email_message, expected_type=type_hints["email_message"])
            check_type(argname="argument email_message_by_link", value=email_message_by_link, expected_type=type_hints["email_message_by_link"])
            check_type(argname="argument email_subject", value=email_subject, expected_type=type_hints["email_subject"])
            check_type(argname="argument email_subject_by_link", value=email_subject_by_link, expected_type=type_hints["email_subject_by_link"])
            check_type(argname="argument sms_message", value=sms_message, expected_type=type_hints["sms_message"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if default_email_option is not None:
            self._values["default_email_option"] = default_email_option
        if email_message is not None:
            self._values["email_message"] = email_message
        if email_message_by_link is not None:
            self._values["email_message_by_link"] = email_message_by_link
        if email_subject is not None:
            self._values["email_subject"] = email_subject
        if email_subject_by_link is not None:
            self._values["email_subject_by_link"] = email_subject_by_link
        if sms_message is not None:
            self._values["sms_message"] = sms_message

    @builtins.property
    def default_email_option(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#default_email_option CognitoUserPool#default_email_option}.'''
        result = self._values.get("default_email_option")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message CognitoUserPool#email_message}.'''
        result = self._values.get("email_message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_message_by_link(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_message_by_link CognitoUserPool#email_message_by_link}.'''
        result = self._values.get("email_message_by_link")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_subject(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject CognitoUserPool#email_subject}.'''
        result = self._values.get("email_subject")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def email_subject_by_link(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#email_subject_by_link CognitoUserPool#email_subject_by_link}.'''
        result = self._values.get("email_subject_by_link")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sms_message(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#sms_message CognitoUserPool#sms_message}.'''
        result = self._values.get("sms_message")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolVerificationMessageTemplate(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolVerificationMessageTemplateOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolVerificationMessageTemplateOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__9554b5700b1bcdc1d0318602fd1ce477c8fb288a560f71d881376d12654a462e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetDefaultEmailOption")
    def reset_default_email_option(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultEmailOption", []))

    @jsii.member(jsii_name="resetEmailMessage")
    def reset_email_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailMessage", []))

    @jsii.member(jsii_name="resetEmailMessageByLink")
    def reset_email_message_by_link(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailMessageByLink", []))

    @jsii.member(jsii_name="resetEmailSubject")
    def reset_email_subject(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailSubject", []))

    @jsii.member(jsii_name="resetEmailSubjectByLink")
    def reset_email_subject_by_link(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailSubjectByLink", []))

    @jsii.member(jsii_name="resetSmsMessage")
    def reset_sms_message(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSmsMessage", []))

    @builtins.property
    @jsii.member(jsii_name="defaultEmailOptionInput")
    def default_email_option_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultEmailOptionInput"))

    @builtins.property
    @jsii.member(jsii_name="emailMessageByLinkInput")
    def email_message_by_link_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailMessageByLinkInput"))

    @builtins.property
    @jsii.member(jsii_name="emailMessageInput")
    def email_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="emailSubjectByLinkInput")
    def email_subject_by_link_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailSubjectByLinkInput"))

    @builtins.property
    @jsii.member(jsii_name="emailSubjectInput")
    def email_subject_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emailSubjectInput"))

    @builtins.property
    @jsii.member(jsii_name="smsMessageInput")
    def sms_message_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "smsMessageInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultEmailOption")
    def default_email_option(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "defaultEmailOption"))

    @default_email_option.setter
    def default_email_option(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f2d0594bd0233ea6bfdb1f4ab77b7bfc3b916c34d7081e1fe03f63b4e8ed10f3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultEmailOption", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailMessage")
    def email_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailMessage"))

    @email_message.setter
    def email_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7a3ed56df2ac12034fb157316f045d5322bf65393c03ffbd0bc236a34b47c7d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailMessageByLink")
    def email_message_by_link(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailMessageByLink"))

    @email_message_by_link.setter
    def email_message_by_link(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__603fe5ff85d3c92eb09d392ad5705de01b9d34185e40c20f9eb8ccfa590587a9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailMessageByLink", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailSubject")
    def email_subject(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailSubject"))

    @email_subject.setter
    def email_subject(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa34992eaed729de68f598d95cdb380fb0da99c5bff2a44dc01a9b0fdcff3c77)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailSubject", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emailSubjectByLink")
    def email_subject_by_link(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emailSubjectByLink"))

    @email_subject_by_link.setter
    def email_subject_by_link(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8d6024a0f5c89b0871f4852e78d76e41b4addc3c72d680663f0d887b6ad0b2f5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailSubjectByLink", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="smsMessage")
    def sms_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "smsMessage"))

    @sms_message.setter
    def sms_message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3bf67ee526d13f739c3a5cf58562e108df539bc19779f1aee8fc89a5a2eb0116)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "smsMessage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[CognitoUserPoolVerificationMessageTemplate]:
        return typing.cast(typing.Optional[CognitoUserPoolVerificationMessageTemplate], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolVerificationMessageTemplate],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5f81f24449a18bde40a352922d1f6429aef9adfe655b16d23261a6ca94fd993a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolWebAuthnConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "relying_party_id": "relyingPartyId",
        "user_verification": "userVerification",
    },
)
class CognitoUserPoolWebAuthnConfiguration:
    def __init__(
        self,
        *,
        relying_party_id: typing.Optional[builtins.str] = None,
        user_verification: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param relying_party_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#relying_party_id CognitoUserPool#relying_party_id}.
        :param user_verification: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_verification CognitoUserPool#user_verification}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a366121dacf0b7bfd89c4a4f7e094395ed4032d01810381dd3884c6856fc3ef6)
            check_type(argname="argument relying_party_id", value=relying_party_id, expected_type=type_hints["relying_party_id"])
            check_type(argname="argument user_verification", value=user_verification, expected_type=type_hints["user_verification"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if relying_party_id is not None:
            self._values["relying_party_id"] = relying_party_id
        if user_verification is not None:
            self._values["user_verification"] = user_verification

    @builtins.property
    def relying_party_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#relying_party_id CognitoUserPool#relying_party_id}.'''
        result = self._values.get("relying_party_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_verification(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/hashicorp/aws/6.18.0/docs/resources/cognito_user_pool#user_verification CognitoUserPool#user_verification}.'''
        result = self._values.get("user_verification")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoUserPoolWebAuthnConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class CognitoUserPoolWebAuthnConfigurationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-aws.cognitoUserPool.CognitoUserPoolWebAuthnConfigurationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d13c184c63b4b8958d6bddf84ed3fc45651d6d1b959fa03a90855c843c386abf)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetRelyingPartyId")
    def reset_relying_party_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRelyingPartyId", []))

    @jsii.member(jsii_name="resetUserVerification")
    def reset_user_verification(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserVerification", []))

    @builtins.property
    @jsii.member(jsii_name="relyingPartyIdInput")
    def relying_party_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "relyingPartyIdInput"))

    @builtins.property
    @jsii.member(jsii_name="userVerificationInput")
    def user_verification_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userVerificationInput"))

    @builtins.property
    @jsii.member(jsii_name="relyingPartyId")
    def relying_party_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "relyingPartyId"))

    @relying_party_id.setter
    def relying_party_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a856bf71aa32e5cf6ac88dcc2b18f329ec54f49e341e2cd000a01c1c64d105bc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "relyingPartyId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userVerification")
    def user_verification(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userVerification"))

    @user_verification.setter
    def user_verification(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f7c5607d168f152c2d06648fd9c51e010de28105b4480b2c6e8e9bb684f3259e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userVerification", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[CognitoUserPoolWebAuthnConfiguration]:
        return typing.cast(typing.Optional[CognitoUserPoolWebAuthnConfiguration], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[CognitoUserPoolWebAuthnConfiguration],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c732c22d2be6f1282a362f727eacd4e550eccf475a8d4518f54ea5dccc828b5f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "CognitoUserPool",
    "CognitoUserPoolAccountRecoverySetting",
    "CognitoUserPoolAccountRecoverySettingOutputReference",
    "CognitoUserPoolAccountRecoverySettingRecoveryMechanism",
    "CognitoUserPoolAccountRecoverySettingRecoveryMechanismList",
    "CognitoUserPoolAccountRecoverySettingRecoveryMechanismOutputReference",
    "CognitoUserPoolAdminCreateUserConfig",
    "CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate",
    "CognitoUserPoolAdminCreateUserConfigInviteMessageTemplateOutputReference",
    "CognitoUserPoolAdminCreateUserConfigOutputReference",
    "CognitoUserPoolConfig",
    "CognitoUserPoolDeviceConfiguration",
    "CognitoUserPoolDeviceConfigurationOutputReference",
    "CognitoUserPoolEmailConfiguration",
    "CognitoUserPoolEmailConfigurationOutputReference",
    "CognitoUserPoolEmailMfaConfiguration",
    "CognitoUserPoolEmailMfaConfigurationOutputReference",
    "CognitoUserPoolLambdaConfig",
    "CognitoUserPoolLambdaConfigCustomEmailSender",
    "CognitoUserPoolLambdaConfigCustomEmailSenderOutputReference",
    "CognitoUserPoolLambdaConfigCustomSmsSender",
    "CognitoUserPoolLambdaConfigCustomSmsSenderOutputReference",
    "CognitoUserPoolLambdaConfigOutputReference",
    "CognitoUserPoolLambdaConfigPreTokenGenerationConfig",
    "CognitoUserPoolLambdaConfigPreTokenGenerationConfigOutputReference",
    "CognitoUserPoolPasswordPolicy",
    "CognitoUserPoolPasswordPolicyOutputReference",
    "CognitoUserPoolSchema",
    "CognitoUserPoolSchemaList",
    "CognitoUserPoolSchemaNumberAttributeConstraints",
    "CognitoUserPoolSchemaNumberAttributeConstraintsOutputReference",
    "CognitoUserPoolSchemaOutputReference",
    "CognitoUserPoolSchemaStringAttributeConstraints",
    "CognitoUserPoolSchemaStringAttributeConstraintsOutputReference",
    "CognitoUserPoolSignInPolicy",
    "CognitoUserPoolSignInPolicyOutputReference",
    "CognitoUserPoolSmsConfiguration",
    "CognitoUserPoolSmsConfigurationOutputReference",
    "CognitoUserPoolSoftwareTokenMfaConfiguration",
    "CognitoUserPoolSoftwareTokenMfaConfigurationOutputReference",
    "CognitoUserPoolUserAttributeUpdateSettings",
    "CognitoUserPoolUserAttributeUpdateSettingsOutputReference",
    "CognitoUserPoolUserPoolAddOns",
    "CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows",
    "CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlowsOutputReference",
    "CognitoUserPoolUserPoolAddOnsOutputReference",
    "CognitoUserPoolUsernameConfiguration",
    "CognitoUserPoolUsernameConfigurationOutputReference",
    "CognitoUserPoolVerificationMessageTemplate",
    "CognitoUserPoolVerificationMessageTemplateOutputReference",
    "CognitoUserPoolWebAuthnConfiguration",
    "CognitoUserPoolWebAuthnConfigurationOutputReference",
]

publication.publish()

def _typecheckingstub__df240343676b855452fad7604d73009e4e700668f14d3349a7b0a18dd56eb538(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    name: builtins.str,
    account_recovery_setting: typing.Optional[typing.Union[CognitoUserPoolAccountRecoverySetting, typing.Dict[builtins.str, typing.Any]]] = None,
    admin_create_user_config: typing.Optional[typing.Union[CognitoUserPoolAdminCreateUserConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    alias_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    auto_verified_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    deletion_protection: typing.Optional[builtins.str] = None,
    device_configuration: typing.Optional[typing.Union[CognitoUserPoolDeviceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_configuration: typing.Optional[typing.Union[CognitoUserPoolEmailConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_mfa_configuration: typing.Optional[typing.Union[CognitoUserPoolEmailMfaConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_verification_message: typing.Optional[builtins.str] = None,
    email_verification_subject: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    lambda_config: typing.Optional[typing.Union[CognitoUserPoolLambdaConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    mfa_configuration: typing.Optional[builtins.str] = None,
    password_policy: typing.Optional[typing.Union[CognitoUserPoolPasswordPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    region: typing.Optional[builtins.str] = None,
    schema: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[CognitoUserPoolSchema, typing.Dict[builtins.str, typing.Any]]]]] = None,
    sign_in_policy: typing.Optional[typing.Union[CognitoUserPoolSignInPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    sms_authentication_message: typing.Optional[builtins.str] = None,
    sms_configuration: typing.Optional[typing.Union[CognitoUserPoolSmsConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    sms_verification_message: typing.Optional[builtins.str] = None,
    software_token_mfa_configuration: typing.Optional[typing.Union[CognitoUserPoolSoftwareTokenMfaConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    user_attribute_update_settings: typing.Optional[typing.Union[CognitoUserPoolUserAttributeUpdateSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    username_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    username_configuration: typing.Optional[typing.Union[CognitoUserPoolUsernameConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    user_pool_add_ons: typing.Optional[typing.Union[CognitoUserPoolUserPoolAddOns, typing.Dict[builtins.str, typing.Any]]] = None,
    user_pool_tier: typing.Optional[builtins.str] = None,
    verification_message_template: typing.Optional[typing.Union[CognitoUserPoolVerificationMessageTemplate, typing.Dict[builtins.str, typing.Any]]] = None,
    web_authn_configuration: typing.Optional[typing.Union[CognitoUserPoolWebAuthnConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__da4182bd7d22389615b86ac1d38af4244548fb62e233d453b13a6ceeb876f56a(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3df549de1be02fcca6b32888adb3deaadf042cd53bc95b91306521b378014671(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[CognitoUserPoolSchema, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5761158faf48575e28b76ced29481fc7995d21870c91d3675301eac7e62c93d3(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__812379b6ac56f8afbe78658f70d43d897d068bdaf5956b89851359ed8329b82c(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04609a36de3026862a1ec7d5557f7e06442eafb1241df56da4c88e4ce0107f16(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9cff28db1c5219a513496e9df5e900d9a7405cc558bf23d26e9312c67e25f14a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b5e7496321573db876e51e7f5ccbb5f94397b052e2ab21b1805a76111ed5efd9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bb92134127d67495aae809ad29ee96723ae307bed2c8f8ca0348a2c90eb1754b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__88427b200ad90bec3f0546096e59abae3c4df05d3645c938f852b727efcc2147(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__358eee877ebe44397e7b2c50717c9bc5c5beb08aeab1de739703605a37bdb67d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec237e81a8820b85ba45473f5c871f4d1021331faaf66af0dd56f23e320669ba(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7b18415ebe9fd02c9d3f2b65769ab8dd6f29b2d7398c51b1e88b400b3c9e4834(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__521276d5268b6b2fe5ab1f221633d818acd5af228af69dc014c64ed004417da3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1fea4288ef68c5d7b6475308f2cd89f9e65793b74bbb9620edd2f21d20c510da(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__592e398830927c091a21273c9aabd962496de4284ce3b1d3fd6b4ea0c6f38290(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17a1ef1384bd83a0de8b95c3cf2a233a611fa51a3fecf1ef7d6890e7dbbc4c7f(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__139b1f8abdf690aa2fce25679c7293c50b77891a877b76204737b91f9aada0f6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__01d316b6cc0ef169f2fbb7c8a1ee57daa6fe8a64b3e77000917e9166f1c2664c(
    *,
    recovery_mechanism: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[CognitoUserPoolAccountRecoverySettingRecoveryMechanism, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__95c0f18485affdb8d77c449f2bb65e40cce486fcbbb20681592d418ab3775a80(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6b6e8dd7574be4a488925c472bc36e33aeb7291c4d1443bc5e7ab6ba5601a7a5(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[CognitoUserPoolAccountRecoverySettingRecoveryMechanism, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b0493289df5643906f8281fc5bafa23b5e688b9b03fcbc85d64af7d8616bac1(
    value: typing.Optional[CognitoUserPoolAccountRecoverySetting],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__06b536da76a1bdf3fe49c8e531d5cd2c1e1116015d7b5f07173f8663e613ee49(
    *,
    name: builtins.str,
    priority: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a0d4ff5e7917b4cbc435960968bf4353c142b5d8f9cf02e9b8aaf2ca9d1318b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54b5d9d424b4a821aa4e425d3d59b0504a2b35136f64010c613357ce2ed91f38(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7128bd667a6a4414db0c3db02de635878aa88d93da5ac1dcf551112289c635a1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f026757f40dd87c0e52beb91c3a1937768d633130970668a96399362a9e8089a(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__95a149622ba53a95a973b92d1ec238e20afc7f427c513033f00bb76cdf63256a(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a902a3a4252bad61489c416f3bf79c662e0b64d5476b0dd1116d16ff627c7737(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolAccountRecoverySettingRecoveryMechanism]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a664771da8e1028822db16625f6edaeaf3d523a275af50b0377227eb8740096e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a50aab5f5dd2bf66bdb28242bcd63e61681390fdd0e64deb34728b414d12fc6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__75a0aa44e7bf8b7b84c28e36e1f4eb9406b958ea588480a86e00c04743464cba(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__15d4f37fe6c6f39cd9dc816affd7510d7c8e3162b9bfa5cccd9db9a94e8aa0ce(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolAccountRecoverySettingRecoveryMechanism]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f1c43b01a94e36046f210602b39032377befeeb35319139a902fea6aef7e374(
    *,
    allow_admin_create_user_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    invite_message_template: typing.Optional[typing.Union[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__faccb36c29a7922678da7fc15b24d561753eedb0d21bb7b69a4d0fcd30f72cff(
    *,
    email_message: typing.Optional[builtins.str] = None,
    email_subject: typing.Optional[builtins.str] = None,
    sms_message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9fb7e398445292a8e32b1838bab38fc0510b79da4ed94f452b4367ff38493cb8(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eab063466194b9d8703150ecdd79c7cf5a86503e9fb13f50cefead8ea698885c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__081f45676b3efdc9eee3e41e3157a70b644ba58eeb0356b1a702babbe459c333(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__999b4ed36ccfddf5ecce0787d9ca354544702db8e510d66cf6ce90094d488ec9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dac387f3b27627a9283473866225cf17e502b8f92d88a5f52229cb2b78748aec(
    value: typing.Optional[CognitoUserPoolAdminCreateUserConfigInviteMessageTemplate],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__75efe294c70cf57e39b12f0e41241d800d36a954ca5089eb761588d8b2f1dcaf(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8763ec7278e3c89370e152982b89839d49a1f8e05f5fcaa0cf2eb732c934b89d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c6f43ca06e29cd4d2c8ccfc0eb3437312c6c0a8ded2e40b7b2235b2bea0d4584(
    value: typing.Optional[CognitoUserPoolAdminCreateUserConfig],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94bb316ae165be77901cf0a4fa060ea14afbce11881d59a4cd529d610caf01e1(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    name: builtins.str,
    account_recovery_setting: typing.Optional[typing.Union[CognitoUserPoolAccountRecoverySetting, typing.Dict[builtins.str, typing.Any]]] = None,
    admin_create_user_config: typing.Optional[typing.Union[CognitoUserPoolAdminCreateUserConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    alias_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    auto_verified_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    deletion_protection: typing.Optional[builtins.str] = None,
    device_configuration: typing.Optional[typing.Union[CognitoUserPoolDeviceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_configuration: typing.Optional[typing.Union[CognitoUserPoolEmailConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_mfa_configuration: typing.Optional[typing.Union[CognitoUserPoolEmailMfaConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    email_verification_message: typing.Optional[builtins.str] = None,
    email_verification_subject: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    lambda_config: typing.Optional[typing.Union[CognitoUserPoolLambdaConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    mfa_configuration: typing.Optional[builtins.str] = None,
    password_policy: typing.Optional[typing.Union[CognitoUserPoolPasswordPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    region: typing.Optional[builtins.str] = None,
    schema: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[CognitoUserPoolSchema, typing.Dict[builtins.str, typing.Any]]]]] = None,
    sign_in_policy: typing.Optional[typing.Union[CognitoUserPoolSignInPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    sms_authentication_message: typing.Optional[builtins.str] = None,
    sms_configuration: typing.Optional[typing.Union[CognitoUserPoolSmsConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    sms_verification_message: typing.Optional[builtins.str] = None,
    software_token_mfa_configuration: typing.Optional[typing.Union[CognitoUserPoolSoftwareTokenMfaConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags_all: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    user_attribute_update_settings: typing.Optional[typing.Union[CognitoUserPoolUserAttributeUpdateSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    username_attributes: typing.Optional[typing.Sequence[builtins.str]] = None,
    username_configuration: typing.Optional[typing.Union[CognitoUserPoolUsernameConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    user_pool_add_ons: typing.Optional[typing.Union[CognitoUserPoolUserPoolAddOns, typing.Dict[builtins.str, typing.Any]]] = None,
    user_pool_tier: typing.Optional[builtins.str] = None,
    verification_message_template: typing.Optional[typing.Union[CognitoUserPoolVerificationMessageTemplate, typing.Dict[builtins.str, typing.Any]]] = None,
    web_authn_configuration: typing.Optional[typing.Union[CognitoUserPoolWebAuthnConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6deb8e1117374362615ebc0a7b7f84fa98a0421f452923c0ed2dce4e1f8fedcd(
    *,
    challenge_required_on_new_device: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    device_only_remembered_on_user_prompt: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0041979c2a1b82b3ec1e6d7cd14f83882bd83af0eee20a3b00f2564aa4c70079(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c3a776eb6f067cd2ef34376bb526e9484dd0eec5be9c8f2047ce7bc706e44047(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eaa77464742c9bb4a379c2de01e91c90879bf5c724ae8d1b73763020685086bc(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8b0009f51eca5e804eb802fa1b5e100585a26f9d3400023697ebea6df57529fe(
    value: typing.Optional[CognitoUserPoolDeviceConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__af9a089de62fc519ccb0f39c0d75830a689c4b0f7f03b195ffa38fbb4b3c11a3(
    *,
    configuration_set: typing.Optional[builtins.str] = None,
    email_sending_account: typing.Optional[builtins.str] = None,
    from_email_address: typing.Optional[builtins.str] = None,
    reply_to_email_address: typing.Optional[builtins.str] = None,
    source_arn: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8d3d63a5174e6335b7ff1303256464c74e2e0764235d1f4b815fc0d77a9d3f8a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0e4dab689cd637a1993e6cda8fae3f7725561ee49f5b917637c41e308fdd972b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8711396f7a6886020a90aed8d68d8121b11663e20763714eff51b46e2eea75b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3c28a226eb8bdb726894ffe35ec5c8686a09772b7a0644ab794598a25993be3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__526a7a3e4e1c434db42ce62ce35f42425cb0ff3ad596c4f2239c49c701ef1186(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4566c62c29a3ad4a285f60f598973552df5190b42ff3ee3b172ea4f2f2ffe9f6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a4bd736f8f2200fde0bf6648a820679aa2c20d183ab4c65ec4c6fb3069bd1079(
    value: typing.Optional[CognitoUserPoolEmailConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a57d909da54e842ec409459d231409dc1686890d6c6173265e9511abda63f717(
    *,
    message: typing.Optional[builtins.str] = None,
    subject: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__66998ee793a843228eec17bf80bc4190e0e97d5e08e8773b8ce1635d11115fad(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__42e5a13b1887a17186f6f7362c05f7ad47e41ebc8863368d373bb6b917e4f8bd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d79cc3719c106a1cb7e15a798c192e0570eca22e11cb9e73d0754d6dfb059ac9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cb9c40ca51b42d99935c2990260202028ecd43b9de656e2bf744ccbabf04cc45(
    value: typing.Optional[CognitoUserPoolEmailMfaConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__60ce4783a7ebfe2aa03fcd1638b963b78e9f61357ec1970f574c47129e7d2822(
    *,
    create_auth_challenge: typing.Optional[builtins.str] = None,
    custom_email_sender: typing.Optional[typing.Union[CognitoUserPoolLambdaConfigCustomEmailSender, typing.Dict[builtins.str, typing.Any]]] = None,
    custom_message: typing.Optional[builtins.str] = None,
    custom_sms_sender: typing.Optional[typing.Union[CognitoUserPoolLambdaConfigCustomSmsSender, typing.Dict[builtins.str, typing.Any]]] = None,
    define_auth_challenge: typing.Optional[builtins.str] = None,
    kms_key_id: typing.Optional[builtins.str] = None,
    post_authentication: typing.Optional[builtins.str] = None,
    post_confirmation: typing.Optional[builtins.str] = None,
    pre_authentication: typing.Optional[builtins.str] = None,
    pre_sign_up: typing.Optional[builtins.str] = None,
    pre_token_generation: typing.Optional[builtins.str] = None,
    pre_token_generation_config: typing.Optional[typing.Union[CognitoUserPoolLambdaConfigPreTokenGenerationConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    user_migration: typing.Optional[builtins.str] = None,
    verify_auth_challenge_response: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__32954a28110eb8412cf1f25dbe1d02f3975d0f1df4396ae6543def087f085e22(
    *,
    lambda_arn: builtins.str,
    lambda_version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3abdc2877f678c48a97131c2ad5b08d74f74f084a647ed4118f61715cee9133(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb9ff17acec8885dcc85535c1a33d1579a3d5eb1823c40e85c6d6148918f7ec7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04105a2fe25c4d1c71c3c901787b3dc28e2ac4adb4b7f875f4296de107b21f5d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__450240547b4d5a97c6a33dd4dfdd25d730e1988959c2a9481b4e0e2ca7eec28b(
    value: typing.Optional[CognitoUserPoolLambdaConfigCustomEmailSender],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__83fb63b7b3b720a5ec597135c314d10891c44b71446e8e4793145d03cf5d6eb8(
    *,
    lambda_arn: builtins.str,
    lambda_version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce0a94ecebe029f57704bcbfd4be03beb8e0561df40dbab44e89db83bfebc7ae(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec1db8cbd9058bccce72d5573276080b5c5f821742ae328f2c6ec756da65e495(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dfbaf96994229d0c184d0b9aab04471a32c6a70be0dcf4997cf58114ee93c9d9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d23037ddd71d0f77a8520042931bb4f58118d96aa18187ae85e6b2f55df1359(
    value: typing.Optional[CognitoUserPoolLambdaConfigCustomSmsSender],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8c65c34d46d64b75eb55e4d7da2b43c07d80e261638d601f66d5cd4f144d6e30(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a41f0873951eef36d9c4fd0933eeff6db4cccb899ce841506609d6975e22979(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04d9b61706477b18a579f37aa5b0f4c26044ce7f165220b17e96644d3977c735(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee4c396b776a36a3faa783d4e041af813847cc30e1b669f8f3239991de91993a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4a5667dce77f54c66dc7ee44c7230e25750a12c39c29e07980080f8030389533(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d2202e3bfba0354c245b9d6fa35814de4f3288cff1c7644d690a342fd9739ef(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__41b546c3f94339d3734bd79cc102e555bf6ec41eb7187458ed11f6ceea656ca1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cb3881906cc6f67522ce323b46c15810bbc098b3b42f992b12cf8fba3b3f79f8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8bff3b03b37b6d549c96cce69cb6397354d3f52201c70c620f062005d7936580(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4e1cb2acf587d8ef3a61df099341dff0728ae0419a6bcf59b8ddf53db3c58449(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f7da50c87e20720d550a7e9eb58051d931d07e96eeff3b635ad4f91c9fcfaa7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ded3ef2c17f8a3a672617c66e26030a90ea49f87530c8c1c7fe5e19e91e8aa59(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bceffa3f5e30c89b485c4e47ca30e39fb173d7b1ac5a1e9d411595e5973333be(
    value: typing.Optional[CognitoUserPoolLambdaConfig],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b30bd6e85f60789417764d86c167a555093880112f253f73dada4e3fee0e566e(
    *,
    lambda_arn: builtins.str,
    lambda_version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1375f7ccbef0898c067a70c708a1dc5b5da254f6c35b7c96f2bc14cd95da2ac(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bf247518d7cf37a0f4f4e8cf8f209553f81e64648bc4d3e8d98bb4c4bdc3790d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__547735dd9f63b8dfb36727da8a116585202346bb460d66688f727701b943a666(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__18f459ec1768d95a3396cc6c34918f2a458c84a82ca170c91027df447f6eaf7d(
    value: typing.Optional[CognitoUserPoolLambdaConfigPreTokenGenerationConfig],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__631a46f60f7494ed7d5ef6ba5879ce6ecc7723e2d9b0d704c26e243c14b05073(
    *,
    minimum_length: typing.Optional[jsii.Number] = None,
    password_history_size: typing.Optional[jsii.Number] = None,
    require_lowercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    require_numbers: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    require_symbols: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    require_uppercase: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    temporary_password_validity_days: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__83e9dda3ed2fb16e9180ae7124628863a14e7586b6bc52e29ab121fec41df344(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__007f59030a469416aa8cd065cefba864fd39f60347a29a11dd07d4bb8c536d43(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8871e155b8b666da538fff4776281fed63f105d290c4cca92fd55193c47b91b2(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c371dbec963cb05ca4e3343f76c36854f321669bf86bddcc91e1483be5ba35ab(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b122c77f73f9328f8699075a3b4cfd12eb6e5a2b5225d272ee07686bdbe0186d(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d27f50051cac084d561cf60727af25a0f4ae5413cbf04101b6b26f8cc28c8d50(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__356214cf60070ea22d866ac913062f67cfb9da1816ae259a8a14f6172891a788(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e47d3a12bb72e93aab94419acff015f2779e584422e9ef2bb42bfa11a54664d6(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__411118f0bed8f2622fa78e7be9c91d373cd44197eb1d5e45bb3e543dd77613bf(
    value: typing.Optional[CognitoUserPoolPasswordPolicy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4ac428a45c7eedbd44d04a1f9cc9afb69a23417beeead59d53553ce735a8c69(
    *,
    attribute_data_type: builtins.str,
    name: builtins.str,
    developer_only_attribute: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    mutable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    number_attribute_constraints: typing.Optional[typing.Union[CognitoUserPoolSchemaNumberAttributeConstraints, typing.Dict[builtins.str, typing.Any]]] = None,
    required: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    string_attribute_constraints: typing.Optional[typing.Union[CognitoUserPoolSchemaStringAttributeConstraints, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad76fd9610f1b6fe0faefce60ba0bc305e470c43f1bceab59bfc8bb6e82595d2(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4565a2ed22310b1aa3b8ce1a17402e75b45e6e0b41495539e8b1c02f08c5f142(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__771ce5e3ff8fca87c9a5742aa9a3195ba6a1db8347cd9810e4638c101b94ee0d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c6493e42346562296ff295fa3615d72f0a6f8bf3cd922fbb3ea45cceaae47c4(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9e9b19ed23c37f7c3f87fea35e546009b2741d7ba372b7dc38b7e62a2424d009(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__067cd7ee6915dcabbedfada1cb549ac3208f9ba9388df5ad44f64b25bf074728(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[CognitoUserPoolSchema]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7cb7eee32db8cce6e32749e30825a808d9b036dc3f55e24c01b250deb7131310(
    *,
    max_value: typing.Optional[builtins.str] = None,
    min_value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6cdf511dee892ae69f5300f6f038832e62179a29ef77cc6e77b246853f9397b3(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f528f2bbac0627208bfd228b155dac06f19d5fb8a0b62237c0a9e16f8f0ac002(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eac49b032239e6643a473752787efb237a1da162a9738db44813974a61e345a4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__15aa5c3b961638d330289b28774de20c3609fb8ee89989f853b873fef10974ef(
    value: typing.Optional[CognitoUserPoolSchemaNumberAttributeConstraints],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aa2a92c9b6042d284b8672dd7a278989488abbbbc3c137f1a176461c74af04cf(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1ff4648e1e648f7051f46a4c31047bcd31a7261979fe8527e606411e76a412b1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e045fb62b5880e6658c8070518a7fa13d3cbd55a10ed0e7964bccffe9334a34(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d1928a11737882c0689b8a99194095fd313932f5025f3cad5a5f0399bb631e0e(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2badf4cb530da930cbc79d29d51f44a1e1a8c066f649274c5796336972e04165(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2cef8c93eb8dd9f03170e5690e6bf60a6e9a59bf09d5f72ba709c0e71ae07b08(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__25c2df1b32bd9b8ce4a9be1fb731bad17eb7aeeffec67007461ac91170977072(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, CognitoUserPoolSchema]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0164f8aca70fbc1cdf462a19b4c8e2003c0c5c081d20931247a25514de66be7(
    *,
    max_length: typing.Optional[builtins.str] = None,
    min_length: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb1171489c0fb9ca819d0f4ffca2043ad6c0e1155cca6665508f80402c3d1099(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__236d3e61948af380022a243f2eb73a9f0330b66e40fba23da816e4c711da11c5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d4222efbcd7cca9e9eaec7a663e69ba2b8e7a7600e345a3be02e03595a9c2a4c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__890fe6dbfc0ad939efa83e4e2791a643223bdb12873558e33b042fc422716d12(
    value: typing.Optional[CognitoUserPoolSchemaStringAttributeConstraints],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40399343ba18eb846c16e68fb429760c59f71a7a01aa95040f180c0c621ddc0a(
    *,
    allowed_first_auth_factors: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d113e5c0ee6f6fbc750ab47bfd7ae9198c1b01ed2692673f5509bd89722931a6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__87f076bc345f75d85e627c53c7a530211fdd23b5be71c8f63419e53ab89e4534(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__44f25df28ff137231337683e8d69a2f1e47c84d2e792b4c7bf12ae679f424949(
    value: typing.Optional[CognitoUserPoolSignInPolicy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__098b42fa7a0f77d8ce0802e08befdfefe8fdde139ec7ec4cfee931d8570dd080(
    *,
    external_id: builtins.str,
    sns_caller_arn: builtins.str,
    sns_region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70123940b5a0f22222de00ecff9eeb5d6b3e81563bed4abcc65223bede4e4053(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a2df6638131dd5324b9c85abb20b5899d59b8a46e8de518f576086226442c1d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f7007ff3da4456bc7b31f4f332989befc14cbb545629cc1c210d357d26354e22(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0c23c63ce7632ce9d6d4f7f53a1618c59c7a12015d84bb7844176bb5d31c2968(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__85a6ad7b5a969f6f9c24d070f00709814e42176ca3f0e8121444867a0154b915(
    value: typing.Optional[CognitoUserPoolSmsConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa997d41c5680ae0a4860a332ba7be63a079caeea0a56b28692b4ec2be9fcdfa(
    *,
    enabled: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e38b13b3d04c6e50b5f1b7d6e21c1cbbf534b47c09df723ff2e32c1f8747710(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__81175d239f9439e94d912d4147866217125b196d372cde9fc3359239625a6022(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5abd8988d319a272038bb3c171ba4ab8869ee0d4ccf35194b6ee03d8b1a6a56a(
    value: typing.Optional[CognitoUserPoolSoftwareTokenMfaConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2eac78eb7a3ffe7c99bc37d96361b490f95178d3cf97311500388ddc278ac0b6(
    *,
    attributes_require_verification_before_update: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b87db15acbcfd810d48fc890aeb522ac4ee652599de90ebb476a674268fec049(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__365edbfd2ce875b81cb77dc8dd99b502a21c268c65e0cafe58d00f0619b3942a(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b09fbad1e9b7e4919b836a8a10fff35f3afca0231a4d585b5f4823db2688fd22(
    value: typing.Optional[CognitoUserPoolUserAttributeUpdateSettings],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a981ae45e5c2957680ce1240804ceb84b62f1cabbe4978884b986b2d88d30ce(
    *,
    advanced_security_mode: builtins.str,
    advanced_security_additional_flows: typing.Optional[typing.Union[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b09ed9ee763732398a9b7a22ec2984722142eb8394ab12c0e0700fb14bead1e5(
    *,
    custom_auth_mode: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b0f910675c3caeae1aa34a1b1da817f562401e589054c9b5986206da14c1058(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3acd0cdf37afae2efbee5578c3f70f94d07a353f11a9a335b59989aefc62ae8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6bc995e031f6b7c90945da6a168ece90026b0e396662a77cf2780fe12c8eaa3(
    value: typing.Optional[CognitoUserPoolUserPoolAddOnsAdvancedSecurityAdditionalFlows],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1b7b7850d0043fb6afb29ac123ac726f52c7c47ebd08ddf518aea9a9f74a219d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8d3259d4d4693813d36e6a3998ac3d0bc1b7e232d58007876cb6295d6a0711ee(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__81efa429d0217a3d53677b830bdd710bbb9d35c7263e539c6419fd255a4fc054(
    value: typing.Optional[CognitoUserPoolUserPoolAddOns],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b777c2bec6187ebc8aec5ead04cb1bbed70d9024c16ac25f267b07a9fc0353bf(
    *,
    case_sensitive: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aec4823f30ba1503a0adf3aafb506c44464ccf81fcb3ed82202a52b3f902b829(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f91fe19e63950227a47ac4c1285901de82e133836f8aef8bca4362f1ade892c1(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5036ebf0f2e82a8764c6c7376744b8a1bd5896a03330002fafa69c1d3c6ca9db(
    value: typing.Optional[CognitoUserPoolUsernameConfiguration],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__19efb34d8c350cff53b4edbb81193aa640ec20273ccbc2d97a25d3f22a5c7c0a(
    *,
    default_email_option: typing.Optional[builtins.str] = None,
    email_message: typing.Optional[builtins.str] = None,
    email_message_by_link: typing.Optional[builtins.str] = None,
    email_subject: typing.Optional[builtins.str] = None,
    email_subject_by_link: typing.Optional[builtins.str] = None,
    sms_message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9554b5700b1bcdc1d0318602fd1ce477c8fb288a560f71d881376d12654a462e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f2d0594bd0233ea6bfdb1f4ab77b7bfc3b916c34d7081e1fe03f63b4e8ed10f3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7a3ed56df2ac12034fb157316f045d5322bf65393c03ffbd0bc236a34b47c7d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__603fe5ff85d3c92eb09d392ad5705de01b9d34185e40c20f9eb8ccfa590587a9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa34992eaed729de68f598d95cdb380fb0da99c5bff2a44dc01a9b0fdcff3c77(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8d6024a0f5c89b0871f4852e78d76e41b4addc3c72d680663f0d887b6ad0b2f5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3bf67ee526d13f739c3a5cf58562e108df539bc19779f1aee8fc89a5a2eb0116(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5f81f24449a18bde40a352922d1f6429aef9adfe655b16d23261a6ca94fd993a(
    value: typing.Optional[CognitoUserPoolVerificationMessageTemplate],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a366121dacf0b7bfd89c4a4f7e094395ed4032d01810381dd3884c6856fc3ef6(
    *,
    relying_party_id: typing.Optional[builtins.str] = None,
    user_verification: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d13c184c63b4b8958d6bddf84ed3fc45651d6d1b959fa03a90855c843c386abf(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a856bf71aa32e5cf6ac88dcc2b18f329ec54f49e341e2cd000a01c1c64d105bc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f7c5607d168f152c2d06648fd9c51e010de28105b4480b2c6e8e9bb684f3259e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c732c22d2be6f1282a362f727eacd4e550eccf475a8d4518f54ea5dccc828b5f(
    value: typing.Optional[CognitoUserPoolWebAuthnConfiguration],
) -> None:
    """Type checking stubs"""
    pass
