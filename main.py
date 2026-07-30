from fastapi import FastAPI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import httpx
import os
import logging

load_dotenv()

environment = os.getenv("ENVIRONMENT", "development")

logging.basicConfig(level=logging.INFO)

log = {
    "info": lambda msg, *args: logging.info(f'[INFO] {msg}', *args),
    "error": lambda msg, *args: logging.error(f'[ERROR] {msg}', *args),
    "debug": lambda msg, *args: logging.debug(f'[DEBUG] {msg}', *args) if environment == "development" else None,
}


client = WebClient()

class SlackAgent:
    def __init__(self):
        self.app = FastAPI()

        self.slack = App(token=os.environ.get("SLACK_BOT_TOKEN"), 
                         signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
                         )
        handler = SocketModeHandler(
        self.slack,
        os.environ["SLACK_APP_TOKEN"]
        )
        handler.start()

        self.webClient = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ.ge("GOOGLE_API_KEY"),
            temperature=0.3,
            max_output_tokens=2048,
        )

        self.setup_fast_api()
        self.setup_slack_events()

    def setup_slack_events(self):
        @self.slack.event("team_join")
        def handle_team_join(event):
                try:
                    log.info(f"event: {event}")

                    user = event["user"]
                    name = user.get("real_name") or user.get("name")

                    log.info(f"New member joined: {name}")

                except Exception as e:
                     log.error("Error calling team_join", e)


    def setup_fast_api(self):
        pass