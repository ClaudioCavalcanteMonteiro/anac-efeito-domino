import duckdb

arquivo = "data/bronze/VRA_2026_09.csv"

# Total de linhas do arquivo
duckdb.sql(f"""
    SELECT COUNT(*) AS total_linhas
    FROM read_csv('{arquivo}', delim=';')
""").show()

# Pergunta 2: Justificativa preenchida
# (escreva aqui)
duckdb.sql(f"""
    SELECT 
        COUNT(*) AS total_linhas,
        COUNT(*) FILTER (
            WHERE NULLIF(TRIM(Justificativa), '') IS NOT NULL
        ) AS justificativas_preenchidas,
        COUNT(*) FILTER (
            WHERE NULLIF(TRIM(Justificativa), '') IS NULL
        ) AS justificativas_nao_preenchidas
    FROM read_csv('{arquivo}', delim=';')
""").show()

# Bônus: valores de Situação Voo
duckdb.sql(f"""
    SELECT 
        "Situação Voo",
        COUNT(*) AS quantidade
    FROM read_csv('{arquivo}', delim=';')
    GROUP BY "Situação Voo"
    ORDER BY quantidade DESC
""").show()