import streamlit as st
import pandas as pd
from io import BytesIO

def show():
    st.set_page_config(page_title="📊 Consolidation PDV", layout="wide")
    st.title("Traitement du Programme de Fidélité")

    st.write(
        "Téléversez les fichiers requis pour démarrer le traitement."
        "\n- Fichier 1 (Opération Topup)"
        "\n- Fichier 2 (Opération CGA)"
        "\n- Fichier 3 (Liste Points de vente)"
        "\n- Fichier 4 (VEO PRO, optionnel)"
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1: up_file1 = st.file_uploader("1. Fichier Opération Topup", type=["xlsx","csv"], key="f1")
    with col2: up_file2 = st.file_uploader("2. Fichier Opération CGA", type=["xlsx","csv"], key="f2")
    with col3: up_file3 = st.file_uploader("3. Liste PDV (multi-feuilles)", type=["xlsx"], key="f3")
    with col4: up_file4 = st.file_uploader("4. Fichier VEO PRO (optionnel)", type=["xlsx","csv"], key="f4")

    def find_col(df, candidates):
        cols = {str(c).strip().upper(): c for c in df.columns if pd.notna(c)}
        for cand in candidates:
            key = cand.strip().upper()
            if key in cols: return cols[key]
        for k, orig in cols.items():
            for cand in candidates:
                tokens = cand.strip().upper().split()
                if all(t in k for t in tokens): return orig
        return None

    def read_file(f, force_str=False):
        if not f: return None
        f.seek(0)
        dtype = str if force_str else None
        if f.name.lower().endswith(".xlsx"):
            return pd.read_excel(f, dtype=dtype)
        for sep, enc in [(";", "latin-1"), (",","utf-8"), ("\t","utf-8")]:
            f.seek(0)
            try:
                df = pd.read_csv(f, sep=sep, encoding=enc, dtype=dtype)
                if len(df.columns) > 1: return df
            except: pass
        f.seek(0)
        return pd.read_csv(f, dtype=dtype)

    if st.button("Démarrer le traitement") or (up_file1 and up_file2 and up_file3):
        if not (up_file1 and up_file2 and up_file3):
            st.info("Importez les fichiers 1, 2 et 3 pour commencer.")
            st.stop()
        try:
            # Lecture
            df1 = read_file(up_file1, force_str=True)
            df2 = read_file(up_file2, force_str=True)
            feuilles = pd.read_excel(up_file3, sheet_name=None, dtype=str)
            df_veo = read_file(up_file4, force_str=True)

            df1.columns = df1.columns.str.strip()
            df2.columns = df2.columns.str.strip()
            if df_veo is not None: df_veo.columns = df_veo.columns.str.strip()

            # Colonnes F1
            col_total = find_col(df1, ["Total général","TOTAL GENERAL","Total","Montant","TOTAL"])
            col_code = find_col(df1, ["CODE","CODE PDV","ID PDV"])
            col_marchand = find_col(df1, ["MARCHAND"])
            col_code_rs = find_col(df1, ["CODE_RS","CODE RS","ID_RESEAU","MARCHAND RS"])
            col_reseau = find_col(df1, ["RESEAUTEUR","RESEAU"])

            # Colonnes F2
            col_numdist_f2 = find_col(df2, ["NUM_DIST","NUMDIST","DISTRIBUTEUR"])
            col_montant_f2 = find_col(df2, ["MONTANT_TTC","MONTANT","Total général","TOTAL GENERAL"])

            # Colonnes F4 (optionnel)
            col_code_veo = find_col(df_veo, ["CODE_VEO_PRO","CODE","NUM_DIST","CODE_PDV","NUMDIST"]) if df_veo is not None else None
            col_chiffre_veo = find_col(df_veo, ["CHIFFRE_VEO_PRO","CHIFFRE","MONTANT","TOTAL"]) if df_veo is not None else None

            # Standardisation F1
            rename_map = {col_total:"Total_general"}
            if col_code: rename_map[col_code]="CODE"
            if col_marchand: rename_map[col_marchand]="MARCHAND"
            if col_code_rs: rename_map[col_code_rs]="CODE_RS"
            if col_reseau: rename_map[col_reseau]="RESEAUTEUR"
            df1 = df1.rename(columns=rename_map)
            for c in ["CODE","MARCHAND","CODE_RS","RESEAUTEUR"]:
                if c in df1.columns: df1[c] = df1[c].astype(str).str.strip().str.upper()
            df1["Total_general"] = pd.to_numeric(df1["Total_general"], errors="coerce").fillna(0)

            # Standardisation F2
            df2 = df2.rename(columns={col_numdist_f2:"NUM_DIST", col_montant_f2:"MONTANT_TTC"})
            df2["NUM_DIST"] = df2["NUM_DIST"].astype(str).str.strip().str.upper()
            df2["MONTANT_TTC"] = pd.to_numeric(df2["MONTANT_TTC"], errors="coerce").fillna(0)

            # F4
            if df_veo is not None and col_code_veo and col_chiffre_veo:
                df_veo = df_veo.rename(columns={col_code_veo:"NUM_DIST", col_chiffre_veo:"CHIFFRE_VEO_PRO"})
                df_veo["NUM_DIST"] = df_veo["NUM_DIST"].astype(str).str.strip().str.upper()
                df_veo["CHIFFRE_VEO_PRO"] = pd.to_numeric(df_veo["CHIFFRE_VEO_PRO"], errors="coerce").fillna(0)
                df_veo_sum = df_veo.groupby("NUM_DIST", as_index=False)["CHIFFRE_VEO_PRO"].sum()
            else: df_veo_sum = pd.DataFrame(columns=["NUM_DIST","CHIFFRE_VEO_PRO"])

            # --- Agrégation F1 total par partenaire
            id_col = col_code if col_code in df1.columns else col_marchand
            if id_col:
                df_f1_tot = df1.groupby(id_col, dropna=False)["Total_general"].sum().reset_index()
                df_f1_tot.rename(columns={id_col:"NUM_DIST","Total_general":"TOTAL_F1"}, inplace=True)
            else: df_f1_tot = pd.DataFrame(columns=["NUM_DIST","TOTAL_F1"])

            # --- Sous-réseau
            if "CODE_RS" in df1.columns and "CODE" in df1.columns:
                sous_pts = df1[df1["CODE"] != df1["CODE_RS"]]
                if not sous_pts.empty:
                    df_reseau = sous_pts.groupby("CODE_RS", dropna=False)["Total_general"].sum().reset_index()
                    df_reseau.rename(columns={"CODE_RS":"NUM_DIST","Total_general":"CHIFFRE_OP_TOPUP_RESEAU"}, inplace=True)
                    nb_sous = sous_pts.groupby("CODE_RS")["CODE"].nunique().reset_index()
                    nb_sous.rename(columns={"CODE_RS":"NUM_DIST","CODE":"TOTAL_RESEAU_PDV"}, inplace=True)
                    df_reseau = df_reseau.merge(nb_sous, on="NUM_DIST", how="outer")
                else: df_reseau = pd.DataFrame(columns=["NUM_DIST","CHIFFRE_OP_TOPUP_RESEAU","TOTAL_RESEAU_PDV"])
            else: df_reseau = pd.DataFrame(columns=["NUM_DIST","CHIFFRE_OP_TOPUP_RESEAU","TOTAL_RESEAU_PDV"])

            # --- Agrégation F2
            df_f2 = df2.groupby("NUM_DIST", dropna=False)["MONTANT_TTC"].sum().reset_index()
            df_f2.rename(columns={"MONTANT_TTC":"TOTAL_F2"}, inplace=True)

            # --- Fusion Totaux
            df_totaux = df_f1_tot.merge(df_f2, on="NUM_DIST", how="outer").merge(df_veo_sum, on="NUM_DIST", how="outer").merge(df_reseau, on="NUM_DIST", how="outer").fillna(0)
            df_totaux["TOTAL_FINAL"] = df_totaux["TOTAL_F1"] + df_totaux["TOTAL_F2"] + df_totaux.get("CHIFFRE_VEO_PRO",0) + df_totaux.get("CHIFFRE_OP_TOPUP_RESEAU",0)

            # --- Consolidation par feuille PDV
            resultats = {}
            synthese_rows = []
            for nom_feuille, df_pdv in feuilles.items():
                df_pdv = df_pdv.copy()
                df_pdv.columns = df_pdv.columns.str.strip()
                col_id = find_col(df_pdv, ["NUM_DIST","NUMDIST","CODE_PDV"])
                if col_id is None:
                    st.warning(f"Feuille '{nom_feuille}' ignorée (pas de colonne NUM_DIST)")
                    continue
                df_pdv = df_pdv.rename(columns={col_id:"NUM_DIST"})
                df_pdv["NUM_DIST"] = df_pdv["NUM_DIST"].astype(str).str.strip().str.upper()
                df_merge = df_pdv.merge(df_totaux, on="NUM_DIST", how="left").fillna(0)

                # Statut
                cond_mixte = (df_merge["TOTAL_F1"]>0) & (df_merge["CHIFFRE_OP_TOPUP_RESEAU"]>0)
                cond_direct = (df_merge["TOTAL_F1"]>0) & (df_merge["CHIFFRE_OP_TOPUP_RESEAU"]==0)
                cond_reseau = (df_merge["TOTAL_F1"]==0) & (df_merge["CHIFFRE_OP_TOPUP_RESEAU"]>0)
                cond_aucun = (df_merge["TOTAL_F1"]==0) & (df_merge["CHIFFRE_OP_TOPUP_RESEAU"]==0)
                df_merge["STATUT"] = ""
                df_merge.loc[cond_mixte,"STATUT"]="Mixte"
                df_merge.loc[cond_direct,"STATUT"]="Direct"
                df_merge.loc[cond_reseau,"STATUT"]="Réseauteur"
                df_merge.loc[cond_aucun,"STATUT"]="Aucun chiffre"

                # Total ligne
                total_row = df_merge.select_dtypes(include="number").sum(numeric_only=True)
                total_row["NUM_DIST"]="TOTAL"
                df_merge = pd.concat([df_merge, pd.DataFrame([total_row], columns=df_merge.columns)], ignore_index=True)

                resultats[nom_feuille]=df_merge

                # Synthèse
                synthese_rows.append({
                    "FEUILLE": nom_feuille,
                    "NB_PDV_Total": len(df_merge)-1,
                    "SUM_TOTAL_FINAL": df_merge["TOTAL_FINAL"].iloc[:-1].sum(),
                    "NB_MIXTE": (df_merge["STATUT"].iloc[:-1]=="Mixte").sum(),
                    "NB_DIRECT": (df_merge["STATUT"].iloc[:-1]=="Direct").sum(),
                    "NB_RESEAU": (df_merge["STATUT"].iloc[:-1]=="Réseauteur").sum(),
                    "NB_AUCUN": (df_merge["STATUT"].iloc[:-1]=="Aucun chiffre").sum()
                })

            # Export Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for nom, df_out in resultats.items():
                    df_out.to_excel(writer, sheet_name=nom[:31], index=False)
                pd.DataFrame(synthese_rows).to_excel(writer, sheet_name="SYNTHÈSE", index=False)
            output.seek(0)

            st.success("✅ Traitement terminé !")
            st.download_button("📥 Télécharger le fichier consolidé", data=output,
                               file_name="consolidation_pdv.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            st.error(f"Erreur durant le traitement : {e}")
