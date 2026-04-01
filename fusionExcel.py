import streamlit as st
import pandas as pd
from io import BytesIO


# 🎯 Ordre final obligatoire
COLONNES_FINALES = [
    "NOMDIST",
    "NUMDIST",
    "CAT",
    "OBJECTIF",
    "REALISATION",
    "TAUX",
    "RANKING",
    "DATE",
    "SOURCE"
]


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
        elif col.startswith("CAT"):
            mapping[col] = "CAT"
        elif "OBJ" in col:
            mapping[col] = "OBJECTIF"
        elif "REAL" in col or "CA" in col:
            mapping[col] = "REALISATION"
        elif "TR" in col or "%" in col:
            mapping[col] = "TAUX"
        elif "RANK" in col:
            mapping[col] = "RANKING"
        elif "DATE" in col:
            mapping[col] = "DATE"

    return df.rename(columns=mapping)


def forcer_ordre(df):
    # Ajouter colonnes manquantes
    for col in COLONNES_FINALES:
        if col not in df.columns:
            df[col] = None

    # Réordonner strictement
    return df[COLONNES_FINALES]


def show():

    st.title("📊 Fusion intelligente avec alignement automatique")

    uploaded_file = st.file_uploader("Importer le fichier Excel", type=["xlsx"])

    if uploaded_file:

        if st.button("🚀 Lancer le traitement"):

            try:
                feuilles = ["GOLD", "SILV", "PREM"]
                dfs = []
                xls = pd.ExcelFile(uploaded_file)

                for sheet in feuilles:

                    if sheet in xls.sheet_names:

                        df_brut = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)

                        header_row = df_brut[df_brut.apply(
                            lambda row: row.astype(str).str.contains("NOM", case=False).any(),
                            axis=1
                        )].index[0]

                        df = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_row)

                        df = df.dropna(how="all")

                        df = normaliser_colonnes(df)
                        df = mapper_colonnes(df)

                        df["SOURCE"] = sheet

                        df = forcer_ordre(df)

                        dfs.append(df)

                df_final = pd.concat(dfs, ignore_index=True)

                # Export propre
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_final.to_excel(writer, sheet_name="GLOBAL", index=False)

                output.seek(0)

                st.success("✅ Fusion et alignement terminés avec succès")

                st.download_button(
                    "📥 Télécharger le fichier final",
                    output,
                    "fusion_GLOBAL.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.dataframe(df_final)

            except Exception as e:
                st.error(f"Erreur détectée : {e}")
