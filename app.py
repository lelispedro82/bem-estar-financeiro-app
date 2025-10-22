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
    dados = pd.read_excel("base_com_scores.xlsx", sheet_name=0)
    dados = dados.loc[:, ~dados.columns.duplicated()].copy()
    dados.columns = dados.columns.str.lower().str.strip().str.replace(" ", "_")

    resumo = dados.copy()
    resumo.rename(columns={
        "faixa_idade": "idade",
        "score_bem_estar_cfpb": "score_bem_estar_cfpb"
    }, inplace=True)

    if "score_bem_estar" not in resumo.columns:
        resumo["score_bem_estar"] = np.nan
    if "score_conhecimento" not in resumo.columns:
        resumo["score_conhecimento"] = np.nan

    st.success("✅ Base CFPB carregada com sucesso!")
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar 'base_com_scores.xlsx'. O app funcionará localmente.\n\nDetalhes: {e}")
    resumo = pd.DataFrame(columns=[
        "idade", "genero", "renda",
        "score_bem_estar", "score_bem_estar_cfpb", "score_conhecimento"
    ])

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
# 4. Escalas e perguntas (CFPB)
# ==========================================================
escala_1 = ["Completamente (4)", "Muito bem (3)", "Um pouco (2)", "Muito pouco (1)", "De modo nenhum (0)"]
escala_2 = ["Sempre (4)", "Frequentemente (3)", "Às vezes (2)", "Raramente (1)", "Nunca (0)"]

mapa_escala_1 = {"Completamente (4)": 4, "Muito bem (3)": 3, "Um pouco (2)": 2, "Muito pouco (1)": 1, "De modo nenhum (0)": 0}
mapa_escala_2 = {"Sempre (4)": 4, "Frequentemente (3)": 3, "Às vezes (2)": 2, "Raramente (1)": 1, "Nunca (0)": 0}

st.header("📋 Seção: Bem-Estar Financeiro (CFPB)")

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
# 4B. Seção: Conhecimento Financeiro (Questões 43–50)
# ==========================================================
st.header("🧠 Seção: Conhecimento Financeiro")

# Perguntas e alternativas (baseadas no questionário do R)
perguntas_conhecimento = {
    "Q43": {
        "texto": "43. Suponha que você tenha R$ 100,00 em uma conta poupança a uma taxa de juros composto de 10% ao ano. Depois de 5 anos, qual o valor você terá na poupança?",
        "opcoes": [
            "Exatamente R$ 150,00",
            "Mais do que R$ 150,00",
            "Menos do que R$ 150,00",
            "Não sei"
        ]
    },
    "Q44": {
        "texto": "44. Suponha que em 2027 sua renda dobrará e os preços de todos os bens também dobrarão. Em 2027, o quanto você será capaz de comprar com a sua renda?",
        "opcoes": [
            "Mais do que hoje",
            "O mesmo que hoje",
            "Menos do que hoje",
            "Não sei"
        ]
    },
    "Q45": {
        "texto": "45. Considerando-se um longo período (ex.: 10 anos), qual ativo, normalmente, oferece maior retorno?",
        "opcoes": [
            "Poupança",
            "Títulos públicos",
            "Ações",
            "Não sei"
        ]
    },
    "Q46": {
        "texto": "46. Imagine que cinco amigos recebem uma doação de R$ 1.000,00 e precisam dividir o dinheiro igualmente entre eles. Quanto cada um vai ganhar?",
        "opcoes": [
            "R$ 100,00",
            "R$ 200,00",
            "R$ 300,00",
            "Não sei"
        ]
    },
    "Q47": {
        "texto": "47. Um investimento com alta taxa de retorno terá alta taxa de risco. Essa afirmação é:",
        "opcoes": [
            "Verdadeira",
            "Falsa",
            "Não sei"
        ]
    },
    "Q48": {
        "texto": "48. Um empréstimo com duração de 15 anos normalmente exige pagamentos mensais maiores do que um empréstimo de 30 anos, mas o total de juros pagos ao final do empréstimo será menor. Essa afirmação é:",
        "opcoes": [
            "Verdadeira",
            "Falsa",
            "Não sei"
        ]
    },
    "Q49": {
        "texto": "49. Suponha que você viu o mesmo televisor em duas lojas diferentes pelo preço de R$ 1.000,00. A loja A oferece um desconto de R$ 150,00, e a loja B oferece um desconto de 10%. Qual é a melhor alternativa?",
        "opcoes": [
            "Comprar na loja A",
            "Comprar na loja B",
            "Tanto faz",
            "Não sei"
        ]
    },
    "Q50": {
        "texto": "50. Suponha que você realizou um empréstimo de R$ 10.000,00 para ser pago após um ano e o custo com os juros é R$ 600,00. A taxa de juros que você irá pagar nesse empréstimo é de:",
        "opcoes": [
            "0,6%",
            "6%",
            "60%",
            "Não sei"
        ]
    }
}

