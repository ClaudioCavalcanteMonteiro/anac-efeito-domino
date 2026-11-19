with sem_duplicatas as (
    -- Regra 6: remove linhas idênticas em todas as colunas
    select distinct *
    from {{ ref('stg_vra') }}
),

base as (
    select
        *,
        -- O arquivo de origem tem a coluna Codeshare? (layout novo)
        bool_or(codeshare is not null)
            over (partition by arquivo_origem)          as arquivo_tem_codeshare,
        -- Existe voo realizado da mesma companhia, rota, horário previsto
        -- e mesmo tipo (passageiros ou carga)?
        bool_or(situacao_voo = 'REALIZADO')
            over (partition by empresa_icao, origem_icao,
                               destino_icao, partida_prevista,
                               tipo_linha in ('C', 'G')) as tem_gemeo_realizado
    from sem_duplicatas
)

select
    -- Companhia e voo
    empresa_icao,
    empresa_nome,
    numero_voo,
    codigo_di,
    tipo_linha,

    -- Aeronave
    modelo_equipamento,
    nullif(assentos, 0)                                 as assentos,               -- regra 3

    -- Aeroportos
    origem_icao,
    origem_nome,
    destino_icao,
    destino_nome,

    -- Horários e atrasos (em minutos; negativo = adiantado)
    partida_prevista,
    partida_real,
    chegada_prevista,
    chegada_real,
    date_diff('minute', partida_prevista, partida_real) as atraso_partida_min,
    date_diff('minute', chegada_prevista, chegada_real) as atraso_chegada_min,

    -- Situação
    situacao_voo,
    situacao_partida,
    situacao_chegada,
    justificativa,

    -- Codeshare (regra 5)
    codeshare,
    case
        when not arquivo_tem_codeshare then null         -- layout antigo: desconhecido
        when codeshare is null         then 0            -- layout novo: sem parceiros
        else len(string_split(codeshare, ','))
    end                                                 as qtd_parceiros_codeshare,

    -- Classificações
    tipo_linha in ('C', 'G')                            as eh_cargueiro,           -- regra 4
    tipo_linha in ('I', 'G')                            as eh_internacional,       -- regra 4
    codigo_di = '0'                                     as eh_voo_regular,         -- regra 9
    situacao_voo = 'CANCELADO'
        and partida_prevista is not null
        and tem_gemeo_realizado                         as eh_substituido,         -- regra 7

    -- Controle
    data_referencia,
    arquivo_origem

from base