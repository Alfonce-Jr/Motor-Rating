import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Motor Quotation", layout="wide")

logo_path = "Company logo.png"

# Centered logo
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{logo_data}' width='300'>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("⚠️ Company logo not found. Please check the file path.")

st.markdown(
    "<h1 style='text-align: center; color: #002060;'>🚗 Motor Quotation</h1>",
    unsafe_allow_html=True
)

# ------------------------------
# SIDEBAR INPUTS
# ------------------------------
st.sidebar.header("Client Information")
client_name = st.sidebar.text_input("Client Name")
address = st.sidebar.text_input("Address")
occupation = st.sidebar.text_input("Occupation")
producer = st.sidebar.text_input("Producer Name")
location = st.sidebar.text_input("Location")
pin = st.sidebar.text_input("PIN")
email = st.sidebar.text_input("Email")
phone = st.sidebar.text_input("Phone")
policy_no = st.sidebar.text_input("Policy No")

# ------------------------------
# CALCULATION FUNCTIONS
# ------------------------------
high_risk_makes = [
    "Subaru", "Nissan", "Honda", "Mazda", "Volkswagen",
    "BMW", "Ford", "Porsche", "Volvo", "Audi", "Alfa Romeo", "Bentley"
]
toyota_high_risk_models = [
    "Probox", "Allion", "Wish", "Rush", "Noah", "Axio", "Fielder",
    "Premio", "Corolla", "Voxy", "Auris", "Mark X"
]

def calculate_private(make, model, sum_insured, excess, pvt):
    make = make.strip().title()
    model = model.strip().title()
    if make in high_risk_makes or (make == "Toyota" and model in toyota_high_risk_models):
        category = "High Risk"
    else:
        category = "Other"

    if "Rare" in model:
        base_premium = sum_insured * 0.05
    else:
        if category == "High Risk":
            if sum_insured <= 1_000_000:
                base_premium = max(sum_insured * 0.07, 50_000)
            elif sum_insured <= 1_500_000:
                base_premium = max(sum_insured * 0.05, 70_000)
            elif sum_insured <= 2_500_000:
                base_premium = max(sum_insured * 0.04, 75_000)
            else:
                base_premium = max(sum_insured * 0.03, 87_500)
        else:
            if sum_insured <= 1_000_000:
                base_premium = max(sum_insured * 0.07, 50_000)
            elif sum_insured <= 1_500_000:
                base_premium = max(sum_insured * 0.0475, 70_000)
            elif sum_insured <= 2_500_000:
                base_premium = max(sum_insured * 0.035, 71_250)
            else:
                base_premium = max(sum_insured * 0.03, 87_500)

    excess_premium = max(sum_insured * 0.0025, 6000) if excess else 0
    pvt_premium = max(sum_insured * 0.0025, 2500) if pvt else 0
    total_premium = base_premium + excess_premium + pvt_premium
    return category, base_premium, excess_premium, pvt_premium, total_premium

def calculate_commercial(subclass, cover, tonnage, sum_insured, unit_type, excess, pvt, pll, passengers):
    subclass = subclass.title()
    cover = cover.upper()

    if cover == "COMPREHENSIVE":
        if subclass == "Own Goods":
            base = max(sum_insured * 0.04, 30_000) if tonnage <= 3 else max(sum_insured * 0.045, 50_000)
            exc = max(sum_insured * 0.005, 10_000)
            pvt_amt = max(sum_insured * 0.003, 3_000)
        elif subclass == "General Cartage":
            base = max(sum_insured * 0.048, 100_000)
            exc = max(sum_insured * 0.005, 12_500)
            pvt_amt = max(sum_insured * 0.003, 3_000)
        elif subclass == "Institutional":
            base = max(sum_insured * 0.035, 50_000)
            exc = max(sum_insured * 0.005, 10_000)
            pvt_amt = max(sum_insured * 0.003, 3_000)
        elif subclass == "Psv":
            base = max(sum_insured * 0.055, 50_000)
            exc = max(sum_insured * 0.005, 10_500)
            pvt_amt = max(sum_insured * 0.003, 3_000)
        else:
            base = exc = pvt_amt = 0
    else:
        if subclass == "Own Goods":
            if tonnage <= 3:
                base = 12_000 if unit_type == "Single Unit" else 10_000
            elif tonnage <= 8:
                base = 15_000 if unit_type == "Single Unit" else 12_500
            else:
                base = 22_500 if unit_type == "Single Unit" else 18_000
        elif subclass == "General Cartage":
            if tonnage <= 8:
                base = 20_000 if unit_type == "Single Unit" else 15_000
            elif tonnage <= 20:
                base = 25_000 if unit_type == "Single Unit" else 20_000
            elif tonnage <= 30:
                base = 30_000 if unit_type == "Single Unit" else 25_000
            else:
                base = 25_000 if unit_type == "Single Unit" else 20_000
        else:
            base = 0
        exc = pvt_amt = 0

    pll_amt = 0
    if pll:
        if subclass == "Institutional":
            pll_amt = passengers * 250
        elif subclass == "Psv":
            pll_amt = passengers * 500

    total = base + (exc if excess else 0) + (pvt_amt if pvt else 0) + pll_amt
    return base, exc if excess else 0, pvt_amt if pvt else 0, pll_amt, total

