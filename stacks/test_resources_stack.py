from aws_cdk import (
    Stack, CfnOutput, RemovalPolicy,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ssm as ssm
)
from constructs import Construct

class TestResourcesStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket
        test_bucket = s3.Bucket(self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create VPC
        vpc = ec2.Vpc(self, "TestVpc",
            max_azs=1,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Get latest Amazon Linux AMI using SSM parameter (no hardcoded AMI)
        amzn_linux_ami = ec2.MachineImage.from_ssm_parameter(
            "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64",
            os=ec2.OperatingSystemType.LINUX
        )

        # Create EC2 Instance
        instance = ec2.Instance(self, "TestInstance",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=amzn_linux_ami
        )

        # Outputs
        CfnOutput(self, "TestBucketName", value=test_bucket.bucket_name)
        CfnOutput(self, "TestInstanceId", value=instance.instance_id)
        CfnOutput(self, "TestVpcId", value=vpc.vpc_id)