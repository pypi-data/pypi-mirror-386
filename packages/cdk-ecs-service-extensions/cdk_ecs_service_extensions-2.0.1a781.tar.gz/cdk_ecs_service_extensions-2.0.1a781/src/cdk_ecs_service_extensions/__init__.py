r'''
# CDK Construct library for building ECS services

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

This library provides a high level, extensible pattern for constructing services
deployed using Amazon ECS.

```python
import {
  AppMeshExtension,
  CloudwatchAgentExtension,
  Container,
  Environment,
  FireLensExtension,
  HttpLoadBalancerExtension,
  Service,
  ServiceDescription,
  XRayExtension,
} from '@aws-cdk-containers/ecs-service-extensions';
```

If you are using the `@aws-cdk-containers/ecs-service-extensions` v1 and need to migrate to
v2, see the [Migration Guide](https://github.com/cdklabs/cdk-ecs-service-extensions/blob/main/MIGRATING.md).

## `Service` construct

The `Service` construct provided by this module can be extended with optional `ServiceExtension` classes that add supplemental ECS features including:

* [AWS X-Ray](https://aws.amazon.com/xray/) for tracing your application
* [Amazon CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html) for capturing per task stats
* [AWS AppMesh](https://aws.amazon.com/app-mesh/) for adding your application to a service mesh
* [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html), for exposing your service to the public
* [AWS FireLens](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html), for filtering and routing application logs
* [Injecter Extension](#injecter-extension), for allowing your service connect to other AWS services by granting permission and injecting environment variables
* [Queue Extension](#queue-extension), for allowing your service to consume messages from an SQS Queue which can be populated by one or more SNS Topics that it is subscribed to
* [Community Extensions](#community-extensions), providing support for advanced use cases

The `ServiceExtension` class is an abstract class which you can also implement in
order to build your own custom service extensions for modifying your service, or
attaching your own custom resources or sidecars.

## Example

```python
// Create an environment to deploy a service in.
const environment = new Environment(this, 'production');

// Build out the service description
const nameDescription = new ServiceDescription();
nameDescription.add(new Container({
  cpu: 1024,
  memoryMiB: 2048,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('nathanpeck/name'),
  environment: {
    PORT: '80',
  },
}));

declare const mesh: appmesh.Mesh;
nameDescription.add(new AppMeshExtension({ mesh }));
nameDescription.add(new FireLensExtension());
nameDescription.add(new XRayExtension());
nameDescription.add(new CloudwatchAgentExtension());
nameDescription.add(new HttpLoadBalancerExtension());

// Implement the service description as a real service inside
// an environment.
const nameService = new Service(this, 'name', {
  environment: environment,
  serviceDescription: nameDescription,
});
```

## Creating an `Environment`

An `Environment` is a place to deploy your services. You can have multiple environments
on a single AWS account. For example, you could create a `test` environment as well
as a `production` environment so you have a place to verify that your application
works as intended before you deploy it to a live environment.

Each environment is isolated from other environments. In other words,
when you create an environment, by default the construct supplies its own VPC,
ECS Cluster, and any other required resources for the environment:

```python
const environment = new Environment(this, 'production');
```

However, you can also choose to build an environment out of a pre-existing VPC
or ECS Cluster:

```python
declare const vpc: ec2.Vpc;
const cluster = new ecs.Cluster(this, 'Cluster', { vpc });

const environment = new Environment(this, 'production', {
  vpc,
  cluster,
});
```

## Defining your `ServiceDescription`

The `ServiceDescription` defines what application you want the service to run and
what optional extensions you want to add to the service. The most basic form of a `ServiceDescription` looks like this:

```python
const nameDescription = new ServiceDescription();
nameDescription.add(new Container({
  cpu: 1024,
  memoryMiB: 2048,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('nathanpeck/name'),
  environment: {
    PORT: '80',
  },
}));
```

Every `ServiceDescription` requires at minimum that you add a `Container` extension
which defines the main application (essential) container to run for the service.

### Logging using `awslogs` log driver

If no observability extensions have been configured for a service, the ECS Service Extensions configures an `awslogs` log driver for the application container of the service to send the container logs to CloudWatch Logs.

You can either provide a log group to the `Container` extension or one will be created for you by the CDK.

Following is an example of an application with an `awslogs` log driver configured for the application container:

```python
import * as logs from 'aws-cdk-lib/aws-logs';

const environment = new Environment(this, 'production');

const nameDescription = new ServiceDescription();
nameDescription.add(new Container({
  cpu: 1024,
  memoryMiB: 2048,
  trafficPort: 80,
  image: ContainerImage.fromRegistry('nathanpeck/name'),
  environment: {
    PORT: '80',
  },
  logGroup: new logs.LogGroup(this, 'MyLogGroup'),
}));
```

If a log group is not provided, no observability extensions have been created, and the `ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER` feature flag is enabled, then logging will be configured by default and a log group will be created for you.

The `ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER` feature flag is enabled by default in any CDK apps that are created with CDK v1.140.0 or v2.8.0 and later.

To enable default logging for previous versions, ensure that the `ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER` flag within the application stack context is set to true, like so:

```python
import * as cxapi from '@aws-cdk/cx-api';

this.node.setContext(cxapi.ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER, true);
```

Alternatively, you can also set the feature flag in the `cdk.json` file. For more information, refer the [docs](https://docs.aws.amazon.com/cdk/v2/guide/featureflags.html).

After adding the `Container` extension, you can optionally enable additional features for the service using the `ServiceDescription.add()` method:

```python
declare const mesh: appmesh.Mesh;
const nameDescription = new ServiceDescription();

nameDescription.add(new AppMeshExtension({ mesh }));
nameDescription.add(new FireLensExtension());
nameDescription.add(new XRayExtension());
nameDescription.add(new CloudwatchAgentExtension());
nameDescription.add(new HttpLoadBalancerExtension());
nameDescription.add(new AssignPublicIpExtension());
```

## Launching the `ServiceDescription` as a `Service`

Once the service description is defined, you can launch it as a service:

```python
const environment = new Environment(this, 'production');
const nameDescription = new ServiceDescription();

const nameService = new Service(this, 'name', {
  environment: environment,
  serviceDescription: nameDescription,
});
```

At this point, all the service resources will be created. This includes the ECS Task
Definition, Service, as well as any other attached resources, such as App Mesh Virtual
Node or an Application Load Balancer.

## Creating your own taskRole

Sometimes the taskRole should be defined outside of the service so that you can create strict resource policies (ie. S3 bucket policies) that are restricted to a given taskRole:

```python
const taskRole = new iam.Role(this, 'CustomTaskRole', {
  assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
});

// Use taskRole in any CDK resource policies
// new s3.BucketPolicy(this, 'BucketPolicy, {});

const environment = new Environment(this, 'production');
const nameDescription = new ServiceDescription();
const nameService = new Service(this, 'name', {
  environment: environment,
  serviceDescription: nameDescription,
  taskRole,
});
```

## Configure Custom Health Check

When you add an HTTPLoadBalancerExtension, you can customize the health checks by accessing the targetGroup field on the service.

```python
const service = new Service(stack, 'my-service', {
  environment,
  serviceDescription,
  autoScaleTaskCount: {
    maxTaskCount: 5,
  },
});

service.targetGroup.configureHealthCheck({
  path: '/',
  port: '80',
});
```

## Task Auto-Scaling

You can configure the task count of a service to match demand. The recommended way of achieving this is to configure target tracking policies for your service which scales in and out in order to keep metrics around target values.

You need to configure an auto scaling target for the service by setting the `minTaskCount` (defaults to 1) and `maxTaskCount` in the `Service` construct. Then you can specify target values for "CPU Utilization" or "Memory Utilization" across all tasks in your service. Note that the `desiredCount` value will be set to `undefined` if the auto scaling target is configured.

If you want to configure auto-scaling policies based on resources like Application Load Balancer or SQS Queues, you can set the corresponding resource-specific fields in the extension. For example, you can enable target tracking scaling based on Application Load Balancer request count as follows:

```python
const environment = new Environment(this, 'production');
const serviceDescription = new ServiceDescription();

serviceDescription.add(new Container({
  cpu: 256,
  memoryMiB: 512,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('my-alb'),
}));

// Add the extension with target `requestsPerTarget` value set
serviceDescription.add(new HttpLoadBalancerExtension({ requestsPerTarget: 10 }));

// Configure the auto scaling target
new Service(this, 'my-service', {
  environment,
  serviceDescription,
  desiredCount: 5,
  // Task auto-scaling constuct for the service
  autoScaleTaskCount: {
    maxTaskCount: 10,
    targetCpuUtilization: 70,
    targetMemoryUtilization: 50,
  },
});
```

You can also define your own service extensions for [other auto-scaling policies](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html) for your service by making use of the `scalableTaskCount` attribute of the `Service` class.

## Creating your own custom `ServiceExtension`

In addition to using the default service extensions that come with this module, you
can choose to implement your own custom service extensions. The `ServiceExtension`
class is an abstract class you can implement yourself. The following example
implements a custom service extension that could be added to a service in order to
autoscale it based on scaling intervals of SQS Queue size:

```python
export class MyCustomAutoscaling extends ServiceExtension {
  constructor() {
    super('my-custom-autoscaling');
    // Scaling intervals for the step scaling policy
    this.scalingSteps = [{ upper: 0, change: -1 }, { lower: 100, change: +1 }, { lower: 500, change: +5 }];
    this.sqsQueue = new sqs.Queue(this.scope, 'my-queue');
  }

  // This hook utilizes the resulting service construct
  // once it is created
  public useService(service: ecs.Ec2Service | ecs.FargateService) {
    this.parentService.scalableTaskCount.scaleOnMetric('QueueMessagesVisibleScaling', {
      metric: this.sqsQueue.metricApproximateNumberOfMessagesVisible(),
      scalingSteps: this.scalingSteps,
    });
  }
}
```

This `ServiceExtension` can now be reused and added to any number of different
service descriptions. This allows you to develop reusable bits of configuration,
attach them to many different services, and centrally manage them. Updating the
`ServiceExtension` in one place would update all services that use it, instead of
requiring decentralized updates to many different services.

Every `ServiceExtension` can implement the following hooks to modify the properties
of constructs, or make use of the resulting constructs:

* `addHooks()` - This hook is called after all the extensions are added to a
  ServiceDescription, but before any of the other extension hooks have been run.
  It gives each extension a chance to do some inspection of the overall ServiceDescription
  and see what other extensions have been added. Some extensions may want to register
  hooks on the other extensions to modify them. For example, the Firelens extension
  wants to be able to modify the settings of the application container to route logs
  through Firelens.
* `modifyTaskDefinitionProps()` - This is hook is passed the proposed
  ecs.TaskDefinitionProps for a TaskDefinition that is about to be created.
  This allows the extension to make modifications to the task definition props
  before the TaskDefinition is created. For example, the App Mesh extension modifies
  the proxy settings for the task.
* `useTaskDefinition()` - After the TaskDefinition is created, this hook is
  passed the actual TaskDefinition construct that was created. This allows the
  extension to add containers to the task, modify the task definition's IAM role,
  etc.
* `resolveContainerDependencies()` - Once all extensions have added their containers,
  each extension is given a chance to modify its container's `dependsOn` settings.
  Extensions need to check and see what other extensions were enabled and decide
  whether their container needs to wait on another container to start first.
* `modifyServiceProps()` - Before an Ec2Service or FargateService is created, this
  hook is passed a draft version of the service props to change. Each extension adds
  its own modifications to the service properties. For example, the App Mesh extension
  needs to modify the service settings to enable CloudMap service discovery.
* `useService()` - After the service is created, this hook is given a chance to
  utilize that service. This is used by extensions like the load balancer or App Mesh
  extension, which create and link other AWS resources to the ECS extension.
* `connectToService()` - This hook is called when a user wants to connect one service
  to another service. It allows an extension to implement logic about how to allow
  connections from one service to another. For example, the App Mesh extension implements
  this method in order to easily connect one service mesh service to another, which
  allows the service's Envoy proxy sidecars to route traffic to each other.

## Connecting services

One of the hooks that a `ServiceExtension` can implement is a hook for connection
logic. This is utilized when connecting one service to another service, e.g.
connecting a user facing web service with a backend API. Usage looks like this:

```python
const frontendDescription = new ServiceDescription();
const frontend = new Service(this, 'frontend', {
  environment,
  serviceDescription: frontendDescription,
});

const backendDescription = new ServiceDescription();
const backend = new Service(this, 'backend', {
  environment,
  serviceDescription: backendDescription,
});

frontend.connectTo(backend);
```

The address that a service will use to talk to another service depends on the
type of ingress that has been created by the extension that did the connecting.
For example, if an App Mesh extension has been used, then the service is accessible
at a DNS address of `<service name>.<environment name>`. For example:

```python
const environment = new Environment(this, 'production');

// Define the frontend tier
const frontendDescription = new ServiceDescription();
frontendDescription.add(new Container({
  cpu: 1024,
  memoryMiB: 2048,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('my-frontend-service'),
  environment: {
    BACKEND_URL: 'http://backend.production',
  },
}));

const frontend = new Service(this, 'frontend', {
  environment,
  serviceDescription: frontendDescription,
});

// Define the backend tier
const backendDescription = new ServiceDescription();
backendDescription.add(new Container({
  cpu: 1024,
  memoryMiB: 2048,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('my-backend-service'),
  environment: {
    FRONTEND_URL: 'http://frontend.production',
  },
}));
const backend = new Service(this, 'backend', {
  environment,
  serviceDescription: backendDescription,
});

// Connect the two tiers to each other
frontend.connectTo(backend);
```

The above code uses the well-known service discovery name for each
service, and passes it as an environment variable to the container so
that the container knows what address to use when communicating to
the other service.

## Importing a pre-existing cluster

To create an environment with a pre-existing cluster, you must import the cluster first, then use `Environment.fromEnvironmentAttributes()`. When a cluster is imported into an environment, the cluster is treated as immutable. As a result, no extension may modify the cluster to change a setting.

```python
declare const cluster: ecs.Cluster;

const environment = Environment.fromEnvironmentAttributes(this, 'Environment', {
  capacityType: ecs.EnvironmentCapacityType.EC2, // or `FARGATE`
  cluster,
});
```

## Injecter Extension

This service extension accepts a list of `Injectable` resources. It grants access to these resources and adds the necessary environment variables to the tasks that are part of the service.

For example, an `InjectableTopic` is an SNS Topic that grants permission to the task role and adds the topic ARN as an environment variable to the task definition.

### Publishing to SNS Topics

You can use this extension to set up publishing permissions for SNS Topics.

```python
const nameDescription = new ServiceDescription();
nameDescription.add(new InjecterExtension({
  injectables: [new InjectableTopic({
    // SNS Topic the service will publish to
    topic: new sns.Topic(this, 'my-topic'),
  })],
}));
```

## Queue Extension

This service extension creates a default SQS Queue `eventsQueue` for the service (if not provided) and optionally also accepts list of `ISubscribable` objects that the `eventsQueue` can subscribe to. The service extension creates the subscriptions and sets up permissions for the service to consume messages from the SQS Queue.

### Setting up SNS Topic Subscriptions for SQS Queues

You can use this extension to set up SNS Topic subscriptions for the `eventsQueue`. To do this, create a new object of type `TopicSubscription` for every SNS Topic you want the `eventsQueue` to subscribe to and provide it as input to the service extension.

```python
const nameDescription = new ServiceDescription();
const myServiceDescription = nameDescription.add(new QueueExtension({
  // Provide list of topic subscriptions that you want the `eventsQueue` to subscribe to
  subscriptions: [new TopicSubscription({
    topic: new sns.Topic(this, 'my-topic'),
  }],
}));

// To access the `eventsQueue` for the service, use the `eventsQueue` getter for the extension
const myQueueExtension = myServiceDescription.extensions.queue as QueueExtension;
const myEventsQueue = myQueueExtension.eventsQueue;
```

For setting up a topic-specific queue subscription, you can provide a custom queue in the `TopicSubscription` object along with the SNS Topic. The extension will set up a topic subscription for the provided queue instead of the default `eventsQueue` of the service.

```python
declare const myEventsQueue: sqs.Queue;
declare const myTopicQueue: sqs.Queue;
const nameDescription = new ServiceDescription();

nameDescription.add(new QueueExtension({
  eventsQueue: myEventsQueue,
  subscriptions: [new TopicSubscription({
    topic: new sns.Topic(this, 'my-topic'),
    // `myTopicQueue` will subscribe to the `my-topic` instead of `eventsQueue`
    topicSubscriptionQueue: {
      queue: myTopicQueue,
    },
  }],
}));
```

### Configuring auto scaling based on SQS Queues

You can scale your service up or down to maintain an acceptable queue latency by tracking the backlog per task. It configures a target tracking scaling policy with target value (acceptable backlog per task) calculated by dividing the `acceptableLatency` by `messageProcessingTime`. For example, if the maximum acceptable latency for a message to be processed after its arrival in the SQS Queue is 10 mins and the average processing time for a task is 250 milliseconds per message, then `acceptableBacklogPerTask = 10 *  60 / 0.25 = 2400`. Therefore, each queue can hold up to 2400 messages before the service starts to scale up. For this, a target tracking policy will be attached to the scaling target for your service with target value `2400`. For more information, please refer: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html .

You can configure auto scaling based on SQS Queue for your service as follows:

```python
declare const myEventsQueue: sqs.Queue;
declare const myTopicQueue: sqs.Queue;
const nameDescription = new ServiceDescription();

nameDescription.add(new QueueExtension({
  eventsQueue: myEventsQueue,
  // Need to specify `scaleOnLatency` to configure auto scaling based on SQS Queue
  scaleOnLatency: {
    acceptableLatency: Duration.minutes(10),
    messageProcessingTime: Duration.millis(250),
  },
  subscriptions: [new TopicSubscription({
    topic: new sns.Topic(this, 'my-topic'),
    // `myTopicQueue` will subscribe to the `my-topic` instead of `eventsQueue`
    topicSubscriptionQueue: {
      queue: myTopicQueue,
      // Optionally provide `scaleOnLatency` for configuring separate autoscaling for `myTopicQueue`
      scaleOnLatency: {
        acceptableLatency: Duration.minutes(10),
        messageProcessingTime: Duration.millis(250),
      },
    },
  }],
}));
```

## Publish/Subscribe Service Pattern

The [Publish/Subscribe Service Pattern](https://aws.amazon.com/pub-sub-messaging/) is used for implementing asynchronous communication between services. It involves 'publisher' services emitting events to SNS Topics, which are passed to subscribed SQS queues and then consumed by 'worker' services.

The following example adds the `InjecterExtension` to a `Publisher` Service which can publish events to an SNS Topic and adds the `QueueExtension` to a `Worker` Service which can poll its `eventsQueue` to consume messages populated by the topic.

```python
const environment = new Environment(this, 'production');

const pubServiceDescription = new ServiceDescription();
pubServiceDescription.add(new Container({
  cpu: 256,
  memoryMiB: 512,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('sns-publish'),
}));

const myTopic = new sns.Topic(this, 'myTopic');

// Add the `InjecterExtension` to the service description to allow publishing events to `myTopic`
pubServiceDescription.add(new InjecterExtension({
  injectables: [new InjectableTopic({
    topic: myTopic,
  }],
}));

// Create the `Publisher` Service
new Service(this, 'Publisher', {
  environment: environment,
  serviceDescription: pubServiceDescription,
});

const subServiceDescription = new ServiceDescription();
subServiceDescription.add(new Container({
  cpu: 256,
  memoryMiB: 512,
  trafficPort: 80,
  image: ecs.ContainerImage.fromRegistry('sqs-reader'),
}));

// Add the `QueueExtension` to the service description to subscribe to `myTopic`
subServiceDescription.add(new QueueExtension({
  subscriptions: [new TopicSubscription({
    topic: myTopic,
  }],
}));

// Create the `Worker` Service
new Service(this, 'Worker', {
  environment: environment,
  serviceDescription: subServiceDescription,
});
```

## Community Extensions

We encourage the development of Community Service Extensions that support
advanced features. Here are some useful extensions that we have reviewed:

* [ListenerRulesExtension](https://www.npmjs.com/package/@wheatstalk/ecs-service-extension-listener-rules) for more precise control over Application Load Balancer rules

> Please submit a pull request so that we can review your service extension and
> list it here.
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
import aws_cdk.aws_appmesh as _aws_cdk_aws_appmesh_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_ecs as _aws_cdk_aws_ecs_ceddda9d
import aws_cdk.aws_elasticloadbalancingv2 as _aws_cdk_aws_elasticloadbalancingv2_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_route53 as _aws_cdk_aws_route53_ceddda9d
import aws_cdk.aws_servicediscovery as _aws_cdk_aws_servicediscovery_ceddda9d
import aws_cdk.aws_sns as _aws_cdk_aws_sns_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AliasedPortMutatingHookProps",
    jsii_struct_bases=[],
    name_mapping={
        "alias_port": "aliasPort",
        "port_mapping_name": "portMappingName",
        "protocol": "protocol",
    },
)
class AliasedPortMutatingHookProps:
    def __init__(
        self,
        *,
        alias_port: jsii.Number,
        port_mapping_name: builtins.str,
        protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
    ) -> None:
        '''
        :param alias_port: (experimental) The port on the container which receives traffic. This is the same as the ``containerPort`` property of port mapping.
        :param port_mapping_name: (experimental) The name by which to refer to this port mapping.
        :param protocol: (experimental) The protocol which this port mapping expects to receive. Default: - none

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9eafc8bc30298b419ba1305209f1f31afbf65c9b3456fc2c643e9dc4c1bd501a)
            check_type(argname="argument alias_port", value=alias_port, expected_type=type_hints["alias_port"])
            check_type(argname="argument port_mapping_name", value=port_mapping_name, expected_type=type_hints["port_mapping_name"])
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "alias_port": alias_port,
            "port_mapping_name": port_mapping_name,
        }
        if protocol is not None:
            self._values["protocol"] = protocol

    @builtins.property
    def alias_port(self) -> jsii.Number:
        '''(experimental) The port on the container which receives traffic.

        This is the same as the ``containerPort`` property of port mapping.

        :stability: experimental
        '''
        result = self._values.get("alias_port")
        assert result is not None, "Required property 'alias_port' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def port_mapping_name(self) -> builtins.str:
        '''(experimental) The name by which to refer to this port mapping.

        :stability: experimental
        '''
        result = self._values.get("port_mapping_name")
        assert result is not None, "Required property 'port_mapping_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def protocol(self) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol]:
        '''(experimental) The protocol which this port mapping expects to receive.

        :default: - none

        :stability: experimental
        '''
        result = self._values.get("protocol")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AliasedPortMutatingHookProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AliasedPortProps",
    jsii_struct_bases=[],
    name_mapping={
        "alias": "alias",
        "alias_port": "aliasPort",
        "app_protocol": "appProtocol",
    },
)
class AliasedPortProps:
    def __init__(
        self,
        *,
        alias: builtins.str,
        alias_port: typing.Optional[jsii.Number] = None,
        app_protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
    ) -> None:
        '''(experimental) AliasedPortProps defines the properties of an aliased port extension.

        :param alias: (experimental) The DNS alias to advertise for downstream clients.
        :param alias_port: (experimental) The traffic port for clients to use to connect to the DNS alias. Default: - same as containerPort.
        :param app_protocol: (experimental) The protocol to use over the specified port. May be one of HTTP, HTTP2, or GRPC. Default: - none

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7d89a6c579317235d028edb793a72ba2e7d3ccda1e4b1f2602503eea428e930c)
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument alias_port", value=alias_port, expected_type=type_hints["alias_port"])
            check_type(argname="argument app_protocol", value=app_protocol, expected_type=type_hints["app_protocol"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "alias": alias,
        }
        if alias_port is not None:
            self._values["alias_port"] = alias_port
        if app_protocol is not None:
            self._values["app_protocol"] = app_protocol

    @builtins.property
    def alias(self) -> builtins.str:
        '''(experimental) The DNS alias to advertise for downstream clients.

        :stability: experimental
        '''
        result = self._values.get("alias")
        assert result is not None, "Required property 'alias' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def alias_port(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The traffic port for clients to use to connect to the DNS alias.

        :default: - same as containerPort.

        :stability: experimental
        '''
        result = self._values.get("alias_port")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def app_protocol(self) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol]:
        '''(experimental) The protocol to use over the specified port.

        May be one of HTTP, HTTP2, or GRPC.

        :default: - none

        :stability: experimental
        '''
        result = self._values.get("app_protocol")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AliasedPortProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AssignPublicIpDnsOptions",
    jsii_struct_bases=[],
    name_mapping={"record_name": "recordName", "zone": "zone"},
)
class AssignPublicIpDnsOptions:
    def __init__(
        self,
        *,
        record_name: builtins.str,
        zone: _aws_cdk_aws_route53_ceddda9d.IHostedZone,
    ) -> None:
        '''
        :param record_name: (experimental) Name of the record to add to the zone and in which to add the task IP addresses to.
        :param zone: (experimental) A DNS Zone to expose task IPs in.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa7fb8b6574fcc7a10ce0f47113796062053fc86dbd682d2487f7cdfb34d46d0)
            check_type(argname="argument record_name", value=record_name, expected_type=type_hints["record_name"])
            check_type(argname="argument zone", value=zone, expected_type=type_hints["zone"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "record_name": record_name,
            "zone": zone,
        }

    @builtins.property
    def record_name(self) -> builtins.str:
        '''(experimental) Name of the record to add to the zone and in which to add the task IP addresses to.

        :stability: experimental

        Example::

            'myservice'
        '''
        result = self._values.get("record_name")
        assert result is not None, "Required property 'record_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def zone(self) -> _aws_cdk_aws_route53_ceddda9d.IHostedZone:
        '''(experimental) A DNS Zone to expose task IPs in.

        :stability: experimental
        '''
        result = self._values.get("zone")
        assert result is not None, "Required property 'zone' is missing"
        return typing.cast(_aws_cdk_aws_route53_ceddda9d.IHostedZone, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AssignPublicIpDnsOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AssignPublicIpExtensionOptions",
    jsii_struct_bases=[],
    name_mapping={"dns": "dns"},
)
class AssignPublicIpExtensionOptions:
    def __init__(
        self,
        *,
        dns: typing.Optional[typing.Union[AssignPublicIpDnsOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param dns: (experimental) Enable publishing task public IPs to a recordset in a Route 53 hosted zone. Note: If you want to change the DNS zone or record name, you will need to remove this extension completely and then re-add it.

        :stability: experimental
        '''
        if isinstance(dns, dict):
            dns = AssignPublicIpDnsOptions(**dns)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2deb6349e9cd894776e0a60628761c1ec58ee4da5eb9e508b90d05cf30b34874)
            check_type(argname="argument dns", value=dns, expected_type=type_hints["dns"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns is not None:
            self._values["dns"] = dns

    @builtins.property
    def dns(self) -> typing.Optional[AssignPublicIpDnsOptions]:
        '''(experimental) Enable publishing task public IPs to a recordset in a Route 53 hosted zone.

        Note: If you want to change the DNS zone or record name, you will need to
        remove this extension completely and then re-add it.

        :stability: experimental
        '''
        result = self._values.get("dns")
        return typing.cast(typing.Optional[AssignPublicIpDnsOptions], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AssignPublicIpExtensionOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AutoScalingOptions",
    jsii_struct_bases=[],
    name_mapping={
        "max_task_count": "maxTaskCount",
        "min_task_count": "minTaskCount",
        "target_cpu_utilization": "targetCpuUtilization",
        "target_memory_utilization": "targetMemoryUtilization",
    },
)
class AutoScalingOptions:
    def __init__(
        self,
        *,
        max_task_count: jsii.Number,
        min_task_count: typing.Optional[jsii.Number] = None,
        target_cpu_utilization: typing.Optional[jsii.Number] = None,
        target_memory_utilization: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param max_task_count: (experimental) The maximum number of tasks when scaling out.
        :param min_task_count: (experimental) The minimum number of tasks when scaling in. Default: - 1
        :param target_cpu_utilization: (experimental) The target value for CPU utilization across all tasks in the service.
        :param target_memory_utilization: (experimental) The target value for memory utilization across all tasks in the service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__caf95230f9a127a46aef16659b3a944e6851420921875acc492c4a7722ded929)
            check_type(argname="argument max_task_count", value=max_task_count, expected_type=type_hints["max_task_count"])
            check_type(argname="argument min_task_count", value=min_task_count, expected_type=type_hints["min_task_count"])
            check_type(argname="argument target_cpu_utilization", value=target_cpu_utilization, expected_type=type_hints["target_cpu_utilization"])
            check_type(argname="argument target_memory_utilization", value=target_memory_utilization, expected_type=type_hints["target_memory_utilization"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "max_task_count": max_task_count,
        }
        if min_task_count is not None:
            self._values["min_task_count"] = min_task_count
        if target_cpu_utilization is not None:
            self._values["target_cpu_utilization"] = target_cpu_utilization
        if target_memory_utilization is not None:
            self._values["target_memory_utilization"] = target_memory_utilization

    @builtins.property
    def max_task_count(self) -> jsii.Number:
        '''(experimental) The maximum number of tasks when scaling out.

        :stability: experimental
        '''
        result = self._values.get("max_task_count")
        assert result is not None, "Required property 'max_task_count' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def min_task_count(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The minimum number of tasks when scaling in.

        :default: - 1

        :stability: experimental
        '''
        result = self._values.get("min_task_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def target_cpu_utilization(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The target value for CPU utilization across all tasks in the service.

        :stability: experimental
        '''
        result = self._values.get("target_cpu_utilization")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def target_memory_utilization(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The target value for memory utilization across all tasks in the service.

        :stability: experimental
        '''
        result = self._values.get("target_memory_utilization")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AutoScalingOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ConnectToProps",
    jsii_struct_bases=[],
    name_mapping={"local_bind_port": "localBindPort"},
)
class ConnectToProps:
    def __init__(self, *, local_bind_port: typing.Optional[jsii.Number] = None) -> None:
        '''(experimental) connectToProps will have all the extra parameters which are required for connecting services.

        :param local_bind_port: (experimental) localBindPort is the local port that this application should use when calling the upstream service in ECS Consul Mesh Extension Currently, this parameter will only be used in the ECSConsulMeshExtension https://github.com/aws-ia/ecs-consul-mesh-extension.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20e37174ab201a5eb1d201637ac0c651f7361afe5cb95a69d57aeed17fde4cc3)
            check_type(argname="argument local_bind_port", value=local_bind_port, expected_type=type_hints["local_bind_port"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if local_bind_port is not None:
            self._values["local_bind_port"] = local_bind_port

    @builtins.property
    def local_bind_port(self) -> typing.Optional[jsii.Number]:
        '''(experimental) localBindPort is the local port that this application should use when calling the upstream service in ECS Consul Mesh Extension Currently, this parameter will only be used in the ECSConsulMeshExtension https://github.com/aws-ia/ecs-consul-mesh-extension.

        :stability: experimental
        '''
        result = self._values.get("local_bind_port")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ConnectToProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ContainerExtensionProps",
    jsii_struct_bases=[],
    name_mapping={
        "cpu": "cpu",
        "image": "image",
        "memory_mib": "memoryMiB",
        "traffic_port": "trafficPort",
        "environment": "environment",
        "environment_files": "environmentFiles",
        "log_group": "logGroup",
        "secrets": "secrets",
    },
)
class ContainerExtensionProps:
    def __init__(
        self,
        *,
        cpu: jsii.Number,
        image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
        memory_mib: jsii.Number,
        traffic_port: jsii.Number,
        environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
        log_group: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup] = None,
        secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
    ) -> None:
        '''(experimental) Setting for the main application container of a service.

        :param cpu: (experimental) How much CPU the container requires.
        :param image: (experimental) The image to run.
        :param memory_mib: (experimental) How much memory in megabytes the container requires.
        :param traffic_port: (experimental) What port the image listen for traffic on.
        :param environment: (experimental) Environment variables to pass into the container. Default: - No environment variables.
        :param environment_files: (experimental) The environment files to pass to the container. Default: - No environment files.
        :param log_group: (experimental) The log group into which application container logs should be routed. Default: - A log group is automatically created for you if the ``ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER`` feature flag is set.
        :param secrets: (experimental) The secret environment variables to pass to the container. Default: - No secret environment variables.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__592d522da39571a2b2a1780c28b1405f8f98b2f7ae4b9ff881cf256a8d3941d3)
            check_type(argname="argument cpu", value=cpu, expected_type=type_hints["cpu"])
            check_type(argname="argument image", value=image, expected_type=type_hints["image"])
            check_type(argname="argument memory_mib", value=memory_mib, expected_type=type_hints["memory_mib"])
            check_type(argname="argument traffic_port", value=traffic_port, expected_type=type_hints["traffic_port"])
            check_type(argname="argument environment", value=environment, expected_type=type_hints["environment"])
            check_type(argname="argument environment_files", value=environment_files, expected_type=type_hints["environment_files"])
            check_type(argname="argument log_group", value=log_group, expected_type=type_hints["log_group"])
            check_type(argname="argument secrets", value=secrets, expected_type=type_hints["secrets"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cpu": cpu,
            "image": image,
            "memory_mib": memory_mib,
            "traffic_port": traffic_port,
        }
        if environment is not None:
            self._values["environment"] = environment
        if environment_files is not None:
            self._values["environment_files"] = environment_files
        if log_group is not None:
            self._values["log_group"] = log_group
        if secrets is not None:
            self._values["secrets"] = secrets

    @builtins.property
    def cpu(self) -> jsii.Number:
        '''(experimental) How much CPU the container requires.

        :stability: experimental
        '''
        result = self._values.get("cpu")
        assert result is not None, "Required property 'cpu' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def image(self) -> _aws_cdk_aws_ecs_ceddda9d.ContainerImage:
        '''(experimental) The image to run.

        :stability: experimental
        '''
        result = self._values.get("image")
        assert result is not None, "Required property 'image' is missing"
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ContainerImage, result)

    @builtins.property
    def memory_mib(self) -> jsii.Number:
        '''(experimental) How much memory in megabytes the container requires.

        :stability: experimental
        '''
        result = self._values.get("memory_mib")
        assert result is not None, "Required property 'memory_mib' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def traffic_port(self) -> jsii.Number:
        '''(experimental) What port the image listen for traffic on.

        :stability: experimental
        '''
        result = self._values.get("traffic_port")
        assert result is not None, "Required property 'traffic_port' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def environment(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Environment variables to pass into the container.

        :default: - No environment variables.

        :stability: experimental
        '''
        result = self._values.get("environment")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def environment_files(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]]:
        '''(experimental) The environment files to pass to the container.

        :default: - No environment files.

        :see: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/taskdef-envfiles.html
        :stability: experimental
        '''
        result = self._values.get("environment_files")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]], result)

    @builtins.property
    def log_group(self) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup]:
        '''(experimental) The log group into which application container logs should be routed.

        :default: - A log group is automatically created for you if the ``ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER`` feature flag is set.

        :stability: experimental
        '''
        result = self._values.get("log_group")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup], result)

    @builtins.property
    def secrets(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]]:
        '''(experimental) The secret environment variables to pass to the container.

        :default: - No secret environment variables.

        :stability: experimental
        '''
        result = self._values.get("secrets")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ContainerExtensionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ContainerMutatingHook(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ContainerMutatingHook",
):
    '''(experimental) This is an abstract class wrapper for a mutating hook.

    It is
    extended by any extension which wants to mutate other extension's containers.

    :stability: experimental
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="mutateContainerDefinition")
    def mutate_container_definition(
        self,
        *,
        image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
        command: typing.Optional[typing.Sequence[builtins.str]] = None,
        container_name: typing.Optional[builtins.str] = None,
        cpu: typing.Optional[jsii.Number] = None,
        disable_networking: typing.Optional[builtins.bool] = None,
        dns_search_domains: typing.Optional[typing.Sequence[builtins.str]] = None,
        dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
        docker_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        docker_security_options: typing.Optional[typing.Sequence[builtins.str]] = None,
        entry_point: typing.Optional[typing.Sequence[builtins.str]] = None,
        environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
        essential: typing.Optional[builtins.bool] = None,
        extra_hosts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        gpu_count: typing.Optional[jsii.Number] = None,
        health_check: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.HealthCheck, typing.Dict[builtins.str, typing.Any]]] = None,
        hostname: typing.Optional[builtins.str] = None,
        inference_accelerator_resources: typing.Optional[typing.Sequence[builtins.str]] = None,
        linux_parameters: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LinuxParameters] = None,
        logging: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LogDriver] = None,
        memory_limit_mib: typing.Optional[jsii.Number] = None,
        memory_reservation_mib: typing.Optional[jsii.Number] = None,
        port_mappings: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.PortMapping, typing.Dict[builtins.str, typing.Any]]]] = None,
        privileged: typing.Optional[builtins.bool] = None,
        readonly_root_filesystem: typing.Optional[builtins.bool] = None,
        secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
        start_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        stop_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        system_controls: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.SystemControl, typing.Dict[builtins.str, typing.Any]]]] = None,
        user: typing.Optional[builtins.str] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions:
        '''(experimental) This is a hook for modifying the container definition of any upstream containers.

        This is primarily used for the main application container.
        For example, the Firelens extension wants to be able to modify the logging
        settings of the application container.

        :param image: The image used to start a container. This string is passed directly to the Docker daemon. Images in the Docker Hub registry are available by default. Other repositories are specified with either repository-url/image:tag or repository-url/image@digest. TODO: Update these to specify using classes of IContainerImage
        :param command: The command that is passed to the container. If you provide a shell command as a single string, you have to quote command-line arguments. Default: - CMD value built into container image.
        :param container_name: The name of the container. Default: - id of node associated with ContainerDefinition.
        :param cpu: The minimum number of CPU units to reserve for the container. Default: - No minimum CPU units reserved.
        :param disable_networking: Specifies whether networking is disabled within the container. When this parameter is true, networking is disabled within the container. Default: false
        :param dns_search_domains: A list of DNS search domains that are presented to the container. Default: - No search domains.
        :param dns_servers: A list of DNS servers that are presented to the container. Default: - Default DNS servers.
        :param docker_labels: A key/value map of labels to add to the container. Default: - No labels.
        :param docker_security_options: A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. Default: - No security labels.
        :param entry_point: The ENTRYPOINT value to pass to the container. Default: - Entry point configured in container.
        :param environment: The environment variables to pass to the container. Default: - No environment variables.
        :param environment_files: The environment files to pass to the container. Default: - No environment files.
        :param essential: Specifies whether the container is marked essential. If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped. If the essential parameter of a container is marked as false, then its failure does not affect the rest of the containers in a task. All tasks must have at least one essential container. If this parameter is omitted, a container is assumed to be essential. Default: true
        :param extra_hosts: A list of hostnames and IP address mappings to append to the /etc/hosts file on the container. Default: - No extra hosts.
        :param gpu_count: The number of GPUs assigned to the container. Default: - No GPUs assigned.
        :param health_check: The health check command and associated configuration parameters for the container. Default: - Health check configuration from container.
        :param hostname: The hostname to use for your container. Default: - Automatic hostname.
        :param inference_accelerator_resources: The inference accelerators referenced by the container. Default: - No inference accelerators assigned.
        :param linux_parameters: Linux-specific modifications that are applied to the container, such as Linux kernel capabilities. For more information see `KernelCapabilities <https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_KernelCapabilities.html>`_. Default: - No Linux parameters.
        :param logging: The log configuration specification for the container. Default: - Containers use the same logging driver that the Docker daemon uses.
        :param memory_limit_mib: The amount (in MiB) of memory to present to the container. If your container attempts to exceed the allocated memory, the container is terminated. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory limit.
        :param memory_reservation_mib: The soft limit (in MiB) of memory to reserve for the container. When system memory is under heavy contention, Docker attempts to keep the container memory to this soft limit. However, your container can consume more memory when it needs to, up to either the hard limit specified with the memory parameter (if applicable), or all of the available memory on the container instance, whichever comes first. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory reserved.
        :param port_mappings: The port mappings to add to the container definition. Default: - No ports are mapped.
        :param privileged: Specifies whether the container is marked as privileged. When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user). Default: false
        :param readonly_root_filesystem: When this parameter is true, the container is given read-only access to its root file system. Default: false
        :param secrets: The secret environment variables to pass to the container. Default: - No secret environment variables.
        :param start_timeout: Time duration (in seconds) to wait before giving up on resolving dependencies for a container. Default: - none
        :param stop_timeout: Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own. Default: - none
        :param system_controls: A list of namespaced kernel parameters to set in the container. Default: - No system controls are set.
        :param user: The user name to use inside the container. Default: root
        :param working_directory: The working directory in which to run commands inside the container. Default: /

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions(
            image=image,
            command=command,
            container_name=container_name,
            cpu=cpu,
            disable_networking=disable_networking,
            dns_search_domains=dns_search_domains,
            dns_servers=dns_servers,
            docker_labels=docker_labels,
            docker_security_options=docker_security_options,
            entry_point=entry_point,
            environment=environment,
            environment_files=environment_files,
            essential=essential,
            extra_hosts=extra_hosts,
            gpu_count=gpu_count,
            health_check=health_check,
            hostname=hostname,
            inference_accelerator_resources=inference_accelerator_resources,
            linux_parameters=linux_parameters,
            logging=logging,
            memory_limit_mib=memory_limit_mib,
            memory_reservation_mib=memory_reservation_mib,
            port_mappings=port_mappings,
            privileged=privileged,
            readonly_root_filesystem=readonly_root_filesystem,
            secrets=secrets,
            start_timeout=start_timeout,
            stop_timeout=stop_timeout,
            system_controls=system_controls,
            user=user,
            working_directory=working_directory,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions, jsii.invoke(self, "mutateContainerDefinition", [props]))


