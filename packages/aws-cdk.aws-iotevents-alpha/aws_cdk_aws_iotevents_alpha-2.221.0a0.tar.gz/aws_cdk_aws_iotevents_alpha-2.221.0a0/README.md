# AWS::IoTEvents Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

AWS IoT Events enables you to monitor your equipment or device fleets for
failures or changes in operation, and to trigger actions when such events
occur.

## `DetectorModel`

The following example creates an AWS IoT Events detector model to your stack.
The detector model need a reference to at least one AWS IoT Events input.
AWS IoT Events inputs enable the detector to get MQTT payload values from IoT Core rules.

You can define built-in actions to use a timer or set a variable, or send data to other AWS resources.
See also [@aws-cdk/aws-iotevents-actions-alpha](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-iotevents-actions-alpha-readme.html) for other actions.

```python
import aws_cdk.aws_iotevents_alpha as iotevents
import aws_cdk.aws_iotevents_actions_alpha as actions
import aws_cdk.aws_lambda as lambda_

# func: lambda.IFunction


input = iotevents.Input(self, "MyInput",
    input_name="my_input",  # optional
    attribute_json_paths=["payload.deviceId", "payload.temperature"]
)

warm_state = iotevents.State(
    state_name="warm",
    on_enter=[iotevents.Event(
        event_name="test-enter-event",
        condition=iotevents.Expression.current_input(input),
        actions=[actions.LambdaInvokeAction(func)]
    )],
    on_input=[iotevents.Event( # optional
        event_name="test-input-event",
        actions=[actions.LambdaInvokeAction(func)])],
    on_exit=[iotevents.Event( # optional
        event_name="test-exit-event",
        actions=[actions.LambdaInvokeAction(func)])]
)
cold_state = iotevents.State(
    state_name="cold"
)

# transit to coldState when temperature is less than 15
warm_state.transition_to(cold_state,
    event_name="to_coldState",  # optional property, default by combining the names of the States
    when=iotevents.Expression.lt(
        iotevents.Expression.input_attribute(input, "payload.temperature"),
        iotevents.Expression.from_string("15")),
    executing=[actions.LambdaInvokeAction(func)]
)
# transit to warmState when temperature is greater than or equal to 15
cold_state.transition_to(warm_state,
    when=iotevents.Expression.gte(
        iotevents.Expression.input_attribute(input, "payload.temperature"),
        iotevents.Expression.from_string("15"))
)

iotevents.DetectorModel(self, "MyDetectorModel",
    detector_model_name="test-detector-model",  # optional
    description="test-detector-model-description",  # optional property, default is none
    evaluation_method=iotevents.EventEvaluation.SERIAL,  # optional property, default is iotevents.EventEvaluation.BATCH
    detector_key="payload.deviceId",  # optional property, default is none and single detector instance will be created and all inputs will be routed to it
    initial_state=warm_state
)
```

To grant permissions to put messages in the input,
you can use the `grantWrite()` method:

```python
import aws_cdk.aws_iam as iam
import aws_cdk.aws_iotevents_alpha as iotevents

# grantable: iam.IGrantable

input = iotevents.Input.from_input_name(self, "MyInput", "my_input")

input.grant_write(grantable)
```
