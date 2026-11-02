# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 02: Conversão de Fasor Retangular para Polar
# ============================================================

import math

# 1. Declarar os valores do fasor
Vr = 127.0
Vi = -73.32

# 2. Calcular o módulo do fasor
magnitude = math.sqrt(Vr**2 + Vi**2)

# 3. Calcular o ângulo em graus
angulo = math.degrees(math.atan2(Vi, Vr))

# 4. Exibir os resultados
print("CONVERSÃO DE FASOR")

print(f"Parte real: {Vr:.2f} V")
print(f"Parte imaginária: {Vi:.2f} V")

print(f"\nMódulo: {magnitude:.2f} V")
print(f"Ângulo: {angulo:.2f} graus")

print(f"\nFasor polar: {magnitude:.2f} ∠ {angulo:.2f}° V")
