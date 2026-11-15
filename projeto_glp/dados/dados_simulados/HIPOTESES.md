# Hipóteses dos dados SIMULADOS

> **Atenção:** todos os arquivos desta pasta são **dados sintéticos**, gerados por `src/dados_simulados.py` a partir de `config/hipoteses_simulacao.toml`. Eles servem para testar e demonstrar o sistema e **não descrevem a empresa**. Nenhuma conclusão sobre o consumo real pode ser tirada deles.

- Período: 365 dias a partir de 2025-11-01
- Semente do gerador: 2026 (dados reprodutíveis)

## Modelos de consumo

- **FORNO-01** (Forno cadinho basculante 1, Fusão): G = 5.5·horas + 85.0·t, ruído 4%
- **FORNO-02** (Forno de espera, Espera): G = 3.2·horas + 10.0·t, ruído 4%
- **FORNO-03** (Forno de tratamento térmico, Tratamento térmico): G = 4.0·horas + 30.0·t, ruído 5%
- **Restaurante**: G = 14.0 + 0.032·refeições, ruído 5%; 620 refeições em dias úteis, 180 aos sábados, fechado aos domingos
- **Chuveiros**: perda em espera 0.35 kg/h + GLP por banho calculado pelas Equações 10 a 12 com os parâmetros de `config/parametros.toml`; 130 usuários em dias úteis

## Intervenções simuladas

- INT-01 — FORNO-01, a partir de 2026-05-04: Ajuste da relação ar-combustível e troca da vedação da tampa (redução de 8%)
- INT-02 — AQUECEDOR-01, a partir de 2026-07-01: Isolamento térmico do reservatório de água quente (perda em espera passa a 0.22 kg/h)

## Anomalias inseridas de propósito (gabarito da detecção)

- FUNDICAO/FORNO-01, 2026-01-20 a 2026-01-20: Consumo 35 % acima do modelo em um dia
- RESTAURANTE/COZINHA, 2026-03-10 a 2026-03-12: Consumo 40 % acima e queimador aceso após o expediente
- CHUVEIROS/AQUECEDOR-01, 2026-08-15 a 2026-08-21: Aquecedor em potência alta na madrugada durante uma semana
