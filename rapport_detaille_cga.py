import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

def show(): 
    st.set_page_config(page_title="📊 Consolidation CGA + TOPUP - Double Synthèse", layout="wide")
    st.title("Consolidation Chiffre - Double Synthèse")
    st.markdown("---")

    # --- Helpers (inchangé) ---
    def read_file(uploaded):
        if uploaded is None: return None
        try:
            name = uploaded.name.lower()
            if name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded)
            else:
                try:
                    df = pd.read_csv(uploaded, sep=";", encoding='latin1')
                except:
                    df = pd.read_csv(uploaded, sep=",", encoding='latin1')
            df.columns = df.columns.str.strip().str.upper()
            return df
        except Exception as e:
            st.error(f"❌ Erreur lecture fichier {uploaded.name} : {e}")
            return None

    def find_pdv_code_col(df):
        for col in ["NUM_DIST", "CODE_RS", "CODE MARCHAND", "CODE"]:
            if col in df.columns:
                return col
        return None

    def find_montant_col(df):
        candidates = ["MONTANT_TTC", "TOTAL", "TOTAL_TTC", "TOTAL_GENERAL", "TOTAL GÉNÉRAL"]
        for c in candidates:
            if c in df.columns:
                return c
        return None

    def ensure_code_rs_and_hierarchy(df, file_type="liste"):
        code_col = find_pdv_code_col(df)
        if code_col:
            df["CODE_RS"] = df[code_col].astype(str).str.strip().replace("", pd.NA)
        else:
            st.warning(f"⚠️ Aucun identifiant de PDV trouvé dans un fichier {file_type}. Opération impossible.")
            return None
        if file_type == "liste":
            for c in ["DIVISION", "SECTEUR", "ZONE"]:
                if c not in df.columns or df[c].isnull().all():
                    df[c] = "INCONNU"
                df[c] = df[c].astype(str).str.strip().str.upper().replace("", "INCONNU")
            return df.drop_duplicates(subset=["CODE_RS"], keep="first")
        return df

    def filter_parecelle_transactions(df, name):
        if 'CODE_RS' in df.columns:
            initial_rows = len(df)
            df_filtered = df[~df['DIVISION'].astype(str).str.contains("PARECELLE", case=False, na=False)]
            excluded_count = initial_rows - len(df_filtered)
            if excluded_count > 0:
                st.info(f"ℹ️ Exclusion 'Parecelle' pour {name}: {excluded_count} lignes exclues.")
            return df_filtered
        return df

    # --- Upload des fichiers ---
    with st.form("form_import"):
        st.subheader("1. Importer les 4 fichiers requis")
        col1, col2, col3, col4 = st.columns(4)
        with col1: file_list_cga = st.file_uploader("1) Liste PDV CGA (Hiérarchie)", type=["xlsx", "csv"])
        with col2: file_trafic_cga = st.file_uploader("2) Trafics CGA (Chiffres)", type=["xlsx", "csv"])
        with col3: file_list_topup = st.file_uploader("3) Liste PDV TOPUP (Hiérarchie)", type=["xlsx", "csv"])
        with col4: file_trafic_topup = st.file_uploader("4) Trafics TOPUP (Chiffres)", type=["xlsx", "csv"])
        st.markdown("---")
        submit = st.form_submit_button("🚀 Consolider et générer le rapport")

    if not submit: st.stop()

    # --- Lecture et préparation des fichiers ---
    df_list_cga = ensure_code_rs_and_hierarchy(read_file(file_list_cga), "liste CGA")
    df_list_topup = ensure_code_rs_and_hierarchy(read_file(file_list_topup), "liste TOPUP")
    df_trafic_cga = ensure_code_rs_and_hierarchy(read_file(file_trafic_cga), "trafic CGA")
    df_trafic_topup = ensure_code_rs_and_hierarchy(read_file(file_trafic_topup), "trafic TOPUP")

    if any(df is None for df in [df_list_cga, df_list_topup, df_trafic_cga, df_trafic_topup]):
        st.error("❌ Tous les fichiers sont requis et doivent être lus correctement."); st.stop()

    amt_cga_col = find_montant_col(df_trafic_cga)
    amt_topup_col = find_montant_col(df_trafic_topup)
    if amt_cga_col is None or amt_topup_col is None:
        st.error("❌ Impossible de trouver les colonnes de montant."); st.stop()

    df_trafic_cga[amt_cga_col] = pd.to_numeric(df_trafic_cga[amt_cga_col], errors='coerce').fillna(0)
    df_trafic_topup[amt_topup_col] = pd.to_numeric(df_trafic_topup[amt_topup_col], errors='coerce').fillna(0)

    # --- Fusion unique de tous les trafics ---
    df_trafic_cga = df_trafic_cga.rename(columns={amt_cga_col: "MONTANT"})
    df_trafic_topup = df_trafic_topup.rename(columns={amt_topup_col: "MONTANT"})
    df_trafic_all = pd.concat([df_trafic_cga, df_trafic_topup], ignore_index=True)

    df_trafic_all = df_trafic_all.merge(
        pd.concat([df_list_cga[["CODE_RS","DIVISION","SECTEUR","ZONE"]],
                   df_list_topup[["CODE_RS","DIVISION","SECTEUR","ZONE"]]], 
                  ignore_index=True).drop_duplicates(subset="CODE_RS"),
        on="CODE_RS", how="left"
    )

    df_trafic_all["DIVISION"] = df_trafic_all["DIVISION"].fillna("INCONNU")
    df_trafic_all["SECTEUR"] = df_trafic_all["SECTEUR"].fillna("INCONNU")
    df_trafic_all["ZONE"] = df_trafic_all["ZONE"].fillna("INCONNU")

    df_trafic_all = filter_parecelle_transactions(df_trafic_all, "Global")

    # --- Consolidation par PDV ---
    df_agg_pdv = df_trafic_all.groupby(["CODE_RS","DIVISION","SECTEUR","ZONE"], as_index=False)["MONTANT"].sum()

    # --- Génération synthèses ---
    def generate_hierarchical_report(df):
        synthese = df.groupby(["DIVISION","SECTEUR","ZONE"], as_index=False)["MONTANT"].sum()
        lines=[]
        for (div, sec), group in synthese.groupby(["DIVISION","SECTEUR"]):
            lines.append(group)
            total_sec=pd.DataFrame({
                "DIVISION":[div],
                "SECTEUR":[f"TOTAL {sec}"],
                "ZONE":[""],
                "MONTANT":[group["MONTANT"].sum()]
            })
            lines.append(total_sec)
        synthese_avec_secteur_total=pd.concat(lines, ignore_index=True)
        div_totals=[]
        for div, group in synthese_avec_secteur_total.groupby("DIVISION"):
            if not div.startswith("TOTAL "):
                div_totals.append(pd.DataFrame({
                    "DIVISION":[f"TOTAL {div}"],
                    "SECTEUR":[""],
                    "ZONE":[""],
                    "MONTANT":[group["MONTANT"].sum()]
                }))
        synthese_finale=pd.concat([synthese_avec_secteur_total]+div_totals, ignore_index=True)
        total_general_amount=synthese_finale[~synthese_finale['DIVISION'].str.startswith('TOTAL')]["MONTANT"].sum()
        total_general=pd.DataFrame({
            "DIVISION":["TOTAL GENERAL"],
            "SECTEUR":[""],
            "ZONE":[""],
            "MONTANT":[total_general_amount]
        })
        return pd.concat([synthese_finale,total_general], ignore_index=True)

    synthese_hierarchique = generate_hierarchical_report(df_agg_pdv)

    def generate_unique_zone_report(df):
        synthese = df.groupby("ZONE", as_index=False)["MONTANT"].sum()
        synthese.insert(0,'DIVISION','SYNTHESE')
        synthese.insert(1,'SECTEUR','ZONE UNIQUE')
        total_general=pd.DataFrame({
            "DIVISION":["TOTAL GENERAL"],
            "SECTEUR":[""],
            "ZONE":[""],
            "MONTANT":[synthese["MONTANT"].sum()]
        })
        return pd.concat([synthese,total_general], ignore_index=True)

    synthese_zones_uniques = generate_unique_zone_report(df_agg_pdv)

    # --- Affichage Streamlit ---
    st.subheader("📈 Synthèse Hiérarchique (Division/Secteur/Zone)")
    def color_total_rows(row):
        style = ['']*len(row)
        if ("TOTAL" in str(row['DIVISION'])) or ("TOTAL" in str(row['SECTEUR'])): 
            style=['background-color: #e6ffe6; font-weight: bold']*len(row)
        return style
    styled_synthese = synthese_hierarchique.style.apply(color_total_rows, axis=1) \
                                                .format({"MONTANT":"{:,.0f}"})
    st.dataframe(styled_synthese, width='stretch')
    st.markdown("---")
    st.info("Le fichier Excel final contient deux onglets de synthèse : 'SYNTHESE_HIERARCHIQUE' et 'SYNTHESE_ZONES_UNIQUES'.")

    # --- Export Excel ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_agg_pdv.to_excel(writer, index=False, sheet_name="CONSOLIDATION_PDV")
        synthese_hierarchique.to_excel(writer, index=False, sheet_name="SYNTHESE_HIERARCHIQUE")
        synthese_zones_uniques.to_excel(writer, index=False, sheet_name="SYNTHESE_ZONES_UNIQUES")
        workbook = writer.book
        green_format = workbook.add_format({'bg_color':'#E6FFE6','bold':True,'num_format':'#,##0'})
        default_format = workbook.add_format({'num_format':'#,##0'})
        # Hiérarchique
        ws_h = writer.sheets["SYNTHESE_HIERARCHIQUE"]
        ws_h.set_column('D:D', 15, default_format)
        for i,row in synthese_hierarchique.iterrows():
            if ("TOTAL" in str(row['DIVISION'])) or ("TOTAL" in str(row['SECTEUR'])):
                ws_h.set_row(i+1,None,green_format)
        # Zones uniques
        ws_u = writer.sheets["SYNTHESE_ZONES_UNIQUES"]
        ws_u.set_column('D:D', 15, default_format)
        ws_u.set_row(len(synthese_zones_uniques), None, green_format)

    output.seek(0)
    st.download_button(
        label="⬇️ Télécharger le fichier consolidé (Excel avec 2 Synthèses)",
        data=output,
        file_name="Consolidation_Double_Synthese_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("✅ Traitement terminé. Le rapport final contient maintenant deux feuilles de synthèse dans le fichier Excel.")
