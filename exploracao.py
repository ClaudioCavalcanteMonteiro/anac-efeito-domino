import duckdb

arquivo = "data/bronze/VRA_2026_09.csv"

# Linhas do arquivo
duckdb.sql(f"""
    SELECT COUNT(*) AS total_linhas
    FROM read_csv('{arquivo}', delim=';')
""").show()

# Coluna Justificativa preenchida

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

# Situação Voo
duckdb.sql(f"""
    SELECT 
        "Situação Voo",
        COUNT(*) AS quantidade
    FROM read_csv('{arquivo}', delim=';')
    GROUP BY "Situação Voo"
    ORDER BY quantidade DESC
""").show()




from pathlib import Path

# Colunas de cada arquivo, agrupadas por layout
layouts = {}
for arquivo in sorted(Path("data/bronze").glob("VRA_*.csv")):
    colunas = duckdb.sql(
        f"SELECT * FROM read_csv('{arquivo.as_posix()}', delim=';') LIMIT 0"
    ).columns
    layouts.setdefault(tuple(colunas), []).append(arquivo.stem)

for i, (colunas, arquivos) in enumerate(layouts.items(), start=1):
    print(f"\n=== Layout {i}: {len(arquivos)} arquivos ({arquivos[0]} a {arquivos[-1]})")
    print(arquivos)



# ============================================================
# Investigação do Codeshare (set/2026)
# ============================================================
arquivo = "data/bronze/VRA_2026_09.csv"
base = f"read_csv('{arquivo}', delim=';')"

# 1. Quais valores aparecem na coluna Codeshare?
print("\n1. Valores de Codeshare")
duckdb.sql(f"""
    SELECT "Codeshare", COUNT(*) AS quantidade
    FROM {base}
    GROUP BY "Codeshare"
    ORDER BY quantidade DESC
""").show()

# 2. Exemplos de voos "gêmeos": mesma origem, destino e partida
#    prevista, mas companhias diferentes
print("\n2. Exemplos de voos gêmeos")
duckdb.sql(f"""
    WITH gemeos AS (
        SELECT
            "Sigla ICAO Aeroporto Origem"  AS origem,
            "Sigla ICAO Aeroporto Destino" AS destino,
            "Partida Prevista"             AS partida
        FROM {base}
        WHERE "Partida Prevista" IS NOT NULL
        GROUP BY ALL
        HAVING COUNT(DISTINCT "Sigla ICAO Empresa Aérea") > 1
        LIMIT 3
    )
    SELECT
        b."Sigla ICAO Empresa Aérea"     AS empresa,
        b."Número Voo"                   AS voo,
        b."Sigla ICAO Aeroporto Origem"  AS origem,
        b."Sigla ICAO Aeroporto Destino" AS destino,
        b."Partida Prevista"             AS partida_prevista,
        b."Partida Real"                 AS partida_real,
        b."Modelo Equipamento"           AS modelo,
        b."Número de Assentos"           AS assentos,
        b."Codeshare"                    AS codeshare
    FROM {base} AS b
    JOIN gemeos AS g
      ON  b."Sigla ICAO Aeroporto Origem"  = g.origem
      AND b."Sigla ICAO Aeroporto Destino" = g.destino
      AND b."Partida Prevista"             = g.partida
    ORDER BY partida_prevista, origem, empresa
""").show(max_width=300)

# 3. Em grande escala: quantos grupos se repetem no mês?
print("\n3. Tamanho do problema")
duckdb.sql(f"""
    WITH grupos AS (
        SELECT
            COUNT(*) AS linhas,
            COUNT(DISTINCT "Sigla ICAO Empresa Aérea") AS empresas
        FROM {base}
        WHERE "Partida Prevista" IS NOT NULL
        GROUP BY "Sigla ICAO Aeroporto Origem",
                 "Sigla ICAO Aeroporto Destino",
                 "Partida Prevista"
        HAVING COUNT(*) > 1
    )
    SELECT
        COUNT(*)                              AS grupos_repetidos,
        SUM(linhas)                           AS linhas_envolvidas,
        COUNT(*) FILTER (WHERE empresas > 1)  AS grupos_empresas_diferentes,
        COUNT(*) FILTER (WHERE empresas = 1)  AS grupos_mesma_empresa
    FROM grupos
""").show()


# 4. Os 21 grupos repetidos da MESMA companhia
print("\n4. Possíveis duplicatas reais")
duckdb.sql(f"""
    WITH dup AS (
        SELECT
            "Sigla ICAO Empresa Aérea"     AS empresa,
            "Sigla ICAO Aeroporto Origem"  AS origem,
            "Sigla ICAO Aeroporto Destino" AS destino,
            "Partida Prevista"             AS partida
        FROM {base}
        WHERE "Partida Prevista" IS NOT NULL
        GROUP BY ALL
        HAVING COUNT(*) > 1
        LIMIT 5
    )
    SELECT
        b."Sigla ICAO Empresa Aérea" AS empresa,
        b."Número Voo"               AS voo,
        b."Código Tipo Linha"        AS tipo_linha,
        d.origem, d.destino,
        b."Partida Prevista"         AS partida_prevista,
        b."Partida Real"             AS partida_real,
        b."Situação Voo"             AS situacao,
        b."Modelo Equipamento"       AS modelo
    FROM {base} AS b
    JOIN dup AS d
      ON  b."Sigla ICAO Empresa Aérea"     = d.empresa
      AND b."Sigla ICAO Aeroporto Origem"  = d.origem
      AND b."Sigla ICAO Aeroporto Destino" = d.destino
      AND b."Partida Prevista"             = d.partida
    ORDER BY empresa, partida_prevista, voo
""").show(max_width=300)

# 5. Tipos de linha e voos sem assentos
print("\n5. Tipos de linha")
duckdb.sql(f"""
    SELECT
        "Código Tipo Linha"                               AS tipo_linha,
        COUNT(*)                                          AS voos,
        COUNT(*) FILTER (WHERE "Número de Assentos" = 0)  AS voos_sem_assentos,
        ROUND(AVG("Número de Assentos"), 0)               AS media_assentos
    FROM {base}
    GROUP BY ALL
    ORDER BY voos DESC
""").show()