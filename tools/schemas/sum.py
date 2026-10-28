from pydantic import BaseModel, Field

NAME = "sum"
DESCRIPTION = "Calculates the sum of two numbers."

class Parameters(BaseModel):
    a: float = Field(
        description="The first number to add."
    )
    b: float = Field(
        description="The second number to add."
    )