from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Rota principal
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

if __name__ == '__main__':
    app.run(debug=True)