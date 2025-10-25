import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from pyod.models.copod import COPOD

def treina_ensemble(data_T, data_V, contamination=0.4):
    """Treina ensemble de anomalias ISF, LOF, OCSVM e COPOD."""

    ISF = IsolationForest(n_estimators=500, contamination=contamination, random_state=1)
    LOF = LocalOutlierFactor(n_neighbors=50, contamination=contamination)
    OCSVM = OneClassSVM(nu=0.8, kernel='rbf', gamma=0.001)
    COPO = COPOD(contamination=contamination)

    ISF.fit(data_T)
    LOF.fit(data_T)
    OCSVM.fit(data_T)
    COPO.fit(data_T)

    ISF_Pred = ISF.predict(data_V)
    LOF_Pred = LOF.fit_predict(data_V)
    OCSVM_Pred = OCSVM.predict(data_V)

    # Ajuste COPOD (1 = normal, 0 = anomalia → converte para -1/1)
    COPO_Pred = COPO.predict(data_V)
    COPO_Pred = np.where(COPO_Pred == 1, -1, 1)

    ENSEMBLE_Pred = ISF_Pred + LOF_Pred + OCSVM_Pred + COPO_Pred

    return ISF_Pred, LOF_Pred, OCSVM_Pred, COPO_Pred, ENSEMBLE_Pred
