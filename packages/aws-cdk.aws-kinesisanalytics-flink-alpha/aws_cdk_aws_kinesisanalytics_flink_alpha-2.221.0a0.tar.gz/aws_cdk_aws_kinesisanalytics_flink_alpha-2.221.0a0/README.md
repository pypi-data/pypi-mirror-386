# Kinesis Analytics Flink

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This package provides constructs for creating Kinesis Analytics Flink
applications. To learn more about using using managed Flink applications, see
the [AWS developer
guide](https://docs.aws.amazon.com/kinesisanalytics/latest/java/).

## Creating Flink Applications

To create a new Flink application, use the `Application` construct:

```python
import path as path
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk as core
import aws_cdk.integ_tests_alpha as integ
import aws_cdk.aws_kinesisanalytics_flink_alpha as flink

app = core.App()
stack = core.Stack(app, "FlinkAppTest")

flink_runtimes = [flink.Runtime.FLINK_1_6, flink.Runtime.FLINK_1_8, flink.Runtime.FLINK_1_11, flink.Runtime.FLINK_1_13, flink.Runtime.FLINK_1_15, flink.Runtime.FLINK_1_18, flink.Runtime.FLINK_1_19, flink.Runtime.FLINK_1_20
]

flink_runtimes.for_each((runtime) => {
      const flinkApp = new flink.Application(stack, `App-${runtime.value}`, {
        code: flink.ApplicationCode.fromAsset(path.join(__dirname, 'code-asset')),
        runtime: runtime,
      });

      new cloudwatch.Alarm(stack, `Alarm-${runtime.value}`, {
        metric: flinkApp.metricFullRestarts(),
        evaluationPeriods: 1,
        threshold: 3,
      });
    })

integ.IntegTest(app, "ApplicationTest",
    test_cases=[stack]
)
```

The `code` property can use `fromAsset` as shown above to reference a local jar
file in s3 or `fromBucket` to reference a file in s3.

```python
flink.Application(stack, "App",
    code=flink.ApplicationCode.from_bucket(bucket, file_key),
    runtime=flink.Runtime.FLINK_1_19
)
```

The `propertyGroups` property provides a way of passing arbitrary runtime
properties to your Flink application. You can use the
aws-kinesisanalytics-runtime library to [retrieve these
properties](https://docs.aws.amazon.com/kinesisanalytics/latest/java/how-properties.html#how-properties-access).

```python
# bucket: s3.Bucket

flink_app = flink.Application(self, "Application",
    property_groups={
        "FlinkApplicationProperties": {
            "input_stream_name": "my-input-kinesis-stream",
            "output_stream_name": "my-output-kinesis-stream"
        }
    },
    # ...
    runtime=flink.Runtime.FLINK_1_20,
    code=flink.ApplicationCode.from_bucket(bucket, "my-app.jar")
)
```

Flink applications also have specific configuration for passing parameters
when the Flink job starts. These include parameters for checkpointing,
snapshotting, monitoring, and parallelism.

```python
# bucket: s3.Bucket

flink_app = flink.Application(self, "Application",
    code=flink.ApplicationCode.from_bucket(bucket, "my-app.jar"),
    runtime=flink.Runtime.FLINK_1_20,
    checkpointing_enabled=True,  # default is true
    checkpoint_interval=Duration.seconds(30),  # default is 1 minute
    min_pause_between_checkpoints=Duration.seconds(10),  # default is 5 seconds
    log_level=flink.LogLevel.ERROR,  # default is INFO
    metrics_level=flink.MetricsLevel.PARALLELISM,  # default is APPLICATION
    auto_scaling_enabled=False,  # default is true
    parallelism=32,  # default is 1
    parallelism_per_kpu=2,  # default is 1
    snapshots_enabled=False,  # default is true
    log_group=logs.LogGroup(self, "LogGroup")
)
```

Flink applications can optionally be deployed in a VPC:

```python
# bucket: s3.Bucket
# vpc: ec2.Vpc

flink_app = flink.Application(self, "Application",
    code=flink.ApplicationCode.from_bucket(bucket, "my-app.jar"),
    runtime=flink.Runtime.FLINK_1_20,
    vpc=vpc
)
```
