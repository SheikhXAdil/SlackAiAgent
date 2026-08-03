import asyncpg
import os
import json
from logger import log
from models import UserInfo, UserAnalysis, UserResearchData

pool = None


async def connect_database():
    global pool

    pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL"),
        max_size=20,
        max_inactive_connection_lifetime=30,
        timeout=10,
    )

    log["info"]("Database connected")


async def init_database():
    con = await pool.acquire()
    try:
        await con.execute("""
            CREATE TABLE IF NOT EXISTS member_analyses (
                id SERIAL PRIMARY KEY,
                member_id VARCHAR(255),
                member_name VARCHAR(255) NOT NULL,
                member_email VARCHAR(255),
                member_title VARCHAR(255),
                member_timezone VARCHAR(100),
                fit_score INTEGER NOT NULL,
                insights JSONB,
                recommendations JSONB,
                research_data JSONB,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_to_slack BOOLEAN DEFAULT FALSE,
                sent_to_slack_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await con.execute("""
            CREATE INDEX IF NOT EXISTS idx_member_id ON member_analyses(member_id);
        """)

        await con.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyzed_at ON member_analyses(analyzed_at);
        """)

        log["info"]("Database Schema Initialized successfully")
    except Exception as e:
        log["error"]("Database Initialization error", e)
    finally:
        await pool.release(con)


async def save_member_analysis(
    member_info: UserInfo,
    analysis: UserAnalysis,
    research_data: list[UserResearchData],
):
    con = await pool.acquire()
    try:
        analysis = await con.fetchrow(
            """INSERT INTO member_analyses (
                member_id, 
                member_name, 
                member_email, 
                member_title, 
                member_timezone,
                fit_score, 
                insights, 
                recommendations, 
                research_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id""",
            member_info.id,
            member_info.name if member_info.name else "Not provided",
            member_info.email,
            member_info.title,
            member_info.timezone,
            analysis.fit_score,
            json.dumps(analysis.insights),
            json.dumps(analysis.recommendations),
            json.dumps([item.model_dump(mode="json") for item in research_data]),
        )

        return analysis["id"]
    except Exception as e:
        log["error"]("Failed to save analysis to database", e)
    finally:
        await pool.release(con)


async def mark_sent_to_slack(
    analysis_id: int,
):
    con = await pool.acquire()
    try:
        await con.execute(
            """UPDATE member_analyses
            SET sent_to_slack = TRUE,
                sent_to_slack_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1""",
            analysis_id,
        )
    except Exception as e:
        log["error"](f"Failed to mark analysis with id {analysis_id} as sent to database", e)
    finally:
        await pool.release(con)


async def close_database():
    await pool.close()
    log["info"]("Database connection pool closed")
