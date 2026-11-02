# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 22: Operações Fasoriais com NumPy
# ============================================================

import numpy as np

# 1. Criar um array com os ângulos das tensões
angulos = np.array([0.0, -120.0, 120.0])

# 2. Calcular os fasores de tensão usando a fórmula de Euler
tensoes = 220 * np.exp(1j * np.radians(angulos))

# 3. Criar um array com as impedâncias complexas
impedancias = np.array([
    10 + 2j,
    12 + 5j,
    8 - 3j
])

# 4. Calcular as correntes usando a Lei de Ohm fasorial
correntes = tensoes / impedancias

# 5. Extrair os módulos das correntes
modulos = np.abs(correntes)

# 6. Extrair os ângulos das correntes em graus
angulos_corrente = np.angle(correntes, deg=True)

# 7. Exibir os resultados arredondados
print("Módulos das correntes (A):")
print(np.round(modulos, 2))

print("\nÂngulos das correntes (graus):")
print(np.round(angulos_corrente, 1))
