import time
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

# --- CONFIGURATION UTILISATEUR ---
URL_CONNEXION = "https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING"
VOTRE_IDENTIFIANT = "Centre_RAyinda"
VOTRE_MOT_DE_PASSE = "7LRvuZlqitVMNI4u"
LIEU_CENTRAL_CARTE = input("Entrez le lieu central à rechercher sur la carte (ex: Yaoundé) : ")
TIMEOUT = 60 # Timeout global de 60 secondes pour les attentes principales

# --- GESTION DU DRIVER EDGE ---
class WebDriverManager:
    def __init__(self, timeout):
        self.timeout = timeout
        self.driver = None

    def start_driver(self, headless=False):
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Edge(options=options)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()


# --- FONCTION UTILE POUR CLIQUER SUR "OUI" DANS LES MODALES ---
def cliquer_oui_unifie(driver, timeout=5):
    """
    Clique sur tout bouton d'une modale ui-dialog dont le texte contient 'Oui'.
    """
    try:
        modale = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'ui-dialog') and contains(@style,'display: block') and .//span[contains(text(),'Oui')]]")
            )
        )

        for _ in range(3):
            try:
                bouton_oui = WebDriverWait(modale, 1).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, ".//div[contains(@class,'ui-dialog-buttonset')]/button[span[contains(text(),'Oui')]]")
                    )
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", bouton_oui)
                driver.execute_script("arguments[0].click();", bouton_oui)
                print("✅ Clic sur le bouton 'Oui' effectué dans la modale.")

                WebDriverWait(driver, timeout).until(
                    EC.invisibility_of_element_located(
                        (By.XPATH, "//div[contains(@class,'ui-dialog') and contains(@style,'display: block')]")
                    )
                )
                time.sleep(0.3)
                return
            except StaleElementReferenceException:
                time.sleep(0.2)
                continue

        print("⚠️ Impossible de cliquer sur un bouton 'Oui' après retry.")

    except TimeoutException:
        print("⚠️ Aucune modale de type 'Oui/Non' apparue.")
    except Exception as e:
        print(f"❌ Erreur lors du clic sur le bouton 'Oui' : {e}")

