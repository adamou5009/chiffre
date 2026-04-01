from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import time
import os

# =============================================================
# 🚗 GESTIONNAIRE DU WEBDRIVER IMPORTÉ
# Assurez-vous que le fichier config_driver.py est présent
from config_driver import WebDriverManager, TIMEOUT
# =============================================================


# --- CONSTANTES GLOBALES ---
# Liste des six statuts qui vous intéressent, dans l'ordre de recherche souhaité.
STATUTS_RECHERCHE = [
    "A qualifier", 
    "A planifier", 
    "Planifiée", 
    "Acceptée", 
    "Terminée OK", 
    "Validée", 
    "annulée"
]
# Nom du fichier pour enregistrer le résultat
RESULTAT_FILENAME = "resultat_verification_statut.csv" 


# -------------------------------------------------------------
# 🛠️ FONCTIONS PRINCIPALES DE SÉLÉNIUM
# -------------------------------------------------------------

def connexion_alonwa(driver_instance, url, username, password, timeout=TIMEOUT):
    """Initialise la connexion à l'application."""
    wait = WebDriverWait(driver_instance, timeout)
    
    try:
        print(f"\nOuverture de la page : {url}")
        driver_instance.get(url)

        # Champs de connexion
        champ_identifiant = wait.until(EC.element_to_be_clickable((By.ID, "in_username")))
        champ_mot_de_passe = wait.until(EC.element_to_be_clickable((By.ID, "in_password")))
        
        champ_identifiant.send_keys(username)
        champ_mot_de_passe.send_keys(password)

        # Bouton de connexion
        bouton_connexion = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@class, 'newimgbtn')]"))
        )
        bouton_connexion.click()
        
        # Validation de la connexion
        wait.until(EC.presence_of_element_located((By.ID, "divContainer")))
        print("✅ Connexion réussie et page 'divContainer' chargée !")
        
        return True, driver_instance, wait
    
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"❌ Erreur lors de la connexion. Erreur : {e.__class__.__name__}")
        return False, None, None

def naviguer_page_intervention(driver_instance, wait):
    """Clique sur le lien 'Intervention' pour naviguer vers la page de liste."""
    try:
        wait.until(EC.presence_of_element_located((By.ID, "menudiv"))) 
        intervention_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'INTER_PENDING')]"))
        )
        driver_instance.execute_script("arguments[0].click();", intervention_btn)
        
        wait.until(EC.presence_of_element_located((By.ID, "home_body"))) 
        print("✅ Page Intervention chargée.")
        return True
    except (TimeoutException, StaleElementReferenceException) as e:
        print(f"❌ Erreur lors du clic sur 'intervention' : {e.__class__.__name__}")
        return False


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time

