# Sistema inteligente de monitoramento, análise estatística e otimização do consumo de GLP industrial

**Instituição:** CEUNSP · **Curso:** Engenharia Elétrica · **Disciplina:** Experimentação e Análise de Dados
**Aluno:** Vitor Henrique Santos Das Virgens · **Ano:** 2026

Ferramenta de monitoramento e apoio à decisão para o consumo de GLP em três setores de uma indústria mecânica:
fundição de peças, restaurante industrial e aquecimento de água dos chuveiros.
O sistema **não atua** sobre os equipamentos: ele só mede, analisa e recomenda.

## Situação das fases

| Fase | Conteúdo | Situação |
|---|---|---|
| 1 – Pesquisa | Fundamentação técnica, fórmulas, indicadores e métodos estatísticos | Concluída |
| 2 – Diagnóstico | Análise do repositório existente | Concluída |
| 3 – Modelagem | Estrutura de dados, fórmulas e métodos detalhados | Aguardando validação |
| 4 – Desenvolvimento | Módulos Python e painel em Streamlit | Não iniciada |
| 5 – Testes | Cálculos, importação, gráficos, filtros e estatística | Não iniciada |
| 6 – Documentação | Instalação, execução e uso | Não iniciada |
| 7 – Validação | Limitações, hipóteses e requisitos de implantação | Não iniciada |

## Documentos

- [`documentos/Relatorio_Fases_1_e_2_GLP_ABNT.docx`](documentos/Relatorio_Fases_1_e_2_GLP_ABNT.docx): relatório técnico-científico das Fases 1 e 2, formatado pelas normas ABNT (NBR 14724:2024, NBR 6023:2018, NBR 10520:2023, NBR 6024, NBR 6027 e NBR 6028).
- [`documentos/Relatorio_Fases_1_e_2_GLP_ABNT.pdf`](documentos/Relatorio_Fases_1_e_2_GLP_ABNT.pdf): o mesmo relatório em PDF, para leitura.

Antes de entregar, complete na capa e na folha de rosto os campos `[Cidade]` e `[Nome do(a) professor(a) da disciplina]`.
Eles ficam nas constantes `CIDADE` e `ORIENTADOR` de `documentos/gerador/relatorio_fases_1_2.py`.

## Como gerar o relatório novamente

```bash
pip install python-docx
python projeto_glp/documentos/gerador/relatorio_fases_1_2.py
```

Com o LibreOffice (`soffice`) e o Poppler (`pdftotext`) instalados, o script também numera o sumário e as listas
e gera o PDF. Sem eles, o `.docx` sai com `00` no lugar dos números de página do sumário.

- `documentos/gerador/abnt_docx.py`: motor de formatação ABNT, reutilizável nos relatórios das próximas fases.
- `documentos/gerador/relatorio_fases_1_2.py`: conteúdo do relatório. Todo número citado no texto é calculado
  neste arquivo e marcado com a sua origem (REFERÊNCIA, CALCULADO ou HIPÓTESE).

## Regras do projeto

- Nenhum dado da empresa é inventado. Sem medição, usam-se dados **SIMULADOS**, identificados e com hipóteses explícitas.
- Estimativas não são apresentadas como medições, e dados reais e simulados não se misturam sem identificação.
- Consumo absoluto maior não é, sozinho, prova de ineficiência: o consumo é normalizado pela atividade do setor.
- Ajustes em equipamentos de GLP são recomendações para profissionais habilitados.

Os exercícios da disciplina de Programação em Python, na raiz do repositório, não foram alterados.
