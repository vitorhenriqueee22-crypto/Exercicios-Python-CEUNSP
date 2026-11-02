# ================================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 09
# TEMA: Calculo do Valor Eficaz RMS de Amostras
# ================================================================

import math

# Lista de amostras de tensao
amostras = [0.0, 110.0, 190.5, 220.0, 190.5, 110.0,
            0.0, -110.0, -190.5, -220.0, -190.5, -110.0]

# Quantidade de amostras
N = len(amostras)

# Variavel acumuladora
soma = 0

# Somatorio dos quadrados
for v in amostras:
    soma = soma + v**2

# Calculo da media quadratica
media = soma / N

# Calculo da tensao eficaz
V_RMS = math.sqrt(media)

# Exibicao do resultado
print(f"Amostras: {N} | V_RMS Calculado: {V_RMS:.2f} V")
