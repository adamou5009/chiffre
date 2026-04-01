import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options

TIMEOUT = 60

# ======================================================
# 🔧 CRÉATION DU DRIVER EDGE (AUTO – Selenium Manager)
# ======================================================
def creer_driver_edge():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")

    # ✅ Selenium Manager gère EdgeDriver automatiquement
    driver = webdriver.Edge(options=options)
    return driver


# ======================================================
# 🔧 PRÉPARATION DU FORMULAIRE
# ======================================================
def preparer_formulaire(driver, date_debut, date_fin, reseau_value):
    critere_select = Select(driver.find_element(By.ID, "_ReportActivity"))
    critere_select.select_by_value("network_turnover")
    time.sleep(1)

    date_start = driver.find_element(By.ID, "_ReportDateStart")
    date_end = driver.find_element(By.ID, "_ReportDateEnd")
    date_start.clear()
    date_start.send_keys(date_debut)
    date_end.clear()
    date_end.send_keys(date_fin)
    time.sleep(1)

    reseau_select_elem = driver.find_element(By.ID, "_ReportBridge")
    driver.execute_script(
        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
        reseau_select_elem,
        reseau_value
    )
    time.sleep(1)

    try:
        tout_select = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//svg[contains(@viewBox,'0 0 100 100')]"))
        )
        driver.execute_script("arguments[0].click();", tout_select)
        time.sleep(1)
    except:
        pass


# ======================================================
# 🚀 FONCTION PRINCIPALE
# ======================================================
def lancer_import(token, date_debut, date_fin):
    status_msg = st.empty()
    status_msg.info("🌐 Démarrage du navigateur Edge...")

    driver = None

    try:
        driver = creer_driver_edge()

        url = f"https://my.topup.cm/fr/portal/login/{token}"
        driver.get(url)
        time.sleep(3)
        status_msg.success("✅ Connexion réussie et page ouverte.")

        # --- Accès Reporting ---
        try:
            reporting_card = driver.find_element(By.XPATH, "//a[contains(@href,'/fr/reporting.ime')]")
            driver.execute_script("arguments[0].click();", reporting_card)
            time.sleep(2)
            status_msg.success("✅ Accès au module 'Reporting'.")
        except:
            status_msg.error("⚠️ Impossible de cliquer sur 'Reporting'.")
            return

        # --- Réseaux ---
        reseau_select = Select(driver.find_element(By.ID, "_ReportBridge"))
        reseaux = [opt.get_attribute("value") for opt in reseau_select.options if opt.get_attribute("value")]

        st.write(f"**{len(reseaux)}** réseaux à traiter trouvés.")

        col1, col2, col3 = st.columns([6, 1, 4])
        progress_bar = col1.progress(0)
        progress_text = col2.empty()
        current_status = col3.empty()

        total = len(reseaux)

        for i, reseau_value in enumerate(reseaux):
            pct = int(((i + 1) / total) * 100)
            progress_bar.progress(pct)
            progress_text.text(f"{pct}%")
            current_status.info(f"Traitement : **{reseau_value}**")

            try:
                preparer_formulaire(driver, date_debut, date_fin, reseau_value)

                valider_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "btnFormSubmit"))
                )
                driver.execute_script("arguments[0].click();", valider_btn)

                current_status.success(f"✅ Export lancé : **{reseau_value}**")
                time.sleep(5)
                driver.refresh()
                time.sleep(3)

            except Exception as e:
                current_status.error(f"❌ Erreur sur {reseau_value} : {e}")
                driver.refresh()
                time.sleep(3)

        progress_bar.progress(100)
        current_status.success("🎉 **Terminé !**")
        st.balloons()

    except Exception as e:
        status_msg.error(f"❌ Une erreur critique est survenue : {e}")

    finally:
        if driver:
            driver.quit()
        st.info("👋 Navigateur fermé et script terminé.")


# ======================================================
# 🖥️ PAGE STREAMLIT
# ======================================================
def show():
    st.title("⬇️ Téléchargement Topup")

    with st.form("topup_form"):
        token = st.text_input("1️⃣ Jeton de connexion :", type="password")

        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("2️⃣ Date de début")
        with col2:
            date_fin = st.date_input("3️⃣ Date de fin")

        submitted = st.form_submit_button("🚀 Lancer l'import", type="primary")

    if submitted:
        lancer_import(
            token,
            date_debut.strftime("%d/%m/%Y"),
            date_fin.strftime("%d/%m/%Y")
        )