# ------------------------------
# VEHICLE INPUTS
# ------------------------------
tab_private, tab_commercial = st.tabs(["Motor Private", "Motor Commercial"])
vehicles = []

# --- PRIVATE ---
with tab_private:
    num_private = st.number_input("Number of Private Vehicles", min_value=0, max_value=20, value=0)
    for i in range(num_private):
        st.subheader(f"Private Vehicle {i+1}")
        make = st.text_input("Make", key=f"make_priv_{i}")
        model = st.text_input("Model", key=f"model_priv_{i}")
        sum_insured = st.number_input("Sum Insured (KSh)", min_value=0.0, step=50000.0, key=f"sum_priv_{i}")
        excess = st.checkbox("Include Excess?", key=f"exc_priv_{i}")
        pvt = st.checkbox("Include PVT?", key=f"pvt_priv_{i}")

        category, base_premium, exc_prem, pvt_prem, total = calculate_private(make, model, sum_insured, excess, pvt)
        vehicles.append({
            "Type": "Private",
            "Make": make,
            "Model": model,
            "Sum Insured": sum_insured,
            "Premium": base_premium,
            "Excess": exc_prem,
            "PVT": pvt_prem,
            "Total": total
        })

# --- COMMERCIAL ---
with tab_commercial:
    num_com = st.number_input("Number of Commercial Vehicles", min_value=0, max_value=20, value=0)
    for i in range(num_com):
        st.subheader(f"Commercial Vehicle {i+1}")
        subclass = st.selectbox("Subclass", ["Own Goods", "General Cartage", "Institutional", "PSV"], key=f"subclass_{i}")
        cover = st.selectbox("Cover Type", ["Comprehensive", "TPO"], key=f"cover_{i}")
        tonnage = st.number_input("Tonnage", min_value=0.0, step=0.5, key=f"ton_{i}") if cover == "TPO" else 0.0
        unit_type = st.selectbox("Unit Type", ["Single Unit", "Fleet"], key=f"unit_{i}") if cover == "TPO" else None
        sum_insured = st.number_input("Sum Insured (KSh)", min_value=0.0, step=50000.0, key=f"sum_com_{i}") if cover == "Comprehensive" else 0.0
        excess = st.checkbox("Include Excess?", key=f"exc_com_{i}")
        pvt = st.checkbox("Include PVT?", key=f"pvt_com_{i}")

        pll = False
        if subclass not in ["Own Goods", "General Cartage"]:
            pll = st.checkbox("Include PLL?", key=f"pll_{i}")
            passengers = st.number_input("No of Passengers", min_value=0, step=1, key=f"pass_{i}") if pll else 0
        else:
            passengers = 0

        base, exc_prem, pvt_prem, pll_amt, total = calculate_commercial(
            subclass, cover, tonnage, sum_insured, unit_type, excess, pvt, pll, passengers
        )

        vehicles.append({
            "Type": "Commercial",
            "Subclass": subclass,
            "Cover": cover,
            "Tonnage": tonnage,
            "Unit Type": unit_type,
            "Sum Insured": sum_insured,
            "Premium": base,
            "Excess": exc_prem,
            "PVT": pvt_prem,
            "PLL": pll_amt,
            "Total": total
        })

