import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import json
from fpdf import FPDF
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pignano Web Management", layout="wide", page_icon="🏰")

# --- CONNESSIONE GOOGLE ---
@st.cache_resource
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Carica le credenziali dai Secrets di Streamlit
        if "gcp_service_account" in st.secrets:
            info = json.loads(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            client = gspread.authorize(creds)
            # Assicurati che il nome del file Google Sheet sia ESATTAMENTE questo:
            spreadsheet = client.open("Manutenzione_Pignano")
            return {
                "Interventi": spreadsheet.worksheet("Interventi"),
                "Parametri": spreadsheet.worksheet("Parametri")
            }
        else:
            st.error("Chiave Google non trovata nei Secrets di Streamlit!")
            return None
    except Exception as e:
        st.error(f"Errore di connessione a Google Sheets: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONE RECUPERO PARAMETRI ---
def get_cfg(tipo):
    try:
        data = sheets["Parametri"].get_all_records()
        return [r['Valore'] for r in data if r['Tipo'].lower() == tipo.lower()]
    except:
        return []

# --- INTERFACCIA ---
st.sidebar.title("🏰 PIGNANO WEB")
menu = st.sidebar.radio("Navigazione", ["📊 Dashboard", "🔧 Nuovo Intervento"])

if sheets:
    if menu == "📊 Dashboard":
        st.title("Stato Manutenzioni")
        try:
            data = sheets["Interventi"].get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nessun dato presente nel foglio Interventi.")
        except Exception as e:
            st.error(f"Errore nel caricamento dati: {e}")

    elif menu == "🔧 Nuovo Intervento":
        st.title("Registra Nuovo Intervento")
        with st.form("form_lavoro"):
            col1, col2 = st.columns(2)
            with col1:
                operatore = st.selectbox("Operatore", get_cfg("Tecnico"))
                luogo = st.selectbox("Luogo", get_cfg("Luogo"))
            with col2:
                attrezzo = st.selectbox("Attrezzatura", get_cfg("Attrezzatura"))
                stato = st.selectbox("Stato", ["Aperto", "Chiuso"])
            
            note = st.text_area("Descrizione intervento")
            
            if st.form_submit_button("SALVA SU GOOGLE"):
                # Crea la riga da aggiungere al foglio
                data_oggi = datetime.now().strftime("%d/%m/%Y")
                id_lavoro = datetime.now().strftime("%y%m%d%H%M")
                nuova_riga = [id_lavoro, "Intervento", luogo, attrezzo, operatore, note, data_oggi, "", stato]
                
                try:
                    sheets["Interventi"].append_row(nuova_riga)
                    st.success("✅ Intervento salvato con successo!")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")
else:
    st.info("In attesa di configurazione Secrets...")
