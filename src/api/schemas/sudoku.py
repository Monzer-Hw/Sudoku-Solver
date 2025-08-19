from pydantic import BaseModel

class SolveResponse(BaseModel):
    grid: list[list[int]]
    solved: bool
