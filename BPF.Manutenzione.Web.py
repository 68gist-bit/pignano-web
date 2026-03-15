import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pignano Management v90", layout="wide", page_icon="🏰")

# --- CONNESSIONE GOOGLE ---
@st.cache_resource
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Leggiamo la stringa pulita
        if "GCP_JSON" not in st.secrets:
            st.error("Manca la chiave GCP_JSON nei Secrets!")
            return None
            
        info = json.loads(st.secrets["GCP_JSON"])
        
        # Pulizia della private_key per il web
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Manutenzione_Pignano")
        
        return {
            "Interventi": spreadsheet.worksheet("Interventi"),
            "Parametri": spreadsheet.worksheet("Parametri"),
            "Piscina": spreadsheet.worksheet("Piscina"),
            "Utenze": spreadsheet.worksheet("Utenze"),
            "Magazzino": spreadsheet.worksheet("Magazzino")
        }
    except Exception as e:
        st.error(f"❌ Errore Connessione: {e}")
        return None

sheets = get_sheets()

# --- SIDEBAR ---
st.sidebar.title("🏰 PIGNANO v90")
menu = st.sidebar.radio("Vai a:", ["📊 Dashboard", "🔧 Nuovo Intervento", "🏊 Piscina", "⚡ Utenze", "📦 Magazzino"])

if sheets:
    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Stato Attività")
        try:
            data = sheets["Interventi"].get_all_records()
            if data:
                df = pd.DataFrame(data)
                df.columns = [c.lower() for c in df.columns]
                st.metric("Totale Lavori", len(df))
                st.dataframe(df.tail(15), use_container_width=True)
        except: st.info("Foglio interventi pronto.")

    # --- NUOVO INTERVENTO ---
    elif menu == "🔧 Nuovo Intervento":
        st.title("🔧 Registrazione")
        with st.form("form_int", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Intervento", "Manutenzione"])
            note = st.text_area("Descrizione")
            if st.form_submit_button("SALVA"):
                riga = [datetime.now().strftime("%y%m%d%H%M"), tipo, "-", "-", "-", note, datetime.now().strftime("%d/%m/%Y"), "", "Aperto"]
                sheets["Interventi"].append_row(riga)
                st.success("✅ Salvato!")

    # --- ALTRI MODULI ---
    elif menu == "🏊 Piscina":
        st.title("🏊 Registro Piscina")
        st.write("Modulo Piscina Attivo")
    
    elif menu == "⚡ Utenze":
        st.title("⚡ Utenze")
        st.write("Modulo Utenze Attivo")

    elif menu == "📦 Magazzino":
        st.title("📦 Magazzino")
        try:
            data_m = sheets["Magazzino"].get_all_records()
            if data_m: st.dataframe(pd.DataFrame(data_m), use_container_width=True)
        except: st.info("Foglio magazzino pronto.")

else:
    st.warning("⚠️ Controlla i Secrets: inserisci GCP_JSON correttamente.")
