# AWS::ApplicationSignals Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

CloudWatch Application Signals is an auto-instrumentation solution built on OpenTelemetry that enables zero-code collection of monitoring data, such
as traces and metrics, from applications running across multiple platforms. It also supports topology auto-discovery based on collected monitoring data
and includes a new feature for managing service-level objectives (SLOs).

It supports Java, Python, .NET, and Node.js on platforms including EKS (and native Kubernetes), Lambda, ECS, and EC2. For more details, visit
[Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html) on the AWS
public website.

## Application Signals Enablement L2 Constructs

A collection of L2 constructs which leverages native L1 CFN resources, simplifying the enablement steps and the creation of Application
Signals resources.

### ApplicationSignalsIntegration

`ApplicationSignalsIntegration` aims to address key challenges in the current CDK enablement process, which requires complex manual configurations for
ECS customers. Application Signals is designed to be flexible and is supported for other platforms as well. However, the initial focus is on supporting
ECS, with plans to potentially extend support to other platforms in the future.

#### Enable Application Signals on ECS with sidecar mode

1. Configure `instrumentation` to instrument the application with the ADOT SDK Agent.
2. Specify `cloudWatchAgentSidecar` to configure the CloudWatch Agent as a sidecar container.

```python
from constructs import Construct
import aws_cdk.aws_applicationsignals_alpha as appsignals
import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs

class MyStack(cdk.Stack):
    def __init__(self, scope=None, id=None, *, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__()
        vpc = ec2.Vpc(self, "TestVpc")
        cluster = ecs.Cluster(self, "TestCluster", vpc=vpc)

        fargate_task_definition = ecs.FargateTaskDefinition(self, "SampleAppTaskDefinition",
            cpu=2048,
            memory_limit_mi_b=4096
        )

        fargate_task_definition.add_container("app",
            image=ecs.ContainerImage.from_registry("test/sample-app")
        )

        appsignals.ApplicationSignalsIntegration(self, "ApplicationSignalsIntegration",
            task_definition=fargate_task_definition,
            instrumentation=appsignals.InstrumentationProps(
                sdk_version=appsignals.JavaInstrumentationVersion.V2_10_0
            ),
            service_name="sample-app",
            cloud_watch_agent_sidecar=appsignals.CloudWatchAgentOptions(
                container_name="cloudwatch-agent",
                enable_logging=True,
                cpu=256,
                memory_limit_mi_b=512
            )
        )

        ecs.FargateService(self, "MySampleApp",
            cluster=cluster,
            task_definition=fargate_task_definition,
            desired_count=1
        )
```

#### Enable Application Signals on ECS with daemon mode

Note: Since the daemon deployment strategy is not supported on ECS Fargate, this mode is only supported on ECS on EC2.

1. Run CloudWatch Agent as a daemon service with HOST network mode.
2. Configure `instrumentation` to instrument the application with the ADOT Python Agent.
3. Override environment variables by configuring `overrideEnvironments` to use service connect endpoints to communicate to the CloudWatch agent server

```python
from constructs import Construct
import aws_cdk.aws_applicationsignals_alpha as appsignals
import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs

class MyStack(cdk.Stack):
    def __init__(self, scope=None, id=None, *, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        vpc = ec2.Vpc(self, "TestVpc")
        cluster = ecs.Cluster(self, "TestCluster", vpc=vpc)

        # Define Task Definition for CloudWatch agent (Daemon)
        cw_agent_task_definition = ecs.Ec2TaskDefinition(self, "CloudWatchAgentTaskDefinition",
            network_mode=ecs.NetworkMode.HOST
        )

        appsignals.CloudWatchAgentIntegration(self, "CloudWatchAgentIntegration",
            task_definition=cw_agent_task_definition,
            container_name="ecs-cwagent",
            enable_logging=False,
            cpu=128,
            memory_limit_mi_b=64,
            port_mappings=[ecs.PortMapping(
                container_port=4316,
                host_port=4316
            ), ecs.PortMapping(
                container_port=2000,
                host_port=2000
            )
            ]
        )

        # Create the CloudWatch Agent daemon service
        ecs.Ec2Service(self, "CloudWatchAgentDaemon",
            cluster=cluster,
            task_definition=cw_agent_task_definition,
            daemon=True
        )

        # Define Task Definition for user application
        sample_app_task_definition = ecs.Ec2TaskDefinition(self, "SampleAppTaskDefinition",
            network_mode=ecs.NetworkMode.HOST
        )

        sample_app_task_definition.add_container("app",
            image=ecs.ContainerImage.from_registry("test/sample-app"),
            cpu=0,
            memory_limit_mi_b=512
        )

        # No CloudWatch Agent side car is needed as application container communicates to CloudWatch Agent daemon through host network
        appsignals.ApplicationSignalsIntegration(self, "ApplicationSignalsIntegration",
            task_definition=sample_app_task_definition,
            instrumentation=appsignals.InstrumentationProps(
                sdk_version=appsignals.PythonInstrumentationVersion.V0_8_0
            ),
            service_name="sample-app"
        )

        ecs.Ec2Service(self, "MySampleApp",
            cluster=cluster,
            task_definition=sample_app_task_definition,
            desired_count=1
        )
```

