import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="PIGNANO WEB", layout="wide")

def get_gspread_client():
    # Recuperiamo il segreto
    creds_info = st.secrets["gcp_service_account"]
    
    # Se Streamlit lo legge come stringa, lo trasformiamo in dizionario
    if isinstance(creds_info, str):
        info = json.loads(creds_info)
    else:
        info = dict(creds_info)
    
    # --- PULIZIA CHIAVE (La "cura" per il padding) ---
    raw_key = info["private_key"]
    # Rimuove virgolette extra, trasforma i \n letterali e pulisce gli spazi
    cleaned_key = raw_key.replace("\\n", "\n").strip()
    info["private_key"] = cleaned_key
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
    return gspread.authorize(creds)

st.title("🏰 PIGNANO WEB")

try:
    client = get_gspread_client()
    sh = client.open("Manutenzione_Pignano")
    st.success("✅ Connessione riuscita! Il padding è sistemato.")
    
    # Prova a leggere il primo foglio per conferma
    ws = sh.get_worksheet(0)
    st.write(f"Siamo connessi al foglio: **{ws.title}**")

except Exception as e:
    st.error(f"❌ Errore persistente: {e}")
