"""User-authored consultation notes; never inputs to the wage engine."""

from datetime import date as CalendarDate
from typing import Annotated

from pydantic import ConfigDict, Field, field_validator, model_validator

from agent.schemas.public.base import ContractModel


class ConsultationEvent(ContractModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    date: CalendarDate | None = None
    text: str = Field(max_length=500)

    @field_validator("text")
    @classmethod
    def trim(cls, value):
        return value.strip()


class ConsultationNotes(ContractModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    displayName: str = Field(default="", max_length=100)
    workLocation: str = Field(default="", max_length=200)
    startDate: CalendarDate | None = None
    endDate: CalendarDate | None = None
    purpose: str = Field(default="", max_length=1000)
    desiredHelp: str = Field(default="", max_length=1000)
    facts: str = Field(default="", max_length=2000)
    unknowns: str = Field(default="", max_length=2000)
    materials: str = Field(default="", max_length=2000)
    events: tuple[ConsultationEvent, ...] = Field(default=(), max_length=20)
    questions: tuple[Annotated[str, Field(max_length=300)], ...] = Field(default=(), max_length=20)

    @field_validator(
        "displayName", "workLocation", "purpose", "desiredHelp", "facts", "unknowns", "materials"
    )
    @classmethod
    def trim(cls, value):
        return value.strip()

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, values):
        return tuple(value.strip() for value in values)

    @model_validator(mode="after")
    def date_order(self):
        if self.startDate and self.endDate and self.startDate > self.endDate:
            raise ValueError("End date must not precede start date")
        return self
