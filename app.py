from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import random
import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Adicionando CPF e data de nascimento aos dados dos cartões
CARDS_DATA = [
    {"id": 5432, "cpf": "12345678901", "name": "Marcos", "email": "marcos@email.com", "phone": "(11) 98765-4321", "type": "pre", "balance": 50.00, "pending": 0.00, "birth_date": "1985-03-15"},
    {"id": 1234, "cpf": "23456789012", "name": "Ana", "email": "ana@email.com", "phone": "(11) 91234-5678", "type": "pre", "balance": 75.50, "pending": 12.50, "birth_date": "1990-07-22"},
    {"id": 7890, "cpf": "34567890123", "name": "Carlos", "email": "carlos@email.com", "phone": "(11) 97890-1234", "type": "pos", "balance": 0.00, "pending": 45.00, "birth_date": "1988-11-05"},
    {"id": 4567, "cpf": "45678901234", "name": "Julia", "email": "julia@email.com", "phone": "(11) 94567-8901", "type": "pos", "balance": 0.00, "pending": 32.75, "birth_date": "1992-04-18"},
    {"id": 9876, "cpf": "56789012345", "name": "Pedro", "email": "pedro@email.com", "phone": "(11) 99876-5432", "type": "pre", "balance": 120.00, "pending": 0.00, "birth_date": "1983-09-30"}
]

# Função auxiliar para validar CPF
def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    return True

# Função auxiliar para validar idade (18 anos)
def validar_idade(birth_date):
    birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
    today = datetime.datetime.now()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 18

@app.route('/card-reader')
def card_reader():
    return render_template('card_reader.html')

@app.route('/')
def home():
    if 'card_data' not in session:
        return redirect(url_for('card_reader'))
    return render_template('index.html')

@app.route('/api/card-data', methods=['GET'])
def get_card_data():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    return jsonify({"success": True, "data": session['card_data']})

@app.route('/api/generate-card-number', methods=['GET'])
def generate_card_number():
    # Gerar um número de cartão aleatório que não exista ainda
    while True:
        card_number = random.randint(1000, 9999)
        if not any(card['id'] == card_number for card in CARDS_DATA):
            break
    return jsonify({"success": True, "card_number": card_number})

@app.route('/api/simulate-active-card', methods=['GET'])
def simulate_active_card():
    card = random.choice(CARDS_DATA)
    card_with_entry = card.copy()
    card_with_entry['entry_date'] = datetime.datetime.now().isoformat()
    session['card_data'] = card_with_entry
    return jsonify({"success": True, "message": "Cartão ativo simulado com sucesso"})

