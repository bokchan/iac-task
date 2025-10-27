from dataclasses import dataclass


@dataclass
class AWSAccountConfig:
    account_id: str = "357864525704"
    user_arn: str = "arn:aws:iam::357864525704:user/andreas"
    user_id: str = "AIDAVGUTDJ6EJZ63H3WRQ"
    region: str = "eu-central-1"
    log_group_prefix: str = "andreas-applogs"
