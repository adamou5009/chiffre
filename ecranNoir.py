# --------------------------------------------
# CANAL+ ServicePlus – Version Finale
# Clic direct sur coordonnées GPS (100% fiable)
# --------------------------------------------
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.edge.service import Service as EdgeService
import os
# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- CONFIG UTILISATEUR ----------
URL_CONNEXION = "https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING"
VOTRE_IDENTIFIANT = "Centre_RAyinda"
VOTRE_MOT_DE_PASSE = "L4E3FrOes4bgNJar"

# Configuration des zones et techniciens
ZONES_CONFIG = {
    'mfoundi': {
        'latitude': 3.841309,
        'longitude': 11.492995,
        'technicien': 'FOKANA STEPHANE'
    },
    'yaounde': {
        'latitude': 3.8480,
        'longitude': 11.5021,
        'technicien': 'MFONDI DAOUDA FALL'
    }
}

# Choisir la zone à utiliser (changez ici selon vos besoins)
ZONE_ACTIVE = input("mfoundi'  # ou 'yaounde': ").strip().lower()
TIMEOUT = 60
MODE_HEADLESS = True

# ---------- DRIVER MANAGER ----------
class WebDriverManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.driver = None

class WebDriverManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.driver = None

    def start_driver(self, headless=False):
        options = webdriver.EdgeOptions()
        
        # Désactiver tous les logs du navigateur - NIVEAU MAXIMAL
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Supprimer TOUS les messages d'erreur du navigateur
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-shm-usage")
        
        # Désactiver DevTools
        options.add_argument("--remote-debugging-port=0")  # Désactive "DevTools listening..."
        
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--page-load-strategy=normal")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Désactiver fonctionnalités inutiles
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-features=EdgeBrowserEssentialsButton")  # Edge spécifique
        
        # Services non nécessaires
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        
        try:
            # Supprimer les logs de service (Edge LLM, etc.)
            import warnings
            warnings.filterwarnings('ignore')
            
            # Créer un service silencieux
            service = EdgeService(log_path=os.devnull)
            
            self.driver = webdriver.Edge(service=service, options=options)
            self.driver.set_page_load_timeout(90)
            self.driver.set_script_timeout(30)
            self.driver.implicitly_wait(10)
            return self.driver
        except Exception as e:
            logger.error(f"❌ Impossible de démarrer Edge: {e}")
            raise

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# ---------- UTILITAIRES ----------
def cliquer_oui_unifie(driver, timeout=5):
    """Clic sur bouton Oui dans les modales de confirmation"""
    try:
        modale = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'ui-dialog') and contains(@style,'display: block') and .//span[contains(text(),'Oui')]]")
            )
        )
        btn_oui = WebDriverWait(modale, 2).until(
            EC.element_to_be_clickable(
                (By.XPATH, ".//div[contains(@class,'ui-dialog-buttonset')]/button[span[contains(text(),'Oui')]]")
            )
        )
        driver.execute_script("arguments[0].click();", btn_oui)
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'ui-dialog') and contains(@style,'display: block')]")
            )
        )
        return True
    except TimeoutException:
        return False

#Fonction pour extraires les informations des interventions
from datetime import datetime

def extraire_infos_intervention(driver):
    """
    Ouvre l'accordéon 'Intervention', extrait les infos et vérifie la date.
    Retourne (infos, doit_traiter)
    """
    wait = WebDriverWait(driver, 10)
    infos = {}

    try:
        # 1. Localiser et ouvrir l'accordéon
        accordion_header = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//h3[contains(., 'Intervention')]")
        ))

        if accordion_header.get_attribute("aria-expanded") == "false":
            driver.execute_script("arguments[0].click();", accordion_header)
            time.sleep(0.5)

        # 2. Helper pour extraire les valeurs
        def get_value_by_label(label_text):
            try:
                xpath = f"//label[contains(text(), '{label_text}')]/following-sibling::div[1]"
                element = driver.find_element(By.XPATH, xpath)
                return element.text.strip()
            except:
                return None

        # 3. Extraction des données
        infos['date_creation'] = get_value_by_label("Date de création")
        infos['ref_cga'] = get_value_by_label("Référence CGA")
        infos['nom_rattachement'] = get_value_by_label("Nom du rattachement")

        # 4. LOGIQUE DE COMPARAISON DE DATE
        doit_traiter = True
        if infos['date_creation']:
            try:
                # On extrait la date (format attendu DD/MM/YYYY)
                date_str = infos['date_creation'].split(' ')[0]
                date_objet = datetime.strptime(date_str, "%d/%m/%Y").date()
                aujourdhui = datetime.now().date()

                if date_objet == aujourdhui:
                    logger.info(f"⏭️ Intervention du jour ({date_str}) : ON NE TRAITE PAS.")
                    doit_traiter = False
                else:
                    logger.info(f"✅ Intervention ancienne ({date_str}) : Traitement autorisé.")
            except Exception as e:
                logger.warning(f"⚠️ Erreur format date ({infos['date_creation']}): {e}")

        return infos, doit_traiter

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction : {e}")
        return None, False

