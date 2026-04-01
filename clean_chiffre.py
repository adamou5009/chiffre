import streamlit as st
import pandas as pd
from io import BytesIO

def show():
    st.set_page_config(page_title="Page clean chiffre", layout="centered")
    st.title("📊 UNIFORMISATION DES CHIFFRES PARTENAIRES")

    uploaded_file = st.file_uploader("Importer le fichier Excel", type=["xlsx"])

    if uploaded_file:
        if st.button("🚀 Lancer fusion"):
            # Lecture du fichier
            df = pd.read_excel(uploaded_file)

            # Normalisation des noms de colonnes
            df.columns = df.columns.str.strip().str.upper()

            # Liste des mois
            mois = ["JANV", "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"]

            # Fusion des lignes par NUMDIST
            df_final = df.groupby("NUMDIST").agg(
                NOMDIST=("NOMDIST", "first"),
                **{mois_col: (mois_col, "sum") for mois_col in mois}
            ).reset_index()

            # Export en mémoire
            output = BytesIO()
            df_final.to_excel(output, index=False, sheet_name="UNIFORME")
            output.seek(0)

            # Bouton téléchargement
            st.download_button(
                "📥 Télécharger le fichier uniforme",
                data=output,
                file_name="partenaires_uniformes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Affichage du tableau final
            st.subheader("👀 Aperçu des données")
            st.dataframe(df_final)
