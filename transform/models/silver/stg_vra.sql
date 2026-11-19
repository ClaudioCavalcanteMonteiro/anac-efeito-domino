with fonte as (
    select *
    from read_csv(
        '../data/bronze/VRA_*.csv',
        delim = ';',
        header = true,
        union_by_name = true,   -- regra 1: junta os arquivos pelo nome da coluna
        filename = true,        -- guarda de qual arquivo veio cada linha
        all_varchar = true      -- lê tudo como texto; a tipagem é feita abaixo
    )
)

select
    -- Companhia e voo
    "Sigla ICAO Empresa Aérea"                      as empresa_icao,
    "Empresa Aérea"                                 as empresa_nome,
    "Número Voo"                                    as numero_voo,
    "Código DI"                                     as codigo_di,
    "Código Tipo Linha"                             as tipo_linha,

    -- Aeronave
    "Modelo Equipamento"                            as modelo_equipamento,
    try_cast("Número de Assentos" as integer)       as assentos,

    -- Aeroportos
    "Sigla ICAO Aeroporto Origem"                   as origem_icao,
    "Descrição Aeroporto Origem"                    as origem_nome,
    "Sigla ICAO Aeroporto Destino"                  as destino_icao,
    "Descrição Aeroporto Destino"                   as destino_nome,

    -- Horários (regra 2: texto -> timestamp, tratando o texto 'null')
    try_strptime(nullif("Partida Prevista", 'null'), '%d/%m/%Y %H:%M') as partida_prevista,
    try_strptime(nullif("Partida Real",     'null'), '%d/%m/%Y %H:%M') as partida_real,
    try_strptime(nullif("Chegada Prevista", 'null'), '%d/%m/%Y %H:%M') as chegada_prevista,
    try_strptime(nullif("Chegada Real",     'null'), '%d/%m/%Y %H:%M') as chegada_real,

    -- Situação
    "Situação Voo"                                  as situacao_voo,
    "Situação Partida"                              as situacao_partida,
    "Situação Chegada"                              as situacao_chegada,
    nullif(trim("Justificativa"), '')               as justificativa,
    "Codeshare"                                     as codeshare,

    -- Controle
    coalesce(
        try_cast("Referência" as date),                               -- layout antigo: 2020-01-01
        try_strptime("Referência", '%d/%m/%Y %H:%M:%S')::date         -- layout novo: 01/09/2026 00:00:00
    )                                               as data_referencia,
    filename                                        as arquivo_origem

from fonte