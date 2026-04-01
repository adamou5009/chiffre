import streamlit as st
import pandas as pd
import io

# --- Configuration des colonnes clés (CORRIGÉE) ---
# Clé dans le Fichier Utilisateur (Utilise le nom exact 'Code')
COLONNE_CLE_UTILISATEUR = 'Code' 

# Clé dans le Fichier Opérations (pour la jointure - Assurez-vous que le fichier Ops utilise AUSSI 'Code')
COLONNE_CLE_OPERATIONS = 'Code marchand' 

# Colonne du réseauteur (parent) dans le Fichier Utilisateur (Utilise le nom exact 'Entreprise du parent')
COLONNE_RESEAUTEUR = 'Entreprise du parent' 

# Colonne du montant dans le Fichier Opérations (à ajuster si ce n'est pas 'Montant')
COLONNE_MONTANT = 'Montant'

def process_files(df_user, df_ops):
    """Effectue la jointure et l'agrégation pour créer le classement hiérarchique."""
    
    # 1. Préparation de la table de hiérarchie (Fichier Utilisateur)
    # ⚠️ LA KEYERROR SE PRODUIT ICI SI LES NOMS CI-DESSUS SONT FAUX DANS DF_USER
    if COLONNE_CLE_UTILISATEUR not in df_user.columns or COLONNE_RESEAUTEUR not in df_user.columns:
        missing_cols = [c for c in [COLONNE_CLE_UTILISATEUR, COLONNE_RESEAUTEUR] if c not in df_user.columns]
        st.error(f"Erreur: Le Fichier Utilisateur n'a pas les colonnes clés. Il manque : {', '.join(missing_cols)}")
        return None

    df_hierarchy = df_user[[COLONNE_CLE_UTILISATEUR, COLONNE_RESEAUTEUR]].copy()
    df_hierarchy = df_hierarchy.drop_duplicates(subset=[COLONNE_CLE_UTILISATEUR])
    df_hierarchy = df_hierarchy.rename(columns={
        COLONNE_CLE_UTILISATEUR: COLONNE_CLE_OPERATIONS
    })

    # 2. Jointure (Matching)
    if COLONNE_CLE_OPERATIONS not in df_ops.columns:
        st.error(f"Erreur: La colonne de jointure '{COLONNE_CLE_OPERATIONS}' est introuvable dans le Fichier des Opérations. Vérifiez les noms.")
        return None
        
    df_ops_enriched = pd.merge(
        df_ops, 
        df_hierarchy, 
        on=COLONNE_CLE_OPERATIONS, 
        how='left'
    )
    
    # 3. Préparation du Montant pour l'agrégation
    if COLONNE_MONTANT not in df_ops_enriched.columns:
        st.error(f"Erreur : La colonne '{COLONNE_MONTANT}' est introuvable dans le Fichier des Opérations. Vérifiez les noms de colonnes.")
        return None
        
    df_ops_enriched[COLONNE_MONTANT] = pd.to_numeric(df_ops_enriched[COLONNE_MONTANT], errors='coerce')
    
    # 4. Agrégation
    df_classement = df_ops_enriched.groupby([
        COLONNE_RESEAUTEUR, 
        COLONNE_CLE_OPERATIONS 
    ])[COLONNE_MONTANT].sum().reset_index()
    
    # 5. Renommer les colonnes pour la sortie finale
    df_classement = df_classement.rename(columns={
        COLONNE_RESEAUTEUR: 'CODE_RS RESEAUTEUR',
        COLONNE_CLE_OPERATIONS: 'CODE MARCHAND',
        COLONNE_MONTANT: 'Total général'
    })
    
    # Supprimer les lignes sans Réseauteur trouvé
    df_classement.dropna(subset=['CODE_RS RESEAUTEUR'], inplace=True)
    
    return df_classement

# Préparation de la fonction de téléchargement (mise en cache Streamlit)
@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Classement Hiérarchique')
    processed_data = output.getvalue()
    return processed_data

# --- Interface Streamlit ---
def show():
    st.set_page_config(
        page_title="Classement Hiérarchique",
        layout="wide"
    )
    st.title("🔗 Générateur de Classement Hiérarchique")
    st.markdown("Chargez les deux fichiers, puis cliquez sur **'Lancer le Traitement'** pour générer le classement agrégé.")

    # Création des deux colonnes pour les uploads
    col_user, col_ops = st.columns(2)

    # 1. Fichier Utilisateur (dans la première colonne)
    with col_user:
        st.header("1️⃣ Fichier Utilisateur ")
        #st.info(f"Doit contenir les colonnes pour la hiérarchie. VÉRIFIEZ : `{COLONNE_CLE_UTILISATEUR}` et `{COLONNE_RESEAUTEUR}`.")
        uploaded_file_user = st.file_uploader("Chargez le fichier Excel de la hiérarchie", type=['xlsx'], key="user_file")

    # 2. Fichier des Opérations (dans la deuxième colonne)
    with col_ops:
        st.header("2️⃣ Fichier des Opérations ")
        #st.info(f"Doit contenir les colonnes pour la transaction. VÉRIFIEZ : `{COLONNE_CLE_OPERATIONS}` et `{COLONNE_MONTANT}`.")
        uploaded_file_ops = st.file_uploader("Chargez le fichier Excel des opérations", type=['xlsx'], key="ops_file")

    st.divider()

    # 3. Bouton de déclenchement du traitement
    if st.button("▶️ Lancer le Traitement", type="primary", use_container_width=True):
        
        if not uploaded_file_user or not uploaded_file_ops:
            st.error("Veuillez charger les deux fichiers Excel avant de lancer le traitement.")
        else:
            with st.spinner('Traitement des données en cours...'):
                try:
                    # Lecture des fichiers
                    df_user = pd.read_excel(uploaded_file_user)
                    df_ops = pd.read_excel(uploaded_file_ops)
                    
                    # Traitement
                    df_resultat = process_files(df_user, df_ops)
                    
                    # Affichage des résultats
                    if df_resultat is not None and not df_resultat.empty:
                        st.header("3️⃣ Résultat du Classement Agrégé")
                        st.dataframe(df_resultat, use_container_width=True)
                        st.success(f"Traitement terminé avec succès ! {len(df_resultat)} lignes de classement générées.")

                        # Bouton de téléchargement
                        excel_data = convert_df_to_excel(df_resultat)
                        st.download_button(
                            label="📥 Télécharger (Excel)",
                            data=excel_data,
                            file_name='Classement_Hierarchique_Agrege.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                    elif df_resultat is not None:
                        st.warning("Traitement terminé, mais la table de classement est vide. Vérifiez si les codes marchands existent dans les deux fichiers.")

                except Exception as e:
                    st.error(f"Une erreur est survenue lors du traitement : {e}")
                    st.exception(e)

# Si vous voulez exécuter l'application
# show()