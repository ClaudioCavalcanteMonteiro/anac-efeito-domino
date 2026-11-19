# Efeito Dominó: como um atraso atravessa o Brasil

Análise de atrasos de voos com dados abertos da ANAC (VRA).

# Limitações dos dados 

A coluna Codeshare não existe em 2020 nem em abr, mai, jun, ago e out de 2021. Nesses meses, ela vem como nula na silver.

# Regras de negócio

1. Ler os 81 arquivos com union_by_name, com Codeshare nulo nos 17 meses antigos.
2. Converter as datas de texto para timestamp, tratando o texto null.
3. Assento 0 vira nulo.
4. Criar eh_cargueiro (C ou G) e eh_internacional (I ou G).
5. Criar qtd_parceiros_codeshare.
6. Remover duplicatas exatas (todas as colunas iguais).
7. Marcar eh_substituido nos cancelamentos que foram trocados por outro voo.
8. Manter justificativa e monitorar o preenchimento com um teste.