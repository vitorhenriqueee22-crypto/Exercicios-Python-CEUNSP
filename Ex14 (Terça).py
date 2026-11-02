# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 14: Buffer Circular Oscilográfico FIFO
# ============================================================

# Buffer inicial com capacidade de 5 amostras
buffer = [81.2, 82.0, 80.9, 83.5, 82.8]

# Novas amostras recebidas pelo conversor A/D
novas_leituras = [86.4, 91.0, 94.5]

print("BUFFER OSCILOGRAFICO INICIAL:")
print(buffer)

# Processamento das novas amostras
for leitura in novas_leituras:

    # Adiciona a nova amostra ao final do buffer
    buffer.append(leitura)

    # Remove a amostra mais antiga (primeira posição)
    buffer.pop(0)

    # Exibe o estado atualizado do buffer
    print(f"\nNova leitura: {leitura} A")
    print(f"Buffer atualizado: {buffer}")

# Exibe o resultado final
print("\nBUFFER FINAL:")
print(buffer)
