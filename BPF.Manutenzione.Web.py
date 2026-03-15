import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import json
from fpdf import FPDF
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pignano Web Management", layout="wide", page_icon="🏰")

# --- CONNESSIONE GOOGLE (Versione Web Corretta) ---
@st.cache_resource
def get_sheets():
    try:
        # Recupera i segreti dai Secrets di Streamlit
        creds_info = st.secrets["gcp_service_account"]
        
        if isinstance(creds_info, str):
            info = json.loads(creds_info)
        else:
            info = dict(creds_info)
        
        # Correzione fondamentale per il Web (evita errore Padding/Private Key)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Apre il file Google Sheet
        spreadsheet = client.open("Manutenzione_Pignano")
        return {
            "Interventi": spreadsheet.worksheet("Interventi"),
            "Parametri": spreadsheet.worksheet("Parametri")
        }
    except Exception as e:
        st.error(f"Errore di connessione a Google Sheets: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONE RECUPERO PARAMETRI (Tecnici, Luoghi, ecc.) ---
def get_cfg(tipo):
    try:
        data = sheets["Parametri"].get_all_records()
        return [r['Valore'] for r in data if str(r['Tipo']).lower() == tipo.lower()]
    except:
        return ["Dato mancante"]

# --- FUNZIONE GENERAZIONE PDF ---
def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Report Interventi Pignano", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    
    for index, row in df.iterrows():
        text = f"ID: {row.get('ID', '')} | Data: {row.get('Data', '')} | Luogo: {row.get('Luogo', '')} | Stato: {row.get('Stato', '')}"
        pdf.cell(190, 8, text, border=1, ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACCIA ---
st.sidebar.title("🏰 PIGNANO WEB")
menu = st.sidebar.radio("Navigazione", ["📊 Dashboard", "🔧 Nuovo Intervento", "📋 Parametri Sistema"])

if sheets:
    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Stato Manutenzioni")
        try:
            data = sheets["Interventi"].get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # Metriche veloci (Le tue caselle)
                c1, c2, c3 = st.columns(3)
                c1.metric("Totale Lavori", len(df))
                c2.metric("Aperti", len(df[df['Stato'] == 'Aperto']))
                c3.metric("Chiusi", len(df[df['Stato'] == 'Chiuso']))
                
                st.divider()
                
                # Filtro di ricerca
                search = st.text_input("🔍 Filtra per camera, tecnico o descrizione")
                if search:
                    df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
                
                st.dataframe(df, use_container_width=True)
                
                # Bottone Download PDF
                if st.button("Genera Report PDF"):
                    pdf_bytes = create_pdf(df)
                    st.download_button("Scarica PDF", data=pdf_bytes, file_name="report_pignano.pdf", mime="application/pdf")
            else:
                st.info("Nessun dato presente nel foglio Interventi.")
        except Exception as e:
            st.error(f"Errore nel caricamento dati: {e}")

    # --- 2. NUOVO INTERVENTO ---
    elif menu == "🔧 Nuovo Intervento":
        st.title("Registra Nuovo Intervento")
        with st.form("form_lavoro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                operatore = st.selectbox("Operatore", get_cfg("Tecnico"))
                luogo = st.selectbox("Luogo", get_cfg("Luogo"))
            with col2:
                attrezzo = st.selectbox("Attrezzatura", get_cfg("Attrezzatura"))
                stato = st.selectbox("Stato", ["Aperto", "Chiuso"])
            
            note = st.text_area("Descrizione intervento")
            
            if st.form_submit_button("SALVA SU GOOGLE"):
                data_oggi = datetime.now().strftime("%d/%m/%Y")
                id_lavoro = datetime.now().strftime("%y%m%d%H%M")
                # Assicurati che l'ordine corrisponda alle colonne del tuo foglio
                nuova_riga = [id_lavoro, "Manutenzione", luogo, attrezzo, operatore, note, data_oggi, "", stato]
                
                try:
                    sheets["Interventi"].append_row(nuova_riga)
                    st.success("✅ Intervento salvato correttamente!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Errore nel salvataggio: {e}")

    # --- 3. PARAMETRI ---
    elif menu == "📋 Parametri Sistema":
        st.title("Configurazione Parametri")
        st.info("Questi dati sono caricati dal foglio 'Parametri'. Modificali direttamente su Google Sheets per vederli aggiornati qui.")
        try:
            data_param = sheets["Parametri"].get_all_records()
            st.table(pd.DataFrame(data_param))
        except:
            st.error("Impossibile caricare la tabella parametri.")

else:
    st.warning("⚠️ In attesa di configurazione corretta nei Secrets.")
