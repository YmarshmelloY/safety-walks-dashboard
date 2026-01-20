import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="BC Safety Walks Dashboard", layout="wide")
st.title("British Columbia Safety Walks Dashboard (Non-ESS Units)")
st.markdown("""
This dashboard analyzes your exported Excel file for safety walks compliance.  
- Excludes all **06-ESS Support Services** units  
- Current period target is configurable (default: 3 for P3)  
- Shows units behind target, grouped by District Manager  
- Includes interactive pie charts for progress  
""")

# Sidebar inputs
st.sidebar.header("Settings")
uploaded_file = st.sidebar.file_uploader("Upload your Excel export (sheet: Export)", type=["xlsx"])
current_period = st.sidebar.number_input("Current Period (target walks per unit)", min_value=1, max_value=12, value=3)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Export")

        # Clean and process data
        df['Walks_YTD'] = pd.to_numeric(df['# of Safety Walks Completed YTD'], errors='coerce').fillna(0).astype(int)
        df = df[df['Unit # - Unit Name'].notna()]
        df = df[~df['Sector Name'].str.startswith('06-ESS', na=False)]

        if df.empty:
            st.warning("No non-ESS units found in the upload.")
            st.stop()

        # Group by District
        districts = sorted(
            df['District'].unique(),
            key=lambda x: x.split('-')[-1].strip() if pd.notna(x) and '-' in str(x) else str(x)
        )

        # Overall summary
        total_units = len(df)
        total_target = total_units * current_period
        total_actual = df['Walks_YTD'].sum()

        st.header(f"Overall Summary (All Non-ESS Units)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Units", total_units)
        col2.metric("Target Walks", total_target)
        col3.metric("Actual Walks Completed", total_actual)
        col4.metric("Compliance %", f"{(total_actual / total_target * 100):.1f}%")

        # Overall pie chart
        completed_overall = min(total_actual, total_target)
        remaining_overall = max(total_target - total_actual, 0)
        excess = max(total_actual - total_target, 0)

        fig_overall, ax = plt.subplots(figsize=(6, 6))
        if excess > 0:
            ax.pie([completed_overall, excess], labels=['On Target', 'Excess'], autopct='%1.1f%%',
                   colors=['#2E8B57', '#90EE90'], startangle=90)
            ax.set_title(f"Overall Progress\n({total_actual}/{total_target} walks, +{excess} excess)")
        else:
            ax.pie([completed_overall, remaining_overall], labels=['Completed', 'Remaining'], autopct='%1.1f%%',
                   colors=['#2E8B57', '#DC143C'], startangle=90)
            ax.set_title(f"Overall Progress\n({total_actual}/{total_target} walks)")
        st.pyplot(fig_overall)

        st.markdown("---")

        # Per District Manager sections
        st.header("District Manager Breakdown")
        for district in districts:
            group = df[df['District'] == district]
            dm_name = district.split('-')[-1].strip() if '-' in district else district
            num_units = len(group)
            target = num_units * current_period
            actual = group['Walks_YTD'].sum()

            with st.expander(f"{district} — {num_units} units | Target: {target} walks | Actual: {actual} walks", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.metric("Units", num_units)
                col2.metric("Target", target)
                col3.metric("Actual", actual)

                behind = group[group['Walks_YTD'] < current_period][['Unit # - Unit Name', 'Unit Type', 'Walks_YTD']]
                behind = behind.sort_values('Walks_YTD').rename(columns={'Walks_YTD': f'Walks YTD (<{current_period})'})

                if not behind.empty:
                    st.subheader("Units Behind Target")
                    st.dataframe(behind, use_container_width=True, hide_index=True)
                else:
                    st.success("🎉 All units in this district are on or above target!")

                # District pie chart
                completed = min(actual, target)
                remaining = max(target - actual, 0)
                excess_dm = max(actual - target, 0)

                fig, ax = plt.subplots(figsize=(5, 5))
                if excess_dm > 0:
                    ax.pie([completed, excess_dm], labels=['On Target', 'Excess'], autopct='%1.1f%%',
                           colors=['#2E8B57', '#90EE90'], startangle=90)
                    ax.set_title(f"{dm_name}\n({actual}/{target} walks, +{excess_dm} excess)")
                else:
                    ax.pie([completed, remaining], labels=['Completed', 'Remaining'], autopct='%1.1f%%',
                           colors=['#2E8B57', '#DC143C'], startangle=90)
                    ax.set_title(f"{dm_name}\n({actual}/{target} walks)")
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload your Excel export file to begin.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("**How to share with your team**")
st.sidebar.markdown("""
1. Save this as `app.py`  
2. Install: `pip install streamlit pandas matplotlib openpyxl`  
3. Run locally: `streamlit run app.py`  
4. Share publicly: Deploy free on [Streamlit Community Cloud](https://streamlit.io/cloud) (connect GitHub repo)  
""")