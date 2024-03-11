import enum
from datetime import datetime
from typing import TypedDict


class PatronStatus(enum.Enum):
    active_patron = "Active"
    declined_patron = "Declined"
    former_patron = "Former"
    none = None

    def is_successful(self):
        return self == PatronStatus.active_patron


class ChargeStatus(enum.Enum):
    paid = "Paid"
    declined = "Declined"
    deleted = "Deleted"
    pending = "Pending"
    refunded = "Refunded"
    fraud = "Fraud"
    other = "Other"
    none = None

    def is_successful(self) -> bool:
        return self == ChargeStatus.paid

    def __str__(self) -> str:
        return str(self.value)


class PledgeEventType(enum.Enum):
    start = "pledge_start"
    delete = "pledge_delete"
    upgrade = "pledge_upgrade"
    downgrade = "pledge_downgrade"
    subscription = "subscription"

    def __str__(self):
        return self.value.replace("_", " ").title()


class PledgeHistory(TypedDict):
    id: str
    type: PledgeEventType
    amount_cents: int
    date: datetime
    status: ChargeStatus
    tier_id: str


# TODO: include pledge history again
class PatreonMember(TypedDict):
    id: str
    name: str
    email: str
    currently_entitled_amount_cents: int
    last_charge_date: datetime | None
    last_charge_status: ChargeStatus
    next_charge_date: datetime | None
    patron_status: PatronStatus
    discord_user_id: int | None
    note: str
    thumb_url: str | None  # user
    pledge_history: list[PledgeHistory]


# TODO: include pledge history again
class PatreonCampaignMember(TypedDict):
    id: str
    name: str
    email: str
    currently_entitled_amount_cents: int
    last_charge_date: datetime | None
    last_charge_status: ChargeStatus
    next_charge_date: datetime | None
    patron_status: PatronStatus
    note: str

    # includes
    user_id: str
    pledge_ids: set[str]


class PatreonUserAttributes(TypedDict):
    thumb_url: str
    discord_user_id: int | None
