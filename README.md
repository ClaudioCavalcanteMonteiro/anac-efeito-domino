# Efeito Dominó: como um atraso atravessa o Brasil

Análise de atrasos de voos com dados abertos da ANAC (VRA – Voo Regular Ativo), de jan/2020 até o mês mais recente publicado.


## Glossário

### Siglas e termos

1. **ANAC** - Agência Nacional de Aviação Civil, órgão que regula a aviação civil no Brasil e publica os dados

2. **VRA** - Voo Regular Ativo, base mensal da ANAC com cada voo programado e realizado: horários previstos e reais, situação, companhia, aeroportos e aeronave

3. **SIROS** - Sistema de Registro de Operações, portal da ANAC onde os arquivos do VRA são publicados

4. **ICAO / OACI** - Organização da Aviação Civil Internacional, que define os códigos de 3 letras das companhias (ex.: `GLO` = Gol, `TAM` = LATAM Brasil, `AZU` = Azul) e de 4 letras dos aeroportos (ex.: `SBGR` = Guarulhos, `SBGL` = Galeão)

5. **Codeshare** - Acordo em que outras companhias vendem assentos de um voo operado por uma parceira, com números de voo próprios

6. **Tipo de linha** - Classificação do voo: `N` nacional de passageiros, `I` internacional de passageiros, `C` nacional cargueiro, `G` internacional cargueiro

7. **Situação do voo** - Indica se o voo foi `REALIZADO` ou `CANCELADO`

8. **Partida/chegada prevista** - Horário programado do voo

9. **Partida/chegada real** - Horário em que o voo de fato decolou ou pousou

## Principais descobertas da exploração

Análise feita no arquivo de set/2026.

Descoberta | Evidência | Decisão

1. O layout das colunas muda entre os meses | 17 arquivos sem a coluna `Codeshare` (2020 e 5 meses de 2021) | Leitura por nome de coluna (`union_by_name`) 

2. `Codeshare` não duplica voos: lista as parceiras que vendem assentos | Valores como `AZU/5327`; ~51% dos voos têm ao menos uma parceira | Sem deduplicação 2. por codeshare; criar `qtd_parceiros_codeshare`

3. O VRA inclui voos cargueiros | Tipos de linha `C` e `G`: 3.048 voos (~3,5%), quase todos com 0 assentos | Marcar `eh_cargueiro` na silver; filtrar na gold

4. Assento 0 em voo de passageiros significa dado ausente | 1.010 voos dos tipos `N` e `I` com 0 assentos | Converter 0 em nulo

5. Existem duplicatas exatas | Linhas idênticas da mesma companhia e voo (ex.: Azul 4509) | Remover duplicatas exatas

6. Cancelamentos substituídos por outro número de voo | AAL 0974 cancelado e AAL 9748 realizado no mesmo horário | Marcar `eh_substituido`, fora da taxa de cancelamento

7. A pandemia aparece no volume de dados | O arquivo de abr/2020 tem ~90% menos dados que o de jan/2020 | Destaque na análise histórica

8. A coluna `Referência` muda de formato junto com o layout | Layout antigo: `2020-01-01`; layout novo: `01/09/2026 00:00:00` | Conversão com `coalesce` dos dois formatos

## Regras de negócio (camada silver)

1. Ler todos os arquivos mensais por nome de coluna (`union_by_name`); `Codeshare` fica nulo nos meses em que não existe.
2. Converter as datas de texto (`dd/mm/aaaa hh:mm`) para timestamp, tratando o texto literal `null`.
3. Converter `Número de Assentos` = 0 em nulo (dado ausente, não ausência de assentos).
4. Criar `eh_cargueiro` (tipos `C` ou `G`) e `eh_internacional` (tipos `I` ou `G`).
5. Criar `qtd_parceiros_codeshare` a partir da lista da coluna `Codeshare`.
6. Remover duplicatas exatas (todas as colunas iguais).
7. Marcar `eh_substituido` em cancelamentos com um voo realizado da mesma companhia, origem, destino e partida prevista.
8. Manter `Justificativa` e monitorar o preenchimento com um teste.

## Limitações dos dados

- **Sem causa do atraso:** a coluna `Justificativa` vem 100% vazia, inclusive nos cancelamentos. A Portaria ANAC nº 55/2026 criou códigos de causa, mas até set/2026 eles não aparecem no arquivo público. O pipeline monitora o preenchimento.
- **Sem matrícula da aeronave:** não é possível seguir o mesmo avião ao longo do dia. A propagação de atrasos é medida por aeroporto e por hora.
- **Codeshare ausente** em 2020 e em abr, mai, jun, ago e out de 2021.
- **Atraso de publicação:** a ANAC publica cada mês de 4 a 8 semanas depois de ele terminar.

## Fonte dos dados

Agência Nacional de Aviação Civil (ANAC) – Voo Regular Ativo (VRA), disponível no portal SIROS.