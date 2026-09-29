from typing import List

from pydantic import BaseModel, Field, field_validator


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=2, max_length=120)
    parties: str = Field(..., min_length=2, max_length=5000)
    terms: List[str] = Field(..., min_length=1, max_length=50)
    effective_date: str = Field(..., min_length=2, max_length=100)

    @field_validator("terms")
    @classmethod
    def clean_terms(cls, value: List[str]) -> List[str]:
        cleaned = [term.strip() for term in value if term and term.strip()]
        if not cleaned:
            raise ValueError("At least one term is required.")
        return cleaned


class DocumentResponse(BaseModel):
    document_type: str
    content: str
    model: str