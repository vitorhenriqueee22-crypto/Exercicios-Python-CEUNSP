# ================================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 10
# TEMA: Integracao de Consumo Ativo Horario com Tarifacao Horosazonal
# ================================================================

demanda_diaria = [
    42.0, 39.5, 38.0, 37.5, 41.0, 56.0, 72.0, 88.5,
    94.0, 96.0, 91.5, 89.0, 85.0, 88.0, 92.5, 98.0,
    115.0, 142.0, 155.0, 148.5, 125.0, 98.0, 68.0, 50.0
]

# 1. Madrugada: 00h ate 05h
madrugada = demanda_diaria[:6]

# 2. Amostragem a cada 2 horas
bi_horaria = demanda_diaria[::2]

# 3. Demanda maxima e minima
P_max = max(demanda_diaria)
P_min = min(demanda_diaria)

# 4. Demanda media
P_media = sum(demanda_diaria) / len(demanda_diaria)

# 5. Fator de carga
F_c = P_media / P_max

print("Demanda da madrugada:", madrugada)
print("Amostragem bi-horaria:", bi_horaria)

print(f"Demanda maxima: {P_max:.1f} kW")
print(f"Demanda minima: {P_min:.1f} kW")
print(f"Fator de carga: {F_c:.3f}")