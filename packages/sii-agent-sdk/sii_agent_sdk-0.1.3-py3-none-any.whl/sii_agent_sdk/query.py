"""
Copyright 2025 Google LLC
Licensed under the Apache License, Version 2.0

Query API - 主要的查询接口 (参考 claude-agent-sdk-python)
"""

import os
from typing import AsyncIterator, Optional

from ._internal.message_parser import parse_message
from .bridge import BridgeProcess
from .errors import AuthenticationError, SiiSDKError, ToolNotAllowedError
from .types import Message, SiiAgentOptions


async def query(
    prompt: str,
    *,
    options: Optional[SiiAgentOptions] = None,
) -> AsyncIterator[Message]:
    """
    执行单次查询，返回异步消息迭代器
    
    参考 claude-agent-sdk-python 的 query() 函数设计，
    提供相似的 API 体验但集成 SII 特色功能。
    
    Args:
        prompt: 用户提示词
        options: 可选配置
    
    Yields:
        Message: 类型化的消息对象
    
    Raises:
        BridgeNotFoundError: 未找到 SII Bridge
        BridgeConnectionError: Bridge 连接失败
        AuthenticationError: 认证失败
        SiiSDKError: 其他错误
    
    Example:
        >>> import anyio
        >>> from sii_agent_sdk import query, SiiAgentOptions
        >>> 
        >>> async def main():
        ...     async for msg in query(
        ...         prompt="列出当前目录文件",
        ...         options=SiiAgentOptions(yolo=True, max_turns=5)
        ...     ):
        ...         print(msg)
        >>> 
        >>> anyio.run(main)
    """
    opts = options or SiiAgentOptions()
    bridge = BridgeProcess(opts)

    # 设置环境变量标识
    os.environ["SII_SDK_ENTRYPOINT"] = "python-sdk"

    try:
        # 1. 启动 Bridge 进程
        await bridge.start()

        # 2. 发送查询请求
        await bridge.send_request(
            "query",
            {
                "prompt": prompt,
                "options": opts.to_dict(),
            },
        )

        # 3. 接收事件流并解析为消息
        async for event in bridge.receive_events():
            message = parse_message(event)
            # print("123123123123:", message)
            if message:
                yield message

            # 4. 处理完成和错误事件
            if event.get("type") == "completed":
                break
            elif event.get("type") == "error":
                error_data = event.get("error", {})
                _raise_appropriate_error(error_data)

    finally:
        # 5. 确保资源清理
        await bridge.close()


def _raise_appropriate_error(error_data: dict) -> None:
    """根据错误码抛出相应的异常"""
    code = error_data.get("code", "UNKNOWN_ERROR")
    message = error_data.get("message", "Unknown error")
    details = error_data.get("details", {})

    if code == "AUTH_FAILED":
        auth_type = details.get("auth_type")
        raise AuthenticationError(message, auth_type)
    elif code == "TOOL_NOT_ALLOWED":
        raise ToolNotAllowedError(
            details.get("tool_name", ""),
            details.get("auth_type", ""),
            details.get("required_auth"),
        )
    else:
        raise SiiSDKError(f"{code}: {message}") 