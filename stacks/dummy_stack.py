from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy   # import RemovalPolicy directly
)
from constructs import Construct


class DummyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Just a demo S3 bucket
        s3.Bucket(
            self, "DemoBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