#### Enable Application Signals on ECS with replica mode

**Note**
*Running CloudWatch Agent service using replica mode requires specific security group configurations to enable communication with other services.
For Application Signals functionality, configure the security group with the following minimum inbound rules: Port 2000 (HTTP) and Port 4316 (HTTP).
This configuration ensures proper connectivity between the CloudWatch Agent and dependent services.*

1. Run CloudWatch Agent as a replica service with service connect.
2. Configure `instrumentation` to instrument the application with the ADOT Python Agent.
3. Override environment variables by configuring `overrideEnvironments` to use service connect endpoints to communicate to the CloudWatch agent server

```python
from constructs import Construct
import aws_cdk.aws_applicationsignals_alpha as appsignals
import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
from aws_cdk.aws_servicediscovery import PrivateDnsNamespace

class MyStack(cdk.Stack):
    def __init__(self, scope=None, id=None, *, description=None, env=None, stackName=None, tags=None, notificationArns=None, synthesizer=None, terminationProtection=None, analyticsReporting=None, crossRegionReferences=None, permissionsBoundary=None, suppressTemplateIndentation=None, propertyInjectors=None):
        super().__init__(scope, id, description=description, env=env, stackName=stackName, tags=tags, notificationArns=notificationArns, synthesizer=synthesizer, terminationProtection=terminationProtection, analyticsReporting=analyticsReporting, crossRegionReferences=crossRegionReferences, permissionsBoundary=permissionsBoundary, suppressTemplateIndentation=suppressTemplateIndentation, propertyInjectors=propertyInjectors)

        vpc = ec2.Vpc(self, "TestVpc")
        cluster = ecs.Cluster(self, "TestCluster", vpc=vpc)
        dns_namespace = PrivateDnsNamespace(self, "Namespace",
            vpc=vpc,
            name="local"
        )
        security_group = ec2.SecurityGroup(self, "ECSSG", vpc=vpc)
        security_group.add_ingress_rule(security_group, ec2.Port.tcp_range(0, 65535))

        # Define Task Definition for CloudWatch agent (Replica)
        cw_agent_task_definition = ecs.FargateTaskDefinition(self, "CloudWatchAgentTaskDefinition")

        appsignals.CloudWatchAgentIntegration(self, "CloudWatchAgentIntegration",
            task_definition=cw_agent_task_definition,
            container_name="ecs-cwagent",
            enable_logging=False,
            cpu=128,
            memory_limit_mi_b=64,
            port_mappings=[ecs.PortMapping(
                name="cwagent-4316",
                container_port=4316,
                host_port=4316
            ), ecs.PortMapping(
                name="cwagent-2000",
                container_port=2000,
                host_port=2000
            )
            ]
        )

        # Create the CloudWatch Agent replica service with service connect
        ecs.FargateService(self, "CloudWatchAgentService",
            cluster=cluster,
            task_definition=cw_agent_task_definition,
            security_groups=[security_group],
            service_connect_configuration=ecs.ServiceConnectProps(
                namespace=dns_namespace.namespace_arn,
                services=[ecs.ServiceConnectService(
                    port_mapping_name="cwagent-4316",
                    dns_name="cwagent-4316-http",
                    port=4316
                ), ecs.ServiceConnectService(
                    port_mapping_name="cwagent-2000",
                    dns_name="cwagent-2000-http",
                    port=2000
                )
                ]
            ),
            desired_count=1
        )

        # Define Task Definition for user application
        sample_app_task_definition = ecs.FargateTaskDefinition(self, "SampleAppTaskDefinition")

        sample_app_task_definition.add_container("app",
            image=ecs.ContainerImage.from_registry("test/sample-app"),
            cpu=0,
            memory_limit_mi_b=512
        )

        # Overwrite environment variables to connect to the CloudWatch Agent service just created
        appsignals.ApplicationSignalsIntegration(self, "ApplicationSignalsIntegration",
            task_definition=sample_app_task_definition,
            instrumentation=appsignals.InstrumentationProps(
                sdk_version=appsignals.PythonInstrumentationVersion.V0_8_0
            ),
            service_name="sample-app",
            override_environments=[appsignals.EnvironmentExtension(
                name=appsignals.CommonExporting.OTEL_AWS_APPLICATION_SIGNALS_EXPORTER_ENDPOINT,
                value="http://cwagent-4316-http:4316/v1/metrics"
            ), appsignals.EnvironmentExtension(
                name=appsignals.TraceExporting.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                value="http://cwagent-4316-http:4316/v1/traces"
            ), appsignals.EnvironmentExtension(
                name=appsignals.TraceExporting.OTEL_TRACES_SAMPLER_ARG,
                value="endpoint=http://cwagent-2000-http:2000"
            )
            ]
        )

        # Create ECS Service with service connect configuration
        ecs.FargateService(self, "MySampleApp",
            cluster=cluster,
            task_definition=sample_app_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                namespace=dns_namespace.namespace_arn
            ),
            desired_count=1
        )
```
