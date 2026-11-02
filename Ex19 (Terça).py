# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 19: Serialização de Dados em JSON
# ============================================================

# 1. Importar a biblioteca JSON
import json

# 2. Criar a lista de alimentadores
# Dados utilizados no Exercício 18

alimentadores = [
    {
        "nome": "Alimentador 1",
        "correntes": [115.0, 114.0, 116.0],
        "desbalanceamento_percentual": 0.8695652173913043,
        "status": "CONFORME"
    },
    {
        "nome": "Alimentador 2",
        "correntes": [140.0, 138.0, 142.0],
        "desbalanceamento_percentual": 1.4285714285714286,
        "status": "CONFORME"
    },
    {
        "nome": "Alimentador 3",
        "correntes": [90.0, 125.0, 88.0],
        "desbalanceamento_percentual": 23.762376237623762,
        "status": "ALERTA_DESBALANCEAMENTO"
    }
]

# 3. Criar o dicionário da subestação
subestacao = {
    "nome": "SE-CENTRAL",
    "alimentadores": alimentadores
}

# 4. Converter os dados Python para uma string JSON
pacote_json = json.dumps(
    subestacao,
    indent=2,
    ensure_ascii=False
)

# 5. Exibir o pacote JSON
print("PACOTE JSON GERADO:")
print(pacote_json)

# 6. Verificar a integridade sintática do JSON
try:
    dados_recuperados = json.loads(pacote_json)
    print("\nJSON válido! Dados recuperados com sucesso.")

except json.JSONDecodeError:
    print("\nERRO: JSON inválido!")
