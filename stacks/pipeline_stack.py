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

        # Add Test stage (deploy Dummy stack)
        test_stage = DummyApp(self, "TestStage")
        pipeline.add_stage(test_stage)

        # Add manual approval before destroy (recommended for safety)
        pipeline.add_wave("ApproveDestroyWave", post=[
            pipelines.ManualApprovalStep("ApproveDestroy")
        ])

        # Add Destroy stage (CloudFormation delete)
        destroy_stage = DummyDestroyApp(self, "DestroyStage")
        pipeline.add_stage(destroy_stage)


class DummyApp(cdk.Stage):
    """Deploys Dummy stack for testing"""
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        DummyStack(self, "DummyStack")


class DummyDestroyApp(cdk.Stage):
    """Deploys an *empty* stage to effectively delete DummyStack"""
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        # 👇 Nothing inside this Stage
        # When deployed, CloudFormation sees DummyStack no longer exists in this stage,
        # so it deletes it.
