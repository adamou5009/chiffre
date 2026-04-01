import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO

# --- Selenium imports ---
from verificationAlonwa import trouver_statut_intervention_specifique, connexion_alonwa, naviguer_page_intervention
from config_driver import WebDriverManager, TIMEOUT
from selenium.webdriver.support.ui import WebDriverWait

# -------------------------
# CONFIG GOOGLE SHEET
# -------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Nom exact du fichier JSON téléchargé depuis Google Cloud
CREDENTIALS_FILE = "streamlit-gsheet-479510-69e0dfecc79fcb928615b5a7b833c32c216db7a3.json"

def connect_google_sheet(credentials_file, sheet_url):
    """Connexion à Google Sheet via gspread et compte de service."""
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    return sheet

# -------------------------
# STREAMLIT APP
# -------------------------
st.title("📘 Vérification automatique des statuts (Google Sheet → Selenium)")

# --- Demande URL Google Sheet
sheet_url = st.text_input(
    "👉 Lien du Google Sheet :",
    placeholder="https://docs.google.com/spreadsheets/..."
)

st.info(f"Placez le fichier JSON du compte de service ({CREDENTIALS_FILE}) dans le même dossier que ce script.")

# --- Formulaire de connexion Alonwa (Selenium)
with st.form("login_form"):
    url_site = st.text_input(
        "URL Alonwa",
        value="https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING"
    )
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    submitted = st.form_submit_button("🔐 Se connecter")

if submitted:
    st.session_state.driver_manager = WebDriverManager()
    st.session_state.driver = st.session_state.driver_manager.start_driver(headless=False)
    driver = st.session_state.driver

    wait = WebDriverWait(driver, TIMEOUT)
    st.session_state.wait = wait

    success, driver, wait = connexion_alonwa(driver, url_site, username, password)
    if success and naviguer_page_intervention(driver, wait):
        st.success("✅ Connecté à Alonwa et page Intervention chargée !")
    else:
        st.error("❌ Impossible de se connecter à Alonwa.")
        st.stop()

# -------------------------
# CHARGEMENT GOOGLE SHEET
# -------------------------
if st.button("📄 Charger Google Sheet"):
    if not sheet_url:
        st.error("❌ Veuillez entrer l’URL Google Sheet.")
        st.stop()

    try:
        sheet = connect_google_sheet(CREDENTIALS_FILE, sheet_url)
        ws = sheet.worksheet("PILOTE INSERTIONS")  # Nom exact de la feuille
        st.success("📄 Google Sheet connecté avec succès !")

        data = ws.get_all_values()
        df = pd.DataFrame(data)

        # Données à partir de la ligne 4
        df_data = df.iloc[3:, :]

        numeros = df_data.iloc[:, 4]  # Colonne E
        statuts = df_data.iloc[:, 6]  # Colonne G

        # Filtrage : statuts ≠ TOK, sécurisation avec fillna()
        index_a_traiter = df_data.index[statuts.fillna("").str.upper() != "TOK"]

        st.subheader("🧾 Abonnés détectés à traiter (≠ TOK)")
        st.dataframe(df.iloc[index_a_traiter, [4, 6]])

        # Stockage pour le traitement Selenium
        st.session_state.df = df
        st.session_state.index_a_traiter = index_a_traiter
        st.success(f"🔍 {len(index_a_traiter)} abonnés seront traités.")

    except Exception as e:
        st.error(f"❌ Erreur Google Sheet : {e}")

# -------------------------
# TRAITEMENT SELENIUM
# -------------------------
if st.button("🚀 Lancer le traitement automatisé"):

    if "index_a_traiter" not in st.session_state:
        st.error("❌ Veuillez d'abord charger le Google Sheet.")
        st.stop()

    df = st.session_state.df
    index_a_traiter = st.session_state.index_a_traiter

    progress = st.progress(0)
    total = len(index_a_traiter)

    for count, i in enumerate(index_a_traiter):
        ligne_google = i + 1  # correspond à la ligne Google Sheet
        numero = str(df.iloc[i, 4]).strip()

        st.write(f"⏳ Vérification : {numero} (ligne {ligne_google})")

        try:
            num, statut = trouver_statut_intervention_specifique(
                st.session_state.driver,
                st.session_state.wait,
                numero
            )

            ws.update(f"G{ligne_google}", statut)
            st.success(f"✔ Mise à jour : {numero} → {statut}")

        except Exception as e:
            st.error(f"❌ Erreur traitement {numero} : {e}")
            ws.update(f"G{ligne_google}", "ERREUR")

        progress.progress((count + 1) / total)

    st.success("🎉 Traitement terminé ! Google Sheet mis à jour.")
