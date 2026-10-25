"""Terminal chat client for an OpenAI-compatible llama.cpp server."""

from __future__ import annotations

import json
import os
from typing import Any, Callable

from .core import FindingsStore, MarketData, PatternBacktester

SYSTEM_PROMPT = """You are tradebot, a local market-research assistant. Answer strategy
questions by using the backtest tool, not by inventing performance. Before giving a
conclusion, load bars and run a backtest. Save each completed backtest as a finding.
State that results are historical event studies, not trading advice."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_or_fetch_bars",
            "description": "Load stored OHLCV bars, or fetch and store the requested range when absent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "timeframe": {"type": "string", "enum": ["1D", "5m"]},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backtest_pattern",
            "description": "Run an event study: pattern fires, then calculate close-to-close return over forward bars.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "pattern": {"type": "string", "enum": ["green", "hammer", "doji", "red_doji", "red", "green_any"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "forward_bars": {"type": "integer", "minimum": 1},
                    "timeframe": {"type": "string", "enum": ["1D", "5m"]},
                },
                "required": ["symbol", "pattern", "start_date", "end_date", "forward_bars"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_finding",
            "description": "Persist a backtest result in the separate tradebot findings database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "pattern": {"type": "string"},
                    "window": {"type": "string", "description": "Stable label, e.g. 1D:2023-01-01:2024-01-01:5"},
                    "summary": {"type": "string"},
                    "result": {"type": "object"},
                },
                "required": ["symbol", "pattern", "window", "summary", "result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_findings",
            "description": "Recall previous findings by exact symbol, pattern, and window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "pattern": {"type": "string"},
                    "window": {"type": "string"},
                },
                "required": ["symbol", "pattern", "window"],
            },
        },
    },
]


class ToolRunner:
    def __init__(self) -> None:
        self.market_data = MarketData()
        self.backtester = PatternBacktester()
        self.findings = FindingsStore()
        self.handlers: dict[str, Callable[..., Any]] = {
            "load_or_fetch_bars": self.load_or_fetch_bars,
            "backtest_pattern": self.backtest_pattern,
            "save_finding": self.findings.save,
            "lookup_findings": self.findings.lookup,
        }

    def load_or_fetch_bars(self, **kwargs: Any) -> dict[str, Any]:
        return self.market_data.load_or_fetch(**kwargs)

    def backtest_pattern(
        self,
        symbol: str,
        pattern: str,
        start_date: str,
        end_date: str,
        forward_bars: int,
        timeframe: str = "1D",
    ) -> dict[str, Any]:
        bars = self.market_data.load_bars(symbol, start_date, end_date, timeframe)
        if not bars:
            raise ValueError("No stored bars. Call load_or_fetch_bars first.")
        return self.backtester.backtest(bars, pattern, forward_bars)

    def run(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.handlers:
            raise ValueError(f"Unknown tool: {name}")
        return self.handlers[name](**arguments)


class LlamaChat:
    def __init__(self) -> None:
        self.base_url = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080").rstrip("/")
        self.model = os.getenv("LLAMA_MODEL", "qwen")
        self.api_key = os.getenv("LLAMA_SERVER_API_KEY")
        self.tools = ToolRunner()

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def ask(self, question: str) -> str:
        try:
            import requests
        except ModuleNotFoundError:
            return "The requests dependency is missing. Install the backend requirements, then try again."

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for _ in range(6):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json={"model": self.model, "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
                    timeout=120,
                )
                response.raise_for_status()
            except requests.RequestException:
                return (
                    f"The llama.cpp server is unavailable at {self.base_url}. "
                    "Start llama-server with --jinja, then try again."
                )

            message = response.json()["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []
            messages.append(message)
            if not tool_calls:
                return message.get("content") or "The model returned no answer."

            for call in tool_calls:
                try:
                    arguments = json.loads(call["function"]["arguments"])
                    result = self.tools.run(call["function"]["name"], arguments)
                    content = json.dumps(result)
                except (ValueError, TypeError, KeyError, RuntimeError) as exc:
                    content = json.dumps({"error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})
        return "The model reached the tool-call limit before finishing the answer."


def run_terminal_chat() -> None:
    chat = LlamaChat()
    print("tradebot terminal chat. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            question = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.lower() in {"exit", "quit"}:
            return
        if question:
            print(f"\ntradebot> {chat.ask(question)}")
