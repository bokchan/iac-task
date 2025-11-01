from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_logs as logs
from config import AppConfig
from constructs import Construct

from stacks.ecr_stack import EcrStack
from stacks.vpc_stack import VpcStack


class AppStack(Stack):
    """A CloudFormation stack that creates the ECS service for the application."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: AppConfig,
        vpc_stack: VpcStack,
        ecr_stack: EcrStack,
        image_tag: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CloudWatch log group with required naming convention
        log_group = logs.LogGroup(
            self,
            "AppLogGroup",
            log_group_name=config.get_log_group_name(),
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
            if config.environment == "dev"
            else RemovalPolicy.RETAIN,
        )

        # Use the high-level ApplicationLoadBalancedFargateService construct
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FargateService",
            vpc=vpc_stack.vpc,
            cpu=config.app_service.cpu,
            memory_limit_mib=config.app_service.memory_limit_mb,
            desired_count=config.app_service.desired_count,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(
                    ecr_stack.repository, tag=image_tag
                ),
                container_port=config.app_service.container_port,
                environment={
                    "IMAGE_TAG": image_tag,
                    **config.app_service.app_environment.to_environment_dict(),  # type: ignore[union-attr]
                },
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix="ecs",
                    log_group=log_group,
                ),
            ),
            public_load_balancer=True,
        )

        # Configure health checks with proper timeouts and intervals
        fargate_service.target_group.configure_health_check(
            path="/health", interval=Duration.seconds(30)
        )

        # Output the URL of the load balancer
        CfnOutput(
            self,
            "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
            description="The DNS name of the application load balancer",
        )

        # Output the log group name for easy reference
        CfnOutput(
            self,
            "LogGroupName",
            value=log_group.log_group_name,
            description="CloudWatch log group name for application logs",
        )
