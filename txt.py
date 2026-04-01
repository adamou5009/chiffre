# --------------------------------------------
# CANAL+ ServicePlus – Version Ultra-Robuste
# Inclus : Filtrage Date, Auto-Refresh & Nettoyage Doublons
# --------------------------------------------
import time
import logging
import os
import warnings
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.edge.service import Service as EdgeService

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ---------- CONFIG UTILISATEUR ----------
URL_CONNEXION = "https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING"
VOTRE_IDENTIFIANT = "Centre_RAyinda"
VOTRE_MOT_DE_PASSE = "L4E3FrOes4bgNJar"

ZONES_CONFIG = {
    'mfoundi': {'latitude': 3.841309, 'longitude': 11.492995, 'technicien': 'FOKANA STEPHANE'},
    'yaounde': {'latitude': 3.8480, 'longitude': 11.5021, 'technicien': 'MFONDI DAOUDA FALL'}
}

ZONE_ACTIVE = input("Choisir zone (mfoundi/yaounde): ").strip().lower()
TIMEOUT = 90
MODE_HEADLESS = True

# ---------- DRIVER MANAGER OPTIMISÉ ----------
class WebDriverManager:
    def start_driver(self, headless=True):
        # Nettoyage des processus fantômes avant de démarrer
        os.system("taskkill /f /im msedgedriver.exe /t >nul 2>&1")
        
        options = webdriver.EdgeOptions()
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Accélérateurs de démarrage
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-features=EdgeSmartScreen,SafeBrowsing")
        options.add_argument("--force-ipv4")
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.page_load_strategy = 'eager' # Ne pas attendre les images
        
        service = EdgeService(log_path=os.devnull)
        self.driver = webdriver.Edge(service=service, options=options)
        self.driver.set_page_load_timeout(100)
        return self.driver

    def stop_driver(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

# ---------- FONCTION DE SECOURS (CONFLIT / DOUBLON) ----------
def procedure_secours_conflit(driver, wait, onglet_parent, ref_inter, tech_nom):
    try:
        # Vérifier si bouton "Retour" présent (signe de conflit)
        btn_retour = driver.find_elements(By.XPATH, "//button[contains(., 'Retour')]")
        if not btn_retour:
            return True 

        logger.warning(f"⚠️ Conflit détecté pour {ref_inter}. Nettoyage du doublon...")
        
        # 1. Aller sur le panier (onglet parent)
        driver.switch_to.window(onglet_parent)
        
        # 2. Filtrer sur "Planifiées"
        wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='Planifiées']"))).click()
        time.sleep(4)

        # 3. Trouver la ligne correspondante
        xpath_doublon = f"//table[@id='tbl_inter_pending']//tr[td[contains(., '{ref_inter}')] and td[contains(., '{tech_nom}')]]//td[1]//a"
        lien_doublon = driver.find_element(By.XPATH, xpath_doublon)
        driver.execute_script("arguments[0].click();", lien_doublon)
        
        # Switch vers l'onglet du doublon (le 3ème)
        wait.until(EC.number_of_windows_to_be(3))
        driver.switch_to.window(driver.window_handles[-1])
        
        # 4. Refuser
        acc = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(., 'RDV')]")))
        if acc.get_attribute("aria-expanded") == "false": driver.execute_script("arguments[0].click();", acc)
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "btn_inter_refuse"))))
        time.sleep(2)
        driver.close()
        
        # 5. Revenir à la fiche bloquée
        driver.switch_to.window(driver.window_handles[1])
        driver.execute_script("arguments[0].click();", btn_retour[0])
        time.sleep(2)
        driver.refresh()
        
        # 6. Remettre filtre "A qualifier" sur parent
        driver.switch_to.window(onglet_parent)
        wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='A qualifier']"))).click()
        driver.switch_to.window(driver.window_handles[1])
        
        return True
    except Exception as e:
        logger.error(f"❌ Échec secours: {e}")
        return False

# ---------- UTILITAIRES ----------
def cliquer_oui_unifie(driver, timeout=5):
    try:
        btn = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class,'ui-dialog-buttonset')]/button[span[contains(text(),'Oui')]]")))
        driver.execute_script("arguments[0].click();", btn)
        return True
    except: return False

