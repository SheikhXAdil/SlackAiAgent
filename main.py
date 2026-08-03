import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime
import httpx
import re
import json

from fastapi import FastAPI, HTTPException, Request

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk import WebClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from logger import log
from models import *
import db

load_dotenv()

environment = os.getenv("ENVIRONMENT", "development")

client = WebClient()


class SlackAgent:
    def __init__(self):
        self.app = FastAPI(lifespan=self.lifespan)

        self.slack = AsyncApp(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )
        self.slack_handler = None
        self.webClient = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.3,
            max_output_tokens=2048,
        )

        self.database_conn = None

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

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.start_server()
        yield
        await self.stop_server()

    async def start_server(self):
        try:
            log["info"]("🗄️ Initializing database...")
            await db.connect_database()
            await db.init_database()

            self.slack_handler = AsyncSocketModeHandler(
                self.slack, os.environ["SLACK_APP_TOKEN"]
            )

            await slack.slack_handler.connect_async()
            log["info"]("⚡️ Slack bot connected")
            log["info"]("🎉 Slack AI Agent is running!")
        except Exception as e:
            log["error"]("Start up error", e)
            raise

    async def stop_server(self):
        try:
            slack.slack_handler.close()
            await db.close_database()
            log["info"]("Stopped successfully")
        except Exception as e:
            log["error"]("Shutdown error", e)
            raise

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

            research_data = await self.do_basic_research(member_info)

            analysis = await self.analyze_with_ai(member_info, research_data)

            log["info"](
                f"Saving analysis on info of member {member_info.name} to database"
            )

            analysis_id = await self.save_member_analysis(
                member_info, analysis, research_data
            )

            await self.post_analysis_to_channel(member_info, analysis)

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

    async def do_basic_research(self, member_info: UserInfo) -> list[UserResearchData]:
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

    def is_personal_email(self, email: str) -> bool:
        personalDomains: list[str] = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "icloud.com",
        ]
        domain = email.split("@")[1].lower() if email.split("@")[1] else None
        return personalDomains.count(domain) > 0

    async def get_company_info(self, domain) -> UserResearchData:

        try:
            company_url = f"https://www.{domain}"
            res = httpx.get(
                company_url, timeout=5000, headers={"User-Agent": "Mozilla/5.0"}
            )

            title_match = re.search(
                r"<title>(.*?)</title>", res.text, re.IGNORECASE | re.DOTALL
            )
            title = (
                title_match.group(1).strip()
                if title_match
                else f"Company name: {domain}"
            )

            return UserResearchData(
                url=company_url,
                title=title,
                content=f"Company website for {domain}",
                type=UserResearchDataType.COMPANY,
            )

        except Exception as e:
            log["debug"](f"Could not fetch {domain}", e)
            return None

    async def get_github_info(self, name) -> UserResearchData:
        try:
            url = f"https://api.github.com/search/users?q={name}"
            res = httpx.get(url, timeout=5000, headers={"User-Agent": "Mozilla/5.0"})

            data = res.json()

            if data["items"] and len(data["items"]) > 0:
                user = data["items"][0]

                return UserResearchData(
                    url=user["html_url"],
                    title=f"Github: {user["login"]}",
                    content=f"repos url: {user["repos_url"]}",
                    type=UserResearchDataType.GITHUB,
                )
        except Exception as e:
            log["debug"](f"Could not fetch github for {name}", e)
            return None

    async def analyze_with_ai(
        self, member_info: UserInfo, research_data: list[UserResearchData]
    ):
        company = os.environ.get("COMPANY_NAME")
        product = os.environ.get("COMPANY_PRODUCT")

        prompt = PromptTemplate.from_template(
            """Analyze this new community member for fit with our commercial 
        product.

        Company: {company}
        Product: {product}

        Member:
        - Name: {name}
        - Email: {email}
        - Title: {title}

        Research Data:
        {research}

        Provide a JSON response with:
        - fit_score (0-100): likelihood they'd be interested in our product
        - insights: array of 3-5 key observations
        - recommendations: array of 2-4 engagement suggestions

        Consider job title, company size, technical background, and budget 
        authority."""
        )

        try:
            if len(research_data) == 0:
                raise

            research_summary = "\n".join(
                list(
                    map(
                        lambda item: f"{item.title}: {item.content}: {item.url}",
                        research_data,
                    )
                )
            )

            chain = prompt.pipe(self.gemini)

            result = await chain.ainvoke(
                {
                    "name": member_info.name,
                    "title": member_info.title or "Not provided",
                    "email": member_info.email or "Not provided",
                    "research": research_summary,
                    "company": company,
                    "product": product,
                }
            )

            res_text: str = result.content[0]["text"]
            cleaned_res = res_text.removeprefix("```json")
            cleaned_res = cleaned_res.removeprefix("```")
            cleaned_res = cleaned_res.removesuffix("```")
            cleaned_res = cleaned_res.strip()
            # log["info"](f"llm result cleaned: {cleaned_res}")

            analysis: UserAnalysis = json.loads(cleaned_res)

            return UserAnalysis(
                fit_score=max(0, min(100, int(analysis["fit_score"] or 50))),
                insights=(
                    analysis["insights"]
                    if isinstance(analysis["insights"], list)
                    else ["Analysis Completed"]
                ),
                recommendations=(
                    analysis["recommendations"]
                    if isinstance(analysis["recommendations"], list)
                    else ["Follow up recommended"]
                ),
            )

        except Exception as e:
            log["error"](f"AI Analysis Error", e)

            return UserAnalysis(
                fit_score=50,
                insights=["unable to complete analysis"],
                recommendations=["Manual review recommended"],
            )

    async def post_analysis_to_channel(
        self,
        member_info: UserInfo,
        analysis: UserAnalysis,
    ):
        color = (
            "#36a64f"
            if analysis.fit_score >= 80
            else (
                "#ffb84d"
                if analysis.fit_score >= 60
                else "#ff9500" if analysis.fit_score >= 40 else "#ff4444"
            )
        )

        blocks: list = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 New Member: {member_info.name}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Fit Score:* {analysis.fit_score}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:* {member_info.email or 'Not provided'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:* {member_info.title or 'Not provided'}",
                    },
                ],
            },
        ]

        if len(analysis.insights) > 0:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f'*Insights:*\n{"\n".join(
                list(
                    map(
                        lambda item: f"{item}",
                        analysis.insights,
                    )
                )
            )}'},
                }
            )

        if len(analysis.recommendations) > 0:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f'*Recommendations:*\n{"\n".join(
                            list(
                                map(
                                    lambda item: f"{item}",
                                    analysis.recommendations,
                                )
                            )
                        )}'},
                }
            )

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 Analyzed: {datetime.now().isoformat()}",
                    }
                ],
            }
        )

        self.webClient.chat_postMessage(
            channel=os.getenv("SLACK_PRIVATE_CHANNEL_ID"),
            text=f"New member analysis: {member_info.name} ({analysis.fit_score}/100)",
            attachments=[{"color": color, "blocks": blocks}],
        )

        log["info"](f"Analysis posted to channel for {member_info.name}")

    async def save_member_analysis(
        self,
        member_info: UserInfo,
        analysis: UserAnalysis,
        research_data: list[UserResearchData],
    ):
        return await db.save_member_analysis(member_info, analysis, research_data)

    async def mark_sent_to_slack(self, analysis_id: int):
        await db.mark_sent_to_slack(analysis_id)


slack = SlackAgent()

app = slack.app
