# ================================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 06
# TEMA: Protecao de Sobrecorrente ANSI 50/51
# ================================================================

#Dados
I_nom = float(input("Digite o valor da corrente nominal em (A): "))
I_medida = float(input("Digite o valor da corrente medida em (A): "))

# Calculo do limite de disparo instantaneo
I_limite = 2.5 * I_nom

# Verificacao das condicoes
if I_medida < I_nom: 
    print("REGIME_NORMAL")

elif I_nom < I_medida < 2.5 * I_nom:
    print("SOBRECARGA_TEMPORIZADA (ANSI 51)")

else:
    print("TRIP_INSTANTANEO (ANSI 50) - DISJUNTOR ABERTO")