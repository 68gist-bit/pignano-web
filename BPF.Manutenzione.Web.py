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

# --- CONNESSIONE GOOGLE (Versione Web Corretta) ---
@st.cache_resource
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Recupera la chiave dai Secrets di Streamlit
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            
            # Se la chiave è una stringa (testo), la puliamo dai simboli \n che creano errore padding
            if isinstance(creds_info, str):
                info = json.loads(creds_info.replace("\\n", "\n"))
            else:
                # Se Streamlit la legge già come oggetto, puliamo solo la private_key
                info = dict(creds_info)
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            client = gspread.authorize(creds)
            
            # Apertura del file Google Sheet
            spreadsheet = client.open("Manutenzione_Pignano")
            return {
                "Interventi": spreadsheet.worksheet("Interventi"),
                "Parametri": spreadsheet.worksheet("Parametri")
            }
        else:
            st.error("Chiave Google non trovata nei Secrets!")
            return None
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONE RECUPERO PARAMETRI ---
def get_cfg(tipo):
    try:
        data = sheets["Parametri"].get_all_records()
        return [r['Valore'] for r in data if str(r['Tipo']).lower() == tipo.lower()]
    except:
        return []

# --- FUNZIONE GENERAZIONE PDF ---
def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Report Interventi Pignano", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    
    for index, row in df.iterrows():
        # Creiamo una riga di testo per ogni intervento nel PDF
        riga_testo = f"ID: {row.get('id', '')} | Data: {row.get('data', '')} | Luogo: {row.get('luogo', '')} | Stato: {row.get('stato', '')}"
        pdf.cell(190, 8, riga_testo.encode('latin-1', 'replace').decode('latin-1'), border=1, ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACCIA ---
st.sidebar.title("🏰 PIGNANO WEB")
menu = st.sidebar.radio("Navigazione", ["📊 Dashboard", "🔧 Nuovo Intervento"])

if sheets:
    # --- SCHEDA DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Stato Manutenzioni")
        try:
            data = sheets["Interventi"].get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # Uniformiamo i nomi delle colonne in minuscolo per non avere errori di ricerca
                df.columns = [c.lower() for c in df.columns]
                
                # --- LE CASELLE (METRICHE) ---
                col1, col2, col3 = st.columns(3)
                col1.metric("Totale Lavori", len(df))
                
                if 'stato' in df.columns:
                    aperti = len(df[df['stato'].astype(str).str.lower() == 'aperto'])
                    chiusi = len(df[df['stato'].astype(str).str.lower() == 'chiuso'])
                    col2.metric("🔴 MANUTENZIONI APERTE", aperti)
                    col3.metric("🟢 LAVORI CONCLUSI", chiusi)
                
                st.divider()
                
                # Tabella dati principale
                st.dataframe(df, use_container_width=True)
                
                # Bottone per il PDF
                if st.button("Genera Report PDF"):
                    pdf_bytes = create_pdf(df)
                    st.download_button("Scarica PDF", data=pdf_bytes, file_name="report_pignano.pdf", mime="application/pdf")
            else:
                st.info("Nessun dato presente nel foglio Interventi.")
        except Exception as e:
            st.error(f"Errore caricamento dati: {e}")

    # --- SCHEDA NUOVO INTERVENTO ---
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
                
                # Riga da aggiungere (assicurati che l'ordine delle colonne nel foglio sia questo)
                nuova_riga = [id_lavoro, "Intervento", luogo, attrezzo, operatore, note, data_oggi, "", stato]
                
                try:
                    sheets["Interventi"].append_row(nuova_riga)
                    st.success("✅ Intervento salvato con successo!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")
else:
    st.info("In attesa di configurazione Secrets...")
