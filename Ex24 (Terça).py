# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 24: Construção da Matriz de Admitância Ybus
# ============================================================

import numpy as np

# 1. Criar a função para montar a matriz Ybus

def montar_ybus(n_barras, linhas):

    # Inicializar uma matriz complexa com zeros
    Y = np.zeros((n_barras, n_barras), dtype=complex)

    # Percorrer todas as conexões da rede
    for barra_de, barra_para, Z_serie in linhas:

        # Converter a numeração das barras para índices Python
        i = barra_de - 1
        j = barra_para - 1

        # Calcular a admitância da linha
        y = 1 / Z_serie

        # Atualizar os elementos da matriz Ybus
        Y[i, i] += y
        Y[j, j] += y
        Y[i, j] -= y
        Y[j, i] -= y

    return Y


# 2. Informar as linhas e suas impedâncias

linhas = [
    (1, 2, 0.20 + 0.40j),
    (2, 3, 0.10 + 0.20j),
    (1, 3, 0.20 + 0.40j)
]

# 3. Montar a matriz Ybus para três barras

Y_bus = montar_ybus(3, linhas)

print("MATRIZ DE ADMITÂNCIA Ybus:")
print(Y_bus)


# 4. Criar o vetor de correntes injetadas

correntes = np.array([
    50.0 + 0.0j,
    -25.0 - 10.0j,
    -25.0 + 10.0j
])

print("\nVETOR DE CORRENTES:")
print(correntes)


# 5. Escolher a barra 1 como referência
# Consideramos V1 = 0 V para obter as tensões relativas.

Y_reduzida = Y_bus[1:, 1:]
I_reduzida = correntes[1:]

# Resolver o sistema linear reduzido
V_reduzidas = np.linalg.solve(Y_reduzida, I_reduzida)

# Reconstruir o vetor de tensões, incluindo a referência
tensoes = np.array([
    0.0 + 0.0j,
    V_reduzidas[0],
    V_reduzidas[1]
])

# 6. Exibir os resultados

print("\nTENSÕES NODAIS (V):")
print(tensoes)

print("\nMAGNITUDES DAS TENSÕES (V):")
print(np.round(np.abs(tensoes), 2))

print("\nÂNGULOS DAS TENSÕES (GRAUS):")
print(np.round(np.angle(tensoes, deg=True), 2))

