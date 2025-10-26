from dataclasses import Field, dataclass


@dataclass
class Tag:
    key: str
    value: str


@dataclass
class AWSAccountConfig:
    account_id: str = "146082935119"
    user_arn: str = "arn:aws:iam::146082935119:user/andreas"
    user_id: str = "AIDASEAZYWFHQREJANLS6"
    region: str = "eu-central-1"
    log_group_prefix: str = "andreas-applogs"
    # tags: list[Tag] = [Tag("Creator", "andreas"), Tag("Project", "iac-task")]
