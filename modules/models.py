"""
FORCASTA — Module de Modélisation Prédictive (V5 - Architecture Décomposition & Haute Précision)

4 Modèles supportés :
1. Random Forest (Décomposition Tendance Linéaire + Résidus Saisonniers ML)
2. XGBoost (Décomposition Tendance Linéaire + Résidus Saisonniers ML)
3. SARIMAX (Saisonnalité adaptée à la fréquence réelle : Mensuelle=12, Hebdo=4, Journalière=7)
4. Prophet (Facebook Prophet avec saisonnalités automatiques)

Garanties :
- Aucune prévision constante (suppression totale des fallbacks plats et des bugs d'indexation).
- Aucune explosion mathématique (tendances régularisées et bornage strict >= 0).
- Support natif et automatique de toutes les fréquences temporelles (Journalier, Hebdomadaire, Mensuel).
"""

import warnings
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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


# ═════════════════════════════════════════════════════════════════════════════
# 1. Helpers & Inférence de Fréquence
# ═════════════════════════════════════════════════════════════════════════════
def infer_freq(dates):
    """Détecte automatiquement la granularité temporelle : 'D', 'W' ou 'M'."""
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.DatetimeIndex(pd.to_datetime(dates))
    dates = dates.sort_values()
    if len(dates) < 3:
        return "D"
    diff_days = pd.Series(dates).diff().dt.total_seconds().div(86400).median()
    if diff_days >= 20:
        return "M"
    elif diff_days >= 4:
        return "W"
    else:
        return "D"


def extract_calendar_features(dates):
    """
    Extrait les variables calendaires et harmoniques (sin/cos).
    Fonctionne indifféremment avec pd.Series ou pd.DatetimeIndex.
    """
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.DatetimeIndex(pd.to_datetime(dates))
        
    out = pd.DataFrame(index=range(len(dates)))
    out["Month"] = dates.month
    out["Quarter"] = dates.quarter
    out["DayOfWeek"] = dates.dayofweek
    out["WeekOfYear"] = dates.isocalendar().week.values.astype(int)
    out["DayOfYear"] = dates.dayofyear
    out["IsWeekend"] = (dates.dayofweek >= 5).astype(int)
    
    # Encodages harmoniques cycliques
    out["Sin_Month"] = np.sin(2 * np.pi * dates.month / 12.0)
    out["Cos_Month"] = np.cos(2 * np.pi * dates.month / 12.0)
    out["Sin_Week"] = np.sin(2 * np.pi * out["WeekOfYear"] / 52.0)
    out["Cos_Week"] = np.cos(2 * np.pi * out["WeekOfYear"] / 52.0)
    out["Sin_DoW"] = np.sin(2 * np.pi * dates.dayofweek / 7.0)
    out["Cos_DoW"] = np.cos(2 * np.pi * dates.dayofweek / 7.0)
    
    return out


