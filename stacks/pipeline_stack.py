from aws_cdk import (
    Stack, CfnOutput, RemovalPolicy,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2
)
from constructs import Construct

class CodePipelineTestStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create source bucket WITHOUT auto_delete_objects
        source_bucket = s3.Bucket(self, "SourceBucket",
            removal_policy=RemovalPolicy.DESTROY
            # No Lambda will be created
        )

        # Create artifacts
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # Create pipeline
        pipeline = codepipeline.Pipeline(self, "Pipeline",
            pipeline_name="TestPipeline",
            restart_execution_on_update=True
        )

        # Source stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                actions.S3SourceAction(
                    action_name="S3Source",
                    bucket=source_bucket,
                    bucket_key="source.zip",
                    output=source_output,
                    trigger=actions.S3Trigger.POLL
                )
            ]
        )

        # Build project
        build_project = codebuild.PipelineProject(self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": ["echo 'No dependencies to install'"]
                    },
                    "build": {
                        "commands": [
                            "echo 'Building application...'",
                            "echo 'Build completed successfully'"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["**/*"]
                }
            })
        )

        # Build stage
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                actions.CodeBuildAction(
                    action_name="CodeBuild",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

        # Test stage
        test_stage = pipeline.add_stage(stage_name="Test")

        # Create test resources
        create_test_action = actions.CloudFormationCreateUpdateStackAction(
            action_name="CreateTestResources",
            stack_name="TestStack",
            template_path=build_output.at_path("TestStack.template.json"),
            admin_permissions=True,
            run_order=1
        )
        test_stage.add_action(create_test_action)

        # Test commands
        test_project = codebuild.PipelineProject(self, "TestProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "echo 'Running tests...'",
                            "aws s3 ls",
                            "aws ec2 describe-instances --filters Name=instance-state-name,Values=running",
                            "echo 'Tests completed successfully'"
                        ]
                    }
                }
            })
        )

        # Grant test permissions
        test_project.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:ListAllMyBuckets", "ec2:DescribeInstances"],
            resources=["*"]
        ))

        run_tests_action = actions.CodeBuildAction(
            action_name="RunTests",
            project=test_project,
            input=source_output,
            run_order=2
        )
        test_stage.add_action(run_tests_action)

        # Delete test resources
        delete_test_action = actions.CloudFormationDeleteStackAction(
            action_name="DeleteTestResources",
            stack_name="TestStack",
            admin_permissions=True,
            run_order=3
        )
        test_stage.add_action(delete_test_action)

        # Deploy stage (placeholder)
        deploy_stage = pipeline.add_stage(stage_name="Deploy")
        deploy_stage.add_action(actions.ManualApprovalAction(
            action_name="DeployApproval",
            run_order=1
        ))

        # Outputz
        CfnOutput(self, "PipelineArn", value=pipeline.pipeline_arn)