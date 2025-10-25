src/mmaing_aesop/plot.py
import matplotlib.pyplot as plt

def plot_ews(df_mun, co_ibge):
    """Gera o gráfico da série temporal com alertas do MMAING (pontos vermelhos)."""

    # Garante a ordem temporal
    df = df_mun.sort_values(['ano','epiweek']).reset_index(drop=True)

    # Série
    plt.figure(figsize=(12, 4))
    plt.plot(df['atend_ivas'], label='Série temporal', linewidth=1.8)

    # Alertas
    alertas = df[df['EWS_MMAING'] == 'Sim']
    plt.scatter(alertas.index, alertas['atend_ivas'], s=50, color='red', label='Alerta (EWS)')

    # Estética
    plt.title(f'EWS - MMAING (Município {co_ibge})')
    plt.xlabel('Tempo (semanas)')
    plt.ylabel('Atendimentos APS')
    plt.legend()
    plt.tight_layout()
    plt.show()
