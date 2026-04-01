import streamlit as st
from datetime import date
import time
from selenium.webdriver.support.ui import WebDriverWait

from fonction import (
    connexion_savant,
    naviguer_page_intervention,
    activer_et_selectionner_dates,
    selectionner_statuts,
    selectionner_statut_temporaire,
    extraire_tableau,
    extraire_interventions_temporaire,
    generer_excel_multi_feuilles,
    est_statut_temporaire,
    demander_arret,
    reset_arret,
    arret_demande
)

from config_driver import WebDriverManager, TIMEOUT


# =====================================================
# PAGE EXTRACTION
# =====================================================
def show():
    # ==================================================
    # CSS PREMIUM
    # ==================================================
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(to bottom right, #f0f4f8, #d9e2ec);
            color: #1c1c1c;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        h1, h2, h3, .css-10trblm { color: #0d3b66; font-weight: 600; }
        .st-expander {
            background-color: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
        }
        .stColumns>div { min-width: 200px; max-width: 350px; }
        .stTextInput>div>div>input, 
        .stMultiSelect>div>div>div>div>div>div {
            border-radius: 8px; border: 1px solid #c0c0c0; padding: 8px 12px; font-size: 14px;
        }
        .stTextInput>div>div>input:focus,
        .stMultiSelect>div>div>div>div>div>div:focus {
            border: 2px solid #0d3b66; outline: none;
        }
        .stButton>button {
            background: linear-gradient(to right, #0d3b66, #1766aa);
            color: white; font-weight: 600; border-radius: 12px; padding: 0.6rem 1.5rem;
            margin-top: 10px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            background: linear-gradient(to right, #1766aa, #0d3b66);
            transform: translateY(-2px);
            box-shadow: 0 6px 10px rgba(0,0,0,0.15);
        }
        .stProgress>div>div>div>div {
            background: linear-gradient(to right, #0d3b66, #4ca1af);
        }
        .stAlert { border-radius: 10px; padding: 12px; font-weight: 500; font-size: 14px; }
        .stDownloadButton>button {
            background: linear-gradient(to right, #28a745, #45c35a); color: white; font-weight: bold;
            border-radius: 12px; padding: 0.5rem 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stDownloadButton>button:hover {
            background: linear-gradient(to right, #45c35a, #28a745);
            transform: translateY(-2px);
            box-shadow: 0 6px 10px rgba(0,0,0,0.15);
        }
        .statut-temporaire { color: #ff8c42; font-weight: bold; }
        .statut-terminee-ok { color: #28a745; font-weight: bold; }
        .statut-terminee-ko { color: #dc3545; font-weight: bold; }
        .statut-annulee { color: #6c757d; font-weight: bold; }
        .statut-planifiee { color: #17a2b8; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.set_page_config(page_title="Extraction Alonwa", layout="centered")

    st.subheader(" Extraction des interventions Alonwa")
    st.markdown("---")

    # =====================================================
    # CONNEXION
    # =====================================================
    with st.expander("👤 Connexion Alonwa", expanded=True):
        col1, col2 = st.columns(2)
        username = col1.text_input("Identifiant")
        password = col2.text_input("Mot de passe", type="password")

    # =====================================================
    # FILTRES
    # =====================================================
    with st.expander("🔎 Filtres d’extraction", expanded=True):
        col3, col4 = st.columns(2)
        date_debut = col3.date_input("Date début", value=date.today().replace(day=1))
        date_fin = col4.date_input("Date fin", value=date.today())

        statuts_disponibles = [
            "Acceptée", "Annulée", "A planifier", "A qualifier",
            "A réconcilier", "Planifiée", "Temporaire",
            "Terminée KO Canal", "Terminée KO Client",
            "Terminée OK", "Validée"
        ]

        statuts_choisis = st.multiselect(
            "Statuts à extraire",
            statuts_disponibles,
            default=["Terminée OK"]
        )

    st.markdown("---")

    # =====================================================
    # BOUTONS
    # =====================================================
    col_run, col_stop = st.columns(2)
    lancer = col_run.button("▶️ Extraire", use_container_width=True)
    stop = col_stop.button("⛔ Arrêter", use_container_width=True)

    if stop:
        demander_arret()
        st.warning("⛔ Arrêt demandé… récupération des données en cours")

    # =====================================================
    # LANCEMENT
    # =====================================================
    data_temporaire = []
    data_autres = []
    excel_buffer = None  # variable globale pour le téléchargement

    if lancer:
        if not username or not password or not statuts_choisis:
            st.error("❌ Tous les champs sont obligatoires")
            return

        reset_arret()
        progress = st.progress(0)
        info = st.empty()

        driver = WebDriverManager().start_driver(headless=False)
        wait = WebDriverWait(driver, TIMEOUT)

        try:
            # CONNEXION
            info.info("Connexion à SAVANT…")
            ok, driver, wait = connexion_savant(
                driver,
                "https://serviceplus.canal-plus.com/index.php?action=GET_LOGIN",
                username,
                password
            )
            if not ok or arret_demande():
                return
            progress.progress(10)

            # NAVIGATION
            info.info("Accès à la page Intervention…")
            if not naviguer_page_intervention(driver, wait) or arret_demande():
                return
            progress.progress(20)
            time.sleep(1)

            # DATES
            info.info("Application de la période…")
            activer_et_selectionner_dates(driver, wait,
                                          date_debut.strftime("%d/%m/%Y"),
                                          date_fin.strftime("%d/%m/%Y"))
            progress.progress(30)

            # PIPELINE TEMPORAIRE
            if est_statut_temporaire(statuts_choisis) and not arret_demande():
                info.info("Extraction des interventions TEMPORAIRE…")
                selectionner_statut_temporaire(driver, wait)
                progress.progress(45)
                data_temporaire = extraire_interventions_temporaire(driver, wait)
                progress.progress(60)

            # PIPELINE AUTRES STATUTS
            autres_statuts = [s for s in statuts_choisis if s != "Temporaire"]
            if autres_statuts and not arret_demande():
                info.info("Extraction des autres statuts…")
                selectionner_statuts(driver, wait, autres_statuts)
                time.sleep(1)
                progress.progress(70)
                data_autres = extraire_tableau(driver, wait, autres_statuts)
                progress.progress(85)

        except Exception as e:
            st.error("❌ Erreur critique pendant l’extraction")
            st.exception(e)

        finally:
            driver.quit()
            st.info("🛑 Navigateur fermé")

        # =============================================
        # EXPORT EXCEL (toujours disponible)
        # =============================================
        excel_buffer = generer_excel_multi_feuilles(data_temporaire, data_autres)
        progress.progress(100)

        if arret_demande():
            info.warning("⚠️ Extraction arrêtée – données partielles disponibles")
        else:
            info.success("✅ Extraction terminée avec succès")

    # =====================================================
    # BOUTON DE TÉLÉCHARGEMENT (toujours visible si données présentes)
    # =====================================================
    if excel_buffer and (data_temporaire or data_autres):
        st.download_button(
            "📥 Télécharger le fichier Excel",
            data=excel_buffer,
            file_name="extraction_interventions_savant.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown(
            f"📊 Résumé : "
            f"<span class='statut-temporaire'>{len(data_temporaire)} TEMPORAIRE</span> | "
            f"<span class='statut-terminee-ok'>{len(data_autres)} autres statuts</span>",
            unsafe_allow_html=True
        )
