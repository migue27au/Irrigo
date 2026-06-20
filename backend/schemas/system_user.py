from pydantic import BaseModel

class ShareSystemRequest(BaseModel):
    username: str
    role: str = "viewer"

class SharedUserOut(BaseModel):
    id: int
    user_id: int
    username: str
    name: str | None
    role: str

    class Config:
        from_attributes = True