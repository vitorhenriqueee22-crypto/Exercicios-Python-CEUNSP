# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 16: Proteção e Imutabilidade de Ajustes IED
# ============================================================

import math

# 1. Tupla com os dados de placa do transformador
# (V1, V2, Potência nominal, Impedância percentual)

trafo_placa = (13800.0, 220.0, 500.0, 4.5)

print("Dados de placa do transformador:")
print(trafo_placa)

# 2. Tentativa de alterar a potência nominal
try:
    trafo_placa[2] = 750.0

except TypeError:
    print("\nSEGURANÇA: Alteração bloqueada!")
    print("A tupla não permite modificar seus elementos.")

# 3. Função para converter fasor retangular em polar

def fasor_polar(I_r, I_i):

    # Calcula a magnitude do fasor
    magnitude = math.sqrt(I_r**2 + I_i**2)

    # Calcula o ângulo em graus
    angulo = math.degrees(math.atan2(I_i, I_r))

    # Retorna os dois valores em uma tupla
    return magnitude, angulo


# 4. Chamada da função e desempacotamento
magnitude, angulo = fasor_polar(10.0, 5.0)

print("\nFASOR DE CORRENTE:")
print(f"Magnitude: {magnitude:.2f} A")
print(f"Ângulo: {angulo:.2f} graus")
