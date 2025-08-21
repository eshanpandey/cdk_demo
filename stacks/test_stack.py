from aws_cdk import (
    Stack, CfnOutput, RemovalPolicy,
    aws_s3 as s3,
    aws_ec2 as ec2
)
from constructs import Construct

class TestStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create S3 bucket for testing
        test_bucket = s3.Bucket(self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create VPC for EC2 instance
        vpc = ec2.Vpc(self, "TestVpc",
            max_azs=1,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC
                )
            ]
        )

        # Create EC2 instance for testing
        ec2.Instance(self, "TestInstance",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            )
        )

        # Output the bucket name for reference
        CfnOutput(self, "TestBucketName",
            value=test_bucket.bucket_name,
            description="Name of the test S3 bucket"
        )