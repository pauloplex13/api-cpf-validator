import psycopg2

conn = psycopg2.connect(
    host="dpg-d3a7t063jp1c73cqrbag-a.oregon-postgres.render.com",
    port=5432,
    dbname="puchar_cpf",
    user="puchar_cpf_user",
    password="gwgSnflYdxweJrurUREJvme8HY5kIF4g",
    sslmode="require"
)

cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS cpfs (
  cpf VARCHAR(11) PRIMARY KEY,
  dados JSONB NOT NULL
);
""")
conn.commit()
cur.close()
conn.close()
print("Tabela criada com sucesso!")
