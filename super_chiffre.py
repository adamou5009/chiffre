import streamlit as st
import pandas as pd
from io import BytesIO

# 🎯 Ordre final obligatoire
MOIS_ORDRE = [
    "JANV", "FÉVR", "MARS", "AVR", "MAI", "JUIN",
    "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"
]

COLONNES_FINALES = ["NOMDIST", "NUMDIST"] + MOIS_ORDRE


def normaliser_colonnes(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(" ", "", regex=False)
    )
    return df


def mapper_colonnes(df):

    mapping = {}

    for col in df.columns:

        if "NOM" in col:
            mapping[col] = "NOMDIST"

        elif "NUM" in col:
            mapping[col] = "NUMDIST"

        elif "JAN" in col:
            mapping[col] = "JANV"

        elif "FEV" in col or "FÉV" in col:
            mapping[col] = "FÉVR"

        elif "MAR" in col:
            mapping[col] = "MARS"

        elif "AVR" in col:
            mapping[col] = "AVR"

        elif "MAI" in col:
            mapping[col] = "MAI"

        elif "JUN" in col:
            mapping[col] = "JUIN"

        elif "JUL" in col:
            mapping[col] = "JUIL"

        elif "AOU" in col or "AOÛ" in col:
            mapping[col] = "AOÛT"

        elif "SEP" in col:
            mapping[col] = "SEPT"

        elif "OCT" in col:
            mapping[col] = "OCT"

        elif "NOV" in col:
            mapping[col] = "NOV"

        elif "DEC" in col or "DÉC" in col:
            mapping[col] = "DÉC"

    df = df.rename(columns=mapping)
    return df


def forcer_structure(df):

    # Ajouter colonnes manquantes
    for col in COLONNES_FINALES:
        if col not in df.columns:
            df[col] = 0

    # Convertir mois en numérique
    for mois in MOIS_ORDRE:
        df[mois] = pd.to_numeric(df[mois], errors="coerce").fillna(0)

    return df[COLONNES_FINALES]


def show():

    st.title("📊 Uniformisation complète des partenaires")

    fichiers = st.file_uploader(
        "Importer un ou plusieurs fichiers",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if fichiers:

        if st.button("🚀 Lancer l'uniformisation"):

            try:
                dfs = []

                for fichier in fichiers:
                    df = pd.read_excel(fichier)
                    df = normaliser_colonnes(df)
                    df = mapper_colonnes(df)
                    df = forcer_structure(df)
                    dfs.append(df)

                df_total = pd.concat(dfs, ignore_index=True)

                # 🔥 UNE SEULE LIGNE PAR NUMDIST
                df_final = df_total.groupby("NUMDIST").agg(
                    NOMDIST=("NOMDIST", "first"),
                    **{mois: (mois, "sum") for mois in MOIS_ORDRE}
                ).reset_index()

                # Réordonner final
                df_final = df_final[COLONNES_FINALES]

                # Export
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_final.to_excel(writer, index=False, sheet_name="UNIFORME")

                output.seek(0)

                st.success("✅ Uniformisation terminée")

                st.download_button(
                    "📥 Télécharger le fichier uniforme",
                    output,
                    "partenaires_uniformes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.dataframe(df_final)

            except Exception as e:
                st.error(f"Erreur détectée : {e}")
