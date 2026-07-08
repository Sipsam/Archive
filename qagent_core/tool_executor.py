"""Shared execution policy for every Agent tool call."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Mapping, MutableMapping

from .deadline import ExecutionDeadline
from .runtime import input_summary, output_summary, safe_error_message, safe_for_log


class ToolExecutor:
    """Execute tools with one limit, timeout, error, and trace policy."""

    def __init__(
        self,
        *,
        tool_functions: Mapping[str, Callable[..., Any]],
        trace: list[dict[str, Any]],
        run_id: str,
        runtime_state: MutableMapping[str, int],
        started_at: float,
        max_tool_calls: int,
        timeout_seconds: float,
        result_summarizer: Callable[[str, dict[str, Any]], str] | None = None,
    ) -> None:
        self.tool_functions = tool_functions
        self.trace = trace
        self.run_id = run_id
        self.runtime_state = runtime_state
        self.runtime_state.setdefault("tool_calls", 0)
        self.started_at = started_at
        self.max_tool_calls = max(int(max_tool_calls), 0)
        self.timeout_seconds = max(float(timeout_seconds), 0.0)
        self.deadline = ExecutionDeadline.from_start(self.started_at, self.timeout_seconds)
        self.result_summarizer = result_summarizer

    def is_timed_out(self) -> bool:
        return self.deadline.expired()

    def remaining_seconds(self) -> float:
        return self.deadline.remaining_seconds()

    def remaining_deadline_ms(self) -> float:
        return self.deadline.remaining_ms()

    def execute_raw(
        self,
        tool_name: str,
        raw_arguments: str | None,
        *,
        turn: int,
        forced_by_app: bool = False,
    ) -> dict[str, Any]:
        try:
            arguments = json.loads(raw_arguments or "{}")
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a JSON object")
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            return self._record_failure(
                tool_name,
                {},
                turn=turn,
                error_type="json_parse_error",
                message=safe_error_message("json", error),
                forced_by_app=forced_by_app,
            )
        return self.execute(
            tool_name,
            arguments,
            turn=turn,
            forced_by_app=forced_by_app,
        )

    def execute(
        self,
        tool_name: str,
        arguments: Mapping[str, Any] | None,
        *,
        turn: int,
        forced_by_app: bool = False,
    ) -> dict[str, Any]:
        args = dict(arguments or {})
        if self.is_timed_out():
            return self._record_timeout(
                tool_name, args, turn=turn, elapsed_ms=0.0,
                task_started=False, cancelled=False,
                forced_by_app=forced_by_app,
            )
        if self.runtime_state["tool_calls"] >= self.max_tool_calls:
            return self._record_failure(
                tool_name, args, turn=turn, error_type="tool_call_limit",
                message=safe_error_message("limit"), forced_by_app=forced_by_app,
            )
        if tool_name not in self.tool_functions:
            return self._record_failure(
                tool_name, args, turn=turn, error_type="unknown_tool",
                message=f"Unknown tool: {tool_name}", forced_by_app=forced_by_app,
            )

        step = self._new_trace_step(tool_name, args, turn, forced_by_app)
        self.trace.append(step)
        tool_started = time.monotonic()
        self.runtime_state["tool_calls"] += 1
        step["executed"] = True
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qagent-tool")
        future = executor.submit(self.tool_functions[tool_name], **args)
        try:
            raw_result = future.result(timeout=self.remaining_seconds())
            result = dict(raw_result) if isinstance(raw_result, dict) else {"result": raw_result}
            result.setdefault("status", "ok")
            result.setdefault("warnings", [])
            result.setdefault("assumptions", [])
        except FutureTimeoutError as error:
            # concurrent.futures.TimeoutError aliases builtins.TimeoutError.
            # A Tool may itself raise that exception, so only an unfinished
            # Future means the caller's deadline actually expired.
            if future.done():
                result = {
                    "status": "error",
                    "message": safe_error_message("tool", error),
                    "error_type": type(error).__name__,
                }
            else:
                elapsed_ms = round((time.monotonic() - tool_started) * 1000, 2)
                cancelled = future.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                return self._finish_timeout_step(
                    step, tool_name, elapsed_ms=elapsed_ms, cancelled=cancelled,
                )
        except Exception as error:
            result = {
                "status": "error",
                "message": safe_error_message("tool", error),
                "error_type": type(error).__name__,
            }
        finally:
            if future.done():
                executor.shutdown(wait=False, cancel_futures=True)

        elapsed_ms = round((time.monotonic() - tool_started) * 1000, 2)
        result["elapsed_ms"] = elapsed_ms
        result["remaining_deadline_ms"] = self.remaining_deadline_ms()
        self._finish_trace_step(step, tool_name, result, elapsed_ms)
        return result

    def _timeout_result(
        self, *, elapsed_ms: float, task_started: bool, cancelled: bool,
    ) -> dict[str, Any]:
        may_complete_later = task_started and not cancelled
        message = safe_error_message("timeout")
        if may_complete_later:
            message += " 제한 시간 초과가 보고되었으며, 실행 중인 작업은 나중에 완료될 수 있습니다."
        return {
            "status": "timeout",
            "error_type": "timeout",
            "message": message,
            "user_safe_message": message,
            "cancelled": cancelled,
            "cancellation_possible": cancelled,
            "cancellation_attempted": task_started,
            "cancellation_succeeded": cancelled,
            "underlying_task_may_complete_later": may_complete_later,
            "elapsed_ms": elapsed_ms,
            "remaining_deadline_ms": self.remaining_deadline_ms(),
        }

    def _record_timeout(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        turn: int,
        elapsed_ms: float,
        task_started: bool,
        cancelled: bool,
        forced_by_app: bool,
    ) -> dict[str, Any]:
        step = self._new_trace_step(tool_name, arguments, turn, forced_by_app)
        result = self._timeout_result(
            elapsed_ms=elapsed_ms, task_started=task_started, cancelled=cancelled,
        )
        self.trace.append(step)
        self._finish_trace_step(step, tool_name, result, elapsed_ms)
        return result

    def _finish_timeout_step(
        self,
        step: dict[str, Any],
        tool_name: str,
        *,
        elapsed_ms: float,
        cancelled: bool,
    ) -> dict[str, Any]:
        result = self._timeout_result(
            elapsed_ms=elapsed_ms, task_started=True, cancelled=cancelled,
        )
        self._finish_trace_step(step, tool_name, result, elapsed_ms)
        return result

    def _record_failure(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        turn: int,
        error_type: str,
        message: str,
        forced_by_app: bool,
    ) -> dict[str, Any]:
        step = self._new_trace_step(tool_name, arguments, turn, forced_by_app)
        result = {
            "status": "error",
            "message": message,
            "error_type": error_type,
            "elapsed_ms": 0.0,
        }
        self.trace.append(step)
        self._finish_trace_step(step, tool_name, result, 0.0)
        return result

    def _new_trace_step(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        turn: int,
        forced_by_app: bool,
    ) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "turn": turn,
            "tool": tool_name,
            "tool_name": tool_name,
            "arguments": safe_for_log(dict(arguments)),
            "input_summary": input_summary(dict(arguments)),
            "result": None,
            "output_summary": "",
            "result_summary": "",
            "duration_ms": 0.0,
            "elapsed_ms": 0.0,
            "success": False,
            "executed": False,
            "error_message": "",
            "summary": "",
            "finished": False,
            "forced_by_app": forced_by_app,
        }

    def _finish_trace_step(
        self,
        step: dict[str, Any],
        tool_name: str,
        result: dict[str, Any],
        elapsed_ms: float,
    ) -> None:
        result_summary = output_summary(result)
        step.update({
            "result": safe_for_log(result),
            "output_summary": result_summary,
            "result_summary": result_summary,
            "duration_ms": elapsed_ms,
            "elapsed_ms": elapsed_ms,
            "status": result.get("status", "unknown"),
            "cancelled": bool(result.get("cancelled", False)),
            "cancellation_possible": bool(result.get("cancellation_possible", False)),
            "cancellation_attempted": bool(result.get("cancellation_attempted", False)),
            "cancellation_succeeded": bool(result.get("cancellation_succeeded", False)),
            "remaining_deadline_ms": result.get("remaining_deadline_ms", self.remaining_deadline_ms()),
            "user_safe_message": str(result.get("user_safe_message", result.get("message", ""))),
            "success": result.get("status") == "ok",
            "error_message": str(result.get("message", "")) if result.get("status") in {"error", "timeout"} else "",
            "summary": (
                self.result_summarizer(tool_name, result)
                if self.result_summarizer is not None
                else result_summary
            ),
            "finished": True,
        })
