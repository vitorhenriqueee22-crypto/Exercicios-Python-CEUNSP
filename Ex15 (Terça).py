# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 15: Processamento Vetorial com List Comprehensions
# ============================================================

# Lista de tensões eficazes medidas no barramento
leituras_v = [
    220.0, 204.5, 218.0, 235.2, 222.1,
    198.0, 228.4, 232.0, 208.5
]

# Tensão de referência
V_base = 220.0

# 1. Conversão das tensões para por unidade (pu)
tensoes_pu = [round(v / V_base, 3) for v in leituras_v]

# 2. Filtragem das tensões fora da faixa adequada
transgressoes = [v for v in leituras_v if v < 209.0 or v > 231.0]

# Exibição dos resultados
print("Tensões em por unidade (pu):")
print(tensoes_pu)

print("\nLeituras que violam a faixa adequada:")
print(transgressoes)
