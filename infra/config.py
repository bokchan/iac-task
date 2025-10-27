from dataclasses import dataclass


@dataclass
class AWSAccountConfig:
    account_id: str = "146082935119"
    user_arn: str = "arn:aws:iam::146082935119:user/andreas"
    user_id: str = "AIDASEAZYWFHQREJANLS6"
    region: str = "eu-central-1"
    log_group_prefix: str = "andreas-applogs"
