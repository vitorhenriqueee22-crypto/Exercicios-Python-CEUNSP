# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 04: Correção do Fator de Potência
# ============================================================

import math

# 1. Declarar os dados da instalação
P = 320.0
FP_atual = 0.80
FP_desejado = 0.92

# 2. Calcular os ângulos em radianos
phi1 = math.acos(FP_atual)
phi2 = math.acos(FP_desejado)

# 3. Calcular a potência reativa necessária
Qc = P * (math.tan(phi1) - math.tan(phi2))

# 4. Exibir os resultados
print("CORREÇÃO DO FATOR DE POTÊNCIA")

print(f"Potência ativa: {P:.2f} kW")
print(f"Fator de potência atual: {FP_atual:.2f}")
print(f"Fator de potência desejado: {FP_desejado:.2f}")

print(f"\nPotência reativa necessária: {Qc:.2f} kVAr")