# ---------- FONCTION CARTE (CLIC DIRECT SUR COORDONNÉES GPS) ----------
def cliquer_coordonnees_sur_carte(driver, lat: float, lng: float, nom_lieu: str = "") -> bool:
    """
    Clic direct sur des coordonnées GPS précises
    Pas de recherche geocoder = 100% fiable !
    """
    wait = WebDriverWait(driver, 30)
    timestamp = int(time.time())

    def capture(etape):
        try:
            driver.save_screenshot(f"carte_{timestamp}_{etape}.png")
        except:
            pass

    try:
        logger.info(f"🗺️ Clic sur coordonnées: {lat:.6f}, {lng:.6f} ({nom_lieu})")
        
        # 1) Attendre que la carte soit visible
        wait.until(EC.visibility_of_element_located((By.ID, "inter_plan_dialog")))
        
        # 2) Vérifier que Leaflet est chargé
        map_ready = WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return typeof window.map !== 'undefined' && window.map._loaded === true;"
            )
        )
        if not map_ready:
            logger.error("❌ Carte Leaflet non initialisée")
            return False
        
        logger.info("   ✓ Carte chargée")
        #capture("01_carte_initiale")
        
        # 3) Nettoyage des anciens marqueurs
        logger.info("   🧹 Nettoyage des marqueurs...")
        driver.execute_script("""
            if (window.map) {
                map.eachLayer(function(layer) {
                    if (layer instanceof L.Marker || 
                        (layer.options && layer.options.icon)) {
                        map.removeLayer(layer);
                    }
                });
            }
        """)
        
        # 4) Centrer la carte sur les coordonnées avec un bon zoom
        logger.info(f"   → Centrage sur {lat:.6f}, {lng:.6f}...")
        center_result = driver.execute_script("""
            var lat = arguments[0];
            var lng = arguments[1];
            
            try {
                if (window.map) {
                    // Centrer et zoomer sur la position
                    map.setView([lat, lng], 13);  // Zoom 13 = niveau ville
                    return {success: true};
                }
                return {success: false, error: 'Map indisponible'};
            } catch(e) {
                return {success: false, error: e.message};
            }
        """, lat, lng)
        
        if not center_result.get('success'):
            logger.error(f"   ❌ Échec centrage: {center_result.get('error')}")
            return False
        
        # Attendre que le zoom soit terminé
        time.sleep(2.0)
        logger.info("   ✓ Carte centrée")
        capture("02_apres_centrage")
        
        # 5) CLIC DIRECT SUR LES COORDONNÉES EXACTES
        logger.info(f"   → Clic sur les coordonnées exactes...")
        
        click_result = driver.execute_script("""
            var lat = arguments[0];
            var lng = arguments[1];
            
            try {
                if (window.map) {
                    // Créer le point exact
                    var targetLatLng = L.latLng(lat, lng);
                    var containerPoint = map.latLngToContainerPoint(targetLatLng);
                    
                    // Événement MouseEvent natif
                    var clickEvent = new MouseEvent('click', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': containerPoint.x,
                        'clientY': containerPoint.y,
                        'button': 0
                    });
                    
                    // Dispatch sur le container de la carte
                    var mapContainer = map.getContainer();
                    mapContainer.dispatchEvent(clickEvent);
                    
                    // Événement Leaflet
                    map.fireEvent('click', {
                        latlng: targetLatLng,
                        layerPoint: map.latLngToLayerPoint(targetLatLng),
                        containerPoint: containerPoint,
                        originalEvent: clickEvent
                    });
                    
                    return {
                        success: true, 
                        lat: lat.toFixed(6), 
                        lng: lng.toFixed(6)
                    };
                }
                return {success: false, error: 'Map indisponible'};
            } catch(e) {
                return {success: false, error: e.message};
            }
        """, lat, lng)
        
        if click_result.get('success'):
            logger.info(f"   ✓ Clic effectué à: {click_result.get('lat')}, {click_result.get('lng')}")
        else:
            logger.warning(f"   ⚠️ Clic partiel: {click_result.get('error')}")
        
        time.sleep(2.0)
        capture("03_apres_clic")
        
        # 6) VALIDATION
        logger.info("   → Validation de la position...")
        
        # Stratégie A : Modale directe
        if cliquer_oui_unifie(driver, timeout=3):
            logger.info("   ✅ SUCCÈS - Validé via modale directe")
            #capture("04_succes")
            return True
        
        # Stratégie B : Bouton Valider
        try:
            btn_valider = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH, "//div[@id='inter_plan_dialog']//input[@value='Valider']"
                ))
            )
            
            is_visible = driver.execute_script(
                "return arguments[0].offsetParent !== null;", 
                btn_valider
            )
            
            if is_visible:
                logger.info("   → Clic sur bouton 'Valider'")
                driver.execute_script("arguments[0].click();", btn_valider)
                time.sleep(1.5)
                
                if cliquer_oui_unifie(driver, timeout=8):
                    logger.info("   ✅ SUCCÈS - Validé après bouton")
                    #capture("04_succes")
                    return True
                    
        except Exception as e:
            logger.debug(f"   Bouton Valider: {e}")
            capture("erreur de validation")
        
        # Stratégie C : Dernière tentative
        if cliquer_oui_unifie(driver, timeout=3):
            logger.info("   ✅ SUCCÈS - Validation ultime")
            #capture("04_succes")
            return True
        
        logger.error("   ❌ ÉCHEC - Aucune validation n'a fonctionné")
        capture("ERREUR_validation_finale")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        capture("ERREUR_exception")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ---------- TRAITEMENT PRINCIPAL ----------
