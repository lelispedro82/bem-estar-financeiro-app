import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import re, unicodedata

# ==========================================================
# 1. Configuração inicial
# ==========================================================
st.set_page_config(page_title="Alfabetização, Vieses e Bem-Estar Financeiro", page_icon="💰")

st.title("💰 Autoavaliação de Alfabetização Financeira, Vieses e Bem-Estar (CFPB)")
st.markdown("""
Responda às seções abaixo. **Todos os scores são somas simples** dos itens.
- **Alfabetização Financeira** = **Comportamento** + **Atitude** + **Conhecimento**  
- **Vieses** exibidos **separadamente**: **Autocontrole** e **Contabilidade mental**  
- **Bem-Estar (CFPB)** convertido para **0–100** a partir da soma (0–40)  
""")

# ==========================================================
# 2. Leitura da base de referência (opcional)
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

    for col in [
        "score_bem_estar", "score_bem_estar_cfpb", "score_conhecimento",
        "score_comport_total", "score_atitude_total",
        "score_autocontrole_total", "score_contab_total",
        "score_alfabetizacao_total"
    ]:
        if col not in resumo.columns:
            resumo[col] = np.nan

    st.success("✅ Base de referência carregada com sucesso!")
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar 'base_com_scores.xlsx'. O app funcionará localmente.\n\nDetalhes: {e}")
    resumo = pd.DataFrame(columns=[
        "idade", "genero", "renda",
        "score_bem_estar", "score_bem_estar_cfpb", "score_conhecimento",
        "score_comport_total", "score_atitude_total",
        "score_autocontrole_total", "score_contab_total",
        "score_alfabetizacao_total"
    ])

# ==========================================================
# 3. Seção inicial qualitativa + Perfil
# ==========================================================
st.header("📊 Seção Inicial — Autoavaliação")

q_ini1 = st.radio(
    "Você se considera capaz de entender informações sobre produtos financeiros, como empréstimos ou investimentos?",
    ["Sim", "Não", "Tenho dúvidas"], horizontal=True
)
q_ini2 = st.radio(
    "Com que frequência você busca informações ou tira dúvidas sobre finanças pessoais?",
    ["Sempre", "Frequentemente", "Às vezes", "Raramente", "Nunca"], horizontal=True
)
q_ini3 = st.text_area(
    "Que tipo de orientação financeira você gostaria de receber da cooperativa?",
    placeholder="Descreva livremente..."
)

st.header("👤 Seu perfil")
idade = st.selectbox("1. Qual é a sua idade (faixa etária) ?", [
    "18 a 28 anos", "29 a 39 anos", "40 a 50 anos", "61 ou mais"
])
genero = st.selectbox("2. Indique o gênero (sexo) no qual você se identifica:", ["Masculino", "Feminino", "Prefiro não responder"])
estado_civil = st.selectbox("3. Qual é o seu estado civil?", ["Solteiro(a)", "Casado(a)/União estável", "Divorciado(a)", "Viúvo(a)", "Prefiro não responder"])
dependentes = st.selectbox("4. Possui dependentes?", ["Não", "Sim, 1", "Sim, 2", "Sim, 3 ou mais", "Prefiro não responder"])
escolaridade = st.selectbox("5. Qual é o seu nível de escolaridade?", [
    "Fundamental", "Médio", "Superior", "Pós-graduação", "Prefiro não responder"
])
renda = st.selectbox("6.  Qual é a sua renda mensal individual, considerando todos os seus trabalhos e outras fontes de rendimento?", [
    "Até 2 salários mínimos",
    "De 2 a 5 salários mínimos",
    "De 5 a 10 salários mínimos",
    "Mais de 10 salários mínimos",
    "Prefiro não responder"
])

# ==========================================================
# 4. Escalas (Likert)
# ==========================================================
escala_concord = [
    "Concordo totalmente (4)",
    "Concordo (3)",
    "Nem concordo nem discordo (2)",
    "Discordo (1)",
    "Discordo totalmente (0)"
]
mapa_concord = {
    "Concordo totalmente (4)": 4,
    "Concordo (3)": 3,
    "Nem concordo nem discordo (2)": 2,
    "Discordo (1)": 1,
    "Discordo totalmente (0)": 0
}

