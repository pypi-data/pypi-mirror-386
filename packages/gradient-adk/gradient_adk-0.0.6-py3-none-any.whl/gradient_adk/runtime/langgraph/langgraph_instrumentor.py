from __future__ import annotations

import functools
import inspect
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence, Tuple, Dict

from langgraph.graph import StateGraph

from ..interfaces import NodeExecution
from ..digitalocean_tracker import DigitalOceanTracesTracker
from ..network_interceptor import get_network_interceptor


WRAPPED_FLAG = "__do_wrapped__"


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _mk_exec(name: str, inputs: Any) -> NodeExecution:
    return NodeExecution(
        node_id=str(uuid.uuid4()),
        node_name=name,
        framework="langgraph",
        start_time=_utc(),
        inputs=inputs,
    )


def _ensure_meta(rec: NodeExecution) -> dict:
    md = getattr(rec, "metadata", None)
    if not isinstance(md, dict):
        md = {}
        try:
            rec.metadata = md
        except Exception:
            pass
    return md


_MAX_DEPTH = 3
_MAX_ITEMS = 100  # keep payloads bounded


def _freeze(obj: Any, depth: int = _MAX_DEPTH) -> Any:
    """Mutation-safe, JSON-ish snapshot for arbitrary Python objects."""
    # if depth < 0:
    #     return "<max-depth>"
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # dict-like
    if isinstance(obj, Mapping):
        out: Dict[str, Any] = {}
        for i, (k, v) in enumerate(obj.items()):
            if i >= _MAX_ITEMS:
                out["<truncated>"] = True
                break
            out[str(k)] = _freeze(v, depth - 1)
        return out

    # sequences
    if isinstance(obj, (list, tuple, set)):
        seq = list(obj)
        out = []
        for i, v in enumerate(seq):
            if i >= _MAX_ITEMS:
                out.append("<truncated>")
                break
            out.append(_freeze(v, depth - 1))
        return out

    # pydantic
    try:
        from pydantic import BaseModel  # type: ignore

        if isinstance(obj, BaseModel):
            return _freeze(obj.model_dump(), depth - 1)
    except Exception:
        pass

    # dataclass
    try:
        import dataclasses

        if dataclasses.is_dataclass(obj):
            return _freeze(dataclasses.asdict(obj), depth - 1)
    except Exception:
        pass

    # fallback
    return repr(obj)


def _snapshot_args_kwargs(a: Tuple[Any, ...], kw: Dict[str, Any]) -> dict:
    """Deepcopy then freeze to avoid mutation surprises."""
    try:
        a_copy = deepcopy(a)
        kw_copy = deepcopy(kw)
    except Exception:
        a_copy, kw_copy = a, kw  # best-effort
    return {"args": _freeze(a_copy), "kwargs": _freeze(kw_copy)}


def _diff(a: Any, b: Any, depth: int = 2) -> Any:
    """Small, generic diff for dicts/lists/tuples; returns None if identical."""
    # if depth < 0:
    #     return "<max-depth>"

    # dict diff
    if isinstance(a, dict) and isinstance(b, dict):
        keys = list(set(a.keys()) | set(b.keys()))
        keys.sort(key=str)
        out: Dict[str, Any] = {}
        count = 0
        for k in keys:
            if count >= _MAX_ITEMS:
                out["<truncated_keys>"] = True
                break
            av = a.get(k, "<missing>")
            bv = b.get(k, "<missing>")
            if av == bv:
                continue
            if isinstance(av, (dict, list, tuple)) and isinstance(
                bv, (dict, list, tuple)
            ):
                sub = _diff(av, bv, depth - 1)
                out[k] = sub if sub is not None else {"before": av, "after": bv}
            else:
                out[k] = {"before": av, "after": bv}
            count += 1
        return out or None

    # list/tuple diff
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        length = max(len(a), len(b))
        changed = False
        out_list = []
        for i in range(min(length, _MAX_ITEMS)):
            av = a[i] if i < len(a) else "<missing>"
            bv = b[i] if i < len(b) else "<missing>"
            if av == bv:
                out_list.append("<same>")
            else:
                if isinstance(av, (dict, list, tuple)) and isinstance(
                    bv, (dict, list, tuple)
                ):
                    sub = _diff(av, bv, depth - 1)
                    out_list.append(
                        sub if sub is not None else {"before": av, "after": bv}
                    )
                else:
                    out_list.append({"before": av, "after": bv})
                changed = True
        if length > _MAX_ITEMS:
            out_list.append("<truncated>")
        return out_list if changed else None

    return None if a == b else {"before": a, "after": b}


