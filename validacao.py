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