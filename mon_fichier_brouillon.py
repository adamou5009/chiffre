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

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- CONFIG UTILISATEUR ----------
URL_CONNEXION = "https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING"
VOTRE_IDENTIFIANT = "Centre_RAyinda"
VOTRE_MOT_DE_PASSE = "7LRvuZlqitVMNI4u"

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

# Choisir la zone à utiliser
print("Zones disponibles: mfoundi, yaounde")
ZONE_ACTIVE = input("Entrez la zone à traiter: ").strip().lower()

if ZONE_ACTIVE not in ZONES_CONFIG:
    print(f"❌ Zone '{ZONE_ACTIVE}' inconnue. Utilisation de 'mfoundi' par défaut.")
    ZONE_ACTIVE = 'mfoundi'

TIMEOUT = 60
MODE_HEADLESS = True

#capturer les erreurs
import os
from datetime import datetime

def capturer_erreur(driver, nom_erreur="crash", ref_inter=""):
    """
    Prend une capture d'écran et l'enregistre dans le dossier 'logs_erreurs'.
    """
    try:
        # Créer le dossier s'il n'existe pas
        dossier_logs = "logs_erreurs"
        if not os.path.exists(dossier_logs):
            os.makedirs(dossier_logs)

        # Formater le nom du fichier
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
        ref_inter_propre = ref_inter.replace("/", "_").replace(" ", "")
        nom_fichier = f"{horodatage}_{nom_erreur}_{ref_inter_propre}.png"
        chemin_complet = os.path.join(dossier_logs, nom_fichier)

        # Prendre la capture
        driver.save_screenshot(chemin_complet)
        logger.info(f"📸 Capture d'écran enregistrée : {chemin_complet}")
        return chemin_complet
    except Exception as e:
        logger.error(f"⚠️ Impossible de prendre la capture d'écran : {e}")
        return None





# ---------- DRIVER MANAGER ----------
class WebDriverManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.driver = None

    def start_driver(self, headless=True):
        options = webdriver.EdgeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--page-load-strategy=normal")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Edge(options=options)
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


