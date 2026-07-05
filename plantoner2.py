import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# --- Configuração da Página ---
st.set_page_config(page_title="Plantões da 40ª Geração", page_icon="🚑", layout="wide")

# --- Funções de Lógica (sem alterações) ---
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

def gerar_pdf_plantoes(nome_completo, codigo_usuario, oficio_usuario, lista_plantoes):
    """Gera um arquivo PDF em memória com os plantões listados."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Cabeçalho
    c.setFont("Helvetica-Bold", 14)
    titulo = f"{nome_completo} - {codigo_usuario} {oficio_usuario}"
    c.drawString(2 * cm, 28 * cm, titulo)

    # Linha divisória
    c.setLineWidth(1)
    c.line(2 * cm, 27.5 * cm, 19 * cm, 27.5 * cm)

    # Corpo (Lista de Plantões)
    y_position = 26 * cm
    c.setFont("Helvetica", 12)

    c.drawString(2 * cm, y_position + 0.5 * cm, "Relação de Plantões:")

    for idx, item in enumerate(lista_plantoes, start=1):
        # Verifica se precisa criar nova página
        if y_position < 3 * cm:
            c.showPage()
            y_position = 28 * cm
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2 * cm, y_position, f"Continuação - {nome_completo}")
            y_position -= 1.5 * cm
            c.setFont("Helvetica", 12)

        # Numeração do plantão (pequena alteração pedida)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2 * cm, y_position, f"Plantão {idx}")
        y_position -= 0.45 * cm

        # Dados do item
        texto_linha1 = f"{item['data_formatada']} ({item['dia_nome']}) - {item['local']}"
        texto_linha2 = f"Horário: {item['horario_texto']}"

        # Escreve Linha 1 (Data e Local) em Negrito
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2.5 * cm, y_position, texto_linha1)

        # Escreve Linha 2 (Horário) normal
        y_position -= 0.5 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2.5 * cm, y_position, texto_linha2)

        # Espaçamento para o próximo item
        y_position -= 1.0 * cm

    c.save()
    buffer.seek(0)
    return buffer

def realizar_busca(df_bases, df_plantoes, usuario_d, oficio_tabela):
    """Função auxiliar para processar a busca e retornar a lista."""
    locais_possiveis = ['HUSE', 'SIQUEIRA', 'UNIT', 'TELECARDIOLOGIA']
    temp_resultados = []

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

                horarios = {
                    'PADRÃO': '19:00 até 00:00',
                    'NOTURNO': '19:00 até 07:00',
                    'DIURNO': '07:00 até 19:00'
                }
                horario_texto = horarios.get(tipo_plantao, tipo_plantao)

                temp_resultados.append({
                    "data_formatada": data_formatada,
                    "dia_nome": nome_dia_completo,
                    "local": local_atual,
                    "horario_texto": horario_texto
                })
    return temp_resultados

# --- Tema (claro/escuro) e Estilização ---
def aplicar_estilo(tema: str):
    if tema == "dark":
        bg = "#0f172a"
        bg_card = "#16213a"
        bg_input = "#1c2b4a"
        texto = "#e8edf5"
        texto_sec = "#93a3bd"
        borda = "#2b3b58"
        accent = "#38bdf8"
        accent2 = "#34d399"
        sombra = "rgba(0,0,0,0.45)"
    else:
        bg = "#f4f7fb"
        bg_card = "#ffffff"
        bg_input = "#ffffff"
        texto = "#0f1b2d"
        texto_sec = "#5c6b82"
        borda = "#e3e9f2"
        accent = "#0ea5e9"
        accent2 = "#16a34a"
        sombra = "rgba(15,27,45,0.08)"

    st.markdown(f"""
    <style>
        .stApp {{
            background: {bg};
            color: {texto};
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        .bloco-central {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .topo-flex {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .titulo-principal {{
            font-size: 2.1rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, {accent}, {accent2});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitulo-boas-vindas {{
            color: {texto_sec};
            font-size: 1.05rem;
            margin-top: 0.2rem;
            margin-bottom: 1.6rem;
        }}

        div[data-testid="stTextInput"] input,
        div[data-baseweb="select"] > div {{
            background-color: {bg_input} !important;
            color: {texto} !important;
            border-radius: 12px !important;
            border: 1px solid {borda} !important;
        }}

        label, .stMarkdown p {{
            color: {texto} !important;
        }}

        div[data-testid="stButton"] button {{
            border-radius: 12px;
            border: 1px solid {borda};
            padding: 0.6rem 1rem;
            font-weight: 600;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
            background: {bg_card};
            color: {texto};
        }}
        div[data-testid="stButton"] button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px {sombra};
            border-color: {accent};
            color: {accent};
        }}

        div[data-testid="stDownloadButton"] button {{
            border-radius: 12px;
            font-weight: 700;
            background: linear-gradient(90deg, {accent}, {accent2});
            color: white;
            border: none;
        }}
        div[data-testid="stDownloadButton"] button:hover {{
            filter: brightness(1.08);
        }}

        .grade-plantoes {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 0.9rem;
            margin-top: 1rem;
        }}

        .cartao-plantao {{
            background: {bg_card};
            border: 1px solid {borda};
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 2px 10px {sombra};
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .cartao-plantao:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 22px {sombra};
        }}

        .rotulo-plantao {{
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: white;
            background: linear-gradient(90deg, {accent}, {accent2});
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            margin-bottom: 0.55rem;
        }}

        .linha-data {{
            font-weight: 700;
            font-size: 1.02rem;
            color: {texto};
            margin-bottom: 0.25rem;
        }}

        .linha-horario {{
            color: {texto_sec};
            font-size: 0.92rem;
        }}

        @media (max-width: 640px) {{
            .titulo-principal {{ font-size: 1.55rem; }}
            .grade-plantoes {{ grid-template-columns: 1fr; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def renderizar_cartoes(resultados):
    html = ['<div class="grade-plantoes">']
    for idx, item in enumerate(resultados, start=1):
        html.append(f"""
        <div class="cartao-plantao">
            <span class="rotulo-plantao">Plantão {idx}</span>
            <div class="linha-data">📅 {item['data_formatada']} ({item['dia_nome']}) - {item['local']}</div>
            <div class="linha-horario">⏰ {item['horario_texto']}</div>
        </div>
        """)
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


# --- Interface Visual do Streamlit ---
def main():
    if 'tema' not in st.session_state:
        st.session_state['tema'] = 'light'
    if 'resultados' not in st.session_state:
        st.session_state['resultados'] = None
    if 'modo_exibicao' not in st.session_state:
        st.session_state['modo_exibicao'] = None

    aplicar_estilo(st.session_state['tema'])

    st.markdown('<div class="bloco-central">', unsafe_allow_html=True)

    col_titulo, col_switch = st.columns([4, 1])
    with col_titulo:
        st.markdown('<p class="titulo-principal">🚑 Plantões da 40ª Geração</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo-boas-vindas">Bem-vindos bananinhas da 40!</p>', unsafe_allow_html=True)
    with col_switch:
        modo_escuro = st.toggle("🌙 Escuro", value=(st.session_state['tema'] == 'dark'))
        novo_tema = 'dark' if modo_escuro else 'light'
        if novo_tema != st.session_state['tema']:
            st.session_state['tema'] = novo_tema
            st.rerun()

    df_bases, df_plantoes = carregar_dados()
    if df_bases is None:
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # --- Entradas do Usuário ---
    col1, col2 = st.columns(2)

    with col1:
        usuario_d = st.text_input("Digite o seu código (Ex: D1, D7):").upper().strip()

    with col2:
        oficio_input = st.selectbox(
            "Qual o seu ofício?",
            ("Medicina", "Enfermagem", "Extra")
        )

    # --- Botões de Ação (Lado a Lado) ---
    col_btn1, col_btn2 = st.columns(2)

    botao_buscar = col_btn1.button("🔎 Buscar Plantões", use_container_width=True)
    botao_pdf = col_btn2.button("📄 Baixar Plantões em PDF", use_container_width=True)

    # --- Lógica dos Botões ---
    if botao_buscar:
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
        else:
            resultados = realizar_busca(df_bases, df_plantoes, usuario_d, oficio_input)
            st.session_state['resultados'] = resultados
            st.session_state['usuario_buscado'] = usuario_d
            st.session_state['oficio_buscado'] = oficio_input
            st.session_state['modo_exibicao'] = 'visual'

    if botao_pdf:
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
        else:
            resultados = realizar_busca(df_bases, df_plantoes, usuario_d, oficio_input)
            st.session_state['resultados'] = resultados
            st.session_state['usuario_buscado'] = usuario_d
            st.session_state['oficio_buscado'] = oficio_input
            st.session_state['modo_exibicao'] = 'pdf'

    # --- Exibição Baseada no Modo ---
    if st.session_state['resultados'] is not None and st.session_state['resultados']:
        resultados = st.session_state['resultados']
        usuario_atual = st.session_state['usuario_buscado']
        oficio_atual = st.session_state['oficio_buscado']
        modo = st.session_state['modo_exibicao']

        st.markdown("---")

        if modo == 'pdf':
            st.info("Preencha seu nome abaixo para gerar o arquivo.")
            col_pdf_1, col_pdf_2 = st.columns([2, 1])

            with col_pdf_1:
                nome_completo = st.text_input("Nome Completo:", placeholder="Ex: Maria da Silva")

            with col_pdf_2:
                st.write("")
                st.write("")
                if nome_completo:
                    pdf_buffer = gerar_pdf_plantoes(nome_completo, usuario_atual, oficio_atual, resultados)
                    st.download_button(
                        label="📥 Download Agora",
                        data=pdf_buffer,
                        file_name=f"escala_{usuario_atual}_{nome_completo.split()[0]}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )

        st.subheader(f"Plantões de {usuario_atual} ({oficio_atual})")
        renderizar_cartoes(resultados)

    elif st.session_state['resultados'] is not None and not st.session_state['resultados']:
        st.info("Nenhum plantão encontrado para os dados informados.")

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
