import streamlit as st
import pandas as pd
import sqlite3
import io
import base64  # ઇમેજને બેઝ64 માં રૂપાંતરિત કરવા માટે જરૂરી
from datetime import datetime

# કોડની શરૂઆતમાં ઇમેજ લોડ કરવાનું ફંક્શન ઉમેરો
# તે ચેકના ફોટાને HTML માં વાપરવા માટે તેને ટેક્સ્ટ (Base64) માં ફેરવે છે.
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# તમારા ચેકના ફોટાનું નામ (જો તે app.py ની જ ફોલ્ડરમાં હોય)
cheque_image_file = 'image_0.png' 

try:
    cheque_bg_base64 = get_base64_of_bin_file(cheque_image_file)
except FileNotFoundError:
    # જો ફોટો ન મળે, તો ભૂલ બતાવવા માટે ખાલી સ્ટ્રિંગ
    cheque_bg_base64 = ""
    st.error(f"ચેકનો ફોટો '{cheque_image_file}' મળ્યો નથી. કૃપા કરીને તપાસો કે તે app.py ની સાથે તે જ ફોલ્ડરમાં છે.")

# --- DATABASE SETUP ---
# ... (તમારો ડેટાબેઝ સેટઅપ કોડ અહીં ચાલુ રહેશે, તેમાં કોઈ ફેરફાર નથી)
conn = sqlite3.connect('cheque_master.db', check_same_thread=False)
c = conn.cursor()

# Tables banavva
c.execute('''CREATE TABLE IF NOT EXISTS bank_profiles 
             (name TEXT PRIMARY KEY, date_x REAL, date_y REAL, payee_x REAL, payee_y REAL, 
              amt_num_x REAL, amt_num_y REAL, amt_word_x REAL, amt_word_y REAL, orientation TEXT)''')
c.execute('CREATE TABLE IF NOT EXISTS parties (name TEXT PRIMARY KEY)')
c.execute('CREATE TABLE IF NOT EXISTS history (date TEXT, party TEXT, amount REAL)')
conn.commit()
# ...

# --- APP CONFIG ---
st.set_page_config(page_title="Universal Cheque Printer", layout="wide")
st.title("🏦 Universal Cheque Printing System")

# --- પ્રિન્ટિંગ માટે CSS વિભાગ (આ નવો ઉમેરો છે) ---
# આ CSS તમારા પ્રિન્ટઆઉટ માંથી બેકગ્રાઉન્ડ ઇમેજ અને કોઇપણ બટન વગેરેને છુપાવી દેશે.
# ખાલી ડેટા જ પ્રિન્ટ થશે.
# @media print ની મદદથી પેજની સાઈઝ પણ તમારા 93x203mm મુજબ સેટ કરો.
st.markdown("""
<style>
@media print {
    /* આખા પેજનું સેટિંગ - કોરા ચેકની સાઈઝ મુજબ */
    @page {
        size: 203mm 93mm; /* ચેકની width 203mm અને height 93mm */
        margin: 0mm; /* કોઈ માર્જિન નહિ, પોઝિશન સ્લાઈડરથી નક્કી થશે */
    }

    /* ચેક કન્ટેનરના કન્ટેન્ટ સિવાયનું બધું છુપાવો */
    body * {
        visibility: hidden;
    }
    
    /* પ્રિન્ટ પ્રિવ્યૂ કન્ટેનર અને તેના કન્ટેન્ટને બતાવો */
    .printable-cheque-area, .printable-cheque-area * {
        visibility: visible;
    }
    
    /* કન્ટેનરને પ્રિન્ટ પેજના કોર્નર પર ફિક્સ કરો */
    .printable-cheque-area {
        position: absolute;
        left: 0;
        top: 0;
        border: none !important; /* Tuteli line print ma na aave */
        background-image: none !important; /* ચેકનો ફોટો પ્રિન્ટમાં ન આવે */
    }
}
</style>
""", unsafe_allow_html=True)

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
    
    # "Save & Print" બટન હવે ખાલી સેવ કરશે અને પ્રિન્ટ બટન પ્રિવ્યૂ માં આવશે.
    if st.button("💾 Save Cheque"):
        if final_payee and amt_num > 0:
            c.execute('INSERT OR IGNORE INTO parties VALUES (?)', (final_payee,))
            c.execute('INSERT INTO history VALUES (?, ?, ?)', (chq_date.strftime('%Y-%m-%d'), final_payee, amt_num))
            conn.commit()
            st.success(f"Record for {final_payee} saved. Scroll down to preview and print.")
        else:
            st.warning("Maherbani kari ne Naam ane Amount lakho.")

