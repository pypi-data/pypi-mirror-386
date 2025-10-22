"""Argument binding utilities with replay support."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fluxloop.schemas import ExperimentConfig, ReplayArgsConfig


class _AwaitableNone:
    """Simple awaitable that resolves to ``None``."""

    def __await__(self):  # type: ignore[override]
        async def _noop() -> None:
            return None

        return _noop().__await__()


class ArgBinder:
    """Bind call arguments using replay data when configured."""

    def __init__(self, experiment_config: ExperimentConfig) -> None:
        self.config = experiment_config
        self.replay_config: Optional[ReplayArgsConfig] = experiment_config.replay_args
        self._recording: Optional[Dict[str, Any]] = None

        if self.replay_config and self.replay_config.enabled:
            self._load_recording()

    def _load_recording(self) -> None:
        replay = self.replay_config
        assert replay is not None

        if not replay.recording_file:
            raise ValueError("replay_args.recording_file must be provided when replay is enabled")

        file_path = Path(replay.recording_file)
        if not file_path.is_absolute():
            source_dir = self.config.get_source_dir()
            if source_dir:
                file_path = (source_dir / file_path).resolve()
            else:
                file_path = file_path.resolve()

        if not file_path.exists():
            raise FileNotFoundError(
                f"Recording file not found: {file_path}. Make sure it is available locally."
            )

        last_line: Optional[str] = None
        with file_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                if line.strip():
                    last_line = line

        if not last_line:
            raise ValueError(f"Recording file is empty: {file_path}")

        try:
            self._recording = json.loads(last_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in recording file {file_path}: {exc}")

        recording_target = self._recording.get("target")
        config_target = self._resolve_config_target()
        if recording_target and recording_target != config_target:
            print(
                "⚠️  Recording target mismatch:"
                f" recording={recording_target}, config={config_target}. Proceeding anyway."
            )

    def bind_call_args(
        self,
        func: Callable,
        *,
        runtime_input: str,
        iteration: int = 0,
    ) -> Dict[str, Any]:
        """Construct kwargs for calling *func* based on replay or inspection."""

        if self._recording:
            kwargs = self._recording.get("kwargs", {}).copy()

            replay = self.replay_config
            assert replay is not None

            if replay.override_param_path:
                try:
                    self._set_by_path(kwargs, replay.override_param_path, runtime_input)
                except (KeyError, TypeError):
                    # If path missing, fall back to plain binding
                    return self._bind_by_signature(func, runtime_input)

            self._restore_callables(kwargs, replay)
            self._ensure_no_unmapped_callables(kwargs, replay)
            return kwargs

        return self._bind_by_signature(func, runtime_input)

    def _bind_by_signature(self, func: Callable, runtime_input: str) -> Dict[str, Any]:
        signature = inspect.signature(func)
        parameters = list(signature.parameters.values())

        if parameters and parameters[0].name == "self":
            parameters = parameters[1:]

        candidate_names = [
            "input",
            "input_text",
            "message",
            "query",
            "text",
            "content",
        ]

        for param in parameters:
            if param.name in candidate_names:
                return {param.name: runtime_input}

        if parameters:
            return {parameters[0].name: runtime_input}

        raise ValueError(
            f"Cannot determine where to bind runtime input for function '{func.__name__}'."
        )

    def _restore_callables(self, kwargs: Dict[str, Any], replay: ReplayArgsConfig) -> None:
        for param_name, provider in replay.callable_providers.items():
            if param_name not in kwargs:
                continue

            marker = kwargs[param_name]
            if isinstance(marker, str) and marker.startswith("<"):
                kwargs[param_name] = self._resolve_builtin_callable(provider, marker)

    def _ensure_no_unmapped_callables(self, kwargs: Dict[str, Any], replay: ReplayArgsConfig) -> None:
        callable_markers = {
            key: value
            for key, value in kwargs.items()
            if isinstance(value, str) and value.startswith("<")
        }

        if not callable_markers:
            return

        configured = set(replay.callable_providers.keys())
        missing = [key for key in callable_markers if key not in configured]
        if missing:
            raise ValueError(
                "Missing callable providers for recorded parameters: "
                f"{', '.join(missing)}. Configure them under replay_args.callable_providers."
            )

    def _resolve_builtin_callable(self, provider: str, marker: str) -> Callable:
        is_async = marker.endswith(":async>")

        if provider == "builtin:collector.send":
            messages: list = []

            def _record(args: Any, kwargs: Any) -> None:
                messages.append((args, kwargs))
                pretty = args[0] if len(args) == 1 and not kwargs else {"args": args, "kwargs": kwargs}

            def send(*args: Any, **kwargs: Any) -> _AwaitableNone:
                _record(args, kwargs)
                return _AwaitableNone()

            async def send_async(*args: Any, **kwargs: Any) -> None:
                _record(args, kwargs)

            send.messages = messages
            send_async.messages = messages
            send.__fluxloop_builtin__ = "collector.send"
            send_async.__fluxloop_builtin__ = "collector.send:async"
            return send_async if is_async else send

        if provider == "builtin:collector.error":
            errors: list = []

            def _record_error(args: Any, kwargs: Any) -> None:
                errors.append((args, kwargs))
                pretty = args[0] if len(args) == 1 and not kwargs else {"args": args, "kwargs": kwargs}
                print(f"[ERROR] {pretty}")

            def send_error(*args: Any, **kwargs: Any) -> _AwaitableNone:
                _record_error(args, kwargs)
                return _AwaitableNone()

            async def send_error_async(*args: Any, **kwargs: Any) -> None:
                _record_error(args, kwargs)

            send_error.errors = errors
            send_error_async.errors = errors
            send_error.__fluxloop_builtin__ = "collector.error"
            send_error_async.__fluxloop_builtin__ = "collector.error:async"
            return send_error_async if is_async else send_error

        raise ValueError(
            f"Unknown callable provider '{provider}'. Supported providers: "
            "builtin:collector.send, builtin:collector.error."
        )

    def _set_by_path(self, payload: Dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = payload
        for key in parts[:-1]:
            current = current[key]
        current[parts[-1]] = value

    def _resolve_config_target(self) -> Optional[str]:
        runner = self.config.runner
        if runner.target:
            return runner.target
        return f"{runner.module_path}:{runner.function_name}"

