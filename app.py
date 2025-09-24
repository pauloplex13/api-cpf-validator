from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from validar_cpf import validar_cpf

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/validar-cpf', methods=['POST'])
@limiter.limit("100 per day")  # Limite de requisições
def validar_cpf_route():
    data = request.get_json()
    cpf = data.get('cpf')
    if not cpf:
        return jsonify({'error': 'CPF não fornecido'}), 400
    result = validar_cpf(cpf)
    return jsonify({'valid': result})

if __name__ == '__main__':
    app.run(debug=True)