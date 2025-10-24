from __future__ import annotations
import inspect
from typing import Callable, Optional, Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
import uvicorn

from .logging import get_logger
from .streaming import StreamingResponse as GradientStreamingResponse

logger = get_logger(__name__)

from gradient_adk.runtime.langgraph.helpers import capture_graph, get_tracker

capture_graph()


def entrypoint(func: Callable) -> Callable:
    """
    Decorator that creates a FastAPI app and exposes it as `app` in the caller module.
    The decorated function must accept exactly (data, context).
    """
    sig = inspect.signature(func)
    if len(sig.parameters) != 2:
        raise ValueError(f"{func.__name__} must accept exactly (data, context)")

    app = FastAPI(title=f"Gradient Agent - {func.__name__}", version="1.0.0")

    @app.on_event("shutdown")
    async def _shutdown():
        # Flush pending trace submissions if a tracker exists
        try:
            tr = get_tracker()
            if tr and hasattr(tr, "aclose"):
                await tr.aclose()
        except Exception:
            pass

    @app.post("/run")
    async def run(req: Request):
        # Parse JSON
        try:
            body = await req.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

        # Start request in tracker (if available)
        tr = None
        try:
            tr = get_tracker()
            if tr:
                tr.on_request_start(func.__name__, body)
        except Exception:
            pass

        # Call user function (context optional; pass None)
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(body, None)
            else:
                result = func(body, None)
        except Exception as e:
            try:
                if tr:
                    tr.on_request_end(outputs=None, error=str(e))
            except Exception:
                pass
            logger.error("Error in /run", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

        # Streaming responses
        if isinstance(result, GradientStreamingResponse):

            async def _wrap(gen):
                try:
                    async for chunk in gen:
                        yield chunk
                    if tr:
                        try:
                            tr.on_request_end(outputs=None, error=None)
                        except Exception:
                            pass
                except Exception as e:
                    if tr:
                        try:
                            tr.on_request_end(outputs=None, error=str(e))
                        except Exception:
                            pass
                    raise

            return FastAPIStreamingResponse(
                _wrap(result.content),
                media_type=result.media_type,
                headers=result.headers,
            )

        # Non-streaming
        if tr:
            try:
                tr.on_request_end(outputs=result, error=None)
            except Exception:
                pass
        return result

    @app.get("/health")
    async def health():
        return {"status": "healthy", "entrypoint": func.__name__}

    # Expose app in caller’s module for `uvicorn main:app`
    import sys

    sys._getframe(1).f_globals["app"] = app
    return func


def run_server(app: FastAPI, host: str = "0.0.0.0", port: int = 8080, **kwargs):
    uvicorn.run(app, host=host, port=port, **kwargs)
