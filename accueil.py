import streamlit as st


st.set_page_config(page_title="📊 Dashboard Chiffres", layout="wide")
import Programme_de_fidelite as page_fidelite
import rapport_detaille_cga as page_cga
import telechargementtopup as page_topup
import Traitement_chiffre as page_traitement
import Telechargement_VEO_PRO as page_telechargement_veo_pro
import consolidation_veo_pro as page_operations_veo_pro
import PageExtraction as page_extraction_alonwa
import interfaceAlonwa as page_verification_alonwa
import fusionExcel as page_page_fusion_excel
import clean_chiffre as page_clean_doublonsom
import super_chiffre as page_normalisation_chiffre
import adcalcul_partenaire as page_generation_personnelle
import fusionMultiFichier as page_fusion_multi_fichier
st.sidebar.title("Navigation")

page_selectionnee = st.sidebar.radio(
    "Choisir une page :",
    [
        "Programme de fidélité",
        "Rapport détaillé CGA",
        "Téléchargement Topup",
        "Traitement chiffre",
        "Téléchargement VEO PRO",
        "Opérations VEO PRO",
        "Extraction alonwa",
        "verication recherche alonwa",
        "Fusion Excel",
        "Somme Unique",
        "Super Chiffre",
        "Chiffre individuel",
        "Fusion Multi Fichier"
    ]
)

if page_selectionnee == "Programme de fidélité":
    page_fidelite.show()
elif page_selectionnee == "Rapport détaillé CGA":
    page_cga.show()
elif page_selectionnee == "Téléchargement Topup":
    page_topup.show()
elif page_selectionnee == "Traitement chiffre":
    page_traitement.show()
elif page_selectionnee == "Téléchargement VEO PRO":
    page_telechargement_veo_pro.show()
elif page_selectionnee == "Opérations VEO PRO":
    page_operations_veo_pro.show()
elif page_selectionnee == "Extraction alonwa":
    page_extraction_alonwa.show()
elif page_selectionnee == "verication recherche alonwa":
    page_verification_alonwa.show()
elif page_selectionnee== "Fusion Excel" :
    page_page_fusion_excel.show()
elif page_selectionnee == "Somme Unique":
    page_clean_doublonsom.show()
elif page_selectionnee == "Super Chiffre":
    page_normalisation_chiffre.show()
elif page_selectionnee== "Chiffre individuel":
    page_generation_personnelle.show()
elif page_selectionnee == "Fusion Multi Fichier":
    page_fusion_multi_fichier.show()

