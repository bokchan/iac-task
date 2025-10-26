from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns

# from aws_cdk import aws_ecs_patterns as ecs_patterns
from constructs import Construct


class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "AndreasVpc", max_azs=2)  # default is all AZs in region
        cluster = ecs.Cluster(self, "AndreasCluster", vpc=vpc)

        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "AndreasFargateService",
            cluster=cluster,  # Required
            cpu=512,  # Default is 256
            desired_count=2,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
            ),
            memory_limit_mib=2048,  # Default is 512
            public_load_balancer=True,
        )  # Default is True