class _ContainerMutatingHookProxy(ContainerMutatingHook):
    pass

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ContainerMutatingHook).__jsii_proxy_class__ = lambda : _ContainerMutatingHookProxy


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.CpuScalingProps",
    jsii_struct_bases=[],
    name_mapping={
        "initial_task_count": "initialTaskCount",
        "max_task_count": "maxTaskCount",
        "min_task_count": "minTaskCount",
        "scale_in_cooldown": "scaleInCooldown",
        "scale_out_cooldown": "scaleOutCooldown",
        "target_cpu_utilization": "targetCpuUtilization",
    },
)
class CpuScalingProps:
    def __init__(
        self,
        *,
        initial_task_count: typing.Optional[jsii.Number] = None,
        max_task_count: typing.Optional[jsii.Number] = None,
        min_task_count: typing.Optional[jsii.Number] = None,
        scale_in_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        scale_out_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        target_cpu_utilization: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(deprecated) The autoscaling settings.

        :param initial_task_count: (deprecated) How many tasks to launch initially. Default: - 2
        :param max_task_count: (deprecated) The maximum number of tasks when scaling out. Default: - 8
        :param min_task_count: (deprecated) The minimum number of tasks when scaling in. Default: - 2
        :param scale_in_cooldown: (deprecated) How long to wait between scale in actions. Default: - 60 seconds
        :param scale_out_cooldown: (deprecated) How long to wait between scale out actions. Default: - 60 seconds
        :param target_cpu_utilization: (deprecated) The CPU utilization to try ot maintain. Default: - 50%

        :deprecated:

        use the ``minTaskCount`` and ``maxTaskCount`` properties of ``autoScaleTaskCount`` in the ``Service`` construct
        to configure the auto scaling target for the service. For more information, please refer
        https://github.com/aws/aws-cdk/blob/master/packages/%40aws-cdk-containers/ecs-service-extensions/README.md#task-auto-scaling .

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da64dd40c2eed49a661888472ad447cdd50d0d1de54b035c25e482f09c6e8d50)
            check_type(argname="argument initial_task_count", value=initial_task_count, expected_type=type_hints["initial_task_count"])
            check_type(argname="argument max_task_count", value=max_task_count, expected_type=type_hints["max_task_count"])
            check_type(argname="argument min_task_count", value=min_task_count, expected_type=type_hints["min_task_count"])
            check_type(argname="argument scale_in_cooldown", value=scale_in_cooldown, expected_type=type_hints["scale_in_cooldown"])
            check_type(argname="argument scale_out_cooldown", value=scale_out_cooldown, expected_type=type_hints["scale_out_cooldown"])
            check_type(argname="argument target_cpu_utilization", value=target_cpu_utilization, expected_type=type_hints["target_cpu_utilization"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if initial_task_count is not None:
            self._values["initial_task_count"] = initial_task_count
        if max_task_count is not None:
            self._values["max_task_count"] = max_task_count
        if min_task_count is not None:
            self._values["min_task_count"] = min_task_count
        if scale_in_cooldown is not None:
            self._values["scale_in_cooldown"] = scale_in_cooldown
        if scale_out_cooldown is not None:
            self._values["scale_out_cooldown"] = scale_out_cooldown
        if target_cpu_utilization is not None:
            self._values["target_cpu_utilization"] = target_cpu_utilization

    @builtins.property
    def initial_task_count(self) -> typing.Optional[jsii.Number]:
        '''(deprecated) How many tasks to launch initially.

        :default: - 2

        :stability: deprecated
        '''
        result = self._values.get("initial_task_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_task_count(self) -> typing.Optional[jsii.Number]:
        '''(deprecated) The maximum number of tasks when scaling out.

        :default: - 8

        :stability: deprecated
        '''
        result = self._values.get("max_task_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_task_count(self) -> typing.Optional[jsii.Number]:
        '''(deprecated) The minimum number of tasks when scaling in.

        :default: - 2

        :stability: deprecated
        '''
        result = self._values.get("min_task_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def scale_in_cooldown(self) -> typing.Optional[_aws_cdk_ceddda9d.Duration]:
        '''(deprecated) How long to wait between scale in actions.

        :default: - 60 seconds

        :stability: deprecated
        '''
        result = self._values.get("scale_in_cooldown")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.Duration], result)

    @builtins.property
    def scale_out_cooldown(self) -> typing.Optional[_aws_cdk_ceddda9d.Duration]:
        '''(deprecated) How long to wait between scale out actions.

        :default: - 60 seconds

        :stability: deprecated
        '''
        result = self._values.get("scale_out_cooldown")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.Duration], result)

    @builtins.property
    def target_cpu_utilization(self) -> typing.Optional[jsii.Number]:
        '''(deprecated) The CPU utilization to try ot maintain.

        :default: - 50%

        :stability: deprecated
        '''
        result = self._values.get("target_cpu_utilization")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CpuScalingProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.EnvironmentAttributes",
    jsii_struct_bases=[],
    name_mapping={"capacity_type": "capacityType", "cluster": "cluster"},
)
class EnvironmentAttributes:
    def __init__(
        self,
        *,
        capacity_type: "EnvironmentCapacityType",
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
    ) -> None:
        '''
        :param capacity_type: (experimental) The capacity type used by the service's cluster.
        :param cluster: (experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3972ae1eaa225a4a8fa626d5b9ec3fc0b64c420599bc3a5f3dd1d2aec30cfd77)
            check_type(argname="argument capacity_type", value=capacity_type, expected_type=type_hints["capacity_type"])
            check_type(argname="argument cluster", value=cluster, expected_type=type_hints["cluster"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "capacity_type": capacity_type,
            "cluster": cluster,
        }

    @builtins.property
    def capacity_type(self) -> "EnvironmentCapacityType":
        '''(experimental) The capacity type used by the service's cluster.

        :stability: experimental
        '''
        result = self._values.get("capacity_type")
        assert result is not None, "Required property 'capacity_type' is missing"
        return typing.cast("EnvironmentCapacityType", result)

    @builtins.property
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        result = self._values.get("cluster")
        assert result is not None, "Required property 'cluster' is missing"
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.EnvironmentCapacityType"
)
class EnvironmentCapacityType(enum.Enum):
    '''(experimental) The types of capacity that are supported.

    These capacity types may change the
    behavior of an extension.

    :stability: experimental
    '''

    FARGATE = "FARGATE"
    '''(experimental) Specify that the environment should use AWS Fargate for hosting containers.

    :stability: experimental
    '''
    EC2 = "EC2"
    '''(experimental) Specify that the environment should launch containers onto EC2 instances.

    :stability: experimental
    '''


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.EnvironmentProps",
    jsii_struct_bases=[],
    name_mapping={"capacity_type": "capacityType", "cluster": "cluster", "vpc": "vpc"},
)
class EnvironmentProps:
    def __init__(
        self,
        *,
        capacity_type: typing.Optional[EnvironmentCapacityType] = None,
        cluster: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Settings for the environment where you want to deploy your services.

        :param capacity_type: (experimental) The type of capacity to use for this environment. Default: - EnvironmentCapacityType.FARGATE
        :param cluster: (experimental) The ECS cluster which provides compute capacity to this service. [disable-awslint:ref-via-interface] Default: - Create a new cluster
        :param vpc: (experimental) The VPC used by the service for networking. Default: - Create a new VPC

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4f994193a0844d1feecc18424b7d4cb07ff8d4ed7fb514183a12bd56930e922b)
            check_type(argname="argument capacity_type", value=capacity_type, expected_type=type_hints["capacity_type"])
            check_type(argname="argument cluster", value=cluster, expected_type=type_hints["cluster"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if capacity_type is not None:
            self._values["capacity_type"] = capacity_type
        if cluster is not None:
            self._values["cluster"] = cluster
        if vpc is not None:
            self._values["vpc"] = vpc

    @builtins.property
    def capacity_type(self) -> typing.Optional[EnvironmentCapacityType]:
        '''(experimental) The type of capacity to use for this environment.

        :default: - EnvironmentCapacityType.FARGATE

        :stability: experimental
        '''
        result = self._values.get("capacity_type")
        return typing.cast(typing.Optional[EnvironmentCapacityType], result)

    @builtins.property
    def cluster(self) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster]:
        '''(experimental) The ECS cluster which provides compute capacity to this service.

        [disable-awslint:ref-via-interface]

        :default: - Create a new cluster

        :stability: experimental
        '''
        result = self._values.get("cluster")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster], result)

    @builtins.property
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC used by the service for networking.

        :default: - Create a new VPC

        :stability: experimental
        '''
        result = self._values.get("vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class FirelensMutatingHook(
    ContainerMutatingHook,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.FirelensMutatingHook",
):
    '''(experimental) This hook modifies the application container's settings so that it routes logs using FireLens.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        log_group: _aws_cdk_aws_logs_ceddda9d.LogGroup,
        parent_service: "Service",
    ) -> None:
        '''
        :param log_group: (experimental) The log group into which logs should be routed.
        :param parent_service: (experimental) The parent service that is being mutated.

        :stability: experimental
        '''
        props = FirelensProps(log_group=log_group, parent_service=parent_service)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="mutateContainerDefinition")
    def mutate_container_definition(
        self,
        *,
        image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
        command: typing.Optional[typing.Sequence[builtins.str]] = None,
        container_name: typing.Optional[builtins.str] = None,
        cpu: typing.Optional[jsii.Number] = None,
        disable_networking: typing.Optional[builtins.bool] = None,
        dns_search_domains: typing.Optional[typing.Sequence[builtins.str]] = None,
        dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
        docker_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        docker_security_options: typing.Optional[typing.Sequence[builtins.str]] = None,
        entry_point: typing.Optional[typing.Sequence[builtins.str]] = None,
        environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
        essential: typing.Optional[builtins.bool] = None,
        extra_hosts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        gpu_count: typing.Optional[jsii.Number] = None,
        health_check: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.HealthCheck, typing.Dict[builtins.str, typing.Any]]] = None,
        hostname: typing.Optional[builtins.str] = None,
        inference_accelerator_resources: typing.Optional[typing.Sequence[builtins.str]] = None,
        linux_parameters: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LinuxParameters] = None,
        logging: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LogDriver] = None,
        memory_limit_mib: typing.Optional[jsii.Number] = None,
        memory_reservation_mib: typing.Optional[jsii.Number] = None,
        port_mappings: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.PortMapping, typing.Dict[builtins.str, typing.Any]]]] = None,
        privileged: typing.Optional[builtins.bool] = None,
        readonly_root_filesystem: typing.Optional[builtins.bool] = None,
        secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
        start_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        stop_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        system_controls: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.SystemControl, typing.Dict[builtins.str, typing.Any]]]] = None,
        user: typing.Optional[builtins.str] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions:
        '''(experimental) This is a hook for modifying the container definition of any upstream containers.

        This is primarily used for the main application container.
        For example, the Firelens extension wants to be able to modify the logging
        settings of the application container.

        :param image: The image used to start a container. This string is passed directly to the Docker daemon. Images in the Docker Hub registry are available by default. Other repositories are specified with either repository-url/image:tag or repository-url/image@digest. TODO: Update these to specify using classes of IContainerImage
        :param command: The command that is passed to the container. If you provide a shell command as a single string, you have to quote command-line arguments. Default: - CMD value built into container image.
        :param container_name: The name of the container. Default: - id of node associated with ContainerDefinition.
        :param cpu: The minimum number of CPU units to reserve for the container. Default: - No minimum CPU units reserved.
        :param disable_networking: Specifies whether networking is disabled within the container. When this parameter is true, networking is disabled within the container. Default: false
        :param dns_search_domains: A list of DNS search domains that are presented to the container. Default: - No search domains.
        :param dns_servers: A list of DNS servers that are presented to the container. Default: - Default DNS servers.
        :param docker_labels: A key/value map of labels to add to the container. Default: - No labels.
        :param docker_security_options: A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. Default: - No security labels.
        :param entry_point: The ENTRYPOINT value to pass to the container. Default: - Entry point configured in container.
        :param environment: The environment variables to pass to the container. Default: - No environment variables.
        :param environment_files: The environment files to pass to the container. Default: - No environment files.
        :param essential: Specifies whether the container is marked essential. If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped. If the essential parameter of a container is marked as false, then its failure does not affect the rest of the containers in a task. All tasks must have at least one essential container. If this parameter is omitted, a container is assumed to be essential. Default: true
        :param extra_hosts: A list of hostnames and IP address mappings to append to the /etc/hosts file on the container. Default: - No extra hosts.
        :param gpu_count: The number of GPUs assigned to the container. Default: - No GPUs assigned.
        :param health_check: The health check command and associated configuration parameters for the container. Default: - Health check configuration from container.
        :param hostname: The hostname to use for your container. Default: - Automatic hostname.
        :param inference_accelerator_resources: The inference accelerators referenced by the container. Default: - No inference accelerators assigned.
        :param linux_parameters: Linux-specific modifications that are applied to the container, such as Linux kernel capabilities. For more information see `KernelCapabilities <https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_KernelCapabilities.html>`_. Default: - No Linux parameters.
        :param logging: The log configuration specification for the container. Default: - Containers use the same logging driver that the Docker daemon uses.
        :param memory_limit_mib: The amount (in MiB) of memory to present to the container. If your container attempts to exceed the allocated memory, the container is terminated. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory limit.
        :param memory_reservation_mib: The soft limit (in MiB) of memory to reserve for the container. When system memory is under heavy contention, Docker attempts to keep the container memory to this soft limit. However, your container can consume more memory when it needs to, up to either the hard limit specified with the memory parameter (if applicable), or all of the available memory on the container instance, whichever comes first. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory reserved.
        :param port_mappings: The port mappings to add to the container definition. Default: - No ports are mapped.
        :param privileged: Specifies whether the container is marked as privileged. When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user). Default: false
        :param readonly_root_filesystem: When this parameter is true, the container is given read-only access to its root file system. Default: false
        :param secrets: The secret environment variables to pass to the container. Default: - No secret environment variables.
        :param start_timeout: Time duration (in seconds) to wait before giving up on resolving dependencies for a container. Default: - none
        :param stop_timeout: Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own. Default: - none
        :param system_controls: A list of namespaced kernel parameters to set in the container. Default: - No system controls are set.
        :param user: The user name to use inside the container. Default: root
        :param working_directory: The working directory in which to run commands inside the container. Default: /

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions(
            image=image,
            command=command,
            container_name=container_name,
            cpu=cpu,
            disable_networking=disable_networking,
            dns_search_domains=dns_search_domains,
            dns_servers=dns_servers,
            docker_labels=docker_labels,
            docker_security_options=docker_security_options,
            entry_point=entry_point,
            environment=environment,
            environment_files=environment_files,
            essential=essential,
            extra_hosts=extra_hosts,
            gpu_count=gpu_count,
            health_check=health_check,
            hostname=hostname,
            inference_accelerator_resources=inference_accelerator_resources,
            linux_parameters=linux_parameters,
            logging=logging,
            memory_limit_mib=memory_limit_mib,
            memory_reservation_mib=memory_reservation_mib,
            port_mappings=port_mappings,
            privileged=privileged,
            readonly_root_filesystem=readonly_root_filesystem,
            secrets=secrets,
            start_timeout=start_timeout,
            stop_timeout=stop_timeout,
            system_controls=system_controls,
            user=user,
            working_directory=working_directory,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions, jsii.invoke(self, "mutateContainerDefinition", [props]))


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.FirelensProps",
    jsii_struct_bases=[],
    name_mapping={"log_group": "logGroup", "parent_service": "parentService"},
)
class FirelensProps:
    def __init__(
        self,
        *,
        log_group: _aws_cdk_aws_logs_ceddda9d.LogGroup,
        parent_service: "Service",
    ) -> None:
        '''(experimental) Settings for the hook which mutates the application container to route logs through FireLens.

        :param log_group: (experimental) The log group into which logs should be routed.
        :param parent_service: (experimental) The parent service that is being mutated.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aceb6633b315022d8687596bd75918bf27f97bab07b5afe71b5de85deefef59c)
            check_type(argname="argument log_group", value=log_group, expected_type=type_hints["log_group"])
            check_type(argname="argument parent_service", value=parent_service, expected_type=type_hints["parent_service"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "log_group": log_group,
            "parent_service": parent_service,
        }

    @builtins.property
    def log_group(self) -> _aws_cdk_aws_logs_ceddda9d.LogGroup:
        '''(experimental) The log group into which logs should be routed.

        :stability: experimental
        '''
        result = self._values.get("log_group")
        assert result is not None, "Required property 'log_group' is missing"
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.LogGroup, result)

    @builtins.property
    def parent_service(self) -> "Service":
        '''(experimental) The parent service that is being mutated.

        :stability: experimental
        '''
        result = self._values.get("parent_service")
        assert result is not None, "Required property 'parent_service' is missing"
        return typing.cast("Service", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FirelensProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.HttpLoadBalancerProps",
    jsii_struct_bases=[],
    name_mapping={"requests_per_target": "requestsPerTarget"},
)
class HttpLoadBalancerProps:
    def __init__(
        self,
        *,
        requests_per_target: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param requests_per_target: (experimental) The number of ALB requests per target.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82df5b77ad12b766d5e63af5b466f4e55ce579599801b70669df556201e35c2c)
            check_type(argname="argument requests_per_target", value=requests_per_target, expected_type=type_hints["requests_per_target"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if requests_per_target is not None:
            self._values["requests_per_target"] = requests_per_target

    @builtins.property
    def requests_per_target(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The number of ALB requests per target.

        :stability: experimental
        '''
        result = self._values.get("requests_per_target")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "HttpLoadBalancerProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@aws-cdk-containers/ecs-service-extensions.IEnvironment")
