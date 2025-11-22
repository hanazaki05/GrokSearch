import httpx
import json
from typing import List
from .base import BaseSearchProvider, SearchResult
from ..utils import search_prompt
from ..logger import log_info


class GrokSearchProvider(BaseSearchProvider):
    def __init__(self, api_url: str, api_key: str, model: str = "grok-4-fast"):
        super().__init__(api_url, api_key)
        self.model = model

    def get_provider_name(self) -> str:
        return "Grok"

    async def search(self, query: str, ctx=None) -> List[SearchResult]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": search_prompt,
                },
                {"role": "user", "content": query},
            ],
            "stream": True,
        }

        timeout = httpx.Timeout(connect=6.0, read=50.0, write=10.0, pool=None)
        
        await log_info(ctx, f"连接 Grok API: {self.api_url}")
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream(
                "POST",
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                await log_info(ctx, "正在接收流式响应...")
                content = await self._parse_streaming_response(response, ctx)

        return content

    async def _parse_streaming_response(self, response, ctx=None) -> str:
        content = ""
        chunk_count = 0
        
        async for line in response.aiter_lines():
            line = line.strip()
            # await log_info(ctx, f"收到数据: {content}")
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        content += delta["content"]
                        chunk_count += 1
                        if chunk_count % 10 == 0:
                            preview = content[-100:] if len(content) > 100 else content
                            # await log_info(ctx, f"收到数据: {content}")
                            await log_info(ctx, f"已接收 {chunk_count} 个数据块，当前内容: ...{preview}")
                except json.JSONDecodeError:
                    continue
        
        # await log_info(ctx, f"流式传输完成，共接收 {chunk_count} 个数据块\n")
        # await log_info(ctx, f"内容: {content}")
        
        return content