with col2:
    st.subheader("⚙️ Visual Adjustment")
    # Real-time Sliders
    new_d_x = st.slider("Date X (Horizontal)", 0, 600, int(d_x))
    new_d_y = st.slider("Date Y (Vertical)", 0, 250, int(d_y))
    new_p_x = st.slider("Payee Name X", 0, 600, int(p_x))
    new_p_y = st.slider("Payee Name Y", 0, 250, int(p_y))
    
    # તમારા દ્વારા પૂરા પાડવામાં આવેલ વધારાના સ્લાઈડર્સ
    new_an_x = st.slider("Amount Number X", 0, 600, int(an_x))
    new_an_y = st.slider("Amount Number Y", 0, 250, int(an_y))
    new_aw_x = st.slider("Amount Word X", 0, 600, int(aw_x))
    new_aw_y = st.slider("Amount Word Y", 0, 250, int(aw_y))
    
    new_orient = st.radio("Orientation", ["Landscape", "Portrait"], index=0 if orient=="Landscape" else 1)

    if st.button("💾 Save Margins for " + selected_profile if selected_profile != "Navi Profile Banavo" else "Save"):
        if selected_profile != "Navi Profile Banavo":
            c.execute('UPDATE bank_profiles SET date_x=?, date_y=?, payee_x=?, payee_y=?, amt_num_x=?, amt_num_y=?, amt_word_x=?, amt_word_y=?, orientation=? WHERE name=?', 
                      (new_d_x, new_d_y, new_p_x, new_p_y, new_an_x, new_an_y, new_aw_x, new_aw_y, new_orient, selected_profile))
            conn.commit()
            st.toast("Settings Saved! ✅")

# --- VISUAL PREVIEW BOX ---
st.divider()
st.subheader("👀 Print Preview (Real-time)")

# કોડને પ્રિન્ટિંગ માટે સુધારેલા CSS ક્લાસ "printable-cheque-area" સાથે અપડેટ કરો
preview_w, preview_h = (600, 250) if new_orient == "Landscape" else (250, 600)

# જો ફોટો મળ્યો હોય, તો તેને બેકગ્રાઉન્ડ તરીકે વાપરો
if cheque_bg_base64:
    bg_style = f"background-image: url(data:image/png;base64,{cheque_bg_base64}); background-size: cover; background-repeat: no-repeat;"
else:
    bg_style = "background-color: white;" # Default blank white if no image found

# તમારા જૂના HTML માર્કડાઉનને આ સુધારેલા કોડથી બદલો
st.markdown(f"""
<div class="printable-cheque-area" style="border: 2px dashed #bbb; width: {preview_w}px; height: {preview_h}px; position: relative; {bg_style} margin: auto;">
    
    <div style="position: absolute; left: {new_d_x}px; top: {250 - new_d_y if new_orient=='Landscape' else 600 - new_d_y}px; color: blue; font-family: monospace; font-weight: bold;">{chq_date.strftime('%d %m %Y')}</div>
    
    <div style="position: absolute; left: {new_p_x}px; top: {250 - new_p_y if new_orient=='Landscape' else 600 - new_p_y}px; color: black; font-size: 18px; font-weight: bold;">{final_payee.upper()}</div>
    
    <div style="position: absolute; left: {new_an_x}px; top: {250 - new_an_y if new_orient=='Landscape' else 600 - new_an_y}px; color: black; font-size: 16px;">
        {'₹ {:,}'.format(amt_num) if amt_num > 0 else ''}
    </div>
    
    <div style="position: absolute; left: {new_aw_x}px; top: {250 - new_aw_y if new_orient=='Landscape' else 600 - new_aw_y}px; color: black; font-size: 14px; max-width: 350px; line-height: 1.2;">
        {amt_word.upper()}
    </div>
    
    <div style="position: absolute; left: 10px; top: 10px; border-bottom: 2px solid black; border-right: 2px solid black; padding: 5px; display: {'block' if is_ac_payee else 'none'}; transform: rotate(-45deg);">A/C PAYEE</div>
</div>
""", unsafe_allow_html=True)

# નવો "Print Cheque Now" વિભાગ
st.info("💡 જ્યારે તમે પ્રિન્ટ આપવા માંગો ત્યારે તમારા બ્રાઉઝરના 'Print' (Ctrl + P) ફંક્શનનો ઉપયોગ કરો. CSS ફેરફારો આપોઆપ બેકગ્રાઉન્ડને છુપાવી દેશે.")