class IEnvironment(typing_extensions.Protocol):
    '''(experimental) An environment into which to deploy a service.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="capacityType")
    def capacity_type(self) -> EnvironmentCapacityType:
        '''(experimental) The capacity type used by the service's cluster.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''(experimental) The name of this environment.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC into which environment services should be placed.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="addDefaultCloudMapNamespace")
    def add_default_cloud_map_namespace(
        self,
        *,
        name: builtins.str,
        type: typing.Optional[_aws_cdk_aws_servicediscovery_ceddda9d.NamespaceType] = None,
        use_for_service_connect: typing.Optional[builtins.bool] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Add a default cloudmap namespace to the environment's cluster.

        :param name: The name of the namespace, such as example.com.
        :param type: The type of CloudMap Namespace to create. Default: PrivateDns
        :param use_for_service_connect: This property specifies whether to set the provided namespace as the service connect default in the cluster properties. Default: false
        :param vpc: The VPC to associate the namespace with. This property is required for private DNS namespaces. Default: VPC of the cluster for Private DNS Namespace, otherwise none

        :stability: experimental
        '''
        ...


class _IEnvironmentProxy:
    '''(experimental) An environment into which to deploy a service.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk-containers/ecs-service-extensions.IEnvironment"

    @builtins.property
    @jsii.member(jsii_name="capacityType")
    def capacity_type(self) -> EnvironmentCapacityType:
        '''(experimental) The capacity type used by the service's cluster.

        :stability: experimental
        '''
        return typing.cast(EnvironmentCapacityType, jsii.get(self, "capacityType"))

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, jsii.get(self, "cluster"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''(experimental) The name of this environment.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC into which environment services should be placed.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))

    @jsii.member(jsii_name="addDefaultCloudMapNamespace")
    def add_default_cloud_map_namespace(
        self,
        *,
        name: builtins.str,
        type: typing.Optional[_aws_cdk_aws_servicediscovery_ceddda9d.NamespaceType] = None,
        use_for_service_connect: typing.Optional[builtins.bool] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Add a default cloudmap namespace to the environment's cluster.

        :param name: The name of the namespace, such as example.com.
        :param type: The type of CloudMap Namespace to create. Default: PrivateDns
        :param use_for_service_connect: This property specifies whether to set the provided namespace as the service connect default in the cluster properties. Default: false
        :param vpc: The VPC to associate the namespace with. This property is required for private DNS namespaces. Default: VPC of the cluster for Private DNS Namespace, otherwise none

        :stability: experimental
        '''
        options = _aws_cdk_aws_ecs_ceddda9d.CloudMapNamespaceOptions(
            name=name,
            type=type,
            use_for_service_connect=use_for_service_connect,
            vpc=vpc,
        )

        return typing.cast(None, jsii.invoke(self, "addDefaultCloudMapNamespace", [options]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IEnvironment).__jsii_proxy_class__ = lambda : _IEnvironmentProxy


@jsii.interface(jsii_type="@aws-cdk-containers/ecs-service-extensions.IInjectable")
class IInjectable(typing_extensions.Protocol):
    '''(experimental) An interface that will be implemented by all the resources that can be published events or written data to.

    :stability: experimental
    '''

    @jsii.member(jsii_name="environmentVariables")
    def environment_variables(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''
        :stability: experimental
        '''
        ...


class _IInjectableProxy:
    '''(experimental) An interface that will be implemented by all the resources that can be published events or written data to.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk-containers/ecs-service-extensions.IInjectable"

    @jsii.member(jsii_name="environmentVariables")
    def environment_variables(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.invoke(self, "environmentVariables", []))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IInjectable).__jsii_proxy_class__ = lambda : _IInjectableProxy


@jsii.interface(jsii_type="@aws-cdk-containers/ecs-service-extensions.ISubscribable")
class ISubscribable(typing_extensions.Protocol):
    '''(experimental) An interface that will be implemented by all the resources that can be subscribed to.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="subscriptionQueue")
    def subscription_queue(self) -> typing.Optional["SubscriptionQueue"]:
        '''(experimental) The ``SubscriptionQueue`` object for the ``ISubscribable`` object.

        :default: none

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="subscribe")
    def subscribe(
        self,
        extension: "QueueExtension",
    ) -> _aws_cdk_aws_sqs_ceddda9d.IQueue:
        '''(experimental) All classes implementing this interface must also implement the ``subscribe()`` method.

        :param extension: -

        :stability: experimental
        '''
        ...


class _ISubscribableProxy:
    '''(experimental) An interface that will be implemented by all the resources that can be subscribed to.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk-containers/ecs-service-extensions.ISubscribable"

    @builtins.property
    @jsii.member(jsii_name="subscriptionQueue")
    def subscription_queue(self) -> typing.Optional["SubscriptionQueue"]:
        '''(experimental) The ``SubscriptionQueue`` object for the ``ISubscribable`` object.

        :default: none

        :stability: experimental
        '''
        return typing.cast(typing.Optional["SubscriptionQueue"], jsii.get(self, "subscriptionQueue"))

    @jsii.member(jsii_name="subscribe")
    def subscribe(
        self,
        extension: "QueueExtension",
    ) -> _aws_cdk_aws_sqs_ceddda9d.IQueue:
        '''(experimental) All classes implementing this interface must also implement the ``subscribe()`` method.

        :param extension: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd1578190a97094d760d76a2f5cebe69df504113964828b89844073359391cb5)
            check_type(argname="argument extension", value=extension, expected_type=type_hints["extension"])
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.IQueue, jsii.invoke(self, "subscribe", [extension]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, ISubscribable).__jsii_proxy_class__ = lambda : _ISubscribableProxy


@jsii.implements(IEnvironment)
class ImportedEnvironment(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ImportedEnvironment",
):
    '''
    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        capacity_type: EnvironmentCapacityType,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
    ) -> None:
        '''
        :param scope: -
        :param id: The name of this environment.
        :param capacity_type: (experimental) The capacity type used by the service's cluster.
        :param cluster: (experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__91378335a3876039a3828c1245b7393e5a1292ba2a049277f1c28e0986b15b07)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = EnvironmentAttributes(capacity_type=capacity_type, cluster=cluster)

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addDefaultCloudMapNamespace")
    def add_default_cloud_map_namespace(
        self,
        *,
        name: builtins.str,
        type: typing.Optional[_aws_cdk_aws_servicediscovery_ceddda9d.NamespaceType] = None,
        use_for_service_connect: typing.Optional[builtins.bool] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Adding a default cloudmap namespace to the cluster will throw an error, as we don't own it.

        :param name: The name of the namespace, such as example.com.
        :param type: The type of CloudMap Namespace to create. Default: PrivateDns
        :param use_for_service_connect: This property specifies whether to set the provided namespace as the service connect default in the cluster properties. Default: false
        :param vpc: The VPC to associate the namespace with. This property is required for private DNS namespaces. Default: VPC of the cluster for Private DNS Namespace, otherwise none

        :stability: experimental
        '''
        _options = _aws_cdk_aws_ecs_ceddda9d.CloudMapNamespaceOptions(
            name=name,
            type=type,
            use_for_service_connect=use_for_service_connect,
            vpc=vpc,
        )

        return typing.cast(None, jsii.invoke(self, "addDefaultCloudMapNamespace", [_options]))

    @builtins.property
    @jsii.member(jsii_name="capacityType")
    def capacity_type(self) -> EnvironmentCapacityType:
        '''(experimental) The capacity type used by the service's cluster.

        :stability: experimental
        '''
        return typing.cast(EnvironmentCapacityType, jsii.get(self, "capacityType"))

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, jsii.get(self, "cluster"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''(experimental) The name of this environment.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC into which environment services should be placed.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.InjectableTopicProps",
    jsii_struct_bases=[],
    name_mapping={"topic": "topic"},
)
class InjectableTopicProps:
    def __init__(self, *, topic: _aws_cdk_aws_sns_ceddda9d.ITopic) -> None:
        '''(experimental) The settings for the ``InjectableTopic`` class.

        :param topic: (experimental) The SNS Topic to publish events to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5404fdd3e63bd485e4db5b2a113ebf7494d35cf4a96f038e9defb7d051989a59)
            check_type(argname="argument topic", value=topic, expected_type=type_hints["topic"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "topic": topic,
        }

    @builtins.property
    def topic(self) -> _aws_cdk_aws_sns_ceddda9d.ITopic:
        '''(experimental) The SNS Topic to publish events to.

        :stability: experimental
        '''
        result = self._values.get("topic")
        assert result is not None, "Required property 'topic' is missing"
        return typing.cast(_aws_cdk_aws_sns_ceddda9d.ITopic, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "InjectableTopicProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.InjecterExtensionProps",
    jsii_struct_bases=[],
    name_mapping={"injectables": "injectables"},
)
class InjecterExtensionProps:
    def __init__(self, *, injectables: typing.Sequence[IInjectable]) -> None:
        '''(experimental) The settings for the Injecter extension.

        :param injectables: (experimental) The list of injectable resources for this service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__764a4ce423345733d9211ae0ec978efe2db85a96e72389375cfe172603235a12)
            check_type(argname="argument injectables", value=injectables, expected_type=type_hints["injectables"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "injectables": injectables,
        }

    @builtins.property
    def injectables(self) -> typing.List[IInjectable]:
        '''(experimental) The list of injectable resources for this service.

        :stability: experimental
        '''
        result = self._values.get("injectables")
        assert result is not None, "Required property 'injectables' is missing"
        return typing.cast(typing.List[IInjectable], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "InjecterExtensionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.MeshProps",
    jsii_struct_bases=[],
    name_mapping={"mesh": "mesh", "protocol": "protocol"},
)
class MeshProps:
    def __init__(
        self,
        *,
        mesh: _aws_cdk_aws_appmesh_ceddda9d.Mesh,
        protocol: typing.Optional["Protocol"] = None,
    ) -> None:
        '''(experimental) The settings for the App Mesh extension.

        :param mesh: (experimental) The service mesh into which to register the service.
        :param protocol: (experimental) The protocol of the service. Valid values are Protocol.HTTP, Protocol.HTTP2, Protocol.TCP, Protocol.GRPC Default: - Protocol.HTTP

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__142846b40345638745bc1a3ab27f3cab5f854bdaf8ca3b69b33a43f481fd5f56)
            check_type(argname="argument mesh", value=mesh, expected_type=type_hints["mesh"])
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "mesh": mesh,
        }
        if protocol is not None:
            self._values["protocol"] = protocol

    @builtins.property
    def mesh(self) -> _aws_cdk_aws_appmesh_ceddda9d.Mesh:
        '''(experimental) The service mesh into which to register the service.

        :stability: experimental
        '''
        result = self._values.get("mesh")
        assert result is not None, "Required property 'mesh' is missing"
        return typing.cast(_aws_cdk_aws_appmesh_ceddda9d.Mesh, result)

    @builtins.property
    def protocol(self) -> typing.Optional["Protocol"]:
        '''(experimental) The protocol of the service.

        Valid values are Protocol.HTTP, Protocol.HTTP2, Protocol.TCP, Protocol.GRPC

        :default: - Protocol.HTTP

        :stability: experimental
        '''
        result = self._values.get("protocol")
        return typing.cast(typing.Optional["Protocol"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MeshProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@aws-cdk-containers/ecs-service-extensions.Protocol")
class Protocol(enum.Enum):
    '''(experimental) Enum of supported AppMesh protocols.

    :stability: experimental
    '''

    HTTP = "HTTP"
    '''
    :stability: experimental
    '''
    TCP = "TCP"
    '''
    :stability: experimental
    '''
    HTTP2 = "HTTP2"
    '''
    :stability: experimental
    '''
    GRPC = "GRPC"
    '''
    :stability: experimental
    '''


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.QueueAutoScalingOptions",
    jsii_struct_bases=[],
    name_mapping={
        "acceptable_latency": "acceptableLatency",
        "message_processing_time": "messageProcessingTime",
    },
)
class QueueAutoScalingOptions:
    def __init__(
        self,
        *,
        acceptable_latency: _aws_cdk_ceddda9d.Duration,
        message_processing_time: _aws_cdk_ceddda9d.Duration,
    ) -> None:
        '''(experimental) Options for configuring SQS Queue auto scaling.

        :param acceptable_latency: (experimental) Acceptable amount of time a message can sit in the queue (including the time required to process it).
        :param message_processing_time: (experimental) Average amount of time for processing a single message in the queue.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a69b597f7f7ad40eda264d309c915a018cfc7e08a24d4fd3431b480aebba63ba)
            check_type(argname="argument acceptable_latency", value=acceptable_latency, expected_type=type_hints["acceptable_latency"])
            check_type(argname="argument message_processing_time", value=message_processing_time, expected_type=type_hints["message_processing_time"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "acceptable_latency": acceptable_latency,
            "message_processing_time": message_processing_time,
        }

    @builtins.property
    def acceptable_latency(self) -> _aws_cdk_ceddda9d.Duration:
        '''(experimental) Acceptable amount of time a message can sit in the queue (including the time required to process it).

        :stability: experimental
        '''
        result = self._values.get("acceptable_latency")
        assert result is not None, "Required property 'acceptable_latency' is missing"
        return typing.cast(_aws_cdk_ceddda9d.Duration, result)

    @builtins.property
    def message_processing_time(self) -> _aws_cdk_ceddda9d.Duration:
        '''(experimental) Average amount of time for processing a single message in the queue.

        :stability: experimental
        '''
        result = self._values.get("message_processing_time")
        assert result is not None, "Required property 'message_processing_time' is missing"
        return typing.cast(_aws_cdk_ceddda9d.Duration, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "QueueAutoScalingOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.QueueExtensionProps",
    jsii_struct_bases=[],
    name_mapping={
        "events_queue": "eventsQueue",
        "scale_on_latency": "scaleOnLatency",
        "subscriptions": "subscriptions",
    },
)
class QueueExtensionProps:
    def __init__(
        self,
        *,
        events_queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
        scale_on_latency: typing.Optional[typing.Union[QueueAutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        subscriptions: typing.Optional[typing.Sequence[ISubscribable]] = None,
    ) -> None:
        '''(experimental) The settings for the Queue extension.

        :param events_queue: (experimental) The user-provided default queue for this service. If the ``eventsQueue`` is not provided, a default SQS Queue is created for the service. Default: none
        :param scale_on_latency: (experimental) The user-provided queue delay fields to configure auto scaling for the default queue. Default: none
        :param subscriptions: (experimental) The list of subscriptions for this service. Default: none

        :stability: experimental
        '''
        if isinstance(scale_on_latency, dict):
            scale_on_latency = QueueAutoScalingOptions(**scale_on_latency)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b4718a77605fed94d29789c1a434b9fcc1ae492a2a3de2712231624c092820cb)
            check_type(argname="argument events_queue", value=events_queue, expected_type=type_hints["events_queue"])
            check_type(argname="argument scale_on_latency", value=scale_on_latency, expected_type=type_hints["scale_on_latency"])
            check_type(argname="argument subscriptions", value=subscriptions, expected_type=type_hints["subscriptions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if events_queue is not None:
            self._values["events_queue"] = events_queue
        if scale_on_latency is not None:
            self._values["scale_on_latency"] = scale_on_latency
        if subscriptions is not None:
            self._values["subscriptions"] = subscriptions

    @builtins.property
    def events_queue(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue]:
        '''(experimental) The user-provided default queue for this service.

        If the ``eventsQueue`` is not provided, a default SQS Queue is created for the service.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("events_queue")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue], result)

    @builtins.property
    def scale_on_latency(self) -> typing.Optional[QueueAutoScalingOptions]:
        '''(experimental) The user-provided queue delay fields to configure auto scaling for the default queue.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("scale_on_latency")
        return typing.cast(typing.Optional[QueueAutoScalingOptions], result)

    @builtins.property
    def subscriptions(self) -> typing.Optional[typing.List[ISubscribable]]:
        '''(experimental) The list of subscriptions for this service.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("subscriptions")
        return typing.cast(typing.Optional[typing.List[ISubscribable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "QueueExtensionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Service(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.Service",
):
    '''(experimental) This Service construct serves as a Builder class for an ECS service.

    It
    supports various extensions and keeps track of any mutating state, allowing
    it to build up an ECS service progressively.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        environment: IEnvironment,
        service_description: "ServiceDescription",
        auto_scale_task_count: typing.Optional[typing.Union[AutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param environment: (experimental) The environment to launch the service in.
        :param service_description: (experimental) The ServiceDescription used to build the service.
        :param auto_scale_task_count: (experimental) The options for configuring the auto scaling target. Default: none
        :param desired_count: (experimental) The desired number of instantiations of the task definition to keep running on the service. Default: - When creating the service, default is 1; when updating the service, default uses the current task number.
        :param task_role: (experimental) The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf. Default: - A task role is automatically created for you.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__db3cb686a45270fdd7e768c5ae18b4f4f6f2162d2173f63f7c535361b5a43ee0)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ServiceProps(
            environment=environment,
            service_description=service_description,
            auto_scale_task_count=auto_scale_task_count,
            desired_count=desired_count,
            task_role=task_role,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addURL")
    def add_url(self, url_name: builtins.str, url: builtins.str) -> None:
        '''(experimental) This method adds a new URL for the service.

        This allows extensions to
        submit a URL for the service. For example, a load balancer might add its
        URL, or App Mesh can add its DNS name for the service.

        :param url_name: - The identifier name for this URL.
        :param url: - The URL itself.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__502b75d7c9b239a450ef6b60bf75138f9e9ad1bf1db3c86bae3750bb5b2ddb85)
            check_type(argname="argument url_name", value=url_name, expected_type=type_hints["url_name"])
            check_type(argname="argument url", value=url, expected_type=type_hints["url"])
        return typing.cast(None, jsii.invoke(self, "addURL", [url_name, url]))

    @jsii.member(jsii_name="connectTo")
    def connect_to(
        self,
        service: "Service",
        *,
        local_bind_port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(experimental) Tell extensions from one service to connect to extensions from another sevice if they have implemented a hook for it.

        :param service: -
        :param local_bind_port: (experimental) localBindPort is the local port that this application should use when calling the upstream service in ECS Consul Mesh Extension Currently, this parameter will only be used in the ECSConsulMeshExtension https://github.com/aws-ia/ecs-consul-mesh-extension.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__74fb3efae7913ceb8ccea9c9b3493498efca8dbd55fc5e00f7140f8a17ed89a9)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        connect_to_props = ConnectToProps(local_bind_port=local_bind_port)

        return typing.cast(None, jsii.invoke(self, "connectTo", [service, connect_to_props]))

    @jsii.member(jsii_name="enableAutoScalingPolicy")
    def enable_auto_scaling_policy(self) -> None:
        '''(experimental) This helper method is used to set the ``autoScalingPoliciesEnabled`` attribute whenever an auto scaling policy is configured for the service.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "enableAutoScalingPolicy", []))

    @jsii.member(jsii_name="getURL")
    def get_url(self, url_name: builtins.str) -> builtins.str:
        '''(experimental) Retrieve a URL for the service.

        The URL must have previously been
        stored by one of the URL providing extensions.

        :param url_name: - The URL to look up.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f9661ad5046e27393ad9a87be136fc5dff0e8a0c90ab0d53f12343c56b38af2)
            check_type(argname="argument url_name", value=url_name, expected_type=type_hints["url_name"])
        return typing.cast(builtins.str, jsii.invoke(self, "getURL", [url_name]))

    @builtins.property
    @jsii.member(jsii_name="capacityType")
    def capacity_type(self) -> EnvironmentCapacityType:
        '''(experimental) The capacity type that this service will use.

        Valid values are EC2 or FARGATE.

        :stability: experimental
        '''
        return typing.cast(EnvironmentCapacityType, jsii.get(self, "capacityType"))

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        [disable-awslint:ref-via-interface]

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, jsii.get(self, "cluster"))

    @builtins.property
    @jsii.member(jsii_name="environment")
    def environment(self) -> IEnvironment:
        '''(experimental) The environment where this service was launched.

        :stability: experimental
        '''
        return typing.cast(IEnvironment, jsii.get(self, "environment"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''(experimental) The name of the service.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="serviceDescription")
    def service_description(self) -> "ServiceDescription":
        '''(experimental) The ServiceDescription used to build this service.

        :stability: experimental
        '''
        return typing.cast("ServiceDescription", jsii.get(self, "serviceDescription"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC where this service should be placed.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))

    @builtins.property
    @jsii.member(jsii_name="scalableTaskCount")
    def scalable_task_count(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ScalableTaskCount]:
        '''(experimental) The scalable attribute representing task count.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ScalableTaskCount], jsii.get(self, "scalableTaskCount"))

    @builtins.property
    @jsii.member(jsii_name="ecsService")
    def ecs_service(
        self,
    ) -> typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService]:
        '''(experimental) The underlying ECS service that was created.

        :stability: experimental
        '''
        return typing.cast(typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService], jsii.get(self, "ecsService"))

    @ecs_service.setter
    def ecs_service(
        self,
        value: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48e0b209d664b802d972b8c57029dfafa732ddd80d7f15177ec1c19fa4ee27e4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ecsService", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="taskDefinition")
    def _task_definition(self) -> _aws_cdk_aws_ecs_ceddda9d.TaskDefinition:
        '''(experimental) The generated task definition for this service.

        It is only
        generated after .prepare() has been executed.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.TaskDefinition, jsii.get(self, "taskDefinition"))

    @_task_definition.setter
    def _task_definition(self, value: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__43501a7df8adf21fb5b2baed0861c8d54532787b41d74a178e59fb2f8d7cb4c7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "taskDefinition", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="targetGroup")
    def target_group(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroup]:
        '''(experimental) The application target group if the service has an HTTPLoadBalancerExtension.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroup], jsii.get(self, "targetGroup"))

    @target_group.setter
    def target_group(
        self,
        value: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroup],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee366325f772dd64ac0fb090f415241df9c08abd4c10129d4accf09912d2ae3f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "targetGroup", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ServiceBuild",
    jsii_struct_bases=[],
    name_mapping={
        "cluster": "cluster",
        "task_definition": "taskDefinition",
        "assign_public_ip": "assignPublicIp",
        "cloud_map_options": "cloudMapOptions",
        "desired_count": "desiredCount",
        "health_check_grace_period": "healthCheckGracePeriod",
        "max_healthy_percent": "maxHealthyPercent",
        "min_healthy_percent": "minHealthyPercent",
        "service_connect_configuration": "serviceConnectConfiguration",
    },
)
class ServiceBuild:
    def __init__(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) A set of mutable service props in the process of being assembled using a builder pattern.

        They will eventually to be translated into an
        ecs.Ec2ServiceProps or ecs.FargateServiceProps interface, depending on the
        environment's capacity type.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        if isinstance(cloud_map_options, dict):
            cloud_map_options = _aws_cdk_aws_ecs_ceddda9d.CloudMapOptions(**cloud_map_options)
        if isinstance(service_connect_configuration, dict):
            service_connect_configuration = _aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps(**service_connect_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bbc157cc76350e79845bf03bad3f7df149e831066f26c4ce897b5f0aa26318c9)
            check_type(argname="argument cluster", value=cluster, expected_type=type_hints["cluster"])
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
            check_type(argname="argument assign_public_ip", value=assign_public_ip, expected_type=type_hints["assign_public_ip"])
            check_type(argname="argument cloud_map_options", value=cloud_map_options, expected_type=type_hints["cloud_map_options"])
            check_type(argname="argument desired_count", value=desired_count, expected_type=type_hints["desired_count"])
            check_type(argname="argument health_check_grace_period", value=health_check_grace_period, expected_type=type_hints["health_check_grace_period"])
            check_type(argname="argument max_healthy_percent", value=max_healthy_percent, expected_type=type_hints["max_healthy_percent"])
            check_type(argname="argument min_healthy_percent", value=min_healthy_percent, expected_type=type_hints["min_healthy_percent"])
            check_type(argname="argument service_connect_configuration", value=service_connect_configuration, expected_type=type_hints["service_connect_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cluster": cluster,
            "task_definition": task_definition,
        }
        if assign_public_ip is not None:
            self._values["assign_public_ip"] = assign_public_ip
        if cloud_map_options is not None:
            self._values["cloud_map_options"] = cloud_map_options
        if desired_count is not None:
            self._values["desired_count"] = desired_count
        if health_check_grace_period is not None:
            self._values["health_check_grace_period"] = health_check_grace_period
        if max_healthy_percent is not None:
            self._values["max_healthy_percent"] = max_healthy_percent
        if min_healthy_percent is not None:
            self._values["min_healthy_percent"] = min_healthy_percent
        if service_connect_configuration is not None:
            self._values["service_connect_configuration"] = service_connect_configuration

    @builtins.property
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster in which to launch the service.

        :stability: experimental
        '''
        result = self._values.get("cluster")
        assert result is not None, "Required property 'cluster' is missing"
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, result)

    @builtins.property
    def task_definition(self) -> _aws_cdk_aws_ecs_ceddda9d.TaskDefinition:
        '''(experimental) The task definition registered to this service.

        :stability: experimental
        '''
        result = self._values.get("task_definition")
        assert result is not None, "Required property 'task_definition' is missing"
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.TaskDefinition, result)

    @builtins.property
    def assign_public_ip(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Specifies whether the task's elastic network interface receives a public IP address.

        If true, each task will receive a public IP address.

        :default: - false

        :stability: experimental
        '''
        result = self._values.get("assign_public_ip")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def cloud_map_options(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions]:
        '''(experimental) Configuration for how to register the service in service discovery.

        :default: - No Cloud Map configured

        :stability: experimental
        '''
        result = self._values.get("cloud_map_options")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions], result)

    @builtins.property
    def desired_count(self) -> typing.Optional[jsii.Number]:
        '''(experimental) How many tasks to run.

        :default: - 1

        :stability: experimental
        '''
        result = self._values.get("desired_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def health_check_grace_period(self) -> typing.Optional[_aws_cdk_ceddda9d.Duration]:
        '''(experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy.

        This is used to give the task more
        time to start passing healthchecks.

        :default: - No grace period

        :stability: experimental
        '''
        result = self._values.get("health_check_grace_period")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.Duration], result)

    @builtins.property
    def max_healthy_percent(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Maximum percentage of tasks that can be launched.

        :default: - 200

        :stability: experimental
        '''
        result = self._values.get("max_healthy_percent")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_healthy_percent(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Minimum healthy task percentage.

        :default: - 100

        :stability: experimental
        '''
        result = self._values.get("min_healthy_percent")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def service_connect_configuration(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps]:
        '''(experimental) Configuration for service connect for this service.

        :default: - No Service Connect configured.

        :stability: experimental
        '''
        result = self._values.get("service_connect_configuration")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ServiceBuild(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ServiceDescription(
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ServiceDescription",
):
    '''(experimental) A ServiceDescription is a wrapper for all of the extensions that a user wants to add to an ECS Service.

    It collects all of the extensions that are added
    to a service, allowing each extension to query the full list of extensions
    added to a service to determine information about how to self-configure.

    :stability: experimental
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="add")
    def add(self, extension: "ServiceExtension") -> "ServiceDescription":
        '''(experimental) Adds a new extension to the service.

        The extensions mutate a service
        to add resources to or configure properties for the service.

        :param extension: - The extension that you wish to add.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c093f5c31129726d3d125fea26e2c3fd91a85698eb1ba8473769eac664ab595a)
            check_type(argname="argument extension", value=extension, expected_type=type_hints["extension"])
        return typing.cast("ServiceDescription", jsii.invoke(self, "add", [extension]))

    @jsii.member(jsii_name="get")
    def get(self, name: builtins.str) -> "ServiceExtension":
        '''(experimental) Get the extension with a specific name.

        This is generally used by
        extensions in order to discover each other.

        :param name: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8352914d442a0691483353eb819f6ab07a7c3906ffcb4a5f205881cab8855693)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        return typing.cast("ServiceExtension", jsii.invoke(self, "get", [name]))

    @builtins.property
    @jsii.member(jsii_name="extensions")
    def extensions(self) -> typing.Mapping[builtins.str, "ServiceExtension"]:
        '''(experimental) The list of extensions that have been registered to run when preparing this service.

        :stability: experimental
        '''
        return typing.cast(typing.Mapping[builtins.str, "ServiceExtension"], jsii.get(self, "extensions"))

    @extensions.setter
    def extensions(
        self,
        value: typing.Mapping[builtins.str, "ServiceExtension"],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3cc49fbfe806b68e28897ef0a6adb82ef13ea662595a6dc16cfbd1c8f3d80ff)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "extensions", value) # pyright: ignore[reportArgumentType]


class ServiceExtension(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ServiceExtension",
):
    '''(experimental) The shape of a service extension.

    This abstract class is implemented
    by other extensions that extend the hooks to implement any custom
    logic that they want to run during each step of preparing the service.

    :stability: experimental
    '''

    def __init__(self, name: builtins.str) -> None:
        '''
        :param name: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1942fe00f761e2c51266b2c817c5520489ca4dfc5fb00a8121bfc670fbf52e3f)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        jsii.create(self.__class__, self, [name])

    @jsii.member(jsii_name="addContainerMutatingHook")
    def add_container_mutating_hook(self, hook: ContainerMutatingHook) -> None:
        '''(experimental) This hook allows another service extension to register a mutating hook for changing the primary container of this extension.

        This is primarily used
        for the application extension. For example, the Firelens extension wants to
        be able to modify the settings of the application container to
        route logs through Firelens.

        :param hook: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__67016c4360f564fd4fe54d7d2b5edd75e564f902aee57e11136af32477ecb5c5)
            check_type(argname="argument hook", value=hook, expected_type=type_hints["hook"])
        return typing.cast(None, jsii.invoke(self, "addContainerMutatingHook", [hook]))

    @jsii.member(jsii_name="addHooks")
    def add_hooks(self) -> None:
        '''(experimental) A hook that allows the extension to add hooks to other extensions that are registered.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "addHooks", []))

    @jsii.member(jsii_name="connectToService")
    def connect_to_service(
        self,
        service: Service,
        *,
        local_bind_port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(experimental) This hook allows the extension to establish a connection to extensions from another service.

        Usually used for things like
        allowing one service to talk to the load balancer or service mesh
        proxy for another service.

        :param service: - The other service to connect to.
        :param local_bind_port: (experimental) localBindPort is the local port that this application should use when calling the upstream service in ECS Consul Mesh Extension Currently, this parameter will only be used in the ECSConsulMeshExtension https://github.com/aws-ia/ecs-consul-mesh-extension.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e2d8de0dbe555c1e1b7b50b5b988162b03bc53d683e2a98a1659e95e6b1180c)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        connect_to_props = ConnectToProps(local_bind_port=local_bind_port)

        return typing.cast(None, jsii.invoke(self, "connectToService", [service, connect_to_props]))

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(experimental) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="modifyTaskDefinitionProps")
    def modify_task_definition_props(
        self,
        *,
        compatibility: _aws_cdk_aws_ecs_ceddda9d.Compatibility,
        cpu: typing.Optional[builtins.str] = None,
        ephemeral_storage_gib: typing.Optional[jsii.Number] = None,
        inference_accelerators: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.InferenceAccelerator, typing.Dict[builtins.str, typing.Any]]]] = None,
        ipc_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.IpcMode] = None,
        memory_mib: typing.Optional[builtins.str] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.NetworkMode] = None,
        pid_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.PidMode] = None,
        placement_constraints: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.PlacementConstraint]] = None,
        runtime_platform: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.RuntimePlatform, typing.Dict[builtins.str, typing.Any]]] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        family: typing.Optional[builtins.str] = None,
        proxy_configuration: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ProxyConfiguration] = None,
        task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        volumes: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.Volume, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps:
        '''(experimental) This is a hook which allows extensions to modify the settings of the task definition prior to it being created.

        For example, the App Mesh
        extension needs to configure an Envoy proxy in the task definition,
        or the Application extension wants to set the overall resource for
        the task.

        :param compatibility: The task launch type compatiblity requirement.
        :param cpu: The number of cpu units used by the task. If you are using the EC2 launch type, this field is optional and any value can be used. If you are using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the memory parameter: 256 (.25 vCPU) - Available memory values: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) 512 (.5 vCPU) - Available memory values: 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) 1024 (1 vCPU) - Available memory values: 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) 2048 (2 vCPU) - Available memory values: Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) 4096 (4 vCPU) - Available memory values: Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) 8192 (8 vCPU) - Available memory values: Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) 16384 (16 vCPU) - Available memory values: Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) Default: - CPU units are not specified.
        :param ephemeral_storage_gib: The amount (in GiB) of ephemeral storage to be allocated to the task. Only supported in Fargate platform version 1.4.0 or later. Default: - Undefined, in which case, the task will receive 20GiB ephemeral storage.
        :param inference_accelerators: The inference accelerators to use for the containers in the task. Not supported in Fargate. Default: - No inference accelerators.
        :param ipc_mode: The IPC resource namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - IpcMode used by the task is not specified
        :param memory_mib: The amount (in MiB) of memory used by the task. If using the EC2 launch type, this field is optional and any value can be used. If using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the cpu parameter: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) - Available cpu values: 256 (.25 vCPU) 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) - Available cpu values: 512 (.5 vCPU) 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) - Available cpu values: 1024 (1 vCPU) Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) - Available cpu values: 2048 (2 vCPU) Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) - Available cpu values: 4096 (4 vCPU) Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) - Available cpu values: 8192 (8 vCPU) Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) - Available cpu values: 16384 (16 vCPU) Default: - Memory used by task is not specified.
        :param network_mode: The networking mode to use for the containers in the task. On Fargate, the only supported networking mode is AwsVpc. Default: - NetworkMode.Bridge for EC2 & External tasks, AwsVpc for Fargate tasks.
        :param pid_mode: The process namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - PidMode used by the task is not specified
        :param placement_constraints: The placement constraints to use for tasks in the service. You can specify a maximum of 10 constraints per task (this limit includes constraints in the task definition and those specified at run time). Not supported in Fargate. Default: - No placement constraints.
        :param runtime_platform: The operating system that your task definitions are running on. A runtimePlatform is supported only for tasks using the Fargate launch type. Default: - Undefined.
        :param execution_role: The name of the IAM task execution role that grants the ECS agent permission to call AWS APIs on your behalf. The role will be used to retrieve container images from ECR and create CloudWatch log groups. Default: - An execution role will be automatically created if you use ECR images in your task definition.
        :param family: The name of a family that this task definition is registered to. A family groups multiple versions of a task definition. Default: - Automatically generated name.
        :param proxy_configuration: The configuration details for the App Mesh proxy. Default: - No proxy configuration.
        :param task_role: The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf. Default: - A task role is automatically created for you.
        :param volumes: The list of volume definitions for the task. For more information, see `Task Definition Parameter Volumes <https://docs.aws.amazon.com/AmazonECS/latest/developerguide//task_definition_parameters.html#volumes>`_. Default: - No volumes are passed to the Docker daemon on a container instance.

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps(
            compatibility=compatibility,
            cpu=cpu,
            ephemeral_storage_gib=ephemeral_storage_gib,
            inference_accelerators=inference_accelerators,
            ipc_mode=ipc_mode,
            memory_mib=memory_mib,
            network_mode=network_mode,
            pid_mode=pid_mode,
            placement_constraints=placement_constraints,
            runtime_platform=runtime_platform,
            execution_role=execution_role,
            family=family,
            proxy_configuration=proxy_configuration,
            task_role=task_role,
            volumes=volumes,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps, jsii.invoke(self, "modifyTaskDefinitionProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, parent: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param parent: - The parent service which this extension has been added to.
        :param scope: - The scope that this extension should create resources in.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eefdf655cd0e7f30d0fcf6f77a6d8729245c20be4605fa83182a750656dd59de)
            check_type(argname="argument parent", value=parent, expected_type=type_hints["parent"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [parent, scope]))

    @jsii.member(jsii_name="resolveContainerDependencies")
    def resolve_container_dependencies(self) -> None:
        '''(experimental) Once all containers are added to the task definition, this hook is called for each extension to give it a chance to resolve its dependency graph so that its container starts in the right order based on the other extensions that were enabled.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "resolveContainerDependencies", []))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(experimental) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is generally used to
        create any final resources which might depend on the service itself.

        :param service: - The generated service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38e3e0860e30eb48b790e6fc0840c9d9d36bff02f4ab4e976e145f4f85ef048d)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: - The created task definition to add containers to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e93694c5c40f28677d9914773fe2949cbdf32f19f86771a0f343852c4a456833)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))

    @builtins.property
    @jsii.member(jsii_name="containerMutatingHooks")
    def _container_mutating_hooks(self) -> typing.List[ContainerMutatingHook]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.List[ContainerMutatingHook], jsii.get(self, "containerMutatingHooks"))

    @_container_mutating_hooks.setter
    def _container_mutating_hooks(
        self,
        value: typing.List[ContainerMutatingHook],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__299f56627660a08293011eb309421e4c9ecab06a492c5135e001bb57465be12a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "containerMutatingHooks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''(experimental) The name of the extension.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffd5c720e9e1800e56e330f06b53101d51e941eae8399ed18a6ce3469d004a45)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parentService")
    def _parent_service(self) -> Service:
        '''(experimental) The service which this extension is being added to.

        Initially, extensions are collected into a ServiceDescription, but no service
        exists yet. Later, when the ServiceDescription is used to create a service,
        the extension is told what Service it is now working on.

        :stability: experimental
        '''
        return typing.cast(Service, jsii.get(self, "parentService"))

    @_parent_service.setter
    def _parent_service(self, value: Service) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__888537d4e44499688ac07459949d868e9b29b5f5b71d885c9f28d9f42d26a293)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parentService", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="scope")
    def _scope(self) -> _constructs_77d1e7e8.Construct:
        '''
        :stability: experimental
        '''
        return typing.cast(_constructs_77d1e7e8.Construct, jsii.get(self, "scope"))

    @_scope.setter
    def _scope(self, value: _constructs_77d1e7e8.Construct) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22b87c7ca09e39c9e04f952a479384b276834e484577d808867f6e8cd36eae87)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "scope", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="container")
    def container(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition]:
        '''(experimental) The container for this extension.

        Most extensions have a container, but not
        every extension is required to have a container. Some extensions may just
        modify the properties of the service, or create external resources
        connected to the service.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition], jsii.get(self, "container"))

    @container.setter
    def container(
        self,
        value: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54f71fbef259bce4d04ac1599a7734f8470b603b265ce3c405992e7d9403cc63)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "container", value) # pyright: ignore[reportArgumentType]


class _ServiceExtensionProxy(ServiceExtension):
    pass

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ServiceExtension).__jsii_proxy_class__ = lambda : _ServiceExtensionProxy


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ServiceProps",
    jsii_struct_bases=[],
    name_mapping={
        "environment": "environment",
        "service_description": "serviceDescription",
        "auto_scale_task_count": "autoScaleTaskCount",
        "desired_count": "desiredCount",
        "task_role": "taskRole",
    },
)
class ServiceProps:
    def __init__(
        self,
        *,
        environment: IEnvironment,
        service_description: ServiceDescription,
        auto_scale_task_count: typing.Optional[typing.Union[AutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    ) -> None:
        '''(experimental) The settings for an ECS Service.

        :param environment: (experimental) The environment to launch the service in.
        :param service_description: (experimental) The ServiceDescription used to build the service.
        :param auto_scale_task_count: (experimental) The options for configuring the auto scaling target. Default: none
        :param desired_count: (experimental) The desired number of instantiations of the task definition to keep running on the service. Default: - When creating the service, default is 1; when updating the service, default uses the current task number.
        :param task_role: (experimental) The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf. Default: - A task role is automatically created for you.

        :stability: experimental
        '''
        if isinstance(auto_scale_task_count, dict):
            auto_scale_task_count = AutoScalingOptions(**auto_scale_task_count)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8324f912a77ba2380fbec2194e091c70e44826a63d04c9b3b3178db416008d54)
            check_type(argname="argument environment", value=environment, expected_type=type_hints["environment"])
            check_type(argname="argument service_description", value=service_description, expected_type=type_hints["service_description"])
            check_type(argname="argument auto_scale_task_count", value=auto_scale_task_count, expected_type=type_hints["auto_scale_task_count"])
            check_type(argname="argument desired_count", value=desired_count, expected_type=type_hints["desired_count"])
            check_type(argname="argument task_role", value=task_role, expected_type=type_hints["task_role"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "environment": environment,
            "service_description": service_description,
        }
        if auto_scale_task_count is not None:
            self._values["auto_scale_task_count"] = auto_scale_task_count
        if desired_count is not None:
            self._values["desired_count"] = desired_count
        if task_role is not None:
            self._values["task_role"] = task_role

    @builtins.property
    def environment(self) -> IEnvironment:
        '''(experimental) The environment to launch the service in.

        :stability: experimental
        '''
        result = self._values.get("environment")
        assert result is not None, "Required property 'environment' is missing"
        return typing.cast(IEnvironment, result)

    @builtins.property
    def service_description(self) -> ServiceDescription:
        '''(experimental) The ServiceDescription used to build the service.

        :stability: experimental
        '''
        result = self._values.get("service_description")
        assert result is not None, "Required property 'service_description' is missing"
        return typing.cast(ServiceDescription, result)

    @builtins.property
    def auto_scale_task_count(self) -> typing.Optional[AutoScalingOptions]:
        '''(experimental) The options for configuring the auto scaling target.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("auto_scale_task_count")
        return typing.cast(typing.Optional[AutoScalingOptions], result)

    @builtins.property
    def desired_count(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The desired number of instantiations of the task definition to keep running on the service.

        :default:

        - When creating the service, default is 1; when updating the service, default uses
        the current task number.

        :stability: experimental
        '''
        result = self._values.get("desired_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def task_role(self) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole]:
        '''(experimental) The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf.

        :default: - A task role is automatically created for you.

        :stability: experimental
        '''
        result = self._values.get("task_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ServiceProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.SubscriptionQueue",
    jsii_struct_bases=[],
    name_mapping={"queue": "queue", "scale_on_latency": "scaleOnLatency"},
)
class SubscriptionQueue:
    def __init__(
        self,
        *,
        queue: _aws_cdk_aws_sqs_ceddda9d.IQueue,
        scale_on_latency: typing.Optional[typing.Union[QueueAutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) ``SubscriptionQueue`` represents the subscription queue object which includes the topic-specific queue and its corresponding auto scaling fields.

        :param queue: (experimental) The user-provided queue to subscribe to the given topic.
        :param scale_on_latency: (experimental) The user-provided queue delay fields to configure auto scaling for the topic-specific queue. Default: none

        :stability: experimental
        '''
        if isinstance(scale_on_latency, dict):
            scale_on_latency = QueueAutoScalingOptions(**scale_on_latency)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ab599485b374c44897ab0ae8820090231221b727f0f9968276a4071085689df)
            check_type(argname="argument queue", value=queue, expected_type=type_hints["queue"])
            check_type(argname="argument scale_on_latency", value=scale_on_latency, expected_type=type_hints["scale_on_latency"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "queue": queue,
        }
        if scale_on_latency is not None:
            self._values["scale_on_latency"] = scale_on_latency

    @builtins.property
    def queue(self) -> _aws_cdk_aws_sqs_ceddda9d.IQueue:
        '''(experimental) The user-provided queue to subscribe to the given topic.

        :stability: experimental
        '''
        result = self._values.get("queue")
        assert result is not None, "Required property 'queue' is missing"
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.IQueue, result)

    @builtins.property
    def scale_on_latency(self) -> typing.Optional[QueueAutoScalingOptions]:
        '''(experimental) The user-provided queue delay fields to configure auto scaling for the topic-specific queue.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("scale_on_latency")
        return typing.cast(typing.Optional[QueueAutoScalingOptions], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubscriptionQueue(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(ISubscribable)
class TopicSubscription(
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.TopicSubscription",
):
    '''(experimental) The ``TopicSubscription`` class represents an SNS Topic resource that can be subscribed to by the service queues.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
        queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
        topic_subscription_queue: typing.Optional[typing.Union[SubscriptionQueue, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param topic: (experimental) The SNS Topic to subscribe to.
        :param queue: (deprecated) The user-provided queue to subscribe to the given topic. Default: none
        :param topic_subscription_queue: (experimental) The object representing topic-specific queue and corresponding queue delay fields to configure auto scaling. If not provided, the default ``eventsQueue`` will subscribe to the given topic. Default: none

        :stability: experimental
        '''
        props = TopicSubscriptionProps(
            topic=topic, queue=queue, topic_subscription_queue=topic_subscription_queue
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="subscribe")
    def subscribe(
        self,
        extension: "QueueExtension",
    ) -> _aws_cdk_aws_sqs_ceddda9d.IQueue:
        '''(experimental) This method sets up SNS Topic subscriptions for the SQS queue provided by the user.

        If a ``queue`` is not provided,
        the default ``eventsQueue`` subscribes to the given topic.

        :param extension: ``QueueExtension`` added to the service.

        :return: the queue subscribed to the given topic

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__542dd993b9b30463def0028989d7fe8b3f0f9e422cb20bea69ab3b83367fbdb4)
            check_type(argname="argument extension", value=extension, expected_type=type_hints["extension"])
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.IQueue, jsii.invoke(self, "subscribe", [extension]))

    @builtins.property
    @jsii.member(jsii_name="topic")
    def topic(self) -> _aws_cdk_aws_sns_ceddda9d.ITopic:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_sns_ceddda9d.ITopic, jsii.get(self, "topic"))

    @builtins.property
    @jsii.member(jsii_name="queue")
    def queue(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue]:
        '''(deprecated) The queue that subscribes to the given topic.

        :default: none

        :deprecated: use ``subscriptionQueue``

        :stability: deprecated
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue], jsii.get(self, "queue"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionQueue")
    def subscription_queue(self) -> typing.Optional[SubscriptionQueue]:
        '''(experimental) The subscription queue object for this subscription.

        :default: none

        :stability: experimental
        '''
        return typing.cast(typing.Optional[SubscriptionQueue], jsii.get(self, "subscriptionQueue"))


@jsii.data_type(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.TopicSubscriptionProps",
    jsii_struct_bases=[],
    name_mapping={
        "topic": "topic",
        "queue": "queue",
        "topic_subscription_queue": "topicSubscriptionQueue",
    },
)
class TopicSubscriptionProps:
    def __init__(
        self,
        *,
        topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
        queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
        topic_subscription_queue: typing.Optional[typing.Union[SubscriptionQueue, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) The topic-specific settings for creating the queue subscriptions.

        :param topic: (experimental) The SNS Topic to subscribe to.
        :param queue: (deprecated) The user-provided queue to subscribe to the given topic. Default: none
        :param topic_subscription_queue: (experimental) The object representing topic-specific queue and corresponding queue delay fields to configure auto scaling. If not provided, the default ``eventsQueue`` will subscribe to the given topic. Default: none

        :stability: experimental
        '''
        if isinstance(topic_subscription_queue, dict):
            topic_subscription_queue = SubscriptionQueue(**topic_subscription_queue)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6ce31ca30734748c8286306049838377fd0ae5237a93f44655e549a682baaf92)
            check_type(argname="argument topic", value=topic, expected_type=type_hints["topic"])
            check_type(argname="argument queue", value=queue, expected_type=type_hints["queue"])
            check_type(argname="argument topic_subscription_queue", value=topic_subscription_queue, expected_type=type_hints["topic_subscription_queue"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "topic": topic,
        }
        if queue is not None:
            self._values["queue"] = queue
        if topic_subscription_queue is not None:
            self._values["topic_subscription_queue"] = topic_subscription_queue

    @builtins.property
    def topic(self) -> _aws_cdk_aws_sns_ceddda9d.ITopic:
        '''(experimental) The SNS Topic to subscribe to.

        :stability: experimental
        '''
        result = self._values.get("topic")
        assert result is not None, "Required property 'topic' is missing"
        return typing.cast(_aws_cdk_aws_sns_ceddda9d.ITopic, result)

    @builtins.property
    def queue(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue]:
        '''(deprecated) The user-provided queue to subscribe to the given topic.

        :default: none

        :deprecated: use ``topicSubscriptionQueue``

        :stability: deprecated
        '''
        result = self._values.get("queue")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue], result)

    @builtins.property
    def topic_subscription_queue(self) -> typing.Optional[SubscriptionQueue]:
        '''(experimental) The object representing topic-specific queue and corresponding queue delay fields to configure auto scaling.

        If not provided, the default ``eventsQueue`` will subscribe to the given topic.

        :default: none

        :stability: experimental
        '''
        result = self._values.get("topic_subscription_queue")
        return typing.cast(typing.Optional[SubscriptionQueue], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TopicSubscriptionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class XRayExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.XRayExtension",
):
    '''(experimental) This extension adds an X-Ray daemon inside the task definition for capturing application trace spans and submitting them to the AWS X-Ray service.

    :stability: experimental
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a25c259153e7aabb24a4f343378b533b165fcb42b53180b3fdd7f72da6371ad2)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="resolveContainerDependencies")
    def resolve_container_dependencies(self) -> None:
        '''(experimental) Once all containers are added to the task definition, this hook is called for each extension to give it a chance to resolve its dependency graph so that its container starts in the right order based on the other extensions that were enabled.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "resolveContainerDependencies", []))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__02d9f8aa0fd942e4f491eeddab502c60a5a201811637d732a37f9d950cb67311)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))


class AliasedPortExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AliasedPortExtension",
):
    '''
    :stability: experimental
    '''

    def __init__(
        self,
        *,
        alias: builtins.str,
        alias_port: typing.Optional[jsii.Number] = None,
        app_protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
    ) -> None:
        '''
        :param alias: (experimental) The DNS alias to advertise for downstream clients.
        :param alias_port: (experimental) The traffic port for clients to use to connect to the DNS alias. Default: - same as containerPort.
        :param app_protocol: (experimental) The protocol to use over the specified port. May be one of HTTP, HTTP2, or GRPC. Default: - none

        :stability: experimental
        '''
        props = AliasedPortProps(
            alias=alias, alias_port=alias_port, app_protocol=app_protocol
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="addHooks")
    def add_hooks(self) -> None:
        '''(experimental) A hook that allows the extension to add hooks to other extensions that are registered.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "addHooks", []))

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(experimental) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1043b521b7d8a62b95b2d33c980009a15390b055b8b23fb3fa89a4601d987fbe)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def _alias(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "alias"))

    @_alias.setter
    def _alias(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d404dfff99916347cd236463a68228c5807d4e62df7247b71f3de0207b4ecdb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "alias", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="aliasPort")
    def _alias_port(self) -> typing.Optional[jsii.Number]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "aliasPort"))

    @_alias_port.setter
    def _alias_port(self, value: typing.Optional[jsii.Number]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__69dab24a138f3970d3fecdca97edefcacb2ca2b0f643129d3cda322bcb9be285)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "aliasPort", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="appProtocol")
    def _app_protocol(self) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol], jsii.get(self, "appProtocol"))

    @_app_protocol.setter
    def _app_protocol(
        self,
        value: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e54f461371069afdb909684795279f736b187cc7fb5b7ef682d1fb827a6b0846)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "appProtocol", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def _namespace(self) -> typing.Optional[builtins.str]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespace"))

    @_namespace.setter
    def _namespace(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0681b9db0238b5ddb0fd915e2a2f44cec1c3d21ec400322498e8bfe207d0f483)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "namespace", value) # pyright: ignore[reportArgumentType]


class AliasedPortMutatingHook(
    ContainerMutatingHook,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AliasedPortMutatingHook",
):
    '''(experimental) This hook modifies the application container's settings so that its primary port mapping has a name.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        alias_port: jsii.Number,
        port_mapping_name: builtins.str,
        protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
    ) -> None:
        '''
        :param alias_port: (experimental) The port on the container which receives traffic. This is the same as the ``containerPort`` property of port mapping.
        :param port_mapping_name: (experimental) The name by which to refer to this port mapping.
        :param protocol: (experimental) The protocol which this port mapping expects to receive. Default: - none

        :stability: experimental
        '''
        props = AliasedPortMutatingHookProps(
            alias_port=alias_port,
            port_mapping_name=port_mapping_name,
            protocol=protocol,
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="mutateContainerDefinition")
    def mutate_container_definition(
        self,
        *,
        image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
        command: typing.Optional[typing.Sequence[builtins.str]] = None,
        container_name: typing.Optional[builtins.str] = None,
        cpu: typing.Optional[jsii.Number] = None,
        disable_networking: typing.Optional[builtins.bool] = None,
        dns_search_domains: typing.Optional[typing.Sequence[builtins.str]] = None,
        dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
        docker_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        docker_security_options: typing.Optional[typing.Sequence[builtins.str]] = None,
        entry_point: typing.Optional[typing.Sequence[builtins.str]] = None,
        environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
        essential: typing.Optional[builtins.bool] = None,
        extra_hosts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        gpu_count: typing.Optional[jsii.Number] = None,
        health_check: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.HealthCheck, typing.Dict[builtins.str, typing.Any]]] = None,
        hostname: typing.Optional[builtins.str] = None,
        inference_accelerator_resources: typing.Optional[typing.Sequence[builtins.str]] = None,
        linux_parameters: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LinuxParameters] = None,
        logging: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.LogDriver] = None,
        memory_limit_mib: typing.Optional[jsii.Number] = None,
        memory_reservation_mib: typing.Optional[jsii.Number] = None,
        port_mappings: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.PortMapping, typing.Dict[builtins.str, typing.Any]]]] = None,
        privileged: typing.Optional[builtins.bool] = None,
        readonly_root_filesystem: typing.Optional[builtins.bool] = None,
        secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
        start_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        stop_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        system_controls: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.SystemControl, typing.Dict[builtins.str, typing.Any]]]] = None,
        user: typing.Optional[builtins.str] = None,
        working_directory: typing.Optional[builtins.str] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions:
        '''(experimental) This is a hook for modifying the container definition of any upstream containers.

        This is primarily used for the main application container.
        For example, the Firelens extension wants to be able to modify the logging
        settings of the application container.

        :param image: The image used to start a container. This string is passed directly to the Docker daemon. Images in the Docker Hub registry are available by default. Other repositories are specified with either repository-url/image:tag or repository-url/image@digest. TODO: Update these to specify using classes of IContainerImage
        :param command: The command that is passed to the container. If you provide a shell command as a single string, you have to quote command-line arguments. Default: - CMD value built into container image.
        :param container_name: The name of the container. Default: - id of node associated with ContainerDefinition.
        :param cpu: The minimum number of CPU units to reserve for the container. Default: - No minimum CPU units reserved.
        :param disable_networking: Specifies whether networking is disabled within the container. When this parameter is true, networking is disabled within the container. Default: false
        :param dns_search_domains: A list of DNS search domains that are presented to the container. Default: - No search domains.
        :param dns_servers: A list of DNS servers that are presented to the container. Default: - Default DNS servers.
        :param docker_labels: A key/value map of labels to add to the container. Default: - No labels.
        :param docker_security_options: A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. Default: - No security labels.
        :param entry_point: The ENTRYPOINT value to pass to the container. Default: - Entry point configured in container.
        :param environment: The environment variables to pass to the container. Default: - No environment variables.
        :param environment_files: The environment files to pass to the container. Default: - No environment files.
        :param essential: Specifies whether the container is marked essential. If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped. If the essential parameter of a container is marked as false, then its failure does not affect the rest of the containers in a task. All tasks must have at least one essential container. If this parameter is omitted, a container is assumed to be essential. Default: true
        :param extra_hosts: A list of hostnames and IP address mappings to append to the /etc/hosts file on the container. Default: - No extra hosts.
        :param gpu_count: The number of GPUs assigned to the container. Default: - No GPUs assigned.
        :param health_check: The health check command and associated configuration parameters for the container. Default: - Health check configuration from container.
        :param hostname: The hostname to use for your container. Default: - Automatic hostname.
        :param inference_accelerator_resources: The inference accelerators referenced by the container. Default: - No inference accelerators assigned.
        :param linux_parameters: Linux-specific modifications that are applied to the container, such as Linux kernel capabilities. For more information see `KernelCapabilities <https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_KernelCapabilities.html>`_. Default: - No Linux parameters.
        :param logging: The log configuration specification for the container. Default: - Containers use the same logging driver that the Docker daemon uses.
        :param memory_limit_mib: The amount (in MiB) of memory to present to the container. If your container attempts to exceed the allocated memory, the container is terminated. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory limit.
        :param memory_reservation_mib: The soft limit (in MiB) of memory to reserve for the container. When system memory is under heavy contention, Docker attempts to keep the container memory to this soft limit. However, your container can consume more memory when it needs to, up to either the hard limit specified with the memory parameter (if applicable), or all of the available memory on the container instance, whichever comes first. At least one of memoryLimitMiB and memoryReservationMiB is required for non-Fargate services. Default: - No memory reserved.
        :param port_mappings: The port mappings to add to the container definition. Default: - No ports are mapped.
        :param privileged: Specifies whether the container is marked as privileged. When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user). Default: false
        :param readonly_root_filesystem: When this parameter is true, the container is given read-only access to its root file system. Default: false
        :param secrets: The secret environment variables to pass to the container. Default: - No secret environment variables.
        :param start_timeout: Time duration (in seconds) to wait before giving up on resolving dependencies for a container. Default: - none
        :param stop_timeout: Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own. Default: - none
        :param system_controls: A list of namespaced kernel parameters to set in the container. Default: - No system controls are set.
        :param user: The user name to use inside the container. Default: root
        :param working_directory: The working directory in which to run commands inside the container. Default: /

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions(
            image=image,
            command=command,
            container_name=container_name,
            cpu=cpu,
            disable_networking=disable_networking,
            dns_search_domains=dns_search_domains,
            dns_servers=dns_servers,
            docker_labels=docker_labels,
            docker_security_options=docker_security_options,
            entry_point=entry_point,
            environment=environment,
            environment_files=environment_files,
            essential=essential,
            extra_hosts=extra_hosts,
            gpu_count=gpu_count,
            health_check=health_check,
            hostname=hostname,
            inference_accelerator_resources=inference_accelerator_resources,
            linux_parameters=linux_parameters,
            logging=logging,
            memory_limit_mib=memory_limit_mib,
            memory_reservation_mib=memory_reservation_mib,
            port_mappings=port_mappings,
            privileged=privileged,
            readonly_root_filesystem=readonly_root_filesystem,
            secrets=secrets,
            start_timeout=start_timeout,
            stop_timeout=stop_timeout,
            system_controls=system_controls,
            user=user,
            working_directory=working_directory,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ContainerDefinitionOptions, jsii.invoke(self, "mutateContainerDefinition", [props]))


class AppMeshExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AppMeshExtension",
):
    '''(experimental) This extension adds an Envoy sidecar to the task definition and creates the App Mesh resources required to route network traffic to the container in a service mesh.

    The service will then be available to other App Mesh services at the
    address ``<service name>.<environment name>``. For example, a service called
    ``orders`` deploying in an environment called ``production`` would be accessible
    to other App Mesh enabled services at the address ``http://orders.production``.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        mesh: _aws_cdk_aws_appmesh_ceddda9d.Mesh,
        protocol: typing.Optional[Protocol] = None,
    ) -> None:
        '''
        :param mesh: (experimental) The service mesh into which to register the service.
        :param protocol: (experimental) The protocol of the service. Valid values are Protocol.HTTP, Protocol.HTTP2, Protocol.TCP, Protocol.GRPC Default: - Protocol.HTTP

        :stability: experimental
        '''
        props = MeshProps(mesh=mesh, protocol=protocol)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="connectToService")
    def connect_to_service(
        self,
        other_service: Service,
        *,
        local_bind_port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(experimental) This hook allows the extension to establish a connection to extensions from another service.

        Usually used for things like
        allowing one service to talk to the load balancer or service mesh
        proxy for another service.

        :param other_service: -
        :param local_bind_port: (experimental) localBindPort is the local port that this application should use when calling the upstream service in ECS Consul Mesh Extension Currently, this parameter will only be used in the ECSConsulMeshExtension https://github.com/aws-ia/ecs-consul-mesh-extension.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__46aa6bb7020052c416acf790220f414bc6b66910844ccb7115c05c2109ffc6bf)
            check_type(argname="argument other_service", value=other_service, expected_type=type_hints["other_service"])
        _connect_to_props = ConnectToProps(local_bind_port=local_bind_port)

        return typing.cast(None, jsii.invoke(self, "connectToService", [other_service, _connect_to_props]))

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(experimental) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="modifyTaskDefinitionProps")
    def modify_task_definition_props(
        self,
        *,
        compatibility: _aws_cdk_aws_ecs_ceddda9d.Compatibility,
        cpu: typing.Optional[builtins.str] = None,
        ephemeral_storage_gib: typing.Optional[jsii.Number] = None,
        inference_accelerators: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.InferenceAccelerator, typing.Dict[builtins.str, typing.Any]]]] = None,
        ipc_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.IpcMode] = None,
        memory_mib: typing.Optional[builtins.str] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.NetworkMode] = None,
        pid_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.PidMode] = None,
        placement_constraints: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.PlacementConstraint]] = None,
        runtime_platform: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.RuntimePlatform, typing.Dict[builtins.str, typing.Any]]] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        family: typing.Optional[builtins.str] = None,
        proxy_configuration: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ProxyConfiguration] = None,
        task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        volumes: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.Volume, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps:
        '''(experimental) This is a hook which allows extensions to modify the settings of the task definition prior to it being created.

        For example, the App Mesh
        extension needs to configure an Envoy proxy in the task definition,
        or the Application extension wants to set the overall resource for
        the task.

        :param compatibility: The task launch type compatiblity requirement.
        :param cpu: The number of cpu units used by the task. If you are using the EC2 launch type, this field is optional and any value can be used. If you are using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the memory parameter: 256 (.25 vCPU) - Available memory values: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) 512 (.5 vCPU) - Available memory values: 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) 1024 (1 vCPU) - Available memory values: 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) 2048 (2 vCPU) - Available memory values: Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) 4096 (4 vCPU) - Available memory values: Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) 8192 (8 vCPU) - Available memory values: Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) 16384 (16 vCPU) - Available memory values: Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) Default: - CPU units are not specified.
        :param ephemeral_storage_gib: The amount (in GiB) of ephemeral storage to be allocated to the task. Only supported in Fargate platform version 1.4.0 or later. Default: - Undefined, in which case, the task will receive 20GiB ephemeral storage.
        :param inference_accelerators: The inference accelerators to use for the containers in the task. Not supported in Fargate. Default: - No inference accelerators.
        :param ipc_mode: The IPC resource namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - IpcMode used by the task is not specified
        :param memory_mib: The amount (in MiB) of memory used by the task. If using the EC2 launch type, this field is optional and any value can be used. If using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the cpu parameter: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) - Available cpu values: 256 (.25 vCPU) 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) - Available cpu values: 512 (.5 vCPU) 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) - Available cpu values: 1024 (1 vCPU) Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) - Available cpu values: 2048 (2 vCPU) Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) - Available cpu values: 4096 (4 vCPU) Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) - Available cpu values: 8192 (8 vCPU) Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) - Available cpu values: 16384 (16 vCPU) Default: - Memory used by task is not specified.
        :param network_mode: The networking mode to use for the containers in the task. On Fargate, the only supported networking mode is AwsVpc. Default: - NetworkMode.Bridge for EC2 & External tasks, AwsVpc for Fargate tasks.
        :param pid_mode: The process namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - PidMode used by the task is not specified
        :param placement_constraints: The placement constraints to use for tasks in the service. You can specify a maximum of 10 constraints per task (this limit includes constraints in the task definition and those specified at run time). Not supported in Fargate. Default: - No placement constraints.
        :param runtime_platform: The operating system that your task definitions are running on. A runtimePlatform is supported only for tasks using the Fargate launch type. Default: - Undefined.
        :param execution_role: The name of the IAM task execution role that grants the ECS agent permission to call AWS APIs on your behalf. The role will be used to retrieve container images from ECR and create CloudWatch log groups. Default: - An execution role will be automatically created if you use ECR images in your task definition.
        :param family: The name of a family that this task definition is registered to. A family groups multiple versions of a task definition. Default: - Automatically generated name.
        :param proxy_configuration: The configuration details for the App Mesh proxy. Default: - No proxy configuration.
        :param task_role: The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf. Default: - A task role is automatically created for you.
        :param volumes: The list of volume definitions for the task. For more information, see `Task Definition Parameter Volumes <https://docs.aws.amazon.com/AmazonECS/latest/developerguide//task_definition_parameters.html#volumes>`_. Default: - No volumes are passed to the Docker daemon on a container instance.

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps(
            compatibility=compatibility,
            cpu=cpu,
            ephemeral_storage_gib=ephemeral_storage_gib,
            inference_accelerators=inference_accelerators,
            ipc_mode=ipc_mode,
            memory_mib=memory_mib,
            network_mode=network_mode,
            pid_mode=pid_mode,
            placement_constraints=placement_constraints,
            runtime_platform=runtime_platform,
            execution_role=execution_role,
            family=family,
            proxy_configuration=proxy_configuration,
            task_role=task_role,
            volumes=volumes,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps, jsii.invoke(self, "modifyTaskDefinitionProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1b6f62b521bb2433821c150319d469dc1de71f54acbc0eeed2b5d8899969492)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(experimental) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is generally used to
        create any final resources which might depend on the service itself.

        :param service: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24ba92fd0ac0c816d12da606204e42c52685b9a00b8a9281497f2571d1e2e592)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf33dc4c9eb7ff891208bb61924a68ed4b4b593f76966a06f425ad88130bd43a)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))

    @builtins.property
    @jsii.member(jsii_name="protocol")
    def protocol(self) -> Protocol:
        '''(experimental) The protocol used for AppMesh routing.

        default - Protocol.HTTP

        :stability: experimental
        '''
        return typing.cast(Protocol, jsii.get(self, "protocol"))

    @builtins.property
    @jsii.member(jsii_name="route")
    def _route(self) -> _aws_cdk_aws_appmesh_ceddda9d.Route:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_appmesh_ceddda9d.Route, jsii.get(self, "route"))

    @_route.setter
    def _route(self, value: _aws_cdk_aws_appmesh_ceddda9d.Route) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__45282d066b0851dbef347c4ad1b08a63c9a6a9fd89bb9bab0d0344a37d51d7e0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "route", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="virtualNode")
    def _virtual_node(self) -> _aws_cdk_aws_appmesh_ceddda9d.VirtualNode:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_appmesh_ceddda9d.VirtualNode, jsii.get(self, "virtualNode"))

    @_virtual_node.setter
    def _virtual_node(self, value: _aws_cdk_aws_appmesh_ceddda9d.VirtualNode) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5a5ea5a7d7c3e24afe0e0135e50a5e8582a8802d26297326e82b08535ed8db7d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "virtualNode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="virtualRouter")
    def _virtual_router(self) -> _aws_cdk_aws_appmesh_ceddda9d.VirtualRouter:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_appmesh_ceddda9d.VirtualRouter, jsii.get(self, "virtualRouter"))

    @_virtual_router.setter
    def _virtual_router(
        self,
        value: _aws_cdk_aws_appmesh_ceddda9d.VirtualRouter,
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2568f8d0e5d292fdf59d27fa103da5a8e7dcf882c1d57cdb4fb9bc163dd53968)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "virtualRouter", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="virtualService")
    def _virtual_service(self) -> _aws_cdk_aws_appmesh_ceddda9d.VirtualService:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_appmesh_ceddda9d.VirtualService, jsii.get(self, "virtualService"))

    @_virtual_service.setter
    def _virtual_service(
        self,
        value: _aws_cdk_aws_appmesh_ceddda9d.VirtualService,
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__557e91721e7f9fa56fe8c0aaed4a95b39f55db769264f9dfe1a37478a24c0cb5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "virtualService", value) # pyright: ignore[reportArgumentType]


class AssignPublicIpExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.AssignPublicIpExtension",
):
    '''(experimental) Modifies the service to assign a public ip to each task and optionally exposes public IPs in a Route 53 record set.

    Note: If you want to change the DNS zone or record name, you will need to
    remove this extension completely and then re-add it.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        dns: typing.Optional[typing.Union[AssignPublicIpDnsOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param dns: (experimental) Enable publishing task public IPs to a recordset in a Route 53 hosted zone. Note: If you want to change the DNS zone or record name, you will need to remove this extension completely and then re-add it.

        :stability: experimental
        '''
        options = AssignPublicIpExtensionOptions(dns=dns)

        jsii.create(self.__class__, self, [options])

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(experimental) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, _scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param _scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38ed1898de13597e3b7d93ee40ce523a890f585a491f671852960714fca854b9)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument _scope", value=_scope, expected_type=type_hints["_scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, _scope]))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(experimental) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is generally used to
        create any final resources which might depend on the service itself.

        :param service: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f2291ce04b362972e55218aa333ff0f9a122a5ea15c56cbb478a163c766c66d)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))

    @builtins.property
    @jsii.member(jsii_name="dns")
    def dns(self) -> typing.Optional[AssignPublicIpDnsOptions]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[AssignPublicIpDnsOptions], jsii.get(self, "dns"))

    @dns.setter
    def dns(self, value: typing.Optional[AssignPublicIpDnsOptions]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f90c2896c6abdd26969b3d38d54e26dc6e666b6c62b45540f048bb96e0d86c9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "dns", value) # pyright: ignore[reportArgumentType]


class CloudwatchAgentExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.CloudwatchAgentExtension",
):
    '''(experimental) This extension adds a CloudWatch agent to the task definition and configures the task to be able to publish metrics to CloudWatch.

    :stability: experimental
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__077bc8d3188083769fa35aaf406ea73e7e9b53de59360a4febecb76aca3e8e02)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="resolveContainerDependencies")
    def resolve_container_dependencies(self) -> None:
        '''(experimental) Once all containers are added to the task definition, this hook is called for each extension to give it a chance to resolve its dependency graph so that its container starts in the right order based on the other extensions that were enabled.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "resolveContainerDependencies", []))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cbde7e49a59cd7cc4d0cae1ae170cfed00a9cd120d6514ef8d2e21e07d37c2c8)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))


class Container(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.Container",
):
    '''(experimental) The main container of a service.

    This is generally the container
    which runs your application business logic. Other extensions will attach
    sidecars alongside this main container.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        cpu: jsii.Number,
        image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
        memory_mib: jsii.Number,
        traffic_port: jsii.Number,
        environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
        log_group: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup] = None,
        secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
    ) -> None:
        '''
        :param cpu: (experimental) How much CPU the container requires.
        :param image: (experimental) The image to run.
        :param memory_mib: (experimental) How much memory in megabytes the container requires.
        :param traffic_port: (experimental) What port the image listen for traffic on.
        :param environment: (experimental) Environment variables to pass into the container. Default: - No environment variables.
        :param environment_files: (experimental) The environment files to pass to the container. Default: - No environment files.
        :param log_group: (experimental) The log group into which application container logs should be routed. Default: - A log group is automatically created for you if the ``ECS_SERVICE_EXTENSIONS_ENABLE_DEFAULT_LOG_DRIVER`` feature flag is set.
        :param secrets: (experimental) The secret environment variables to pass to the container. Default: - No secret environment variables.

        :stability: experimental
        '''
        props = ContainerExtensionProps(
            cpu=cpu,
            image=image,
            memory_mib=memory_mib,
            traffic_port=traffic_port,
            environment=environment,
            environment_files=environment_files,
            log_group=log_group,
            secrets=secrets,
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="modifyTaskDefinitionProps")
    def modify_task_definition_props(
        self,
        *,
        compatibility: _aws_cdk_aws_ecs_ceddda9d.Compatibility,
        cpu: typing.Optional[builtins.str] = None,
        ephemeral_storage_gib: typing.Optional[jsii.Number] = None,
        inference_accelerators: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.InferenceAccelerator, typing.Dict[builtins.str, typing.Any]]]] = None,
        ipc_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.IpcMode] = None,
        memory_mib: typing.Optional[builtins.str] = None,
        network_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.NetworkMode] = None,
        pid_mode: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.PidMode] = None,
        placement_constraints: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.PlacementConstraint]] = None,
        runtime_platform: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.RuntimePlatform, typing.Dict[builtins.str, typing.Any]]] = None,
        execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        family: typing.Optional[builtins.str] = None,
        proxy_configuration: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ProxyConfiguration] = None,
        task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        volumes: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_ecs_ceddda9d.Volume, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps:
        '''(experimental) This is a hook which allows extensions to modify the settings of the task definition prior to it being created.

        For example, the App Mesh
        extension needs to configure an Envoy proxy in the task definition,
        or the Application extension wants to set the overall resource for
        the task.

        :param compatibility: The task launch type compatiblity requirement.
        :param cpu: The number of cpu units used by the task. If you are using the EC2 launch type, this field is optional and any value can be used. If you are using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the memory parameter: 256 (.25 vCPU) - Available memory values: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) 512 (.5 vCPU) - Available memory values: 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) 1024 (1 vCPU) - Available memory values: 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) 2048 (2 vCPU) - Available memory values: Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) 4096 (4 vCPU) - Available memory values: Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) 8192 (8 vCPU) - Available memory values: Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) 16384 (16 vCPU) - Available memory values: Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) Default: - CPU units are not specified.
        :param ephemeral_storage_gib: The amount (in GiB) of ephemeral storage to be allocated to the task. Only supported in Fargate platform version 1.4.0 or later. Default: - Undefined, in which case, the task will receive 20GiB ephemeral storage.
        :param inference_accelerators: The inference accelerators to use for the containers in the task. Not supported in Fargate. Default: - No inference accelerators.
        :param ipc_mode: The IPC resource namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - IpcMode used by the task is not specified
        :param memory_mib: The amount (in MiB) of memory used by the task. If using the EC2 launch type, this field is optional and any value can be used. If using the Fargate launch type, this field is required and you must use one of the following values, which determines your range of valid values for the cpu parameter: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB) - Available cpu values: 256 (.25 vCPU) 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB) - Available cpu values: 512 (.5 vCPU) 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB) - Available cpu values: 1024 (1 vCPU) Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB) - Available cpu values: 2048 (2 vCPU) Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB) - Available cpu values: 4096 (4 vCPU) Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB) - Available cpu values: 8192 (8 vCPU) Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB) - Available cpu values: 16384 (16 vCPU) Default: - Memory used by task is not specified.
        :param network_mode: The networking mode to use for the containers in the task. On Fargate, the only supported networking mode is AwsVpc. Default: - NetworkMode.Bridge for EC2 & External tasks, AwsVpc for Fargate tasks.
        :param pid_mode: The process namespace to use for the containers in the task. Not supported in Fargate and Windows containers. Default: - PidMode used by the task is not specified
        :param placement_constraints: The placement constraints to use for tasks in the service. You can specify a maximum of 10 constraints per task (this limit includes constraints in the task definition and those specified at run time). Not supported in Fargate. Default: - No placement constraints.
        :param runtime_platform: The operating system that your task definitions are running on. A runtimePlatform is supported only for tasks using the Fargate launch type. Default: - Undefined.
        :param execution_role: The name of the IAM task execution role that grants the ECS agent permission to call AWS APIs on your behalf. The role will be used to retrieve container images from ECR and create CloudWatch log groups. Default: - An execution role will be automatically created if you use ECR images in your task definition.
        :param family: The name of a family that this task definition is registered to. A family groups multiple versions of a task definition. Default: - Automatically generated name.
        :param proxy_configuration: The configuration details for the App Mesh proxy. Default: - No proxy configuration.
        :param task_role: The name of the IAM role that grants containers in the task permission to call AWS APIs on your behalf. Default: - A task role is automatically created for you.
        :param volumes: The list of volume definitions for the task. For more information, see `Task Definition Parameter Volumes <https://docs.aws.amazon.com/AmazonECS/latest/developerguide//task_definition_parameters.html#volumes>`_. Default: - No volumes are passed to the Docker daemon on a container instance.

        :stability: experimental
        '''
        props = _aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps(
            compatibility=compatibility,
            cpu=cpu,
            ephemeral_storage_gib=ephemeral_storage_gib,
            inference_accelerators=inference_accelerators,
            ipc_mode=ipc_mode,
            memory_mib=memory_mib,
            network_mode=network_mode,
            pid_mode=pid_mode,
            placement_constraints=placement_constraints,
            runtime_platform=runtime_platform,
            execution_role=execution_role,
            family=family,
            proxy_configuration=proxy_configuration,
            task_role=task_role,
            volumes=volumes,
        )

        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.TaskDefinitionProps, jsii.invoke(self, "modifyTaskDefinitionProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf3fc5c42aa1818482bd8743e8f10ba77aaf61317153f1d97445a58428f36bfd)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="resolveContainerDependencies")
    def resolve_container_dependencies(self) -> None:
        '''(experimental) Once all containers are added to the task definition, this hook is called for each extension to give it a chance to resolve its dependency graph so that its container starts in the right order based on the other extensions that were enabled.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "resolveContainerDependencies", []))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fbba7cbbc3927c630f737fd180e52eb90546a0dea499f24f8979548d012cdb6a)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))

    @builtins.property
    @jsii.member(jsii_name="trafficPort")
    def traffic_port(self) -> jsii.Number:
        '''(experimental) The port on which the container expects to receive network traffic.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "trafficPort"))

    @builtins.property
    @jsii.member(jsii_name="logGroup")
    def log_group(self) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup]:
        '''(experimental) The log group into which application container logs should be routed.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup], jsii.get(self, "logGroup"))

    @log_group.setter
    def log_group(
        self,
        value: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5b56773bc13f3475e7efec07360704534718edfb3b9af5f22103e481189bef3f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "logGroup", value) # pyright: ignore[reportArgumentType]


@jsii.implements(IEnvironment)
class Environment(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.Environment",
):
    '''(experimental) An environment into which to deploy a service.

    This environment
    can either be instantiated with a pre-existing AWS VPC and ECS cluster,
    or it can create its own VPC and cluster. By default, it will create
    a cluster with Fargate capacity.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        capacity_type: typing.Optional[EnvironmentCapacityType] = None,
        cluster: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: The name of this environment.
        :param capacity_type: (experimental) The type of capacity to use for this environment. Default: - EnvironmentCapacityType.FARGATE
        :param cluster: (experimental) The ECS cluster which provides compute capacity to this service. [disable-awslint:ref-via-interface] Default: - Create a new cluster
        :param vpc: (experimental) The VPC used by the service for networking. Default: - Create a new VPC

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__79df512c816cd130c68fb458db12eca79849784c45022a670ceeb7656c517376)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = EnvironmentProps(capacity_type=capacity_type, cluster=cluster, vpc=vpc)

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromEnvironmentAttributes")
    @builtins.classmethod
    def from_environment_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        capacity_type: EnvironmentCapacityType,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
    ) -> IEnvironment:
        '''(experimental) Import an existing environment from its attributes.

        :param scope: -
        :param id: -
        :param capacity_type: (experimental) The capacity type used by the service's cluster.
        :param cluster: (experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__032296542d572c6b398d9bf3c547056ab67cd1b9afdb7c038ad699976d18e3db)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = EnvironmentAttributes(capacity_type=capacity_type, cluster=cluster)

        return typing.cast(IEnvironment, jsii.sinvoke(cls, "fromEnvironmentAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="addDefaultCloudMapNamespace")
    def add_default_cloud_map_namespace(
        self,
        *,
        name: builtins.str,
        type: typing.Optional[_aws_cdk_aws_servicediscovery_ceddda9d.NamespaceType] = None,
        use_for_service_connect: typing.Optional[builtins.bool] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Add a default cloudmap namespace to the environment's cluster.

        The environment's cluster must not be imported.

        :param name: The name of the namespace, such as example.com.
        :param type: The type of CloudMap Namespace to create. Default: PrivateDns
        :param use_for_service_connect: This property specifies whether to set the provided namespace as the service connect default in the cluster properties. Default: false
        :param vpc: The VPC to associate the namespace with. This property is required for private DNS namespaces. Default: VPC of the cluster for Private DNS Namespace, otherwise none

        :stability: experimental
        '''
        options = _aws_cdk_aws_ecs_ceddda9d.CloudMapNamespaceOptions(
            name=name,
            type=type,
            use_for_service_connect=use_for_service_connect,
            vpc=vpc,
        )

        return typing.cast(None, jsii.invoke(self, "addDefaultCloudMapNamespace", [options]))

    @builtins.property
    @jsii.member(jsii_name="capacityType")
    def capacity_type(self) -> EnvironmentCapacityType:
        '''(experimental) The capacity type used by the service's cluster.

        :stability: experimental
        '''
        return typing.cast(EnvironmentCapacityType, jsii.get(self, "capacityType"))

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_ecs_ceddda9d.ICluster:
        '''(experimental) The cluster that is providing capacity for this service.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ICluster, jsii.get(self, "cluster"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''(experimental) The name of this environment.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC where environment services should be placed.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


class FireLensExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.FireLensExtension",
):
    '''(experimental) This extension adds a FluentBit log router to the task definition and does all the configuration necessarily to enable log routing for the task using FireLens.

    :stability: experimental
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="addHooks")
    def add_hooks(self) -> None:
        '''(experimental) A hook that allows the extension to add hooks to other extensions that are registered.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "addHooks", []))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc44db22afa05d01048722e48f64c16657acd6619ff44e75cd439cc75e743eb1)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="resolveContainerDependencies")
    def resolve_container_dependencies(self) -> None:
        '''(experimental) Once all containers are added to the task definition, this hook is called for each extension to give it a chance to resolve its dependency graph so that its container starts in the right order based on the other extensions that were enabled.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "resolveContainerDependencies", []))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) Once the task definition is created, this hook is called for each extension to give it a chance to add containers to the task definition, change the task definition's role to add permissions, etc.

        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26302b705de590e08625ea7201dd37b89ed5101384565fd0faf5199984ed9c46)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))


class HttpLoadBalancerExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.HttpLoadBalancerExtension",
):
    '''(experimental) This extension add a public facing load balancer for sending traffic to one or more replicas of the application container.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        requests_per_target: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param requests_per_target: (experimental) The number of ALB requests per target.

        :stability: experimental
        '''
        props = HttpLoadBalancerProps(requests_per_target=requests_per_target)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(experimental) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: experimental
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed8391caad963614ec93d1a0d7e9d9747d62bf0d502b9ad5c4c57f654c5f7315)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(experimental) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is generally used to
        create any final resources which might depend on the service itself.

        :param service: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5d2291e3a7f3e7948ea69040817ea11f3b4c2e634bcdd8ac8fb0199f4fe839bb)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))


@jsii.interface(
    jsii_type="@aws-cdk-containers/ecs-service-extensions.IGrantInjectable"
)
class IGrantInjectable(IInjectable, typing_extensions.Protocol):
    '''(experimental) An interface that will be implemented by all the injectable resources that need to grant permissions to the task role.

    :stability: experimental
    '''

    @jsii.member(jsii_name="grant")
    def grant(self, task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition) -> None:
        '''
        :param task_definition: -

        :stability: experimental
        '''
        ...


class _IGrantInjectableProxy(
    jsii.proxy_for(IInjectable), # type: ignore[misc]
):
    '''(experimental) An interface that will be implemented by all the injectable resources that need to grant permissions to the task role.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk-containers/ecs-service-extensions.IGrantInjectable"

    @jsii.member(jsii_name="grant")
    def grant(self, task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition) -> None:
        '''
        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5c9b77d6baabb5e5cb335d3b7b76d564d05a0a40856291a10a44c767bc2520b)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "grant", [task_definition]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IGrantInjectable).__jsii_proxy_class__ = lambda : _IGrantInjectableProxy


