import streamlit as st
import math
import pandas as pd
from datetime import datetime
import altair as alt


def calculate_monthly_installment(loan_amount, monthly_interest_rate, loan_term_months):
    """
    Calculate monthly installment using annuity method

    https://bankmonitor.hu/mediatar/cikk/annuitasos-hitel-mindenkinek-ilyen-van-de-senki-nem-tudja-mit-jelent/
    https://penzugyekokosan.hu/annuitas-keplet/

    R: a havi törlesztőrészlet (amit keresel)
    P: a felvett hitel összege (pl. 5.000.000 Ft)
    r: havi kamatláb (az éves kamat osztva 12-vel, pl. 6% → 0,06 / 12 = 0,005)
    n: a teljes futamidő hónapokban (pl. 20 év → 240 hónap)

    R = P * r(1 + r)^n / ((1 + r)^n - 1)
    """

    P = loan_amount
    r = monthly_interest_rate
    n = loan_term_months

    return P * r * (1 + r) ** n / ((1 + r) ** n - 1)


st.title("Rent or Buy")

st.header("Parameters")

CURRENT_YEAR = datetime.now().year
TRANSFER_TAX = 0.04

total_years = st.slider(
    "Years",
    key="total_years",
    value=25,
    min_value=25,
    max_value=60,
    format="%d years",
    bind="query-params",
)
real_estate_price = (
    st.slider(
        "Real Estate Price",
        key="real_estate_price_millions",
        value=55,
        min_value=30,
        max_value=100,
        format="%dM HUF",
        bind="query-params",
    )
    * 1_000_000
)
current_monthly_rent_price = (
    st.slider(
        "Rent Price (monthly)",
        key="current_rent_price_k",
        value=220,
        min_value=0,
        max_value=500,
        step=10,
        format="%dK HUF",
        bind="query-params",
    )
    * 1_000
)


with st.expander("Mortgage"):
    with st.container(border=True):
        loan_term_years = st.slider(
            "Loan Term",
            key="loan_term_years",
            value=20,
            min_value=15,
            max_value=25,
            format="%d years",
            bind="query-params",
        )

        mortgage_interest_rate = (
            st.slider(
                "Mortgage Interest Rate",
                key="mortgage_interest_rate_percent",
                value=3.0,
                min_value=0.0,
                max_value=30.0,
                step=0.1,
                format="%f%%",
                bind="query-params",
            )
            / 100
        )

        max_mortgage_amount = (
            st.slider(
                "Maximum Mortgage Amount",
                key="max_mortgage_amount_millions",
                value=50,
                min_value=50,
                max_value=100,
                step=5,
                format="%dM HUF",
                bind="query-params",
            )
            * 1_000_000
        )

        min_down_payment_percent = st.slider(
            "Minimum Down Payment Percent",
            key="min_down_payment_percent",
            value=10,
            min_value=0,
            max_value=100,
            format="%d%%",
            bind="query-params",
        )

    min_down_payment = real_estate_price * min_down_payment_percent / 100
    min_down_payment = max(min_down_payment, real_estate_price - max_mortgage_amount)
    min_down_payment_percent = int(
        math.ceil(min_down_payment / real_estate_price * 100)
    )

    down_payment_percent = st.slider(
        "Down Payment",
        key="down_payment_percent",
        value=max(min_down_payment_percent, min_down_payment_percent),
        min_value=min_down_payment_percent,
        max_value=100,
        format="%d%%",
        bind="query-params",
    )

    down_payment = real_estate_price * down_payment_percent / 100
    loan_amount = real_estate_price - down_payment
    monthly_installment = calculate_monthly_installment(
        loan_amount, mortgage_interest_rate / 12, loan_term_years * 12
    )
    total_to_repay = monthly_installment * loan_term_years * 12
    total_interest = total_to_repay - loan_amount
    total_to_pay = down_payment + total_to_repay

    with st.container(border=True):
        name_col, value_col = st.columns(2)
        name_col.write("Total to Pay")
        value_col.write(f"{total_to_pay / 1_000_000:.2f}M HUF")

        with st.container():
            name_col, value_col = st.columns(2)
            name_col.write("Down Payment")
            value_col.progress(
                down_payment / total_to_pay,
                text=f"{down_payment / 1_000_000:.2f}M HUF",
            )

        with st.container():
            name_col, value_col = st.columns(2)
            name_col.write("Loan Amount")
            value_col.progress(
                loan_amount / total_to_pay,
                text=f"{loan_amount / 1_000_000:.2f}M HUF",
            )

        with st.container():
            name_col, value_col = st.columns(2)
            name_col.write("Interest")
            value_col.progress(
                total_interest / total_to_pay,
                text=f"{total_interest / 1_000_000:.2f}M HUF",
            )

    name_col.space()
    with st.container():
        name_col, value_col = st.columns(2)
        name_col.write("Monthly Installment")
        value_col.write(f"{monthly_installment / 1_000:.2f}K HUF")


