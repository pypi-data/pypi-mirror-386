# AWS::AppRunner Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This module is part of the [AWS Cloud Development Kit](https://github.com/aws/aws-cdk) project.

```python
import aws_cdk.aws_apprunner_alpha as apprunner
```

## Introduction

AWS App Runner is a fully managed service that makes it easy for developers to quickly deploy containerized web applications and APIs, at scale and with no prior infrastructure experience required. Start with your source code or a container image. App Runner automatically builds and deploys the web application and load balances traffic with encryption. App Runner also scales up or down automatically to meet your traffic needs. With App Runner, rather than thinking about servers or scaling, you have more time to focus on your applications.

## Service

The `Service` construct allows you to create AWS App Runner services with `ECR Public`, `ECR` or `Github` with the `source` property in the following scenarios:

* `Source.fromEcr()` - To define the source repository from `ECR`.
* `Source.fromEcrPublic()` - To define the source repository from `ECR Public`.
* `Source.fromGitHub()` - To define the source repository from the `Github repository`.
* `Source.fromAsset()` - To define the source from local asset directory.

The `Service` construct implements `IGrantable`.

## ECR Public

To create a `Service` with ECR Public:

```python
apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    )
)
```

## ECR

To create a `Service` from an existing ECR repository:

```python
import aws_cdk.aws_ecr as ecr


apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr(
        image_configuration=apprunner.ImageConfiguration(port=80),
        repository=ecr.Repository.from_repository_name(self, "NginxRepository", "nginx"),
        tag_or_digest="latest"
    )
)
```

To create a `Service` from local docker image asset directory built and pushed to Amazon ECR:

You can specify whether to enable continuous integration from the source repository with the `autoDeploymentsEnabled` flag.

```python
import aws_cdk.aws_ecr_assets as assets


image_asset = assets.DockerImageAsset(self, "ImageAssets",
    directory=path.join(__dirname, "docker.assets")
)
apprunner.Service(self, "Service",
    source=apprunner.Source.from_asset(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        asset=image_asset
    ),
    auto_deployments_enabled=True
)
```

## GitHub

To create a `Service` from the GitHub repository, you need to specify an existing App Runner `Connection`.