def _first_arg_after(a: Tuple[Any, ...]) -> Optional[Any]:
    return a[0] if (a and isinstance(a[0], dict)) else None


def _first_arg_before(before_inputs: dict) -> Optional[Any]:
    try:
        args = before_inputs.get("args")
        if isinstance(args, list) and args:
            return args[0]
    except Exception:
        pass
    return None


def _canonical_output(
    before_inputs: dict, a: Tuple[Any, ...], kw: Dict[str, Any], ret: Any
) -> dict:
    """
    Choose a single, compact output dict:
      1) If ret is a mapping -> return snapshot(ret)
      2) Else if first arg is a dict and appears changed -> snapshot(first arg)
      3) Else -> {"return": snapshot(ret)}
    Always returns a dict (keeps Pydantic 'output must be dict' happy).
    """
    if isinstance(ret, Mapping):
        return _freeze(ret)

    arg0_before = _first_arg_before(before_inputs)
    arg0_after = _first_arg_after(a)
    if isinstance(arg0_after, dict):
        arg0_after_frozen = _freeze(arg0_after)
        if not isinstance(arg0_before, dict) or arg0_before != arg0_after_frozen:
            return arg0_after_frozen

    return {"return": _freeze(ret)}


def _snap():
    intr = get_network_interceptor()
    try:
        tok = intr.snapshot_token()
    except Exception:
        tok = 0
    return intr, tok


def _had_hits_since(intr, token) -> bool:
    try:
        return intr.hits_since(token) > 0
    except Exception:
        return False