# ------------------------------
# PDF GENERATION
# ------------------------------
if vehicles:
    # Create DataFrame
    df = pd.DataFrame(vehicles)

    # ---- Premium Summary Section ----
    st.subheader("Premium Summary")

    # Format numeric columns with commas, 0 dp, and currency
    money_cols = ["Sum Insured", "Premium", "Excess", "PVT", "PLL", "Total"]
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: f"KShs {float(x):,.0f}" if pd.notnull(x) and str(x).replace('.', '', 1).isdigit() else x
            )

    # Display formatted dataframe
    st.dataframe(df)

    # ---- PDF Generation ----
    if st.button("Generate Quote"):
        pdf_file = f"Quotation_{client_name.replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        elements = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='BlueTitle', fontSize=16, textColor=colors.HexColor("#002060"), alignment=1))
        styles.add(ParagraphStyle(name='NormalCenter', fontSize=10, alignment=1))
        styles.add(ParagraphStyle(name='BlueItalic', fontSize=10, textColor=colors.HexColor("#002060"), alignment=1, italic=True))
        styles.add(ParagraphStyle(name='BlueAddress', fontSize=9, textColor=colors.HexColor("#002060"), alignment=1))

        # --- HEADER ---
        if os.path.exists(logo_path):
            elements.append(RLImage(logo_path, width=250, height=80))
        elements.append(Paragraph("LIBERTY HOUSE - MAMLAKA ROAD", styles['BlueAddress']))
        elements.append(Paragraph("P.O BOX 30390 - 00100 GPO NAIROBI", styles['BlueAddress']))
        elements.append(Paragraph("Email: info@heritage.co.ke", styles['BlueAddress']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Premium Quotation</b>", styles['BlueTitle']))
        elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %b %Y')}", styles['Normal']))
        elements.append(Spacer(1, 15))

        # --- CLIENT INFO ---
        client_info = f"""
        <b>Client Name:</b> {client_name}<br/>
        <b>Address:</b> {address}<br/>
        <b>Occupation:</b> {occupation}<br/>
        <b>Producer:</b> {producer}<br/>
        <b>PIN:</b> {pin}<br/>
        <b>Email:</b> {email}<br/>
        <b>Phone:</b> {phone}<br/>
        """
        elements.append(Paragraph(client_info, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Replace NaN / None with "N/A"
        df = df.fillna("N/A")

        # Create numeric version for calculations
        df_numeric = pd.DataFrame(vehicles)
        if "Total" in df_numeric.columns:
            df_numeric["Total"] = pd.to_numeric(df_numeric["Total"], errors="coerce").fillna(0)

        grand_total = 0.0

        for vtype in ["Private", "Commercial"]:
            df_sub = df[df["Type"] == vtype]
            df_sub_numeric = df_numeric[df_numeric["Type"] == vtype]

            if not df_sub.empty:
                # Section title
                elements.append(Paragraph(f"Motor {vtype}", styles['BlueTitle']))
                elements.append(Spacer(1, 8))

                # Drop unnecessary columns
                df_sub = df_sub.drop(columns=["Type"], errors="ignore")
                if vtype == "Private":
                    drop_cols = ["Cover", "Rate", "Tonnage", "Unit Type", "Subclass", "PLL", "Passengers"]
                else:
                    drop_cols = ["Make", "Model", "Rate", "Passengers"]
                df_sub = df_sub.drop(columns=drop_cols, errors="ignore")

                # Reorder columns for Commercial
                if vtype == "Commercial":
                    preferred_order = [
                        "Subclass", "Cover", "Sum Insured", "Unit Type", "Tonnage",
                        "Premium", "Excess", "PVT", "PLL", "Total"
                    ]
                    df_sub = df_sub[[col for col in preferred_order if col in df_sub.columns]]

                # Prepare table
                data = [list(df_sub.columns)] + df_sub.values.tolist()
                h_align = 'CENTER' if vtype == "Private" else 'LEFT'
                table = Table(data, hAlign=h_align)

                # Table style
                style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#002060")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                ]

                for i in range(1, len(data)):
                    if i % 2 == 0:
                        style.append(('BACKGROUND', (0, i), (-1, i), colors.whitesmoke))

                table.setStyle(TableStyle(style))
                elements.append(table)
                elements.append(Spacer(1, 12))

                # Subtotal
                subtotal = df_sub_numeric["Total"].sum()
                grand_total += float(subtotal)

                # Total line
                elements.append(Paragraph(f"<b>Total: KShs {subtotal:,.0f}</b>", styles['Normal']))
                elements.append(Spacer(1, 20))

        # Grand total
        elements.append(Paragraph(f"<b>Grand Total: KShs {grand_total:,.0f}</b>", styles['BlueTitle']))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<i>Thank you for choosing Heritage Insurance Company.</i>", styles['BlueItalic']))

        # Build PDF
        doc.build(elements)

        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download Quotation", f, pdf_file, "application/pdf")

# Refresh
if st.button("🔄 Refresh App"):
    st.rerun()