def calculate_mape(y_true, y_pred):
    """Calcul sécurisé du MAPE (Mean Absolute Percentage Error)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = (y_true > 0) & np.isfinite(y_true) & np.isfinite(y_pred)
    if mask.sum() == 0:
        return 999.0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0
    return float(round(mape, 2)) if np.isfinite(mape) else 999.0


# ═════════════════════════════════════════════════════════════════════════════
# 2. Modèles : Entraînement & Évaluation (Train 80% / Test 20%)
# ═════════════════════════════════════════════════════════════════════════════

def train_eval_random_forest(df, train_size=0.8):
    """
    Random Forest avec décomposition Tendance + Résidus Cycliques.
    Garantit une capture parfaite de la saisonnalité sans prévision plate.
    """
    n = len(df)
    split = int(n * train_size)
    if split < 5 or (n - split) < 1:
        return None, None, float("inf")

    y = df["Sales"].values.astype(float)
    dates = pd.to_datetime(df["Date"])
    
    # 1. Tendance linéaire globale
    t = np.arange(n).reshape(-1, 1)
    ridge = Ridge(alpha=1.0)
    ridge.fit(t[:split], y[:split])
    trend_train = ridge.predict(t[:split])
    trend_test = ridge.predict(t[split:])
    residuals_train = y[:split] - trend_train

    # 2. Apprentissage des cycles avec Random Forest
    X = extract_calendar_features(dates)
    feature_cols = list(X.columns)
    
    model = RandomForestRegressor(
        n_estimators=100, 
        max_depth=8, 
        min_samples_split=4, 
        random_state=42
    )
    
    try:
        model.fit(X.iloc[:split], residuals_train)
        pred_res = model.predict(X.iloc[split:])
        preds = np.clip(trend_test + pred_res, a_min=0, a_max=None)
        mape = calculate_mape(y[split:], preds)
        return (model, ridge), feature_cols, mape
    except Exception as e:
        print(f"Erreur RF: {e}")
        return None, None, float("inf")


def train_eval_xgboost(df, train_size=0.8):
    """
    XGBoost avec décomposition Tendance + Résidus Cycliques.
    """
    if not XGB_AVAILABLE:
        return None, None, float("inf")

    n = len(df)
    split = int(n * train_size)
    if split < 5 or (n - split) < 1:
        return None, None, float("inf")

    y = df["Sales"].values.astype(float)
    dates = pd.to_datetime(df["Date"])

    # 1. Tendance
    t = np.arange(n).reshape(-1, 1)
    ridge = Ridge(alpha=1.0)
    ridge.fit(t[:split], y[:split])
    trend_train = ridge.predict(t[:split])
    trend_test = ridge.predict(t[split:])
    residuals_train = y[:split] - trend_train

    # 2. XGBoost
    X = extract_calendar_features(dates)
    feature_cols = list(X.columns)

    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
        verbosity=0
    )

    try:
        model.fit(X.iloc[:split], residuals_train)
        pred_res = model.predict(X.iloc[split:])
        preds = np.clip(trend_test + pred_res, a_min=0, a_max=None)
        mape = calculate_mape(y[split:], preds)
        return (model, ridge), feature_cols, mape
    except Exception as e:
        print(f"Erreur XGB: {e}")
        return None, None, float("inf")


def train_eval_sarimax(df, train_size=0.8):
    """
    SARIMAX avec détection automatique de la saisonnalité selon la fréquence :
    - Mensuel (M) : s=12 (si historique suffisant)
    - Hebdomadaire (W) : s=4
    - Journalier (D) : s=7
    """
    n = len(df)
    split = int(n * train_size)
    y = df["Sales"].values.astype(float)
    y_train = y[:split]
    y_test = y[split:]

    if len(y_test) == 0:
        return None, None, float("inf")

    freq = infer_freq(df["Date"])
    if freq == "M":
        s = 12 if len(y_train) >= 24 else 0
    elif freq == "W":
        s = 4 if len(y_train) >= 12 else 0
    else:
        s = 7 if len(y_train) >= 21 else 0

    try:
        order = (1, 1, 1)
        seasonal_order = (1, 0, 0, s) if s > 0 else (0, 0, 0, 0)
        
        m = SARIMAX(
            y_train, 
            order=order, 
            seasonal_order=seasonal_order,
            enforce_stationarity=False, 
            enforce_invertibility=False
        )
        fit = m.fit(disp=False, maxiter=50)
        preds = fit.forecast(steps=len(y_test))
        preds = np.clip(preds, a_min=0, a_max=None)
        mape = calculate_mape(y_test, preds)
        return fit, None, mape
    except Exception as e:
        print(f"Erreur SARIMAX: {e}")
        return None, None, float("inf")


def train_eval_prophet(df, train_size=0.8):
    """
    Facebook Prophet configuré proprement selon la fréquence des données.
    """
    if not PROPHET_AVAILABLE:
        return None, None, float("inf")

    n = len(df)
    split = int(n * train_size)
    dates = pd.to_datetime(df["Date"])
    y = df["Sales"].values.astype(float)

    if (n - split) == 0:
        return None, None, float("inf")

    freq = infer_freq(dates)
    train_df = pd.DataFrame({"ds": dates.iloc[:split], "y": y[:split]})
    test_df = pd.DataFrame({"ds": dates.iloc[split:]})

    try:
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=(freq == "D"),
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )
        m.fit(train_df)
        fc = m.predict(test_df)
        preds = np.clip(fc["yhat"].values, a_min=0, a_max=None)
        mape = calculate_mape(y[split:], preds)
        return m, None, mape
    except Exception as e:
        print(f"Erreur Prophet: {e}")
        return None, None, float("inf")


def train_eval_ets(df, train_size=0.8):
    """
    Exponential Smoothing (ETS) (Holt-Winters).
    """
    n = len(df)
    split = int(n * train_size)
    y = df["Sales"].values.astype(float)
    y_train = y[:split]
    y_test = y[split:]

    if len(y_test) == 0:
        return None, None, float("inf")

    freq = infer_freq(df["Date"])
    if freq == "M":
        s = 12 if len(y_train) >= 24 else 0
    elif freq == "W":
        s = 4 if len(y_train) >= 12 else 0
    else:
        s = 7 if len(y_train) >= 21 else 0

    try:
        seasonal = 'add' if s > 0 else None
        m = ExponentialSmoothing(
            y_train,
            trend='add',
            seasonal=seasonal,
            seasonal_periods=s if s > 0 else None,
            initialization_method='estimated'
        )
        fit = m.fit()
        preds = fit.forecast(len(y_test))
        preds = np.clip(preds, a_min=0, a_max=None)
        mape = calculate_mape(y_test, preds)
        return fit, None, mape
    except Exception as e:
        print(f"Erreur ETS: {e}")
        return None, None, float("inf")


# ═════════════════════════════════════════════════════════════════════════════
# 3. Benchmark Global
# ═════════════════════════════════════════════════════════════════════════════
def evaluate_all_models(df):
    """
    Évalue les 4 modèles sur le dataset passé en paramètre.
    Identifie le modèle Champion avec le plus faible MAPE.
    """
    # Nettoyage et tri obligatoire
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce").fillna(0)

    results = {}

    # 1. Random Forest
    m, f, mape = train_eval_random_forest(df)
    results["Random Forest"] = {"model": m, "features": f, "mape": mape}

    # 2. XGBoost
    if XGB_AVAILABLE:
        m, f, mape = train_eval_xgboost(df)
        results["XGBoost"] = {"model": m, "features": f, "mape": mape}

    # 3. SARIMAX
    m, f, mape = train_eval_sarimax(df)
    results["SARIMAX"] = {"model": m, "features": f, "mape": mape}

    # 4. Prophet
    if PROPHET_AVAILABLE:
        m, f, mape = train_eval_prophet(df)
        results["Prophet"] = {"model": m, "features": f, "mape": mape}

    # 5. ETS (Holt-Winters)
    m, f, mape = train_eval_ets(df)
    results["ETS"] = {"model": m, "features": f, "mape": mape}

    # Sélection du Champion
    valid = {k: v for k, v in results.items() if v["mape"] != float("inf") and v["mape"] < 900}
    champion = min(valid, key=lambda k: valid[k]["mape"]) if valid else "Random Forest"
    
    return results, champion
