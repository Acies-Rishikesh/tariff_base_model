import pandas as pd

def load_cleaned_data(base_path='../data/cleaned/'):
    product = pd.read_csv(f"{base_path}product_master_data_final.csv")
    supplier = pd.read_csv(f"{base_path}supplier_master.csv")
    tariff = pd.read_csv(f"{base_path}trade_&_tariff_reference_data.csv")
    financial = pd.read_csv(f"{base_path}financial__performance_data.csv")
    policy = pd.read_csv(f"{base_path}policy_&_volatility_data.csv")
    return product, supplier, tariff, financial, policy

def get_valid_countries_for_hscode(tariff, hs_code):
    filtered = tariff[tariff["hs_code"] == hs_code]
    importing_countries = sorted(filtered["country"].unique())
    exporting_countries = sorted(filtered["exporting_country"].unique())
    return importing_countries, exporting_countries

def filter_data(product, tariff, hs_code, importing_country, exporting_country):
    df = product.copy()
    df = df[
        (df["hs_code"] == hs_code) &
        (df["importing_country"] == importing_country) &
        (df["country_of_origin_coo"] == exporting_country)
    ]
    tariff_row = tariff[
        (tariff["hs_code"] == hs_code) &
        (tariff["country"] == importing_country) &
        (tariff["exporting_country"] == exporting_country)
    ]
    return df, tariff_row

def run_landed_cost_calculation(product_row, tariff_row, volume_override=None, 
                                  new_freight=None, new_insurance=None, 
                                  new_base_price=None, new_target_margin=None,
                                  new_fx=None, new_bcd=None, new_igst=None,
                                  pass_through_rate=100.0):
    """
    Calculate landed cost with all metrics including pass through rate
    pass_through_rate: 0-100, where 100 means all cost increase passed to customer, 
                       0 means all absorbed by company
    """
    # Extract base values - OVERRIDE if parameters provided
    base_price = float(new_base_price) if new_base_price is not None else float(product_row["base_price_usd"].iloc[0])
    freight = float(new_freight) if new_freight is not None else float(product_row["freight_usd"].iloc[0])
    ins_percent = float(new_insurance) if new_insurance is not None else float(product_row["insurance_percent"].iloc[0])
    fx_rate = float(new_fx) if new_fx is not None else float(product_row["fx_rate"].iloc[0])
    bcd = float(new_bcd) if new_bcd is not None else float(product_row["bcd_percent"].iloc[0])
    igst = float(new_igst) if new_igst is not None else float(product_row["igst_percent"].iloc[0])
    add_duty = float(product_row["additional_duty_percent"].iloc[0]) if "additional_duty_percent" in product_row.columns else 0
    fta_eligible = (product_row["fta_eligibility"].iloc[0] == "Yes")
    fta_reduction = float(product_row["fta_reduction_percent"].iloc[0]) if "fta_reduction_percent" in product_row.columns else 0
    volume = float(product_row["volume_units"].iloc[0]) if not volume_override else float(volume_override)
    target_margin = float(new_target_margin) if new_target_margin is not None else float(product_row["target_margin_percent"].iloc[0])
    
    # Static values for comparison (from original product data, not overridden)
    static_fx_rate = float(product_row["fx_rate"].iloc[0])
    static_bcd = float(product_row["bcd_percent"].iloc[0])
    
    # Determine effective BCD
    if fta_eligible and pd.notna(tariff_row["fta_duty_rate_percent"].iloc[0]) and tariff_row["fta_duty_rate_percent"].iloc[0] > 0:
        bcd_effective = float(tariff_row["fta_duty_rate_percent"].iloc[0])
    else:
        bcd_effective = bcd

    # Calculate cost components
    insurance = (base_price * ins_percent) / 100
    bcd_amount = (base_price * bcd_effective) / 100
    igst_amount = ((base_price + freight + insurance + bcd_amount) * igst) / 100
    additional_duty = (base_price * add_duty) / 100 if add_duty else 0
    total_duties = bcd_amount + igst_amount + additional_duty
    
    # Landed cost calculations
    landed_cost_usd = base_price + freight + insurance + total_duties
    landed_cost_inr = landed_cost_usd * fx_rate
    
    # Adjusted margin based on pass through rate
    adjusted_margin = target_margin * (pass_through_rate / 100)
    
    # Target selling price based on ADJUSTED margin
    target_selling_price_inr = landed_cost_inr * (1 + adjusted_margin / 100)
    
    # Profit based on adjusted margin
    profit_inr = target_selling_price_inr - landed_cost_inr
    
    # FX Impact per unit (USING OVERRIDDEN FX RATE IF PROVIDED)
    fx_impact_inr = (fx_rate - static_fx_rate) * base_price
    
    # Comparison metrics (for scenario planning)
    logistics_impact_usd = freight - float(product_row["freight_usd"].iloc[0]) if new_freight is not None else 0
    
    # Duty Impact: Compare the new BCD amount with static (original) BCD amount
    static_bcd_amount = (base_price * static_bcd / 100)
    new_bcd_amount = (base_price * bcd_effective / 100)
    duty_impact_usd = new_bcd_amount - static_bcd_amount
    
    total_duty_exposure_usd = bcd_amount * volume
    
    # FTA Savings
    if fta_eligible:
        fta_savings_usd = (base_price * static_bcd / 100 - base_price * bcd_effective / 100) * volume
    else:
        fta_savings_usd = -total_duty_exposure_usd
    
    # Duty impact percentage (percentage change in duty cost)
    if static_bcd_amount > 0:
        duty_impact_percent = ((new_bcd_amount - static_bcd_amount) / static_bcd_amount) * 100
    else:
        duty_impact_percent = 0

    return {
        "base_price_usd": base_price,
        "freight_usd": freight,
        "insurance_usd": insurance,
        "bcd_percent": bcd_effective,
        "igst_percent": igst,
        "bcd_amount": bcd_amount,
        "igst_amount": igst_amount,
        "additional_duty": additional_duty,
        "total_duties": total_duties,
        "landed_cost_usd": landed_cost_usd,
        "landed_cost_inr": landed_cost_inr,
        "fx_rate": fx_rate,
        "volume": volume,
        "target_margin_percent": target_margin,
        "adjusted_margin_percent": adjusted_margin,
        "target_selling_price_inr": target_selling_price_inr,
        "profit_inr": profit_inr,
        "fx_impact_inr": fx_impact_inr,
        "logistics_impact_usd": logistics_impact_usd,
        "duty_impact_usd": duty_impact_usd,
        "total_duty_exposure_usd": total_duty_exposure_usd,
        "fta_savings_usd": fta_savings_usd,
        "duty_impact_percent": duty_impact_percent,
        "pass_through_rate": pass_through_rate
    }
