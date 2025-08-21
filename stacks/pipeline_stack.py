from aws_cdk import (
    Stack,
    pipelines as pipelines,
    RemovalPolicy,
    aws_s3 as s3,
)
from constructs import Construct
import aws_cdk as cdk


class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            synth=pipelines.ShellStep("Synth",
                input=pipelines.CodePipelineSource.connection(
                    "eshanpandey/cdk_demo",
                    "main",
                    connection_arn="arn:aws:codeconnections:ap-south-1:996200611121:connection/611f4017-ae11-4f95-8ab1-9cf3e2cf8610"
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk synth"
                ]
            )
        )

        # Deploy stage
        pipeline.add_stage(DummyApp(self, "TestStage"))

        # Destroy stage (CloudFormation will delete stack)
        pipeline.add_stage(DestroyApp(self, "DestroyStage"))


class DummyApp(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        DummyStack(self, "DummyStack")


class DestroyApp(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        DestroyStack(self, "DestroyDummyStack")


class DummyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        s3.Bucket(
            self, "DemoBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )


class DestroyStack(Stack):
    """An empty stack just so CloudFormation DELETE_ONLY works"""
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        # no resources, ensures stack can be safely deleted
