import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# ==========================================================
# 1. Configuração inicial
# ==========================================================
st.set_page_config(page_title="Bem-Estar Financeiro (CFPB)", page_icon="💰")

st.title("💰 Autoavaliação de Bem-Estar Financeiro (CFPB)")
st.markdown("""
Responda às perguntas abaixo para avaliar seu **bem-estar financeiro**  
e comparar seus resultados com a **média geral dos respondentes**.
""")

# ==========================================================
# 2. Leitura da base de referência (exportada do R)
# ==========================================================
try:
    dados = pd.read_excel("base_com_scores.xlsx", sheet_name="respostas_com_scores")
    dados = dados.loc[:, ~dados.columns.duplicated()].copy()
    dados.columns = dados.columns.str.lower().str.strip().str.replace(" ", "_")

    resumo = dados.copy()
    resumo.rename(columns={
        "faixa_idade": "idade",
        "score_bem_estar_cfpb": "score_bem_estar_cfpb"
    }, inplace=True)

    if "score_bem_estar" not in resumo.columns:
        resumo["score_bem_estar"] = np.nan

    st.success("✅ Base CFPB carregada com sucesso!")
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar 'base_com_scores.xlsx'. O app funcionará localmente.\n\nDetalhes: {e}")
    resumo = pd.DataFrame(columns=["idade", "genero", "renda", "score_bem_estar", "score_bem_estar_cfpb"])

# ==========================================================
# 3. Perfil do respondente
# ==========================================================
st.header("👤 Seu perfil")

idade = st.selectbox("Faixa etária:", [
    "18 a 28 anos", "29 a 39 anos", "40 a 50 anos", "61 ou mais"
])
genero = st.selectbox("Gênero:", ["Masculino", "Feminino", "Prefiro não responder"])
renda = st.selectbox("Renda mensal:", [
    "Até 2 salários mínimos",
    "De 2 a 5 salários mínimos",
    "De 5 a 10 salários mínimos",
    "Mais de 10 salários mínimos"
])

# ==========================================================
# 4. Escalas e perguntas
# ==========================================================
escala_1 = ["Completamente (4)", "Muito bem (3)", "Um pouco (2)", "Muito pouco (1)", "De modo nenhum (0)"]
escala_2 = ["Sempre (4)", "Frequentemente (3)", "Às vezes (2)", "Raramente (1)", "Nunca (0)"]

mapa_escala_1 = {"Completamente (4)": 4, "Muito bem (3)": 3, "Um pouco (2)": 2, "Muito pouco (1)": 1, "De modo nenhum (0)": 0}
mapa_escala_2 = {"Sempre (4)": 4, "Frequentemente (3)": 3, "Às vezes (2)": 2, "Raramente (1)": 1, "Nunca (0)": 0}

st.header("📋 Seção: Bem-Estar Financeiro")

perguntas = {
    "BEM_Q07": "07. Você poderia lidar com uma grande despesa inesperada.",
    "BEM_Q08": "08. Você está garantindo seu futuro financeiro.",
    "BEM_Q09": "09. Por causa da sua situação financeira, você sente que nunca terá as coisas que quer na vida.",
    "BEM_Q10": "10. Você pode aproveitar a vida devido à maneira como está administrando seu dinheiro.",
    "BEM_Q11": "11. Você está apenas sobrevivendo financeiramente.",
    "BEM_Q12": "12. Você está preocupado(a) que o dinheiro que tem ou terá economizado pode não ser suficiente.",
    "BEM_Q13": "13. Dar um presente de casamento, aniversário ou outra ocasião colocaria em dificuldade suas finanças do mês.",
    "BEM_Q14": "14. Você tem dinheiro sobrando no final do mês.",
    "BEM_Q15": "15. Você NÃO está em dia com as suas finanças.",
    "BEM_Q16": "16. Suas finanças controlam sua vida."
}

respostas = {}
for cod, texto in perguntas.items():
    if int(cod[-2:]) <= 12:
        respostas[cod] = st.radio(texto, escala_1, horizontal=True, index=2, key=cod)
    else:
        respostas[cod] = st.radio(texto, escala_2, horizontal=True, index=2, key=cod)

