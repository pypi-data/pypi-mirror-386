from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class Item(BaseModel):
    id: str
    payload: Mapping[str, Any] | BaseModel | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def prompt_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping ready for prompt rendering."""
        data: dict[str, Any] = (
            self._serialise_payload(self.payload) if self.payload is not None else {}
        )
        data["id"] = self.id
        return data

    @staticmethod
    def _serialise_payload(payload: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
        converted = Item._convert(payload)
        if isinstance(converted, Mapping):
            return {str(key): value for key, value in converted.items()}

        msg = "Item payload must serialise to a mapping"
        raise TypeError(msg)

    @staticmethod
    def _convert(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")

        if isinstance(value, Mapping):
            return {str(key): Item._convert(val) for key, val in value.items()}

        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [Item._convert(item) for item in value]

        return value


class Juror(BaseModel):
    id: str
    instructions: str | None = None
    model: str | None = None
    agent: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _exclusive_agent_or_model(self) -> "Juror":
        """Allow either `agent` or `model`, but not both, to avoid ambiguity."""
        if self.agent is not None and self.model is not None:
            raise ValueError("Provide either `agent` or `model`, not both.")
        return self


class ComparisonChoice(str, Enum):
    item_a = "item_a"
    item_b = "item_b"


class Comparison(BaseModel):
    juror_id: str
    item_a: str
    item_b: str
    winner: str
    created_at: datetime
    cost: Decimal | None = None