# Criação dos botões de múltipla escolha
respostas_conhecimento = {}
for cod, info in perguntas_conhecimento.items():
    respostas_conhecimento[cod] = st.radio(
        info["texto"], info["opcoes"], horizontal=False, key=cod
    )

# Função para normalizar texto e avaliar acertos
def norm_text(x):
    import re, unicodedata
    if pd.isna(x): return ""
    x = str(x).strip().lower()
    x = ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn')
    x = re.sub(r'[[:punct:]]', '', x)
    x = re.sub(r'\s+', ' ', x)
    return x

def avaliar_conhecimento(resps):
    score = 0
    corretas = {
        "Q43": "mais do que r$ 150,00",
        "Q44": "o mesmo que hoje",
        "Q45": "ações",
        "Q46": "r$ 200,00",
        "Q47": "verdadeira",
        "Q48": "verdadeira",
        "Q49": "comprar na loja a",
        "Q50": "6%"
    }
    for q, resp in resps.items():
        if norm_text(resp) == norm_text(corretas[q]):
            score += 1
    return score

# ----------------------------------------------------------
# Função auxiliar e gabarito
# ----------------------------------------------------------
def norm_text(x):
    import re, unicodedata
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    x = ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn')
    x = re.sub(r'[[:punct:]]', '', x)
    x = re.sub(r'\s+', ' ', x)
    return x

def avaliar_conhecimento(resps):
    score = 0
    corretas = {
        "Q43": lambda x: ("mais" in x and "150" in x and "exatamente" not in x),
        "Q44": lambda x: any(p in x for p in ["exatamente", "mesmo", "igual"]),
        "Q45": lambda x: "acao" in x or "acoes" in x,
        "Q46": lambda x: "200" in x,
        "Q47": lambda x: "verdade" in x,
        "Q48": lambda x: "verdade" in x,
        "Q49": lambda x: "loja a" in x,
        "Q50": lambda x: ("6" in x or "0.06" in x or "0,06" in x) and not "0,6" in x
    }
    for q, val in resps.items():
        txt = norm_text(val)
        if corretas[q](txt):
            score += 1
    return score

