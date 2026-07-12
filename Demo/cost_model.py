"""
AP6.3 — Token cost model (per-model, input/output split).

Replaces the AP2.5 placeholder, which charged ONE blended rate per 1K tokens for input and
output alike (`_COST_PER_1K_TOKENS = 0.005`). That was wrong in a way that mattered here:
LLM providers bill output several times higher than input, and this system's token mix is
extremely input-heavy — 950k of its ~1.08M tokens are prompt tokens, because
`generate_correction_llm` ships large snapshot excerpts into the prompt. Charging those
prompt tokens at an output-weighted blended rate roughly DOUBLED the reported cost.

Single source of truth: every place that estimates a cost calls `estimate_cost()`.

Prices are an ASSUMPTION, not a bill.
--------------------------------------
They are list prices, entered by hand from the public gpt-4o price sheet (USD, per 1M
tokens: $2.50 input / $10.00 output). They ignore Azure commitment discounts, batch
pricing, and cached-input rebates, and they go stale when a provider re-prices. They are
therefore an ESTIMATE for relative comparison ("which agent burns the budget?"), never an
accounting figure. Override without touching code:

    COST_PER_1K_INPUT=0.0025      # USD per 1K prompt tokens
    COST_PER_1K_OUTPUT=0.01       # USD per 1K completion tokens

Adding a model: put it in MODEL_PRICES. The active model comes from AZURE_OPENAI_DEPLOYMENT
(this project runs `gpt-4o`); an unknown model falls back to the default rates and says so
via `describe_prices()`, rather than silently costing zero.
"""
from __future__ import annotations

import os
from typing import Optional

#: USD per 1K tokens, (input, output). List prices — see the module docstring.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.010, 0.030),
}

#: Used when the deployment name is unknown to MODEL_PRICES.
DEFAULT_PRICES: tuple[float, float] = MODEL_PRICES["gpt-4o"]


def active_model() -> str:
    """The deployment this system actually calls (same env var the agents read)."""
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")


def prices_for(model: Optional[str] = None) -> tuple[float, float]:
    """
    (input_per_1k, output_per_1k) for `model`.

    Env overrides win over the table, so a changed price sheet never needs a code change.
    They are applied per-direction: setting only COST_PER_1K_OUTPUT keeps the table's
    input rate.
    """
    table_in, table_out = MODEL_PRICES.get(model or active_model(), DEFAULT_PRICES)
    env_in = os.getenv("COST_PER_1K_INPUT")
    env_out = os.getenv("COST_PER_1K_OUTPUT")
    return (
        float(env_in) if env_in else table_in,
        float(env_out) if env_out else table_out,
    )


def estimate_cost(
    tokens_prompt: Optional[int],
    tokens_completion: Optional[int],
    model: Optional[str] = None,
) -> Optional[float]:
    """
    Estimated USD for one call, billing input and output at their own rates.

    Returns None when NEITHER count is known — that is "we don't know", and it must not be
    reported as $0.00. A missing half counts as 0 (a call with prompt tokens but no
    completion tokens really did cost only its input).
    """
    if tokens_prompt is None and tokens_completion is None:
        return None
    in_rate, out_rate = prices_for(model)
    cost = ((tokens_prompt or 0) / 1000.0) * in_rate + ((tokens_completion or 0) / 1000.0) * out_rate
    return round(cost, 6)


def describe_prices(model: Optional[str] = None) -> dict:
    """The assumptions behind every cost on the dashboard, so they can be shown, not hidden."""
    name = model or active_model()
    in_rate, out_rate = prices_for(name)
    return {
        "model": name,
        "known_model": name in MODEL_PRICES,
        "input_per_1k_usd": in_rate,
        "output_per_1k_usd": out_rate,
        "overridden_by_env": bool(os.getenv("COST_PER_1K_INPUT") or os.getenv("COST_PER_1K_OUTPUT")),
    }
