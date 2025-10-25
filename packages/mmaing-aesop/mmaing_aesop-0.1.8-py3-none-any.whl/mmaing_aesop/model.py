import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from .utils import filtraMun, calculo_rt, calculate_limit_sazonal, calculate_limit
from .ensemble import treina_ensemble
from .plot import plot_ews

class MMAING:
    """
    MMAING-AESOP — Early Warning System usando Rt + Ensemble ML
    """

    def __init__(
        self,
        limiar_rt=1.25,
        window_rt=5,
        gamma=0.2,
        contamination=0.4,
        vote_threshold=3,
        alpha=0.05,
        baseline_years=[2017, 2018, 2019],
        start_year_detection=2020
    ):
        self.limiar_rt = limiar_rt
        self.window_rt = window_rt
        self.gamma = gamma
        self.contamination = contamination
        self.vote_threshold = vote_threshold
        self.alpha = alpha
        self.baseline_years = baseline_years
        self.start_year_detection = start_year_detection
        self.result_ = None

    def fit(self, df: pd.DataFrame):
        """ Executa o MMAING para todos os municípios do dataframe. """
        dadosAGP = filtraMun(df)
        municipios = dadosAGP['co_ibge'].unique()
        result_final = pd.DataFrame()

        for mun in municipios:
            df_mun = dadosAGP[dadosAGP['co_ibge'] == mun]
            df_proc = self._process_single_municipio(df_mun)
            result_final = pd.concat([result_final, df_proc], ignore_index=True)

        self.result_ = result_final
        return self

    def _process_single_municipio(self, df_mun: pd.DataFrame) -> pd.DataFrame:
        DADOS_TREINO = df_mun[df_mun['ano'].isin(self.baseline_years]]
        DADOS_DETECCAO = df_mun[df_mun['ano'] >= self.start_year_detection].copy()

        n = len(DADOS_DETECCAO)
        serie = DADOS_DETECCAO['atend_ivas'].values
        q = np.exp(-self.gamma)

        # Rt
        rt = calculo_rt(n, self.window_rt, self.gamma, q, serie)

        # Limites
        limite1 = calculate_limit_sazonal(df_mun, self.baseline_years, alpha=self.alpha)
        limite1 = (pd.Series(limite1)
                   .reindex(range(len(df_mun)))  # garante alinhamento
                   .tail(n)                      # pega apenas anos deteccao
                   .reset_index(drop=True))

        limite2 = calculate_limit(serie)

        DADOS_DETECCAO['limite1'] = limite1
        DADOS_DETECCAO['limite2'] = limite2
        DADOS_DETECCAO['upperbound'] = DADOS_DETECCAO[['limite1', 'limite2']].max(axis=1, skipna=True)
        DADOS_DETECCAO['excesso'] = DADOS_DETECCAO['atend_ivas'] - DADOS_DETECCAO['upperbound']

        # Normalização
        scaler_T = MinMaxScaler()
        scaler_V = MinMaxScaler()
        dados_T = scaler_T.fit_transform(DADOS_TREINO['atend_ivas'].values.reshape(-1,1))
        dados_V = scaler_V.fit_transform(DADOS_DETECCAO['atend_ivas'].values.reshape(-1,1))
        dados_V_inv = scaler_V.inverse_transform(dados_V)

        # Ensemble ML
        ISF, LOF, OCSVM, COPOD, _ = treina_ensemble(dados_T, dados_V, contamination=self.contamination)

        # Votação
        final_alerta = []
        for i in range(n):
            votos = sum([ISF[i] == -1, LOF[i] == -1, OCSVM[i] == -1, COPOD[i] == -1])
            if rt[i] > self.limiar_rt:
                votos += 1
            final_alerta.append('Sim' if (votos >= self.vote_threshold and
                                          dados_V_inv[i][0] > DADOS_DETECCAO['upperbound'].iloc[i]) else 'Não')

        # Salva EWS
        DADOS_DETECCAO['rt'] = rt
        DADOS_DETECCAO['EWS_ISF'] = ['Sim' if (ISF[i] == -1) else 'Não' for i in range(n)]
        DADOS_DETECCAO['EWS_LOF'] = ['Sim' if (LOF[i] == -1) else 'Não' for i in range(n)]
        DADOS_DETECCAO['EWS_OCSVM'] = ['Sim' if (OCSVM[i] == -1) else 'Não' for i in range(n)]
        DADOS_DETECCAO['EWS_COPOD'] = ['Sim' if (COPOD[i] == -1) else 'Não' for i in range(n)]
        DADOS_DETECCAO['EWS_Rt'] = ['Sim' if (rt[i] > self.limiar_rt) else 'Não' for i in range(n)]
        DADOS_DETECCAO['EWS_MMAING'] = final_alerta

        return DADOS_DETECCAO

    def get_alerts(self):
        if self.result_ is None:
            raise ValueError("Execute modelo.fit(df) antes de get_alerts()")
        return self.result_[['co_ibge','ano','epiweek','EWS_MMAING']]

    def get_results(self):
        if self.result_ is None:
            raise ValueError("Execute modelo.fit(df) antes de get_results()")
        return self.result_

    def to_csv(self, path):
        if self.result_ is None:
            raise ValueError("Execute modelo.fit(df) antes de to_csv()")
        self.result_.to_csv(path, index=False, sep=';')
        return path

    def plot(self, co_ibge):
        if self.result_ is None:
            raise ValueError("Execute modelo.fit(df) antes de plot()")
        df_mun = self.result_[self.result_['co_ibge'] == co_ibge]
        if df_mun.empty:
            raise ValueError(f"Município {co_ibge} não encontrado nos resultados.")
        plot_ews(df_mun, co_ibge)
