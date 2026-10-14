"""
FORCASTA — Module de Simulation & Prévisions Futures (V5 - Architecture Haute Précision)

Fournit les prévisions futures sur l'horizon choisi avec le modèle sélectionné
(Random Forest, XGBoost, SARIMAX, Prophet) et applique les scénarios de simulation.
"""

import warnings
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

# Silence noisy libraries
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from modules.models import infer_freq, extract_calendar_features


# ═════════════════════════════════════════════════════════════════════════════
# 1. Génération Sûre des Dates Futures
# ═════════════════════════════════════════════════════════════════════════════
def build_future_dates(last_date, horizon, freq="D"):
    """
    Construit l'index temporel futur selon la fréquence détectée.
    Empêche les erreurs de type string/Timestamp.
    """
    last_date = pd.to_datetime(last_date)
    
    if freq == "M":
        # Fin de mois
        return pd.date_range(start=last_date + pd.DateOffset(days=1), periods=horizon, freq="ME")
    elif freq == "W":
        # Hebdomadaire (même jour de semaine)
        return pd.date_range(start=last_date + pd.DateOffset(days=7), periods=horizon, freq="W")
    else:
        # Journalier
        return pd.date_range(start=last_date + pd.DateOffset(days=1), periods=horizon, freq="D")


# ═════════════════════════════════════════════════════════════════════════════
# 2. Ré-entraînement sur tout l'historique et Prévision Future
# ═════════════════════════════════════════════════════════════════════════════
def refit_and_forecast(model_name, df, horizon, freq=None):
    """
    Ré-entraîne le modèle choisi sur l'ensemble des données historiques et projette
    la prévision de base (Baseline) sur 'horizon' périodes.
    """
    # Nettoyage et tri
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce").fillna(0)

    dates = df["Date"]
    y = df["Sales"].values.astype(float)
    n = len(df)
    last_date = dates.iloc[-1]

    # Détection automatique de la fréquence si non fournie ou incompatible
    detected_freq = infer_freq(dates)
    if freq is None or freq not in ["D", "W", "M"]:
        freq = detected_freq

    future_dates = build_future_dates(last_date, horizon, freq)
    forecast_df = pd.DataFrame({"Date": future_dates})

    # Fallback intelligent (tendance moyenne récente au lieu d'une valeur plate)
    recent_mean = float(np.mean(y[-min(n, 12):])) if n > 0 else 100.0

    # ─────────────────────────────────────────────────────────────────────────
    # A. Modèles à Décomposition ML (Random Forest & XGBoost)
    # ─────────────────────────────────────────────────────────────────────────
    if model_name in ["Random Forest", "XGBoost"]:
        try:
            # 1. Tendance globale
            t_train = np.arange(n).reshape(-1, 1)
            t_future = np.arange(n, n + horizon).reshape(-1, 1)
            ridge = Ridge(alpha=1.0)
            ridge.fit(t_train, y)
            trend_future = ridge.predict(t_future)
            residuals_train = y - ridge.predict(t_train)

            # 2. Features calendaires pour le passé et le futur
            X_train = extract_calendar_features(dates)
            X_future = extract_calendar_features(future_dates)

            # 3. Fit et prédiction
            if model_name == "Random Forest" or not XGB_AVAILABLE:
                ml_model = RandomForestRegressor(
                    n_estimators=100, 
                    max_depth=8, 
                    min_samples_split=4, 
                    random_state=42
                )
            else:
                ml_model = xgb.XGBRegressor(
                    n_estimators=100, 
                    learning_rate=0.05, 
                    max_depth=4, 
                    random_state=42, 
                    verbosity=0
                )

            ml_model.fit(X_train, residuals_train)
            pred_res = ml_model.predict(X_future)
            preds = np.clip(trend_future + pred_res, a_min=0, a_max=None)
            forecast_df["Baseline_Sales"] = np.round(preds, 2)
            return forecast_df

        except Exception as e:
            print(f"Erreur forecast ML ({model_name}): {e}")
            forecast_df["Baseline_Sales"] = recent_mean
            return forecast_df

    # ─────────────────────────────────────────────────────────────────────────
    # B. SARIMAX
    # ─────────────────────────────────────────────────────────────────────────
    elif model_name == "SARIMAX":
        try:
            if freq == "M":
                s = 12 if n >= 24 else 0
            elif freq == "W":
                s = 4 if n >= 12 else 0
            else:
                s = 7 if n >= 21 else 0

            order = (1, 1, 1)
            seasonal_order = (1, 0, 0, s) if s > 0 else (0, 0, 0, 0)

            m = SARIMAX(
                y, 
                order=order, 
                seasonal_order=seasonal_order, 
                enforce_stationarity=False, 
                enforce_invertibility=False
            )
            fit = m.fit(disp=False, maxiter=60)
            preds = fit.forecast(steps=horizon)
            preds = np.clip(preds, a_min=0, a_max=None)
            forecast_df["Baseline_Sales"] = np.round(preds, 2)
            return forecast_df

        except Exception as e:
            print(f"Erreur forecast SARIMAX: {e}")
            # Si SARIMAX échoue, utiliser la décomposition RF
            return refit_and_forecast("Random Forest", df, horizon, freq)

    # ─────────────────────────────────────────────────────────────────────────
    # C. Prophet
    # ─────────────────────────────────────────────────────────────────────────
    elif model_name == "Prophet":
        if not PROPHET_AVAILABLE:
            return refit_and_forecast("Random Forest", df, horizon, freq)

        try:
            prophet_df = pd.DataFrame({"ds": dates, "y": y})
            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=(freq == "D"),
                daily_seasonality=False,
                changepoint_prior_scale=0.05
            )
            m.fit(prophet_df)
            future_df = pd.DataFrame({"ds": future_dates})
            fc = m.predict(future_df)
            preds = np.clip(fc["yhat"].values, a_min=0, a_max=None)
            forecast_df["Baseline_Sales"] = np.round(preds, 2)
            return forecast_df

        except Exception as e:
            print(f"Erreur forecast Prophet: {e}")
            return refit_and_forecast("Random Forest", df, horizon, freq)

    # Modèle inconnu -> fallback RF
    return refit_and_forecast("Random Forest", df, horizon, freq)


# ═════════════════════════════════════════════════════════════════════════════
# 3. Application des Scénarios de Simulation
# ═════════════════════════════════════════════════════════════════════════════
def apply_simulations(forecast_df, scenarios):
    """
    Applique les variations en pourcentage des scénarios d'événements
    sur la prévision Baseline pour obtenir la prévision Simulated_Sales.
    """
    df_sim = forecast_df.copy()
    df_sim["Simulated_Sales"] = df_sim["Baseline_Sales"].copy()

    for sc in scenarios:
        s_start = pd.to_datetime(sc["start"])
        s_end = pd.to_datetime(sc["end"])
        impact = 1.0 + (sc["impact_pct"] / 100.0)

        mask = (df_sim["Date"] >= s_start) & (df_sim["Date"] <= s_end)
        df_sim.loc[mask, "Simulated_Sales"] = np.round(df_sim.loc[mask, "Simulated_Sales"] * impact, 2)

    return df_sim
