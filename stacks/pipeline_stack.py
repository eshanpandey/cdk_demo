from aws_cdk import (
    Stack,
    pipelines as pipelines,
)
from constructs import Construct
from .dummy_stack import DummyStack
import aws_cdk as cdk


class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Use your existing CodeStar connection
        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            synth=pipelines.ShellStep("Synth",
                input=pipelines.CodePipelineSource.connection(
                    "eshanpandey/cdk_demo",   # 👈 your repo
                    "main",                   # 👈 branch to track
                    connection_arn="arn:aws:codeconnections:ap-south-1:996200611121:connection/611f4017-ae11-4f95-8ab1-9cf3e2cf8610"
                ),
                commands=[
                    "npm install -g aws-cdk",          # install CDK CLI
                    "pip install -r requirements.txt", # install Python deps
                    "cdk synth"                        # synthesize cloud assembly
                ]
            )
        )

        # Add Test stage (Dummy stack)
        pipeline.add_stage(DummyApp(self, "TestStage"))

        # Add Destroy stage
        pipeline.add_wave("DestroyWave", post=[
            pipelines.ShellStep("DestroyStep",
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk destroy DummyStack --force --app ."
                ]
            )
        ])


class DummyApp(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        DummyStack(self, "DummyStack")
