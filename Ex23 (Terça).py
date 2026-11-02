# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 23: Cálculo Matricial de Perdas Ôhmicas
# ============================================================

import numpy as np

# 1. Criar a matriz de correntes das três fases
# Cada linha representa um patamar horário
# Cada coluna representa uma fase (A, B, C)

i_matriz = np.array([
    [80.0, 82.0, 81.0],
    [95.0, 94.0, 97.0],
    [120.0, 118.0, 122.0],
    [60.0, 59.0, 61.0]
])

# 2. Criar o vetor de resistências das três fases
r_fases = np.array([0.15, 0.15, 0.15])

# 3. Calcular as perdas por efeito Joule
# Fórmula: P = I² * R

P_perdas = (i_matriz ** 2) * r_fases

# 4. Somar as perdas das três fases em cada patamar
perdas_totais = np.sum(P_perdas, axis=1)

# 5. Exibir os resultados

print("MATRIZ DE PERDAS POR FASE (W):")
print(P_perdas)

print("\nPERDAS TRIFÁSICAS POR PATAMAR (W):")
print(np.round(perdas_totais, 2))
