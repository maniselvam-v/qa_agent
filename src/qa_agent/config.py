import os
from dotenv import load_dotenv
load_dotenv()

if "AWS_REGION" in os.environ and "AWS_DEFAULT_REGION" not in os.environ:
    os.environ["AWS_DEFAULT_REGION"] = os.environ["AWS_REGION"]

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    app_name: str = "QA Agent APIs"
    environment: str = "development"

    # ── Databricks ────────────────────────────────────
    databricks_host: str = ""
    databricks_server_hostname: str = ""
    databricks_http_path: str = ""
    databricks_token: str = ""
    databricks_catalog: str = "hive_metastore"
    databricks_schema: str = "default"

    # ── Postgres ──────────────────────────────────────
    database_username: str = "postgres"
    database_password: str = ""
    database_hostname: str = ""
    database_port: int = 5432
    database_name: str = ""
    database_url: str = ""

    @property
    def resolved_database_url(self) -> str:
        """
        Use DATABASE_URL if explicitly set,
        otherwise build it from individual parts.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.database_username}:"
            f"{self.database_password}@{self.database_hostname}:"
            f"{self.database_port}/{self.database_name}"
        )

    # ── AWS Bedrock ───────────────────────────────────
    aws_region: str = "us-west-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_llm_model: str = "bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_llm_model_prod: str = "bedrock:global.anthropic.claude-sonnet-4-6"
    agent_timeout: int = 120

    @field_validator("bedrock_llm_model", "bedrock_llm_model_prod")
    @classmethod
    def prefix_bedrock(cls, v: str) -> str:
        if v and not v.startswith("bedrock:"):
            return f"bedrock:{v}"
        return v

    @property
    def llm_model(self) -> str:
        if self.environment == "production":
            return self.bedrock_llm_model_prod
        return self.bedrock_llm_model

    # ── Integrations ──────────────────────────────────
    slack_webhook_url: str = ""
    jira_api_key: str = ""
    jira_base_url: str = ""
    jira_project_key: str = "QA"
    github_access_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()