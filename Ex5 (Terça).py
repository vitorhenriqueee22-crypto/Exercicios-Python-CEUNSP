# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 05: Validação de Dados de Telemetria
# ============================================================

# Entrada de dados
V = float(input("Digite a tensao eficaz (V): "))
I = float(input("Digite a corrente eficaz (A): "))
f = float(input("Digite a frequencia da rede (Hz): "))

# Verificacao das grandezas eletricas
if V < 0 or I < 0 or f < 45 or f > 65:
    print("FALHA_SINAL: Transdutor corrompido")

else:
    print("TELEMETRIA_VALIDA")
