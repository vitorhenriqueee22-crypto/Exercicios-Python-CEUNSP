# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 20: Sistema de Deslastre de Cargas Prioritárias
# ============================================================

# 1. Criar a lista de cargas elétricas

cargas = [
    {
        "circuito": "UTI_HOSPITALAR",
        "corrente_a": 60.0,
        "prioridade": 1,
        "ligado": True
    },
    {
        "circuito": "ILUMINACAO_PUBLICA",
        "corrente_a": 45.0,
        "prioridade": 3,
        "ligado": True
    },
    {
        "circuito": "BOMBEAMENTO_ESGOTO",
        "corrente_a": 55.0,
        "prioridade": 2,
        "ligado": True
    },
    {
        "circuito": "CLUBE_RECREATIVO",
        "corrente_a": 35.0,
        "prioridade": 4,
        "ligado": True
    }
]

# 2. Definir a corrente máxima admissível
limite_corrente = 150.0

# 3. Calcular a corrente total inicial
corrente_total = sum(
    carga["corrente_a"]
    for carga in cargas
    if carga["ligado"]
)

print(f"Corrente inicial: {corrente_total:.1f} A")

# 4. Ordenar as cargas da menor para a maior prioridade
cargas_ordenadas = sorted(
    cargas,
    key=lambda carga: carga["prioridade"],
    reverse=True
)

# 5. Desligar cargas até atingir o limite permitido
for carga in cargas_ordenadas:

    if corrente_total <= limite_corrente:
        break

    carga["ligado"] = False

    corrente_total -= carga["corrente_a"]

    print(f"\nDesligando: {carga['circuito']}")
    print(f"Corrente atual: {corrente_total:.1f} A")

# 6. Exibir o estado final das cargas
print("\nESTADO FINAL DOS CIRCUITOS:")

for carga in cargas:
    print(f"{carga['circuito']}: ligado = {carga['ligado']}")

print(f"\nCorrente final: {corrente_total:.1f} A")
