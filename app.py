import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from validar_cpf import validar_cpf

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'API de validação de CPF - Use /validar-cpf com POST'}), 200

@app.route('/validar-cpf', methods=['POST'])
@limiter.limit("100 per day")
def validar_cpf_route():
    data = request.get_json()
    cpf = data.get('cpf')
    if not cpf:
        return jsonify({'error': 'CPF não fornecido'}), 400
    result = validar_cpf(cpf)
    return jsonify({'valid': result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)