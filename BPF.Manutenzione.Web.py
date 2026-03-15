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
        
        # Recupero sicuro dai Secrets
        creds_raw = st.secrets["gcp_service_account"]
        
        # Trasformazione e pulizia rigorosa
        if isinstance(creds_raw, str):
            # Pulizia per evitare l'errore "Invalid control character"
            info = json.loads(creds_raw.strip().replace("\\n", "\n"))
        else:
            info = dict(creds_raw)
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
        st.error(f"❌ Errore di Configurazione: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONI UTILI ---
def get_cfg(tipo):
    try:
        data = sheets["Parametri"].get_all_records()
        return [r['Valore'] for r in data if str(r['Tipo']).lower() == tipo.lower()]
    except: return ["-"]

# --- SIDEBAR ---
st.sidebar.title("🏰 PIGNANO v90")
menu = st.sidebar.radio("Vai a:", ["📊 Dashboard", "🔧 Nuovo Intervento", "🏊 Piscina", "⚡ Utenze", "📦 Magazzino"])

if sheets:
    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Riepilogo Attività")
        data = sheets["Interventi"].get_all_records()
        if data:
            df = pd.DataFrame(data)
            df.columns = [c.lower() for c in df.columns]
            c1, c2 = st.columns(2)
            c1.metric("Totale Lavori", len(df))
            if 'stato' in df.columns:
                ap = len(df[df['stato'].astype(str).str.lower() == 'aperto'])
                c2.metric("🔴 Interventi Aperti", ap)
            st.divider()
            st.dataframe(df.tail(15), use_container_width=True)

    # --- NUOVO INTERVENTO ---
    elif menu == "🔧 Nuovo Intervento":
        st.title("🔧 Registrazione Lavoro")
        with st.form("form_int", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tipo = st.selectbox("Tipo", ["Intervento", "Manutenzione"])
                luogo = st.selectbox("Luogo", get_cfg("Luogo"))
            with c2:
                tecnico = st.selectbox("Tecnico", get_cfg("Tecnico"))
                stato = st.selectbox("Stato", ["Aperto", "Chiuso"])
            note = st.text_area("Descrizione")
            if st.form_submit_button("SALVA"):
                riga = [datetime.now().strftime("%y%m%d%H%M"), tipo, luogo, "-", tecnico, note, datetime.now().strftime("%d/%m/%Y"), "", stato]
                sheets["Interventi"].append_row(riga)
                st.success("✅ Salvato!")

    # --- ALTRI MODULI ---
    elif menu == "🏊 Piscina":
        st.title("🏊 Registro Piscina")
        st.info("I dati verranno salvati nel foglio 'Piscina'")
        # Qui puoi aggiungere i campi pH, Cloro come prima...
    
    elif menu == "⚡ Utenze":
        st.title("⚡ Utenze")
        st.info("I dati verranno salvati nel foglio 'Utenze'")

    elif menu == "📦 Magazzino":
        st.title("📦 Magazzino")
        data_m = sheets["Magazzino"].get_all_records()
        if data_m: st.dataframe(pd.DataFrame(data_m), use_container_width=True)

else:
    st.warning("⚠️ L'app non riesce a connettersi. Ricontrolla i Secrets.")