@app.route('/api/check-client', methods=['POST'])
def check_client():
    data = request.json
    if 'cpf' not in data:
        return jsonify({"success": False, "message": "CPF não fornecido"}), 400
    
    # Validar formato do CPF
    if not validar_cpf(data['cpf']):
        return jsonify({"success": False, "message": "CPF inválido"}), 400
    
    # Remover caracteres não numéricos do CPF
    cpf_numerico = re.sub(r'[^0-9]', '', data['cpf'])
    
    # Verificar se o CPF já existe
    existing_client = next((card for card in CARDS_DATA if re.sub(r'[^0-9]', '', card.get('cpf', '')) == cpf_numerico), None)
    
    if existing_client:
        # Cliente já existe, associar o cartão atual a este cliente
        card_with_entry = existing_client.copy()
        card_with_entry['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = card_with_entry
        return jsonify({"success": True, "client_exists": True, "message": "Cliente encontrado"})
    else:
        # Cliente não existe
        return jsonify({"success": True, "client_exists": False, "message": "Cliente não encontrado"})

@app.route('/api/activate-card', methods=['POST'])
def activate_card():
    data = request.json
    required_fields = ['cpf', 'name', 'email', 'phone', 'card_type', 'card_number', 'birth_date']
    
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Campo obrigatório ausente: {field}"}), 400
    
    # Validar CPF
    if not validar_cpf(data['cpf']):
        return jsonify({"success": False, "message": "CPF inválido"}), 400
    
    # Remover caracteres não numéricos do CPF
    cpf_numerico = re.sub(r'[^0-9]', '', data['cpf'])
    
    # Verificar se o cliente já existe pelo CPF
    existing_client_by_cpf = next((card for card in CARDS_DATA if re.sub(r'[^0-9]', '', card.get('cpf', '')) == cpf_numerico), None)
    
    # Verificar se o cartão já existe
    existing_card = next((card for card in CARDS_DATA if card['id'] == int(data['card_number'])), None)
    
    if existing_client_by_cpf:
        # Cliente já existe, atualizar dados e redirecionar
        existing_client_by_cpf['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = existing_client_by_cpf
        return jsonify({"success": True, "message": "Cliente já existe, redirecionando", "redirect": True})
    
    if existing_card:
        return jsonify({"success": False, "message": "Número de cartão já está em uso"}), 400
    
    # Verificar idade (18 anos)
    if not validar_idade(data['birth_date']):
        return jsonify({"success": False, "message": "Cliente deve ter pelo menos 18 anos"}), 400
    
    # Criar novo cartão
    new_card = {
        "id": int(data['card_number']),
        "cpf": cpf_numerico,
        "name": data['name'],
        "email": data['email'],
        "phone": data['phone'],
        "type": data['card_type'],
        "balance": 0.00,
        "pending": 0.00,
        "entry_date": datetime.datetime.now().isoformat(),
        "birth_date": data['birth_date'],
        "register_date": datetime.datetime.now().isoformat()
    }
    
    # Adicionar à lista de cartões (em um sistema real, isso seria salvo em um banco de dados)
    CARDS_DATA.append(new_card)
    
    # Salvar na sessão
    session['card_data'] = new_card
    
    return jsonify({"success": True, "message": "Cartão ativado com sucesso"})

@app.route('/api/recharge-card', methods=['POST'])
def recharge_card():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    data = request.json
    if 'amount' not in data or not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({"success": False, "message": "Valor de recarga inválido"}), 400
    
    # Atualizar saldo do cartão na sessão
    card_data = session['card_data']
    card_data['balance'] += data['amount']
    session['card_data'] = card_data
    
    # Atualizar saldo do cartão na lista de cartões
    for card in CARDS_DATA:
        if card['id'] == card_data['id']:
            card['balance'] += data['amount']
            break
    
    return jsonify({"success": True, "message": "Cartão recarregado com sucesso", "new_balance": card_data['balance']})

@app.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    # Atualizar saldo do cartão na sessão
    card_data = session['card_data']
    card_data['pending'] = 0.00
    session['card_data'] = card_data
    
    # Atualizar saldo do cartão na lista de cartões
    for card in CARDS_DATA:
        if card['id'] == card_data['id']:
            card['pending'] = 0.00
            break
    
    return jsonify({"success": True, "message": "Pagamento confirmado com sucesso"})

@app.route('/api/end-session', methods=['POST'])
def end_session():
    if 'card_data' in session:
        session.pop('card_data')
    return jsonify({"success": True, "message": "Sessão encerrada com sucesso"})

@app.route('/api/change-card-type', methods=['POST'])
def change_card_type():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    # Atualizar tipo do cartão na sessão
    card_data = session['card_data']
    new_type = 'pos' if card_data['type'] == 'pre' else 'pre'
    card_data['type'] = new_type
    session['card_data'] = card_data
    
    # Atualizar tipo do cartão na lista de cartões
    for card in CARDS_DATA:
        if card['id'] == card_data['id']:
            card['type'] = new_type
            break
    
    return jsonify({"success": True, "message": "Tipo de cartão alterado com sucesso", "new_type": new_type})

if __name__ == '__main__':
    app.run(debug=True)