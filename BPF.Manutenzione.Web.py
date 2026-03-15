import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# Configurazione pagina
st.set_page_config(page_title="PIGNANO WEB", layout="wide")

# Funzione per caricare le credenziali dai Secrets di Streamlit
def get_gspread_client():
    # Carica la stringa JSON dai secrets
    creds_json = st.secrets["gcp_service_account"]
    # Se la stringa è stata incollata con gli apici, la puliamo
    if isinstance(creds_json, str):
        info = json.loads(creds_json)
    else:
        info = dict(creds_json)
        
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
    return gspread.authorize(creds)

# Connessione al foglio
try:
    client = get_gspread_client()
    sh = client.open("Manutenzione_Pignano")
    st.success("Connessione riuscita!")
except Exception as e:
    st.error(f"Errore di connessione: {e}")

st.title("🏰 PIGNANO WEB - Dashboard")
