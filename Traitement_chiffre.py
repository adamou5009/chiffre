import streamlit as st
import pandas as pd
from io import BytesIO
def show():
    st.set_page_config(page_title="Traitement des Chiffres", layout="wide")

    # ---------- FORMULAIRE ----------
    with st.form(key='my_form'):
        st.title("📊 Traitement des Chiffres d'affaires")
        uploaded_file = st.file_uploader("📂 Sélectionner un fichier Excel ou CSV", type=["xlsx", "csv"])
        submit_button = st.form_submit_button(label='🚀 Traiter le fichier')

    # ---------- TRAITEMENT HORS FORMULAIRE ----------
    if submit_button:
        if uploaded_file is None:
            st.warning("⚠️ Veuillez sélectionner un fichier avant de soumettre.")
        else:
            try:
                # Lecture du fichier
                if uploaded_file.name.endswith(".xlsx"):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file, sep=";")

                # Vérification des colonnes
                required_cols = ['NUMDIST', 'NOMDIST', 'CUSER', 'MONTANT_TTC', 'CMOUVMT', 'LARTICLE', 'CARTICLE']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
                else:
                    df = df[required_cols]

                    # ===== RÉABONNEMENT =====
                    df_reabo = df[
                        df['CMOUVMT'].isin(['MODART', 'REAAP', 'REAAV']) &
                        df['LARTICLE'].notna() &
                        (~df['LARTICLE'].str.lower().isin(['echange materiel', 'terminal global', '']))
                    ]
                    pivot_reabo = pd.pivot_table(
                        df_reabo,
                        values='MONTANT_TTC',
                        index=['NUMDIST', 'NOMDIST', 'CUSER'],
                        aggfunc='sum'
                    ).rename(columns={'MONTANT_TTC': 'Montant Réabonnement'}).reset_index()

                    # ===== RECRUTEMENT =====
                    df_recrut = df[
                        df['CMOUVMT'].isin(['CREAT']) &
                        df['LARTICLE'].isin(['ACCESS', 'ACCESS+', 'EVASION', 'EVASION+', 'TOUT CANAL', 'UNAWELCOME'])
                    ]
                    pivot_recrut = pd.pivot_table(
                        df_recrut,
                        values='CARTICLE',
                        index=['NUMDIST', 'NOMDIST', 'CUSER'],
                        aggfunc='count'
                    ).rename(columns={'CARTICLE': 'Nombre Recrutement'}).reset_index()

                    # ===== Tableau final combiné =====
                    tableau_final = pd.merge(pivot_reabo, pivot_recrut, on=['NUMDIST', 'NOMDIST', 'CUSER'], how='outer').fillna(0)

                    total_reabo = tableau_final['Montant Réabonnement'].sum()
                    total_recrut = tableau_final['Nombre Recrutement'].sum()
                    total_row = pd.DataFrame({
                        'NUMDIST': [''],
                        'NOMDIST': ['TOTAL GÉNÉRAL'],
                        'CUSER': [''],
                        'Montant Réabonnement': [total_reabo],
                        'Nombre Recrutement': [total_recrut]
                    })
                    tableau_final = pd.concat([tableau_final, total_row], ignore_index=True)

                    # ===== AFFICHAGE =====
                with st.container():
                        st.subheader("📘 Tableau consolidé : Réabonnement & Recrutement")
                        st.dataframe(tableau_final)
                        st.markdown(f"""
                            ✅ Résumé global  
                            - Montant total Réabonnement : {total_reabo:,.0f} FCFA  
                            - Total Recrutements : {int(total_recrut):,} articles
                        """)

                        # ===== EXPORT EXCEL =====
                        def convert_two_tables_to_excel(df1, df2):
                            df1_tot = df1.copy()
                            df2_tot = df2.copy()

                            # Ajouter ligne TOTAL si pas déjà présente
                            if 'TOTAL GÉNÉRAL' not in df1['NOMDIST'].values:
                                df1_tot = pd.concat([df1_tot, pd.DataFrame([{
                                    'NUMDIST': '',
                                    'NOMDIST': 'TOTAL GÉNÉRAL',
                                    'CUSER': '',
                                    'Montant Réabonnement': df1['Montant Réabonnement'].sum()
                                }])], ignore_index=True)

                            if 'TOTAL GÉNÉRAL' not in df2['NOMDIST'].values:
                                df2_tot = pd.concat([df2_tot, pd.DataFrame([{
                                    'NUMDIST': '',
                                    'NOMDIST': 'TOTAL GÉNÉRAL',
                                    'CUSER': '',
                                    'Nombre Recrutement': df2['Nombre Recrutement'].sum()
                                }])], ignore_index=True)

                            output = BytesIO()
                            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                                # Exporter les deux tableaux
                                df1_tot.to_excel(writer, index=False, sheet_name="Synthèse", startrow=1, startcol=0)
                                df2_tot.to_excel(writer, index=False, sheet_name="Synthèse", startrow=1, startcol=6)

                                workbook = writer.book
                                worksheet = writer.sheets["Synthèse"]

                                # Formats
                                header_format = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7'})
                                total_format  = workbook.add_format({'bold': True})

                                # Titres des tableaux
                                worksheet.write(0, 0, "Tableau Réabonnement", header_format)
                                worksheet.write(0, 6, "Tableau Recrutement", header_format)

                                # Largeur des colonnes
                                worksheet.set_column("A:L", 22)

                                # Mettre les lignes totaux en gras
                                worksheet.set_row(len(df1_tot), None, total_format)
                                worksheet.set_row(len(df2_tot), None, total_format)

                            return output.getvalue()

                        excel_data = convert_two_tables_to_excel(pivot_reabo, pivot_recrut)

                        # ===== BOUTON DE TÉLÉCHARGEMENT =====
                        st.download_button(
                            label="⬇️ Télécharger (Réabo + Recrutement)",
                            data=excel_data,
                            file_name="tableau_reabo_recrutement.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

            except Exception as e:
                st.error(f"Erreur lors du traitement : {e}")
