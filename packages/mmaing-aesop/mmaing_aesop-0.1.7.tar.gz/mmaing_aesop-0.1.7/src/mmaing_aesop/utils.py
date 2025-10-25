import numpy as np
import pandas as pd
from scipy import stats

def filtraMun(df):
    """Agrupa valores por município, ano e semana epidemiológica (soma atend_ivas)."""
    dados_agp = df.groupby(['co_ibge','municipio','ano','epiweek'])['atend_ivas'].sum()
    dataAGP = pd.DataFrame(dados_agp).reset_index()
    return dataAGP

def calculo_rt(n, m, gamma, q, serie):
    """Cálculo do Rt (adaptado do código original)."""
    rt = [0] * n
    w = [0.0] * (m + 1)

    for i in range(1, n + 1):
        deno = 0.0
        ie = min(i, m)

        if ie > 1:
            ww = ((1 - q) ** 2) / (q * (1.0 + (ie - 1) * q ** ie - ie * q ** (ie - 1)))
            for j in range(1, ie + 1):
                w[j] = ww * (j - 1) * q ** (j - 1)
                deno += w[j] * serie[i - j]

            if deno != 0:
                rt[i - 1] = serie[i - 1] / deno

    return rt

def calculate_limit_sazonal(df_rgi, baseline_years, alpha=0.05):
    """Limite histórico (por semana epi) baseado nos anos do baseline."""
    limits = []
    semanas = df_rgi['epiweek'].values

    for w in semanas:
        filtered_df = df_rgi[(df_rgi['ano'].isin(baseline_years)) & (df_rgi['epiweek'] == w)]
        data_week = filtered_df['atend_ivas']
        media = np.mean(data_week)
        desvio = np.std(data_week, ddof=0)
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        limit = media + z_alpha * (desvio / np.sqrt(len(data_week)))
        limits.append(limit)

    return limits

def calculate_limit(serie, l=5, alpha=0.05):
    """Limite do passado recente (média móvel + intervalo normal)."""
    n = len(serie)
    z_alpha = stats.norm.ppf(1 - alpha / 2)

    actual_l = min(l, n)
    media_movel = np.convolve(serie, np.ones(actual_l) / actual_l, mode='valid')
    media_movel = np.concatenate(([media_movel[0]] * (actual_l - 1), media_movel))

    variabilidade = [np.std(serie[max(0, i-(actual_l-1)):i+1]) for i in range(n)]
    variabilidade = np.array(variabilidade)

    threshold = media_movel + z_alpha * variabilidade / np.sqrt(actual_l)
    return threshold
