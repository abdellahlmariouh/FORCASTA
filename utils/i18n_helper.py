"""
FORCASTA — Dictionnaire et Système d'Internationalisation (FR / EN)
Support bilingue intégral pour usage technique et professionnel.
"""

I18N = {
    "fr": {
        # Global & Header
        "app_name": "FORCASTA",
        "app_subtitle": "Intelligence Prédictive & Séries Temporelles de Ventes",
        "active_project": "Projet actif",
        "logout": "Déconnexion",
        "user_role_admin": "ADMINISTRATEUR",
        "user_role_user": "ANALYSTE",
        "theme_dark": "Mode Sombre",
        "theme_light": "Mode Clair",
        "lang_fr": "Français",
        "lang_en": "English",
        "progress_label": "Progression du pipeline",
        "step_counter": "Étape {current} sur {total}",
        "btn_prev": "⬅️ Précédent",
        "btn_next": "Suivant ➡️",
        "btn_restart": "🔄 Revenir à l'étape 1",
        "admin_console": "Console Administrateur",
        "back_to_project": "⬅️ Revenir au Projet",

        # Projets & Navigation
        "nav_home": "Accueil",
        "btn_delete_project": "Supprimer le projet",
        "confirm_delete_project": "Confirmer la suppression",
        "project_deleted": "Projet supprimé avec succès.",
        "btn_open_project": "Ouvrir le projet",
        "home_welcome": "Tableau de Bord & Accueil",
        "home_welcome_subtitle": "Gérez vos projets d'analyse de séries temporelles et suivez vos prévisions.",
        "home_my_projects": "Mes Projets d'Analyse",
        "projects_title": "PROJETS DE VENTES",
        "new_project": "Nouveau Projet",
        "project_name": "Nom du projet",
        "project_desc": "Description (optionnelle)",
        "btn_create_project": "Créer le projet",
        "no_project_selected": "Veuillez sélectionner ou créer un projet pour accéder aux modules de prévision.",

        # Modules
        "m1_short": "1. Ingestion",
        "m1_name": "Module 1 : Ingestion & Nettoyage",
        "m1_desc": "Importation de fichiers CSV/Excel, parsing temporel, standardisation de fréquence et traitement des outliers.",
        
        "m2_short": "2. Features",
        "m2_name": "Module 2 : Feature Engineering",
        "m2_desc": "Extraction des variables calendaires et harmoniques, génération des décalages (lags) et moyennes glissantes.",
        
        "m3_short": "3. Historique",
        "m3_name": "Module 3 : Analyse Historique",
        "m3_desc": "Visualisation de l'évolution des ventes réelles, indicateurs statistiques et décomposition de la saisonnalité.",
        
        "m4_short": "4. Benchmark",
        "m4_name": "Module 4 : Benchmark & Champion",
        "m4_desc": "Comparaison de 4 architectures (Random Forest, XGBoost, SARIMAX, Prophet) et élection du Champion via le MAPE.",
        
        "m5_short": "5. Simulation",
        "m5_name": "Module 5 : Simulation Prédictive",
        "m5_desc": "Calcul des prévisions futures sur l'horizon choisi, simulation de scénarios (+/- %) et bandes de confiance.",
        
        "m6_short": "6. Conseils",
        "m6_name": "Module 6 : Conseils Stratégiques",
        "m6_desc": "Recommandations concrètes d'aide à la décision (approvisionnement, calendrier optimal des soldes et promotions).",
        
        "m7_short": "7. Exports",
        "m7_name": "Module 7 : Exports & Rapports",
        "m7_desc": "Génération et téléchargement direct des résultats et synthèses au format CSV et classeur Excel multi-feuilles.",

        # Status
        "status_ready": "Validé",
        "status_pending": "En attente",
        "require_m1": "⚠️ Veuillez d'abord valider le Module 1 (Données & Nettoyage).",
        "require_m5": "⚠️ Les prévisions complètes sont requises. Exécutez le Module 5 d'abord.",
        
        # M1 UI
        "m1_tab_upload": "📂 Importer un Fichier (CSV / Excel)",
        "m1_tab_demo": "🚀 Données de Démonstration",
        "m1_upload_prompt": "Sélectionnez votre fichier de ventes (CSV ou Excel)",
        "m1_btn_demo": "🚀 Charger les Données Mensuelles de Démonstration",
        "m1_date_col": "Colonne Date",
        "m1_sales_col": "Colonne Ventes",
        "m1_freq": "Fréquence temporelle",
        "m1_outliers": "Plafonner les outliers (3σ)",
        "m1_btn_clean": "✨ Nettoyer & Structurer la Série Temporelle",
        "m1_kpi_obs": "Observations validées",
        "m1_kpi_start": "Date Début",
        "m1_kpi_end": "Date Fin",
        "m1_kpi_freq": "Fréquence",

        # M2 UI
        "m2_lags": "Retards temporels (Lags séparés par virgules) :",
        "m2_rolling": "Fenêtres glissantes (Rolling Stats) :",
        "m2_btn_calc": "⚙️ Extraire les Variables & Statistiques",

        # M3 UI
        "m3_kpi_avg": "Vente Moyenne",
        "m3_kpi_std": "Écart-Type (σ)",
        "m3_kpi_min": "Minimum Vendu",
        "m3_kpi_max": "Pic Historique",
        "m3_kpi_growth": "Croissance Nette",
        "m3_tab_trend": "Série & Moyenne Mobile",
        "m3_tab_monthly": "Saisonnalité Mensuelle",
        "m3_tab_yearly": "Volumes Annuels",

        # M4 UI
        "m4_btn_eval": "🚀 Lancer l'Évaluation Comparative des 4 Modèles",
        "m4_table_algo": "Algorithme",
        "m4_table_mape": "Taux d'erreur (MAPE)",
        "m4_table_qual": "Qualification",
        "m4_table_champ": "Statut Champion",
        "m4_selected_model": "Modèle retenu pour les prévisions :",

        # M5 UI
        "m5_horizon": "Horizon de prévision (périodes futures) :",
        "m5_scenario": "Simulation de scénario (+/- % ventes) :",
        "m5_btn_calc": "🔮 Calculer les Projections Futures",
        "m5_chart_title": "Projection Graphique : Historique, Prévision & Incertitude",

        # M6 UI
        "m6_title": "🧠 Synthèse Décisionnelle générée par l'IA",

        # M7 UI
        "m7_csv_title": "📄 Fichier CSV",
        "m7_csv_desc": "Télécharger les projections futures et scénarios directement en CSV.",
        "m7_btn_csv": "⬇️ Télécharger Prévisions (CSV)",
        "m7_xlsx_title": "📊 Classeur Excel Multi-Feuilles",
        "m7_xlsx_desc": "Rapport complet avec onglets Historique Nettoyé et Prévisions Futures.",
        "m7_btn_xlsx": "⬇️ Télécharger Rapport Global (Excel .xlsx)",
    },
    "en": {
        # Global & Header
        "app_name": "FORCASTA",
        "app_subtitle": "Predictive Intelligence & Commercial Time-Series Forecasting",
        "active_project": "Active Project",
        "logout": "Sign Out",
        "user_role_admin": "ADMINISTRATOR",
        "user_role_user": "ANALYST",
        "theme_dark": "Dark Mode",
        "theme_light": "Light Mode",
        "lang_fr": "Français",
        "lang_en": "English",
        "progress_label": "Pipeline completion",
        "step_counter": "Step {current} of {total}",
        "btn_prev": "⬅️ Previous",
        "btn_next": "Next ➡️",
        "btn_restart": "🔄 Return to Step 1",
        "admin_console": "Admin Console",
        "back_to_project": "⬅️ Back to Project",

        # Projects & Navigation
        "nav_home": "Home",
        "btn_delete_project": "Delete Project",
        "confirm_delete_project": "Confirm Deletion",
        "project_deleted": "Project deleted successfully.",
        "btn_open_project": "Open Project",
        "home_welcome": "Dashboard & Home",
        "home_welcome_subtitle": "Manage your time-series projects and track commercial forecasts.",
        "home_my_projects": "My Sales Projects",
        "projects_title": "SALES PROJECTS",
        "new_project": "New Project",
        "project_name": "Project Name",
        "project_desc": "Description (optional)",
        "btn_create_project": "Create Project",
        "no_project_selected": "Please select or create a project to access forecasting modules.",

        # Modules
        "m1_short": "1. Ingestion",
        "m1_name": "Module 1: Ingestion & Cleaning",
        "m1_desc": "CSV/Excel data import, datetime parsing, frequency standardization, and outlier mitigation.",
        
        "m2_short": "2. Features",
        "m2_name": "Module 2: Feature Engineering",
        "m2_desc": "Calendar & harmonic indicator extraction, temporal lag generators, and moving rolling statistics.",
        
        "m3_short": "3. History",
        "m3_name": "Module 3: Historical Analysis",
        "m3_desc": "Chronological sales exploration, statistical volatility indicators, and monthly seasonality breakdown.",
        
        "m4_short": "4. Benchmark",
        "m4_name": "Module 4: Benchmark & Champion",
        "m4_desc": "Cross-validation of 4 algorithms (Random Forest, XGBoost, SARIMAX, Prophet) with automated Champion election via MAPE.",
        
        "m5_short": "5. Simulation",
        "m5_name": "Module 5: Predictive Simulation",
        "m5_desc": "Forward-looking forecasts across a target horizon, What-If scenario simulation (+/- %), and statistical confidence intervals.",
        
        "m6_short": "6. Insights",
        "m6_name": "Module 6: Strategic Insights",
        "m6_desc": "Actionable decision support generated by machine learning (supply planning, optimal promotional timing).",
        
        "m7_short": "7. Exports",
        "m7_name": "Module 7: Exports & Reports",
        "m7_desc": "Direct export of forecasted series and analytical summaries in CSV and multi-tab formatted Excel workbooks.",

        # Status
        "status_ready": "Completed",
        "status_pending": "Pending",
        "require_m1": "⚠️ Please complete Module 1 (Data Ingestion & Cleaning) first.",
        "require_m5": "⚠️ Complete forecast projections are required. Run Module 5 first.",
        
        # M1 UI
        "m1_tab_upload": "📂 Upload Dataset (CSV / Excel)",
        "m1_tab_demo": "🚀 Built-in Demo Dataset",
        "m1_upload_prompt": "Select your sales time-series file (CSV or Excel)",
        "m1_btn_demo": "🚀 Load Demo Dataset (36 Months Sales)",
        "m1_date_col": "Date Column",
        "m1_sales_col": "Sales Column",
        "m1_freq": "Time Frequency",
        "m1_outliers": "Cap Outliers (3σ)",
        "m1_btn_clean": "✨ Clean & Standardize Time-Series",
        "m1_kpi_obs": "Validated Records",
        "m1_kpi_start": "Start Date",
        "m1_kpi_end": "End Date",
        "m1_kpi_freq": "Frequency",

        # M2 UI
        "m2_lags": "Temporal Lags (comma-separated):",
        "m2_rolling": "Rolling Windows (Rolling Stats):",
        "m2_btn_calc": "⚙️ Extract Features & Statistics",

        # M3 UI
        "m3_kpi_avg": "Mean Sales",
        "m3_kpi_std": "Volatility (σ)",
        "m3_kpi_min": "Historical Min",
        "m3_kpi_max": "Historical Peak",
        "m3_kpi_growth": "Net Growth",
        "m3_tab_trend": "Series & Moving Average",
        "m3_tab_monthly": "Monthly Seasonality",
        "m3_tab_yearly": "Annual Totals",

        # M4 UI
        "m4_btn_eval": "🚀 Launch 4-Model Comparative Benchmark",
        "m4_table_algo": "Algorithm",
        "m4_table_mape": "Error Rate (MAPE)",
        "m4_table_qual": "Reliability Index",
        "m4_table_champ": "Champion Status",
        "m4_selected_model": "Active Model for Predictions:",

        # M5 UI
        "m5_horizon": "Forecast Horizon (Future Periods):",
        "m5_scenario": "What-If Scenario (+/- % sales):",
        "m5_btn_calc": "🔮 Compute Forward Projections",
        "m5_chart_title": "Projection Plot: Historical Actuals, Baseline & Confidence Interval",

        # M6 UI
        "m6_title": "🧠 AI Strategic Decision Support",

        # M7 UI
        "m7_csv_title": "📄 Raw CSV Export",
        "m7_csv_desc": "Download raw projections and simulated scenarios in CSV format.",
        "m7_btn_csv": "⬇️ Download Forecast (CSV)",
        "m7_xlsx_title": "📊 Multi-Sheet Excel Workbook",
        "m7_xlsx_desc": "Executive workbook containing Cleaned History and Future Projections.",
        "m7_btn_xlsx": "⬇️ Download Full Report (Excel .xlsx)",
    }
}

def t(key: str, lang: str = "fr", **kwargs) -> str:
    """Renvoie la chaîne traduite selon la langue active ('fr' ou 'en')."""
    text = I18N.get(lang, I18N["fr"]).get(key, I18N["fr"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
