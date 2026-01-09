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
    if 'usuario_buscado' not in st.session_state:
        st.session_state['usuario_buscado'] = ""
    if 'oficio_buscado' not in st.session_state:
        st.session_state['oficio_buscado'] = ""

    # --- Entradas do Usuário ---
    col1, col2 = st.columns(2)

    with col1:
        usuario_d = st.text_input("Digite o seu código (Ex: D1, D7):").upper().strip()

    with col2:
        oficio_input = st.selectbox(
            "Qual o seu ofício?",
            ("Medicina", "Enfermagem", "Extra")
        )

    # --- Botão de Buscar (Processa e Salva na Memória) ---
    if st.button("Buscar Plantões"):
        if not usuario_d:
            st.warning("Por favor, digite o seu código (Ex: D1).")
            return

        oficio_tabela = oficio_input
        locais_possiveis = ['HUSE', 'SIQUEIRA', 'UNIT', 'TELECARDIOLOGIA']
        
        temp_resultados = []

        # Lógica de Busca
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
        
        # SALVA TUDO NA MEMÓRIA DO STREAMLIT
        st.session_state['resultados'] = temp_resultados
        st.session_state['usuario_buscado'] = usuario_d
        st.session_state['oficio_buscado'] = oficio_tabela

    # --- Exibição (Lê da Memória) ---
    # Essa parte roda mesmo que a página recarregue ao digitar o nome
    if st.session_state['resultados'] is not None:
        resultados = st.session_state['resultados']
        usuario_atual = st.session_state['usuario_buscado']
        oficio_atual = st.session_state['oficio_buscado']

        if resultados:
            st.success(f"Foram encontrados {len(resultados)} plantões para **{usuario_atual}**.")
            
            # --- Área de Download do PDF ---
            with st.container():
                st.markdown("### 📄 Baixar Relatório em PDF")
                col_pdf_1, col_pdf_2 = st.columns([2, 1])
                
                with col_pdf_1:
                    nome_completo = st.text_input("Digite seu nome para o PDF:", placeholder="Ex: Maria da Silva")
                
                with col_pdf_2:
                    st.write("") 
                    st.write("") 
                    if nome_completo:
                        pdf_buffer = gerar_pdf_plantoes(nome_completo, usuario_atual, oficio_atual, resultados)
                        st.download_button(
                            label="📥 Baixar PDF",
                            data=pdf_buffer,
                            file_name=f"escala_{usuario_atual}_{nome_completo.split()[0]}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.info("Digite o nome antes do download.")
            
            st.markdown("---")
            st.subheader("Visualização Rápida:")

            for item in resultados:
                st.success(f"📅 **{item['data_formatada']} ({item['dia_nome']})** - **{item['local']}**\n\n⏰ {item['horario_texto']}")
        
        else:
            st.info("Nenhum plantão encontrado para os dados informados.")

if __name__ == "__main__":
    main()
