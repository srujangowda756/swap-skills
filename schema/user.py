from pydantic import BaseModel

class BaseCredentials(BaseModel):
    email:str 
    name:str 
    password:str

class user_credentials(BaseCredentials):
    pass

