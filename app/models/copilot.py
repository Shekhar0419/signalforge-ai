from pydantic import BaseModel, Field, field_validator


class CopilotRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1000,
        description="Question about the analyzed dataset.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "The copilot question cannot be empty."
            )

        return cleaned_value


class CopilotResponse(BaseModel):
    dataset_id: str
    question: str
    answer: str
    provider: str = "fallback"
    model: str | None = None