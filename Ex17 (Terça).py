# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 17: Modelagem Semântica de Ativos e Consulta Segura
# ============================================================

# 1. Criando um dicionário com os dados do alimentador

alimentador = {
    "tag": "AL-01",
    "subestacao": "SE-CENTRAL",
    "tensao_kv": 13.8,
    "corrente_a": 142.5,
    "disjuntor_fechado": True
}

# 2. Consultando a temperatura com o método get()

temperatura = alimentador.get("temperatura_oleo_c", 25.0)

print("Temperatura inicial:")
print(f"{temperatura:.1f} °C")

# 3. Atualizando o dicionário com update()

alimentador.update({
    "temperatura_oleo_c": 78.2,
    "alarme": "ALERTA_TERMICO"
})

# 4. Exibindo os dados atualizados usando items()

print("\nDADOS ATUALIZADOS DO ALIMENTADOR:")

for chave, valor in alimentador.items():
    print(f"{chave}: {valor}")