import time

def traiter_toutes_les_interventions():
    driver_manager = WebDriverManager(timeout=TIMEOUT)
    driver = None
    
    # Variables pour les statistiques
    temps_total_session = 0
    debut_session = time.time()
    
    try:
        logger.info("🚀 Démarrage Edge (headless)...")
        driver = driver_manager.start_driver(headless=MODE_HEADLESS)
        wait = WebDriverWait(driver, TIMEOUT)

        # --- Connexion ---
        logger.info("Connexion...")
        max_retry = 3
        for retry in range(max_retry):
            try:
                driver.get(URL_CONNEXION)
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                username_field = wait.until(EC.presence_of_element_located((By.ID, "in_username")))
                username_field.clear()
                username_field.send_keys(VOTRE_IDENTIFIANT)
                
                password_field = wait.until(EC.presence_of_element_located((By.ID, "in_password")))
                password_field.clear()
                password_field.send_keys(VOTRE_MOT_DE_PASSE)
                
                submit_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and contains(@class, 'newimgbtn')]")))
                submit_btn.click()
                
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                logger.info("✅ Connecté")
                break
            except TimeoutException as e:
                logger.error(f" ❌ Timeout tentative {retry + 1}")
                
                if retry >= max_retry - 1: raise Exception("Échec connexion")
                time.sleep(5)

        # --- Accès Page Interventions ---
        wait.until(EC.presence_of_element_located((By.ID, "menudiv")))
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href, 'INTER_PENDING')]"))))
        wait.until(EC.presence_of_element_located((By.ID, "home_body")))
        logger.info("✅ Page Intervention")

        # --- Filtre ---
        wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='A qualifier']"))).click()
        time.sleep(2)

        # --- Boucle de Traitement ---
        onglet_parent = driver.current_window_handle
        xpath_liens = "#tbl_inter_pending tbody tr:not(.dataTables_empty) td:nth-child(1) a"
        
        i = 0
        succes = 0
        index_intervention = 0

        while True:
            try:
                liens = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, xpath_liens)))
                
                if not liens or index_intervention >= len(liens):
                    logger.info(f"Fin de liste : {len(liens)} liens trouvés.")
                    break
                
                # --- DÉBUT CHRONO INTERVENTION ---
                start_inter = time.time()
                
                lien = liens[index_intervention]
                ref = lien.text.strip()
                logger.info(f"\n{'='*50}\n{i+1}. TRAITEMENT : {ref}\n{'='*50}")

                # Ouverture fiche
                driver.execute_script("arguments[0].click();", lien)
                wait.until(EC.number_of_windows_to_be(2))
                
                for w in driver.window_handles:
                    if w != onglet_parent:
                        driver.switch_to.window(w)
                        break
                
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                # EXtraire les informations 
                infos, doit_traiter = extraire_infos_intervention(driver)
                if not doit_traiter:
                    # on ferme l'onglet 
                    driver.close()
                    # On revient sur la page principale
                    driver.switch_to.window(onglet_parent)
                    # incrermenter l'index pour ne pas ouvrir la même intervention
                    index_intervention += 1
                    continue

                # --- Actions sur la fiche ---
                accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[@id='ui-id-7' or contains(., 'RDV')]")))
                if accordion.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion)
                    time.sleep(0.5)

                wait.until(EC.element_to_be_clickable((By.ID, "btn_inter_plan"))).click()
                
                try:
                    modale_3_id = "inter_confirm_plan"
                    wait.until(EC.presence_of_element_located((By.XPATH, f"//div[@aria-describedby='{modale_3_id}']")))
                    driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//div[@aria-describedby='{modale_3_id}']//span[text()='Confirmer']/parent::button"))))
                    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, modale_3_id)))
                except: pass

                # Carte
                wait.until(EC.presence_of_element_located((By.ID, "inter_plan_dialog")))
                config_zone = ZONES_CONFIG[ZONE_ACTIVE]
                if not cliquer_coordonnees_sur_carte(driver, config_zone['latitude'], config_zone['longitude'], ZONE_ACTIVE.upper()):
                    raise Exception("Échec localisation carte")

                # Actualisation & Affectation
                driver.refresh()
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                
                
                accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[@id='ui-id-7' or contains(., 'RDV')]")))
                if accordion.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion)

                driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "inter_affect_tech_btn"))))
                wait.until(EC.presence_of_element_located((By.ID, "affect_tech_div_dt")))
                
                technicien = config_zone['technicien']
                xpath_tech = f"//table[@id='affect_tech_table_dt']/tbody/tr[td[contains(text(), '{technicien}')]]//button[text()='Planifier']"
                driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.XPATH, xpath_tech))))

                driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "valid_affecter_inter"))))
                
                # Fermeture et Retour
                driver.close()
                driver.switch_to.window(onglet_parent)
                
                driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.ID, "btn_period_valid"))))
                time.sleep(3)
                
                # --- FIN CHRONO INTERVENTION ---
                end_inter = time.time()
                duree = end_inter - start_inter
                temps_total_session += duree
                
                index_intervention = 0 
                succes += 1
                i += 1
                logger.info(f"✅ {ref} terminé en {int(duree)}s")

            except Exception as e:
                logger.error(f"❌ Erreur critique sur {ref if 'ref' in locals() else 'inconnu'}: {str(e)}")
                
                try:
                    current_handles = driver.window_handles
                    if len(current_handles) > 1:
                        if driver.current_window_handle != onglet_parent:
                            driver.close()
                    driver.switch_to.window(onglet_parent)
                    index_intervention += 1 
                    logger.info("♻️ Recouvrement réussi, passage au suivant.")
                except: break 
                continue

        # --- RAPPORT DE PERFORMANCE FINAL ---
        if succes > 0:
            moyenne = temps_total_session / succes
            logger.info(f"\n" + "="*50)
            logger.info(f"📊 RAPPORT DE PERFORMANCE")
            logger.info(f"Total traitées : {succes}")
            logger.info(f"Temps total    : {int(temps_total_session // 60)}m {int(temps_total_session % 60)}s")
            logger.info(f"Moyenne/fiche  : {int(moyenne)} secondes")
            logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ ERREUR GLOBALE: {e}")
    finally:
        if driver: driver_manager.stop_driver()
        logger.info("🛑 Fin du script")


# ---------- LANCEMENT ----------
if __name__ == "__main__":
    logger.info("⚠️ MODE HEADLESS - Le navigateur sera invisible")
    
    config_zone = ZONES_CONFIG[ZONE_ACTIVE]
    logger.info(f"📍 Zone active: {ZONE_ACTIVE.upper()}")
    logger.info(f"📍 Coordonnées: {config_zone['latitude']}, {config_zone['longitude']}")
    logger.info(f"👷 Technicien: {config_zone['technicien']}")
    logger.info(f"🔐 Identifiant: {VOTRE_IDENTIFIANT}")
    logger.info("="*60)
    
    traiter_toutes_les_interventions()