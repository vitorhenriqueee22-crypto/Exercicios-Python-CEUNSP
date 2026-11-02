# =====================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 12
# TEMA: Simulacao Transiente de Resfriamento de Motor
# =====================================================

# 1. Definir as condicoes iniciais
T = 95.0
T_amb = 25.0
k_term = 0.08

# 2. Inicializar o contador de tempo
tempo = 0

# 3. Repetir enquanto a temperatura estiver acima de 25.5
while abs(T - T_amb) >= 0.5:

    # Calcular a nova temperatura
    T = T - k_term * (T - T_amb)

    # Acrescentar um minuto ao tempo
    tempo = tempo + 1

# 4. Exibir os resultados
print(f"Tempo para resfriamento: {tempo} minutos")
print(f"Temperatura final: {T:.2f} °C")
print("Condicao segura para religamento atingida!")
