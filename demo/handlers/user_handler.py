import re
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from cibo import BaseApiBody, Handler, SimpleContext
from cibo.args import BaseApiPath, BaseApiSuccessResp
from demo.handlers import api


class User(BaseModel):
    name: str = Field(description="姓名")
    emails: Optional[List[str]] = Field(description="邮箱")

    @classmethod
    def validate(cls, value: Dict):
        obj = cls(**value)
        if obj.emails:
            if not all(
                [
                    re.match(r"^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$", email)
                    for email in obj.emails
                ]
            ):
                raise ValueError("email is not valid")
        return obj


@api.post("/user")
class UserHandler(Handler):
    class Body(BaseApiBody):
        class Teacher(BaseModel):
            id: int
            name: str

        user: User
        inviter: str
        invitees: List[str] = Field(description="邀请到的用户")

        teacher: Teacher

    class Resp(BaseApiSuccessResp):
        """用户信息响应"""

        class Teacher(BaseModel):
            id: int
            name: str
            email: str

        user: User = Field(description="用户信息")
        inviter: str
        invitees: List[str] = Field(description="邀请到的用户")
        teachers: List[Dict[str, Teacher]]

    def handle(self, context: SimpleContext, body: Body):
        """handle user"""
        return context.success(user=body.user, inviter=body.inviter, invitees=body.invitees)


@api.get("/callback/<int:id>/<string:suffix>")
class CallBackHandler(Handler):
    class Path(BaseApiPath):
        id: int = Field(description="description of id")
        suffix: str = Field(description="description of suffix")

    def handle(self, context: SimpleContext, path: Path):
        """handle callback"""
        return context.success(id=path.id, suffix=path.suffix)
