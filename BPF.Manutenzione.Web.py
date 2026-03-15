import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd

st.set_page_config(page_title="PIGNANO WEB", layout="wide")

def get_gspread_client():
    creds_info = st.secrets["gcp_service_account"]
    if isinstance(creds_info, str):
        info = json.loads(creds_info)
    else:
        info = dict(creds_info)
    
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

st.title("🏰 PIGNANO WEB - Visualizzazione Dati")

try:
    client = get_gspread_client()
    sh = client.open("Manutenzione_Pignano")
    
    # Prendi tutte le linguette disponibili
    worksheets = sh.worksheets()
    titles = [ws.title for ws in worksheets]
    
    # Crea un selettore per cambiare foglio nell'app
    st.sidebar.header("Impostazioni")
    sheet_name = st.sidebar.selectbox("Scegli il foglio da leggere:", titles)
    
    ws = sh.worksheet(sheet_name)
    data = ws.get_all_records()

    if data:
        df = pd.DataFrame(data)
        st.success(f"✅ Dati caricati correttamente dal foglio: **{sheet_name}**")
        
        # Filtro di ricerca veloce
        search = st.text_input("🔍 Cerca nel foglio (es. Filtro, Caldaia, ecc.):")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        # Mostra la tabella
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"⚠️ Il foglio '{sheet_name}' sembra non avere dati o mancano le intestazioni nella prima riga.")
        st.info("Assicurati che la prima riga del foglio contenga i nomi delle colonne (es. DATA, DESCRIZIONE, STATO).")

except Exception as e:
    st.error(f"❌ Errore durante la lettura: {e}")
