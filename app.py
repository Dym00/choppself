from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import random
import datetime
import os
import re
import pyodbc
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração do banco de dados SQL Server
DB_CONFIG = {
    'server': 'seu_servidor',        # Ex: 'localhost\\SQLEXPRESS'
    'database': 'chopperia',         # Nome do seu banco
    'username': 'seu_usuario',       # Seu usuário do SQL Server
    'password': 'sua_senha',         # Sua senha
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_connection_string():
    """Gera a string de conexão para SQL Server"""
    return (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "Trusted_Connection=no;"
    )

@contextmanager
def get_db_connection():
    """Context manager para conexões com o banco de dados SQL Server"""
    conn = None
    try:
        conn = pyodbc.connect(get_connection_string())
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def buscar_cartao_com_dados_cliente(card_id):
    """Busca dados completos do cartão com informações do cliente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                c.ID_CARTAO as id,
                cl.CPF as cpf,
                cl.NM_CLIENTE as name,
                cl.EMAIL as email,
                cl.TELEFONE as phone,
                tc.DESC_CARTAO as type,
                ISNULL(s.QTD_SALDO, 0) as balance,
                cl.DT_NASC as birth_date,
                cl.DT_CADASTRO as register_date,
                c.DT_EMISSAO as card_issue_date
            FROM CARTAO c
            INNER JOIN CARTAO_CLIENTE cc ON c.ID_CARTAO = cc.FK_ID_CARTAO
            INNER JOIN CLIENTE cl ON cc.FK_ID_CLIENTE = cl.ID_CLIENTE
            INNER JOIN TIPO_DE_CARTAO tc ON c.FK_ID_TP_CARTAO = tc.ID_TP_CARTAO
            LEFT JOIN SALDO s ON c.ID_CARTAO = s.FK_ID_CARTAO
            WHERE c.ID_CARTAO = ?
        ''', (card_id,))
        
        row = cursor.fetchone()
        if row:
            # Calcular valor pendente (soma dos pedidos não pagos)
            cursor.execute('''
                SELECT ISNULL(SUM(p.VL_PGTO), 0) as pending
                FROM PAGAMENTO p
                WHERE p.FK_ID_CARTAO = ? AND p.FK_ID_MT_PGTO = 2
                AND p.DT_PGTO IS NULL
            ''', (card_id,))
            
            pending_row = cursor.fetchone()
            pending = pending_row[0] if pending_row else 0
            
            return {
                'id': int(row[0]),
                'cpf': row[1],
                'name': row[2],
                'email': row[3],
                'phone': row[4],
                'type': row[5],
                'balance': float(row[6]),
                'pending': float(pending),
                'birth_date': row[7].strftime('%Y-%m-%d') if row[7] else None,
                'register_date': row[8].strftime('%Y-%m-%d') if row[8] else None,
                'card_issue_date': row[9].strftime('%Y-%m-%d') if row[9] else None
            }
        return None

def buscar_cliente_por_cpf(cpf):
    """Busca um cliente pelo CPF"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CLIENTE WHERE CPF = ?', (cpf,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None

def buscar_cartao_por_cpf(cpf):
    """Busca cartão pelo CPF do cliente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.ID_CARTAO
            FROM CARTAO c
            INNER JOIN CARTAO_CLIENTE cc ON c.ID_CARTAO = cc.FK_ID_CARTAO
            INNER JOIN CLIENTE cl ON cc.FK_ID_CLIENTE = cl.ID_CLIENTE
            WHERE cl.CPF = ?
        ''', (cpf,))
        
        row = cursor.fetchone()
        if row:
            return buscar_cartao_com_dados_cliente(row[0])
        return None

def criar_cliente_e_cartao(client_data, card_data):
    """Cria um novo cliente e cartão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Gerar ID do cliente
        cursor.execute('SELECT ISNULL(MAX(ID_CLIENTE), 0) + 1 FROM CLIENTE')
        client_id = cursor.fetchone()[0]
        
        # Inserir cliente
        cursor.execute('''
            INSERT INTO CLIENTE (ID_CLIENTE, NM_CLIENTE, CPF, DT_NASC, EMAIL, TELEFONE, DT_CADASTRO, ENDERECO, FK_ID_GENERO)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id,
            client_data['name'],
            client_data['cpf'],
            client_data['birth_date'],
            client_data['email'],
            client_data['phone'],
            datetime.datetime.now().date(),
            '',  # Endereço vazio por enquanto
            1    # Gênero padrão (pode ser ajustado)
        ))
        
        # Determinar tipo do cartão (1=pre, 2=pos)
        card_type_id = 1 if card_data['type'] == 'pre' else 2
        
        # Inserir cartão
        cursor.execute('''
            INSERT INTO CARTAO (ID_CARTAO, DT_EMISSAO, FK_ID_TP_CARTAO)
            VALUES (?, ?, ?)
        ''', (
            card_data['id'],
            datetime.datetime.now().date(),
            card_type_id
        ))
        
        # Associar cartão ao cliente
        cursor.execute('''
            INSERT INTO CARTAO_CLIENTE (FK_ID_CLIENTE, FK_ID_CARTAO)
            VALUES (?, ?)
        ''', (client_id, card_data['id']))
        
        # Criar saldo inicial
        cursor.execute('SELECT ISNULL(MAX(ID_SALDO), 0) + 1 FROM SALDO')
        saldo_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO SALDO (ID_SALDO, QTD_SALDO, FK_ID_CARTAO)
            VALUES (?, ?, ?)
        ''', (saldo_id, 0, card_data['id']))
        
        conn.commit()
        return client_id

def atualizar_saldo_cartao(card_id, new_balance):
    """Atualiza o saldo de um cartão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE SALDO 
            SET QTD_SALDO = ? 
            WHERE FK_ID_CARTAO = ?
        ''', (new_balance, card_id))
        conn.commit()
        return cursor.rowcount > 0

def atualizar_tipo_cartao(card_id, new_type):
    """Atualiza o tipo de um cartão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        card_type_id = 1 if new_type == 'pre' else 2
        cursor.execute('''
            UPDATE CARTAO 
            SET FK_ID_TP_CARTAO = ? 
            WHERE ID_CARTAO = ?
        ''', (card_type_id, card_id))
        conn.commit()
        return cursor.rowcount > 0

def obter_todos_ids_cartoes():
    """Retorna todos os IDs de cartões existentes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ID_CARTAO FROM CARTAO')
        return [row[0] for row in cursor.fetchall()]

def criar_sessao(card_id, client_id):
    """Cria uma nova sessão para o cartão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.datetime.now()
        cursor.execute('''
            INSERT INTO SESSAO (FK_ID_CARTAO, FK_ID_CLIENTE, DT_ENTRADA, DT_SAIDA, HORA_ENTRADA, HORA_SAIDA)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            card_id, 
            client_id, 
            now.date(), 
            now.date(), 
            now.time(), 
            now.time()
        ))
        conn.commit()

def adicionar_registro_pagamento(card_id, client_id, amount, payment_type_id=1, motive_id=1):
    """Adiciona um registro de pagamento"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Gerar ID do pagamento
        cursor.execute('SELECT ISNULL(MAX(ID_PGTO), 0) + 1 FROM PAGAMENTO')
        payment_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO PAGAMENTO (ID_PGTO, DT_PGTO, VL_PGTO, FK_ID_CLIENTE, FK_ID_MT_PGTO, FK_ID_CARTAO, FK_ID_TP_PGTO)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment_id,
            datetime.datetime.now().date(),
            amount,
            client_id,
            motive_id,  # 1=Recarga de cartão
            card_id,
            payment_type_id  # 1=Dinheiro
        ))
        conn.commit()

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
    existing_ids = obter_todos_ids_cartoes()
    while True:
        card_number = random.randint(1000, 9999)
        if card_number not in existing_ids:
            break
    return jsonify({"success": True, "card_number": card_number})

@app.route('/api/simulate-active-card', methods=['GET'])
def simulate_active_card():
    existing_ids = obter_todos_ids_cartoes()
    if not existing_ids:
        return jsonify({"success": False, "message": "Nenhum cartão disponível"}), 404
    
    random_id = random.choice(existing_ids)
    card = buscar_cartao_com_dados_cliente(random_id)
    
    if card:
        card['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = card
        return jsonify({"success": True, "message": "Cartão ativo simulado com sucesso"})
    else:
        return jsonify({"success": False, "message": "Erro ao buscar cartão"}), 500

@app.route('/api/check-client', methods=['POST'])
def check_client():
    data = request.json
    if 'cpf' not in data:
        return jsonify({"success": False, "message": "CPF não fornecido"}), 400
    
    if not validar_cpf(data['cpf']):
        return jsonify({"success": False, "message": "CPF inválido"}), 400
    
    cpf_numerico = re.sub(r'[^0-9]', '', data['cpf'])
    existing_client = buscar_cartao_por_cpf(cpf_numerico)
    
    if existing_client:
        existing_client['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = existing_client
        return jsonify({"success": True, "client_exists": True, "message": "Cliente encontrado"})
    else:
        return jsonify({"success": True, "client_exists": False, "message": "Cliente não encontrado"})

@app.route('/api/activate-card', methods=['POST'])
def activate_card():
    data = request.json
    required_fields = ['cpf', 'name', 'email', 'phone', 'card_type', 'card_number', 'birth_date']
    
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Campo obrigatório ausente: {field}"}), 400
    
    if not validar_cpf(data['cpf']):
        return jsonify({"success": False, "message": "CPF inválido"}), 400
    
    cpf_numerico = re.sub(r'[^0-9]', '', data['cpf'])
    
    # Verificar se o cliente já existe pelo CPF
    existing_client_by_cpf = buscar_cartao_por_cpf(cpf_numerico)
    
    # Verificar se o cartão já existe
    existing_card = buscar_cartao_com_dados_cliente(int(data['card_number']))
    
    if existing_client_by_cpf:
        existing_client_by_cpf['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = existing_client_by_cpf
        return jsonify({"success": True, "message": "Cliente já existe, redirecionando", "redirect": True})
    
    if existing_card:
        return jsonify({"success": False, "message": "Número de cartão já está em uso"}), 400
    
    if not validar_idade(data['birth_date']):
        return jsonify({"success": False, "message": "Cliente deve ter pelo menos 18 anos"}), 400
    
    # Criar novo cliente e cartão
    client_data = {
        "name": data['name'],
        "cpf": cpf_numerico,
        "email": data['email'],
        "phone": data['phone'],
        "birth_date": data['birth_date']
    }
    
    card_data = {
        "id": int(data['card_number']),
        "type": data['card_type']
    }
    
    try:
        client_id = criar_cliente_e_cartao(client_data, card_data)
        
        # Buscar dados completos do cartão criado
        new_card = buscar_cartao_com_dados_cliente(card_data['id'])
        new_card['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = new_card
        
        return jsonify({"success": True, "message": "Cartão ativado com sucesso"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao criar cartão: {str(e)}"}), 500

@app.route('/api/recharge-card', methods=['POST'])
def recharge_card():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    data = request.json
    if 'amount' not in data or not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({"success": False, "message": "Valor de recarga inválido"}), 400
    
    card_data = session['card_data']
    new_balance = card_data['balance'] + data['amount']
    
    try:
        # Atualizar saldo no banco
        if atualizar_saldo_cartao(card_data['id'], new_balance):
            # Registrar pagamento
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT cl.ID_CLIENTE 
                    FROM CLIENTE cl
                    INNER JOIN CARTAO_CLIENTE cc ON cl.ID_CLIENTE = cc.FK_ID_CLIENTE
                    WHERE cc.FK_ID_CARTAO = ?
                ''', (card_data['id'],))
                client_id = cursor.fetchone()[0]
            
            adicionar_registro_pagamento(card_data['id'], client_id, data['amount'], 1, 1)  # Dinheiro, Recarga
            
            card_data['balance'] = new_balance
            session['card_data'] = card_data
            return jsonify({"success": True, "message": "Cartão recarregado com sucesso", "new_balance": new_balance})
        else:
            return jsonify({"success": False, "message": "Erro ao atualizar saldo"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao recarregar cartão: {str(e)}"}), 500

@app.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    card_data = session['card_data']
    
    try:
        # Atualizar pagamentos pendentes para confirmados
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE PAGAMENTO 
                SET DT_PGTO = ? 
                WHERE FK_ID_CARTAO = ? AND FK_ID_MT_PGTO = 2 AND DT_PGTO IS NULL
            ''', (datetime.datetime.now().date(), card_data['id']))
            conn.commit()
        
        card_data['pending'] = 0.00
        session['card_data'] = card_data
        return jsonify({"success": True, "message": "Pagamento confirmado com sucesso"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao confirmar pagamento: {str(e)}"}), 500

@app.route('/api/end-session', methods=['POST'])
def end_session():
    if 'card_data' in session:
        session.pop('card_data')
    return jsonify({"success": True, "message": "Sessão encerrada com sucesso"})

@app.route('/api/change-card-type', methods=['POST'])
def change_card_type():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401
    
    card_data = session['card_data']
    new_type = 'pos' if card_data['type'] == 'pre' else 'pre'
    
    try:
        if atualizar_tipo_cartao(card_data['id'], new_type):
            card_data['type'] = new_type
            session['card_data'] = card_data
            return jsonify({"success": True, "message": "Tipo de cartão alterado com sucesso", "new_type": new_type})
        else:
            return jsonify({"success": False, "message": "Erro ao alterar tipo do cartão"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao alterar tipo do cartão: {str(e)}"}), 500

if __name__ == '__main__':
    try:
        # Testar conexão
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM CLIENTE')
            count = cursor.fetchone()[0]
            print(f"Conexão com SQL Server estabelecida! {count} clientes encontrados.")
        
        app.run(debug=True)
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")