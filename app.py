import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# ==========================================================
# 1. Configuração inicial
# ==========================================================
st.set_page_config(page_title="Bem-Estar Financeiro", page_icon="💰")

st.title("💰 Autoavaliação de Bem-Estar Financeiro")
st.markdown("""
Responda às perguntas abaixo para avaliar seu **bem-estar financeiro**  
e comparar seus resultados com pessoas de **perfil semelhante**.
""")

# ==========================================================
# 2. Leitura das bases
# ==========================================================
try:
    dados = pd.read_csv("dados_tratados.csv")
    dados.columns = dados.columns.str.lower().str.strip().str.replace(" ", "_")
except:
    st.warning("⚠️ Base 'dados_tratados.csv' não encontrada. O app funcionará localmente.")
    dados = pd.DataFrame()

try:
    resumo = pd.read_csv("dados_resumo.csv")
    resumo.columns = resumo.columns.str.lower().str.strip().str.replace(" ", "_")
except:
    resumo = pd.DataFrame(columns=["idade", "genero", "renda", "score_bem_estar"])

# ==========================================================
# 3. Perfil do respondente
# ==========================================================
st.header("👤 Seu perfil")

idade = st.selectbox("Faixa etária:", [
    "18 a 28 anos", "29 a 39 anos", "40 a 50 anos", "Acima de 50"
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

    # Itens que precisam ser invertidos (crescentes)
    itens_crescentes = ["BEM_Q09", "BEM_Q11", "BEM_Q12", "BEM_Q13", "BEM_Q15", "BEM_Q16"]
    for item in itens_crescentes:
        if item in respostas_num:
            respostas_num[item] = 4 - respostas_num[item]

    score_total = sum(respostas_num.values())
    score_medio = np.mean(list(respostas_num.values()))

    st.subheader("🧮 Seu resultado")
    st.metric("Média (escala 0–4)", f"{score_medio:.2f} / 4")
    st.metric("Soma total", f"{score_total} / 40")

    # --- Comparações com médias ---
    if not resumo.empty:
        media_geral = resumo["score_bem_estar"].mean()
        media_genero = resumo[resumo["genero"] == genero]["score_bem_estar"].mean()
        media_idade = resumo[resumo["idade"] == idade]["score_bem_estar"].mean()
        media_renda = resumo[resumo["renda"] == renda]["score_bem_estar"].mean()
    else:
        media_geral = media_genero = media_idade = media_renda = np.nan

    # --- Gráficos principais ---
    st.markdown("### 📊 Comparativos gerais e por perfil")

    def grafico_comparativo(titulo, media_ref, label_ref):
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["Você"], y=[score_medio], name="Seu Score", marker_color="teal"))
        fig.add_trace(go.Bar(x=[label_ref], y=[media_ref], name="Média", marker_color="gray"))
        fig.update_layout(title=titulo, yaxis_title="Pontuação média (0–4)", barmode="group", height=400)
        st.plotly_chart(fig, use_container_width=True)

    grafico_comparativo("Comparativo Geral", media_geral, "Média Geral")
    grafico_comparativo("Por Gênero", media_genero, "Média do Gênero")
    grafico_comparativo("Por Faixa Etária", media_idade, "Média da Idade")
    grafico_comparativo("Por Renda Mensal", media_renda, "Média da Renda")

    # --- Dicas interpretativas ---
    st.markdown("### 💬 Interpretação e Dicas")

    if score_medio <= 1.5:
        nivel = "Baixo"
        dica = ("Você pode estar enfrentando dificuldades financeiras. "
                "💡 *Sugestão:* registre todas as despesas, priorize dívidas essenciais "
                "e crie uma reserva de emergência de pelo menos 5% da renda mensal.")
    elif score_medio <= 2.5:
        nivel = "Moderado"
        dica = ("Você demonstra algum controle, mas há espaço para evoluir. "
                "💡 *Sugestão:* defina metas mensais, monitore gastos e inicie investimentos simples como Tesouro Direto.")
    elif score_medio <= 3.4:
        nivel = "Bom"
        dica = ("Seu bem-estar financeiro é satisfatório. "
                "💡 *Sugestão:* mantenha o planejamento e diversifique aplicações para objetivos de médio e longo prazo.")
    else:
        nivel = "Alto"
        dica = ("Excelente equilíbrio financeiro! "
                "💡 *Sugestão:* mantenha seus hábitos e ajude outras pessoas a desenvolverem educação financeira.")

    st.info(f"**Nível de bem-estar financeiro: {nivel}**\n\n{dica}")

    # ==========================================================
    # 6. Geração de PDF
    # ==========================================================
    def gerar_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("💰 Relatório de Bem-Estar Financeiro", styles["Title"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Idade:</b> {idade}", styles["Normal"]))
        story.append(Paragraph(f"<b>Gênero:</b> {genero}", styles["Normal"]))
        story.append(Paragraph(f"<b>Renda mensal:</b> {renda}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph(f"<b>Pontuação média:</b> {score_medio:.2f} / 4", styles["Normal"]))
        story.append(Paragraph(f"<b>Nível:</b> {nivel}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("<b>Recomendações:</b>", styles["Heading3"]))
        story.append(Paragraph(dica, styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Este relatório foi gerado automaticamente pelo aplicativo de autoavaliação de bem-estar financeiro.", styles["Italic"]))

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
    # 7. Salvar nova linha
    # ==========================================================
    nova_linha = pd.DataFrame([{
        "idade": idade, "genero": genero, "renda": renda, "score_bem_estar": score_medio
    }])
    resumo = pd.concat([resumo, nova_linha], ignore_index=True)
    resumo.to_csv("dados_resumo.csv", index=False)
    st.success("✅ Seus dados foram salvos anonimamente para futuras comparações.")

## -m streamlit run app.py