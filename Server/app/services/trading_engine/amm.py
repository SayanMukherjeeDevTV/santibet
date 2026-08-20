"""Hanson's LMSR (Logarithmic Market Scoring Rule) - the AMM half of the
hybrid trading engine.

For outcome quantities q = {outcome_id: net_shares_issued}, liquidity
parameter b:

    C(q) = b * ln( sum_i exp(q_i / b) )                 cost function
    p_i  = exp(q_i / b) / sum_j exp(q_j / b)             price of outcome i (sums to 1)
    cost_to_trade(delta) = C(q_after) - C(q_before)      what a trader pays/receives

Implemented with Decimal (not float) for consistency with the rest of the
money-handling code, using the log-sum-exp trick for numerical stability.
These are pure functions with no I/O so they're trivially unit-testable.
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40

QuantityMap = dict[str, Decimal]


def _log_sum_exp(exponents: list[Decimal]) -> Decimal:
    m = max(exponents)
    total = sum((e - m).exp() for e in exponents)
    return m + total.ln()


def cost_function(q: QuantityMap, b: Decimal) -> Decimal:
    if b <= 0:
        raise ValueError("liquidity parameter b must be positive")
    exponents = [qi / b for qi in q.values()]
    return b * _log_sum_exp(exponents)


def prices(q: QuantityMap, b: Decimal) -> dict[str, Decimal]:
    if b <= 0:
        raise ValueError("liquidity parameter b must be positive")
    exponents = {k: v / b for k, v in q.items()}
    m = max(exponents.values())
    shifted = {k: (v - m).exp() for k, v in exponents.items()}
    total = sum(shifted.values())
    return {k: v / total for k, v in shifted.items()}


def cost_to_trade(q: QuantityMap, b: Decimal, outcome_id: str, delta_shares: Decimal) -> Decimal:
    """Cost (positive = trader pays, negative = trader receives) to move
    `outcome_id`'s net issued shares by `delta_shares` (positive = buy,
    negative = sell)."""
    q_after = dict(q)
    q_after[outcome_id] = q.get(outcome_id, Decimal("0")) + delta_shares
    return cost_function(q_after, b) - cost_function(q, b)


def shares_for_amount(
    q: QuantityMap,
    b: Decimal,
    outcome_id: str,
    amount: Decimal,
    *,
    is_buy: bool,
    max_iterations: int = 80,
    tolerance: Decimal = Decimal("0.0001"),
) -> Decimal:
    """Invert cost_to_trade via bisection: how many shares does `amount`
    dollars buy (or how many shares must be sold to receive `amount`
    dollars)? cost_to_trade is strictly monotonic in delta_shares so
    bisection converges reliably without needing derivatives."""
    if amount <= 0:
        return Decimal("0")

    sign = Decimal("1") if is_buy else Decimal("-1")
    target = amount if is_buy else -amount

    lo = Decimal("0")
    hi = Decimal("1")
    # Expand hi until cost_to_trade(hi) overshoots the target.
    for _ in range(200):
        c = cost_to_trade(q, b, outcome_id, sign * hi)
        if (is_buy and c >= target) or (not is_buy and c <= target):
            break
        hi *= 2
    else:
        raise ValueError("Could not bracket a solution - amount too large for this pool")

    for _ in range(max_iterations):
        mid = (lo + hi) / 2
        c = cost_to_trade(q, b, outcome_id, sign * mid)
        diff = c - target
        if abs(diff) <= tolerance:
            return mid
        if (is_buy and c < target) or (not is_buy and c > target):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def avg_price(cost: Decimal, shares: Decimal) -> Decimal:
    if shares == 0:
        return Decimal("0")
    return abs(cost) / shares


def initial_quantities(outcome_ids: list[str]) -> QuantityMap:
    """A freshly-created pool starts at q_i = 0 for every outcome, which
    yields a uniform price (1/N each)."""
    return {oid: Decimal("0") for oid in outcome_ids}


def max_subsidy_loss(b: Decimal, num_outcomes: int) -> Decimal:
    """LMSR's classic bounded-loss guarantee: the market maker's maximum
    possible loss is b * ln(N). This is what `subsidy_remaining` on the
    amm_pools row is initialized to, so admins can reason about worst-case
    treasury exposure per market before setting b."""
    from decimal import Decimal as D

    return b * D(num_outcomes).ln()
