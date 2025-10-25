import matplotlib.pyplot as plt

def plot_ews(df_mun, co_ibge):


    df = df_mun.sort_values(['ano', 'epiweek']).reset_index(drop=True)

    # coluna continua no eixo X
    df['semanas'] = range(1, len(df) + 1)

    # coluna texto (Ano-Semana)
    df['tempo'] = df['ano'].astype(str) + '-S' + df['epiweek'].astype(str)

    # --- Plot ---
    plt.figure(figsize=(18, 6))

    plt.plot(df['semanas'], df['atend_ivas'], label='Série temporal', linewidth=1.8)
    plt.plot(df['semanas'], df['upperbound'], label='Limite (upperbound)', linestyle='--', color='orange', linewidth=2)

    # Alertas em vermelho
    alertas = df[df['EWS_MMAING'] == 'Sim']
    plt.scatter(alertas['semanas'], alertas['atend_ivas'], color='red', label='Alerta (EWS)', s=60)

    # Eixo X com menos rótulos e rotacionado
    step = max(1, len(df) // 30)
    x_ticks = df['semanas'][::step]
    x_labels = df['tempo'][::step]
    plt.xticks(x_ticks, x_labels, rotation=90, fontsize=12)

    # Estética
    plt.title(f'EWS - MMAING (Município {co_ibge})', fontsize=18)
    plt.xlabel('Ano - Semana Epidemiológica', fontsize=14)
    plt.ylabel('Atendimentos APS', fontsize=14)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()
