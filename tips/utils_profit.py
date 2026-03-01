
from decimal import Decimal, InvalidOperation


def fractional_to_decimal(odds_str):
    """Converts fractional odds like '7/2' to decimal."""
    if "/" not in odds_str:
        return None

    try:
        num, den = odds_str.split("/")
        return Decimal(num) / Decimal(den)
    except (InvalidOperation, ValueError):
        return None


def calculate_profit(odds, result, category="EW"):
    """
    Correct profit engine with proper EW maths and VOID handling.

    EW = 1pt win + 1pt place (2pts total stake)
    Win-only = 1pt stake
    """

    decimal_odds = fractional_to_decimal(odds)
    if decimal_odds is None:
        return Decimal("0.00")

    win_stake = Decimal("1.00")
    place_stake = Decimal("1.00")
    total_stake = win_stake + place_stake
    place_odds = decimal_odds / Decimal("5")  # fixed 1/5 terms

    # ------------------------------------
    # VOID BET
    # ------------------------------------
    if result == "VOID":
        if category == "EW":
            return total_stake  # 2 pts returned
        return win_stake       # 1 pt returned (win only)

    # ------------------------------------
    # EACH-WAY BET LOGIC
    # ------------------------------------
    if category == "EW":

        # WIN
        if result == "WON":
            win_profit = win_stake * decimal_odds
            place_profit = place_stake * place_odds

            total_win_return = win_stake + win_profit
            total_place_return = place_stake + place_profit

            total_return = total_win_return + total_place_return
            return total_return - total_stake

        # PLACED (not winning)
        if result == "PLACED":
            place_profit = place_stake * place_odds
            total_place_return = place_stake + place_profit

            return total_place_return - total_stake

        # LOST
        if result == "LOST":
            return -total_stake

    # ------------------------------------
    # WIN-ONLY BET TYPES
    # ------------------------------------
    if result == "WON":
        win_profit = win_stake * decimal_odds
        total_return = win_stake + win_profit
        return total_return - win_stake

    if result in ("PLACED", "LOST"):
        return -win_stake

    return Decimal("0.00")
