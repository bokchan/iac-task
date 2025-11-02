from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from config import InfrastructureConfig
from constructs import Construct


class VpcStack(Stack):
    """A CloudFormation stack that creates a VPC for the application."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: InfrastructureConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=config.get_resource_name("vpc"),
            max_azs=config.vpc.max_azs,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=config.get_resource_name("public"),
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name=config.get_resource_name("private"),
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )
