r'''
# CDK EC2 Key Pair

[![Source](https://img.shields.io/badge/Source-GitHub-blue?logo=github)](https://github.com/udondan/cdk-ec2-key-pair)
[![Test](https://github.com/udondan/cdk-ec2-key-pair/workflows/Test/badge.svg)](https://github.com/udondan/cdk-ec2-key-pair/actions?query=workflow%3ATest)
[![GitHub](https://img.shields.io/github/license/udondan/cdk-ec2-key-pair)](https://github.com/udondan/cdk-ec2-key-pair/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/Construct%20Hub-cdk--ec2--key--pair-orange)](https://constructs.dev/packages/cdk-ec2-key-pair)

[![npm package](https://img.shields.io/npm/v/cdk-ec2-key-pair?color=brightgreen)](https://www.npmjs.com/package/cdk-ec2-key-pair)
[![PyPI package](https://img.shields.io/pypi/v/cdk-ec2-key-pair?color=brightgreen)](https://pypi.org/project/cdk-ec2-key-pair/)

![Downloads](https://img.shields.io/badge/-DOWNLOADS:-brightgreen?color=gray)
[![npm](https://img.shields.io/npm/dt/cdk-ec2-key-pair?label=npm&color=blueviolet)](https://www.npmjs.com/package/cdk-ec2-key-pair)
[![PyPI](https://img.shields.io/pypi/dm/cdk-ec2-key-pair?label=pypi&color=blueviolet)](https://pypi.org/project/cdk-ec2-key-pair/)

[AWS CDK](https://aws.amazon.com/cdk/) L3 construct for managing [EC2 Key Pairs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).

Manages RSA and ED25519 Key Pairs in EC2 through a Lambda function.

Support for public key format in:

* OpenSSH
* ssh
* PEM
* PKCS#1
* PKCS#8
* RFC4253 (Base64 encoded)
* PuTTY ppk

> [!NOTE]
> Please be aware, CloudFormation now natively supports creating EC2 Key Pairs via [AWS::EC2::KeyPair](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-keypair.html), so you can generally use [CDK's own KeyPair construct](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.KeyPair.html). There are a few differences, though, and this is why the custom construct remains valuable:
>
> * Instead of SSM Parameter Store, keys are stored in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
> * Secrets can be **KMS encrypted** - even different KMS keys for the private and public keys. Of course, SSM parameters *can* be encrypted too, CloudFormation just doesn't do it
> * Optionally, this construct can store and expose the public key, enabling the user to directly use it as input for other resources, e.g. for CloudFront signed urls

## Installation

This package has peer dependencies, which need to be installed along in the expected version.

For TypeScript/NodeJS, add these to your `dependencies` in `package.json`. For Python, add these to your `requirements.txt`:

* cdk-ec2-key-pair
* aws-cdk-lib (^2.116.0)
* constructs (^10.0.0)

## Usage

```python
import cdk = require('aws-cdk-lib');
import { Construct } from 'constructs';
import { KeyPair } from 'cdk-ec2-key-pair';

// ...

// Create the Key Pair
const key = new KeyPair(this, 'A-Key-Pair', {
  keyPairName: 'a-key-pair',
  description: 'This is a Key Pair',
  storePublicKey: true, // by default the public key will not be stored in Secrets Manager
});

// Grant read access to the private key to a role or user
key.grantReadOnPrivateKey(someRole);

// Grant read access to the public key to another role or user
key.grantReadOnPublicKey(anotherRole);

// Use Key Pair on an EC2 instance
new ec2.Instance(this, 'An-Instance', {
  keyPair: key,
  // ...
});
```

The private (and optionally the public) key will be stored in AWS Secrets Manager. The secret names by default are prefixed with `ec2-ssh-key/`. The private key is suffixed with `/private`, the public key is suffixed with `/public`. So in this example they will be stored as `ec2-ssh-key/a-key-pair/private` and `ec2-ssh-key/a-key-pair/public`.

To download the private key via AWS cli you can run:

```bash
aws secretsmanager get-secret-value \
  --secret-id ec2-ssh-key/a-key-pair/private \
  --query SecretString \
  --output text
```

### Tag support

The construct supports tagging:

```python
cdk.Tags.of(key).add('someTag', 'some value');
```

We also use tags to restrict update/delete actions to those, the construct created itself. The Lambda function, which backs the custom CFN resource, is not able to manipulate other keys/secrets. The tag we use for identifying these resources is `CreatedByCfnCustomResource` with value `CFN::Resource::Custom::EC2-Key-Pair`.

### Updates

Since an EC2 KeyPair cannot be updated, you cannot change any property related to the KeyPair. The code has checks in place which will prevent any attempt to do so. If you try, the stack will end in a failed state. In that case you can safely continue the rollback in the AWS console and ignore the key resource.

You can, however, change properties that only relate to the secrets. These are the KMS keys used for encryption, the `secretPrefix`, `description` and `removeKeySecretsAfterDays`.

### Encryption

Secrets in the AWS Secrets Manager by default are encrypted with the key `alias/aws/secretsmanager`.

To use a custom KMS key you can pass it to the Key Pair:

```python
const kmsKey = new kms.Key(this, 'KMS-key');

const keyPair = new KeyPair(this, 'A-Key-Pair', {
  keyPairName: 'a-key-pair',
  kms: kmsKey,
});
```

This KMS key needs to be created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified.

To use different KMS keys for the private and public key, use the `kmsPrivateKey` and `kmsPublicKey` instead:

```python
const kmsKeyPrivate = new kms.Key(this, 'KMS-key-private');
const kmsKeyPublic = new kms.Key(this, 'KMS-key-public');

const keyPair = new KeyPair(this, 'A-Key-Pair', {
  keyPairName: 'a-key-pair',
  kmsPrivateKey: kmsKeyPrivate,
  kmsPublicKey: kmsKeyPublic,
});
```

### Importing public key

You can create a key pair by importing the public key. Obviously, in this case the private key won't be available in secrets manager.

The public key has to be in OpenSSH format.

```python
new KeyPair(this, 'Test-Key-Pair', {
  keyPairName: 'imported-key-pair',
  publicKey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuMmbK...',
});
```

### Using the key pair for CloudFront signed url/cookies

You can use this library for generating keys for CloudFront signed url/cookies.

Make sure to set `publicKeyFormat` to `PublicKeyFormat.PEM` as that is the format required for CloudFront.
You also have to set `exposePublicKey` to `true` so you can actually get the public key.

```python
const key = new KeyPair(this, 'Signing-Key-Pair', {
  keyPairName: 'CFN-signing-key',
  exposePublicKey: true,
  storePublicKey: true,
  publicKeyFormat: PublicKeyFormat.PEM,
});

const pubKey = new cloudfront.PublicKey(this, 'Signing-Public-Key', {
  encodedKey: key.publicKeyValue,
});
const trustedKeyGroupForCF = new cloudfront.KeyGroup(
  this,
  'Signing-Key-Group',
  {
    items: [pubKey],
  },
);
```
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

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.implements(_aws_cdk_ceddda9d.ITaggable, _aws_cdk_aws_ec2_ceddda9d.IKeyPair)
class KeyPair(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-ec2-key-pair.KeyPair",
):
    '''An EC2 Key Pair.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        key_pair_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        expose_public_key: typing.Optional[builtins.bool] = None,
        key_type: typing.Optional["KeyType"] = None,
        kms: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        kms_private_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        kms_public_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        legacy_lambda_name: typing.Optional[builtins.bool] = None,
        log_level: typing.Optional["LogLevel"] = None,
        public_key: typing.Optional[builtins.str] = None,
        public_key_format: typing.Optional["PublicKeyFormat"] = None,
        remove_key_secrets_after_days: typing.Optional[jsii.Number] = None,
        resource_prefix: typing.Optional[builtins.str] = None,
        secret_prefix: typing.Optional[builtins.str] = None,
        store_public_key: typing.Optional[builtins.bool] = None,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Defines a new EC2 Key Pair.

        The private key will be stored in AWS Secrets Manager

        :param scope: -
        :param id: -
        :param key_pair_name: Name of the Key Pair. In AWS Secrets Manager the key will be prefixed with ``ec2-ssh-key/``. The name can be up to 255 characters long. Valid characters include _, -, a-z, A-Z, and 0-9.
        :param description: The description for the key in AWS Secrets Manager. Default: - ''
        :param expose_public_key: Expose the public key as property ``publicKeyValue``. Default: - false
        :param key_type: The type of key pair. Default: - RSA
        :param kms: The KMS key used to encrypt the Secrets Manager secrets with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. Default: - ``alias/aws/secretsmanager``
        :param kms_private_key: The KMS key to use to encrypt the private key with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. If no value is provided, the property ``kms`` will be used instead. Default: - ``this.kms``
        :param kms_public_key: The KMS key to use to encrypt the public key with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. If no value is provided, the property ``kms`` will be used instead. Default: - ``this.kms``
        :param legacy_lambda_name: Whether to use the legacy name for the Lambda function, which backs the custom resource. Starting with v4 of this package, the Lambda function by default has no longer a fixed name. If you migrate from v3 to v4, you need to set this to ``true`` as CloudFormation does not allow to change the name of the Lambda function used by custom resource. Default: false
        :param log_level: The log level of the Lambda function. Default: LogLevel.warn
        :param public_key: Import a public key instead of creating it. If no public key is provided, a new key pair will be created.
        :param public_key_format: Format for public key. Relevant only if the public key is stored and/or exposed. Default: - SSH
        :param remove_key_secrets_after_days: When the resource is destroyed, after how many days the private and public key in the AWS Secrets Manager should be deleted. Valid values are 0 and 7 to 30 Default: 0
        :param resource_prefix: A prefix for all resource names. By default all resources are prefixed with the stack name to avoid collisions with other stacks. This might cause problems when you work with long stack names and can be overridden through this parameter. Default: Name of the stack
        :param secret_prefix: Prefix for the secret in AWS Secrets Manager. Default: ``ec2-ssh-key/``
        :param store_public_key: Store the public key as a secret. Default: - false
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba97debf8723cff0eacba3e749a5826e9370b73123b213e1fa59471c93b71ea5)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = KeyPairProps(
            key_pair_name=key_pair_name,
            description=description,
            expose_public_key=expose_public_key,
            key_type=key_type,
            kms=kms,
            kms_private_key=kms_private_key,
            kms_public_key=kms_public_key,
            legacy_lambda_name=legacy_lambda_name,
            log_level=log_level,
            public_key=public_key,
            public_key_format=public_key_format,
            remove_key_secrets_after_days=remove_key_secrets_after_days,
            resource_prefix=resource_prefix,
            secret_prefix=secret_prefix,
            store_public_key=store_public_key,
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="grantReadOnPrivateKey")
    def grant_read_on_private_key(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''Grants read access to the private key in AWS Secrets Manager.

        :param grantee: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__674c4c11f9a0efc44319ec27788cc4dd19ef981f1274b3a1fa5bc1232076e555)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantReadOnPrivateKey", [grantee]))

    @jsii.member(jsii_name="grantReadOnPublicKey")
    def grant_read_on_public_key(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''Grants read access to the public key in AWS Secrets Manager.

        :param grantee: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5b040bc4a9ad1d5cf8873edf241be4da5e7699b7c1ccdc1cbaea4a0d78398297)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantReadOnPublicKey", [grantee]))

    @builtins.property
    @jsii.member(jsii_name="keyPairFingerprint")
    def key_pair_fingerprint(self) -> builtins.str:
        '''Fingerprint of the Key Pair.'''
        return typing.cast(builtins.str, jsii.get(self, "keyPairFingerprint"))

    @builtins.property
    @jsii.member(jsii_name="keyPairID")
    def key_pair_id(self) -> builtins.str:
        '''ID of the Key Pair.'''
        return typing.cast(builtins.str, jsii.get(self, "keyPairID"))

    @builtins.property
    @jsii.member(jsii_name="keyPairName")
    def key_pair_name(self) -> builtins.str:
        '''Name of the Key Pair.'''
        return typing.cast(builtins.str, jsii.get(self, "keyPairName"))

    @builtins.property
    @jsii.member(jsii_name="keyPairRef")
    def key_pair_ref(self) -> _aws_cdk_aws_ec2_ceddda9d.KeyPairReference:
        '''A reference to a KeyPair resource.'''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.KeyPairReference, jsii.get(self, "keyPairRef"))

    @builtins.property
    @jsii.member(jsii_name="keyType")
    def key_type(self) -> "KeyType":
        '''Type of the Key Pair.'''
        return typing.cast("KeyType", jsii.get(self, "keyType"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.IFunction:
        '''The lambda function that is created.'''
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.IFunction, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="prefix")
    def prefix(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "prefix"))

    @builtins.property
    @jsii.member(jsii_name="privateKeyArn")
    def private_key_arn(self) -> builtins.str:
        '''ARN of the private key in AWS Secrets Manager.'''
        return typing.cast(builtins.str, jsii.get(self, "privateKeyArn"))

    @builtins.property
    @jsii.member(jsii_name="publicKeyArn")
    def public_key_arn(self) -> builtins.str:
        '''ARN of the public key in AWS Secrets Manager.'''
        return typing.cast(builtins.str, jsii.get(self, "publicKeyArn"))

    @builtins.property
    @jsii.member(jsii_name="publicKeyFormat")
    def public_key_format(self) -> "PublicKeyFormat":
        '''Format of the public key.'''
        return typing.cast("PublicKeyFormat", jsii.get(self, "publicKeyFormat"))

    @builtins.property
    @jsii.member(jsii_name="publicKeyValue")
    def public_key_value(self) -> builtins.str:
        '''The public key.

        Only filled, when ``exposePublicKey = true``
        '''
        return typing.cast(builtins.str, jsii.get(self, "publicKeyValue"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> _aws_cdk_ceddda9d.TagManager:
        '''Resource tags.'''
        return typing.cast(_aws_cdk_ceddda9d.TagManager, jsii.get(self, "tags"))


@jsii.data_type(
    jsii_type="cdk-ec2-key-pair.KeyPairProps",
    jsii_struct_bases=[_aws_cdk_ceddda9d.ResourceProps],
    name_mapping={
        "account": "account",
        "environment_from_arn": "environmentFromArn",
        "physical_name": "physicalName",
        "region": "region",
        "key_pair_name": "keyPairName",
        "description": "description",
        "expose_public_key": "exposePublicKey",
        "key_type": "keyType",
        "kms": "kms",
        "kms_private_key": "kmsPrivateKey",
        "kms_public_key": "kmsPublicKey",
        "legacy_lambda_name": "legacyLambdaName",
        "log_level": "logLevel",
        "public_key": "publicKey",
        "public_key_format": "publicKeyFormat",
        "remove_key_secrets_after_days": "removeKeySecretsAfterDays",
        "resource_prefix": "resourcePrefix",
        "secret_prefix": "secretPrefix",
        "store_public_key": "storePublicKey",
    },
)
class KeyPairProps(_aws_cdk_ceddda9d.ResourceProps):
    def __init__(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
        key_pair_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        expose_public_key: typing.Optional[builtins.bool] = None,
        key_type: typing.Optional["KeyType"] = None,
        kms: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        kms_private_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        kms_public_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        legacy_lambda_name: typing.Optional[builtins.bool] = None,
        log_level: typing.Optional["LogLevel"] = None,
        public_key: typing.Optional[builtins.str] = None,
        public_key_format: typing.Optional["PublicKeyFormat"] = None,
        remove_key_secrets_after_days: typing.Optional[jsii.Number] = None,
        resource_prefix: typing.Optional[builtins.str] = None,
        secret_prefix: typing.Optional[builtins.str] = None,
        store_public_key: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Definition of EC2 Key Pair.

        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        :param key_pair_name: Name of the Key Pair. In AWS Secrets Manager the key will be prefixed with ``ec2-ssh-key/``. The name can be up to 255 characters long. Valid characters include _, -, a-z, A-Z, and 0-9.
        :param description: The description for the key in AWS Secrets Manager. Default: - ''
        :param expose_public_key: Expose the public key as property ``publicKeyValue``. Default: - false
        :param key_type: The type of key pair. Default: - RSA
        :param kms: The KMS key used to encrypt the Secrets Manager secrets with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. Default: - ``alias/aws/secretsmanager``
        :param kms_private_key: The KMS key to use to encrypt the private key with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. If no value is provided, the property ``kms`` will be used instead. Default: - ``this.kms``
        :param kms_public_key: The KMS key to use to encrypt the public key with. This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified. If no value is provided, the property ``kms`` will be used instead. Default: - ``this.kms``
        :param legacy_lambda_name: Whether to use the legacy name for the Lambda function, which backs the custom resource. Starting with v4 of this package, the Lambda function by default has no longer a fixed name. If you migrate from v3 to v4, you need to set this to ``true`` as CloudFormation does not allow to change the name of the Lambda function used by custom resource. Default: false
        :param log_level: The log level of the Lambda function. Default: LogLevel.warn
        :param public_key: Import a public key instead of creating it. If no public key is provided, a new key pair will be created.
        :param public_key_format: Format for public key. Relevant only if the public key is stored and/or exposed. Default: - SSH
        :param remove_key_secrets_after_days: When the resource is destroyed, after how many days the private and public key in the AWS Secrets Manager should be deleted. Valid values are 0 and 7 to 30 Default: 0
        :param resource_prefix: A prefix for all resource names. By default all resources are prefixed with the stack name to avoid collisions with other stacks. This might cause problems when you work with long stack names and can be overridden through this parameter. Default: Name of the stack
        :param secret_prefix: Prefix for the secret in AWS Secrets Manager. Default: ``ec2-ssh-key/``
        :param store_public_key: Store the public key as a secret. Default: - false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c3e3d0951b980fa4044d4513992557a06c3152f208080e12317889f2c06aa1d)
            check_type(argname="argument account", value=account, expected_type=type_hints["account"])
            check_type(argname="argument environment_from_arn", value=environment_from_arn, expected_type=type_hints["environment_from_arn"])
            check_type(argname="argument physical_name", value=physical_name, expected_type=type_hints["physical_name"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument key_pair_name", value=key_pair_name, expected_type=type_hints["key_pair_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument expose_public_key", value=expose_public_key, expected_type=type_hints["expose_public_key"])
            check_type(argname="argument key_type", value=key_type, expected_type=type_hints["key_type"])
            check_type(argname="argument kms", value=kms, expected_type=type_hints["kms"])
            check_type(argname="argument kms_private_key", value=kms_private_key, expected_type=type_hints["kms_private_key"])
            check_type(argname="argument kms_public_key", value=kms_public_key, expected_type=type_hints["kms_public_key"])
            check_type(argname="argument legacy_lambda_name", value=legacy_lambda_name, expected_type=type_hints["legacy_lambda_name"])
            check_type(argname="argument log_level", value=log_level, expected_type=type_hints["log_level"])
            check_type(argname="argument public_key", value=public_key, expected_type=type_hints["public_key"])
            check_type(argname="argument public_key_format", value=public_key_format, expected_type=type_hints["public_key_format"])
            check_type(argname="argument remove_key_secrets_after_days", value=remove_key_secrets_after_days, expected_type=type_hints["remove_key_secrets_after_days"])
            check_type(argname="argument resource_prefix", value=resource_prefix, expected_type=type_hints["resource_prefix"])
            check_type(argname="argument secret_prefix", value=secret_prefix, expected_type=type_hints["secret_prefix"])
            check_type(argname="argument store_public_key", value=store_public_key, expected_type=type_hints["store_public_key"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "key_pair_name": key_pair_name,
        }
        if account is not None:
            self._values["account"] = account
        if environment_from_arn is not None:
            self._values["environment_from_arn"] = environment_from_arn
        if physical_name is not None:
            self._values["physical_name"] = physical_name
        if region is not None:
            self._values["region"] = region
        if description is not None:
            self._values["description"] = description
        if expose_public_key is not None:
            self._values["expose_public_key"] = expose_public_key
        if key_type is not None:
            self._values["key_type"] = key_type
        if kms is not None:
            self._values["kms"] = kms
        if kms_private_key is not None:
            self._values["kms_private_key"] = kms_private_key
        if kms_public_key is not None:
            self._values["kms_public_key"] = kms_public_key
        if legacy_lambda_name is not None:
            self._values["legacy_lambda_name"] = legacy_lambda_name
        if log_level is not None:
            self._values["log_level"] = log_level
        if public_key is not None:
            self._values["public_key"] = public_key
        if public_key_format is not None:
            self._values["public_key_format"] = public_key_format
        if remove_key_secrets_after_days is not None:
            self._values["remove_key_secrets_after_days"] = remove_key_secrets_after_days
        if resource_prefix is not None:
            self._values["resource_prefix"] = resource_prefix
        if secret_prefix is not None:
            self._values["secret_prefix"] = secret_prefix
        if store_public_key is not None:
            self._values["store_public_key"] = store_public_key

    @builtins.property
    def account(self) -> typing.Optional[builtins.str]:
        '''The AWS account ID this resource belongs to.

        :default: - the resource is in the same account as the stack it belongs to
        '''
        result = self._values.get("account")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def environment_from_arn(self) -> typing.Optional[builtins.str]:
        '''ARN to deduce region and account from.

        The ARN is parsed and the account and region are taken from the ARN.
        This should be used for imported resources.

        Cannot be supplied together with either ``account`` or ``region``.

        :default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        '''
        result = self._values.get("environment_from_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def physical_name(self) -> typing.Optional[builtins.str]:
        '''The value passed in by users to the physical name prop of the resource.

        - ``undefined`` implies that a physical name will be allocated by
          CloudFormation during deployment.
        - a concrete value implies a specific physical name
        - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated
          by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation.

        :default: - The physical name will be allocated by CloudFormation at deployment time
        '''
        result = self._values.get("physical_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def region(self) -> typing.Optional[builtins.str]:
        '''The AWS region this resource belongs to.

        :default: - the resource is in the same region as the stack it belongs to
        '''
        result = self._values.get("region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def key_pair_name(self) -> builtins.str:
        '''Name of the Key Pair.

        In AWS Secrets Manager the key will be prefixed with ``ec2-ssh-key/``.

        The name can be up to 255 characters long. Valid characters include _, -, a-z, A-Z, and 0-9.
        '''
        result = self._values.get("key_pair_name")
        assert result is not None, "Required property 'key_pair_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The description for the key in AWS Secrets Manager.

        :default: - ''
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def expose_public_key(self) -> typing.Optional[builtins.bool]:
        '''Expose the public key as property ``publicKeyValue``.

        :default: - false
        '''
        result = self._values.get("expose_public_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def key_type(self) -> typing.Optional["KeyType"]:
        '''The type of key pair.

        :default: - RSA
        '''
        result = self._values.get("key_type")
        return typing.cast(typing.Optional["KeyType"], result)

    @builtins.property
    def kms(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''The KMS key used to encrypt the Secrets Manager secrets with.

        This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified.

        :default: - ``alias/aws/secretsmanager``
        '''
        result = self._values.get("kms")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def kms_private_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''The KMS key to use to encrypt the private key with.

        This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified.

        If no value is provided, the property ``kms`` will be used instead.

        :default: - ``this.kms``
        '''
        result = self._values.get("kms_private_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def kms_public_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''The KMS key to use to encrypt the public key with.

        This needs to be a key created in the same stack. You cannot use a key imported via ARN, because the keys access policy will need to be modified.

        If no value is provided, the property ``kms`` will be used instead.

        :default: - ``this.kms``
        '''
        result = self._values.get("kms_public_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def legacy_lambda_name(self) -> typing.Optional[builtins.bool]:
        '''Whether to use the legacy name for the Lambda function, which backs the custom resource.

        Starting with v4 of this package, the Lambda function by default has no longer a fixed name.

        If you migrate from v3 to v4, you need to set this to ``true`` as CloudFormation does not allow to change the name of the Lambda function used by custom resource.

        :default: false
        '''
        result = self._values.get("legacy_lambda_name")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_level(self) -> typing.Optional["LogLevel"]:
        '''The log level of the Lambda function.

        :default: LogLevel.warn
        '''
        result = self._values.get("log_level")
        return typing.cast(typing.Optional["LogLevel"], result)

    @builtins.property
    def public_key(self) -> typing.Optional[builtins.str]:
        '''Import a public key instead of creating it.

        If no public key is provided, a new key pair will be created.
        '''
        result = self._values.get("public_key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def public_key_format(self) -> typing.Optional["PublicKeyFormat"]:
        '''Format for public key.

        Relevant only if the public key is stored and/or exposed.

        :default: - SSH
        '''
        result = self._values.get("public_key_format")
        return typing.cast(typing.Optional["PublicKeyFormat"], result)

    @builtins.property
    def remove_key_secrets_after_days(self) -> typing.Optional[jsii.Number]:
        '''When the resource is destroyed, after how many days the private and public key in the AWS Secrets Manager should be deleted.

        Valid values are 0 and 7 to 30

        :default: 0
        '''
        result = self._values.get("remove_key_secrets_after_days")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def resource_prefix(self) -> typing.Optional[builtins.str]:
        '''A prefix for all resource names.

        By default all resources are prefixed with the stack name to avoid collisions with other stacks. This might cause problems when you work with long stack names and can be overridden through this parameter.

        :default: Name of the stack
        '''
        result = self._values.get("resource_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def secret_prefix(self) -> typing.Optional[builtins.str]:
        '''Prefix for the secret in AWS Secrets Manager.

        :default: ``ec2-ssh-key/``
        '''
        result = self._values.get("secret_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def store_public_key(self) -> typing.Optional[builtins.bool]:
        '''Store the public key as a secret.

        :default: - false
        '''
        result = self._values.get("store_public_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KeyPairProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="cdk-ec2-key-pair.KeyType")
class KeyType(enum.Enum):
    RSA = "RSA"
    ED25519 = "ED25519"


@jsii.enum(jsii_type="cdk-ec2-key-pair.LogLevel")
class LogLevel(enum.Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


@jsii.enum(jsii_type="cdk-ec2-key-pair.PublicKeyFormat")
class PublicKeyFormat(enum.Enum):
    OPENSSH = "OPENSSH"
    '''OpenSSH format.'''
    SSH = "SSH"
    '''SSH format.'''
    PEM = "PEM"
    '''PEM format.'''
    PKCS1 = "PKCS1"
    '''PKCS#1 format.'''
    PKCS8 = "PKCS8"
    '''PKCS#8 format.'''
    RFC4253 = "RFC4253"
    '''Raw OpenSSH wire format.

    As CloudFormation cannot handle binary data, if the public key is exposed in the template, the value is base64 encoded
    '''
    PUTTY = "PUTTY"
    '''PuTTY ppk format.'''


__all__ = [
    "KeyPair",
    "KeyPairProps",
    "KeyType",
    "LogLevel",
    "PublicKeyFormat",
]

publication.publish()

def _typecheckingstub__ba97debf8723cff0eacba3e749a5826e9370b73123b213e1fa59471c93b71ea5(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    key_pair_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    expose_public_key: typing.Optional[builtins.bool] = None,
    key_type: typing.Optional[KeyType] = None,
    kms: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    kms_private_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    kms_public_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    legacy_lambda_name: typing.Optional[builtins.bool] = None,
    log_level: typing.Optional[LogLevel] = None,
    public_key: typing.Optional[builtins.str] = None,
    public_key_format: typing.Optional[PublicKeyFormat] = None,
    remove_key_secrets_after_days: typing.Optional[jsii.Number] = None,
    resource_prefix: typing.Optional[builtins.str] = None,
    secret_prefix: typing.Optional[builtins.str] = None,
    store_public_key: typing.Optional[builtins.bool] = None,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__674c4c11f9a0efc44319ec27788cc4dd19ef981f1274b3a1fa5bc1232076e555(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5b040bc4a9ad1d5cf8873edf241be4da5e7699b7c1ccdc1cbaea4a0d78398297(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c3e3d0951b980fa4044d4513992557a06c3152f208080e12317889f2c06aa1d(
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
    key_pair_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    expose_public_key: typing.Optional[builtins.bool] = None,
    key_type: typing.Optional[KeyType] = None,
    kms: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    kms_private_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    kms_public_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    legacy_lambda_name: typing.Optional[builtins.bool] = None,
    log_level: typing.Optional[LogLevel] = None,
    public_key: typing.Optional[builtins.str] = None,
    public_key_format: typing.Optional[PublicKeyFormat] = None,
    remove_key_secrets_after_days: typing.Optional[jsii.Number] = None,
    resource_prefix: typing.Optional[builtins.str] = None,
    secret_prefix: typing.Optional[builtins.str] = None,
    store_public_key: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass
