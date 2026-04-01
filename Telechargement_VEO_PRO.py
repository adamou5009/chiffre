from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import streamlit as st
from datetime import date, timedelta
# Importation de votre gestionnaire de driver
from config_driver import WebDriverManager 


def run_automation(driver, url, username, password, start_date_dt, end_date_dt):
    """Contient la logique d'automatisation Selenium."""
    
    # CORRECTION : Conversion au format DD/MM/YYYY
    start_date_str = start_date_dt.strftime("%d/%m/%Y")
    end_date_str = end_date_dt.strftime("%d/%m/%Y")

    # Stocke l'identifiant de la fenêtre principale avant d'ouvrir la nouvelle fenêtre
    main_window_handle = driver.current_window_handle

    try:
        # 1. Connexion (Attente, saisie, clic)
        st.info(f"Connexion à l'URL : {url}...")
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//button[@type="submit"]/div/div/span[text()="Se connecter"]')))
        username_input = driver.find_element(By.XPATH, '//input[@type="text" or @placeholder="Nom d\'utilisateur"]')
        password_input = driver.find_element(By.XPATH, '//input[@type="password" or @placeholder="Mot de passe"]') 
        username_input.send_keys(username)
        password_input.send_keys(password)
        bouton_connexion = driver.find_element(By.XPATH, '//button[@type="submit"]')
        bouton_connexion.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'aside.fixed')))
        st.success("Connexion réussie.")
        
        # 2. Navigation vers "Souscriptions"
        st.info("Navigation vers la page 'Souscriptions'...")
        subscriptions_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#/subscriptions']")))
        subscriptions_link.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sm\\:flex.items-center.bg-white')))
        st.info("Page Souscriptions chargée.")
    
        # 3. Clic sur le bouton "FILTRER"
        st.info("Clic sur le bouton 'Filtrer'...")
        filter_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Filtrer"]]')))
        filter_button.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//span[text()="Date de début"]')))
        st.success("Filtres affichés.")

        # 4. Remplissage des Dates
        st.info(f"Remplissage des dates : {start_date_str} au {end_date_str}...")
        start_date_input = driver.find_element(By.XPATH, '//span[text()="Date de début"]/following::input[1]')
        start_date_input.clear() 
        start_date_input.send_keys(start_date_str) 
        end_date_input = driver.find_element(By.XPATH, '//span[text()="Date de fin"]/following::input[1]')
        end_date_input.clear()
        end_date_input.send_keys(end_date_str)
        
        # 5. Sélection du Statut de Paiement 'Réussi' (Clic JS pour robustesse)
        st.info("Sélection du statut 'Réussi'...")
        payment_status_opener = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "payment_status")))
        payment_status_opener.click()
        choix_statut = "Réussi"
        option_xpath = f"//div[@role='option'][text()='{choix_statut}' or .//text()='{choix_statut}'] | //li[text()='{choix_statut}' or .//text()='{choix_statut}']"
        option_a_choisir = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
        driver.execute_script("arguments[0].click();", option_a_choisir)
        st.success(f"Statut '{choix_statut}' sélectionné.")

        # 6. Soumission du Formulaire
        st.info("Soumission du filtre...")
        validate_button = driver.find_element(By.XPATH, '//button[.//span[text()="Valider"] or text()="Valider"]')
        driver.execute_script("arguments[0].click();", validate_button)
        
        # 7. Clic sur le bouton "Exporter"
        st.info("Clic sur le bouton 'Exporter' pour lancer la tâche...")
        XPATH_BOUTON_EXPORTER = "//button[.//span[text()='Exporter']]"
        export_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_BOUTON_EXPORTER))
        )
        export_button.click()
        st.success("Tâche d'exportation lancée sur le serveur.")
        time.sleep(2) # Laisse un court délai pour l'enregistrement de la tâche
        
        # 8. Navigation vers la liste des téléchargements
        st.info("Navigation vers la page 'Téléchargements' pour récupérer le fichier...")
        # Attendre la stabilisation de la barre latérale
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'aside.fixed'))
        )
        
        # XPATH: Cibler le lien <a> avec l'URL de téléchargement
        DOWNLOAD_NAV_XPATH = '//a[contains(@href, "#/downloads-histories")]'
        download_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, DOWNLOAD_NAV_XPATH))
        )
        download_link.click()

        # 9. Attendre le chargement de la page de téléchargement
        XPATH_TITRE_PAGE = "//span[text()='Liste des télechargements']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, XPATH_TITRE_PAGE))
        )
        st.success("Page 'Liste des télechargements' chargée.")

        # 10. Clic sur le bouton de téléchargement ET gestion de la nouvelle fenêtre
        st.info("Localisation et clic sur l'icône de téléchargement du fichier le plus récent...")
        
        # XPATH: Première ligne du tableau //tbody/tr[1], deuxième icône d'action (l'icône de téléchargement)
        XPATH_TELECHARGER_PREMIER_FICHIER = "//tbody/tr[1]//div[@id='tooltip'][2]"
        
        download_icon_element = WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_TELECHARGER_PREMIER_FICHIER))
        )
        
        # Enregistre les fenêtres actuelles avant le clic
        original_handles = driver.window_handles
        
        download_icon_element.click()
        st.info("Clic sur l'icône 'Télécharger le fichier'. Nouvelle fenêtre attendue...")

        # --- GESTION DE LA NOUVELLE FENÊTRE ---
        
        # Attendre l'ouverture de la nouvelle fenêtre
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(len(original_handles) + 1))
        
        new_window_handle = None
        for handle in driver.window_handles:
            if handle != main_window_handle:
                new_window_handle = handle
                break
        
        if new_window_handle:
            # Basculer vers la nouvelle fenêtre
            driver.switch_to.window(new_window_handle)
            st.success("Basculement vers la nouvelle fenêtre/onglet pour la finalisation.")
            
            # TODO: SI des actions sont nécessaires dans cette nouvelle fenêtre, elles doivent être ajoutées ici.
            # Par exemple: driver.find_element(By.ID, "confirm_download").click()
            
            # Le script est terminé, le focus est sur la nouvelle fenêtre.
            st.balloons()
            st.success("Automatisation terminée. Le navigateur est laissé ouvert sur la dernière page/fenêtre pour inspection.")

        else:
            st.warning("Nouvelle fenêtre de téléchargement non détectée après le clic. Le processus s'arrête ici.")
            
        return True # Indique que l'automatisation a réussi
            
    except Exception as e:
        st.error(f"Erreur d'automatisation : {e}")
        st.error("L'automatisation a échoué. Veuillez vérifier les logs ci-dessus.")
        
        # Tenter de revenir à la fenêtre principale en cas d'erreur
        if main_window_handle in driver.window_handles:
             driver.switch_to.window(main_window_handle)
        
        return False # Indique que l'automatisation a échoué


