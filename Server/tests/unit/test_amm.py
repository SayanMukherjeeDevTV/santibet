"""Pure-math unit tests for app.services.trading_engine.amm - no DB, no
event loop needed."""
from decimal import Decimal

import pytest

from app.services.trading_engine import amm

B = Decimal("100")


def test_initial_prices_are_uniform_for_binary_market():
    q = amm.initial_quantities(["YES", "NO"])
    p = amm.prices(q, B)
    assert abs(p["YES"] - Decimal("0.5")) < Decimal("0.0001")
    assert abs(p["NO"] - Decimal("0.5")) < Decimal("0.0001")


def test_prices_always_sum_to_one():
    q = {"YES": Decimal("37.5"), "NO": Decimal("-12.25")}
    p = amm.prices(q, B)
    assert abs(sum(p.values()) - Decimal("1")) < Decimal("0.0000001")
    for price in p.values():
        assert Decimal("0") < price < Decimal("1")


def test_buying_yes_increases_yes_price():
    q = amm.initial_quantities(["YES", "NO"])
    p_before = amm.prices(q, B)["YES"]

    cost = amm.cost_to_trade(q, B, "YES", Decimal("10"))
    q["YES"] += Decimal("10")
    p_after = amm.prices(q, B)["YES"]

    assert cost > 0  # buying costs the trader money
    assert p_after > p_before


def test_cost_function_is_convex_buying_more_costs_more_per_share():
    q = amm.initial_quantities(["YES", "NO"])
    cost_10 = amm.cost_to_trade(q, B, "YES", Decimal("10"))

    q2 = dict(q)
    q2["YES"] += Decimal("10")
    cost_next_10 = amm.cost_to_trade(q2, B, "YES", Decimal("10"))

    # Same size trade costs more once you've already pushed the price up.
    assert cost_next_10 > cost_10


def test_buy_then_sell_same_shares_is_roughly_a_round_trip():
    q = amm.initial_quantities(["YES", "NO"])
    buy_cost = amm.cost_to_trade(q, B, "YES", Decimal("5"))
    q["YES"] += Decimal("5")
    sell_proceeds = amm.cost_to_trade(q, B, "YES", Decimal("-5"))

    # Selling back immediately returns (approximately) what was paid, since
    # no other trades happened in between and there's no explicit spread in
    # LMSR itself (spread/fees are layered on top by the trading service).
    assert abs(buy_cost + sell_proceeds) < Decimal("0.01")


def test_shares_for_amount_inverts_cost_to_trade():
    q = amm.initial_quantities(["YES", "NO"])
    amount = Decimal("20")

    shares = amm.shares_for_amount(q, B, "YES", amount, is_buy=True)
    actual_cost = amm.cost_to_trade(q, B, "YES", shares)

    assert abs(actual_cost - amount) < Decimal("0.01")


def test_negative_liquidity_param_rejected():
    q = amm.initial_quantities(["YES", "NO"])
    with pytest.raises(ValueError):
        amm.cost_function(q, Decimal("-5"))


def test_max_subsidy_loss_scales_with_b_and_outcome_count():
    loss_2 = amm.max_subsidy_loss(Decimal("100"), 2)
    loss_3 = amm.max_subsidy_loss(Decimal("100"), 3)
    assert loss_3 > loss_2 > 0