def trouver_statut_intervention_specifique(driver, wait, numero_recherche):
    DROPDOWN_ID = "intervention_status_select-button"
    MENU_ID = "intervention_status_select-menu"
    VALIDER_ID = "btn_period_valid"
    SEARCH_XPATH = "//input[@type='search' and contains(@aria-controls, 'tbl_inter_pending')]"

    STATUTS_MAP = {
        "A qualifier":  "A qualifier",
        "A planifier":  "A planifier",
        "Planifiée":    "Planifiée",
        "Acceptée":     "Acceptée",
        "Terminée OK":  "Terminée OK",
        "Validée":      "Validée",
        "annulée":       "Annulée"
    }

    def attendre_tableau_charge(driver, timeout=10):
        """Attendre que le tableau contienne au moins une ligne valide"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(d.find_elements(
                    By.XPATH,
                    "//table[@id='tbl_inter_pending']/tbody/tr[not(contains(@class,'dataTables_empty'))]"
                )) >= 0
            )
            return True
        except TimeoutException:
            return False

    def cliquer_option(driver, wait, texte_menu, menu_id):
        """Cliquer sur l’option du menu avec retry pour StaleElementReference"""
        for _ in range(3):
            try:
                xpath_option = f"//ul[@id='{menu_id}']/li[contains(normalize-space(), '{texte_menu}')]"
                option = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_option)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                ActionChains(driver).move_to_element(option).click().perform()
                return True
            except StaleElementReferenceException:
                time.sleep(0.2)
        return False

    for statut_logique, texte_menu in STATUTS_MAP.items():
        print(f"\n🔍 Test du statut : {statut_logique}")

        try:
            # 1️⃣ Ouvrir le menu dropdown
            dropdown = wait.until(EC.element_to_be_clickable((By.ID, DROPDOWN_ID)))
            driver.execute_script("arguments[0].click();", dropdown)
            time.sleep(0.2)

            # 2️⃣ Cliquer sur l’option
            if not cliquer_option(driver, wait, texte_menu, MENU_ID):
                print(f"⚠ Impossible de sélectionner le statut {statut_logique}")
                continue
            #print(f"-> Statut sélectionné : {texte_menu}")

            # 3️⃣ Valider le filtre
            for _ in range(3):
                try:
                    bouton_valider_filtre = wait.until(
                        EC.element_to_be_clickable((By.ID, VALIDER_ID))
                    )
                    driver.execute_script("arguments[0].click();", bouton_valider_filtre)
                    break
                except StaleElementReferenceException:
                    time.sleep(0.2)

            # 4️⃣ Saisir le numéro dans le champ de recherche
            search = wait.until(EC.presence_of_element_located((By.XPATH, SEARCH_XPATH)))
            search.clear()
            search.send_keys(numero_recherche)
            time.sleep(0.3)

            # 5️⃣ Valider la recherche
            for _ in range(3):
                try:
                    bouton_valider_recherche = wait.until(
                        EC.element_to_be_clickable((By.ID, VALIDER_ID))
                    )
                    driver.execute_script("arguments[0].click();", bouton_valider_recherche)
                    break
                except StaleElementReferenceException:
                    time.sleep(0.2)

            # ⏱ Attendre 5 secondes pour que le tableau se mette à jour
            time.sleep(5)
            attendre_tableau_charge(driver)

            # 6️⃣ Parcourir toutes les pages du tableau
            numero_trouve = False
            try:
                driver.find_element(By.ID, "tbl_inter_pending_first").click()
                attendre_tableau_charge(driver)
            except:
                pass

            while True:
                lignes = driver.find_elements(By.XPATH,
                    "//table[@id='tbl_inter_pending']/tbody/tr[not(contains(@class,'dataTables_empty'))]"
                )
                for tr in lignes:
                    if numero_recherche in tr.text:
                        numero_trouve = True
                        break
                if numero_trouve:
                    break

                # Passer à la page suivante
                try:
                    next_btn = driver.find_element(By.ID, "tbl_inter_pending_next")
                    if "ui-state-disabled" in next_btn.get_attribute("class"):
                        break
                    next_btn.click()
                    attendre_tableau_charge(driver)
                except:
                    break

            if numero_trouve:
                print(f"🎉 Intervention trouvée sous : {statut_logique}")
                search.clear()
                return numero_recherche, statut_logique

            print(f"-> Non trouvée sous : {statut_logique}")
            search.clear()

            # ⏱ Attendre 1 seconde avant de passer au prochain filtre
            time.sleep(1)

        except Exception as e:
            print(f"⚠ Erreur statut « {statut_logique} » : {type(e).__name__}")
            continue

    print(f"❌ Aucun statut ne correspond à {numero_recherche}")
    return numero_recherche, "Statut non trouvé"



# -------------------------------------------------------------
# 💾 FONCTION D'ENREGISTREMENT DES RÉSULTATS
def enregistrer_resultat(numero, statut, filename=RESULTAT_FILENAME):
    """
    Enregistre le numéro d'abonné et son statut dans un fichier CSV.
    """
    fichier_existe = os.path.exists(filename)
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            if not fichier_existe:
                f.write("Numero_Abonne;Statut_Trouve;Date_Verification\n")
            
            date_verification = time.strftime("%Y-%m-%d %H:%M:%S")
            ligne = f"{numero};{statut};{date_verification}\n"
            f.write(ligne)
            
        print(f"\n💾 Résultat enregistré : '{numero}:{statut}' dans {filename}")
        return True
    except IOError as e:
        print(f"\n❌ Erreur lors de l'enregistrement du fichier {filename} : {e.__class__.__name__}")
        return False


# -------------------------------------------------------------
# 🚀 BLOC PRINCIPAL D'EXÉCUTION
# -------------------------------------------------------------

if __name__ == '__main__':
    
    print("--- ⚙️ Configuration du script ---")
    URL_CONNEXION ="https://serviceplus.canal-plus.com/index.php?action=INTER_PENDING" #input("Entrez l'URL du site : ")
    VOTRE_IDENTIFIANT ="Centre_RAyinda" #input("Entrez le nom utilisateur : ")
   #faire plusieurs tests avec différents numéros d'abonnés 
    VOTRE_MOT_DE_PASSE = input("Entrez le mot de passe : ")
    while True:
        NUMERO_ABONNE_RECHERCHE = input("Entrez le numéro d'abonné à vérifier : ")
    
        print("\n--- 🚀 Début du processus de vérification ---")
        print(f"Le driver est recherché ici : {MSEDGEDRIVER_PATH}")
        driver_manager = WebDriverManager()
        driver = None
        wait = None
        
        numero_resultat = NUMERO_ABONNE_RECHERCHE
        statut_resultat = "Echec de l'initialisation du driver"
        
        try:
            driver = driver_manager.start_driver(headless=False)
            statut_resultat = "Echec de connexion" 
            
            # 1. CONNEXION
            succes_connexion, driver, wait = connexion_alonwa(driver, URL_CONNEXION, VOTRE_IDENTIFIANT, VOTRE_MOT_DE_PASSE)
            
            if succes_connexion:
                
                # 2. NAVIGATION VERS LA PAGE INTERVENTION
                statut_resultat = "Echec de navigation"
                if naviguer_page_intervention(driver, wait):
                    
                    # 3. RECHERCHE OPTIMISÉE DU NUMÉRO ET DE SON STATUT
                    print(f"\nRecherche du statut de l'abonné : {NUMERO_ABONNE_RECHERCHE}")
                    
                    numero_resultat, statut_resultat = trouver_statut_intervention_specifique(driver, wait, NUMERO_ABONNE_RECHERCHE)
                    
                else:
                    statut_resultat = "Echec de navigation"
            else:
                statut_resultat = "Echec de connexion"
                
        except Exception as e:
            print(f"\n❌ Erreur critique lors de l'exécution : {e.__class__.__name__}")
            statut_resultat = f"Erreur critique: {e.__class__.__name__}"
            
        finally:
            # 4. AFFICHAGE ET ENREGISTREMENT DU RÉSULTAT
            print("\n=============================================")
            if statut_resultat.startswith("Erreur") or statut_resultat.startswith("Echec"):
                print(f"RÉSULTAT FINAL : **{numero_resultat}** : {statut_resultat}")
            elif statut_resultat == "Statut non trouvé":
                print(f"RÉSULTAT FINAL : **{numero_resultat}** : STATUT NON IDENTIFIÉ (n'est pas dans la liste des 6 statuts)")
            else:
                print(f"RÉSULTAT FINAL : **{numero_resultat}** : **{statut_resultat}**")
            print("=============================================")
            
            # 5. ENREGISTREMENT
            enregistrer_resultat(numero_resultat, statut_resultat)
            
            if driver_manager:
                try:
                    driver_manager.stop_driver() 
                    print("\n🛑 Le script a terminé. Veuillez fermer le navigateur Edge manuellement.")
                except:
                    pass