# ==========================================================
# 5. Cálculo e exibição de resultados
# ==========================================================
if st.button("Calcular meu resultado"):
    # ------------------------------
    # 5A. Cálculo do Bem-Estar CFPB
    # ------------------------------
    respostas_num = {}
    for cod, val in respostas.items():
        if int(cod[-2:]) <= 12:
            respostas_num[cod] = mapa_escala_1[val]
        else:
            respostas_num[cod] = mapa_escala_2[val]

    # Inversão de itens negativos
    itens_reversos = ["BEM_Q09", "BEM_Q11", "BEM_Q12", "BEM_Q13", "BEM_Q15", "BEM_Q16"]
    for item in itens_reversos:
        if item in respostas_num:
            respostas_num[item] = 4 - respostas_num[item]

    score_total = sum(respostas_num.values())
    score_medio = np.mean(list(respostas_num.values()))

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

    # ------------------------------
    # 5B. Cálculo do Conhecimento
    # ------------------------------
    score_conhecimento = avaliar_conhecimento(respostas_conhecimento)

    st.markdown("### 🧠 Resultado: Conhecimento Financeiro")
    st.metric("Score Conhecimento (0–8)", f"{score_conhecimento}")

    # Feedback textual
    if score_conhecimento <= 3:
        st.warning("Seu nível de conhecimento financeiro é **baixo**. Busque capacitação sobre juros, investimentos e inflação.")
    elif score_conhecimento <= 6:
        st.info("Seu nível de conhecimento é **moderado**. Você entende os conceitos principais, mas pode reforçar temas como juros compostos e risco.")
    else:
        st.success("Excelente! Seu nível de conhecimento é **alto**, demonstrando domínio sobre conceitos financeiros e econômicos.")

    # Comparativo de conhecimento
    if not resumo.empty and "score_conhecimento" in resumo.columns:
        media_conhecimento = resumo["score_conhecimento"].mean(skipna=True)
    else:
        media_conhecimento = np.nan

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=["Você"], y=[score_conhecimento], name="Você", marker_color="#3498DB"))
    if not np.isnan(media_conhecimento):
        fig3.add_trace(go.Bar(x=["Média Geral"], y=[media_conhecimento], name="Média", marker_color="gray"))
    fig3.update_layout(title="Comparativo do Score de Conhecimento Financeiro (0–8)", yaxis_title="Pontuação", barmode="group", height=400, template="plotly_white")
    st.plotly_chart(fig3, use_container_width=True)

    # ------------------------------
    # 5C. Bem-Estar Financeiro
    # ------------------------------
    st.subheader("🧮 Seus resultados (Bem-Estar Financeiro)")
    st.metric("Score médio (0–4)", f"{score_medio:.2f}")
    st.metric("Score total (0–40)", f"{score_total}")
    st.metric("Score CFPB (0–100)", f"{score_cfpb:.0f}")

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

    st.markdown(f"### Nível: <span style='color:{cor_nivel}'><b>{nivel}</b></span>", unsafe_allow_html=True)
    st.info(dica)

    # ------------------------------
    # 6. Gráficos comparativos
    # ------------------------------
    if not resumo.empty:
        media_score_medio = resumo["score_bem_estar"].mean(skipna=True)
        media_score_cfpb = resumo["score_bem_estar_cfpb"].mean(skipna=True)
    else:
        media_score_medio = media_score_cfpb = np.nan

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=["Você"], y=[score_medio], name="Você", marker_color=cor_nivel))
    if not np.isnan(media_score_medio):
        fig1.add_trace(go.Bar(x=["Média Geral"], y=[media_score_medio], name="Média", marker_color="gray"))
    fig1.update_layout(title="Comparativo do Score Médio (0–4)", yaxis_title="Pontuação média (0–4)", barmode="group", height=400, template="plotly_white")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=["Você"], y=[score_cfpb], name="Você", marker_color=cor_nivel))
    if not np.isnan(media_score_cfpb):
        fig2.add_trace(go.Bar(x=["Média Geral"], y=[media_score_cfpb], name="Média", marker_color="gray"))
    fig2.update_layout(title="Comparativo do Score CFPB (0–100)", yaxis_title="Pontuação CFPB (0–100)", barmode="group", height=400, template="plotly_white")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)

    # ------------------------------
    # 7. PDF
    # ------------------------------
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
        story.append(Paragraph(f"<b>Score Conhecimento (0–8):</b> {score_conhecimento}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Nível CFPB:</b> {nivel}", styles["Normal"]))
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

    # ------------------------------
    # 8. Salvamento anônimo
    # ------------------------------
    nova_linha = pd.DataFrame([{
        "idade": idade,
        "genero": genero,
        "renda": renda,
        "score_bem_estar": score_medio,
        "score_bem_estar_cfpb": score_cfpb,
        "score_conhecimento": score_conhecimento
    }])

    try:
        resumo = pd.concat([resumo, nova_linha], ignore_index=True)
        resumo.to_csv("dados_resumo.csv", index=False)
        st.success("✅ Seus dados foram salvos anonimamente para futuras comparações.")
    except Exception as e:
        st.error(f"❌ Erro ao salvar dados: {e}")

