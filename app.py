import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
from datetime import datetime

# --- NUMBER TO WORDS FUNCTION ---
def number_to_words(n):
    if n == 0: 
        return ""
    words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', 
             11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', 15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', 19: 'Nineteen', 
             20: 'Twenty', 30: 'Thirty', 40: 'Forty', 50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', 90: 'Ninety'}
    
    def get_words(num):
        if num == 0: return ""
        elif num < 20: return words[num] + " "
        elif num < 100: return words[num // 10 * 10] + " " + get_words(num % 10)
        elif num < 1000: return words[num // 100] + " Hundred " + get_words(num % 100)
        elif num < 100000: return get_words(num // 1000) + " Thousand " + get_words(num % 1000)
        elif num < 10000000: return get_words(num // 100000) + " Lakh " + get_words(num % 100000)
        else: return get_words(num // 10000000) + " Crore " + get_words(num % 10000000)
        
    return get_words(int(n)).strip() + " Only"

# --- DATABASE SETUP ---
conn = sqlite3.connect('cheque_master.db', check_same_thread=False)
c = conn.cursor()

# Tables banavva
c.execute('''CREATE TABLE IF NOT EXISTS bank_profiles 
             (name TEXT PRIMARY KEY, date_x REAL, date_y REAL, payee_x REAL, payee_y REAL, 
              amt_num_x REAL, amt_num_y REAL, amt_word_x REAL, amt_word_y REAL, orientation TEXT)''')

# 💡 NAVU: Juna database ma navi columns add karva mate (Error aave to ignore karshe)
new_columns = [
    ("f_family", "TEXT", "'Arial'"), ("f_size_d", "INTEGER", "16"), 
    ("f_size_p", "INTEGER", "18"), ("f_size_an", "INTEGER", "16"), ("f_size_aw", "INTEGER", "14")
]
for col_name, col_type, default_val in new_columns:
    try:
        c.execute(f'ALTER TABLE bank_profiles ADD COLUMN {col_name} {col_type} DEFAULT {default_val}')
    except sqlite3.OperationalError:
        pass # Column pehlathi j che

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

# Default Values 
p_name, d_x, d_y, p_x, p_y, an_x, an_y, aw_x, aw_y, orient = ("", 450, 210, 70, 170, 480, 135, 70, 140, "Landscape")
f_fam, fs_d, fs_p, fs_an, fs_aw = ("Arial", 16, 18, 16, 14)

if selected_profile == "Navi Profile Banavo":
    new_profile_name = st.sidebar.text_input("Bank nu Naam (e.g. HDFC_Current)")
    if st.sidebar.button("Profile Create Karo"):
        if new_profile_name:
            c.execute('''INSERT OR IGNORE INTO bank_profiles 
                         (name, date_x, date_y, payee_x, payee_y, amt_num_x, amt_num_y, amt_word_x, amt_word_y, orientation, f_family, f_size_d, f_size_p, f_size_an, f_size_aw) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                      (new_profile_name, 450, 210, 70, 170, 480, 135, 70, 140, "Landscape", "Arial", 16, 18, 16, 14))
            conn.commit()
            st.success(f"{new_profile_name} Profile Bani Gai! Have Dropdown mathi select karo.")
            st.rerun()
else:
    # Database mathi existing profile no data levu
    data = c.execute('SELECT * FROM bank_profiles WHERE name=?', (selected_profile,)).fetchone()
    if data:
        p_name, d_x, d_y, p_x, p_y, an_x, an_y, aw_x, aw_y, orient, f_fam, fs_d, fs_p, fs_an, fs_aw = data

# --- MAIN UI: DATA ENTRY ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Cheque Details")
    all_parties = [row[0] for row in c.execute('SELECT name FROM parties').fetchall()]
    payee_choice = st.selectbox("Payee Name (Select from History)", [""] + all_parties)
    new_payee = st.text_input("Navu Naam (Jo List ma na hoy to)")
    final_payee = new_payee if new_payee else payee_choice

    amt_num = st.number_input("Amount (In Numbers)", min_value=0.0, step=1.0)
    auto_word = number_to_words(amt_num) if amt_num > 0 else ""
    amt_word = st.text_input("Amount (In Words)", value=auto_word)
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
    st.subheader("⚙️ Visual & Font Adjustment")
    
    # --- FONT SETTINGS ---
    st.markdown("**Font Style & Size Settings:**")
    font_options = ["Arial", "Verdana", "Times New Roman", "Courier New", "Georgia", "Tahoma"]
    new_f_fam = st.selectbox("Font Type", font_options, index=font_options.index(f_fam) if f_fam in font_options else 0)
    
    c1, c2, c3, c4 = st.columns(4)
    new_fs_d = c1.number_input("Date Size", min_value=8, max_value=40, value=fs_d)
    new_fs_p = c2.number_input("Payee Size", min_value=8, max_value=40, value=fs_p)
    new_fs_an = c3.number_input("Num Size", min_value=8, max_value=40, value=fs_an)
    new_fs_aw = c4.number_input("Word Size", min_value=8, max_value=40, value=fs_aw)
    
    st.markdown("---")
    
    # --- MARGIN SETTINGS ---
    c5, c6 = st.columns(2)
    with c5:
        new_d_x = st.slider("Date X", 0, 600, int(d_x))
        new_p_x = st.slider("Payee Name X", 0, 600, int(p_x))
        new_an_x = st.slider("Amount Number X", 0, 600, int(an_x))
        new_aw_x = st.slider("Amount Word X", 0, 600, int(aw_x))
    with c6:
        new_d_y = st.slider("Date Y", 0, 250, int(d_y))
        new_p_y = st.slider("Payee Name Y", 0, 250, int(p_y))
        new_an_y = st.slider("Amount Number Y", 0, 250, int(an_y))
        new_aw_y = st.slider("Amount Word Y", 0, 250, int(aw_y))
        
    new_orient = st.radio("Orientation", ["Landscape", "Portrait"], index=0 if orient=="Landscape" else 1, horizontal=True)

    if st.button("💾 Save Settings for " + selected_profile if selected_profile != "Navi Profile Banavo" else "Save"):
        if selected_profile != "Navi Profile Banavo":
            c.execute('''UPDATE bank_profiles 
                         SET date_x=?, date_y=?, payee_x=?, payee_y=?, 
                             amt_num_x=?, amt_num_y=?, amt_word_x=?, amt_word_y=?, orientation=?,
                             f_family=?, f_size_d=?, f_size_p=?, f_size_an=?, f_size_aw=?
                         WHERE name=?''', 
                      (new_d_x, new_d_y, new_p_x, new_p_y, new_an_x, new_an_y, new_aw_x, new_aw_y, new_orient, 
                       new_f_fam, new_fs_d, new_fs_p, new_fs_an, new_fs_aw, selected_profile))
            conn.commit()
            st.toast("Settings Saved! ✅")

# --- VISUAL PREVIEW BOX ---
st.divider()
st.subheader("👀 Print Preview (Drag & Drop)")
st.info("💡 **TIPS:** Tame preview ma text ne drag kari shaksho. Drag karya pachi upar khuna ma nava number aavse, ae number tame upar slider ma nakhine save kari sako cho.")

preview_w, preview_h = (600, 250) if new_orient == "Landscape" else (250, 600)

display_payee = final_payee.upper() if final_payee else "SAMPLE PAYEE NAME"
display_amt_num = f"<b>₹ {int(amt_num)}/-</b>" if amt_num > 0 else "<b style='color:gray;'>₹ 10000/- (Sample)</b>"
display_amt_word = amt_word if amt_word else "<span style='color:gray;'>Ten Thousand Only (Sample)</span>"

# HTML code ma Drag & Drop Javascript add karyo che
html_code = f"""
<div id="cheque_box" style="border: 2px dashed #bbb; width: {preview_w}px; height: {preview_h}px; position: relative; background-color: white; margin: auto; overflow: hidden; font-family: '{new_f_fam}', sans-serif;">
    
    <div id="coord_box" style="position:absolute; top:5px; right:5px; background:#fff3cd; border:1px solid #ffeeba; padding:5px; font-size:12px; font-family:sans-serif; display:none; z-index:1000; color:#856404; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
        Dragging...
    </div>

    <div id="drag_date" style="position: absolute; left: {new_d_x}px; top: {250 - new_d_y if new_orient=='Landscape' else 600 - new_d_y}px; color: blue; font-family: 'Courier New', monospace; font-weight: bold; font-size: {new_fs_d}px; cursor: grab; user-select: none;">{chq_date.strftime('%d %m %Y')}</div>
    
    <div id="drag_payee" style="position: absolute; left: {new_p_x}px; top: {250 - new_p_y if new_orient=='Landscape' else 600 - new_p_y}px; color: black; font-size: {new_fs_p}px; font-weight: bold; cursor: grab; user-select: none; white-space: nowrap;">{display_payee}</div>
    
    <div id="drag_amt_num" style="position: absolute; left: {new_an_x}px; top: {250 - new_an_y if new_orient=='Landscape' else 600 - new_an_y}px; color: black; font-size: {new_fs_an}px; cursor: grab; user-select: none; white-space: nowrap;">{display_amt_num}</div>
    
    <div id="drag_amt_word" style="position: absolute; left: {new_aw_x}px; top: {250 - new_aw_y if new_orient=='Landscape' else 600 - new_aw_y}px; color: black; font-size: {new_fs_aw}px; width: 350px; line-height: 1.2; cursor: grab; user-select: none;">{display_amt_word}</div>
    
    <div style="position: absolute; left: 10px; top: 10px; border-bottom: 2px solid black; border-right: 2px solid black; padding: 5px; font-size: 14px; display: {'block' if is_ac_payee else 'none'}; transform: rotate(-45deg);">A/C PAYEE</div>
</div>

<script>
function makeDraggable(elementId, labelName) {{
    var elmnt = document.getElementById(elementId);
    var coordBox = document.getElementById("coord_box");
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    var containerHeight = {preview_h};

    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {{
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
        elmnt.style.cursor = "grabbing";
    }}

    function elementDrag(e) {{
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
        
        // Calculate Streamlit coordinate logic (Bottom-Up Y Axis)
        var newX = elmnt.offsetLeft;
        var newY = containerHeight - elmnt.offsetTop;
        
        coordBox.style.display = "block";
        coordBox.innerHTML = "<b>📌 " + labelName + "</b><br>X Slider: <b>" + newX + "</b><br>Y Slider: <b>" + newY + "</b>";
    }}

    function closeDragElement() {{
        document.onmouseup = null;
        document.onmousemove = null;
        elmnt.style.cursor = "grab";
    }}
}}

makeDraggable("drag_date", "Date");
makeDraggable("drag_payee", "Payee Name");
makeDraggable("drag_amt_num", "Amount Number");
makeDraggable("drag_amt_word", "Amount Word");
</script>
"""

# HTML UI Render karvu
components.html(html_code, height=preview_h + 30)
