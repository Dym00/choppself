from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Rota para a tela de leitura de cartão
@app.route('/card-reader')
def card_reader():
    return render_template('card_reader.html')

# Rota principal (agora será a interface de chopp)
@app.route('/')
def home():
    return render_template('index.html')

# Rota simulada para retornar saldo
@app.route('/api/saldo')
def saldo():
    return jsonify({
        'saldo': 50.00,
        'pendente': 0.00,
        'cartao': '5432',
        'status': 'ativo'
    })

# Rota simulada para processar pagamento de consumo
@app.route('/api/pagar-consumo')
def pagar_consumo():
    return jsonify({'status': 'pago', 'mensagem': 'Consumo pendente pago com sucesso.'})

# Nova rota para obter dados do cartão
@app.route('/api/card-data', methods=['POST'])
def card_data():
    data = request.json
    # Em um sistema real, aqui você consultaria o banco de dados
    # Para a simulação, apenas retornamos os dados recebidos
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)