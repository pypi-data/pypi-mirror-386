# Actions for AWS IoT Rule

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This library contains integration classes to send data to any number of
supported AWS Services. Instances of these classes should be passed to
`TopicRule` defined in `aws-cdk-lib/aws-iot`.

Currently supported are:

* Republish a message to another MQTT topic
* Invoke a Lambda function
* Put objects to a S3 bucket
* Put logs to CloudWatch Logs
* Capture CloudWatch metrics
* Change state for a CloudWatch alarm
* Put records to Kinesis Data stream
* Put records to Amazon Data Firehose stream
* Send messages to SQS queues
* Publish messages on SNS topics
* Write messages into columns of DynamoDB
* Put messages IoT Events input
* Send messages to HTTPS endpoints

## Republish a message to another MQTT topic

The code snippet below creates an AWS IoT Rule that republish a message to
another MQTT topic when it is triggered.

```python
iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp, temperature FROM 'device/+/data'"),
    actions=[
        actions.IotRepublishMqttAction("${topic()}/republish",
            quality_of_service=actions.MqttQualityOfService.AT_LEAST_ONCE
        )
    ]
)
```

## Invoke a Lambda function

The code snippet below creates an AWS IoT Rule that invoke a Lambda function
when it is triggered.

```python
func = lambda_.Function(self, "MyFunction",
    runtime=lambda_.Runtime.NODEJS_LATEST,
    handler="index.handler",
    code=lambda_.Code.from_inline("""
            exports.handler = (event) => {
              console.log("It is test for lambda action of AWS IoT Rule.", event);
            };""")
)

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp, temperature FROM 'device/+/data'"),
    actions=[actions.LambdaFunctionAction(func)]
)
```

## Put objects to a S3 bucket

The code snippet below creates an AWS IoT Rule that puts objects to a S3 bucket
when it is triggered.

```python
bucket = s3.Bucket(self, "MyBucket")

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id FROM 'device/+/data'"),
    actions=[actions.S3PutObjectAction(bucket)]
)
```