escala_freq = ["Sempre (4)", "Quase sempre (3)", "Às vezes (2)", "Raramente (1)", "Nunca (0)"]
mapa_freq = {
    "Sempre (4)": 4,
    "Quase sempre (3)": 3,
    "Às vezes (2)": 2,
    "Raramente (1)": 1,
    "Nunca (0)": 0
}

escala_1 = ["Completamente (4)", "Muito bem (3)", "Um pouco (2)", "Muito pouco (1)", "De modo nenhum (0)"]
escala_2 = ["Sempre (4)", "Frequentemente (3)", "Às vezes (2)", "Raramente (1)", "Nunca (0)"]
mapa_escala_1 = {"Completamente (4)": 4, "Muito bem (3)": 3, "Um pouco (2)": 2, "Muito pouco (1)": 1, "De modo nenhum (0)": 0}
mapa_escala_2 = {"Sempre (4)": 4, "Frequentemente (3)": 3, "Às vezes (2)": 2, "Raramente (1)": 1, "Nunca (0)": 0}

# ==========================================================
# 5. Formulário — Bem-estar (CFPB) Q07–Q16 (textos originais)
# ==========================================================
st.header("📋 Seção: Bem-Estar Financeiro (CFPB) — Q07–Q16")
perguntas_bem = {
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
respostas_bem = {}
for cod, texto in perguntas_bem.items():
    if int(cod[-2:]) <= 12:
        respostas_bem[cod] = st.radio(texto, escala_1, horizontal=True, index=2, key=cod)
    else:
        respostas_bem[cod] = st.radio(texto, escala_2, horizontal=True, index=2, key=cod)

# ==========================================================
# 6. Formulário — Autocontrole (Q17–Q20) (textos originais)
# ==========================================================
st.header("🧭 Seção: Autocontrole (Q17–Q20)")
perguntas_vies = {
    "VIE_Q17": "17. Considero cuidadosamente as consequências das minhas decisões de compras antes de gastar.",
    "VIE_Q18": "18. Consigo seguir metas financeiras em longo prazo.",
    "VIE_Q19": "19. Consigo resistir a tentações para alcançar meus objetivos orçamentários.",
    "VIE_Q20": "20. Eu sei quando “dizer chega” em relação aos meus gastos."
}
respostas_vies = {}
for cod, texto in perguntas_vies.items():
    respostas_vies[cod] = st.radio(texto, escala_concord, horizontal=True, index=2, key=cod)

# ==========================================================
# 7. Formulário — Contabilidade mental (Q21–Q25) (textos originais)
# ==========================================================
st.header("💡 Seção: Contabilidade mental (Q21–Q25)")
perguntas_contab = {
    "CON_Q21": "21.  É importante para mim acompanhar minhas movimentações financeiras com precisão.",
    "CON_Q22": "22.  Eu costumo registrar meus ganhos e despesas, seja anotando em caderno, planilha, aplicativo ou de qualquer outra forma.",
    "CON_Q23": "23. Eu saberia dizer, pelo menos aproximadamente, quanto gastei neste mês.",
    "CON_Q24": "24.  Eu separo meus gastos em diferentes categorias (como, por exemplo, alimentação, lazer, educação etc.).",
    "CON_Q25": "25.  De modo geral, sou uma pessoa bem-organizada com relação ao meu dinheiro."
}
respostas_contab = {}
for cod, texto in perguntas_contab.items():
    respostas_contab[cod] = st.radio(texto, escala_concord, horizontal=True, index=2, key=cod)

# ==========================================================
# 8. Formulário — Comportamento financeiro (Q26–Q34) (textos originais)
# ==========================================================
st.header("📈 Seção: Comportamento financeiro (Q26–Q34)")
perguntas_comport = {
    "COM_Q26": "26. Você anota e controla os seus gastos pessoais (ex.: planilha de receitas e despesas mensais).",
    "COM_Q27": "27. Você compara preços ao fazer uma compra.",
    "COM_Q28": "28. Você tem um plano de gastos/orçamento.",
    "COM_Q29": "29. Você paga suas contas em dia.",
    "COM_Q30": "30. Você analisa suas contas antes de fazer uma compra de alto valor.",
    "COM_Q31": "31. Você passa a poupar mais quando recebe um aumento de salário.",
    "COM_Q32": "32. Você faz uma reserva do dinheiro que recebe mensalmente para uma necessidade futura.",
    "COM_Q33": "33. Você guarda parte da sua renda todo o mês.",
    "COM_Q34": "34. Você guarda dinheiro regularmente para atingir objetivos financeiros de longo prazo como, por exemplo, educação dos seus filhos, aquisição de uma casa, aposentadoria."
}
respostas_comport = {}
for cod, texto in perguntas_comport.items():
    respostas_comport[cod] = st.radio(texto, escala_freq, horizontal=True, index=2, key=cod)

# ==========================================================
# 9. Formulário — Atitude financeira (Q35–Q42) (textos originais)
# ==========================================================
st.header("🎯 Seção: Atitude financeira (Q35–Q42)")
perguntas_ati = {
    "ATI_Q35": "35. Para você é importante definir metas para o futuro.",
    "ATI_Q36": "36. Você acredita que a maneira como administra o seu dinheiro vai afetar o seu futuro.",
    "ATI_Q37": "37. Você não se preocupa com o futuro, vive apenas o presente.",
    "ATI_Q38": "38. Poupar é impossível para mim.",
    "ATI_Q39": "39. Depois de tomar uma decisão sobre dinheiro, você se preocupa muito com a sua decisão.",
    "ATI_Q40": "40.  É difícil para mim construir um planejamento de gastos.",
    "ATI_Q41": "41. Você considera mais satisfatório gastar dinheiro do que poupar para o futuro.",
    "ATI_Q42": "42. Para você o dinheiro é feito para gastar."
}
respostas_ati = {}
for cod, texto in perguntas_ati.items():
    respostas_ati[cod] = st.radio(texto, escala_concord, horizontal=True, index=2, key=cod)

# ==========================================================
# 10. Formulário — Conhecimento financeiro (Q43–Q50) (textos originais)
# ==========================================================
st.header("🧠 Seção: Conhecimento Financeiro (Q43–Q50)")
perguntas_conhecimento = {
    "Q43": {
        "texto": "43. Suponha que você tenha R$ 100,00 em uma conta poupança a uma taxa de juros composto de 10% ao ano. Depois de 5 anos, qual o valor você terá na poupança? Considere que não tenha sido depositado nem retirado dinheiro.",
        "opcoes": ["Exatamente R$ 150,00", "Mais do que R$ 150,00", "Menos do que R$ 150,00", "Não sei"]
    },
    "Q44": {
        "texto": "44. Suponha que em 2027 sua renda dobrará e os preços de todos os bens também dobrarão. Em 2027, o quanto você será capaz de comprar com a sua renda?",
        "opcoes": ["Mais do que hoje", "O mesmo que hoje", "Menos do que hoje", "Não sei"]
    },
    "Q45": {
        "texto": "45.Considerando-se um longo período (ex.: 10 anos), qual ativo, normalmente, oferece maior retorno?",
        "opcoes": ["Poupança", "Títulos públicos", "Ações", "Não sei"]
    },
    "Q46": {
        "texto": "46. Imagine que cinco amigos recebem uma doação de R$ 1.000,00 e precisam dividir o dinheiro igualmente entre eles. Quanto cada um vai ganhar?",
        "opcoes": ["R$ 100,00", "R$ 200,00", "R$ 300,00", "Não sei"]
    },
    "Q47": {
        "texto": "47. Um investimento com alta taxa de retorno terá alta taxa de risco. Essa afirmação é:",
        "opcoes": ["Verdadeira", "Falsa", "Não sei"]
    },
    "Q48": {
        "texto": "48. Um empréstimo com duração de 15 anos normalmente exige pagamentos mensais maiores do que um empréstimo de 30 anos, mas o total de juros pagos ao final do empréstimo será menor. Essa afirmação é:",
        "opcoes": ["Verdadeira", "Falsa", "Não sei"]
    },
    "Q49": {
        "texto": "49. Suponha que você viu o mesmo televisor em duas lojas diferentes pelo preço inicial de R$ 1.000,00. A loja “A” oferece um desconto de R$ 150,00, enquanto a loja “B” oferece um desconto de 10%. Qual é a melhor alternativa?",
        "opcoes": ["Comprar na loja A", "Comprar na loja B", "Tanto faz", "Não sei"]
    },
    "Q50": {
        "texto": "50. Suponha que você realizou um empréstimo de R$ 10.000,00 para ser pago após um ano e o custo com os juros é R$ 600,00. A taxa de juros que você irá pagar nesse empréstimo é de:",
        "opcoes": ["0,6%", "6%", "60%", "Não sei"]
    }
}
respostas_conhecimento = {}
for cod, info in perguntas_conhecimento.items():
    respostas_conhecimento[cod] = st.radio(info["texto"], info["opcoes"], horizontal=False, key=cod)

# ==========================================================
# 11. Funções utilitárias (normalização + gabarito R)
# ==========================================================
def norm_text_r(x):
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    x = ''.join(c for c in unicodedata.normalize('NFD', x) if unicodedata.category(c) != 'Mn')
    x = re.sub(r'[[:punct:]]', '', x)
    x = re.sub(r'\s+', ' ', x)
    return x

def avaliar_conhecimento_r(resps):
    correct_patterns = {
        "Q43": lambda x: re.search(r"mais.*150", x) and not re.search(r"exatamente", x),
        "Q44": lambda x: re.search(r"exatamente|mesmo|igual", x),
        "Q45": lambda x: re.search(r"acao|acoes", x),
        "Q46": lambda x: re.search(r"\b200\b", x),
        "Q47": lambda x: re.search(r"verdade", x),
        "Q48": lambda x: re.search(r"verdade", x),
        "Q49": lambda x: re.search(r"loja ?a", x),
        "Q50": lambda x: ("6" in x or "0.06" in x or "0,06" in x) and ("0,6" not in x)
    }
    score = 0
    for q, val in resps.items():
        txt = norm_text_r(val)
        if q in correct_patterns and correct_patterns[q](txt):
            score += 1
    return score  # 0–8

# ==========================================================
# 12. Variáveis padrão (evita NameError)
# ==========================================================
score_comport_total = np.nan
score_atitude_total = np.nan
score_conhecimento = np.nan
score_alfabetizacao_total = np.nan
score_autocontrole_total = np.nan
score_contab_total = np.nan
score_bem_total = np.nan
score_cfpb = np.nan
nivel_af = nivel_vie = nivel_con = nivel_bem = ""
dica_af = dica_vie = dica_con = dica_bem = ""
cor_nivel = "#3498DB"

# ==========================================================
# 13. Cálculo e exibição
# ==========================================================
if st.button("Calcular meus resultados"):
    # --- Comportamento (0–36) — soma
    num_comport = {k: mapa_freq[v] for k, v in respostas_comport.items()}
    score_comport_total = int(np.sum(list(num_comport.values())))

    # --- Atitude (0–32) — soma (inverter 37–42)
    num_ati = {k: mapa_concord[v] for k, v in respostas_ati.items()}
    for inv in [f"ATI_Q{i}" for i in range(37, 43)]:
        num_ati[inv] = 4 - num_ati[inv]
    score_atitude_total = int(np.sum(list(num_ati.values())))

    # --- Conhecimento (0–8) — soma de acertos (regex R)
    score_conhecimento = int(avaliar_conhecimento_r(respostas_conhecimento))

    # --- Alfabetização Financeira (0–76) — soma
    score_alfabetizacao_total = int(score_comport_total + score_atitude_total + score_conhecimento)
    max_af = 36 + 32 + 8  # 76

    # --- Autocontrole (0–16) — soma (sem inversões; maior = melhor autocontrole)
    num_vies = {k: mapa_concord[v] for k, v in respostas_vies.items()}
    score_autocontrole_total = int(np.sum(list(num_vies.values())))

    # --- Contabilidade mental (0–20) — soma (sem inversões; maior = melhor organização mental)
    num_contab = {k: mapa_concord[v] for k, v in respostas_contab.items()}
    score_contab_total = int(np.sum(list(num_contab.values())))

    # --- CFPB (0–40) e conversão (0–100) — inversões padrão
    num_bem = {}
    for k, v in respostas_bem.items():
        if int(k[-2:]) <= 12:
            num_bem[k] = mapa_escala_1[v]
        else:
            num_bem[k] = mapa_escala_2[v]
    for inv in ["BEM_Q09", "BEM_Q11", "BEM_Q12", "BEM_Q13", "BEM_Q15", "BEM_Q16"]:
        num_bem[inv] = 4 - num_bem[inv]
    score_bem_total = int(np.sum(list(num_bem.values())))

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
    score_cfpb = float(np.interp(score_bem_total, conv_tab["total"], conv_tab[col_ref]))

    # --- Classificação por tercis
    def classificar(score, maximo):
        if score < (maximo/3):
            return "Baixo"
        elif score < (2*maximo/3):
            return "Moderado"
        else:
            return "Alto"

    nivel_af  = classificar(score_alfabetizacao_total, max_af)
    nivel_vie = classificar(score_autocontrole_total, 16)
    nivel_con = classificar(score_contab_total, 20)
    nivel_bem = classificar(score_bem_total, 40)

    # --- Dicas (maior soma = melhor; vieses separados)
    dica_af = {
        "Baixo": "Refine hábitos: orçamento, registro de gastos, metas SMART e estudo de juros/inflação.",
        "Moderado": "Consolide poupança automática e revisão mensal; aprofunde no básico de investimentos.",
        "Alto": "Mantenha disciplina e diversificação; educação continuada em investimentos."
    }[nivel_af]

    dica_vie = {
        "Baixo": "⚠️ Sinal de viés de autocontrole: regra dos 2 dias, automatização da poupança e listas de compra.",
        "Moderado": "🟡 Bom, mas com lapsos: limites por categoria e metas semanais.",
        "Alto": "🟢 Ótimo autocontrole: preserve gatilhos positivos (débitos automáticos, metas mensais)."
    }[nivel_vie]

    dica_con = {
        "Baixo": "⚠️ Sinal de fragilidade na contabilidade mental: centralize visão (planilha/app) e defina centros de custo.",
        "Moderado": "🟡 Estrutura razoável: envelopes digitais e revisão quinzenal.",
        "Alto": "🟢 Boa organização mental do dinheiro: mantenha regras de remanejamento e metas por categoria."
    }[nivel_con]

    dica_bem = {
        "Baixo": "⚠️ Priorize reserva de emergência, redução de dívidas e um planejamento mensal simples.",
        "Moderado": "🟡 Ajuste fluxo de caixa, eleve poupança automática e revise seguros.",
        "Alto": "🟢 Mantenha hábitos, metas de longo prazo e diversifique investimentos."
    }[nivel_bem]

    # --- Métricas principais
    st.subheader("📊 Resultados — Somas dos Construtos")
    colA, colB, colC = st.columns(3)
    colA.metric("Comportamento (0–36)", f"{score_comport_total}")
    colB.metric("Atitude (0–32)", f"{score_atitude_total}")
    colC.metric("Conhecimento (0–8)", f"{score_conhecimento}")

    st.metric("Alfabetização Financeira — Soma (0–76)", f"{score_alfabetizacao_total}")
    st.info(f"Nível AF: **{nivel_af}** — {dica_af}")

    st.markdown("---")
    colD, colE = st.columns(2)
    with colD:
        st.metric("Autocontrole — Soma (0–16)", f"{score_autocontrole_total}")
        st.info(f"Nível Autocontrole: **{nivel_vie}** — {dica_vie}")
    with colE:
        st.metric("Contabilidade mental — Soma (0–20)", f"{score_contab_total}")
        st.info(f"Nível Contab. mental: **{nivel_con}** — {dica_con}")

    st.markdown("---")
    st.subheader("🧮 Bem-Estar Financeiro (CFPB)")
    colF, colG = st.columns(2)
    with colF:
        st.metric("Soma CFPB (0–40)", f"{score_bem_total}")
    with colG:
        st.metric("Escala CFPB (0–100)", f"{score_cfpb:.0f}")
    st.info(f"Nível Bem-Estar: **{nivel_bem}** — {dica_bem}")

    # --- Médias de referência
    if not resumo.empty:
        media_af   = resumo["score_alfabetizacao_total"].mean(skipna=True) if "score_alfabetizacao_total" in resumo.columns else np.nan
        media_bem  = resumo["score_bem_estar_cfpb"].mean(skipna=True)      if "score_bem_estar_cfpb" in resumo.columns else np.nan
        media_vie  = resumo["score_autocontrole_total"].mean(skipna=True)  if "score_autocontrole_total" in resumo.columns else np.nan
        media_con  = resumo["score_contab_total"].mean(skipna=True)        if "score_contab_total" in resumo.columns else np.nan
        media_com  = resumo["score_comport_total"].mean(skipna=True)       if "score_comport_total" in resumo.columns else np.nan
        media_ati  = resumo["score_atitude_total"].mean(skipna=True)       if "score_atitude_total" in resumo.columns else np.nan
        media_conh = resumo["score_conhecimento"].mean(skipna=True)        if "score_conhecimento" in resumo.columns else np.nan
    else:
        media_af = media_bem = media_vie = media_con = media_com = media_ati = media_conh = np.nan

    # --- Barras AF
    fig_af = go.Figure()
    fig_af.add_trace(go.Bar(x=["Você"], y=[score_alfabetizacao_total], name="Você"))
    if not np.isnan(media_af):
        fig_af.add_trace(go.Bar(x=["Média"], y=[media_af], name="Média", marker_color="gray"))
    fig_af.update_layout(title="Alfabetização Financeira (Soma 0–76)", yaxis_title="Soma", barmode="group", height=380, template="plotly_white")
    st.plotly_chart(fig_af, use_container_width=True, key="grafico_af")

    # --- Barras Vieses separados
    colH, colI = st.columns(2)
    with colH:
        fig_vie = go.Figure()
        fig_vie.add_trace(go.Bar(x=["Você"], y=[score_autocontrole_total], name="Você"))
        if not np.isnan(media_vie):
            fig_vie.add_trace(go.Bar(x=["Média"], y=[media_vie], name="Média", marker_color="gray"))
        fig_vie.update_layout(title="Autocontrole (Soma 0–16)", yaxis_title="Soma", barmode="group", height=360, template="plotly_white")
        st.plotly_chart(fig_vie, use_container_width=True, key="grafico_vie")
    with colI:
        fig_con = go.Figure()
        fig_con.add_trace(go.Bar(x=["Você"], y=[score_contab_total], name="Você"))
        if not np.isnan(media_con):
            fig_con.add_trace(go.Bar(x=["Média"], y=[media_con], name="Média", marker_color="gray"))
        fig_con.update_layout(title="Contabilidade mental (Soma 0–20)", yaxis_title="Soma", barmode="group", height=360, template="plotly_white")
        st.plotly_chart(fig_con, use_container_width=True, key="grafico_con")

    # --- Barras CFPB
    fig_cfpb = go.Figure()
    fig_cfpb.add_trace(go.Bar(x=["Você"], y=[score_cfpb], name="Você"))
    if not np.isnan(media_bem):
        fig_cfpb.add_trace(go.Bar(x=["Média"], y=[media_bem], name="Média", marker_color="gray"))
    fig_cfpb.update_layout(title="Bem-Estar (CFPB 0–100)", yaxis_title="CFPB (0–100)", barmode="group", height=380, template="plotly_white")
    st.plotly_chart(fig_cfpb, use_container_width=True, key="grafico_cfpb")

    # --- Radar normalizado (visual)
    radar_labels = ["Comportamento", "Atitude", "Conhecimento", "Autocontrole", "Contab. mental", "Bem-Estar"]
    radar_vals   = [
        score_comport_total/36 if 36 else 0,
        score_atitude_total/32 if 32 else 0,
        score_conhecimento/8 if 8 else 0,
        score_autocontrole_total/16 if 16 else 0,
        score_contab_total/20 if 20 else 0,
        score_bem_total/40 if 40 else 0
    ]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_vals + [radar_vals[0]],
        theta=radar_labels + [radar_labels[0]],
        fill='toself',
        name="Você"
    ))
    if not resumo.empty and all(c in resumo.columns for c in
        ["score_comport_total", "score_atitude_total", "score_conhecimento",
         "score_autocontrole_total", "score_contab_total", "score_bem_estar"]):
        medias_norm = [
            (resumo["score_comport_total"].mean(skipna=True) or 0) / 36,
            (resumo["score_atitude_total"].mean(skipna=True) or 0) / 32,
            (resumo["score_conhecimento"].mean(skipna=True) or 0) / 8,
            (resumo["score_autocontrole_total"].mean(skipna=True) or 0) / 16,
            (resumo["score_contab_total"].mean(skipna=True) or 0) / 20,
            (resumo["score_bem_estar"].mean(skipna=True) or 0) / 40
        ]
        fig_radar.add_trace(go.Scatterpolar(
            r=medias_norm + [medias_norm[0]],
            theta=radar_labels + [radar_labels[0]],
            fill='toself',
            name="Média",
            line=dict(dash="dot")
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Radar dos construtos (normalizado 0–1 apenas para visualização)",
        template="plotly_white",
        height=520
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="grafico_radar")

    # --- PDF
    def gerar_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("💰 Relatório: Alfabetização, Vieses e Bem-Estar Financeiro", styles["Title"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Faixa etária:</b> {idade}", styles["Normal"]))
        story.append(Paragraph(f"<b>Gênero:</b> {genero}", styles["Normal"]))
        story.append(Paragraph(f"<b>Estado civil:</b> {estado_civil}", styles["Normal"]))
        story.append(Paragraph(f"<b>Dependentes:</b> {dependentes}", styles["Normal"]))
        story.append(Paragraph(f"<b>Escolaridade:</b> {escolaridade}", styles["Normal"]))
        story.append(Paragraph(f"<b>Renda:</b> {renda}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("<b>Alfabetização Financeira</b>", styles["Heading3"]))
        story.append(Paragraph(f"- Comportamento (0–36): <b>{score_comport_total}</b>", styles["Normal"]))
        story.append(Paragraph(f"- Atitude (0–32): <b>{score_atitude_total}</b>", styles["Normal"]))
        story.append(Paragraph(f"- Conhecimento (0–8): <b>{score_conhecimento}</b>", styles["Normal"]))
        story.append(Paragraph(f"- <b>AF Total (0–76): {score_alfabetizacao_total}</b> — Nível: <b>{nivel_af}</b>", styles["Normal"]))
        story.append(Paragraph(f"Recomendação AF: {dica_af}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("<b>Vieses (maior soma = menor viés)</b>", styles["Heading3"]))
        story.append(Paragraph(f"- Autocontrole (0–16): <b>{score_autocontrole_total}</b> — Nível: <b>{nivel_vie}</b>", styles["Normal"]))
        story.append(Paragraph(f"Recomendação Autocontrole: {dica_vie}", styles["Normal"]))
        story.append(Paragraph(f"- Contabilidade mental (0–20): <b>{score_contab_total}</b> — Nível: <b>{nivel_con}</b>", styles["Normal"]))
        story.append(Paragraph(f"Recomendação Contab. mental: {dica_con}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("<b>Bem-Estar (CFPB)</b>", styles["Heading3"]))
        story.append(Paragraph(f"- Soma (0–40): <b>{score_bem_total}</b>", styles["Normal"]))
        story.append(Paragraph(f"- Escala CFPB (0–100): <b>{score_cfpb:.0f}</b> — Nível: <b>{nivel_bem}</b>", styles["Normal"]))
        story.append(Paragraph(f"Recomendação Bem-Estar: {dica_bem}", styles["Normal"]))
        doc.build(story)
        buffer.seek(0)
        return buffer

    pdf_file = gerar_pdf()
    st.download_button(
        label="📄 Baixar Relatório em PDF",
        data=pdf_file,
        file_name="relatorio_alfabetizacao_vieses_bemestar.pdf",
        mime="application/pdf"
    )

    # --- Salvamento anônimo
    nova_linha = pd.DataFrame([{
        "idade": idade,
        "genero": genero,
        "renda": renda,
        "score_comport_total": score_comport_total,
        "score_atitude_total": score_atitude_total,
        "score_conhecimento": score_conhecimento,
        "score_alfabetizacao_total": score_alfabetizacao_total,
        "score_autocontrole_total": score_autocontrole_total,
        "score_contab_total": score_contab_total,
        "score_bem_estar": score_bem_total,
        "score_bem_estar_cfpb": score_cfpb
    }])

    try:
        resumo = pd.concat([resumo, nova_linha], ignore_index=True)
        resumo.to_csv("dados_resumo.csv", index=False)
        st.success("✅ Seus dados foram salvos anonimamente para futuras comparações.")
    except Exception as e:
        st.error(f"❌ Erro ao salvar dados: {e}")