@jsii.implements(IGrantInjectable)
class InjectableTopic(
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.InjectableTopic",
):
    '''(experimental) The ``InjectableTopic`` class represents SNS Topic resource that can be published events to by the parent service.

    :stability: experimental
    '''

    def __init__(self, *, topic: _aws_cdk_aws_sns_ceddda9d.ITopic) -> None:
        '''
        :param topic: (experimental) The SNS Topic to publish events to.

        :stability: experimental
        '''
        props = InjectableTopicProps(topic=topic)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="environmentVariables")
    def environment_variables(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.invoke(self, "environmentVariables", []))

    @jsii.member(jsii_name="grant")
    def grant(self, task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition) -> None:
        '''
        :param task_definition: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48c7f195f42f8e59cbbfa1cbbb92b61da9881c8a02edf111a97cd4db56e0e94a)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "grant", [task_definition]))

    @builtins.property
    @jsii.member(jsii_name="topic")
    def topic(self) -> _aws_cdk_aws_sns_ceddda9d.ITopic:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_sns_ceddda9d.ITopic, jsii.get(self, "topic"))


class InjecterExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.InjecterExtension",
):
    '''(experimental) This extension accepts a list of ``Injectable`` resources that the parent service can publish events or write data to.

    It sets up the corresponding permissions for the task role of the parent service.

    :stability: experimental
    '''

    def __init__(self, *, injectables: typing.Sequence[IInjectable]) -> None:
        '''
        :param injectables: (experimental) The list of injectable resources for this service.

        :stability: experimental
        '''
        props = InjecterExtensionProps(injectables=injectables)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="addHooks")
    def add_hooks(self) -> None:
        '''(experimental) Add hooks to the main application extension so that it is modified to add the injectable resource environment variables to the container environment.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "addHooks", []))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) A hook that is called for each extension ahead of time to allow for any initial setup, such as creating resources in advance.

        :param service: -
        :param scope: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba812a9535025f034270daebc1bb1dcb1c0aa3ad083d9911e25dd4ed1bdd49dd)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) After the task definition has been created, this hook grants the required permissions to the task role for the parent service.

        :param task_definition: The created task definition.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__965f371f47a5e35e297c690ad4fd62e38130d0f53ddfa246cbd67b7e5a78ebd3)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))