def show():
    st.set_page_config(page_title="📊 Extraction VEO PRO", layout="wide")
    st.title("Extraction  VEO PRO 🤖")
    
    # --- Champs de connexion et URL ---
    url = st.text_input("1. Entrez l'URL de la page de connexion : ")
    utilsateur = st.text_input("2. Entrez votre nom d'utilisateur : ")
    mot_de_passe = st.text_input("3. Entrez votre mot de passe : ", type="password") 
    
    st.markdown("---")
    
    # --- Champs de Date ---
    st.header("Paramètres de Filtre")
    
    col1, col2 = st.columns(2)
    with col1:
        # Date par défaut: 90 jours en arrière
        default_start_date = date.today() - timedelta(days=90)
        date_debut = st.date_input(
            "4. Date de début du filtre (JJ/MM/AAAA)", 
            value=default_start_date,
            format="DD/MM/YYYY" # Affichage pour l'utilisateur
        )
    with col2:
        # Date par défaut: Aujourd'hui
        date_fin = st.date_input(
            "5. Date de fin du filtre (JJ/MM/AAAA)", 
            value=date.today(),
            format="DD/MM/YYYY"
        )
    
    st.markdown("---")
    
    bouton_lancer = st.button("🚀 Lancer l'automatisation et l'extraction")
    
    if bouton_lancer:
        if not all([url, utilsateur, mot_de_passe]):
            st.warning("Veuillez remplir les champs de connexion.")
            return

        # 1. INITIALISATION DU DRIVER
        manager = WebDriverManager()
        driver = None
        
        try:
            # Démarrer le driver (headless=False pour voir la fenêtre s'ouvrir)
            driver = manager.start_driver(headless=False)
            
            # 2. Exécuter la logique d'automatisation
            run_automation(driver, url, utilsateur, mot_de_passe, date_debut, date_fin)
            
        except RuntimeError as re:
            st.error(f"Impossible de démarrer le navigateur: {re}")
            
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue: {e}")
            
        finally:
            # La fermeture est gérée par la suppression de self.driver.quit() dans config_driver.py
            # et nous ne faisons plus d'appel explicite ici.
            pass