The property `key` of `S3PutObjectAction` is given the value `${topic()}/${timestamp()}` by default. This `${topic()}`
and `${timestamp()}` is called Substitution templates. For more information see
[this documentation](https://docs.aws.amazon.com/iot/latest/developerguide/iot-substitution-templates.html).
In above sample, `${topic()}` is replaced by a given MQTT topic as `device/001/data`. And `${timestamp()}` is replaced
by the number of the current timestamp in milliseconds as `1636289461203`. So if the MQTT broker receives an MQTT topic
`device/001/data` on `2021-11-07T00:00:00.000Z`, the S3 bucket object will be put to `device/001/data/1636243200000`.

You can also set specific `key` as following:

```python
bucket = s3.Bucket(self, "MyBucket")

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, year, month, day FROM 'device/+/data'"),
    actions=[
        actions.S3PutObjectAction(bucket,
            key="${year}/${month}/${day}/${topic(2)}"
        )
    ]
)
```

If you wanna set access control to the S3 bucket object, you can specify `accessControl` as following:

```python
bucket = s3.Bucket(self, "MyBucket")

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.S3PutObjectAction(bucket,
            access_control=s3.BucketAccessControl.PUBLIC_READ
        )
    ]
)
```

## Put logs to CloudWatch Logs

The code snippet below creates an AWS IoT Rule that puts logs to CloudWatch Logs
when it is triggered.

```python
import aws_cdk.aws_logs as logs


log_group = logs.LogGroup(self, "MyLogGroup")

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id FROM 'device/+/data'"),
    actions=[actions.CloudWatchLogsAction(log_group)]
)
```

## Capture CloudWatch metrics

The code snippet below creates an AWS IoT Rule that capture CloudWatch metrics
when it is triggered.

```python
topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, namespace, unit, value, timestamp FROM 'device/+/data'"),
    actions=[
        actions.CloudWatchPutMetricAction(
            metric_name="${topic(2)}",
            metric_namespace="${namespace}",
            metric_unit="${unit}",
            metric_value="${value}",
            metric_timestamp="${timestamp}"
        )
    ]
)
```

## Start Step Functions State Machine

The code snippet below creates an AWS IoT Rule that starts a Step Functions State Machine
when it is triggered.

```python
state_machine = stepfunctions.StateMachine(self, "SM",
    definition_body=stepfunctions.DefinitionBody.from_chainable(stepfunctions.Wait(self, "Hello", time=stepfunctions.WaitTime.duration(Duration.seconds(10))))
)

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.StepFunctionsStateMachineAction(state_machine)
    ]
)
```

## Change the state of an Amazon CloudWatch alarm

The code snippet below creates an AWS IoT Rule that changes the state of an Amazon CloudWatch alarm when it is triggered:

```python
import aws_cdk.aws_cloudwatch as cloudwatch


metric = cloudwatch.Metric(
    namespace="MyNamespace",
    metric_name="MyMetric",
    dimensions_map={"MyDimension": "MyDimensionValue"}
)
alarm = cloudwatch.Alarm(self, "MyAlarm",
    metric=metric,
    threshold=100,
    evaluation_periods=3,
    datapoints_to_alarm=2
)

topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id FROM 'device/+/data'"),
    actions=[
        actions.CloudWatchSetAlarmStateAction(alarm,
            reason="AWS Iot Rule action is triggered",
            alarm_state_to_set=cloudwatch.AlarmState.ALARM
        )
    ]
)
```

## Put records to Kinesis Data stream

The code snippet below creates an AWS IoT Rule that puts records to Kinesis Data
stream when it is triggered.

```python
import aws_cdk.aws_kinesis as kinesis


stream = kinesis.Stream(self, "MyStream")

topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.KinesisPutRecordAction(stream,
            partition_key="${newuuid()}"
        )
    ]
)
```

## Put records to Amazon Data Firehose stream

The code snippet below creates an AWS IoT Rule that puts records to Put records
to Amazon Data Firehose stream when it is triggered.

```python
import aws_cdk.aws_kinesisfirehose as firehose


bucket = s3.Bucket(self, "MyBucket")
stream = firehose.DeliveryStream(self, "MyStream",
    destination=firehose.S3Bucket(bucket)
)

topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.FirehosePutRecordAction(stream,
            batch_mode=True,
            record_separator=actions.FirehoseRecordSeparator.NEWLINE
        )
    ]
)
```

## Send messages to an SQS queue

The code snippet below creates an AWS IoT Rule that send messages
to an SQS queue when it is triggered:

```python
import aws_cdk.aws_sqs as sqs


queue = sqs.Queue(self, "MyQueue")

topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, year, month, day FROM 'device/+/data'"),
    actions=[
        actions.SqsQueueAction(queue,
            use_base64=True
        )
    ]
)
```

## Publish messages on an SNS topic

The code snippet below creates and AWS IoT Rule that publishes messages to an SNS topic when it is triggered:

```python
import aws_cdk.aws_sns as sns


topic = sns.Topic(self, "MyTopic")

topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, year, month, day FROM 'device/+/data'"),
    actions=[
        actions.SnsTopicAction(topic,
            message_format=actions.SnsActionMessageFormat.JSON
        )
    ]
)
```

## Write attributes of a message to DynamoDB

The code snippet below creates an AWS IoT rule that writes all or part of an
MQTT message to DynamoDB using the DynamoDBv2 action.

```python
import aws_cdk.aws_dynamodb as dynamodb

# table: dynamodb.Table


topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.DynamoDBv2PutItemAction(table)
    ]
)
```

## Put messages IoT Events input

The code snippet below creates an AWS IoT Rule that puts messages
to an IoT Events input when it is triggered:

```python
import aws_cdk.aws_iotevents_alpha as iotevents
import aws_cdk.aws_iam as iam

# role: iam.IRole


input = iotevents.Input(self, "MyInput",
    attribute_json_paths=["payload.temperature", "payload.transactionId"]
)
topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'device/+/data'"),
    actions=[
        actions.IotEventsPutMessageAction(input,
            batch_mode=True,  # optional property, default is 'false'
            message_id="${payload.transactionId}",  # optional property, default is a new UUID
            role=role
        )
    ]
)
```

## Send Messages to HTTPS Endpoints

The code snippet below creates an AWS IoT Rule that sends messages
to an HTTPS endpoint when it is triggered:

```python
topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, year, month, day FROM 'device/+/data'")
)

topic_rule.add_action(
    actions.HttpsAction("https://example.com/endpoint",
        confirmation_url="https://example.com",
        headers=[actions.HttpActionHeader(key="key0", value="value0"), actions.HttpActionHeader(key="key1", value="value1")
        ],
        auth=actions.HttpActionSigV4Auth(service_name="serviceName", signing_region="us-east-1")
    ))
```

## Write Data to Open Search Service

The code snippet below creates an AWS IoT Rule that writes data
to an Open Search Service when it is triggered:

```python
import aws_cdk.aws_opensearchservice as opensearch
# domain: opensearch.Domain


topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, year, month, day FROM 'device/+/data'")
)

topic_rule.add_action(actions.OpenSearchAction(domain,
    id="my-id",
    index="my-index",
    type="my-type"
))
```