See [Managing App Runner connections](https://docs.aws.amazon.com/apprunner/latest/dg/manage-connections.html) for more details.

```python
apprunner.Service(self, "Service",
    source=apprunner.Source.from_git_hub(
        repository_url="https://github.com/aws-containers/hello-app-runner",
        branch="main",
        configuration_source=apprunner.ConfigurationSourceType.REPOSITORY,
        connection=apprunner.GitHubConnection.from_connection_arn("CONNECTION_ARN")
    )
)
```

Use `codeConfigurationValues` to override configuration values with the `API` configuration source type.

```python
apprunner.Service(self, "Service",
    source=apprunner.Source.from_git_hub(
        repository_url="https://github.com/aws-containers/hello-app-runner",
        branch="main",
        configuration_source=apprunner.ConfigurationSourceType.API,
        code_configuration_values=apprunner.CodeConfigurationValues(
            runtime=apprunner.Runtime.PYTHON_3,
            port="8000",
            start_command="python app.py",
            build_command="yum install -y pycairo && pip install -r requirements.txt"
        ),
        connection=apprunner.GitHubConnection.from_connection_arn("CONNECTION_ARN")
    )
)
```

## IAM Roles

You are allowed to define `instanceRole` and `accessRole` for the `Service`.

`instanceRole` - The IAM role that provides permissions to your App Runner service. These are permissions that
your code needs when it calls any AWS APIs. If not defined, a new instance role will be generated
when required.

To add IAM policy statements to this role, use `addToRolePolicy()`:

```python
import aws_cdk.aws_iam as iam


service = apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    )
)

service.add_to_role_policy(iam.PolicyStatement(
    effect=iam.Effect.ALLOW,
    actions=["s3:GetObject"],
    resources=["*"]
))
```

`accessRole` - The IAM role that grants the App Runner service access to a source repository. It's required for
ECR image repositories (but not for ECR Public repositories). If not defined, a new access role will be generated
when required.

See [App Runner IAM Roles](https://docs.aws.amazon.com/apprunner/latest/dg/security_iam_service-with-iam.html#security_iam_service-with-iam-roles) for more details.

## Auto Scaling Configuration

To associate an App Runner service with a custom Auto Scaling Configuration, define `autoScalingConfiguration` for the service.

```python
auto_scaling_configuration = apprunner.AutoScalingConfiguration(self, "AutoScalingConfiguration",
    auto_scaling_configuration_name="MyAutoScalingConfiguration",
    max_concurrency=150,
    max_size=20,
    min_size=5
)

apprunner.Service(self, "DemoService",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    auto_scaling_configuration=auto_scaling_configuration
)
```

## VPC Connector

To associate an App Runner service with a custom VPC, define `vpcConnector` for the service.

```python
import aws_cdk.aws_ec2 as ec2


vpc = ec2.Vpc(self, "Vpc",
    ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16")
)

vpc_connector = apprunner.VpcConnector(self, "VpcConnector",
    vpc=vpc,
    vpc_subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC),
    vpc_connector_name="MyVpcConnector"
)

apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    vpc_connector=vpc_connector
)
```

## VPC Ingress Connection

To make your App Runner service private and only accessible from within a VPC use the `isPubliclyAccessible` property and associate it to a `VpcIngressConnection` resource.

To set up a `VpcIngressConnection`, specify a VPC, a VPC Interface Endpoint, and the App Runner service.
Also you must set `isPubliclyAccessible` property in ther `Service` to `false`.

For more information, see [Enabling Private endpoint for incoming traffic](https://docs.aws.amazon.com/apprunner/latest/dg/network-pl.html).

```python
import aws_cdk.aws_ec2 as ec2

# vpc: ec2.Vpc


interface_vpc_endpoint = ec2.InterfaceVpcEndpoint(self, "MyVpcEndpoint",
    vpc=vpc,
    service=ec2.InterfaceVpcEndpointAwsService.APP_RUNNER_REQUESTS,
    private_dns_enabled=False
)

service = apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(
            port=8000
        ),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    is_publicly_accessible=False
)

apprunner.VpcIngressConnection(self, "VpcIngressConnection",
    vpc=vpc,
    interface_vpc_endpoint=interface_vpc_endpoint,
    service=service
)
```

## Dual Stack

To use dual stack (IPv4 and IPv6) for your incoming public network configuration, set `ipAddressType` to `IpAddressType.DUAL_STACK`.

```python
apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    ip_address_type=apprunner.IpAddressType.DUAL_STACK
)
```

**Note**: Currently, App Runner supports dual stack for only Public endpoint.
Only IPv4 is supported for Private endpoint.
If you update a service that's using dual-stack Public endpoint to a Private endpoint,
your App Runner service will default to support only IPv4 for Private endpoint and fail
to receive traffic originating from IPv6 endpoint.

## Secrets Manager

To include environment variables integrated with AWS Secrets Manager, use the `environmentSecrets` attribute.
You can use the `addSecret` method from the App Runner `Service` class to include secrets from outside the
service definition.

```python
import aws_cdk.aws_secretsmanager as secretsmanager
import aws_cdk.aws_ssm as ssm

# stack: Stack


secret = secretsmanager.Secret(stack, "Secret")
parameter = ssm.StringParameter.from_secure_string_parameter_attributes(stack, "Parameter",
    parameter_name="/name",
    version=1
)

service = apprunner.Service(stack, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(
            port=8000,
            environment_secrets={
                "SECRET": apprunner.Secret.from_secrets_manager(secret),
                "PARAMETER": apprunner.Secret.from_ssm_parameter(parameter),
                "SECRET_ID": apprunner.Secret.from_secrets_manager_version(secret, version_id="version-id"),
                "SECRET_STAGE": apprunner.Secret.from_secrets_manager_version(secret, version_stage="version-stage")
            }
        ),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    )
)

service.add_secret("LATER_SECRET", apprunner.Secret.from_secrets_manager(secret, "field"))
```

## Use a customer managed key

To use a customer managed key for your source encryption, use the `kmsKey` attribute.

```python
import aws_cdk.aws_kms as kms

# kms_key: kms.IKey


apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    kms_key=kms_key
)
```

## HealthCheck

To configure the health check for the service, use the `healthCheck` attribute.

You can specify it by static methods `HealthCheck.http` or `HealthCheck.tcp`.

```python
apprunner.Service(self, "Service",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    health_check=apprunner.HealthCheck.http(
        healthy_threshold=5,
        interval=Duration.seconds(10),
        path="/",
        timeout=Duration.seconds(10),
        unhealthy_threshold=10
    )
)
```

## Observability Configuration

To associate an App Runner service with a custom observability configuration, use the `observabilityConfiguration` property.

```python
observability_configuration = apprunner.ObservabilityConfiguration(self, "ObservabilityConfiguration",
    observability_configuration_name="MyObservabilityConfiguration",
    trace_configuration_vendor=apprunner.TraceConfigurationVendor.AWSXRAY
)

apprunner.Service(self, "DemoService",
    source=apprunner.Source.from_ecr_public(
        image_configuration=apprunner.ImageConfiguration(port=8000),
        image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest"
    ),
    observability_configuration=observability_configuration
)
```
