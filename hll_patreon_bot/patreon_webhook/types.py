import enum
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class PatreonTriggerResource(enum.Enum):
    MEMBER = "members"
    PLEDGE = "pledge"


class PatreonTriggerAction(enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PatronStatus(enum.Enum):
    active = "active_patron"
    declined = "declined_patron"
    former = "former_patron"
    none = None

    def is_successful(self):
        return self == PatronStatus.active


class ChargeStatus(enum.Enum):
    paid = "paid"
    declined = "declined"
    deleted = "deleted"
    pending = "pending"
    refunded = "refunded"
    fraud = "fraud"
    other = "other"

    def is_successful(self) -> bool:
        return self == ChargeStatus.paid


@dataclass
class PatreonWebhook:
    resource: PatreonTriggerResource
    action: PatreonTriggerAction
    sub_resource: PatreonTriggerResource | None = None


class PatreonMemberWH(TypedDict):
    id: str
    currently_entitled_amount_cents: int | None
    email: str
    last_charge_date: datetime | None
    last_charge_status: ChargeStatus
    patron_status: PatronStatus
    discord_user_id: str | None


class PatreonPledgeWH(TypedDict):
    id: str
    currently_entitled_amount_cents: int | None
    email: str | None
    last_charge_date: datetime
    next_charge_date: datetime | None
    last_charge_status: ChargeStatus
    patron_status: PatronStatus
    discord_user_id: str | None
