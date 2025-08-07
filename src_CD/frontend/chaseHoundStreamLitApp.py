"""
ChaseHound Streamlit App
========================

Interface graphique minimaliste permettant :
1. La saisie d'une configuration ChaseHound
2. L'envoi de cette configuration vers le backend (endpoint /run)
3. L'affichage des résultats retournés (CSV -> table)

Lancement :
    streamlit run src_CD/chaseHoundStreamLitApp.py
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Any

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Backend URL configuration - Support for remote access
import os

# Allow configuration via environment variable for production deployment
BACKEND_HOST = os.getenv("CHASEHOUND_BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("CHASEHOUND_BACKEND_PORT", "8000")
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
RUN_ENDPOINT = f"{BACKEND_URL}/run"

default_start = date(datetime.now().year - 1, 1, 1)
default_end = datetime.now().date()

# ---------------------------------------------------------------------------
# Configuration form
# ---------------------------------------------------------------------------

st.title("🐾 ChaseHound – Stock Screener")

with st.form("ch_config"):
    # Basic parameters
    st.subheader("📅 Basic Parameters")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=default_start)
    with col2:
        end_date = st.date_input("End date", value=default_end)

    # Fundamental filters
    st.subheader("💰 Fundamental Filters")
    col1, col2 = st.columns(2)
    with col1:
        lowest_price = st.number_input("Lowest price", value=2.0, min_value=0.0, step=0.1)
        lowest_market_gap = st.number_input("Lowest market gap", value=50000000.0, min_value=0.0, step=1000000.0, format="%.0f")
        lowest_avg_turnover = st.number_input("Lowest avg turnover", value=20000000.0, min_value=0.0, step=1000000.0, format="%.0f")
    with col2:
        lowest_avg_turnover_days = st.number_input("Lowest avg turnover days", value=20, min_value=1, step=1)
        latest_report_date_days = st.number_input("Latest report date days", value=120, min_value=1, step=1)

    # Volatility filters - Turnover
    st.subheader("📈 Volatility Filters - Turnover")
    col1, col2, col3 = st.columns(3)
    with col1:
        turnover_spike_threshold = st.number_input("Turnover spike threshold", value=1.05, step=0.01)
    with col2:
        turnover_short_term_days = st.number_input("Turnover short term days", value=5, min_value=1, step=1)
    with col3:
        turnover_long_term_days = st.number_input("Turnover long term days", value=60, min_value=1, step=1)

    # Volatility filters - ATR
    st.subheader("📊 Volatility Filters - ATR")
    col1, col2, col3 = st.columns(3)
    with col1:
        atr_spike_threshold = st.number_input("ATR spike threshold", value=1.2, step=0.01)
    with col2:
        atr_short_term_days = st.number_input("ATR short term days", value=5, min_value=1, step=1)
    with col3:
        atr_long_term_days = st.number_input("ATR long term days", value=20, min_value=1, step=1)

    # Volatility filters - Price Std
    st.subheader("📉 Volatility Filters - Price Std")
    col1, col2, col3 = st.columns(3)
    with col1:
        price_std_spike_threshold = st.number_input("Price Std spike threshold", value=1.1, step=0.01)
    with col2:
        price_std_short_term_days = st.number_input("Price Std short term days", value=5, min_value=1, step=1)
    with col3:
        price_std_long_term_days = st.number_input("Price Std long term days", value=60, min_value=1, step=1)

    # Volatility filters passing threshold
    volatility_filters_passing_threshold = st.number_input(
        "Volatility filters passing threshold", value=2, min_value=0, step=1, format="%d"
    )

    # Right-side filters - Breakout detection
    st.subheader("🚀 Right-side Filters - Breakout Detection")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        breakout_detection_days_lookback = st.number_input("Breakout detection days lookback", value=20, min_value=1, step=1)
    with col2:
        breakout_detection_price_ratio_threshold = st.number_input("Breakout detection price ratio threshold", value=0.05, step=0.01)
    with col3:
        breakout_detection_ma_tolerance = st.number_input("Breakout detection MA tolerance", value=1.0, step=0.01)
    with col4:
        breakout_detection_volume_augmentation_ratio_threshold = st.number_input("Breakout detection volume augmentation ratio threshold", value=1.5, step=0.1)

    # Right-side filters - Structure confirmation
    st.subheader("🏗️ Right-side Filters - Structure Confirmation")
    col1, col2 = st.columns(2)
    with col1:
        structure_confirmation_days_lookback = st.number_input("Structure confirmation days lookback", value=20, min_value=1, step=1)
    with col2:
        structure_confirmation_ma_tolerance = st.number_input("Structure confirmation MA tolerance", value=0.97, step=0.01)

    submitted = st.form_submit_button("🚀 Launch")

# ---------------------------------------------------------------------------
# Submission & results display
# ---------------------------------------------------------------------------

if submitted:
    with st.status("Sending configuration..."):
        payload: Dict[str, Any] = {
            # Basic parameters
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            
            # Fundamental filters
            "lowest_price": lowest_price,
            "lowest_market_gap": lowest_market_gap,
            "lowest_avg_turnover": lowest_avg_turnover,
            "lowest_avg_turnover_days": int(lowest_avg_turnover_days),
            "latest_report_date_days": int(latest_report_date_days),
            
            # Volatility filters - Turnover
            "turnoverSpikeThreshold": turnover_spike_threshold,
            "turnoverShortTermDays": int(turnover_short_term_days),
            "turnoverLongTermDays": int(turnover_long_term_days),
            
            # Volatility filters - ATR
            "atrSpikeThreshold": atr_spike_threshold,
            "atrShortTermDays": int(atr_short_term_days),
            "atrLongTermDays": int(atr_long_term_days),
            
            # Volatility filters - Price Std
            "priceStdSpikeThreshold": price_std_spike_threshold,
            "priceStdShortTermDays": int(price_std_short_term_days),
            "priceStdLongTermDays": int(price_std_long_term_days),
            
            # Volatility filters passing threshold
            "volatilityFiltersPassingThreshold": int(volatility_filters_passing_threshold),
            
            # Right-side filters - Breakout detection
            "breakoutDetectionDaysLookback": int(breakout_detection_days_lookback),
            "breakoutDetectionPriceRatioThreshold": breakout_detection_price_ratio_threshold,
            "breakoutDetectionMaTolerance": breakout_detection_ma_tolerance,
            "breakoutDetectionVolumeAugmentationRatioThreshold": breakout_detection_volume_augmentation_ratio_threshold,
            
            # Right-side filters - Structure confirmation
            "structureConfirmationDaysLookback": int(structure_confirmation_days_lookback),
            "structureConfirmationMaTolerance": structure_confirmation_ma_tolerance,
        }

        try:
            resp = requests.post(RUN_ENDPOINT, json=payload, timeout=None)
        except requests.exceptions.RequestException as exc:
            st.error(f"Backend connection error: {exc}")
            st.stop()

    if resp.status_code != 200:
        st.error(f"Backend error {resp.status_code}: {resp.text}")
        st.stop()

    data = resp.json()
    st.success(
        f"Completed in {data.get('execution_time', '?')} s – "
        f"{data.get('results_count', 0)} records"
    )

    # List of results_*.csv files
    results = data.get("results", [])
    if not results:
        st.info("No result files returned.")
        st.stop()

    filenames = [r["file"] for r in results]
    sel_file = st.selectbox("File to display", filenames)
    recs = next((r.get("records", []) for r in results if r["file"] == sel_file), [])

    if recs:
        st.dataframe(pd.DataFrame(recs), use_container_width=True)
    else:
        st.warning("This file contains no data (or an error occurred).")

st.caption("Backend: " + BACKEND_URL) 