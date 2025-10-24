import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
import calculator 

@st.cache_data
def load_data():
    return calculator.load_cleaned_data('./data/cleaned/')

product, supplier, tariff, financial, policy = load_data()
hs_codes = sorted(tariff["hs_code"].unique())

st.set_page_config(page_title="Tariff Scenario Planner", layout="wide")

# Sidebar navigation
st.sidebar.title("Tariff Scenario Planner")
st.sidebar.markdown("### Landed Cost & Scenario Planner")

if True:
    tab1, tab2 = st.tabs(["Landed Cost Calculator", "Scenario Planner"])

    with tab1:
        st.header("Landed Cost Calculator")

        # Filters in 3 columns
        col1, col2, col3 = st.columns(3)
        with col1:
            hs_code = st.selectbox("HS Code", hs_codes, key="hs_lc")
        
        importing_countries, exporting_countries = calculator.get_valid_countries_for_hscode(tariff, hs_code)
        
        with col2:
            importing_country = st.selectbox("Importing Country", importing_countries, key="ic_lc")
        with col3:
            exporting_country = st.selectbox("Exporting Country", exporting_countries, key="ec_lc")

        # Pass Through Rate input (reactive, outside any form)
        pass_through_rate = st.slider("Pass Through Rate (%)", 0, 100, 70, 
                                       help="Determines how much of cost increase is passed to customer vs absorbed",
                                       key="ptr_lc")

        filtered, tariff_row = calculator.filter_data(product, tariff, hs_code, importing_country, exporting_country)

        if len(filtered) and len(tariff_row):
            # Calculate with pass through rate
            results = calculator.run_landed_cost_calculation(filtered, tariff_row, pass_through_rate=pass_through_rate)
            
            # Show KPIs - Primary metrics
            st.subheader("Primary Output Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Landed Cost (USD)", f"${results['landed_cost_usd']:,.2f}")
            col2.metric("Landed Cost (INR)", f"₹{results['landed_cost_inr']:,.2f}")
            col3.metric("Target Selling Price (INR)", f"₹{results['target_selling_price_inr']:,.2f}")
            col4.metric("Profit (INR)", f"₹{results['profit_inr']:,.2f}")
            col5.metric("Adjusted Margin", f"{results['adjusted_margin_percent']:.1f}%")

            # Show all metrics in detailed table
            st.subheader("All Output Metrics")
            all_metrics = {
                "Metric": [
                    "Landed Cost (INR)",
                    "Landed Cost (USD)",
                    "Target Selling Price (INR)",
                    "Profit (INR)",
                    "Target Margin (%)",
                    "Adjusted Margin (%)",
                    "Freight Cost (USD)",
                    "Insurance Cost (USD)",
                    "BCD (%)",
                    "IGST (%)",
                    "BCD Amount (USD)",
                    "IGST Amount (USD)",
                    "Additional Duty (USD)",
                    "Total Duties & Taxes (USD)",
                    "Base Price (USD)",
                    "Volume Units",
                    "FX Rate",
                    "FX Impact (per unit INR)",
                    "Logistics Impact (USD)",
                    "Duty Impact (USD)",
                    "Total Duty Exposure (USD)",
                    "FTA Savings (USD)",
                    "Duty Impact (%)",
                    "Pass Through Rate (%)"
                ],
                "Value": [
                    f"₹{results['landed_cost_inr']:,.2f}",
                    f"${results['landed_cost_usd']:,.2f}",
                    f"₹{results['target_selling_price_inr']:,.2f}",
                    f"₹{results['profit_inr']:,.2f}",
                    f"{results['target_margin_percent']:.0f}%",
                    f"{results['adjusted_margin_percent']:.1f}%",
                    f"${results['freight_usd']:,.2f}",
                    f"${results['insurance_usd']:,.2f}",
                    f"{results['bcd_percent']:.1f}%",
                    f"{results['igst_percent']:.0f}%",
                    f"${results['bcd_amount']:,.2f}",
                    f"${results['igst_amount']:,.2f}",
                    f"${results['additional_duty']:,.2f}",
                    f"${results['total_duties']:,.2f}",
                    f"${results['base_price_usd']:,.2f}",
                    f"{int(results['volume']):,}",
                    f"{results['fx_rate']:.4f}",
                    f"₹{results['fx_impact_inr']:,.2f}",
                    f"${results['logistics_impact_usd']:,.2f}",
                    f"${results['duty_impact_usd']:,.2f}",
                    f"${results['total_duty_exposure_usd']:,.2f}",
                    f"${results['fta_savings_usd']:,.2f}",
                    f"{results['duty_impact_percent']:.2f}%",
                    f"{results['pass_through_rate']:.0f}%"
                ]
            }
            df_all_metrics = pd.DataFrame(all_metrics)
            st.dataframe(df_all_metrics, use_container_width=True, hide_index=True)

            # Breakdown section: Table and Pie Chart side by side
            st.subheader("Breakdown of Landed Cost Components (USD)")
            col_table, col_chart = st.columns(2)
            
            with col_table:
                breakdown = {
                    "Component": ["Base Price", "Freight Cost", "Insurance Cost", 
                                  "BCD Amount", "IGST Amount", "Additional Duty"],
                    "Amount (USD)": [
                        f"${results['base_price_usd']:,.2f}",
                        f"${results['freight_usd']:,.2f}",
                        f"${results['insurance_usd']:,.2f}",
                        f"${results['bcd_amount']:,.2f}",
                        f"${results['igst_amount']:,.2f}",
                        f"${results['additional_duty']:,.2f}"
                    ]
                }
                df_breakdown = pd.DataFrame(breakdown)
                st.table(df_breakdown)
            
            with col_chart:
                breakdown_chart = {
                    "Component": ["Base Price", "Freight", "Insurance", 
                                  "BCD", "IGST", "Add. Duty"],
                    "Amount": [
                        results['base_price_usd'],
                        results['freight_usd'],
                        results['insurance_usd'],
                        results['bcd_amount'],
                        results['igst_amount'],
                        results['additional_duty']
                    ]
                }
                df_chart = pd.DataFrame(breakdown_chart)
                fig = px.pie(df_chart, values='Amount', names='Component', 
                            title='Cost Distribution')
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("No data found for the selected filters.")


    with tab2:
        st.header("Scenario Planner")

        # Filters in 3 columns
        col1, col2, col3 = st.columns(3)
        with col1:
            hs_code = st.selectbox("HS Code", hs_codes, key="hs_sp")
        
        importing_countries, exporting_countries = calculator.get_valid_countries_for_hscode(tariff, hs_code)
        
        with col2:
            importing_country = st.selectbox("Importing Country", importing_countries, key="ic_sp")
        with col3:
            exporting_country = st.selectbox("Exporting Country", exporting_countries, key="ec_sp")

        filtered, tariff_row = calculator.filter_data(product, tariff, hs_code, importing_country, exporting_country)

        # Initialize defaults
        if len(filtered):
            default_bcd = float(filtered["bcd_percent"].iloc[0])
            default_igst = float(filtered["igst_percent"].iloc[0])
            default_fx = float(filtered["fx_rate"].iloc[0])
            default_volume = float(filtered["volume_units"].iloc[0])
            default_freight = float(filtered["freight_usd"].iloc[0])
            default_insurance = float(filtered["insurance_percent"].iloc[0])
            default_base_price = float(filtered["base_price_usd"].iloc[0])
            default_target_margin = float(filtered["target_margin_percent"].iloc[0])
        else:
            default_bcd = default_igst = default_fx = default_volume = 0.0
            default_freight = default_insurance = default_base_price = default_target_margin = 0.0

        with st.form("Scenario Inputs"):
            st.subheader("Scenario Parameters")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                new_bcd = st.number_input("New BCD (%)", min_value=0.0, max_value=100.0, step=0.1, value=default_bcd)
                new_igst = st.number_input("New IGST (%)", min_value=0.0, max_value=100.0, step=0.1, value=default_igst)
                new_base_price = st.number_input("New Base Price (USD)", min_value=0.01, step=0.01, value=default_base_price)
            
            with col2:
                new_freight = st.number_input("New Freight (USD)", min_value=0.0, step=0.1, value=default_freight)
                new_insurance = st.number_input("New Insurance (%)", min_value=0.0, max_value=100.0, step=0.1, value=default_insurance)
                new_fx = st.number_input("New FX Rate", min_value=0.01, max_value=500.0, step=0.01, value=default_fx)
            
            with col3:
                volume_override = st.number_input("Volume (units)", min_value=1.0, step=1.0, value=default_volume)
                new_target_margin = st.number_input("New Target Margin (%)", min_value=0.0, max_value=200.0, step=0.1, value=default_target_margin)
            
            submitted = st.form_submit_button("Run Scenario")

        # Pass Through Rate outside form so it's reactive
        pass_through_rate = st.slider("Pass Through Rate (%)", 0, 100, 70, key="ptr_sp")

        if submitted and len(filtered) and len(tariff_row):
            # Current (baseline) calculation with default pass through rate
            current_results = calculator.run_landed_cost_calculation(
                filtered.copy(), tariff_row, 
                pass_through_rate=pass_through_rate
            )
            
            # Scenario calculation with ALL OVERRIDES
            updated_results = calculator.run_landed_cost_calculation(
                filtered.copy(), tariff_row, 
                volume_override=volume_override,
                new_freight=new_freight,
                new_insurance=new_insurance,
                new_base_price=new_base_price,
                new_target_margin=new_target_margin,
                new_fx=new_fx,
                new_bcd=new_bcd,
                new_igst=new_igst,
                pass_through_rate=pass_through_rate
            )

            # Comparison table
            st.subheader("Comparison of Current and Scenario Values")
            comparisons = {
                "Output Metric": [
                    "Landed Cost (INR)",
                    "Target Selling Price (INR)",
                    "Profit (INR)",
                    "Landed Cost (USD)",
                    "Freight Cost (USD)",
                    "Insurance Cost (USD)",
                    "Base Price (USD)",
                    "BCD (%)",
                    "IGST (%)",
                    "BCD Amount (USD)",
                    "IGST Amount (USD)",
                    "Additional Duty (USD)",
                    "Total Duties & Taxes (USD)",
                    "Target Margin (%)",
                    "Adjusted Margin (%)",
                    "FX Rate",
                    "FX Impact (per unit INR)",
                    "Logistics Impact (USD)",
                    "Duty Impact (USD)",
                    "Total Duty Exposure (USD)",
                    "FTA Savings (USD)",
                    "Duty Impact (%)",
                ],
                "Current Values": [
                    f"₹{current_results['landed_cost_inr']:,.2f}",
                    f"₹{current_results['target_selling_price_inr']:,.2f}",
                    f"₹{current_results['profit_inr']:,.2f}",
                    f"${current_results['landed_cost_usd']:,.2f}",
                    f"${current_results['freight_usd']:,.2f}",
                    f"${current_results['insurance_usd']:,.2f}",
                    f"${current_results['base_price_usd']:,.2f}",
                    f"{current_results['bcd_percent']:.1f}",
                    f"{current_results['igst_percent']:.0f}",
                    f"${current_results['bcd_amount']:,.2f}",
                    f"${current_results['igst_amount']:,.2f}",
                    f"${current_results['additional_duty']:,.2f}",
                    f"${current_results['total_duties']:,.2f}",
                    f"{current_results['target_margin_percent']:.0f}",
                    f"{current_results['adjusted_margin_percent']:.1f}",
                    f"{current_results['fx_rate']:.4f}",
                    f"₹{current_results['fx_impact_inr']:,.2f}",
                    f"${current_results['logistics_impact_usd']:,.2f}",
                    f"${current_results['duty_impact_usd']:,.2f}",
                    f"${current_results['total_duty_exposure_usd']:,.2f}",
                    f"${current_results['fta_savings_usd']:,.2f}",
                    f"{current_results['duty_impact_percent']:.2f}",
                ],
                "Updated Values": [
                    f"₹{updated_results['landed_cost_inr']:,.2f}",
                    f"₹{updated_results['target_selling_price_inr']:,.2f}",
                    f"₹{updated_results['profit_inr']:,.2f}",
                    f"${updated_results['landed_cost_usd']:,.2f}",
                    f"${updated_results['freight_usd']:,.2f}",
                    f"${updated_results['insurance_usd']:,.2f}",
                    f"${updated_results['base_price_usd']:,.2f}",
                    f"{updated_results['bcd_percent']:.1f}",
                    f"{updated_results['igst_percent']:.0f}",
                    f"${updated_results['bcd_amount']:,.2f}",
                    f"${updated_results['igst_amount']:,.2f}",
                    f"${updated_results['additional_duty']:,.2f}",
                    f"${updated_results['total_duties']:,.2f}",
                    f"{updated_results['target_margin_percent']:.0f}",
                    f"{updated_results['adjusted_margin_percent']:.1f}",
                    f"{updated_results['fx_rate']:.4f}",
                    f"₹{updated_results['fx_impact_inr']:,.2f}",
                    f"${updated_results['logistics_impact_usd']:,.2f}",
                    f"${updated_results['duty_impact_usd']:,.2f}",
                    f"${updated_results['total_duty_exposure_usd']:,.2f}",
                    f"${updated_results['fta_savings_usd']:,.2f}",
                    f"{updated_results['duty_impact_percent']:.2f}",
                ]
            }
            comp_df = pd.DataFrame(comparisons)
            st.dataframe(comp_df, use_container_width=True)

        elif submitted:
            st.error("No data found for the selected filters.")
