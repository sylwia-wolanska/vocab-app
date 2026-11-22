from pydantic import BaseModel


class StudyCounts(BaseModel):
    due: int
    learn_new: int
    new_total: int
