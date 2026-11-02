# ================================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 07
# TEMA: Controle de Temperatura do Oleo de Transformador
# ================================================================

# Temperatura medida do óleo do transformador
T_oleo = float(input("Digite o valor da temperatura em (°C): "))

# Análise da temperatura
if T_oleo < 65:
    print("VENTILACAO_NATURAL (ONAN)")

elif 65 <= T_oleo < 80:
    print("VENTILACAO_FORCADA_ESTAGIO_1 (ONAF-1)")

elif T_oleo >= 95:
    print("TRIP_TERMICO_EMERGENCIA - DESLASTRE TOTAL")

else:
    print("VENTILACAO_FORCADA_ESTAGIO_2 (ONAF-2) + ALARME")