def extraire_infos_intervention(driver):
    wait = WebDriverWait(driver, 10)
    infos = {}
    try:
        accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(., 'Intervention')]")))
        if accordion.get_attribute("aria-expanded") == "false":
            driver.execute_script("arguments[0].click();", accordion)
            time.sleep(0.5)
        
        def get_val(label):
            try: return driver.find_element(By.XPATH, f"//label[contains(text(), '{label}')]/following-sibling::div[1]").text.strip()
            except: return None

        infos['date_creation'] = get_val("Date de création")
        infos['nom'] = get_val("Nom du rattachement")
        
        doit_traiter = True
        if infos['date_creation']:
            date_str = infos['date_creation'].split(' ')[0]
            if datetime.strptime(date_str, "%d/%m/%Y").date() == datetime.now().date():
                doit_traiter = False
        return infos, doit_traiter
    except: return {}, True

def cliquer_coordonnees_sur_carte(driver, lat, lng, nom):
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "inter_plan_dialog")))
        # Forcer centrage et clic via JS Leaflet
        driver.execute_script("""
            var lat = arguments[0]; var lng = arguments[1];
            if(window.map) {
                map.setView([lat, lng], 15);
                var pt = map.latLngToContainerPoint(L.latLng(lat, lng));
                map.fireEvent('click', {latlng: L.latLng(lat, lng), containerPoint: pt});
            }
        """, lat, lng)
        time.sleep(2)
        return cliquer_oui_unifie(driver) or True
    except: return False

# ---------- TRAITEMENT PRINCIPAL ----------
def traiter_toutes_les_interventions():
    mgr = WebDriverManager()
    driver = mgr.start_driver(headless=MODE_HEADLESS)
    wait = WebDriverWait(driver, TIMEOUT)
    
    try:
        # Connexion
        driver.get(URL_CONNEXION)
        wait.until(EC.presence_of_element_located((By.ID, "in_username"))).send_keys(VOTRE_IDENTIFIANT)
        driver.find_element(By.ID, "in_password").send_keys(VOTRE_MOT_DE_PASSE)
        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        
        # Filtre initial
        wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='A qualifier']"))).click()
        
        onglet_parent = driver.current_window_handle
        index_inter = 0

        while True:
            time.sleep(2)
            liens = driver.find_elements(By.CSS_SELECTOR, "#tbl_inter_pending tbody tr td:nth-child(1) a")
            if not liens or index_inter >= len(liens): break
            
            ref = liens[index_inter].text.strip()
            logger.info(f"--- Fiche {index_inter+1}: {ref} ---")
            
            driver.execute_script("arguments[0].click();", liens[index_inter])
            wait.until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[-1])
            
            # 1. Vérif Date
            infos, doit = extraire_infos_intervention(driver)
            if not doit:
                driver.close(); driver.switch_to.window(onglet_parent)
                index_inter += 1; continue

            # 2. Boucle de tentative interne (Planification + Affectation)
            reussi = False
            for essai in range(2):
                try:
                    # Planification
                    acc = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(., 'RDV')]")))
                    if acc.get_attribute("aria-expanded") == "false": driver.execute_script("arguments[0].click();", acc)
                    
                    wait.until(EC.element_to_be_clickable((By.ID, "btn_inter_plan"))).click()
                    cliquer_coordonnees_sur_carte(driver, ZONES_CONFIG[ZONE_ACTIVE]['latitude'], ZONES_CONFIG[ZONE_ACTIVE]['longitude'], ZONE_ACTIVE)
                    
                    # Affectation
                    driver.refresh()
                    acc = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(., 'RDV')]")))
                    if acc.get_attribute("aria-expanded") == "false": driver.execute_script("arguments[0].click();", acc)
                    
                    driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "inter_affect_tech_btn"))))
                    tech = ZONES_CONFIG[ZONE_ACTIVE]['technicien']
                    xpath_tech = f"//table[@id='affect_tech_table_dt']//tr[td[contains(., '{tech}')]]//button"
                    driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.XPATH, xpath_tech))))
                    
                    # Validation finale
                    driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "valid_affecter_inter"))))
                    
                    # Gérer bouton Retour / Conflit
                    if procedure_secours_conflit(driver, wait, onglet_parent, ref, tech):
                        reussi = True; break
                except Exception as e:
                    logger.warning(f"Tentative {essai+1} échouée, refresh...")
                    driver.refresh()
            
            # Sortie de fiche
            if len(driver.window_handles) > 1: driver.close()
            driver.switch_to.window(onglet_parent)
            
            # On clique sur Valider la période sur le panier
            try: driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "btn_period_valid"))
            except: pass
            
            index_inter = 0 if reussi else index_inter + 1

    finally:
        mgr.stop_driver()

if __name__ == "__main__":
    traiter_toutes_les_interventions()