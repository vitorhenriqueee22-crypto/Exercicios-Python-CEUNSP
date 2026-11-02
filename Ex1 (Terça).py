# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 01: Resistência Elétrica com Temperatura
# ============================================================

# Dados do condutor de alumínio

rho20 = 0.0282       # Resistividade (ohm.mm²/m)
L = 12500            # Comprimento em metros
S = 240              # Seção transversal em mm²
alpha20 = 0.0039     # Coeficiente de temperatura
T = 45               # Temperatura de operação em °C

# Cálculo da resistência elétrica
R = rho20 * (L / S) * (1 + alpha20 * (T - 20))

# Exibição do resultado
print("CÁLCULO DA RESISTÊNCIA ELÉTRICA")
print(f"Comprimento: {L} m")
print(f"Seção transversal: {S} mm²")
print(f"Temperatura: {T} °C")
print(f"Resistência elétrica: {R:.4f} ohms")
