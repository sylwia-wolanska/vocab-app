from pydantic import BaseModel


class ImportSummary(BaseModel):
    added: int
    already_present: int
