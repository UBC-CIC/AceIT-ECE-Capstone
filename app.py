#!/usr/bin/env python3
import os

import aws_cdk as cdk

from priv_ace_it_ece_capstone_main.priv_ace_it_ece_capstone_main_stack import PrivAceItEceCapstoneMainStack


app = cdk.App()
env_prefix = app.node.try_get_context("env_prefix") or "aceitdev"
PrivAceItEceCapstoneMainStack(app, f"{env_prefix}-MainStack", env_prefix=env_prefix,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    env=cdk.Environment(account=os.getenv('AWS_ACCOUNT_ID'), region=os.getenv('AWS_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
