# =====================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 13
# TEMA: Fatiamento Temporal e Indicadores de Carga
# =====================================================

# 1. Lista com as 24 demandas horarias em kW
demanda_diaria = [
    42.0, 39.5, 38.0, 37.5, 41.0, 56.0,
    72.0, 88.5, 94.0, 96.0, 91.5, 89.0,
    85.0, 88.0, 92.5, 98.0, 115.0, 142.0,
    155.0, 148.5, 125.0, 98.0, 68.0, 50.0
]

# 2. Extrair as demandas da madrugada (00h ate 05h)
madrugada = demanda_diaria[:6]

# 3. Extrair uma amostra a cada duas horas
bi_horaria = demanda_diaria[::2]

# 4. Encontrar a demanda maxima e minima
P_max = max(demanda_diaria)
P_min = min(demanda_diaria)

# 5. Calcular a demanda media
P_media = sum(demanda_diaria) / len(demanda_diaria)

# 6. Calcular o fator de carga
F_c = P_media / P_max

# 7. Exibir os resultados
print("Demandas da madrugada:", madrugada)
print("Amostragem bi-horaria:", bi_horaria)

print(f"\nDemanda maxima: {P_max:.1f} kW")
print(f"Demanda minima: {P_min:.1f} kW")
print(f"Demanda media: {P_media:.3f} kW")
print(f"Fator de carga: {F_c:.3f}")
