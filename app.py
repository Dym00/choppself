from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import random
import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave para sessão

# Dados simulados de cartões
CARDS_DATA = [
    {"id": 5432, "name": "Marcos", "email": "marcos@email.com", "phone": "(11) 98765-4321", "type": "pre", "balance": 50.00, "pending": 0.00},
    {"id": 1234, "name": "Ana", "email": "ana@email.com", "phone": "(11) 91234-5678", "type": "pre", "balance": 75.50, "pending": 12.50},
    {"id": 7890, "name": "Carlos", "email": "carlos@email.com", "phone": "(11) 97890-1234", "type": "pos", "balance": 0.00, "pending": 45.00},
    {"id": 4567, "name": "Julia", "email": "julia@email.com", "phone": "(11) 94567-8901", "type": "pos", "balance": 0.00, "pending": 32.75},
    {"id": 9876, "name": "Pedro", "email": "pedro@email.com", "phone": "(11) 99876-5432", "type": "pre", "balance": 120.00, "pending": 0.00}
]

# Rota para a tela de leitura de cartão
@app.route('/card-reader')
def card_reader():
    return render_template('card_reader.html')

# Rota principal
@app.route('/')
def home():
    if 'card_data' not in session:
        return redirect(url_for('card_reader'))
    return render_template('index.html')

# Rota para simular cartão ativo
@app.route('/api/simulate-active-card', methods=['GET'])
def simulate_active_card():
    # Selecionar um cartão aleatório
    card = random.choice(CARDS_DATA)
    
    # Adicionar data de entrada
    card_with_entry = card.copy()
    card_with_entry['entry_date'] = datetime.datetime.now().isoformat()
    
    # Salvar na sessão
    session['card_data'] = card_with_entry
    
    return jsonify({"success": True, "message": "Cartão ativo simulado com sucesso"})

# Rota para ativar um novo cartão
@app.route('/api/activate-card', methods=['POST'])
def activate_card():
    data = request.json
    
    # Verificar se todos os campos necessários estão presentes
    required_fields = ['name', 'email', 'phone', 'card_type', 'card_number']
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Campo obrigatório ausente: {field}"}), 400
    
    # Criar novo cartão
    new_card = {
        "id": int(data['card_number']),
        "name": data['name'],
        "email": data['email'],
        "phone": data['phone'],
        "type": data['card_type'],
        "balance": 0.00,
        "pending": 0.00,
        "entry_date": datetime.datetime.now().isoformat()
    }
    
    # Salvar na sessão
    session['card_data'] = new_card
    
    return jsonify({"success": True, "message": "Cartão ativado com sucesso"})

# Rota para obter dados do cartão atual
@app.route('/api/card-data')
def get_card_data():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo"}), 404
    
    return jsonify({"success": True, "data": session['card_data']})

# Rota para recarregar cartão
@app.route('/api/recharge-card', methods=['POST'])
def recharge_card():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo"}), 404
    
    data = request.json
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({"success": False, "message": "Valor de recarga inválido"}), 400
    
    # Atualizar saldo
    card_data = session['card_data']
    card_data['balance'] += amount
    session['card_data'] = card_data
    
    return jsonify({
        "success": True, 
        "message": "Recarga realizada com sucesso",
        "new_balance": card_data['balance']
    })

# Rota para confirmar pagamento (cartões pós-pagos)
@app.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo"}), 404
    
    card_data = session['card_data']
    
    if card_data['type'] != 'pos':
        return jsonify({"success": False, "message": "Operação válida apenas para cartões pós-pagos"}), 400
    
    # Zerar pendências
    card_data['pending'] = 0.00
    session['card_data'] = card_data
    
    return jsonify({
        "success": True, 
        "message": "Pagamento confirmado com sucesso"
    })

# Rota para mudar tipo de cartão
@app.route('/api/change-card-type', methods=['POST'])
def change_card_type():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo"}), 404
    
    card_data = session['card_data']
    
    # Alternar tipo
    new_type = 'pos' if card_data['type'] == 'pre' else 'pre'
    card_data['type'] = new_type
    session['card_data'] = card_data
    
    return jsonify({
        "success": True, 
        "message": f"Tipo de cartão alterado para {new_type}",
        "new_type": new_type
    })

# Rota para encerrar sessão
@app.route('/api/end-session', methods=['POST'])
def end_session():
    if 'card_data' in session:
        session.pop('card_data')
    
    return jsonify({
        "success": True, 
        "message": "Sessão encerrada com sucesso"
    })

# Rota para gerar número de cartão aleatório
@app.route('/api/generate-card-number')
def generate_card_number():
    # Gerar número aleatório entre 1 e 20
    card_number = random.randint(1, 20)
    
    # Verificar se já existe
    existing_ids = [card['id'] for card in CARDS_DATA]
    while card_number in existing_ids:
        card_number = random.randint(1, 20)
    
    return jsonify({
        "success": True,
        "card_number": card_number
    })

if __name__ == '__main__':
    app.run(debug=True)