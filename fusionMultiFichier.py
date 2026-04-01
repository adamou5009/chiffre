import streamlit as st
import pandas as pd
import io
import re

# ----------------------------
# Fonctions utilitaires
# ----------------------------
def extraire_date_depuis_nom(feuille_nom):
    """
    Extrait la date complète depuis le nom de la feuille.
    Supporte formats collés (310126) ou avec espaces (31 01 26)
    """
    feuille_nom = feuille_nom.lower()
    match = re.search(r'au\s*(\d{6,8}|\d{1,2}\s*\d{1,2}\s*\d{2,4})', feuille_nom)
    if match:
        date_str = match.group(1).replace(" ", "")
        if len(date_str) == 6:  # 310126
            jour = int(date_str[0:2])
            mois = int(date_str[2:4])
            annee = int(date_str[4:6]) + 2000
        elif len(date_str) == 8:  # 31012026
            jour = int(date_str[0:2])
            mois = int(date_str[2:4])
            annee = int(date_str[4:8])
        else:
            return None
        return pd.Timestamp(year=annee, month=mois, day=jour)
    return None

def extraire_mois_depuis_nom(feuille_nom):
    """
    Retourne le mois pour le pivot final
    """
    date = extraire_date_depuis_nom(feuille_nom)
    if date:
        return date.strftime("%b-%Y").upper()
    return pd.Timestamp.today().strftime("%b-%Y").upper()

# ----------------------------
# Streamlit
# ----------------------------
def show():
    st.set_page_config(layout="wide")
    st.title("📊 RECAP RÉABO CONSOLIDÉ FINAL")

    uploaded_files = st.file_uploader(
        "Importer les fichiers Excel",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        return

    # =============================
    # Étape 1 : trouver toutes les feuilles valides et déterminer la date max
    # =============================
    feuilles_a_traiter_par_fichier = {}

    for f in uploaded_files:
        try:
            xls = pd.ExcelFile(f)
            feuilles_valides = [
                (sheet, extraire_date_depuis_nom(sheet))
                for sheet in xls.sheet_names
                if "detail reabo" in sheet.lower() and "detail recru topup" not in sheet.lower()
            ]
            # Retirer les feuilles où la date n'a pas pu être extraite
            feuilles_valides = [(s,d) for s,d in feuilles_valides if d is not None]

            if feuilles_valides:
                # Date max parmi toutes les feuilles du fichier
                date_max = max([d for _, d in feuilles_valides])
                # Toutes les feuilles dont la date = date_max
                feuilles_max = [s for s,d in feuilles_valides if d == date_max]
                feuilles_a_traiter_par_fichier[f.name] = feuilles_max
                st.info(f"Fichier: {f.name} → Feuilles traitées: {', '.join(feuilles_max)}")
            else:
                st.warning(f"Fichier: {f.name} → Aucune feuille valide à traiter")
        except Exception as e:
            st.error(f"Impossible de lire {f.name} : {e}")

    # =============================
    # Étape 2 : Lancer le traitement
    # =============================
    if st.button("🟢 Lancer le traitement"):

        toutes_donnees = []

        for fichier in uploaded_files:
            nom_fichier = fichier.name
            if nom_fichier not in feuilles_a_traiter_par_fichier:
                continue

            for sheet in feuilles_a_traiter_par_fichier[nom_fichier]:
                try:
                    df = pd.read_excel(fichier, sheet_name=sheet)
                except:
                    continue

                # Nettoyage colonnes
                df.columns = df.columns.astype(str).str.strip()
                mois_str = extraire_mois_depuis_nom(sheet)

                # -------------------------
                # Cas 1 : feuille classique CODE_RS / RESEAUTEUR / CODE / MARCHAND / Total général
                # -------------------------
                if {"CODE_RS", "RESEAUTEUR", "CODE", "MARCHAND", "Total général"}.issubset(df.columns):
                    temp = df[["CODE_RS", "RESEAUTEUR", "CODE", "MARCHAND", "Total général"]].copy()

                    # Conversion Total général en float
                    temp["Total général"] = (
                        temp["Total général"]
                        .astype(str)
                        .str.replace(" ", "")
                        .str.replace(",", "")
                        .astype(float)
                    )

                    temp["MOIS"] = mois_str

                    # Mapping pour consolidation
                    mapping_reseau = {row["CODE"]: (row["CODE_RS"], row["RESEAUTEUR"]) for _, row in temp.iterrows()}

                    temp["CODE_RS"] = temp["CODE"]
                    temp["RESEAUTEUR"] = temp["MARCHAND"]

                    toutes_donnees.append(temp[["CODE_RS", "RESEAUTEUR", "Total général", "MOIS"]])

                # -------------------------
                # Cas 2 : feuille simple NUMDIST / NOMDIST / Total général
                # -------------------------
                elif {"NUMDIST", "NOMDIST", "Total général"}.issubset(df.columns):
                    temp = df[["NUMDIST", "NOMDIST", "Total général"]].copy()

                    # Conversion Total général en float
                    temp["Total général"] = (
                        temp["Total général"]
                        .astype(str)
                        .str.replace(" ", "")
                        .str.replace(",", "")
                        .astype(float)
                    )

                    temp["MOIS"] = mois_str

                    # Assignation directe (évite le mapping vide)
                    temp["CODE_RS"] = temp["NUMDIST"]
                    temp["RESEAUTEUR"] = temp["NOMDIST"]

                    toutes_donnees.append(temp[["CODE_RS", "RESEAUTEUR", "Total général", "MOIS"]])

        # -------------------------
        # Consolidation finale
        # -------------------------
        if not toutes_donnees:
            st.warning("Aucune donnée valide trouvée dans les fichiers uploadés.")
            return

        df_global = pd.concat(toutes_donnees, ignore_index=True)

        df_global_agg = df_global.groupby(
            ["CODE_RS", "RESEAUTEUR", "MOIS"], as_index=False
        )["Total général"].sum()

        pivot_final = df_global_agg.pivot_table(
            index=["CODE_RS", "RESEAUTEUR"],
            columns="MOIS",
            values="Total général",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        pivot_final.rename(columns={
            "CODE_RS": "NUMDIST",
            "RESEAUTEUR": "NOMDIST"
        }, inplace=True)

        # Tri chronologique des mois
        mois_cols = [col for col in pivot_final.columns if col not in ["NUMDIST", "NOMDIST"]]
        try:
            mois_cols_sorted = sorted(
                mois_cols,
                key=lambda x: pd.to_datetime(x, format="%b-%Y")
            )
            pivot_final = pivot_final[["NUMDIST", "NOMDIST"] + mois_cols_sorted]
        except:
            pass

        st.subheader("📋 RECAP FINAL PAR PARTENAIRE")
        st.dataframe(pivot_final, use_container_width=True)

        # Export Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            pivot_final.to_excel(writer, sheet_name="Recap_Partenaires", index=False)

        st.download_button(
            label="📥 Télécharger le fichier consolidé",
            data=output.getvalue(),
            file_name="recap_reabo_consolide.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
