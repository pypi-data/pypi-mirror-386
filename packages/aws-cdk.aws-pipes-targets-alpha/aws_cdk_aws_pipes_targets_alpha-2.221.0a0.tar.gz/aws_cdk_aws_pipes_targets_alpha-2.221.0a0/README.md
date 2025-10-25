# Amazon EventBridge Pipes Targets Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

EventBridge Pipes Targets let you create a target for an EventBridge Pipe.

For more details see the [service documentation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-target.html).

## Targets

Pipe targets are the end point of an EventBridge Pipe. The following targets are supported:

* `targets.ApiDestinationTarget`: [Send event source to an EventBridge API destination](#amazon-eventbridge-api-destination)
* `targets.ApiGatewayTarget`: [Send event source to an API Gateway REST API](#amazon-api-gateway-rest-api)
* `targets.CloudWatchLogsTarget`: [Send event source to a CloudWatch Logs log group](#amazon-cloudwatch-logs-log-group)
* `targets.EventBridgeTarget`: [Send event source to an EventBridge event bus](#amazon-eventbridge-event-bus)
* `targets.FirehoseTarget`: [Send event source to an Amazon Data Firehose delivery stream](#amazon-data-firehose-delivery-stream)
* `targets.KinesisTarget`: [Send event source to a Kinesis data stream](#amazon-kinesis-data-stream)
* `targets.LambdaFunction`: [Send event source to a Lambda function](#aws-lambda-function)
* `targets.SageMakerTarget`: [Send event source to a SageMaker pipeline](#amazon-sagemaker-pipeline)
* `targets.SfnStateMachine`: [Invoke a Step Functions state machine from an event source](#aws-step-functions-state-machine)
* `targets.SnsTarget`: [Send event source to an SNS topic](#amazon-sns-topic)
* `targets.SqsTarget`: [Send event source to an SQS queue](#amazon-sqs-queue)

### Amazon EventBridge API Destination

An EventBridge API destination can be used as a target for a pipe.
The API destination will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# dest: events.ApiDestination


api_target = targets.ApiDestinationTarget(dest)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=api_target
)
```

The input to the target API destination can be transformed:

```python
# source_queue: sqs.Queue
# dest: events.ApiDestination


api_target = targets.ApiDestinationTarget(dest,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=api_target
)
```

### Amazon API Gateway Rest API

A REST API can be used as a target for a pipe.
The REST API will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue


fn = lambda_.Function(self, "MyFunc",
    handler="index.handler",
    runtime=lambda_.Runtime.NODEJS_LATEST,
    code=lambda_.Code.from_inline("exports.handler = e => {}")
)

rest_api = api.LambdaRestApi(self, "MyRestAPI", handler=fn)
api_target = targets.ApiGatewayTarget(rest_api)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=api_target
)
```

The input to the target REST API can be transformed:

```python
# source_queue: sqs.Queue


fn = lambda_.Function(self, "MyFunc",
    handler="index.handler",
    runtime=lambda_.Runtime.NODEJS_LATEST,
    code=lambda_.Code.from_inline("exports.handler = e => {}")
)

rest_api = api.LambdaRestApi(self, "MyRestAPI", handler=fn)
api_target = targets.ApiGatewayTarget(rest_api,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=api_target
)
```

### Amazon CloudWatch Logs Log Group

A CloudWatch Logs log group can be used as a target for a pipe.
The log group will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_log_group: logs.LogGroup


log_group_target = targets.CloudWatchLogsTarget(target_log_group)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=log_group_target
)
```

The input to the target log group can be transformed:

```python
# source_queue: sqs.Queue
# target_log_group: logs.LogGroup


log_group_target = targets.CloudWatchLogsTarget(target_log_group,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=log_group_target
)
```

### Amazon EventBridge Event Bus

An EventBridge event bus can be used as a target for a pipe.
The event bus will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_event_bus: events.EventBus


event_bus_target = targets.EventBridgeTarget(target_event_bus)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=event_bus_target
)
```

The input to the target event bus can be transformed:

```python
# source_queue: sqs.Queue
# target_event_bus: events.EventBus


event_bus_target = targets.EventBridgeTarget(target_event_bus,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=event_bus_target
)
```

### Amazon Data Firehose Delivery Stream

An Amazon Data Firehose delivery stream can be used as a target for a pipe.
The delivery stream will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_delivery_stream: firehose.DeliveryStream


delivery_stream_target = targets.FirehoseTarget(target_delivery_stream)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=delivery_stream_target
)
```

The input to the target delivery stream can be transformed:

```python
# source_queue: sqs.Queue
# target_delivery_stream: firehose.DeliveryStream


delivery_stream_target = targets.FirehoseTarget(target_delivery_stream,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=delivery_stream_target
)
```

### Amazon Kinesis Data Stream

A Kinesis data stream can be used as a target for a pipe.
The data stream will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_stream: kinesis.Stream


stream_target = targets.KinesisTarget(target_stream,
    partition_key="pk"
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=stream_target
)
```

The input to the target data stream can be transformed:

```python
# source_queue: sqs.Queue
# target_stream: kinesis.Stream


stream_target = targets.KinesisTarget(target_stream,
    partition_key="pk",
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=stream_target
)
```

### AWS Lambda Function

A Lambda function can be used as a target for a pipe.
The Lambda function will be invoked with the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_function: lambda.IFunction


pipe_target = targets.LambdaFunction(target_function)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

The target Lambda function is invoked synchronously by default. You can also choose to invoke the Lambda Function asynchronously by setting `invocationType` property to `FIRE_AND_FORGET`.

```python
# source_queue: sqs.Queue
# target_function: lambda.IFunction


pipe_target = targets.LambdaFunction(target_function,
    invocation_type=targets.LambdaFunctionInvocationType.FIRE_AND_FORGET
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

The input to the target Lambda Function can be transformed:

```python
# source_queue: sqs.Queue
# target_function: lambda.IFunction


pipe_target = targets.LambdaFunction(target_function,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

### Amazon SageMaker Pipeline

A SageMaker pipeline can be used as a target for a pipe.
The pipeline will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_pipeline: sagemaker.IPipeline


pipeline_target = targets.SageMakerTarget(target_pipeline)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipeline_target
)
```

The input to the target pipeline can be transformed:

```python
# source_queue: sqs.Queue
# target_pipeline: sagemaker.IPipeline


pipeline_target = targets.SageMakerTarget(target_pipeline,
    input_transformation=pipes.InputTransformation.from_object({"body": "👀"})
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipeline_target
)
```

### AWS Step Functions State Machine

A Step Functions state machine can be used as a target for a pipe.
The state machine will be invoked with the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_state_machine: sfn.IStateMachine


pipe_target = targets.SfnStateMachine(target_state_machine)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

You can specify the invocation type when the target state machine is invoked:

```python
# source_queue: sqs.Queue
# target_state_machine: sfn.IStateMachine


pipe_target = targets.SfnStateMachine(target_state_machine,
    invocation_type=targets.StateMachineInvocationType.FIRE_AND_FORGET
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

The input to the target state machine can be transformed:

```python
# source_queue: sqs.Queue
# target_state_machine: sfn.IStateMachine


pipe_target = targets.SfnStateMachine(target_state_machine,
    input_transformation=pipes.InputTransformation.from_object({"body": "<$.body>"}),
    invocation_type=targets.StateMachineInvocationType.FIRE_AND_FORGET
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

### Amazon SNS Topic

An SNS topic can be used as a target for a pipe.
The topic will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_topic: sns.Topic


pipe_target = targets.SnsTarget(target_topic)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

The target input can be transformed:

```python
# source_queue: sqs.Queue
# target_topic: sns.Topic


pipe_target = targets.SnsTarget(target_topic,
    input_transformation=pipes.InputTransformation.from_object({
        "SomeKey": pipes.DynamicInput.from_event_path("$.body")
    })
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

### Amazon SQS Queue

An SQS queue can be used as a target for a pipe.
The queue will receive the (enriched/filtered) source payload.

```python
# source_queue: sqs.Queue
# target_queue: sqs.Queue


pipe_target = targets.SqsTarget(target_queue)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```

The target input can be transformed:

```python
# source_queue: sqs.Queue
# target_queue: sqs.Queue


pipe_target = targets.SqsTarget(target_queue,
    input_transformation=pipes.InputTransformation.from_object({
        "SomeKey": pipes.DynamicInput.from_event_path("$.body")
    })
)

pipe = pipes.Pipe(self, "Pipe",
    source=SqsSource(source_queue),
    target=pipe_target
)
```
