r'''
# Tweet Queue for AWS CDK

This is an [AWS CDK](https://github.com/awslabs/aws-cdk) construct library which
allows you to get a feed of Twitter search results into an SQS queue. It works
by periodically polling the freely available [Twitter Standard Search
API](https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets.html) and
sending all new tweets to an SQS queue.

Inspired by
[@jlhood](https://github.com/awslabs/aws-serverless-twitter-event-source/commits?author=jlhood)'s
[aws-serverless-twitter-event-source](https://github.com/awslabs/aws-serverless-twitter-event-source)

## Architecture

![](https://github.com/eladb/cdk-tweet-queue/raw/main/images/architecture.png)

1. A CloudWatch Event Rule triggers the poller AWS Lambda function periodically
2. The poller reads the last checkpoint from a DynamoDB table (if exists)
3. The poller issues a Twitter search query for all new tweets
4. The poller enqueues all tweets to an SQS queue
5. The poller stores the ID of the last tweet into the DynamoDB checkpoint table.
6. Rinse & repeat.

## Twitter API Keys

To issue a Twitter search request, you will need to
[apply](https://developer.twitter.com/en/apply-for-access.html) for a Twitter
developer account, and obtain API keys through by defining a [new
application](http://twitter.com/oauth_clients/new).

The Twitter API keys are read by the poller from an [AWS Secrets
Manager](https://aws.amazon.com/secrets-manager/) entry. The entry must contain
the following attributes: `consumer_key`, `consumer_secret`, `access_token_key`
and `access_token_secret` (exact names).

1. Create a new AWS Secrets Manager entry for your API keys
2. Fill in the key values as shown below:
   ![](https://github.com/eladb/cdk-tweet-queue/raw/main/images/secretsmanager.png)
3. Store the key
4. Obtain the ARN of the secret (you will need it soon).

## Usage

Use `npm` to install the module in your CDK project. This will also add it to
your `package.json` file.

```console
$ npm install cdk-tweet-queue
```

Add a `TweetQueue` to your CDK stack:

```python
import { TweetQueue } from 'cdk-tweet-queue';

const queue = new TweetQueue(this, 'TweetStream', {
  // this is the ARN of the secret you stored
  secretArn: 'arn:aws:secretsmanager:us-east-1:1234567891234:secret:xxxxxxxxx'

  // twitter search query
  // see https://developer.twitter.com/en/docs/tweets/search/guides/standard-operators
  query: '#awscdk',

  // optional properties
  intervalMin: 60,          // optional: polling interval in minutes
  retentionPeriodSec: 60,   // optional: queue retention period
  visibilityTimeoutSec: 60, // optional: queue visilibity timeout
});
```

Now, `queue` is an `sqs.Queue` object and can be used anywhere a queue is
accepted. For example, you could process the queue messages using an AWS Lambda
function by setting up an SQS event source mapping.

## Development

The project is managed by [projen](https://github.com/projen/projen) and offers the following commands:

* `yarn projen` - Synthesize the project configuration.
* `yarn compile` - Compile all source code.
* `yarn test` - Run all tests.
* `yarn build` - Complie, test, and package the module.

## Integration test

There is also an integration test that can be executed by running the following commands. You will need to set the `TWEET_QUEUE_SECRET_ARN` environment variable in order for the test to be able to use your Twitter API keys.

```console
$ yarn integ:deploy
```

Don't forget to destroy:

```console
$ yarn integ:destroy
```

You can also run any cdk command on the integration test application by running:

```console
yarn integ <command>
```

## License

Apache-2.0
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

import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class TweetQueue(
    _aws_cdk_aws_sqs_ceddda9d.Queue,
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-tweet-queue.TweetQueue",
):
    def __init__(
        self,
        parent: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        query: builtins.str,
        secret_arn: builtins.str,
        interval_min: typing.Optional[jsii.Number] = None,
        retention_period_sec: typing.Optional[jsii.Number] = None,
        visibility_timeout_sec: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param parent: -
        :param id: -
        :param query: The twitter query string to stream.
        :param secret_arn: The SecretsManager secret that contains Twitter authentication credentials from https://apps.twitter.com/ with the following attributes (exact names): - consumer_key - consumer_secret - access_token_key - access_token_secret.
        :param interval_min: Polling interval in minutes. Set to 0 to disable polling. Default: 1min
        :param retention_period_sec: Number of seconds for messages to wait in the queue for processing. After this time, messages will be removed from the queue. Default: 60 seconds
        :param visibility_timeout_sec: Number of seconds for messages to be invisible while they are processed. Based on the amount of time it would require to process a single message. Default: 60 seconds
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae78463f3971fd58b1dba203cff938a429a0fb63a0374a1da182efed47b58f88)
            check_type(argname="argument parent", value=parent, expected_type=type_hints["parent"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = TweetQueueProps(
            query=query,
            secret_arn=secret_arn,
            interval_min=interval_min,
            retention_period_sec=retention_period_sec,
            visibility_timeout_sec=visibility_timeout_sec,
        )

        jsii.create(self.__class__, self, [parent, id, props])


@jsii.data_type(
    jsii_type="cdk-tweet-queue.TweetQueueProps",
    jsii_struct_bases=[],
    name_mapping={
        "query": "query",
        "secret_arn": "secretArn",
        "interval_min": "intervalMin",
        "retention_period_sec": "retentionPeriodSec",
        "visibility_timeout_sec": "visibilityTimeoutSec",
    },
)
class TweetQueueProps:
    def __init__(
        self,
        *,
        query: builtins.str,
        secret_arn: builtins.str,
        interval_min: typing.Optional[jsii.Number] = None,
        retention_period_sec: typing.Optional[jsii.Number] = None,
        visibility_timeout_sec: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param query: The twitter query string to stream.
        :param secret_arn: The SecretsManager secret that contains Twitter authentication credentials from https://apps.twitter.com/ with the following attributes (exact names): - consumer_key - consumer_secret - access_token_key - access_token_secret.
        :param interval_min: Polling interval in minutes. Set to 0 to disable polling. Default: 1min
        :param retention_period_sec: Number of seconds for messages to wait in the queue for processing. After this time, messages will be removed from the queue. Default: 60 seconds
        :param visibility_timeout_sec: Number of seconds for messages to be invisible while they are processed. Based on the amount of time it would require to process a single message. Default: 60 seconds
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e207700c31acaa9b874071145c70e822e9521b55512fb318d24e3d27a59106d5)
            check_type(argname="argument query", value=query, expected_type=type_hints["query"])
            check_type(argname="argument secret_arn", value=secret_arn, expected_type=type_hints["secret_arn"])
            check_type(argname="argument interval_min", value=interval_min, expected_type=type_hints["interval_min"])
            check_type(argname="argument retention_period_sec", value=retention_period_sec, expected_type=type_hints["retention_period_sec"])
            check_type(argname="argument visibility_timeout_sec", value=visibility_timeout_sec, expected_type=type_hints["visibility_timeout_sec"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "query": query,
            "secret_arn": secret_arn,
        }
        if interval_min is not None:
            self._values["interval_min"] = interval_min
        if retention_period_sec is not None:
            self._values["retention_period_sec"] = retention_period_sec
        if visibility_timeout_sec is not None:
            self._values["visibility_timeout_sec"] = visibility_timeout_sec

    @builtins.property
    def query(self) -> builtins.str:
        '''The twitter query string to stream.'''
        result = self._values.get("query")
        assert result is not None, "Required property 'query' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def secret_arn(self) -> builtins.str:
        '''The SecretsManager secret that contains Twitter authentication credentials from https://apps.twitter.com/ with the following attributes (exact names):  - consumer_key  - consumer_secret  - access_token_key  - access_token_secret.'''
        result = self._values.get("secret_arn")
        assert result is not None, "Required property 'secret_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def interval_min(self) -> typing.Optional[jsii.Number]:
        '''Polling interval in minutes.

        Set to 0 to disable polling.

        :default: 1min
        '''
        result = self._values.get("interval_min")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def retention_period_sec(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds for messages to wait in the queue for processing.

        After this time, messages will be removed from the queue.

        :default: 60 seconds
        '''
        result = self._values.get("retention_period_sec")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def visibility_timeout_sec(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds for messages to be invisible while they are processed.

        Based on the amount of time it would require to process a single message.

        :default: 60 seconds
        '''
        result = self._values.get("visibility_timeout_sec")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TweetQueueProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "TweetQueue",
    "TweetQueueProps",
]

publication.publish()

def _typecheckingstub__ae78463f3971fd58b1dba203cff938a429a0fb63a0374a1da182efed47b58f88(
    parent: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    query: builtins.str,
    secret_arn: builtins.str,
    interval_min: typing.Optional[jsii.Number] = None,
    retention_period_sec: typing.Optional[jsii.Number] = None,
    visibility_timeout_sec: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e207700c31acaa9b874071145c70e822e9521b55512fb318d24e3d27a59106d5(
    *,
    query: builtins.str,
    secret_arn: builtins.str,
    interval_min: typing.Optional[jsii.Number] = None,
    retention_period_sec: typing.Optional[jsii.Number] = None,
    visibility_timeout_sec: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass
