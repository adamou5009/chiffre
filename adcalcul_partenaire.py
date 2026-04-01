import streamlit as st
import pandas as pd
from io import BytesIO

def show():
    st.set_page_config(page_title="Consolidation Opérations", layout="wide")
    st.title("📊 Consolidation des opérations vers le fichier mère")

    # --- Upload des fichiers ---
    st.subheader("1️⃣ Charger les fichiers opérations")
    uploaded_ops_files = st.file_uploader(
        "Sélectionnez les fichiers opérations (Excel ou CSV)", 
        type=["xlsx", "xls", "csv"], 
        accept_multiple_files=True
    )

    st.subheader("2️⃣ Charger le fichier mère")
    uploaded_mere_file = st.file_uploader(
        "Sélectionnez le fichier mère (Excel)", 
        type=["xlsx", "xls"]
    )

    if uploaded_ops_files and uploaded_mere_file:
        # --- Lecture du fichier mère ---
        try:
            df_mere = pd.read_excel(uploaded_mere_file)
            df_mere.columns = df_mere.columns.str.strip().str.upper()
        except Exception as e:
            st.error(f"Erreur lecture fichier mère : {e}")
            st.stop()

        # --- Lecture et concaténation des fichiers opérations ---
        df_ops_list = []
        for file in uploaded_ops_files:
            try:
                if file.name.endswith((".xls", ".xlsx")):
                    df_ops = pd.read_excel(file)
                else:
                    df_ops = pd.read_csv(file)
                df_ops.columns = df_ops.columns.str.strip().str.upper()
                df_ops_list.append(df_ops)
            except Exception as e:
                st.warning(f"Impossible de lire {file.name}: {e}")
        
        if not df_ops_list:
            st.error("Aucun fichier opération valide")
            st.stop()

        df_ops_all = pd.concat(df_ops_list, ignore_index=True)

        # --- Nettoyage et transformation ---
        if "TOTAL GÉNÉRAL" not in df_ops_all.columns:
            st.error("La colonne 'TOTAL GÉNÉRAL' est manquante dans les fichiers opérations")
            st.stop()

        df_ops_all["TOTAL GÉNÉRAL"] = (
            df_ops_all["TOTAL GÉNÉRAL"].astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
        )
        df_ops_all["TOTAL GÉNÉRAL"] = pd.to_numeric(
            df_ops_all["TOTAL GÉNÉRAL"], errors="coerce"
        ).fillna(0)

        # --- Création identifiant final (réseauteur ou CODE) ---
        df_ops_all["IDENTIFIANT_FINAL"] = df_ops_all["CODE_RS"].fillna(df_ops_all["CODE"])
        df_ops_all["NOM_FINAL"] = df_ops_all["RESEAUTEUR"].fillna(df_ops_all["MARCHAND"])

        # --- Consolidation par identifiant ---
        df_resume = (
            df_ops_all.groupby(["IDENTIFIANT_FINAL", "NOM_FINAL"])["TOTAL GÉNÉRAL"]
            .sum()
            .reset_index()
        )

        # --- Fusion avec le fichier mère ---
        df_final = df_mere.merge(
            df_resume,
            left_on="NUMDIST",   # NUMDIST = CODE dans fichier mère
            right_on="IDENTIFIANT_FINAL",
            how="left"
        )

        # --- Calcul du total final ---
        df_final["TOTAL_CALCULE"] = df_final["TOTAL GÉNÉRAL"].fillna(0)
        df_final["TOTAL"] = df_final["TOTAL_CALCULE"]

        # --- Nettoyage colonnes temporaires (safe drop) ---
        df_final = df_final.drop(columns=["IDENTIFIANT_FINAL", "TOTAL_GÉNÉRAL", "NOM_FINAL"], errors="ignore")

        # --- Affichage ---
        st.subheader("3️⃣ Aperçu du fichier final")
        st.dataframe(df_final.head(50))

        # --- Téléchargement ---
        def to_excel_bytes(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Consolidation")
            return output.getvalue()

        st.download_button(
            label="📥 Télécharger le fichier final",
            data=to_excel_bytes(df_final),
            file_name="fichier_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("⚠️ Veuillez charger au moins un fichier opérations et le fichier mère.")
