"""
LLM 客户端封装

支持 Claude 和 OpenAI
"""

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class LLMClient:
    """LLM 客户端管理器"""

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        # 初始化 Claude
        if settings.anthropic_api_key:
            self.claude_client = AsyncAnthropic(
                api_key=settings.anthropic_api_key
            )
            logger.info("claude_client_initialized")

        # 初始化 OpenAI
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(
                api_key=settings.openai_api_key
            )
            logger.info("openai_client_initialized")

    async def generate(
        self,
        prompt: str,
        system: str = None,
        model: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """生成文本（自动选择可用的 LLM）"""

        # 决定使用哪个模型
        use_model = model or settings.default_llm

        if use_model == "claude" and self.claude_client:
            return await self._generate_claude(prompt, system, max_tokens, temperature)
        elif use_model == "openai" and self.openai_client:
            return await self._generate_openai(prompt, system, max_tokens, temperature)
        else:
            raise ValueError(f"LLM {use_model} 不可用，请检查 API key 配置")

    async def _generate_claude(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """使用 Claude 生成"""

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else "You are a helpful AI assistant.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = response.content[0].text
            logger.info("claude_generation_success", prompt_length=len(prompt), response_length=len(result))
            return result

        except Exception as e:
            logger.error("claude_generation_failed", error=str(e))
            raise

    async def _generate_openai(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """使用 OpenAI 生成"""

        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )

            result = response.choices[0].message.content
            logger.info("openai_generation_success", prompt_length=len(prompt), response_length=len(result))
            return result

        except Exception as e:
            logger.error("openai_generation_failed", error=str(e))
            raise


# 全局 LLM 客户端实例
llm_client = LLMClient()