# ---------- FONCTION CARTE (CLIC DIRECT SUR COORDONNÉES GPS) ----------
def cliquer_coordonnees_sur_carte(driver, lat: float, lng: float, nom_lieu: str = "") -> bool:
    """
    Clic direct sur des coordonnées GPS précises
    Pas de recherche geocoder = 100% fiable !
    """
    wait = WebDriverWait(driver, 30)

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
        
        # 3) Nettoyage des anciens marqueurs
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
        
        # 4) Centrer la carte sur les coordonnées
        logger.info(f"   → Centrage sur {lat:.6f}, {lng:.6f}...")
        center_result = driver.execute_script("""
            var lat = arguments[0];
            var lng = arguments[1];
            
            try {
                if (window.map) {
                    map.setView([lat, lng], 13);
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
        
        time.sleep(2.0)
        logger.info("   ✓ Carte centrée")
        
        # 5) CLIC DIRECT SUR LES COORDONNÉES EXACTES
        click_result = driver.execute_script("""
            var lat = arguments[0];
            var lng = arguments[1];
            
            try {
                if (window.map) {
                    var targetLatLng = L.latLng(lat, lng);
                    var containerPoint = map.latLngToContainerPoint(targetLatLng);
                    
                    var clickEvent = new MouseEvent('click', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': containerPoint.x,
                        'clientY': containerPoint.y,
                        'button': 0
                    });
                    
                    map.getContainer().dispatchEvent(clickEvent);
                    
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
        
        # 6) VALIDATION
        logger.info("   → Validation...")
        
        # Stratégie A : Modale directe
        if cliquer_oui_unifie(driver, timeout=3):
            logger.info("   ✅ Validé")
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
                driver.execute_script("arguments[0].click();", btn_valider)
                time.sleep(1.5)
                
                if cliquer_oui_unifie(driver, timeout=8):
                    logger.info("   ✅ Validé")
                    return True
                    
        except:
            pass
        
        # Stratégie C : Dernière tentative
        if cliquer_oui_unifie(driver, timeout=3):
            logger.info("   ✅ Validé")
            return True
        
        logger.error("   ❌ Échec validation")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur carte: {e}")
        return False


# ---------- TRAITEMENT PRINCIPAL ----------
def traiter_toutes_les_interventions():
    driver_manager = WebDriverManager(timeout=TIMEOUT)
    driver = None
    
    try:
        logger.info("🚀 Démarrage Edge (headless)...")
        driver = driver_manager.start_driver(headless=MODE_HEADLESS)
        wait = WebDriverWait(driver, TIMEOUT)

        # Connexion
        logger.info("Connexion...")
        for retry in range(3):
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
                
            except TimeoutException:
                if retry < 2:
                    time.sleep(5)
                else:
                    raise Exception("Échec connexion")

        # Menu Interventions
        wait.until(EC.presence_of_element_located((By.ID, "menudiv")))
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href, 'INTER_PENDING')]"))))
        wait.until(EC.presence_of_element_located((By.ID, "home_body")))
        logger.info("✅ Page Intervention")

        # Filtre A qualifier
        logger.info("🎯 Filtre 'A qualifier'...")
        wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='A qualifier']"))).click()
        time.sleep(2)

        # Boucle interventions avec pagination
        onglet_parent = driver.current_window_handle
        xpath_liens = "#tbl_inter_pending tbody tr:not(.dataTables_empty) td:nth-child(1) a"
        
        i = 0
        succes = 0
        page = 1
        
        while True:
            # Vérifier s'il y a des interventions sur cette page
            try:
                liens = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, xpath_liens))
                )
            except TimeoutException:
                logger.info("ℹ️ Plus d'interventions à traiter")
                break
            
            if not liens:
                logger.info("ℹ️ Page vide, fin du traitement")
                break
            
            logger.info(f"\n📄 PAGE {page} - {len(liens)} intervention(s)")
            
            # Traiter TOUTES les interventions de la page courante
            for idx in range(len(liens)):
                try:
                    # Recharger la liste à chaque itération (car le DOM change)
                    liens = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, xpath_liens)))
                    
                    if idx >= len(liens):
                        logger.warning(f"⚠️ Index {idx} hors limites, page suivante")
                        break
                    
                    lien = liens[idx]
                    ref = lien.text.strip()
                    logger.info(f"\n{'='*50}\n{i+1}. {ref} (page {page}, #{idx+1})\n{'='*50}")
                except Exception as e:
                    logger.error(f"❌ Erreur récupération lien intervention #{i+1}: {e}")
                    continue
                driver.execute_script("arguments[0].click();", liens[0])
                wait.until(EC.number_of_windows_to_be(2))
                
                for w in driver.window_handles:
                    if w != onglet_parent:
                        driver.switch_to.window(w)
                        break
                
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))

                # Accordéon RDV
                accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[@id='ui-id-7' or contains(., 'RDV')]")))
                if accordion.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion)
                    time.sleep(0.5)

                # Planification
                wait.until(EC.element_to_be_clickable((By.ID, "btn_inter_plan"))).click()
                logger.info("→ Planification")

                # Modale date
                try:
                    modale_3_id = "inter_confirm_plan"
                    wait.until(EC.presence_of_element_located((By.XPATH, f"//div[@aria-describedby='{modale_3_id}']")))
                    driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//div[@aria-describedby='{modale_3_id}']//span[text()='Confirmer']/parent::button"))))
                    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, modale_3_id)))
                except TimeoutException:
                    pass

                # Carte - CLIC DIRECT SUR COORDONNÉES
                wait.until(EC.presence_of_element_located((By.ID, "inter_plan_dialog")))
                
                config_zone = ZONES_CONFIG[ZONE_ACTIVE]
                if not cliquer_coordonnees_sur_carte(
                    driver, 
                    config_zone['latitude'], 
                    config_zone['longitude'],
                    ZONE_ACTIVE.upper()
                ):
                    raise Exception("Échec localisation")

                # Actualiser
                driver.refresh()
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                
                accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[@id='ui-id-7' or contains(., 'RDV')]")))
                if accordion.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion)
                    time.sleep(0.5)

                # Affecter technicien
                logger.info("→ Affectation")
                
                btn_affect = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "inter_affect_tech_btn"))
                )
                driver.execute_script("arguments[0].click();", btn_affect)
                
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "affect_tech_div_dt"))
                )
                time.sleep(2)
                
                technicien = config_zone['technicien']
                xpath_tech = f"//table[@id='affect_tech_table_dt']/tbody/tr[td[contains(text(), '{technicien}')]]//button[text()='Planifier']"
                
                btn_planifier = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_tech))
                )
                driver.execute_script("arguments[0].click();", btn_planifier)
                logger.info(f"   ✓ {technicien}")
                time.sleep(1)

                # Validation affectation
                btn_valid_affect = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "valid_affecter_inter"))
                )
                driver.execute_script("arguments[0].click();", btn_valid_affect)
                
                modale_confirm_id = "dialog_prompt_confirm"
                modale_elem = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((
                        By.XPATH, f"//div[@aria-describedby='{modale_confirm_id}' and contains(@style,'display: block')]"
                    ))
                )
                
                for cb_id in ["notif_msg", "notif_mail", "notif_sms"]:
                    try:
                        cb = modale_elem.find_element(By.ID, cb_id)
                        if cb.is_selected():
                            driver.execute_script("arguments[0].click();", cb)
                    except NoSuchElementException:
                        pass
                
                btn_valider_modale = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH, f"//div[@aria-describedby='{modale_confirm_id}']//span[text()='Valider']/parent::button"
                    ))
                )
                driver.execute_script("arguments[0].click();", btn_valider_modale)
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.ID, modale_confirm_id))
                )
                time.sleep(2)
                
                # Refuser
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                accordion = wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[@id='ui-id-7' or contains(., 'RDV')]")))
                if accordion.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion)
                    time.sleep(0.5)

                btn_refuser = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((
                        By.XPATH, "//button[text()='Refuser' and @onclick='accepter_inter(0);']"
                    ))
                )
                driver.execute_script("arguments[0].click();", btn_refuser)
                cliquer_oui_unifie(driver, timeout=10)
                logger.info("✅ Refusée")
                
                # Retour à la liste (GESTION ROBUSTE)
                try:
                    driver.close()
                    
                    # Vérifier que l'onglet parent existe
                    if onglet_parent in driver.window_handles:
                        driver.switch_to.window(onglet_parent)
                    else:
                        driver.switch_to.window(driver.window_handles[0])
                        logger.warning("⚠️ Onglet parent fermé")
                    
                    try:
                        btn_period = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.ID, "btn_period_valid"))
                        )
                        driver.execute_script("arguments[0].click();", btn_period)
                    except TimeoutException:
                        logger.warning("⚠️ Bouton période non trouvé, rechargement")
                        driver.refresh()
                    
                    time.sleep(3)
                    wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                    
                except Exception as return_error:
                    logger.error(f"❌ Erreur retour: {return_error}")
                    if len(driver.window_handles) > 0:
                        driver.switch_to.window(driver.window_handles[0])
                        driver.get(URL_CONNEXION + "&action=INTER_PENDING")
                        time.sleep(3)
                        wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                
                    succes += 1
                    logger.info(f"✅ {ref} OK")
                    i += 1

                except Exception as e:
                    logger.error(f"❌ Erreur intervention #{i+1}: {str(e)}")
                    
                    # GESTION ROBUSTE DES FENÊTRES
                    try:
                        handles = driver.window_handles
                        
                        if len(handles) > 1:
                            for handle in handles[1:]:
                                try:
                                    driver.switch_to.window(handle)
                                    driver.close()
                                except:
                                    pass
                            
                            try:
                                driver.switch_to.window(handles[0])
                            except:
                                driver.switch_to.window(driver.window_handles[0])
                        
                        try:
                            wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                        except:
                            driver.get(URL_CONNEXION + "&action=INTER_PENDING")
                            time.sleep(3)
                            wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                            
                    except Exception as window_error:
                        logger.error(f"❌ Erreur récupération: {window_error}")

                        break
                    
                    i += 1
                    time.sleep(2)
                    continue
            
            # FIN DE LA BOUCLE FOR (toutes les interventions de la page traitées)
            logger.info(f"✅ Page {page} terminée")
            
            # Passer à la page suivante
            try:
                # Chercher le bouton "Suivant"
                btn_suivant = driver.find_element(By.ID, "tbl_inter_pending_next")
                
                # Vérifier s'il est désactivé (dernière page)
                if "ui-state-disabled" in btn_suivant.get_attribute("class"):
                    logger.info("ℹ️ Dernière page atteinte")
                    break
                
                # Cliquer sur Suivant
                driver.execute_script("arguments[0].click();", btn_suivant)
                logger.info(f"→ Passage à la page {page + 1}")
                time.sleep(3)
                
                # Attendre que le tableau soit rechargé
                wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                time.sleep(1)
                
                page += 1
                
            except NoSuchElementException:
                logger.info("ℹ️ Bouton Suivant non trouvé, fin")
                break
            except Exception as e:
                logger.error(f"❌ Erreur pagination: {e}")
                break

        logger.info(f"\n🎉 Terminé ! {succes} intervention(s) traitée(s)")

    except Exception as e:
        logger.error(f"❌ ERREUR GLOBALE: {e}")
        if driver:
            capturer_erreur(driver, nom_erreur="erreur_globale")
    finally:
        driver_manager.stop_driver()
        logger.info("🛑 Fermé")


# ---------- LANCEMENT ----------
if __name__ == "__main__":
    logger.info("⚠️ MODE HEADLESS - Le navigateur sera invisible")
    
    config_zone = ZONES_CONFIG[ZONE_ACTIVE]
    logger.info(f"📍 Zone: {ZONE_ACTIVE.upper()}")
    logger.info(f"📍 Coordonnées: {config_zone['latitude']}, {config_zone['longitude']}")
    logger.info(f"👷 Technicien: {config_zone['technicien']}")
    logger.info("="*60)
    
    traiter_toutes_les_interventions()