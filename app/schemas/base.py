from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MoneyModel(ORMBaseModel):
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

