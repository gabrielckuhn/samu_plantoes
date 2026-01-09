import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# --- Configuração da Página ---
st.set_page_config(page_title="Escala SAMU", page_icon="🚑")

# --- Funções de Lógica ---
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
    
    c.drawString(2 * cm, y_position + 0.5*cm, "Relação de Plantões:")
    
    for item in lista_plantoes:
        # Verifica se precisa criar nova página
        if y_position < 3 * cm:
            c.showPage()
            y_position = 28 * cm
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2 * cm, y_position, f"Continuação - {nome_completo}")
            y_position -= 1.5 * cm
            c.setFont("Helvetica", 12)

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

# --- Interface Visual do Streamlit ---
def main():
    st.title("🚑 Consulta de Escala de Plantões")
    st.write("Bem-vindo ao Sistema de Gerenciamento de Escalas.")
    st.markdown("---")

    df_bases, df_plantoes = carregar_dados()
    if df_bases is None: return

    # --- Inicialização do Session State (MEMÓRIA) ---
    if 'resultados' not in st.session_state:
        st.session_state['resultados'] = None
    if 'modo_exibicao' not in st.session_state:
        st.session_state['modo_exibicao'] = None  # pode ser 'visual' ou 'pdf'

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
    # Se clicar em Buscar: Faz a busca e define modo 'visual'
    if botao_buscar:
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
        else:
            resultados = realizar_busca(df_bases, df_plantoes, usuario_d, oficio_input)
            st.session_state['resultados'] = resultados
            st.session_state['usuario_buscado'] = usuario_d
            st.session_state['oficio_buscado'] = oficio_input
            st.session_state['modo_exibicao'] = 'visual' # Define o modo

    # Se clicar em PDF: Faz a busca (para garantir dados atualizados) e define modo 'pdf'
    if botao_pdf:
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
        else:
            resultados = realizar_busca(df_bases, df_plantoes, usuario_d, oficio_input)
            st.session_state['resultados'] = resultados
            st.session_state['usuario_buscado'] = usuario_d
            st.session_state['oficio_buscado'] = oficio_input
            st.session_state['modo_exibicao'] = 'pdf' # Define o modo

    # --- Exibição Baseada no Modo ---
    if st.session_state['resultados'] is not None and st.session_state['resultados']:
        resultados = st.session_state['resultados']
        usuario_atual = st.session_state['usuario_buscado']
        oficio_atual = st.session_state['oficio_buscado']
        modo = st.session_state['modo_exibicao']

        st.markdown("---")
        
        # MODO PDF: Mostra o formulário de download e depois a lista
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

        # MODO VISUAL: Mostra título de "Visualização Rápida" 
        # (No modo PDF também mostramos a lista abaixo, conforme pedido)
        st.subheader(f"Plantões de {usuario_atual} ({oficio_atual})")

        for item in resultados:
            st.success(f"📅 **{item['data_formatada']} ({item['dia_nome']})** - **{item['local']}**\n\n⏰ {item['horario_texto']}")

    elif st.session_state['resultados'] is not None and not st.session_state['resultados']:
        st.info("Nenhum plantão encontrado para os dados informados.")

if __name__ == "__main__":
    main()