# --- FONCTION PRINCIPALE ---
def traiter_toutes_les_interventions():
    driver_manager = WebDriverManager(timeout=TIMEOUT)
    driver = None
    try:
        # --- Initialisation du driver ---
        print("\n🚀 Démarrage du driver Edge...")
        driver = driver_manager.start_driver(headless=False) 
        wait = WebDriverWait(driver, TIMEOUT)

        # --- Connexion ---
        print(f"Ouverture de la page : {URL_CONNEXION}")
        driver.get(URL_CONNEXION)
        wait.until(EC.element_to_be_clickable((By.ID, "in_username"))).send_keys(VOTRE_IDENTIFIANT)
        wait.until(EC.element_to_be_clickable((By.ID, "in_password"))).send_keys(VOTRE_MOT_DE_PASSE)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@class, 'newimgbtn')]"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
        print("✅ Connexion réussie.")

        # --- Passage portail ---
        try:
            portail_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "portail")))
            driver.execute_script("arguments[0].click();", portail_btn)
        except:
            pass

        # --- Page Intervention ---
        wait.until(EC.presence_of_element_located((By.ID, "menudiv")))
        intervention_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'INTER_PENDING')]")))
        driver.execute_script("arguments[0].click();", intervention_btn)
        wait.until(EC.presence_of_element_located((By.ID, "home_body")))
        print("✅ Page Intervention chargée.")

        # --- Filtre "A qualifier" ---
        span_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "intervention_status_select-button")))
        span_dropdown.click() 
        time.sleep(0.5)
        
        option_a_qualifier = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//ul[@id='intervention_status_select-menu']/li[text()='A qualifier']")))
        
        option_a_qualifier.click()
        print("🎯 Filtre appliqué : A qualifier")
        time.sleep(2) 

        # --- Boucle de traitement ---
        onglet_parent = driver.current_window_handle
        xpath_liens = "#tbl_inter_pending tbody tr:not(.dataTables_empty) td:nth-child(1) a"
        liens = driver.find_elements(By.CSS_SELECTOR, xpath_liens)
        nombre_interventions = len(liens)
        print(f"Nombre d'interventions : {nombre_interventions}")

        i = 0
        while i < nombre_interventions:
            try:
                liens_actuels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, xpath_liens)))
                lien = liens_actuels[0] 
                numero_ref = lien.text.strip()
                print(f"\n--- Traitement intervention {i + 1} : {numero_ref} ---")
                
                driver.execute_script("arguments[0].click();", lien)
                wait.until(EC.number_of_windows_to_be(2))

                # --- Bascule vers onglet détail ---
                for wh in driver.window_handles:
                    if wh != onglet_parent:
                        driver.switch_to.window(wh)
                        break
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))

                # --- Accordéon RDV ---
                xpath_accordion = "//h3[@id='ui-id-7' or contains(., 'RDV')]"
                accordion_rdv = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_accordion)))
                if accordion_rdv.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion_rdv)
                    time.sleep(0.5)

                # --- Planification ---
                wait.until(EC.element_to_be_clickable((By.ID, "btn_inter_plan"))).click()
                print("-> Clic sur Planification")

                # --- Modale confirmation date (Modale 3) ---
                try:
                    modale_3_id = "inter_confirm_plan"
                    wait.until(EC.presence_of_element_located((By.XPATH, f"//div[@aria-describedby='{modale_3_id}']")))
                    xpath_confirmer = f"//div[@aria-describedby='{modale_3_id}']//span[text()='Confirmer']/parent::button"
                    wait.until(EC.element_to_be_clickable((By.XPATH, xpath_confirmer)))
                    driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, xpath_confirmer))
                    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, modale_3_id)))
                    print("-> Modale 3 confirmée")
                except TimeoutException:
                    print("-> Modale 3 non apparue ou confirmée")

                # --- Modale planification carte (Modale 4) ---
                modale_4_id = "inter_plan_dialog"
                wait.until(EC.presence_of_element_located((By.ID, modale_4_id)))

                # 1. Recherche du lieu (Déplacement de la carte au bon endroit)
                search_input = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[@id='{modale_4_id}']//input[@type='text']")))
                search_input.send_keys(LIEU_CENTRAL_CARTE)
                search_input.send_keys(Keys.ENTER)
                print(f"-> Recherche de la carte déplacée sur : {LIEU_CENTRAL_CARTE}")
                
                time.sleep(4) 
                
                # 2. Détermination technicien cible pour la carte
                technicien_cible = "FOKANA STEPHANE" if (i+1) % 2 != 0 else "FOKANA STEPHANE" #"MFONDI DAOUDA FALL"
                
                # 3. Cibler et cliquer le polygone SVG
                xpath_polygone_svg = "#gmaps_canvas .leaflet-overlay-pane svg path.leaflet-interactive"
                print(f"-> Cible technique carte : {technicien_cible}. Tentative de clic SVG...")

                try:
                    polygone_elem = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, xpath_polygone_svg))
                    )
                    ActionChains(driver).move_to_element(polygone_elem).click().perform()
                    print(f"✅ Clic SVG réussi sur le polygone de la zone.")

                except TimeoutException:
                    print("❌ Erreur: Polygone SVG cliquable introuvable. Tentative de Fallback (clic au centre).")
                    map_elem = driver.find_element(By.ID, "gmaps_canvas")
                    ActionChains(driver).move_to_element(map_elem).click().perform()
                    
                time.sleep(1) 

                # 4. LOGIQUE DE CONTINGENCE : Valider Modale 4 OU détecter Modale 5
                xpath_bouton_valider = f"//div[@id='{modale_4_id}']//input[@type='button' and @value='Valider']"
                modale_5_id = "confirm_position_dialog" 

                try:
                    bouton_valider = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                        (By.XPATH, xpath_bouton_valider)))
                    driver.execute_script("arguments[0].click();", bouton_valider)
                    print("✅ Clic sur 'Valider' Modale 4 effectué.")
                    
                    time.sleep(1)
                    cliquer_oui_unifie(driver, timeout=5)

                except TimeoutException:
                    print("⚠️ Bouton 'Valider' (Modale 4) introuvable ou inactif après 5s. Vérification Modale 5 (apparition directe)...")
                    
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located(
                                (By.XPATH, f"//div[@aria-describedby='{modale_5_id}' and contains(@style,'display: block')]")
                            )
                        )
                        print("✅ Modale de confirmation du lieu (Modale 5) détectée directement. Clic sur 'Oui'.")
                        cliquer_oui_unifie(driver, timeout=5)
                        
                    except TimeoutException:
                        print(f"❌ Échec critique : Ni le bouton 'Valider' (Modale 4) ni la Modale 5 ('{modale_5_id}') n'ont été trouvés.")
                        raise

                # --- Actualisation et Affectation technicien ---
                driver.refresh()
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                
                accordion_rdv = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_accordion)))
                if accordion_rdv.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion_rdv)
                    time.sleep(0.5)

                wait.until(EC.element_to_be_clickable((By.ID, "inter_affect_tech_btn"))).click()
                print("-> Clic sur Affecter un technicien")
                
                time.sleep(1) 
                
                # Fenêtre d'affectation techniciens (affect_tech_div_dt)
                wait.until(EC.presence_of_element_located((By.ID, "affect_tech_div_dt")))
                
                # --- Phase 1: Planification du RDV (Technicien) ---
                technicien_cible_affectation = "FOKANA STEPHANE" if (i+1) % 2 != 0 else "FOKANA STEPHANE"#"MFONDI DAOUDA FALL"
                
                print(f"-> Tentative de planification du seul technicien autorisé : {technicien_cible_affectation}")

                try:
                    xpath_tech = f"//table[@id='affect_tech_table_dt']/tbody/tr[td[contains(text(), '{technicien_cible_affectation}')]]//button[text()='Planifier']"
                    
                    bouton_planifier = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_tech)))
                    driver.execute_script("arguments[0].click();", bouton_planifier)
                    print(f"✅ Technicien {technicien_cible_affectation} planifié avec succès.")
                    
                    # Fermeture de la fenêtre d'affectation après la sélection du technicien
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.ID, "affect_tech_div_dt"))
                    )
                    
                except TimeoutException:
                    raise NoSuchElementException(f"Technicien requis ({technicien_cible_affectation}) introuvable ou bouton 'Planifier' inaccessible dans la liste.")


                # -------------------------------------------------------------
                # Phase 2 : Lancement Modale Notifications (via valid_affecter_inter) et Validation
                # -------------------------------------------------------------
                
                # 1. Cliquer sur le bouton 'Valider' qui ouvre la modale de notifications
                print("-> Clic sur le bouton de Validation finale de l'affectation (valid_affecter_inter) pour ouvrir la modale.")
                wait.until(EC.element_to_be_clickable((By.ID, "valid_affecter_inter"))).click()
                
                # 2. Gestion de la Modale de Notifications (dialog_prompt_confirm)
                modale_confirm_id = "dialog_prompt_confirm"
                
                # Attendre l'apparition de la modale
                modale_element = wait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, f"//div[@aria-describedby='{modale_confirm_id}' and contains(@style,'display: block')]")
                    )
                )
                print("-> Modale de confirmation/notifications détectée.")
                
                # Désactiver les cases à cocher (Elles sont cochées par défaut)
                checkboxes_ids = ["notif_msg", "notif_mail", "notif_sms"]
                for checkbox_id in checkboxes_ids:
                    try:
                        checkbox = modale_element.find_element(By.ID, checkbox_id)
                        if checkbox.is_selected():
                             driver.execute_script("arguments[0].click();", checkbox)
                             print(f"   Désactivation de la notification : {checkbox_id}")
                    except NoSuchElementException:
                        print(f"   Avertissement : Checkbox {checkbox_id} non trouvée.")

                # Cliquer sur le bouton 'Valider' de la modale de notifications
                xpath_valider_modale = f"//div[@aria-describedby='{modale_confirm_id}']//div[@class='ui-dialog-buttonset']/button[span[text()='Valider']]"
                wait.until(EC.element_to_be_clickable((By.XPATH, xpath_valider_modale))).click()
                print("✅ Clic sur 'Valider' de la modale de notifications.")
                
                # Attendre que la modale disparaisse
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.ID, modale_confirm_id))
                )
                
                # -------------------------------------------------------------
                wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
                accordion_rdv = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_accordion)))
                if accordion_rdv.get_attribute("aria-expanded") == "false":
                    driver.execute_script("arguments[0].click();", accordion_rdv)
                    time.sleep(0.5)

                # --- Phase 3 : Refuser intervention (fin du processus) ---
                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Refuser' and @onclick='accepter_inter(0);']"))).click()
                cliquer_oui_unifie(driver, timeout=10) 
                
                # --- Retour onglet principal ---
                driver.close()
                driver.switch_to.window(onglet_parent)
                # cliquer sur le bouton valider pour que la requette traitée quitte du panier  id="btn_period_valid"
                wait.until(EC.element_to_be_clickable((By.ID, "btn_period_valid"))).click()
                time.sleep(2)

                wait.until(EC.presence_of_element_located((By.ID, "tbl_inter_pending")))
                
                i += 1

            except Exception as e:
                print(f"❌ Erreur critique intervention {i+1} : {type(e).__name__} - {e}")
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(onglet_parent)
                except:
                    pass
                i += 1
                continue

        print("\n🎉 Toutes les interventions traitées !")

    except Exception as e_global:
        print(f"❌ Erreur globale fatale : {type(e_global).__name__} - {e_global}")
        if driver:
            driver.save_screenshot(os.path.join(os.getcwd(), "erreur_processus.png"))
    finally:
        if driver_manager:
            driver_manager.stop_driver()
            print("🛑 Fermeture du navigateur.")


# --- EXECUTION ---
if __name__ == "__main__":
    if not LIEU_CENTRAL_CARTE:
        print("Erreur: Le lieu central de carte ne doit pas être vide.")
    else:
        traiter_toutes_les_interventions()