class QueueExtension(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.QueueExtension",
):
    '''(experimental) This extension creates a default ``eventsQueue`` for the service (if not provided) and accepts a list of objects of type ``ISubscribable`` that the ``eventsQueue`` subscribes to.

    It creates the subscriptions and sets up permissions
    for the service to consume messages from the SQS Queues.

    It also configures a target tracking scaling policy for the service to maintain an acceptable queue latency by tracking
    the backlog per task. For more information, please refer: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-using-sqs-queue.html .

    The default queue for this service can be accessed using the getter ``<extension>.eventsQueue``.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        events_queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
        scale_on_latency: typing.Optional[typing.Union[QueueAutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        subscriptions: typing.Optional[typing.Sequence[ISubscribable]] = None,
    ) -> None:
        '''
        :param events_queue: (experimental) The user-provided default queue for this service. If the ``eventsQueue`` is not provided, a default SQS Queue is created for the service. Default: none
        :param scale_on_latency: (experimental) The user-provided queue delay fields to configure auto scaling for the default queue. Default: none
        :param subscriptions: (experimental) The list of subscriptions for this service. Default: none

        :stability: experimental
        '''
        props = QueueExtensionProps(
            events_queue=events_queue,
            scale_on_latency=scale_on_latency,
            subscriptions=subscriptions,
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="addHooks")
    def add_hooks(self) -> None:
        '''(experimental) Add hooks to the main application extension so that it is modified to add the events queue URL to the container environment.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "addHooks", []))

    @jsii.member(jsii_name="prehook")
    def prehook(self, service: Service, scope: _constructs_77d1e7e8.Construct) -> None:
        '''(experimental) This hook creates (if required) and sets the default queue ``eventsQueue``.

        It also sets up the subscriptions for
        the provided ``ISubscribable`` objects.

        :param service: The parent service which this extension has been added to.
        :param scope: The scope that this extension should create resources in.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c2f5ee1195fd16f7e0ef20ecbd77d67b9fbafa0ecd9617a5e91a28ef3de4ced)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        return typing.cast(None, jsii.invoke(self, "prehook", [service, scope]))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(experimental) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is used to add target tracking
        scaling policies for the SQS Queues of the service. It also creates an AWS Lambda
        Function for calculating the backlog per task metric.

        :param service: - The generated service.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c33c510d93072d2b4ea0fcf0ba7fbae74143e371e7996c0e2805f9cf1a9af7c)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))

    @jsii.member(jsii_name="useTaskDefinition")
    def use_task_definition(
        self,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    ) -> None:
        '''(experimental) After the task definition has been created, this hook grants SQS permissions to the task role.

        :param task_definition: The created task definition.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__994a45034920765ebf187cd6c2f9dd5d5d81863eb6a995f3f6c09b1d1ef8cce1)
            check_type(argname="argument task_definition", value=task_definition, expected_type=type_hints["task_definition"])
        return typing.cast(None, jsii.invoke(self, "useTaskDefinition", [task_definition]))

    @builtins.property
    @jsii.member(jsii_name="eventsQueue")
    def events_queue(self) -> _aws_cdk_aws_sqs_ceddda9d.IQueue:
        '''
        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.IQueue, jsii.get(self, "eventsQueue"))

    @builtins.property
    @jsii.member(jsii_name="autoscalingOptions")
    def autoscaling_options(self) -> typing.Optional[QueueAutoScalingOptions]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[QueueAutoScalingOptions], jsii.get(self, "autoscalingOptions"))

    @builtins.property
    @jsii.member(jsii_name="logGroup")
    def log_group(self) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup]:
        '''(experimental) The log group created by the extension where the AWS Lambda function logs are stored.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup], jsii.get(self, "logGroup"))

    @log_group.setter
    def log_group(
        self,
        value: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e381a94b8fd01616977d82ea065a59158d8c683625e4200204ab6cae2823a5e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "logGroup", value) # pyright: ignore[reportArgumentType]


