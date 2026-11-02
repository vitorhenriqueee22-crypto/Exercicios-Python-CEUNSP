# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 18: Cálculo de Desbalanceamento de Fases
# ============================================================

# 1. Lista de dicionários com as correntes dos alimentadores

alimentadores = [
    {
        "nome": "Alimentador 1",
        "correntes": [115.0, 114.0, 116.0]
    },
    {
        "nome": "Alimentador 2",
        "correntes": [140.0, 138.0, 142.0]
    },
    {
        "nome": "Alimentador 3",
        "correntes": [90.0, 125.0, 88.0]
    }
]

# 2. Percorrer cada alimentador
for alimentador in alimentadores:

    correntes = alimentador["correntes"]

    # Calcular a corrente média das três fases
    media = sum(correntes) / len(correntes)

    # Calcular a maior diferença absoluta em relação à média
    diferencas = [abs(i - media) for i in correntes]

    maior_diferenca = max(diferencas)

    # Calcular o percentual de desbalanceamento
    desbalanceamento = (maior_diferenca / media) * 100

    # 3. Classificar o alimentador
    if desbalanceamento > 15.0:
        alimentador["status"] = "ALERTA_DESBALANCEAMENTO"
    else:
        alimentador["status"] = "CONFORME"

    # 4. Exibir os resultados
    print(f"\n{alimentador['nome']}")
    print(f"Correntes: {correntes}")
    print(f"Corrente média: {media:.2f} A")
    print(f"Desbalanceamento: {desbalanceamento:.2f}%")
    print(f"Status: {alimentador['status']}")
