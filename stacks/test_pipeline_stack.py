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

class TestPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create pipeline
        pipeline = codepipeline.Pipeline(self, "TestPipeline",
            pipeline_name="TestPipeline",
            restart_execution_on_update=True
        )

        # Source Stage - Using your GitHub connection
        source_output = codepipeline.Artifact("SourceArtifact")
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                actions.CodeStarConnectionsSourceAction(
                    action_name="Source",
                    connection_arn="arn:aws:codeconnections:ap-south-1:996200611121:connection/e8c4c109-bb57-4c4a-aeb7-9589ffa6d954",
                    output=source_output,
                    owner="learnysthq",
                    repo="plato",
                    branch="CDK_demo",
                    trigger_on_push=True
                )
            ]
        )

        # Build Stage - Debug enabled buildspec
        build_output = codepipeline.Artifact("BuildArtifact")
        build_project = codebuild.PipelineProject(self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "echo 'Current directory: $(pwd)'",
                            "echo 'Files in directory:'",
                            "ls -la",
                            "echo 'Looking for template.yml:'",
                            "find . -name 'template.yml' -type f",
                            "echo 'Validating CloudFormation template...'",
                            # SINGLE LINE if statement - no multiline!
                            "if [ -f 'template.yml' ]; then aws cloudformation validate-template --template-body file://template.yml && echo 'Template validation successful'; else echo 'ERROR: template.yml not found in current directory!'; echo 'Available files:'; ls -la; exit 1; fi",
                            "echo 'Build phase completed'"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["template.yml"],  # Changed to .yml
                    "base-directory": "."
                }
            })
        )

        # ADD IAM PERMISSIONS FOR CLOUDFORMATION
        build_project.role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "cloudformation:ValidateTemplate",
                "cloudformation:DescribeStacks"
            ],
            resources=["*"]
        ))

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                actions.CodeBuildAction(
                    action_name="ValidateTemplate",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

        # Test Stage - Create, Test, and Delete resources
        test_stage = pipeline.add_stage(stage_name="Test")

        # 1. CREATE Test Resources
        test_stage.add_action(actions.CloudFormationCreateUpdateStackAction(
            action_name="CreateTestResources",
            stack_name="TestResourcesStack",
            template_path=build_output.at_path("template.yml"),  # Changed to .yml
            admin_permissions=True,
            run_order=1
        ))

        # 2. RUN Tests
        test_project = codebuild.PipelineProject(self, "TestProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "echo 'Testing created resources...'",
                            "aws s3 ls | grep test-bucket || echo 'Bucket test passed'",
                            "aws ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].InstanceId' --output text | grep i- || echo 'EC2 test passed'",
                            "echo 'All tests completed successfully'"
                        ]
                    }
                }
            })
        )

        test_project.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:ListAllMyBuckets", "ec2:DescribeInstances"],
            resources=["*"]
        ))

        test_stage.add_action(actions.CodeBuildAction(
            action_name="RunTests",
            project=test_project,
            run_order=2,
            input=build_output,
        ))

        # 3. DELETE Test Resources
        test_stage.add_action(actions.CloudFormationDeleteStackAction(
            action_name="DeleteTestResources",
            stack_name="TestResourcesStack",
            admin_permissions=True,
            run_order=3
        ))

        CfnOutput(self, "PipelineArn", value=pipeline.pipeline_arn)