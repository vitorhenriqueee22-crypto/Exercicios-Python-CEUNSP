# ============================================================
# Instituição: CEUNSP
# Curso: Engenharia Elétrica
# Disciplina: Programação em Python

# Aluno: Vitor Henrique Santos Das Virgens
# RGM: 48303577

# Exercício 21: Queda de Tensão Trifásica
# ============================================================

import math


def queda_tensao_trifasica(
    i_linha: float,
    comprimento_km: float,
    fator_potencia: float,
    r_km: float = 0.19,
    x_km: float = 0.08
) -> tuple[float, float, bool]:
    """
    Calcula a queda de tensão aproximada em uma linha trifásica.

    ENTRADAS:
        i_linha: corrente de linha em ampères (A).
        comprimento_km: comprimento da linha em quilômetros.
        fator_potencia: fator de potência entre 0 e 1.
        r_km: resistência por quilômetro (ohm/km).
        x_km: reatância por quilômetro (ohm/km).

    FÓRMULAS:
        DeltaV = raiz(3) * I * [R*FP + X*sen(arccos(FP))] * L

        Regulação (%) = (DeltaV / 13800) * 100

    SAÍDAS:
        Retorna uma tupla contendo:
        1. Queda de tensão em volts.
        2. Regulação percentual.
        3. Indicador de conformidade (True ou False).
    """

    # Verifica se o fator de potência está entre 0 e 1
    if not 0 <= fator_potencia <= 1:
        raise ValueError("O fator de potência deve estar entre 0 e 1.")

    # Calcula o seno do ângulo de defasagem
    seno_phi = math.sin(math.acos(fator_potencia))

    # Calcula a queda de tensão trifásica
    delta_v = (
        math.sqrt(3)
        * i_linha
        * (r_km * fator_potencia + x_km * seno_phi)
        * comprimento_km
    )

    # Calcula a regulação percentual
    regulacao = (delta_v / 13800.0) * 100

    # Verifica se a regulação está dentro do limite de 5%
    conforme = regulacao <= 5.0

    # Retorna os três resultados
    return delta_v, regulacao, conforme


# ============================================================
# TESTE DA FUNÇÃO
# ============================================================

delta_v, regulacao, conforme = queda_tensao_trifasica(
    i_linha=120.0,
    comprimento_km=2.5,
    fator_potencia=0.88
)

print("RESULTADOS DO CÁLCULO:")
print(f"Queda de tensão: {delta_v:.2f} V")
print(f"Regulação: {regulacao:.2f}%")
print(f"Conforme: {conforme}")
