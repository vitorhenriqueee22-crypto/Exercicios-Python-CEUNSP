# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 03: Rendimento de um Transformador
# ============================================================

# 1. Solicitar os dados do transformador
P_saida = float(input("Digite a potência de saída (kW): "))
perdas_nucleo = float(input("Digite as perdas no núcleo (W): "))
perdas_cobre = float(input("Digite as perdas no cobre (W): "))

# 2. Converter as perdas de Watts para kW
perdas_nucleo = perdas_nucleo / 1000
perdas_cobre = perdas_cobre / 1000

# 3. Calcular as perdas totais
P_perdas = perdas_nucleo + perdas_cobre

# 4. Calcular a potência de entrada
P_entrada = P_saida + P_perdas

# 5. Calcular o rendimento percentual
rendimento = (P_saida / P_entrada) * 100

# 6. Exibir os resultados
print("\nRESULTADO DO TRANSFORMADOR")
print(f"Potência de saída: {P_saida:.2f} kW")
print(f"Perdas totais: {P_perdas:.2f} kW")
print(f"Potência de entrada: {P_entrada:.2f} kW")
print(f"Rendimento: {rendimento:.3f}%")
