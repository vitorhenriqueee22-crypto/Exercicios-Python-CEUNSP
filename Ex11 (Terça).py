# =====================================================
# INSTITUICAO: CEUNSP
# CURSO: ENGENHARIA ELETRICA
# DISCIPLINA: PROGRAMACAO EM PYTHON

# ALUNO: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# EXERCICIO: 11
# TEMA: Varredura de Telemetria com Deteccao de Falta
# =====================================================

# Lista de correntes medidas pelo sistema SCADA
correntes = [
    82.0, 85.5, -99.0, 90.0, 94.2,
    -50.0, 105.0, 218.0, 95.0, 91.0
]

# Variaveis acumuladoras
soma = 0
contador = 0

# Percorrer as correntes
for corrente in correntes:

    # Verificar se existe leitura negativa (ruido)
    if corrente < 0:
        print(f"Ruido descartado: {corrente} A")
        continue

    # Verificar se existe corrente de curto-circuito
    if corrente > 200.0:
        print(f"ALARME: Falta detectada! Corrente: {corrente} A")
        break

    # Acumular as correntes validas
    soma = soma + corrente
    contador = contador + 1

# Calcular a media das leituras processadas
media = soma / contador

# Exibir resultado
print(f"\nQuantidade de leituras validas: {contador}")
print(f"Media das correntes validas: {media:.2f} A")