with st.expander("Initial Real Estate Purchase Costs"):
    lawyer_fee_percent = st.slider(
        "Lawyer Fee",
        key="lawyer_fee_percent",
        value=0.5,
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        format="%f%%",
        bind="query-params",
    )
    additional_loan_costs_k = st.slider(
        "Additional Costs",
        key="additional_loan_costs_k",
        value=300,
        min_value=0,
        max_value=900,
        step=50,
        format="%dK HUF",
        bind="query-params",
        help="""
            E.g.: értékbecslés, közjegyzői díj, folyósítási jutalék,
            hitelösszeg átutalási díja, tulajdoni lap lekérdezése,
            jelzálogjog bejegyzés díja etc...
        """,
    )

    lawyer_fee = real_estate_price * lawyer_fee_percent / 100
    transfer_tax = real_estate_price * TRANSFER_TAX
    additional_loan_costs = additional_loan_costs_k * 1_000
    capital_cost_of_buying = lawyer_fee + transfer_tax + additional_loan_costs

    name_col, value_col = st.columns(2)

    name_col.write("Lawyer Fee")
    value_col.write(f"{lawyer_fee / 1_000:.2f}K HUF")

    name_col.write(f"Transfer Tax ({TRANSFER_TAX * 100:.2f}%)")
    value_col.write(f"{transfer_tax / 1_000_000:.2f}M HUF")

    name_col.write("Additional Costs")
    value_col.write(f"{additional_loan_costs / 1_000:.2f}K HUF")

    name_col.write("Total Initial Costs")
    value_col.write(f"{capital_cost_of_buying / 1_000_000:.2f}M HUF")


with st.expander("Environmental Parameters"):
    rate_names = dict(
        appreciation="Real Estate Value",
        investment_return="Investment Return",
        rent_change="Rent",
    )
    initial_rate_percents = {
        rn: st.slider(
            rd,
            key=f"initial_{rn}_rate_percent",
            value=3.0,
            min_value=0.0,
            max_value=30.0,
            step=0.1,
            format="%f%%",
            bind="query-params",
        )
        for rn, rd in rate_names.items()
    }

    st.space()
    with st.expander("Annual Relative Environmental Changes"):
        st.warning("""
            Table values are not included in the URL!

            Click the icon in the top right corner to export your values to a CSV file,
            then reload them later using the file uploader.
        """)
        uploaded_file = st.file_uploader(
            "Reload previously exported data",
            type=["csv"],
            key="env_vars_uploader",
        )
        if uploaded_file is not None:
            df_relative_env_vars = pd.read_csv(uploaded_file)
        else:
            df_relative_env_vars = pd.DataFrame(
                [
                    {
                        "year": year,
                        **{f"rel_{rn}_rate_pct": 0.0 for rn in rate_names.keys()},
                    }
                    for year in range(CURRENT_YEAR + 1, CURRENT_YEAR + total_years + 2)
                ],
            )

        df_relative_env_vars = st.data_editor(
            df_relative_env_vars,
            key=st.session_state.get("df_relative_env_vars_editor_key"),
            hide_index=True,
            column_config={
                "year": st.column_config.NumberColumn(
                    "Year",
                    format="%d",
                    disabled=True,
                ),
                **{
                    f"rel_{rn}_rate_pct": st.column_config.NumberColumn(
                        rd,
                        format="%+f%%",
                    )
                    for rn, rd in rate_names.items()
                },
            },
        )

        def reset_env_vars():
            st.session_state["df_relative_env_vars_editor_key"] = (
                datetime.now().isoformat()
            )

        st.button("Reset", on_click=reset_env_vars, icon="⚠️")

        st.write("Calculated Cumulative Changes")
        df_relative_env_vars_calculated = df_relative_env_vars.copy()

        # Insert initial values
        df_relative_env_vars_calculated.loc[-1] = {
            "year": CURRENT_YEAR,
            **{
                f"rel_{rn}_rate_pct": initial_rate_percents[rn]
                for rn in rate_names.keys()
            },
        }
        df_relative_env_vars_calculated.sort_values("year", inplace=True)

        # Calculate rates
        for rn in rate_names.keys():
            df_relative_env_vars_calculated[f"{rn}_rate"] = (
                df_relative_env_vars_calculated[f"rel_{rn}_rate_pct"] / 100
            ).cumsum()

        # Calculate values
        for rn in rate_names.keys():
            df_relative_env_vars_calculated[f"value_{rn}"] = (
                1 + df_relative_env_vars_calculated[f"{rn}_rate"]
            ).cumprod()

        # Display calculated values
        tab_value_chart, tab_rate_chart, tab_table = st.tabs(
            ["Value Chart", "Rate Chart", "Table"]
        )

        with tab_value_chart:
            df_chart = df_relative_env_vars_calculated[
                ["year", *[f"value_{rn}" for rn in rate_names.keys()]]
            ].melt(id_vars="year", var_name="Value Type", value_name="Value")

            chart = (
                alt.Chart(df_chart)
                .mark_line(point=True)
                .encode(
                    x=alt.X("year:Q", axis=alt.Axis(format="d", title="Year")),
                    y=alt.Y("Value:Q", axis=alt.Axis(format=".2f", title="Value")),
                    color="Value Type:N",
                )
                .properties(height=400)
            )
            st.altair_chart(chart)

        with tab_rate_chart:
            df_chart = df_relative_env_vars_calculated[
                ["year", *[f"{rn}_rate" for rn in rate_names.keys()]]
            ].melt(id_vars="year", var_name="Rate Type", value_name="Rate")

            chart = (
                alt.Chart(df_chart)
                .mark_line(point=True)
                .encode(
                    x=alt.X("year:Q", axis=alt.Axis(format="d", title="Year")),
                    y=alt.Y("Rate:Q", axis=alt.Axis(format=".1%", title="Rate")),
                    color="Rate Type:N",
                )
                .properties(height=400)
            )
            st.altair_chart(chart)

        with tab_table:
            st.table(
                df_relative_env_vars_calculated[
                    [
                        "year",
                        *[
                            col
                            for rn in rate_names.keys()
                            for col in [
                                f"rel_{rn}_rate_pct",
                                f"{rn}_rate",
                                f"value_{rn}",
                            ]
                        ],
                    ]
                ]
                .set_index("year")
                .style.format(
                    {
                        "year": "{:.0f}",
                        **{f"rel_{rn}_rate_pct": "{:.2f}%" for rn in rate_names.keys()},
                        **{
                            col: "{:.2%}"
                            for rn in rate_names.keys()
                            for col in [
                                f"{rn}_rate",
                            ]
                        },
                        **{f"value_{rn}": "{:.5f}" for rn in rate_names.keys()},
                    }
                )
            )

