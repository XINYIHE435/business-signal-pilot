"""
SignalPilot 配置管理

使用 pydantic-settings 管理环境变量
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    app_name: str = "SignalPilot API"
    app_version: str = "1.0.0"
    debug: bool = False

    # AI 配置
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm: str = "claude"  # claude or openai

    # 数据库配置
    database_path: str = "../data/signal.db"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # 日志配置
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
