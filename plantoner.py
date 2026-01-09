import pandas as pd
from datetime import datetime, timedelta


def carregar_dados():
    try:
        # Carrega os arquivos CSV
        # O parâmetro keep_default_na=False evita que 'NA' seja lido como NaN (caso exista algum código assim)
        df_bases = pd.read_csv('BASES.csv')
        df_plantoes = pd.read_csv('PLANTOES.csv')
        return df_bases, df_plantoes
    except FileNotFoundError:
        print(
            "Erro: Certifique-se de que os arquivos 'BASES.xlsx - BASES.csv' e 'PLANTOES.xlsx - PLANTOES.csv' estão na mesma pasta.")
        return None, None


def obter_data_plantao(semana_index, dia_str):
    # Data base: Segunda-feira, 05 de Janeiro de 2026 (Semana 1)
    data_base = datetime(2026, 1, 5)

    # Mapeamento de dias para incremento de dias (Segunda = 0, Terça = 1, etc.)
    offset_dias = {
        'Seg': 0, 'Ter': 1, 'Qua': 2, 'Qui': 3, 'Sex': 4, 'Sáb': 5, 'Dom': 6
    }

    # Encontra qual dia da semana é (ex: "Seg" de "Seg (PADRÃO)")
    dia_chave = dia_str[:3]  # Pega as 3 primeiras letras

    if dia_chave in offset_dias:
        dias_a_somar = (semana_index * 7) + offset_dias[dia_chave]
        data_final = data_base + timedelta(days=dias_a_somar)
        return data_final
    return None


def main():
    df_bases, df_plantoes = carregar_dados()
    if df_bases is None: return

    # --- Entradas do Usuário ---
    print("--- Consulta de Escala de Plantões ---")
    usuario_d = input("Digite o seu código (Ex: D1, D2... D7): ").upper().strip()

    print("Qual o seu ofício?")
    print("[MED] Medicina")
    print("[ENF] Enfermagem")
    print("[EXT] Extra")
    oficio_input = input("Digite a opção (MED, ENF ou EXT): ").upper().strip()

    # Mapeamento do input para o termo exato na tabela BASES
    mapa_oficios = {
        'MED': 'Medicina',
        'ENF': 'Enfermagem',
        'EXT': 'Extra'
    }

    if oficio_input not in mapa_oficios:
        print("Ofício inválido.")
        return

    oficio_tabela = mapa_oficios[oficio_input]
    locais_possiveis = ['HUSE', 'SIQUEIRA', 'UNIT', 'TELECARDIOLOGIA']

    print("\n--- Seus Plantões ---")

    # Itera sobre cada semana (linha) da tabela de plantões
    # Assumindo que as tabelas BASES e PLANTOES têm a mesma ordem de semanas
    for index, row in df_plantoes.iterrows():

        # 1. Descobrir onde esse ofício está lotado nesta semana específica
        linha_base = df_bases.iloc[index]
        local_atual = "NÃO ALOCADO"

        for local in locais_possiveis:
            # Verifica se a coluna existe e se o valor é igual ao ofício do usuário
            if local in df_bases.columns and linha_base[local] == oficio_tabela:
                local_atual = local
                break

        # Se não achou local (ex: Pós-Graduação que não foi selecionado), pula ou define como tal
        if local_atual == "NÃO ALOCADO":
            continue

        # 2. Verificar os plantões do usuário nesta semana (D1, D2, etc)
        # Colunas de dias no arquivo PLANTOES (ignora a primeira coluna que é 'Semana / Período')
        colunas_dias = [col for col in df_plantoes.columns if 'PADRÃO' in col or 'NOTURNO' in col or 'DIURNO' in col]

        for col_dia in colunas_dias:
            if row[col_dia] == usuario_d:
                # Extrair informações do cabeçalho. Ex: "Seg (PADRÃO)"
                partes = col_dia.replace(')', '').split(' (')
                dia_semana_abrev = partes[0]  # Seg
                tipo_plantao = partes[1]  # PADRÃO

                # Calcular Data
                data = obter_data_plantao(index, dia_semana_abrev)
                data_formatada = data.strftime("%d/%m")

                # Mapear nome completo do dia
                nomes_dias = {
                    'Seg': 'Segunda', 'Ter': 'Terça', 'Qua': 'Quarta',
                    'Qui': 'Quinta', 'Sex': 'Sexta', 'Sáb': 'Sábado', 'Dom': 'Domingo'
                }
                nome_dia_completo = nomes_dias.get(dia_semana_abrev, dia_semana_abrev)

                # Formato Solicitado: "01/01 - Sábado - PADRÃO - HUSE"
                print(f'"{data_formatada} - {nome_dia_completo} - {tipo_plantao} - {local_atual}"')


if __name__ == "__main__":
    main()