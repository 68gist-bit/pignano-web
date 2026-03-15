import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# Configurazione pagina
st.set_page_config(page_title="PIGNANO WEB", layout="wide")

def get_gspread_client():
    # Carica i segreti
    creds_info = st.secrets["gcp_service_account"]
    
    # Se Streamlit passa una stringa invece di un dizionario, la convertiamo
    if isinstance(creds_info, str):
        info = json.loads(creds_info)
    else:
        info = dict(creds_info)
    
    # PULIZIA CHIAVE: Trasforma i \n di testo in veri "a capo" per Google
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Creazione credenziali
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

st.title("🏰 PIGNANO WEB - Gestione Manutenzioni")

try:
    # Tentativo di connessione
    client = get_gspread_client()
    # Apri il foglio Google (Assicurati che il nome sia esatto)
    sh = client.open("Manutenzione_Pignano")
    
    st.success("✅ Connessione riuscita! Il database è online.")
    
    # Esempio: Mostra i dati della prima tabella
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_records()
    
    if data:
        import pandas as pd
        df = pd.DataFrame(data)
        st.subheader(f"Dati da: {worksheet.title}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Il foglio è connesso ma sembra vuoto.")

except Exception as e:
    st.error("❌ Errore di connessione")
    st.info(f"Dettaglio tecnico: {e}")
    st.warning("Verifica che il foglio Google sia condiviso con l'email dell'account di servizio.")
