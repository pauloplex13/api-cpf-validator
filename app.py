from flask import Flask, request, jsonify
import psycopg
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = Flask(__name__)

# Conexão com Postgres
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Aviso: DATABASE_URL não definida no .env. Cache será desativado localmente.")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao Postgres: {e}")
        return None

# Rota para puxar dados do CPF
@app.route('/dados-cpf', methods=['POST'])
def dados_cpf():
    data = request.get_json()
    cpf = data.get('cpf', '').replace('.', '').replace('-', '').replace(' ', '') if data else None

    # Validação básica do CPF
    if not cpf or len(cpf) != 11 or not cpf.isdigit():
        return jsonify({'erro': 'CPF inválido ou ausente'}), 400

    conn = get_db_connection()
    cur = None

    try:
        # 1. Checa cache no banco (se conexão disponível)
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT dados FROM cpfs WHERE cpf = %s', (cpf,))
            cache_result = cur.fetchone()
            if cache_result:
                return jsonify({**cache_result[0], 'fonte': 'cache'})

        # 2. Consulta API SintegraWS
        token = os.getenv('SINTEGRA_TOKEN')
        if not token:
            return jsonify({'erro': 'Token da API não configurado'}), 500

        # Usar plugin 'cpf'
        api_url = f'https://www.sintegraws.com.br/api/v1/execute-api.php?token={token}&cpf={cpf}&plugin=cpf'
        response = requests.get(api_url, timeout=10)

        api_data = response.json()
        if api_data.get('status') != 'OK':
            return jsonify({'erro': api_data.get('message', 'Dados não encontrados')}), 404

        dados = api_data

        # 3. Salva no cache (se conexão disponível)
        if conn and cur:
            cur.execute(
                'INSERT INTO cpfs (cpf, dados) VALUES (%s, %s) ON CONFLICT (cpf) DO UPDATE SET dados = EXCLUDED.dados',
                (cpf, dados)
            )
            conn.commit()

        return jsonify({**dados, 'fonte': 'api'})
    except Exception as e:
        print(f"Erro na consulta: {e}")
        return jsonify({'erro': 'Erro interno no servidor'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Rota de teste
@app.route('/', methods=['GET'])
def home():
    return jsonify({'mensagem': 'API CPF Validator rodando! Use POST /dados-cpf com {"cpf": "12345678900"}'}), 200

# Cria a tabela se não existir
def create_table():
    conn = get_db_connection()
    if not conn:
        print("Aviso: Não foi possível criar a tabela cpfs (sem conexão com Postgres)")
        return
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS cpfs (
              cpf VARCHAR(11) PRIMARY KEY,
              dados JSONB NOT NULL
            )
        ''')
        conn.commit()
        print("Tabela cpfs criada ou já existe")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")

if __name__ == '__main__':
    create_table()
    port = int(os.environ.get('PORT', 3000))  # Usa $PORT no Render, 3000 localmente
    app.run(host='0.0.0.0', port=port, debug=True)  # debug=True apenas localmente