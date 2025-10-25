# AWS IoT Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

AWS IoT Core lets you connect billions of IoT devices and route trillions of
messages to AWS services without managing infrastructure.

## `TopicRule`

Create a topic rule that give your devices the ability to interact with AWS services.
You can create a topic rule with an action that invoke the Lambda action as following:

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
    topic_rule_name="MyTopicRule",  # optional
    description="invokes the lambda function",  # optional
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp FROM 'device/+/data'"),
    actions=[actions.LambdaFunctionAction(func)]
)
```

Or, you can add an action after constructing the `TopicRule` instance as following:

```python
# func: lambda.Function


topic_rule = iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp FROM 'device/+/data'")
)
topic_rule.add_action(actions.LambdaFunctionAction(func))
```

You can also supply `errorAction` as following,
and the IoT Rule will trigger it if a rule's action is unable to perform:

```python
import aws_cdk.aws_logs as logs


log_group = logs.LogGroup(self, "MyLogGroup")

iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp FROM 'device/+/data'"),
    error_action=actions.CloudWatchLogsAction(log_group)
)
```

If you wanna make the topic rule disable, add property `enabled: false` as following:

```python
iot.TopicRule(self, "TopicRule",
    sql=iot.IotSql.from_string_as_ver20160323("SELECT topic(2) as device_id, timestamp() as timestamp FROM 'device/+/data'"),
    enabled=False
)
```

See also [@aws-cdk/aws-iot-actions-alpha](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-iot-actions-alpha-readme.html) for other actions.

## Logging

AWS IoT provides a [logging feature](https://docs.aws.amazon.com/iot/latest/developerguide/configure-logging.html) that allows you to monitor and log AWS IoT activity.

You can enable IoT logging with the following code:

```python
iot.Logging(self, "Logging",
    log_level=iot.LogLevel.INFO
)
```

**Note**: All logs are forwarded to the `AWSIotLogsV2` log group in CloudWatch.

## Audit

An [AWS IoT Device Defender audit looks](https://docs.aws.amazon.com/iot-device-defender/latest/devguide/device-defender-audit.html) at account- and device-related settings and policies to ensure security measures are in place.
An audit can help you detect any drifts from security best practices or access policies.

### Account Audit Configuration

The IoT audit includes [various audit checks](https://docs.aws.amazon.com/iot-device-defender/latest/devguide/device-defender-audit-checks.html), and it is necessary to configure settings to enable those checks.

You can enable an account audit configuration with the following code:

```python
# Audit notification are sent to the SNS topic
# target_topic: sns.ITopic


iot.AccountAuditConfiguration(self, "AuditConfiguration",
    target_topic=target_topic
)
```

By default, all audit checks are enabled, but it is also possible to enable only specific audit checks.

```python
iot.AccountAuditConfiguration(self, "AuditConfiguration",
    check_configuration=iot.CheckConfiguration(
        # enabled
        authenticated_cognito_role_overly_permissive_check=True,
        # enabled by default
        ca_certificate_expiring_check=undefined,
        # disabled
        ca_certificate_key_quality_check=False,
        conflicting_client_ids_check=False,
        device_certificate_age_check=False,
        device_certificate_expiring_check=False,
        device_certificate_key_quality_check=False,
        device_certificate_shared_check=False,
        intermediate_ca_revoked_for_active_device_certificates_check=False,
        io_tPolicy_potential_mis_configuration_check=False,
        iot_policy_overly_permissive_check=False,
        iot_role_alias_allows_access_to_unused_services_check=False,
        iot_role_alias_overly_permissive_check=False,
        logging_disabled_check=False,
        revoked_ca_certificate_still_active_check=False,
        revoked_device_certificate_still_active_check=False,
        unauthenticated_cognito_role_overly_permissive_check=False
    )
)
```

To configure [the device certificate age check](https://docs.aws.amazon.com/iot-device-defender/latest/devguide/device-certificate-age-check.html), you can specify the duration for the check:

```python
from aws_cdk import Duration


iot.AccountAuditConfiguration(self, "AuditConfiguration",
    check_configuration=iot.CheckConfiguration(
        device_certificate_age_check=True,
        # The default value is 365 days
        # Valid values range from 30 days (minimum) to 3650 days (10 years, maximum)
        device_certificate_age_check_duration=Duration.days(365)
    )
)
```

### Scheduled Audit

You can create a [scheduled audit](https://docs.aws.amazon.com/iot-device-defender/latest/devguide/AuditCommands.html#device-defender-AuditCommandsManageSchedules) that is run at a specified time interval. Checks must be enabled for your account by creating `AccountAuditConfiguration`.

```python
# config: iot.AccountAuditConfiguration


# Daily audit
daily_audit = iot.ScheduledAudit(self, "DailyAudit",
    account_audit_configuration=config,
    frequency=iot.Frequency.DAILY,
    audit_checks=[iot.AuditCheck.AUTHENTICATED_COGNITO_ROLE_OVERLY_PERMISSIVE_CHECK
    ]
)

# Weekly audit
weekly_audit = iot.ScheduledAudit(self, "WeeklyAudit",
    account_audit_configuration=config,
    frequency=iot.Frequency.WEEKLY,
    day_of_week=iot.DayOfWeek.SUNDAY,
    audit_checks=[iot.AuditCheck.CA_CERTIFICATE_EXPIRING_CHECK
    ]
)

# Monthly audit
monthly_audit = iot.ScheduledAudit(self, "MonthlyAudit",
    account_audit_configuration=config,
    frequency=iot.Frequency.MONTHLY,
    day_of_month=iot.DayOfMonth.of(1),
    audit_checks=[iot.AuditCheck.CA_CERTIFICATE_KEY_QUALITY_CHECK
    ]
)
```
