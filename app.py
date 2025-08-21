#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.pipeline_stack import PipelineStack

app = cdk.App()
PipelineStack(app, "PipelineStack",
    env=cdk.Environment(account="996200611121", region="ap-south-1")
)
app.synth()
