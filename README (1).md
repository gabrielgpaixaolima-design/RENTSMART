# RentSmart — Sistema de Orçamento de Locação (R.M Imóveis)

Aplicação em Python (POO) que calcula o orçamento de locação de apartamentos,
casas e estúdios, mostra um resumo detalhado e gera um CSV com a projeção dos
12 primeiros meses.

## Requisitos
- Python 3.8 ou superior (nenhuma biblioteca externa)

## Como executar
```bash
python rentsmart.py
```
No Visual Studio Code: abra a pasta, abra `rentsmart.py` e clique em **Run Python File**
(ou use o terminal com o comando acima).

O programa pergunta o tipo de imóvel, as características da locação e o número
de parcelas da taxa contratual (1 a 5). Entradas inválidas são perguntadas de novo.

## Saída
- Resumo do orçamento na tela (aluguel, adicionais, desconto, taxa e parcelamento).
- Arquivo `projecao_12_meses.csv` na pasta do projeto, com as colunas
  `mes;aluguel;parcela_taxa;total_mes` (separador `;` e decimal `,`, para abrir direto no Excel).

## Regras implementadas
| Imóvel | Aluguel-base | Adicionais |
|---|---|---|
| Apartamento | R$ 700,00 | 2 quartos +R$ 200,00; garagem +R$ 300,00; desconto de 5% (após adicionais) se não há crianças |
| Casa | R$ 900,00 | 2 quartos +R$ 250,00; garagem +R$ 300,00 |
| Estúdio | R$ 1.200,00 | pacote de 2 vagas +R$ 250,00; cada vaga extra +R$ 60,00 |

Taxa contratual de R$ 2.000,00 em até 5 parcelas sem juros, cobrada à parte do aluguel
(meses 1 a n); a última parcela absorve a diferença de centavos.

## Estrutura de classes
`Imovel` (abstrata) → `Apartamento`, `Casa`, `Estudio` · `Orcamento` · `ExportadorCSV` · `InterfaceUsuario`

## Exemplo
Apartamento, 2 quartos, com garagem, sem crianças, taxa em 5x: aluguel de R$ 1.140,00,
parcela da taxa de R$ 400,00 e total de R$ 15.680,00 em 12 meses.
