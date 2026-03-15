import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pignano Web Management", layout="wide", page_icon="🏰")

# --- CONNESSIONE GOOGLE ---
@st.cache_resource
def get_sheets():
    try:
        # Recupera il segreto
        creds_info = st.secrets["gcp_service_account"]
        
        # Converte in dizionario se necessario
        if isinstance(creds_info, str):
            info = json.loads(creds_info)
        else:
            info = dict(creds_info)
        
        # PULIZIA CHIAVE (Essenziale per evitare errori di Padding)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Apre il file Google Sheet
        spreadsheet = client.open("Manutenzione_Pignano")
        
        return {
            "Interventi": spreadsheet.worksheet("Interventi"),
            "Parametri": spreadsheet.worksheet("Parametri")
        }
    except Exception as e:
        st.error(f"❌ Errore di connessione: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONE RECUPERO PARAMETRI ---
def get_cfg(tipo):
    try:
        # Legge tutti i dati dal foglio Parametri
        data = sheets["Parametri"].get_all_records()
        # Filtra i valori in base alla colonna 'Tipo' (es. Tecnico, Luogo, Attrezzatura)
        return [r['Valore'] for r in data if str(r['Tipo']).strip().lower() == tipo.lower()]
    except:
        return ["Nessun dato"]

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
                
                # Piccola Dashboard a caselle in alto
                c1, c2, c3 = st.columns(3)
                c1.metric("Totale Interventi", len(df))
                c2.metric("Aperti", len(df[df['Stato'] == 'Aperto']) if 'Stato' in df.columns else 0)
                c3.metric("Chiusi", len(df[df['Stato'] == 'Chiuso']) if 'Stato' in df.columns else 0)
                
                st.divider()
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nessun dato presente nel foglio Interventi.")
        except Exception as e:
            st.error(f"Errore nel caricamento dati: {e}")

    elif menu == "🔧 Nuovo Intervento":
        st.title("Registra Nuovo Intervento")
        
        with st.form("form_lavoro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                operatore = st.selectbox("👷 Operatore", get_cfg("Tecnico"))
                luogo = st.selectbox("📍 Luogo", get_cfg("Luogo"))
            with col2:
                attrezzo = st.selectbox("🛠️ Attrezzatura", get_cfg("Attrezzatura"))
                stato = st.selectbox("📝 Stato", ["Aperto", "Chiuso"])
            
            note = st.text_area("Descrizione intervento")
            
            if st.form_submit_button("SALVA SU GOOGLE"):
                data_oggi = datetime.now().strftime("%d/%m/%Y")
                id_lavoro = datetime.now().strftime("%y%m%d%H%M")
                
                # Deve corrispondere alle colonne del tuo foglio "Interventi"
                nuova_riga = [id_lavoro, "Intervento", luogo, attrezzo, operatore, note, data_oggi, "", stato]
                
                try:
                    sheets["Interventi"].append_row(nuova_riga)
                    st.success("✅ Intervento salvato con successo!")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")
else:
    st.warning("⚠️ L'app non è connessa a Google Sheets. Controlla i Secrets.")
