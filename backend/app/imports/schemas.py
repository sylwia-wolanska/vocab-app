from pydantic import BaseModel


class ImportSummary(BaseModel):
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deactivated: int = 0
    reactivated: int = 0
