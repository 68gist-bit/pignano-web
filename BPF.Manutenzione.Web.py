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
        
        # Recupera la chiave dai Secrets di Streamlit
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            
            # Pulizia chiave per evitare errori di caricamento sul Web
            if isinstance(creds_info, str):
                info = json.loads(creds_info.replace("\\n", "\n"))
            else:
                info = dict(creds_info)
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            client = gspread.authorize(creds)
            
            # Apertura del file Google Sheet
            spreadsheet = client.open("Manutenzione_Pignano")
            
            # Carichiamo i fogli necessari (Assicurati che esistano nel tuo file Google Sheets)
            return {
                "Interventi": spreadsheet.worksheet("Interventi"),
                "Parametri": spreadsheet.worksheet("Parametri"),
                "Piscina": spreadsheet.worksheet("Piscina"),
                "Utenze": spreadsheet.worksheet("Utenze"),
                "Magazzino": spreadsheet.worksheet("Magazzino")
            }
        else:
            st.error("Chiave Google non trovata nei Secrets!")
            return None
    except Exception as e:
        st.error(f"Errore di connessione a Google Sheets: {e}")
        return None

sheets = get_sheets()

# --- FUNZIONE RECUPERO PARAMETRI ---
def get_cfg(tipo):
    try:
        data = sheets["Parametri"].get_all_records()
        return [r['Valore'] for r in data if str(r['Tipo']).lower() == tipo.lower()]
    except:
        return ["Dato mancante"]

# --- SIDEBAR NAVIGAZIONE ---
st.sidebar.title("🏰 BORGO PIGNANO v90")
menu = st.sidebar.radio("Scegli Modulo:", [
    "📊 Dashboard", 
    "🔧 Nuovo Intervento", 
    "🏊 Registro Piscina", 
    "⚡ Energia & Acqua",
    "📦 Magazzino"
])

if sheets:
    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Pannello di Controllo")
        try:
            data = sheets["Interventi"].get_all_records()
            if data:
                df = pd.DataFrame(data)
                df.columns = [c.lower() for c in df.columns]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Totale Lavori", len(df))
                
                if 'stato' in df.columns:
                    aperti = len(df[df['stato'].astype(str).str.lower() == 'aperto'])
                    c2.metric("🔴 Interventi Aperti", aperti)
                
                st.divider()
                st.subheader("Ultimi Interventi Registrati")
                st.dataframe(df.tail(15), use_container_width=True)
            else:
                st.info("Nessun dato presente.")
        except:
            st.warning("Verifica la struttura del foglio 'Interventi'")

    # --- 2. NUOVO INTERVENTO ---
    elif menu == "🔧 Nuovo Intervento":
        st.title("Registra Intervento / Manutenzione")
        with st.form("form_int", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tipo_lavoro = st.selectbox("Tipo", ["Intervento", "Manutenzione"])
                luogo = st.selectbox("Luogo", get_cfg("Luogo"))
                tecnico = st.selectbox("Tecnico", get_cfg("Tecnico"))
            with c2:
                attrezzo = st.selectbox("Attrezzatura", get_cfg("Attrezzatura"))
                stato = st.selectbox("Stato", ["Aperto", "Chiuso"])
            
            note = st.text_area("Note / Descrizione del problema o lavoro")
            
            if st.form_submit_button("SALVA REGISTRAZIONE"):
                data_oggi = datetime.now().strftime("%d/%m/%Y")
                id_lavoro = datetime.now().strftime("%y%m%d%H%M")
                riga = [id_lavoro, tipo_lavoro, luogo, attrezzo, tecnico, note, data_oggi, "", stato]
                
                try:
                    sheets["Interventi"].append_row(riga)
                    st.success("✅ Salvato con successo!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Errore nel salvataggio: {e}")

    # --- 3. PISCINA ---
    elif menu == "🏊 Registro Piscina":
        st.title("🏊 Registro Autocontrollo Piscina")
        with st.form("form_piscina", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                op = st.text_input("Operatore")
                m3 = st.number_input("Lettura Contatore m³", step=0.1)
                ph = st.number_input("Valore pH", min_value=0.0, max_value=14.0, value=7.2, step=0.1)
            with c2:
                cl_l = st.number_input("Cloro Libero (mg/l)", step=0.1)
                cl_c = st.number_input("Cloro Combinato", step=0.1)
                temp = st.number_input("Temperatura Acqua °C", value=28.0)
            
            trasp = st.selectbox("Trasparenza Acqua", ["Limpida", "Sufficiente", "Torbida"])
            lavaggio = st.checkbox("Controlavaggio Filtri Eseguito")
            
            if st.form_submit_button("💾 SALVA DATI PISCINA"):
                riga = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), op, m3, ph, cl_l, cl_c, trasp, temp, "SÌ" if lavaggio else "NO"]
                try:
                    sheets["Piscina"].append_row(riga)
                    st.success("✅ Registro Piscina aggiornato!")
                except:
                    st.error("Errore: Assicurati che esista il foglio 'Piscina'")

    # --- 4. ENERGIA & ACQUA ---
    elif menu == "⚡ Energia & Acqua":
        st.title("⚡ Lettura Contatori Utenze")
        with st.form("form_utenze", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                enel = st.number_input("Lettura Energia Elettrica (MT)", step=1.0)
                k = st.selectbox("Fattore K (Moltiplicatore)", [1, 40, 60, 80])
            with c2:
                acqua = st.number_input("Lettura Contatore Acqua m³", step=1.0)
            
            if st.form_submit_button("⚡ REGISTRA LETTURE"):
                cons_eff = enel * k
                riga = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), acqua, enel, k, cons_eff]
                try:
                    sheets["Utenze"].append_row(riga)
                    st.success(f"✅ Registrato! Consumo effettivo calcolato: {cons_eff} kWh")
                except:
                    st.error("Errore: Assicurati che esista il foglio 'Utenze'")

    # --- 5. MAGAZZINO ---
    elif menu == "📦 Magazzino":
        st.title("📦 Gestione Magazzino e Scorte")
        try:
            data_m = sheets["Magazzino"].get_all_records()
            if data_m:
                df_m = pd.DataFrame(data_m)
                st.dataframe(df_m, use_container_width=True)
                
                # Sistema Allerta Scorte
                # Cerchiamo colonne che somigliano a 'Stock' e 'Soglia'
                st.subheader("⚠️ Alert Riordino")
                try:
                    sotto_soglia = df_m[df_m['Stock'] <= df_m['Soglia']]
                    if not sotto_soglia.empty:
                        st.warning("I seguenti articoli sono sotto la soglia minima:")
                        st.table(sotto_soglia[['Descrizione', 'Stock', 'Soglia']])
                    else:
                        st.success("Tutte le scorte sono in regola.")
                except:
                    st.info("Controlla che le colonne nel foglio Magazzino si chiamino 'Stock' e 'Soglia'")
            else:
                st.info("Foglio Magazzino vuoto.")
        except:
            st.error("Errore nel caricamento del Magazzino.")

else:
    st.warning("⚠️ L'app non è connessa. Verifica i Secrets su Streamlit Cloud.")