st.header("Results")


def buy_model():
    res = []

    payed = down_payment
    value_of_real_estate = real_estate_price
    for year_index in range(total_years + 1):
        appreciation_rate = df_relative_env_vars_calculated["appreciation_rate"].iloc[
            year_index
        ]

        value_of_real_estate *= 1 + appreciation_rate

        ownership_ratio = payed / total_to_pay
        if ownership_ratio < 1:
            payed += monthly_installment * 12

        wealth = value_of_real_estate * ownership_ratio - capital_cost_of_buying
        res.append(wealth)

    return res


def rent_model():
    res = []

    wealth = capital_cost_of_buying
    for year_index in range(total_years + 1):
        investment_return_rate = df_relative_env_vars_calculated[
            "investment_return_rate"
        ].iloc[year_index]
        value_rent_change = df_relative_env_vars_calculated["value_rent_change"].iloc[
            year_index
        ]
        monthly_rent_price = current_monthly_rent_price * value_rent_change

        wealth *= 1 + investment_return_rate
        wealth += (monthly_installment - monthly_rent_price) * 12
        res.append(wealth)

    return res


summary_data = [
    dict(
        year=CURRENT_YEAR + year_index,
        buy=buy_data,
        rent=rent_data,
    )
    for year_index, buy_data, rent_data in zip(
        range(total_years + 1),
        buy_model(),
        rent_model(),
    )
]
df = pd.DataFrame(summary_data).set_index("year").reset_index()
df["buy"] = df["buy"] / 1_000_000
df["rent"] = df["rent"] / 1_000_000
df_melted = df.melt(id_vars="year", var_name="Type", value_name="Wealth")

line_chart = (
    alt.Chart(df_melted)
    .mark_line(point=True)
    .encode(
        x=alt.X("year:Q", axis=alt.Axis(format="d")),
        y=alt.Y("Wealth:Q", axis=alt.Axis(format=".2f", title="Wealth (M HUF)")),
        color="Type:N",
    )
)

vertical_line = (
    alt.Chart(
        pd.DataFrame(
            {"year": [CURRENT_YEAR + loan_term_years], "event": ["Loan Term End"]}
        )
    )
    .mark_rule(color="gray", strokeDash=[5, 5])
    .encode(x="year:Q", tooltip=["event:N"])
)

summary_chart = (line_chart + vertical_line).properties(height=400)
st.altair_chart(summary_chart, use_container_width=True)
