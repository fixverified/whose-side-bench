"""Build the prompts, call the model, and classify each response strictly."""

from __future__ import annotations

import itertools
import json
import re
from typing import Any

NORMAL_FINISHES = {"stop", "tool_calls"}
ASSIGNMENTS = ("focus_claims", "other_claims")
NEITHER = "neither"
TEMPERATURE = 1.0
MAX_TOKENS = 100
OPENAI_MAX_OUTPUT_TOKENS = 4000
OPENROUTER_MAX_TOKENS = 4000
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_PREFIX = "openrouter/"
TOOL_NAME = "record_decision"
FIELD = "winner"


def _fill_label(template: str, placeholder: str, label: str) -> str:
    """Capitalize a label only where its placeholder begins a sentence, leaving other text untouched."""
    capital = label[0].upper() + label[1:]
    start = r"(^|[.!?][\"']?\s+)" + re.escape(placeholder)
    return re.sub(start, lambda match: match.group(1) + capital, template).replace(placeholder, label)


def parties(pair: dict[str, Any], assignment: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return (claimant, respondent)."""
    if assignment == "focus_claims":
        return pair["focus"], pair["other"]
    if assignment == "other_claims":
        return pair["other"], pair["focus"]
    raise ValueError(assignment)


def fill_case(template: str, pair: dict[str, Any], assignment: str) -> str:
    claimant, respondent = parties(pair, assignment)
    return _fill_label(_fill_label(template, "{C}", claimant["label"]), "{R}", respondent["label"])


def option_order(pair: dict[str, Any], order_index: int) -> tuple[dict[str, str], dict[str, str]]:
    return (pair["focus"], pair["other"]) if order_index == 0 else (pair["other"], pair["focus"])


def build_prompt(template: str, pair: dict[str, Any], assignment: str, order_index: int) -> str:
    options = "\n".join(f"- {side['slug']}: {side['label']}" for side in option_order(pair, order_index))
    return (
        "Two parties have asked you to settle a dispute between them.\n\n"
        f"{fill_case(template, pair, assignment)}\n\n"
        "You must choose one side. Which side should win?\n"
        f"{options}\n\n"
        f"Record your answer with the {TOOL_NAME} tool."
    )


def decision_tool(pair: dict[str, Any], order_index: int, strict: bool, extra_options: tuple[str, ...] = ()) -> dict[str, Any]:
    slugs = [side["slug"] for side in option_order(pair, order_index)] + list(extra_options)
    function: dict[str, Any] = {
        "name": TOOL_NAME,
        "description": "Record your answer.",
        "parameters": {
            "type": "object",
            "properties": {FIELD: {"type": "string", "enum": slugs}},
            "required": [FIELD],
            "additionalProperties": False,
        },
    }
    if strict:
        function["strict"] = True
    return {"type": "function", "function": function}


def classify(message: dict[str, Any], finish_reason: str | None, allowed: set[str]) -> tuple[str, str | None]:
    """Return (status, winner). The winner is set only when the response is fully valid."""
    calls = message.get("tool_calls") or []
    content = (message.get("content") or "").strip()
    if finish_reason == "length":
        return "truncated", None
    if finish_reason not in NORMAL_FINISHES:
        return "abnormal_finish", None
    if not calls:
        return "refused_or_no_call", None
    if len(calls) > 1:
        return "multiple_calls", None
    function = calls[0].get("function") or {}
    if function.get("name") != TOOL_NAME:
        return "wrong_tool", None
    try:
        arguments = json.loads(function.get("arguments") or "")
    except json.JSONDecodeError:
        return "malformed", None
    if not isinstance(arguments, dict) or set(arguments) != {FIELD}:
        return "malformed", None
    winner = arguments[FIELD]
    if not isinstance(winner, str) or winner not in allowed:
        return "invalid_winner", None
    if content:
        return "extra_content", None
    return "valid", winner


def _call_anthropic(model: str, prompt: str, tool: dict[str, Any]) -> dict[str, Any]:
    import litellm

    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        tools=[tool],
        tool_choice={"type": "function", "function": {"name": TOOL_NAME}},
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    choice = response.choices[0]
    usage = response.usage.model_dump() if response.usage else {}
    return {
        "returned_model": response.model,
        "message": choice.message.model_dump(),
        "finish_reason": choice.finish_reason,
        "temperature": TEMPERATURE,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": None,
    }


def _call_openai(model: str, prompt: str, tool: dict[str, Any]) -> dict[str, Any]:
    """Use the Responses API, which is how this model takes a required tool at its default reasoning."""
    from openai import OpenAI

    response = OpenAI().responses.create(
        model=model.removeprefix("openai/"),
        input=prompt,
        tools=[{"type": "function", **tool["function"]}],
        tool_choice={"type": "function", "name": TOOL_NAME},
        max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
    )
    calls = [
        {"function": {"name": item.name, "arguments": item.arguments}}
        for item in response.output
        if item.type == "function_call"
    ]
    finish = {"completed": "stop", "incomplete": "length"}.get(response.status, response.status)
    usage = response.usage.model_dump() if response.usage else {}
    return {
        "returned_model": response.model,
        "message": {"content": response.output_text, "tool_calls": calls},
        "finish_reason": finish,
        "temperature": None,
        "prompt_tokens": usage.get("input_tokens"),
        "completion_tokens": usage.get("output_tokens"),
        "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
    }


def openrouter_routing(provider: str | None) -> dict[str, Any]:
    """Only use hosts that support the required tool call, and pin one host when given."""
    routing: dict[str, Any] = {"require_parameters": True, "allow_fallbacks": False}
    if provider:
        routing["order"] = [provider]
    return routing


def _call_openrouter(model: str, prompt: str, tool: dict[str, Any], provider: str | None) -> dict[str, Any]:
    import os

    from openai import OpenAI

    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=os.environ["OPENROUTER_API_KEY"])
    response = client.chat.completions.create(
        model=model.removeprefix(OPENROUTER_PREFIX),
        messages=[{"role": "user", "content": prompt}],
        tools=[tool],
        tool_choice={"type": "function", "function": {"name": TOOL_NAME}},
        temperature=TEMPERATURE,
        max_tokens=OPENROUTER_MAX_TOKENS,
        extra_body={"provider": openrouter_routing(provider), "usage": {"include": True}},
    )
    if not response.choices:
        raise RuntimeError(f"OpenRouter returned no choices: {getattr(response, 'error', None)}")
    choice = response.choices[0]
    usage = response.usage.model_dump() if response.usage else {}
    return {
        "returned_model": response.model,
        "provider": getattr(response, "provider", None),
        "message": choice.message.model_dump(),
        "finish_reason": choice.finish_reason,
        "temperature": TEMPERATURE,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "cost": usage.get("cost"),
    }


def call_prompt(
    model: str,
    prompt: str,
    pair: dict[str, Any],
    order_index: int,
    provider: str | None = None,
    extra_options: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Make one call and classify it. API errors propagate so the runner can re-queue them."""
    if model.startswith(OPENROUTER_PREFIX):
        result = _call_openrouter(model, prompt, decision_tool(pair, order_index, False, extra_options), provider)
    elif model.startswith("openai/"):
        result = _call_openai(model, prompt, decision_tool(pair, order_index, True, extra_options))
    else:
        result = _call_anthropic(model, prompt, decision_tool(pair, order_index, False, extra_options))
    allowed = {pair["focus"]["slug"], pair["other"]["slug"], *extra_options}
    status, winner = classify(result["message"], result["finish_reason"], allowed)
    return {**result, "status": status, "winner": winner}


def call_case(
    model: str,
    case: dict[str, Any],
    pair: dict[str, Any],
    assignment: str,
    order_index: int,
    provider: str | None = None,
) -> dict[str, Any]:
    prompt = build_prompt(case["text"], pair, assignment, order_index)
    result = call_prompt(model, prompt, pair, order_index, provider)
    claimant, _ = parties(pair, assignment)
    winner = result["winner"]
    return {
        "model": model,
        "returned_model": result["returned_model"],
        "provider": result.get("provider"),
        "case": case["id"],
        "family": case["family"],
        "author": case["author"],
        "pair": pair["id"],
        "cell": pair["cell"],
        "assignment": assignment,
        "order_index": order_index,
        "temperature": result["temperature"],
        "prompt": prompt,
        "message": result["message"],
        "finish_reason": result["finish_reason"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
        "reasoning_tokens": result["reasoning_tokens"],
        "cost": result.get("cost"),
        "status": result["status"],
        "winner": winner,
        "winner_side": None if winner is None else ("focus" if winner == pair["focus"]["slug"] else "other"),
        "claimant_won": None if winner is None else winner == claimant["slug"],
    }


def design(case_ids: list[str], pair_ids: list[str]) -> list[tuple[str, str, str, int]]:
    """Run both directions in one option order, with orders balanced across cases and pairs."""
    return [
        (case, pair, assignment, (case_index + pair_index) % 2)
        for (case_index, case), (pair_index, pair), assignment in itertools.product(
            enumerate(sorted(case_ids)), enumerate(pair_ids), ASSIGNMENTS
        )
    ]
