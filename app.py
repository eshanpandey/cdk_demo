#!/usr/bin/env python3

from aws_cdk import App
from stacks.test_pipeline_stack import TestPipelineStack  # ← Import from test_pipeline_stack.py

app = App()
TestPipelineStack(app, "TestPipelineStack")
app.synth()