import numpy as np
import pandas as pd


def generate_recommendations(history_df, forecast_df, mape, model_name):
    """
    Génère des recommandations métier basées sur l'historique récent, la prévision et le MAPE.
    """
    recos = []

    # 1. Analyse de la confiance du modèle
    if mape < 10:
        recos.append(
            (
                "✅ Confiance Forte",
                f"Le modèle **{model_name}** a un taux d'erreur (MAPE) de seulement {mape:.2f}%. Les prévisions sont très fiables, vous pouvez aligner votre chaîne d'approvisionnement dessus avec sécurité.",
            )
        )
    elif mape < 25:
        recos.append(
            (
                "⚠️ Confiance Moyenne",
                f"Le modèle **{model_name}** a un MAPE de {mape:.2f}%. Les tendances globales sont correctes, mais prévoyez un stock de sécurité de {int(mape)}% pour absorber les imprévus.",
            )
        )
    else:
        recos.append(
            (
                "❌ Confiance Faible",
                f"Le MAPE est élevé ({mape:.2f}%). Le marché est très volatil. Prenez ces prévisions à titre indicatif et croisez-les absolument avec votre intuition métier.",
            )
        )

    # 2. Analyse de la tendance (Croissance/Baisse)
    # Prendre les 20 dernières périodes de l'historique et les 20 premières périodes prévues
    n_periods = min(20, len(history_df), len(forecast_df))
    if n_periods > 0:
        last_historical_mean = history_df["Sales"].tail(n_periods).mean()
        first_forecast_mean = forecast_df["Baseline_Sales"].head(n_periods).mean()

        if last_historical_mean > 0:
            trend_pct = (
                (first_forecast_mean - last_historical_mean) / last_historical_mean
            ) * 100

            if trend_pct > 10:
                recos.append(
                    (
                        "📈 Tendance Haussière Anticipée",
                        f"Une augmentation moyenne de **{trend_pct:.1f}%** est attendue dans les prochaines périodes par rapport à vos ventes récentes. Anticipez cette demande en augmentant vos capacités de production ou vos stocks.",
                    )
                )
            elif trend_pct < -10:
                recos.append(
                    (
                        "📉 Alerte de Baisse",
                        f"Attention, une baisse moyenne de **{abs(trend_pct):.1f}%** est prévue à court terme. C'est peut-être le moment idéal pour lancer des actions marketing ciblées.",
                    )
                )
            else:
                recos.append(
                    (
                        "➡️ Stabilité du Marché",
                        "Les ventes prévues semblent stables dans un futur proche par rapport à la dynamique récente. Maintenez vos stratégies actuelles.",
                    )
                )

    # 3. Opportunité de Promotion (Trouver le "creux" prévisionnel)
    if len(forecast_df) > 7:
        min_sale_idx = forecast_df["Baseline_Sales"].idxmin()
        raw_date = forecast_df.loc[min_sale_idx, "Date"]
        min_date = pd.to_datetime(raw_date).strftime("%d %B %Y")
        recos.append(
            (
                "💡 Timing de Promotion Optimal",
                f"Le modèle détecte une chute naturelle des ventes autour du **{min_date}**. Si vous prévoyez une promotion ou des soldes, c'est le moment idéal pour les placer afin de compenser ce creux naturel.",
            )
        )

    return recos
