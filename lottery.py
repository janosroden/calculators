import dataclasses
import datetime
import json
import urllib.request
from typing import Optional

import streamlit as st

st.title("Which lottery worth playing?")

st.subheader("Parameters")

##########################
# Parameters
##########################

money_you_need_per_month = (
    st.slider(
        "Money you need per month",
        key="money_you_need_per_month_k",
        min_value=500.0,
        max_value=5000.0,
        value=800.0,
        step=50.0,
        format="%0.0fK HUF",
        bind="query-params",
        help="The amount of money you need each month to cover your expenses.",
    )
    * 1000
)
interest_rate = (
    st.slider(
        "Interest rate",
        key="interest_rate_pct",
        min_value=0.0,
        max_value=30.0,
        value=3.0,
        step=0.5,
        format="%0.1f%%",
        bind="query-params",
        help="Annual interest rate for the money you would win in the lottery.",
    )
    / 100
)


money_you_need_per_year = money_you_need_per_month * 12
money_to_win = money_you_need_per_year / interest_rate

col_name, col_value = st.columns(2)
col_name.write("Money you need per year")
col_value.write(f"{money_you_need_per_year:,.0f} HUF")

col_name.write("Money to win")
col_value.write(f"{money_to_win:,.0f} HUF")


##########################
# Games
##########################


@dataclasses.dataclass(kw_only=True)
class GameDetail:
    type: str
    win_chance: float
    price: float | None
    title: str | None
    prize: float | None = None
    next_draw: Optional[datetime.datetime] = None

    @property
    def expected_value(self) -> Optional[float]:
        """Expected value per ticket.

        This assumes:
        - `win_chance` is the chance of winning the jackpot (not smaller tiers)
        - `prize` is the jackpot amount
        - you win the full jackpot (i.e., you don't share it)

        In reality, the jackpot is often shared by multiple winners, so this
        should be treated as a best-case upper bound rather than a precise EV.
        """
        if self.prize is None:
            return None
        return self.win_chance * self.prize - (self.price or 0.0)

    @property
    def expected_return_ratio(self) -> Optional[float]:
        """Expected return ratio per ticket.

        This is the ratio of expected value to price.
        """
        if self.prize is None or not self.price:
            return None
        return (self.win_chance * self.prize) / self.price


GAMES = [
    GameDetail(
        type="LOTTO5",
        title="Ötöslottó",
        win_chance=1 / 43_949_268,
        price=400.0,
    ),
    GameDetail(
        type="LOTTO6",
        title="Hatoslottó",
        win_chance=1 / 8_145_060,
        price=400.0,
    ),
    GameDetail(
        type="LOTTO7",
        title="Skandináv lottó",
        win_chance=1 / 3_362_260,
        price=400.0,
    ),
]


##########################
# Next-draw prizes
##########################


def _parse_hu_number(value: Optional[str]) -> float:
    """Parse Hungarian formatted numbers like '5.900.000,00' into a float."""
    if not value:
        return 0.0
    normalized = value.replace(".", "").replace(",", ".").strip()
    try:
        return float(normalized)
    except ValueError:
        return 0.0


@st.cache_data(ttl=3600)
def _fetch_all_games_json() -> dict:
    url = "https://bet.szerencsejatek.hu/PublicInfo/ResultJSON.aspx?query=last"
    resp = urllib.request.urlopen(url).read().decode("utf-8")
    return json.loads(resp)


def fill_next_draw_details() -> None:
    """Fill in missing attributes in the global GAMES list from the JSON API."""

    game_map = {g.type: g for g in GAMES}

    data = _fetch_all_games_json()
    for game in data.get("game", []):
        game_type = game.get("type")
        base = game_map.get(game_type)
        if base is None:
            continue

        draw = game.get("draw", {})
        prize_str = draw.get("next-draw-expected-win") or draw.get(
            "next-draw-expected-win-mrdhuf"
        )
        base.prize = _parse_hu_number(prize_str)

        # Prefer the API-provided next draw date (draw-date inside next-draw)
        next_draw_date = game.get("next-draw", {}).get("draw-date")
        if next_draw_date:
            try:
                base.next_draw = datetime.datetime.strptime(
                    next_draw_date, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                try:
                    base.next_draw = datetime.datetime.fromisoformat(next_draw_date)
                except ValueError:
                    base.next_draw = None


with st.expander("Expected next-draw prizes", expanded=True):
    fill_next_draw_details()
    now = datetime.datetime.now()
    for detail in GAMES:
        col_name, col_value = st.columns(2)
        col_name.write(detail.title or detail.type)

        if detail.next_draw is None:
            suffix = " (date unknown)"
        else:
            delta = detail.next_draw - now
            # breakdown delta into days + hours (ignore minutes/seconds)
            total_seconds = int(delta.total_seconds())
            sign = 1 if total_seconds >= 0 else -1
            total_seconds = abs(total_seconds)
            days, rem = divmod(total_seconds, 86400)
            hours = rem // 3600

            if sign >= 0:
                suffix = f" ({days}d {hours}h left)"
            else:
                suffix = f" ({days}d {hours}h ago)"

        col_value.write(f"{detail.prize:,.0f} HUF{suffix}")


##########################
# Results
##########################

st.subheader("Results")

for detail in sorted(GAMES, key=lambda g: g.expected_return_ratio or 0, reverse=True):
    st.metric(
        label=detail.title or detail.type,
        value=f"{detail.prize:,.0f} HUF ({detail.prize / money_to_win:0f}x)",
        delta=f"{detail.expected_return_ratio:.3f} ROI",
        delta_color="green" if detail.prize >= money_to_win else "red",
        delta_arrow="off",
        # delta_description=f"",
    )