class ScaleOnCpuUtilization(
    ServiceExtension,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk-containers/ecs-service-extensions.ScaleOnCpuUtilization",
):
    '''(deprecated) This extension helps you scale your service according to CPU utilization.

    :deprecated:

    To enable target tracking based on CPU utilization, use the ``targetCpuUtilization`` property of ``autoScaleTaskCount`` in the ``Service`` construct.
    For more information, please refer https://github.com/aws/aws-cdk/blob/master/packages/%40aws-cdk-containers/ecs-service-extensions/README.md#task-auto-scaling .

    :stability: deprecated
    '''

    def __init__(
        self,
        *,
        initial_task_count: typing.Optional[jsii.Number] = None,
        max_task_count: typing.Optional[jsii.Number] = None,
        min_task_count: typing.Optional[jsii.Number] = None,
        scale_in_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        scale_out_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        target_cpu_utilization: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param initial_task_count: (deprecated) How many tasks to launch initially. Default: - 2
        :param max_task_count: (deprecated) The maximum number of tasks when scaling out. Default: - 8
        :param min_task_count: (deprecated) The minimum number of tasks when scaling in. Default: - 2
        :param scale_in_cooldown: (deprecated) How long to wait between scale in actions. Default: - 60 seconds
        :param scale_out_cooldown: (deprecated) How long to wait between scale out actions. Default: - 60 seconds
        :param target_cpu_utilization: (deprecated) The CPU utilization to try ot maintain. Default: - 50%

        :stability: deprecated
        '''
        props = CpuScalingProps(
            initial_task_count=initial_task_count,
            max_task_count=max_task_count,
            min_task_count=min_task_count,
            scale_in_cooldown=scale_in_cooldown,
            scale_out_cooldown=scale_out_cooldown,
            target_cpu_utilization=target_cpu_utilization,
        )

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="modifyServiceProps")
    def modify_service_props(
        self,
        *,
        cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
        task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
        assign_public_ip: typing.Optional[builtins.bool] = None,
        cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        desired_count: typing.Optional[jsii.Number] = None,
        health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        max_healthy_percent: typing.Optional[jsii.Number] = None,
        min_healthy_percent: typing.Optional[jsii.Number] = None,
        service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> ServiceBuild:
        '''(deprecated) Prior to launching the task definition as a service, this hook is called on each extension to give it a chance to mutate the properties of the service to be created.

        :param cluster: (experimental) The cluster in which to launch the service.
        :param task_definition: (experimental) The task definition registered to this service.
        :param assign_public_ip: (experimental) Specifies whether the task's elastic network interface receives a public IP address. If true, each task will receive a public IP address. Default: - false
        :param cloud_map_options: (experimental) Configuration for how to register the service in service discovery. Default: - No Cloud Map configured
        :param desired_count: (experimental) How many tasks to run. Default: - 1
        :param health_check_grace_period: (experimental) How long the healthcheck can fail during initial task startup before the task is considered unhealthy. This is used to give the task more time to start passing healthchecks. Default: - No grace period
        :param max_healthy_percent: (experimental) Maximum percentage of tasks that can be launched. Default: - 200
        :param min_healthy_percent: (experimental) Minimum healthy task percentage. Default: - 100
        :param service_connect_configuration: (experimental) Configuration for service connect for this service. Default: - No Service Connect configured.

        :stability: deprecated
        '''
        props = ServiceBuild(
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=assign_public_ip,
            cloud_map_options=cloud_map_options,
            desired_count=desired_count,
            health_check_grace_period=health_check_grace_period,
            max_healthy_percent=max_healthy_percent,
            min_healthy_percent=min_healthy_percent,
            service_connect_configuration=service_connect_configuration,
        )

        return typing.cast(ServiceBuild, jsii.invoke(self, "modifyServiceProps", [props]))

    @jsii.member(jsii_name="useService")
    def use_service(
        self,
        service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
    ) -> None:
        '''(deprecated) When this hook is implemented by extension, it allows the extension to use the service which has been created.

        It is generally used to
        create any final resources which might depend on the service itself.

        :param service: -

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3cee1d52046f25f6baf6e7092422c633ee0e1b80c82bc9313467d3eea1800a1f)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
        return typing.cast(None, jsii.invoke(self, "useService", [service]))

    @builtins.property
    @jsii.member(jsii_name="initialTaskCount")
    def initial_task_count(self) -> jsii.Number:
        '''(deprecated) How many tasks to launch initially.

        :stability: deprecated
        '''
        return typing.cast(jsii.Number, jsii.get(self, "initialTaskCount"))

    @builtins.property
    @jsii.member(jsii_name="maxTaskCount")
    def max_task_count(self) -> jsii.Number:
        '''(deprecated) The maximum number of tasks when scaling out.

        :stability: deprecated
        '''
        return typing.cast(jsii.Number, jsii.get(self, "maxTaskCount"))

    @builtins.property
    @jsii.member(jsii_name="minTaskCount")
    def min_task_count(self) -> jsii.Number:
        '''(deprecated) The minimum number of tasks when scaling in.

        :stability: deprecated
        '''
        return typing.cast(jsii.Number, jsii.get(self, "minTaskCount"))

    @builtins.property
    @jsii.member(jsii_name="scaleInCooldown")
    def scale_in_cooldown(self) -> _aws_cdk_ceddda9d.Duration:
        '''(deprecated) How long to wait between scale in actions.

        :stability: deprecated
        '''
        return typing.cast(_aws_cdk_ceddda9d.Duration, jsii.get(self, "scaleInCooldown"))

    @builtins.property
    @jsii.member(jsii_name="scaleOutCooldown")
    def scale_out_cooldown(self) -> _aws_cdk_ceddda9d.Duration:
        '''(deprecated) How long to wait between scale out actions.

        :stability: deprecated
        '''
        return typing.cast(_aws_cdk_ceddda9d.Duration, jsii.get(self, "scaleOutCooldown"))

    @builtins.property
    @jsii.member(jsii_name="targetCpuUtilization")
    def target_cpu_utilization(self) -> jsii.Number:
        '''(deprecated) The CPU utilization to try ot maintain.

        :stability: deprecated
        '''
        return typing.cast(jsii.Number, jsii.get(self, "targetCpuUtilization"))


__all__ = [
    "AliasedPortExtension",
    "AliasedPortMutatingHook",
    "AliasedPortMutatingHookProps",
    "AliasedPortProps",
    "AppMeshExtension",
    "AssignPublicIpDnsOptions",
    "AssignPublicIpExtension",
    "AssignPublicIpExtensionOptions",
    "AutoScalingOptions",
    "CloudwatchAgentExtension",
    "ConnectToProps",
    "Container",
    "ContainerExtensionProps",
    "ContainerMutatingHook",
    "CpuScalingProps",
    "Environment",
    "EnvironmentAttributes",
    "EnvironmentCapacityType",
    "EnvironmentProps",
    "FireLensExtension",
    "FirelensMutatingHook",
    "FirelensProps",
    "HttpLoadBalancerExtension",
    "HttpLoadBalancerProps",
    "IEnvironment",
    "IGrantInjectable",
    "IInjectable",
    "ISubscribable",
    "ImportedEnvironment",
    "InjectableTopic",
    "InjectableTopicProps",
    "InjecterExtension",
    "InjecterExtensionProps",
    "MeshProps",
    "Protocol",
    "QueueAutoScalingOptions",
    "QueueExtension",
    "QueueExtensionProps",
    "ScaleOnCpuUtilization",
    "Service",
    "ServiceBuild",
    "ServiceDescription",
    "ServiceExtension",
    "ServiceProps",
    "SubscriptionQueue",
    "TopicSubscription",
    "TopicSubscriptionProps",
    "XRayExtension",
]

publication.publish()

def _typecheckingstub__9eafc8bc30298b419ba1305209f1f31afbf65c9b3456fc2c643e9dc4c1bd501a(
    *,
    alias_port: jsii.Number,
    port_mapping_name: builtins.str,
    protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7d89a6c579317235d028edb793a72ba2e7d3ccda1e4b1f2602503eea428e930c(
    *,
    alias: builtins.str,
    alias_port: typing.Optional[jsii.Number] = None,
    app_protocol: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa7fb8b6574fcc7a10ce0f47113796062053fc86dbd682d2487f7cdfb34d46d0(
    *,
    record_name: builtins.str,
    zone: _aws_cdk_aws_route53_ceddda9d.IHostedZone,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2deb6349e9cd894776e0a60628761c1ec58ee4da5eb9e508b90d05cf30b34874(
    *,
    dns: typing.Optional[typing.Union[AssignPublicIpDnsOptions, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__caf95230f9a127a46aef16659b3a944e6851420921875acc492c4a7722ded929(
    *,
    max_task_count: jsii.Number,
    min_task_count: typing.Optional[jsii.Number] = None,
    target_cpu_utilization: typing.Optional[jsii.Number] = None,
    target_memory_utilization: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20e37174ab201a5eb1d201637ac0c651f7361afe5cb95a69d57aeed17fde4cc3(
    *,
    local_bind_port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__592d522da39571a2b2a1780c28b1405f8f98b2f7ae4b9ff881cf256a8d3941d3(
    *,
    cpu: jsii.Number,
    image: _aws_cdk_aws_ecs_ceddda9d.ContainerImage,
    memory_mib: jsii.Number,
    traffic_port: jsii.Number,
    environment: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    environment_files: typing.Optional[typing.Sequence[_aws_cdk_aws_ecs_ceddda9d.EnvironmentFile]] = None,
    log_group: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup] = None,
    secrets: typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_ecs_ceddda9d.Secret]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da64dd40c2eed49a661888472ad447cdd50d0d1de54b035c25e482f09c6e8d50(
    *,
    initial_task_count: typing.Optional[jsii.Number] = None,
    max_task_count: typing.Optional[jsii.Number] = None,
    min_task_count: typing.Optional[jsii.Number] = None,
    scale_in_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    scale_out_cooldown: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    target_cpu_utilization: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3972ae1eaa225a4a8fa626d5b9ec3fc0b64c420599bc3a5f3dd1d2aec30cfd77(
    *,
    capacity_type: EnvironmentCapacityType,
    cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4f994193a0844d1feecc18424b7d4cb07ff8d4ed7fb514183a12bd56930e922b(
    *,
    capacity_type: typing.Optional[EnvironmentCapacityType] = None,
    cluster: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aceb6633b315022d8687596bd75918bf27f97bab07b5afe71b5de85deefef59c(
    *,
    log_group: _aws_cdk_aws_logs_ceddda9d.LogGroup,
    parent_service: Service,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82df5b77ad12b766d5e63af5b466f4e55ce579599801b70669df556201e35c2c(
    *,
    requests_per_target: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd1578190a97094d760d76a2f5cebe69df504113964828b89844073359391cb5(
    extension: QueueExtension,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91378335a3876039a3828c1245b7393e5a1292ba2a049277f1c28e0986b15b07(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    capacity_type: EnvironmentCapacityType,
    cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5404fdd3e63bd485e4db5b2a113ebf7494d35cf4a96f038e9defb7d051989a59(
    *,
    topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__764a4ce423345733d9211ae0ec978efe2db85a96e72389375cfe172603235a12(
    *,
    injectables: typing.Sequence[IInjectable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__142846b40345638745bc1a3ab27f3cab5f854bdaf8ca3b69b33a43f481fd5f56(
    *,
    mesh: _aws_cdk_aws_appmesh_ceddda9d.Mesh,
    protocol: typing.Optional[Protocol] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a69b597f7f7ad40eda264d309c915a018cfc7e08a24d4fd3431b480aebba63ba(
    *,
    acceptable_latency: _aws_cdk_ceddda9d.Duration,
    message_processing_time: _aws_cdk_ceddda9d.Duration,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b4718a77605fed94d29789c1a434b9fcc1ae492a2a3de2712231624c092820cb(
    *,
    events_queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
    scale_on_latency: typing.Optional[typing.Union[QueueAutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    subscriptions: typing.Optional[typing.Sequence[ISubscribable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__db3cb686a45270fdd7e768c5ae18b4f4f6f2162d2173f63f7c535361b5a43ee0(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    environment: IEnvironment,
    service_description: ServiceDescription,
    auto_scale_task_count: typing.Optional[typing.Union[AutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    desired_count: typing.Optional[jsii.Number] = None,
    task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__502b75d7c9b239a450ef6b60bf75138f9e9ad1bf1db3c86bae3750bb5b2ddb85(
    url_name: builtins.str,
    url: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__74fb3efae7913ceb8ccea9c9b3493498efca8dbd55fc5e00f7140f8a17ed89a9(
    service: Service,
    *,
    local_bind_port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f9661ad5046e27393ad9a87be136fc5dff0e8a0c90ab0d53f12343c56b38af2(
    url_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48e0b209d664b802d972b8c57029dfafa732ddd80d7f15177ec1c19fa4ee27e4(
    value: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__43501a7df8adf21fb5b2baed0861c8d54532787b41d74a178e59fb2f8d7cb4c7(
    value: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee366325f772dd64ac0fb090f415241df9c08abd4c10129d4accf09912d2ae3f(
    value: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroup],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bbc157cc76350e79845bf03bad3f7df149e831066f26c4ce897b5f0aa26318c9(
    *,
    cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
    assign_public_ip: typing.Optional[builtins.bool] = None,
    cloud_map_options: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.CloudMapOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    desired_count: typing.Optional[jsii.Number] = None,
    health_check_grace_period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    max_healthy_percent: typing.Optional[jsii.Number] = None,
    min_healthy_percent: typing.Optional[jsii.Number] = None,
    service_connect_configuration: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ServiceConnectProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c093f5c31129726d3d125fea26e2c3fd91a85698eb1ba8473769eac664ab595a(
    extension: ServiceExtension,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8352914d442a0691483353eb819f6ab07a7c3906ffcb4a5f205881cab8855693(
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3cc49fbfe806b68e28897ef0a6adb82ef13ea662595a6dc16cfbd1c8f3d80ff(
    value: typing.Mapping[builtins.str, ServiceExtension],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1942fe00f761e2c51266b2c817c5520489ca4dfc5fb00a8121bfc670fbf52e3f(
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__67016c4360f564fd4fe54d7d2b5edd75e564f902aee57e11136af32477ecb5c5(
    hook: ContainerMutatingHook,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8e2d8de0dbe555c1e1b7b50b5b988162b03bc53d683e2a98a1659e95e6b1180c(
    service: Service,
    *,
    local_bind_port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eefdf655cd0e7f30d0fcf6f77a6d8729245c20be4605fa83182a750656dd59de(
    parent: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__38e3e0860e30eb48b790e6fc0840c9d9d36bff02f4ab4e976e145f4f85ef048d(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e93694c5c40f28677d9914773fe2949cbdf32f19f86771a0f343852c4a456833(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__299f56627660a08293011eb309421e4c9ecab06a492c5135e001bb57465be12a(
    value: typing.List[ContainerMutatingHook],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffd5c720e9e1800e56e330f06b53101d51e941eae8399ed18a6ce3469d004a45(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__888537d4e44499688ac07459949d868e9b29b5f5b71d885c9f28d9f42d26a293(
    value: Service,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22b87c7ca09e39c9e04f952a479384b276834e484577d808867f6e8cd36eae87(
    value: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54f71fbef259bce4d04ac1599a7734f8470b603b265ce3c405992e7d9403cc63(
    value: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8324f912a77ba2380fbec2194e091c70e44826a63d04c9b3b3178db416008d54(
    *,
    environment: IEnvironment,
    service_description: ServiceDescription,
    auto_scale_task_count: typing.Optional[typing.Union[AutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    desired_count: typing.Optional[jsii.Number] = None,
    task_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2ab599485b374c44897ab0ae8820090231221b727f0f9968276a4071085689df(
    *,
    queue: _aws_cdk_aws_sqs_ceddda9d.IQueue,
    scale_on_latency: typing.Optional[typing.Union[QueueAutoScalingOptions, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__542dd993b9b30463def0028989d7fe8b3f0f9e422cb20bea69ab3b83367fbdb4(
    extension: QueueExtension,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6ce31ca30734748c8286306049838377fd0ae5237a93f44655e549a682baaf92(
    *,
    topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
    queue: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.IQueue] = None,
    topic_subscription_queue: typing.Optional[typing.Union[SubscriptionQueue, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a25c259153e7aabb24a4f343378b533b165fcb42b53180b3fdd7f72da6371ad2(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__02d9f8aa0fd942e4f491eeddab502c60a5a201811637d732a37f9d950cb67311(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1043b521b7d8a62b95b2d33c980009a15390b055b8b23fb3fa89a4601d987fbe(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d404dfff99916347cd236463a68228c5807d4e62df7247b71f3de0207b4ecdb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__69dab24a138f3970d3fecdca97edefcacb2ca2b0f643129d3cda322bcb9be285(
    value: typing.Optional[jsii.Number],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e54f461371069afdb909684795279f736b187cc7fb5b7ef682d1fb827a6b0846(
    value: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.AppProtocol],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0681b9db0238b5ddb0fd915e2a2f44cec1c3d21ec400322498e8bfe207d0f483(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__46aa6bb7020052c416acf790220f414bc6b66910844ccb7115c05c2109ffc6bf(
    other_service: Service,
    *,
    local_bind_port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1b6f62b521bb2433821c150319d469dc1de71f54acbc0eeed2b5d8899969492(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__24ba92fd0ac0c816d12da606204e42c52685b9a00b8a9281497f2571d1e2e592(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cf33dc4c9eb7ff891208bb61924a68ed4b4b593f76966a06f425ad88130bd43a(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__45282d066b0851dbef347c4ad1b08a63c9a6a9fd89bb9bab0d0344a37d51d7e0(
    value: _aws_cdk_aws_appmesh_ceddda9d.Route,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a5ea5a7d7c3e24afe0e0135e50a5e8582a8802d26297326e82b08535ed8db7d(
    value: _aws_cdk_aws_appmesh_ceddda9d.VirtualNode,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2568f8d0e5d292fdf59d27fa103da5a8e7dcf882c1d57cdb4fb9bc163dd53968(
    value: _aws_cdk_aws_appmesh_ceddda9d.VirtualRouter,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__557e91721e7f9fa56fe8c0aaed4a95b39f55db769264f9dfe1a37478a24c0cb5(
    value: _aws_cdk_aws_appmesh_ceddda9d.VirtualService,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__38ed1898de13597e3b7d93ee40ce523a890f585a491f671852960714fca854b9(
    service: Service,
    _scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f2291ce04b362972e55218aa333ff0f9a122a5ea15c56cbb478a163c766c66d(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f90c2896c6abdd26969b3d38d54e26dc6e666b6c62b45540f048bb96e0d86c9(
    value: typing.Optional[AssignPublicIpDnsOptions],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__077bc8d3188083769fa35aaf406ea73e7e9b53de59360a4febecb76aca3e8e02(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cbde7e49a59cd7cc4d0cae1ae170cfed00a9cd120d6514ef8d2e21e07d37c2c8(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bf3fc5c42aa1818482bd8743e8f10ba77aaf61317153f1d97445a58428f36bfd(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fbba7cbbc3927c630f737fd180e52eb90546a0dea499f24f8979548d012cdb6a(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5b56773bc13f3475e7efec07360704534718edfb3b9af5f22103e481189bef3f(
    value: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__79df512c816cd130c68fb458db12eca79849784c45022a670ceeb7656c517376(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    capacity_type: typing.Optional[EnvironmentCapacityType] = None,
    cluster: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.Cluster] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__032296542d572c6b398d9bf3c547056ab67cd1b9afdb7c038ad699976d18e3db(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    capacity_type: EnvironmentCapacityType,
    cluster: _aws_cdk_aws_ecs_ceddda9d.ICluster,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc44db22afa05d01048722e48f64c16657acd6619ff44e75cd439cc75e743eb1(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26302b705de590e08625ea7201dd37b89ed5101384565fd0faf5199984ed9c46(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed8391caad963614ec93d1a0d7e9d9747d62bf0d502b9ad5c4c57f654c5f7315(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5d2291e3a7f3e7948ea69040817ea11f3b4c2e634bcdd8ac8fb0199f4fe839bb(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5c9b77d6baabb5e5cb335d3b7b76d564d05a0a40856291a10a44c767bc2520b(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48c7f195f42f8e59cbbfa1cbbb92b61da9881c8a02edf111a97cd4db56e0e94a(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ba812a9535025f034270daebc1bb1dcb1c0aa3ad083d9911e25dd4ed1bdd49dd(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__965f371f47a5e35e297c690ad4fd62e38130d0f53ddfa246cbd67b7e5a78ebd3(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c2f5ee1195fd16f7e0ef20ecbd77d67b9fbafa0ecd9617a5e91a28ef3de4ced(
    service: Service,
    scope: _constructs_77d1e7e8.Construct,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1c33c510d93072d2b4ea0fcf0ba7fbae74143e371e7996c0e2805f9cf1a9af7c(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__994a45034920765ebf187cd6c2f9dd5d5d81863eb6a995f3f6c09b1d1ef8cce1(
    task_definition: _aws_cdk_aws_ecs_ceddda9d.TaskDefinition,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e381a94b8fd01616977d82ea065a59158d8c683625e4200204ab6cae2823a5e(
    value: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3cee1d52046f25f6baf6e7092422c633ee0e1b80c82bc9313467d3eea1800a1f(
    service: typing.Union[_aws_cdk_aws_ecs_ceddda9d.Ec2Service, _aws_cdk_aws_ecs_ceddda9d.FargateService],
) -> None:
    """Type checking stubs"""
    pass

for cls in [IEnvironment, IGrantInjectable, IInjectable, ISubscribable]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
