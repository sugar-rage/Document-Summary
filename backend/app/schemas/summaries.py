from pydantic import BaseModel, Field


class SummaryCreate(BaseModel):
    mode: str = Field(..., pattern="^(short|medium|long)$")
