from dataclasses import dataclass


@dataclass
class AWSAccountConfig:
    # Phasetree
    # account_id: str = "146082935119"
    # user_arn: str = "arn:aws:iam::146082935119:user/andreas"
    # user_id: str = "AIDASEAZYWFHQREJANLS6"
    # Personal
    account_id: str = "357864525704"
    user_arn: str = "arn:aws:iam::357864525704:user/andreas"
    user_id: str = "AIDAVGUTDJ6EJZ63H3WRQ"
    region: str = "eu-central-1"
    log_group_prefix: str = "andreas-applogs"
