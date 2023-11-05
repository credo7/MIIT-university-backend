import json

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    full_name: str


class User(UserOut):
    approved: bool

if __name__ == "__main__":
    user = User(id=5, full_name="Vitaly AKhmetzianov", approved=True)
    print(user.dict())
    user_out = UserOut(**user.dict())
    print(json.dumps(user_out))