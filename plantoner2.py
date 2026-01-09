import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# --- Configuração da Página ---
st.set_page_config(page_title="Escala SAMU", page_icon="🚑")


# --- Funções de Lógica (Mantidas iguais) ---
def carregar_dados():
    try:
        df_bases = pd.read_csv('BASES.csv')
        df_plantoes = pd.read_csv('PLANTOES.csv')
        return df_bases, df_plantoes
    except FileNotFoundError:
        st.error("Erro: Arquivos 'BASES.csv' e 'PLANTOES.csv' não encontrados.")
        return None, None


def obter_data_plantao(semana_index, dia_str):
    data_base = datetime(2026, 1, 5)
    offset_dias = {'Seg': 0, 'Ter': 1, 'Qua': 2, 'Qui': 3, 'Sex': 4, 'Sáb': 5, 'Dom': 6}
    dia_chave = dia_str[:3]

    if dia_chave in offset_dias:
        dias_a_somar = (semana_index * 7) + offset_dias[dia_chave]
        data_final = data_base + timedelta(days=dias_a_somar)
        return data_final
    return None


# --- Interface Visual do Streamlit ---
def main():
    # Título e Boas-vindas
    st.title("🚑 Consulta de Escala de Plantões")
    st.write("Bem-vindo ao Sistema de Gerenciamento de Escalas.")
    st.markdown("---")

    df_bases, df_plantoes = carregar_dados()
    if df_bases is None: return

    # --- Entradas do Usuário ---
    col1, col2 = st.columns(2)

    with col1:
        usuario_d = st.text_input("Digite o seu código (Ex: D1, D7):").upper().strip()

    with col2:
        oficio_input = st.selectbox(
            "Qual o seu ofício?",
            ("Medicina", "Enfermagem", "Extra")
        )

    # Botão para processar
    if st.button("Buscar Plantões"):
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
            return

        oficio_tabela = oficio_input
        locais_possiveis = ['HUSE', 'SIQUEIRA', 'UNIT', 'TELECARDIOLOGIA']

        st.subheader(f"Plantões encontrados para {usuario_d} ({oficio_tabela}):")

        encontrou_algo = False

        # Itera sobre cada semana
        for index, row in df_plantoes.iterrows():
            linha_base = df_bases.iloc[index]
            local_atual = "NÃO ALOCADO"

            for local in locais_possiveis:
                if local in df_bases.columns and linha_base[local] == oficio_tabela:
                    local_atual = local
                    break

            if local_atual == "NÃO ALOCADO":
                continue

            colunas_dias = [col for col in df_plantoes.columns if
                            'PADRÃO' in col or 'NOTURNO' in col or 'DIURNO' in col]

            for col_dia in colunas_dias:
                if row[col_dia] == usuario_d:
                    partes = col_dia.replace(')', '').split(' (')
                    dia_semana_abrev = partes[0]
                    tipo_plantao = partes[1]

                    data = obter_data_plantao(index, dia_semana_abrev)
                    data_formatada = data.strftime("%d/%m")

                    nomes_dias = {
                        'Seg': 'Segunda', 'Ter': 'Terça', 'Qua': 'Quarta',
                        'Qui': 'Quinta', 'Sex': 'Sexta', 'Sáb': 'Sábado', 'Dom': 'Domingo'
                    }
                    nome_dia_completo = nomes_dias.get(dia_semana_abrev, dia_semana_abrev)

                    # --- Lógica de Horários Modificada ---
                    horarios = {
                        'PADRÃO': '19:00 até 00:00',
                        'NOTURNO': '19:00 até 07:00',
                        'DIURNO': '07:00 até 19:00'
                    }
                    # Pega o horário correspondente ou mantém o nome original se não encontrar
                    horario_texto = horarios.get(tipo_plantao, tipo_plantao)

                    # Exibe o resultado formatado com quebra de linha
                    st.success(f"""
                    📅 **{data_formatada} ({nome_dia_completo})** - **{local_atual}** ⏰ {horario_texto}
                    """)
                    encontrou_algo = True

        if not encontrou_algo:
            st.info("Nenhum plantão encontrado para os dados informados.")


if __name__ == "__main__":
    main()