class LangGraphInstrumentor:
    """Wraps LangGraph nodes with tracing."""

    def __init__(self) -> None:
        self._installed = False
        self._tracker: Optional[DigitalOceanTracesTracker] = None

    def install(self, tracker: DigitalOceanTracesTracker) -> None:
        if self._installed:
            return
        self._tracker = tracker

        original_add_node = StateGraph.add_node
        t = tracker  # close over

        def _start(node_name: str, a: Tuple[Any, ...], kw: Dict[str, Any]):
            inputs_snapshot = _snapshot_args_kwargs(a, kw)
            rec = _mk_exec(node_name, inputs_snapshot)
            intr, tok = _snap()
            t.on_node_start(rec)
            return rec, inputs_snapshot, intr, tok

        def _finish_ok(
            rec: NodeExecution,
            inputs_snapshot: dict,
            a: Tuple[Any, ...],
            kw: Dict[str, Any],
            ret: Any,
            intr,
            tok,
        ):
            out_payload = _canonical_output(inputs_snapshot, a, kw, ret)
            if _had_hits_since(intr, tok):
                _ensure_meta(rec)["is_llm_call"] = True
            t.on_node_end(rec, out_payload)

        def _finish_err(rec: NodeExecution, intr, tok, e: BaseException):
            if _had_hits_since(intr, tok):
                _ensure_meta(rec)["is_llm_call"] = True
            t.on_node_error(rec, e)

        def _wrap_async_func(node_name: str, func):
            @functools.wraps(func)
            async def _wrapped(*a, **kw):
                rec, snap, intr, tok = _start(node_name, a, kw)
                try:
                    ret = await func(*a, **kw)
                    _finish_ok(rec, snap, a, kw, ret, intr, tok)
                    return ret
                except BaseException as e:
                    _finish_err(rec, intr, tok, e)
                    raise

            setattr(_wrapped, WRAPPED_FLAG, True)
            return _wrapped

        def _wrap_sync_func(node_name: str, func):
            @functools.wraps(func)
            def _wrapped(*a, **kw):
                rec, snap, intr, tok = _start(node_name, a, kw)
                try:
                    ret = func(*a, **kw)
                    _finish_ok(rec, snap, a, kw, ret, intr, tok)
                    return ret
                except BaseException as e:
                    _finish_err(rec, intr, tok, e)
                    raise

            setattr(_wrapped, WRAPPED_FLAG, True)
            return _wrapped

        def _wrap_async_gen(node_name: str, func):
            @functools.wraps(func)
            async def _wrapped(*a, **kw):
                rec, snap, intr, tok = _start(node_name, a, kw)
                try:
                    # Accumulate a compact, canonical final payload
                    # (string: concatenate; list: extend; else: last write wins)
                    acc: Dict[str, Any] = {}

                    async for chunk in func(*a, **kw):
                        # Merge into acc for the final on_node_end payload
                        for k, v in chunk.items():
                            if isinstance(v, str):
                                acc[k] = acc.get(k, "") + v
                            elif isinstance(v, bytes):
                                acc[k] = acc.get(k, b"") + v
                            elif isinstance(v, list):
                                acc.setdefault(k, []).extend(v)
                            else:
                                acc[k] = v

                        # Pass the live chunk downstream unchanged
                        yield chunk

                    # Finish the span with the aggregated mapping
                    _finish_ok(rec, snap, a, kw, acc, intr, tok)
                except BaseException as e:
                    _finish_err(rec, intr, tok, e)
                    raise

            setattr(_wrapped, WRAPPED_FLAG, True)
            return _wrapped

        def _wrap_runnable_ainvoke(node_name: str, runnable):
            async def _wrapped(*a, **kw):
                rec, snap, intr, tok = _start(node_name, a, kw)
                try:
                    ret = await runnable.ainvoke(*a, **kw)
                    _finish_ok(rec, snap, a, kw, ret, intr, tok)
                    return ret
                except BaseException as e:
                    _finish_err(rec, intr, tok, e)
                    raise

            setattr(_wrapped, WRAPPED_FLAG, True)
            return _wrapped

        def _wrap_runnable_invoke(node_name: str, runnable):
            def _wrapped(*a, **kw):
                rec, snap, intr, tok = _start(node_name, a, kw)
                try:
                    ret = runnable.invoke(*a, **kw)
                    _finish_ok(rec, snap, a, kw, ret, intr, tok)
                    return ret
                except BaseException as e:
                    _finish_err(rec, intr, tok, e)
                    raise

            setattr(_wrapped, WRAPPED_FLAG, True)
            return _wrapped

        def wrap_callable(node_name: str, func: Any):
            if getattr(func, WRAPPED_FLAG, False):
                return func

            # Runnable-like objects
            if hasattr(func, "ainvoke"):
                return _wrap_runnable_ainvoke(node_name, func)
            if hasattr(func, "invoke"):
                return _wrap_runnable_invoke(node_name, func)

            # Functions
            if inspect.isasyncgenfunction(func):
                return _wrap_async_gen(node_name, func)
            if inspect.iscoroutinefunction(func):
                return _wrap_async_func(node_name, func)
            if inspect.isfunction(func):
                return _wrap_sync_func(node_name, func)

            # Unknown type -> leave untouched
            return func

        def wrapped_add_node(graph_self, name, func, *args, **kwargs):
            return original_add_node(
                graph_self, name, wrap_callable(name, func), *args, **kwargs
            )

        StateGraph.add_node = wrapped_add_node
        self._installed = True
