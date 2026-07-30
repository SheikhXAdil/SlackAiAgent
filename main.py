from fastapi import FastAPI, HTTPException, Request
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import httpx
import os
import asyncio
import re
from datetime import datetime
import logging
from enum import Enum
from pydantic import BaseModel

load_dotenv()

environment = os.getenv("ENVIRONMENT", "development")

logging.basicConfig(level=logging.INFO)

log = {
    "info": logging.info,
    "error": logging.error,
    "warning": logging.warning,
}


client = WebClient()


class MemberInfoReqBody(BaseModel):
    pass


class UserProfileInfo(BaseModel):
    first_name: str
    last_name: str
    status_text: str


class UserInfo(BaseModel):
    id: str
    name: str
    username: str
    email: str
    title: str
    timezone: str
    profile: UserProfileInfo


class UserResearchDataType(Enum):
    GITHUB = 'github'
    COMPANY = 'company'

class UserResearchData(BaseModel):
    url: str
    title: str
    content: str
    type: UserResearchDataType


class UserAnalysis(BaseModel):
    pass


class SlackAgent:
    def __init__(self):
        self.app = FastAPI()

        self.slack = App(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )
        self.slack_handler = SocketModeHandler(
            self.slack, os.environ["SLACK_APP_TOKEN"]
        )
        self.webClient = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.3,
            max_output_tokens=2048,
        )

        self.setup_fast_api()
        self.setup_slack_events()

    def setup_slack_events(self):
        @self.slack.error
        async def handle_slack_error(error):
            log["error"]("Slack Error", error.message)

        @self.slack.event("team_join")
        async def handle_team_join(event):
            try:
                log["info"](f"event: {event}")

                user = event["user"]
                name = user.get("real_name") or user.get("name")

                log["info"](f"New member joined: {name}")

                userInfo = await self.get_user_info(user.get("id"))
                await self.analyze_and_post(userInfo)

            except Exception as e:
                log.error("Error calling team_join", e)

        @self.slack.event("member_joined_channel")
        async def handle_member_joined_channel(event):
            try:
                log["info"](f"event: {event}")

                user = event["user"]
                channel_type = event["channel_type"]
                channel = event["channel"]

                if channel_type == "c":
                    log["info"](f"Member {user} joined channel {channel}")

                    userInfo = await self.get_user_info(user.get("id"))
                    await self.analyze_and_post(userInfo)

            except Exception as e:
                log["error"]("Error calling member_joined_channel", e)

    def setup_fast_api(self):
        @self.app.exception_handler(HTTPException)
        def handle_http_exception(req: Request, exc: HTTPException):
            return {"status_code": exc.status_code, "error": exc.detail}

        @self.app.exception_handler(Exception)
        def handle_unchecked_exception(req: Request, exc: Exception):
            log["error"]("Error in handling Request", str(exc))
            log["error"]("Request Url", str(req.url))
            log["error"]("Request Body", req.body)

            return {"status_code": 500, "error": "Internal Server Error"}

        @self.app.get("/")
        def server_health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.post("/test/analyze-member")
        async def test_analyze_member(member_info: MemberInfoReqBody):
            if environment != "development":
                raise HTTPException(status_code=401, detail={"error": "Unauthorized"})

            analysis = await self.analyze_and_post(member_info)

            return {
                "success": True,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
            }

    async def get_user_info(self, userId: str) -> UserInfo:
        res = await self.webClient.users_info(userId)
        user = res.user

        return UserInfo(
            id=user.id,
            username=user.name,
            timezone=user.tz,
            name=user.real_name if user.real_name else user.name,
            email=user.profile.email if user.profile else None,
            title=user.profile.title if user.profile else None,
            profile=UserProfileInfo(
                first_name=user.profile.first_name if user.profile else None,
                last_name=user.profile.last_name if user.profile else None,
                status_text=user.profile.status_text if user.profile else None,
            ),
        )

    async def analyze_and_post(self, member_info: UserInfo):
        analysis_id = None

        try:
            log["info"](f"Processing info of member: {member_info.name}")

            research_data = self.do_basic_research(member_info)
            analysis = self.analyze_with_ai(member_info, research_data)

            log["info"](
                f"Saving analysis on info of member: {member_info.name} to database"
            )

            analysis_id = await self.save_member_analysis(
                member_info, analysis, research_data
            )

            await self.post_analysis_to_channel(member_info, analysis, research_data)

            if analysis_id:
                await self.mark_sent_to_slack(analysis_id)

            pass
        except Exception as e:
            log["error"](f"Error analyzing info of member: {member_info.name}", e)

            if analysis_id:
                log["info"](
                    f"Analysis on info of member: {member_info.name} saved to database but not sent to slack due to error",
                    e,
                )

            raise e

    async def do_basic_research(self, member_info: UserInfo) -> UserResearchData:
        results = []

        try:
            if member_info.email and not self.is_personal_email(member_info.email):
                domain = member_info.email.split("@")[1]
                company_info = await self.get_company_info(domain)

                if company_info:
                    results.append(company_info)

            if member_info.name:
                github_info = await self.get_github_info(member_info.name)
                if github_info:
                    results.append(github_info)

        except Exception as e:
            log["error"]("Research Error", e)
        finally:
            return results

    async def get_company_info(self, domain):
        try:
            company_url = f"https://www.{domain}"
            res = httpx.get(
                company_url, timeout=5000, headers={"User-Agent": "Mozilla/5.0"}
            )

            title_match = re.search(r"<title>(.*?)</title>", res.text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else f"Company name: {domain}"

            return UserResearchData(
                url=company_url,
                title=title,
                content=f"Company website for {domain}",
                type=UserResearchDataType.COMPANY
            )
        
        except Exception as e:
            log["debug"](f"Could not fetch {domain}", e)
            return None

    async def get_github_info(self, name):
        try:
            url = f"https://api.github.com/search/users?q={name}"
            res = httpx.get(
                url, timeout=5000, headers={"User-Agent": "Mozilla/5.0"}
            )

            data = res.json()

            if data and len(data) > 0:
                user = data[0]

                return UserResearchData(
                    url=user.html_url,
                    title=f"Github: {user.login}",
                    content=f"{user.public_repos} public repositories",
                    type=UserResearchDataType.GITHUB
                )
        except Exception as e:
            log["debug"](f"Could not fetch github for {name}", e)
            return None

    async def analyze_with_ai(
        self, member_info: UserInfo, research_data: list[UserResearchData]
    ):
        pass

    async def save_member_analysis(
        self,
        member_info: UserInfo,
        analysis: UserAnalysis,
        research_data: list[UserResearchData],
    ):
        pass

    async def post_analysis_to_channel(
        self,
        member_info: UserInfo,
        analysis: UserAnalysis,
        research_data: list[UserResearchData],
    ):
        pass

    async def mark_sent_to_slack(self, analysis_id: str):
        pass


slack = SlackAgent()

app = slack.app


@app.on_event("startup")
async def startup():
    asyncio.create_task(asyncio.to_thread(slack.slack_handler.connect))
