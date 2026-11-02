# ================================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 08
# TEMA: Classificacao dos Niveis de Tensao conforme Faixas do Exercicio
# ================================================================

# Classificacao de tensao eletrica - PRODIST

# Entrada de dados
V = float(input("Digite a tensao eficaz media (V): "))

# Verificacao da classificacao
if 202 <= V <= 231:
    print("Status: TENSAO_ADEQUADA | Acao: Operacao normal")

elif (191 <= V < 202) or (231 < V <= 233):
    print("Status: TENSAO_PRECÁRIA | Acao: Verificar conformidade")

else:
    print("Status: TENSAO_CRITICA | Acao: Sujeito a penalizacao e compensacao financeira")
