import streamlit as st
import pandas as pd
from io import BytesIO
from verificationAlonwa import trouver_statut_intervention_specifique, enregistrer_resultat, connexion_alonwa, naviguer_page_intervention
from config_driver import WebDriverManager, TIMEOUT
from selenium.webdriver.support.ui import WebDriverWait

st.set_page_config(page_title="📊 Vérification Statuts Abonnés", layout="wide")
st.title("📋 Vérification des statuts d'abonnés depuis Excel")

# --- Entrée des identifiants ---
def show():
    st.subheader("🔐 Connexion à Alonwa")
    with st.form("login_form"):
        url_site = st.text_input("URL du site", value="https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("🔑 Se connecter")

    if submitted:
        st.session_state.driver_manager = WebDriverManager()
        st.session_state.driver = st.session_state.driver_manager.start_driver(headless=False)
        driver = st.session_state.driver
        wait = WebDriverWait(driver, TIMEOUT)
        st.session_state.wait = wait

        succes, driver, wait = connexion_alonwa(driver, url_site, username, password)
        if succes:
            if naviguer_page_intervention(driver, wait):
                st.success("✅ Connecté et page Intervention chargée !")
            else:
                st.error("❌ Connexion OK mais navigation vers la page Intervention échouée.")
        else:
            st.error("❌ Échec de la connexion.")

    # --- Upload du fichier Excel ---
    uploaded_file = st.file_uploader("Téléversez un fichier Excel avec une colonne 'numero_abonne'", type=["xlsx", "xls"])

    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        if "numero_abonne" not in df_input.columns:
            st.error("Le fichier doit contenir une colonne 'numero_abonne'.")
        else:
            st.success(f"Fichier chargé avec {len(df_input)} abonnés.")

            if st.button("🚀 Lancer le traitement"):

                if "driver" not in st.session_state or st.session_state.driver is None:
                    st.error("❌ Veuillez d'abord vous connecter avec vos identifiants.")
                else:
                    resultat = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    total = len(df_input)
                    for idx, row in df_input.iterrows():
                        numero = str(row["numero_abonne"]).strip()
                        status_text.text(f"⏳ Vérification du numéro {numero} ({idx+1}/{total})")

                        # Appel de ta fonction Selenium
                        numero_trouve, statut = trouver_statut_intervention_specifique(
                            st.session_state.driver, st.session_state.wait, numero
                        )

                        resultat.append({"numero_abonne": numero_trouve, "statut": statut})
                        enregistrer_resultat(numero_trouve, statut)  # Enregistrement csv local

                        status_text.text(f"✅ Résultat pour {numero} : {statut}")
                        progress_bar.progress((idx+1)/total)

                    # --- Affichage des résultats ---
                    df_result = pd.DataFrame(resultat)
                    st.subheader("📊 Résultats finaux")
                    st.dataframe(df_result)

                    # --- Préparer téléchargement Excel ---
                    output = BytesIO()

                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        df_result.to_excel(writer, index=False)

                    output.seek(0)

                    st.download_button(
                        label="💾 Télécharger les résultats",
                        data=output,
                        file_name="resultat_verification_statuts.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )


                    st.success("✅ Traitement terminé ! Le navigateur Edge reste ouvert pour inspection.")
