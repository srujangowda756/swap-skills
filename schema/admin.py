from pydantic import BaseModel

class UpdatedSkill(BaseModel):
    name:str
    description:str