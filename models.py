from enum import Enum
from pydantic import BaseModel

class UserProfileInfo(BaseModel):
    first_name: str
    last_name: str
    status_text: str


class MemberInfoReqBody(BaseModel):
    id: str
    name: str
    username: str
    email: str
    title: str
    timezone: str
    profile: UserProfileInfo


class UserInfo(BaseModel):
    id: str
    name: str
    username: str
    email: str
    title: str
    timezone: str
    profile: UserProfileInfo


class UserResearchDataType(Enum):
    GITHUB = "github"
    COMPANY = "company"


class UserResearchData(BaseModel):
    url: str
    title: str
    content: str
    type: UserResearchDataType


class UserAnalysis(BaseModel):
    fit_score: int
    insights: list[str]
    recommendations: list[str]
