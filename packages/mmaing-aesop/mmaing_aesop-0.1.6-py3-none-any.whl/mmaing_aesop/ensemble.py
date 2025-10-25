import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from pyod.models.copod import COPOD

def treina_ensemble(data_T, data_V, contamination=0.4):
    """
    Treina e aplica o ensemble: IF, LOF, OCSVM e COPOD.
    Retorna as predições individuais e a soma ENSEMBLE.
    """

    # Modelos
    ISF = IsolationForest(
        n_estimators=500,
        contamination=contamination,
        random_state=1
    )
    LOF = LocalOutlierFactor(
        n_neighbors=500,
        contamination=contamination
    )
    OCSVM = OneClassSVM(
        nu=0.8,
        kernel="rbf",
        gamma=0.001
    )
    COPO = COPOD(
        contamination=contamination
    )

    # Treinamento
    ISF.fit(data_T)
    LOF.fit(data_T)
    OCSVM.fit(data_T)
    COPO.fit(data_T)

    # Predições nas séries de detecção
    ISF_Pred = ISF.predict(data_V)
    LOF_Pred = LOF.fit_predict(data_V)
    OCSVM_Pred = OCSVM.predict(data_V)
    COPO_Pred = COPO.predict(data_V)

    # COPOD retorna 0/1 — convertemos para 1 / -1
    COPO_Pred = np.where(COPO_Pred == 1, -1, 1)

    # Soma final
    ENSEMBLE_Pred = ISF_Pred + LOF_Pred + OCSVM_Pred + COPO_Pred

    return ISF_Pred, LOF_Pred, OCSVM_Pred, COPO_Pred, ENSEMBLE_Pred
