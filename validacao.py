import duckdb

con = duckdb.connect("data/anac.duckdb", read_only=True)

# Falhas de conversão por ano do arquivo
con.sql("""
    SELECT
        regexp_extract(arquivo_origem, 'VRA_(\\d{4})', 1)          AS ano_arquivo,
        COUNT(*)                                                   AS linhas,
        COUNT(*) FILTER (WHERE partida_prevista IS NULL)           AS sem_partida_prevista,
        COUNT(*) FILTER (WHERE partida_real IS NULL
                           AND situacao_voo = 'REALIZADO')         AS realizado_sem_partida_real,
        COUNT(*) FILTER (WHERE data_referencia IS NULL)            AS sem_referencia
    FROM stg_vra
    GROUP BY ALL
    ORDER BY ano_arquivo
""").show()

# Como a Referência aparece em cada layout? (3 exemplos por arquivo)
duckdb.sql("""
    SELECT DISTINCT
        regexp_extract(filename, 'VRA_(\\d{4}_\\d{2})', 1) AS arquivo,
        "Referência"                                       AS referencia_texto
    FROM read_csv(
        ['data/bronze/VRA_2020_01.csv', 'data/bronze/VRA_2026_09.csv'],
        delim = ';', union_by_name = true, filename = true, all_varchar = true
    )
    QUALIFY row_number() OVER (PARTITION BY arquivo ORDER BY referencia_texto) <= 3
    ORDER BY arquivo
""").show()


# ============================================================
#  2- Voos sem partida prevista
# ============================================================

# 2a. Por Código DI: algum código concentra os voos sem previsão?
print("\n2a. Por Código DI")
con.sql("""
    SELECT
        codigo_di,
        COUNT(*)                                          AS voos,
        COUNT(*) FILTER (WHERE partida_prevista IS NULL)  AS sem_prevista,
        ROUND(100.0 * COUNT(*) FILTER (WHERE partida_prevista IS NULL)
              / COUNT(*), 1)                              AS pct_sem_prevista
    FROM stg_vra
    GROUP BY ALL
    ORDER BY voos DESC
""").show()

# 2b. Qual a situação desses voos?
print("\n2b. Situação dos voos sem previsão")
con.sql("""
    SELECT
        situacao_voo,
        COUNT(*)                                          AS voos,
        COUNT(*) FILTER (WHERE chegada_prevista IS NULL)  AS tambem_sem_chegada_prevista
    FROM stg_vra
    WHERE partida_prevista IS NULL
    GROUP BY ALL
    ORDER BY voos DESC
""").show()

# 2c. Voos não regulares por ano e por layout
print("\n2c. Voos não regulares por ano")
con.sql("""
    SELECT
        year(data_referencia)                                       AS ano,
        codeshare_existe,
        COUNT(*)                                                    AS voos,
        COUNT(*) FILTER (WHERE codigo_di <> '0')                    AS nao_regulares,
        ROUND(100.0 * COUNT(*) FILTER (WHERE codigo_di <> '0')
              / COUNT(*), 1)                                        AS pct_nao_regulares
    FROM (
        SELECT *,
               regexp_extract(arquivo_origem, 'VRA_(\\d{4}_\\d{2})', 1) IN
                   ('2021_04','2021_05','2021_06','2021_08','2021_10')
               OR arquivo_origem LIKE '%VRA_2020_%'                 AS layout_antigo,
               NOT layout_antigo                                    AS codeshare_existe
        FROM stg_vra
    )
    GROUP BY ALL
    ORDER BY ano, codeshare_existe
""").show()


# ============================================================
# Ponto 3: fuso horário dos horários
# ============================================================
print("\n3. Duração prevista: ida x volta")
con.sql("""
    SELECT
        origem_icao || ' -> ' || destino_icao                          AS rota,
        COUNT(*)                                                       AS voos,
        median(date_diff('minute', partida_prevista, chegada_prevista)) AS duracao_prevista_min,
        median(date_diff('minute', partida_real, chegada_real))        AS duracao_real_min
    FROM stg_vra
    WHERE codigo_di = '0'
      AND situacao_voo = 'REALIZADO'
      AND origem_icao || '-' || destino_icao IN (
          'SBGR-SBEG', 'SBEG-SBGR',   -- Guarulhos <-> Manaus (1h de fuso)
          'SBBR-SBRB', 'SBRB-SBBR',   -- Brasília <-> Rio Branco (2h de fuso)
          'SBGR-SBBR', 'SBBR-SBGR',   -- Guarulhos <-> Brasília (controle: mesmo fuso)
          'SBGR-LPPT', 'LPPT-SBGR'    -- Guarulhos <-> Lisboa (3h ou 4h de fuso)
      )
    GROUP BY ALL
    ORDER BY rota
""").show()

# 3b. Em que horas os voos domésticos partem?
print("\n3b. Voos domésticos regulares por hora de partida prevista")
con.sql("""
    SELECT
        hour(partida_prevista)  AS hora,
        COUNT(*)                AS voos,
        bar(COUNT(*), 0, 400000, 40) AS grafico
    FROM stg_vra
    WHERE codigo_di = '0'
      AND tipo_linha = 'N'
    GROUP BY ALL
    ORDER BY hora
""").show(max_rows=30)

# ============================================================
# Ponto 4: validação do silver_voos (etapa 4.1)
# ============================================================
print("\n4. Validação do silver_voos")
con.sql("""
    SELECT
        COUNT(*)                                             AS linhas,
        COUNT(*) FILTER (WHERE eh_voo_regular)               AS regulares,
        COUNT(*) FILTER (WHERE eh_cargueiro)                 AS cargueiros,
        COUNT(*) FILTER (WHERE assentos IS NULL)             AS assentos_nulos,
        COUNT(*) FILTER (WHERE qtd_parceiros_codeshare IS NULL) AS codeshare_desconhecido,
        median(atraso_chegada_min) FILTER (
            WHERE eh_voo_regular AND NOT eh_cargueiro
        )                                                    AS atraso_mediano_chegada_min
    FROM silver_voos
""").show()


# ============================================================
# Regra 6: quantas duplicatas exatas existem?
# ============================================================
print("\n6. Duplicatas exatas")
con.sql("""
    SELECT
        (SELECT COUNT(*) FROM stg_vra)                            AS total_linhas,
        (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM stg_vra))   AS distintas_por_arquivo,
        (SELECT COUNT(*) FROM (
            SELECT DISTINCT * EXCLUDE (arquivo_origem) FROM stg_vra
        ))                                                        AS distintas_entre_arquivos
""").show()