from datetime import date

from pydantic import ConfigDict, Field

from tp_shared.base.base_message import BaseMessage
from tp_shared.types.dc_operator_status import DcOperatorStatus


class GibddDcResultOperator(BaseMessage):
    operator_id: int
    status: DcOperatorStatus
    name: str
    address_line: str
    phone_number: str
    email: str
    site: str
    canceled_date: date | None
    canceled_at: int | None


class GibddDcResultCard(BaseMessage):
    card_number: str = Field(..., min_length=10)
    vin: str = Field(..., min_length=17)
    start_date: date
    end_date: date
    odometer_value: int
    is_active: bool

    operator: GibddDcResultOperator

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class GibddDcResultMessage(BaseMessage):
    version: str = "1.0"
    vin: str
    diagnostic_cards: list[GibddDcResultCard] = []
