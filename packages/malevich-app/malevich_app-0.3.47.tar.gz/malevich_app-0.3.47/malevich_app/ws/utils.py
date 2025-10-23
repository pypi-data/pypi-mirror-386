import json
import asyncio
from typing import Callable
from pydantic import BaseModel
from pydantic.v1.json import pydantic_encoder
from malevich_app.export.abstract.abstract import WSMessage
import malevich_app.export.secondary.const as C


_ws_send_lock = asyncio.Lock()
_chunk_size: int = 1024 * 512

async def ws_send(data: str):
    async with _ws_send_lock:
        sz = len(data)
        for i in range(0, sz, _chunk_size):
            chunk = data[i:i + _chunk_size]
            if i + _chunk_size < sz:
                chunk = chunk.encode("utf-8")   # intermediate - bytes
            await C.WS.send(chunk)


async def ws_call(f: Callable, msg: WSMessage):
    try:
        res, response = await f(msg.payload)
    except BaseException as ex:
        res_msg = WSMessage(
            operationId=msg.operationId,
            error=str(ex),
            operation=msg.operation,
            id=msg.id,
        )
    else:
        if response is None:
            ok = True   # only ping
        else:
            ok = response.status_code < 300

        if msg.operation == "stream":
            if ok:
                async for chunk in res.body_iterator:
                    intermediate_msg = WSMessage(
                        operationId=msg.operationId,
                        payload=chunk,
                        operation=msg.operation,
                        id=msg.id,
                    )
                    await ws_send(intermediate_msg.model_dump_json())
                    C.WS_SEND.append(intermediate_msg)
            payload = None
        else:
            payload = res
            if isinstance(payload, dict):
                payload = json.dumps(payload, default=pydantic_encoder)
            elif isinstance(payload, BaseModel):
                payload = payload.model_dump_json()

        res_msg = WSMessage(
            operationId=msg.operationId,
            payload=payload,
            error=None if ok else f"response code={response.status_code}",
            operation=msg.operation,
            id=msg.id,
        )
    await ws_send(res_msg.model_dump_json())
    C.WS_SEND.append(res_msg)