# ==========================================================
# 5. Cálculo e exibição de resultados
# ==========================================================
if st.button("Calcular meu resultado"):
    respostas_num = {}
    for cod, val in respostas.items():
        if int(cod[-2:]) <= 12:
            respostas_num[cod] = mapa_escala_1[val]
        else:
            respostas_num[cod] = mapa_escala_2[val]

    # Itens negativos (devem ser invertidos)
    itens_reversos = ["BEM_Q09", "BEM_Q11", "BEM_Q12", "BEM_Q13", "BEM_Q15", "BEM_Q16"]
    for item in itens_reversos:
        if item in respostas_num:
            respostas_num[item] = 4 - respostas_num[item]

    score_total = sum(respostas_num.values())
    score_medio = np.mean(list(respostas_num.values()))

    # --- Conversão CFPB (oficial 0–100) ---
    conv_tab = pd.DataFrame({
        "total": range(0, 41),
        "self_18_61": [
            14,19,22,25,27,29,31,32,34,35,
            37,38,40,41,42,44,45,46,47,49,
            50,51,52,54,55,56,58,59,60,62,
            63,65,66,68,69,71,73,75,78,81,86
        ],
        "self_62plus": [
            14,20,24,26,29,31,33,35,36,38,
            39,41,42,44,45,46,48,49,50,52,
            53,54,56,57,58,60,61,63,64,66,
            67,69,71,73,75,77,79,82,84,88,95
        ]
    })
    idade_grupo = "18-61" if "61" not in idade else "61+"
    col_ref = "self_18_61" if idade_grupo == "18-61" else "self_62plus"
    score_cfpb = np.interp(score_total, conv_tab["total"], conv_tab[col_ref])

    # --- Classificação ---
    if score_cfpb < 37:
        nivel = "Baixo"
        cor_nivel = "#E74C3C"
        dica = "⚠️ Seu bem-estar financeiro está baixo. Revise gastos e tente formar uma reserva de emergência."
    elif score_cfpb < 57:
        nivel = "Moderado"
        cor_nivel = "#F1C40F"
        dica = "🟡 Seu bem-estar é moderado. Busque equilibrar consumo e poupança mensalmente."
    else:
        nivel = "Alto"
        cor_nivel = "#2ECC71"
        dica = "🟢 Seu bem-estar financeiro é alto! Continue mantendo bons hábitos e planejamento."

    # ==========================================================
    # 6. Exibição e gráficos
    # ==========================================================
    st.subheader("🧮 Seus resultados")
    st.metric("Score médio (0–4)", f"{score_medio:.2f}")
    st.metric("Score total (0–40)", f"{score_total}")
    st.metric("Score CFPB (0–100)", f"{score_cfpb:.0f}")
    st.markdown(f"### Nível: <span style='color:{cor_nivel}'><b>{nivel}</b></span>", unsafe_allow_html=True)
    st.info(dica)

    st.markdown("### 📊 Comparativos gerais")

    if not resumo.empty:
        media_score_medio = resumo["score_bem_estar"].mean(skipna=True)
        media_score_cfpb = resumo["score_bem_estar_cfpb"].mean(skipna=True)
    else:
        media_score_medio = media_score_cfpb = np.nan

    # Gráfico 1 - Score médio
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=["Você"], y=[score_medio], name="Você", marker_color=cor_nivel))
    if not np.isnan(media_score_medio):
        fig1.add_trace(go.Bar(x=["Média Geral"], y=[media_score_medio], name="Média", marker_color="gray"))
    fig1.update_layout(
        title="Comparativo do Score Médio (0–4)",
        yaxis_title="Pontuação média (0–4)",
        barmode="group",
        height=400,
        template="plotly_white"
    )

    # Gráfico 2 - Score CFPB
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=["Você"], y=[score_cfpb], name="Você", marker_color=cor_nivel))
    if not np.isnan(media_score_cfpb):
        fig2.add_trace(go.Bar(x=["Média Geral"], y=[media_score_cfpb], name="Média", marker_color="gray"))
    fig2.update_layout(
        title="Comparativo do Score CFPB (0–100)",
        yaxis_title="Pontuação CFPB (0–100)",
        barmode="group",
        height=400,
        template="plotly_white"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)

    # ==========================================================
    # 7. PDF
    # ==========================================================
    def gerar_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("💰 Relatório de Bem-Estar Financeiro (CFPB)", styles["Title"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Faixa etária:</b> {idade}", styles["Normal"]))
        story.append(Paragraph(f"<b>Gênero:</b> {genero}", styles["Normal"]))
        story.append(Paragraph(f"<b>Renda:</b> {renda}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph(f"<b>Score médio (0–4):</b> {score_medio:.2f}", styles["Normal"]))
        story.append(Paragraph(f"<b>Score CFPB (0–100):</b> {score_cfpb:.0f}", styles["Normal"]))
        story.append(Paragraph(f"<b>Nível:</b> {nivel}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>Recomendações:</b>", styles["Heading3"]))
        story.append(Paragraph(dica, styles["Normal"]))
        doc.build(story)
        buffer.seek(0)
        return buffer

    pdf_file = gerar_pdf()
    st.download_button(
        label="📄 Baixar Relatório em PDF",
        data=pdf_file,
        file_name="relatorio_bem_estar_financeiro.pdf",
        mime="application/pdf"
    )

    # ==========================================================
    # 8. Salvamento anônimo
    # ==========================================================
    nova_linha = pd.DataFrame([{
        "idade": idade,
        "genero": genero,
        "renda": renda,
        "score_bem_estar": score_medio,
        "score_bem_estar_cfpb": score_cfpb
    }])

    try:
        resumo = resumo.loc[:, ~resumo.columns.duplicated()].copy()
        resumo.reset_index(drop=True, inplace=True)
        resumo = pd.concat([resumo, nova_linha], ignore_index=True)
        resumo.to_csv("dados_resumo.csv", index=False)
        st.success("✅ Seus dados foram salvos anonimamente para futuras comparações.")
    except Exception as e:
        st.error(f"❌ Erro ao salvar dados: {e}")
