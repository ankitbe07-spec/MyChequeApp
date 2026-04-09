import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('cheque_master.db', check_same_thread=False)
c = conn.cursor()

# Tables banavva
c.execute('''CREATE TABLE IF NOT EXISTS bank_profiles 
             (name TEXT PRIMARY KEY, date_x REAL, date_y REAL, payee_x REAL, payee_y REAL, 
              amt_num_x REAL, amt_num_y REAL, amt_word_x REAL, amt_word_y REAL, orientation TEXT)''')
c.execute('CREATE TABLE IF NOT EXISTS parties (name TEXT PRIMARY KEY)')
c.execute('CREATE TABLE IF NOT EXISTS history (date TEXT, party TEXT, amount REAL)')
conn.commit()

# --- APP CONFIG ---
st.set_page_config(page_title="Universal Cheque Printer", layout="wide")
st.title("🏦 Universal Cheque Printing System")

# --- SIDEBAR: BANK PROFILES ---
st.sidebar.header("🏦 Bank Profile Settings")
profiles = [row[0] for row in c.execute('SELECT name FROM bank_profiles').fetchall()]
selected_profile = st.sidebar.selectbox("Bank Profile Select Karo", ["Navi Profile Banavo"] + profiles)

# Default Values (Jo navi profile hoy to aa vapraase)
p_name, d_x, d_y, p_x, p_y, an_x, an_y, aw_x, aw_y, orient = ("", 450, 210, 70, 170, 480, 135, 70, 140, "Landscape")

if selected_profile == "Navi Profile Banavo":
    new_profile_name = st.sidebar.text_input("Bank nu Naam (e.g. HDFC_Current)")
    if st.sidebar.button("Profile Create Karo"):
        if new_profile_name:
            c.execute('INSERT OR IGNORE INTO bank_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                      (new_profile_name, 450, 210, 70, 170, 480, 135, 70, 140, "Landscape"))
            conn.commit()
            st.success(f"{new_profile_name} Profile Bani Gai! Have Dropdown mathi select karo.")
            st.rerun()
else:
    # Database mathi existing profile no data levu
    data = c.execute('SELECT * FROM bank_profiles WHERE name=?', (selected_profile,)).fetchone()
    if data:
        p_name, d_x, d_y, p_x, p_y, an_x, an_y, aw_x, aw_y, orient = data

# --- MAIN UI: DATA ENTRY ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Cheque Details")
    
    # Auto-suggest Party Name
    all_parties = [row[0] for row in c.execute('SELECT name FROM parties').fetchall()]
    payee_choice = st.selectbox("Payee Name (Select from History)", [""] + all_parties)
    new_payee = st.text_input("Navu Naam (Jo List ma na hoy to)")
    final_payee = new_payee if new_payee else payee_choice

    amt_num = st.number_input("Amount (In Numbers)", min_value=0.0, step=1.0)
    amt_word = st.text_input("Amount (In Words)")
    chq_date = st.date_input("Date", datetime.now())
    is_ac_payee = st.checkbox("A/c Payee (Cross Cheque)")
    
    if st.button("🖨️ Save & Print"):
        if final_payee and amt_num > 0:
            c.execute('INSERT OR IGNORE INTO parties VALUES (?)', (final_payee,))
            c.execute('INSERT INTO history VALUES (?, ?, ?)', (chq_date.strftime('%Y-%m-%d'), final_payee, amt_num))
            conn.commit()
            st.success(f"Cheque for {final_payee} is ready to print!")
        else:
            st.warning("Maherbani kari ne Naam ane Amount lakho.")

with col2:
    st.subheader("⚙️ Visual Adjustment")
    # Real-time Sliders
    new_d_x = st.slider("Date X (Horizontal)", 0, 600, int(d_x))
    new_d_y = st.slider("Date Y (Vertical)", 0, 250, int(d_y))
    new_p_x = st.slider("Payee Name X", 0, 600, int(p_x))
    new_p_y = st.slider("Payee Name Y", 0, 250, int(p_y))
    new_orient = st.radio("Orientation", ["Landscape", "Portrait"], index=0 if orient=="Landscape" else 1)

    if st.button("💾 Save Margins for " + selected_profile if selected_profile != "Navi Profile Banavo" else "Save"):
        if selected_profile != "Navi Profile Banavo":
            c.execute('UPDATE bank_profiles SET date_x=?, date_y=?, payee_x=?, payee_y=?, orientation=? WHERE name=?', 
                      (new_d_x, new_d_y, new_p_x, new_p_y, new_orient, selected_profile))
            conn.commit()
            st.toast("Settings Saved! ✅")

# --- VISUAL PREVIEW BOX ---
st.divider()
st.subheader("👀 Print Preview (Real-time)")
preview_w, preview_h = (600, 250) if new_orient == "Landscape" else (250, 600)

st.markdown(f"""
<div style="border: 2px dashed #bbb; width: {preview_w}px; height: {preview_h}px; position: relative; background-color: white; margin: auto;">
    <div style="position: absolute; left: {new_d_x}px; top: {250 - new_d_y if new_orient=='Landscape' else 600 - new_d_y}px; color: blue; font-family: monospace; font-weight: bold;">{chq_date.strftime('%d %m %Y')}</div>
    <div style="position: absolute; left: {new_p_x}px; top: {250 - new_p_y if new_orient=='Landscape' else 600 - new_p_y}px; color: black; font-size: 18px; font-weight: bold;">{final_payee.upper()}</div>
    <div style="position: absolute; left: 10px; top: 10px; border-bottom: 2px solid black; border-right: 2px solid black; padding: 5px; display: {'block' if is_ac_payee else 'none'}; transform: rotate(-45deg);">A/C PAYEE</div>
</div>
""", unsafe_allow_html=True)
