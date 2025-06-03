from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import json
import random
import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Configurações do Banco de Dados para SQL Server (Autenticação Windows) ---
# ATENÇÃO: Substitua 'ODBC+Driver+18+for+SQL+Server' pelo nome do driver ODBC instalado no seu sistema.
# E certifique-se que 'ATRIUM-AP002\SQLEXPRESS' e 'chopperia' estão corretos.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://ATRIUM-AP002\SQLEXPRESS/chopperia?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Modelos do Banco de Dados ---

class TipoDeCerveja(db.Model):
    __tablename__ = 'TIPO_DE_CERVEJA'
    ID_TP_CERVEJA = db.Column(db.Numeric, primary_key=True)
    DESC_TP_CERVEJA = db.Column(db.String(50), nullable=False)

class Saldo(db.Model):
    __tablename__ = 'SALDO'
    ID_SALDO = db.Column(db.Numeric, primary_key=True)
    QTD_SALDO = db.Column(db.Numeric(10, 2), nullable=False)
    FK_ID_CARTAO = db.Column(db.Numeric, db.ForeignKey('CARTAO.ID_CARTAO'))

    def to_dict(self):
        return {
            "id_saldo": int(self.ID_SALDO),
            "quantidade_saldo": float(self.QTD_SALDO),
            "fk_id_cartao": int(self.FK_ID_CARTAO) if self.FK_ID_CARTAO else None
        }

class MotivoDePagamento(db.Model):
    __tablename__ = 'MOTIVO_DE_PAGAMENTO'
    ID_MT_PGTO = db.Column(db.Numeric, primary_key=True)
    DESC_MT_PGTO = db.Column(db.String(50), nullable=False)

class TipoDeCartao(db.Model):
    __tablename__ = 'TIPO_DE_CARTAO'
    ID_TP_CARTAO = db.Column(db.Numeric, primary_key=True)
    DESC_CARTAO = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id_tipo_cartao": int(self.ID_TP_CARTAO),
            "descricao_cartao": self.DESC_CARTAO
        }

class Cartao(db.Model):
    __tablename__ = 'CARTAO'
    ID_CARTAO = db.Column(db.Numeric, primary_key=True, autoincrement=False)
    DT_EMISSAO = db.Column(db.Date, default=datetime.date.today)
    FK_ID_TP_CARTAO = db.Column(db.Numeric, db.ForeignKey('TIPO_DE_CARTAO.ID_TP_CARTAO'), nullable=False)

    tipo_cartao = db.relationship('TipoDeCartao', backref='cartoes')
    saldos = db.relationship('Saldo', backref='cartao', lazy=True, cascade="all, delete-orphan")
    clientes = db.relationship('Cliente', secondary='CARTAO_CLIENTE', backref=db.backref('cartoes', lazy='dynamic'))

    def to_dict(self):
        current_balance = sum(saldo.QTD_SALDO for saldo in self.saldos) if self.saldos else 0.00
        return {
            "id_cartao": int(self.ID_CARTAO),
            "data_emissao": self.DT_EMISSAO.strftime('%Y-%m-%d'),
            "tipo_cartao": self.tipo_cartao.to_dict() if self.tipo_cartao else None,
            "balance": float(current_balance)
        }

class Funcionario(db.Model):
    __tablename__ = 'FUNCIONARIO'
    ID_FUNC = db.Column(db.Numeric, primary_key=True)
    NM_FUNC = db.Column(db.String(50), nullable=False)
    EMAIL = db.Column(db.String(50), nullable=False)
    SENHA = db.Column(db.String(50), nullable=False)

class Pedido(db.Model):
    __tablename__ = 'PEDIDO'
    ID_PEDIDO = db.Column(db.Numeric, primary_key=True)
    DT_PEDIDO = db.Column(db.Date, nullable=False)
    HR_PEDIDO = db.Column(db.Time, nullable=False)
    FK_ID_FUNC = db.Column(db.Numeric, db.ForeignKey('FUNCIONARIO.ID_FUNC'))

    funcionario = db.relationship('Funcionario', backref='pedidos')
    cartoes_associados = db.relationship('Cartao', secondary='CARTAO_PEDIDO', backref=db.backref('pedidos', lazy='dynamic'))
    cervejas_pedidas = db.relationship('Cerveja', secondary='PEDIDO_CERVEJA', backref=db.backref('pedidos', lazy='dynamic'))

class Cerveja(db.Model):
    __tablename__ = 'CERVEJA'
    ID_CERVEJA = db.Column(db.Numeric, primary_key=True)
    NM_CERVEJA = db.Column(db.String(50), nullable=False)
    QTD_CERVEJA = db.Column(db.Numeric, nullable=False)
    FK_ID_TP_CERVEJA = db.Column(db.Numeric, db.ForeignKey('TIPO_DE_CERVEJA.ID_TP_CERVEJA'))

    tipo_cerveja = db.relationship('TipoDeCerveja', backref='cervejas')

class Genero(db.Model):
    __tablename__ = 'GENERO'
    ID_GENERO = db.Column(db.Numeric, primary_key=True)
    DESC_GENERO = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id_genero": int(self.ID_GENERO),
            "descricao_genero": self.DESC_GENERO
        }

class Cliente(db.Model):
    __tablename__ = 'CLIENTE'
    ID_CLIENTE = db.Column(db.Numeric, primary_key=True)
    CPF = db.Column(db.String(11), unique=True, nullable=False)
    NM_CLIENTE = db.Column(db.String(50), nullable=False)
    DT_NASC = db.Column(db.Date, nullable=False)
    EMAIL = db.Column(db.String(50), nullable=False)
    TELEFONE = db.Column(db.String(20), nullable=False)
    DT_CADASTRO = db.Column(db.Date, default=datetime.date.today)
    ENDERECO = db.Column(db.String(100))
    FK_ID_GENERO = db.Column(db.Numeric, db.ForeignKey('GENERO.ID_GENERO'))

    genero = db.relationship('Genero', backref='clientes')

    def to_dict(self):
        return {
            "id_cliente": int(self.ID_CLIENTE),
            "nome_cliente": self.NM_CLIENTE,
            "cpf": self.CPF,
            "data_nascimento": self.DT_NASC.strftime('%Y-%m-%d'),
            "email": self.EMAIL,
            "telefone": self.TELEFONE,
            "data_cadastro": self.DT_CADASTRO.strftime('%Y-%m-%d') if self.DT_CADASTRO else None, # Ajuste para DT_CADASTRO
            "endereco": self.ENDERECO,
            "genero": self.genero.to_dict() if self.genero else None
        }

class TipoDePagamento(db.Model):
    __tablename__ = 'TIPO_DE_PAGAMENTO'
    ID_TP_PGTO = db.Column(db.Numeric, primary_key=True)
    DESC_TP_PGTO = db.Column(db.String(50), nullable=False)

class Pagamento(db.Model):
    __tablename__ = 'PAGAMENTO'
    ID_PGTO = db.Column(db.Numeric, primary_key=True)
    DT_PGTO = db.Column(db.Date, nullable=False)
    VL_PGTO = db.Column(db.Numeric(10, 2), nullable=False)
    FK_ID_CLIENTE = db.Column(db.Numeric, db.ForeignKey('CLIENTE.ID_CLIENTE'))
    FK_ID_MT_PGTO = db.Column(db.Numeric, db.ForeignKey('MOTIVO_DE_PAGAMENTO.ID_MT_PGTO'))
    FK_ID_CARTAO = db.Column(db.Numeric, db.ForeignKey('CARTAO.ID_CARTAO'))
    FK_ID_TP_PGTO = db.Column(db.Numeric, db.ForeignKey('TIPO_DE_PAGAMENTO.ID_TP_PGTO'))

    cliente = db.relationship('Cliente', backref='pagamentos')
    motivo_pagamento = db.relationship('MotivoDePagamento', backref='pagamentos')
    cartao = db.relationship('Cartao', backref='pagamentos')
    tipo_pagamento = db.relationship('TipoDePagamento', backref='pagamentos')

class TipoDeUsuario(db.Model):
    __tablename__ = 'TIPO_DE_USUARIO'
    ID_TP_USUARIO = db.Column(db.Numeric, primary_key=True)
    DESC_TP_USUARIO = db.Column(db.String(50), nullable=False)

# --- Tabelas de Associação ---
class CartaoPedido(db.Model):
    __tablename__ = 'CARTAO_PEDIDO'
    FK_ID_PEDIDO = db.Column(db.Numeric, db.ForeignKey('PEDIDO.ID_PEDIDO'), primary_key=True)
    FK_ID_CARTAO = db.Column(db.Numeric, db.ForeignKey('CARTAO.ID_CARTAO'), primary_key=True)

class CartaoCliente(db.Model):
    __tablename__ = 'CARTAO_CLIENTE'
    FK_ID_CLIENTE = db.Column(db.Numeric, db.ForeignKey('CLIENTE.ID_CLIENTE'), primary_key=True)
    FK_ID_CARTAO = db.Column(db.Numeric, db.ForeignKey('CARTAO.ID_CARTAO'), primary_key=True)

class PedidoCerveja(db.Model):
    __tablename__ = 'PEDIDO_CERVEJA'
    FK_ID_PEDIDO = db.Column(db.Numeric, db.ForeignKey('PEDIDO.ID_PEDIDO'), primary_key=True)
    FK_ID_CERVEJA = db.Column(db.Numeric, db.ForeignKey('CERVEJA.ID_CERVEJA'), primary_key=True)

# Cria as tabelas no banco de dados, se não existirem
with app.app_context():
    db.create_all()

# --- Funções Auxiliares ---
def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    return True

def validar_idade(birth_date_str):
    try:
        birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = datetime.date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age >= 18
    except ValueError:
        return False

# --- Rotas da Aplicação ---

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

    card_id = session['card_data'].get('id_cartao')
    if not card_id:
        return jsonify({"success": False, "message": "ID do cartão não encontrado na sessão"}), 400

    current_card = Cartao.query.get(card_id)
    if not current_card:
        session.pop('card_data', None)
        return jsonify({"success": False, "message": "Cartão não encontrado no banco de dados"}), 404

    cliente_associado = current_card.clientes[0] if current_card.clientes else None

    card_data_for_session = current_card.to_dict()

    if cliente_associado:
        card_data_for_session['cpf'] = cliente_associado.CPF
        card_data_for_session['name'] = cliente_associado.NM_CLIENTE
        card_data_for_session['email'] = cliente_associado.EMAIL
        card_data_for_session['phone'] = cliente_associado.TELEFONE
        card_data_for_session['birth_date'] = cliente_associado.DT_NASC.strftime('%Y-%m-%d')
        card_data_for_session['register_date'] = cliente_associado.DT_CADASTRO.strftime('%Y-%m-%d') if cliente_associado.DT_CADASTRO else None # Passa a data de cadastro real
        card_data_for_session['type'] = current_card.tipo_cartao.DESC_CARTAO if current_card.tipo_cartao else None
    else:
        card_data_for_session['cpf'] = None
        card_data_for_session['name'] = "N/A"
        card_data_for_session['email'] = "N/A"
        card_data_for_session['phone'] = "N/A"
        card_data_for_session['birth_date'] = "N/A"
        card_data_for_session['register_date'] = None # Não há data de cadastro sem cliente
        card_data_for_session['type'] = current_card.tipo_cartao.DESC_CARTAO if current_card.tipo_cartao else None

    card_data_for_session['pending'] = session['card_data'].get('pending', 0.00)

    if 'entry_date' in session['card_data']:
        card_data_for_session['entry_date'] = session['card_data']['entry_date']
    else:
        card_data_for_session['entry_date'] = datetime.datetime.now().isoformat()

    session['card_data'] = card_data_for_session
    return jsonify({"success": True, "data": session['card_data']})

@app.route('/api/generate-card-number', methods=['GET'])
def generate_card_number():
    while True:
        card_number = random.randint(1000, 9999)
        existing_card = Cartao.query.get(card_number)
        if not existing_card:
            break
    return jsonify({"success": True, "card_number": card_number})

@app.route('/api/simulate-active-card', methods=['GET'])
def simulate_active_card():
    all_cards = Cartao.query.all()
    if not all_cards:
        return jsonify({"success": False, "message": "Nenhum cartão cadastrado para simular"}), 404

    card_from_db = random.choice(all_cards)
    cliente_associado = card_from_db.clientes[0] if card_from_db.clientes else None

    if not cliente_associado:
        return jsonify({"success": False, "message": "Cartão simulado não tem cliente associado. Simule um cartão com cliente ou crie um novo."}), 400

    card_data_for_session = card_from_db.to_dict()
    card_data_for_session['cpf'] = cliente_associado.CPF
    card_data_for_session['name'] = cliente_associado.NM_CLIENTE
    card_data_for_session['email'] = cliente_associado.EMAIL
    card_data_for_session['phone'] = cliente_associado.TELEFONE
    card_data_for_session['birth_date'] = cliente_associado.DT_NASC.strftime('%Y-%m-%d')
    card_data_for_session['register_date'] = cliente_associado.DT_CADASTRO.strftime('%Y-%m-%d') if cliente_associado.DT_CADASTRO else None
    card_data_for_session['type'] = card_from_db.tipo_cartao.DESC_CARTAO if card_from_db.tipo_cartao else None
    card_data_for_session['pending'] = 0.00

    card_data_for_session['entry_date'] = datetime.datetime.now().isoformat()
    session['card_data'] = card_data_for_session
    return jsonify({"success": True, "message": "Cartão ativo simulado com sucesso"})

@app.route('/api/check-client', methods=['POST'])
def check_client():
    data = request.json
    if 'cpf' not in data:
        return jsonify({"success": False, "message": "CPF não fornecido"}), 400

    if not validar_cpf(data['cpf']):
        return jsonify({"success": False, "message": "CPF inválido"}), 400

    cpf_limpo = re.sub(r'[^0-9]', '', data['cpf'])

    existing_client = Cliente.query.filter_by(CPF=cpf_limpo).first()

    if existing_client:
        if existing_client.cartoes:
            cartao_associado = existing_client.cartoes[0]
            card_data_for_session = cartao_associado.to_dict()
            card_data_for_session['cpf'] = existing_client.CPF
            card_data_for_session['name'] = existing_client.NM_CLIENTE
            card_data_for_session['email'] = existing_client.EMAIL
            card_data_for_session['phone'] = existing_client.TELEFONE
            card_data_for_session['birth_date'] = existing_client.DT_NASC.strftime('%Y-%m-%d')
            card_data_for_session['register_date'] = existing_client.DT_CADASTRO.strftime('%Y-%m-%d') if existing_client.DT_CADASTRO else None
            card_data_for_session['type'] = cartao_associado.tipo_cartao.DESC_CARTAO if cartao_associado.tipo_cartao else None
            card_data_for_session['pending'] = 0.00

            card_data_for_session['entry_date'] = datetime.datetime.now().isoformat()
            session['card_data'] = card_data_for_session
            return jsonify({"success": True, "client_exists": True, "message": "Cliente e cartão encontrados"})
        else:
            return jsonify({"success": True, "client_exists": True, "message": "Cliente encontrado, mas sem cartão associado. Prossiga para ativação."})
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

    cpf_limpo = re.sub(r'[^0-9]', '', data['cpf'])
    telefone_limpo = re.sub(r'[^0-9]', '', data['phone'])

    existing_client = Cliente.query.filter_by(CPF=cpf_limpo).first()

    if existing_client:
        if existing_client.cartoes:
            cartao_associado = existing_client.cartoes[0]
            card_data_for_session = cartao_associado.to_dict()
            card_data_for_session['cpf'] = existing_client.CPF
            card_data_for_session['name'] = existing_client.NM_CLIENTE
            card_data_for_session['email'] = existing_client.EMAIL
            card_data_for_session['phone'] = existing_client.TELEFONE
            card_data_for_session['birth_date'] = existing_client.DT_NASC.strftime('%Y-%m-%d')
            card_data_for_session['register_date'] = existing_client.DT_CADASTRO.strftime('%Y-%m-%d') if existing_client.DT_CADASTRO else None
            card_data_for_session['type'] = cartao_associado.tipo_cartao.DESC_CARTAO if cartao_associado.tipo_cartao else None
            card_data_for_session['pending'] = 0.00
            card_data_for_session['entry_date'] = datetime.datetime.now().isoformat()
            session['card_data'] = card_data_for_session
            return jsonify({"success": True, "message": "Cliente já existe e possui cartão, redirecionando", "redirect": True})

    existing_card = Cartao.query.get(int(data['card_number']))
    if existing_card:
        return jsonify({"success": False, "message": "Número de cartão já está em uso"}), 400

    if not validar_idade(data['birth_date']):
        return jsonify({"success": False, "message": "Cliente deve ter pelo menos 18 anos"}), 400

    try:
        tipo_cartao_db = TipoDeCartao.query.filter_by(DESC_CARTAO=data['card_type']).first()
        if not tipo_cartao_db:
            return jsonify({"success": False, "message": f"Tipo de cartão '{data['card_type']}' inválido ou não cadastrado"}), 400

        if not existing_client:
            # Não gera ID para Cliente, o DB fará isso (IDENTITY)
            new_client = Cliente(
                NM_CLIENTE=data['name'],
                CPF=cpf_limpo,
                DT_NASC=datetime.datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
                EMAIL=data['email'],
                TELEFONE=telefone_limpo,
                # DT_CADASTRO terá o DEFAULT GETDATE() do DB
                FK_ID_GENERO=None # Ou a lógica para definir o gênero
            )
            db.session.add(new_client)
            db.session.flush() # Para que new_client.ID_CLIENTE seja populado pelo DB
            cliente_a_associar = new_client
        else:
            cliente_a_associar = existing_client
            cliente_a_associar.EMAIL = data['email']
            cliente_a_associar.TELEFONE = telefone_limpo

        new_card = Cartao(
            ID_CARTAO=int(data['card_number']), # ID_CARTAO é gerado pelo Flask, não pelo DB
            DT_EMISSAO=datetime.date.today(),
            FK_ID_TP_CARTAO=tipo_cartao_db.ID_TP_CARTAO
        )
        db.session.add(new_card)
        db.session.flush()

        # Não gera ID para Saldo, o DB fará isso (IDENTITY)
        new_saldo = Saldo(
            QTD_SALDO=0.00,
            FK_ID_CARTAO=new_card.ID_CARTAO
        )
        db.session.add(new_saldo)
        # db.session.flush() # Não necessário aqui, a menos que precise do ID_SALDO imediatamente

        new_card_client_association = CartaoCliente(
            FK_ID_CLIENTE=cliente_a_associar.ID_CLIENTE,
            FK_ID_CARTAO=new_card.ID_CARTAO
        )
        db.session.add(new_card_client_association)

        db.session.commit()

        card_data_for_session = new_card.to_dict()
        card_data_for_session['cpf'] = cliente_a_associar.CPF
        card_data_for_session['name'] = cliente_a_associar.NM_CLIENTE
        card_data_for_session['email'] = cliente_a_associar.EMAIL
        card_data_for_session['phone'] = cliente_a_associar.TELEFONE
        card_data_for_session['birth_date'] = cliente_a_associar.DT_NASC.strftime('%Y-%m-%d')
        card_data_for_session['register_date'] = cliente_a_associar.DT_CADASTRO.strftime('%Y-%m-%d') if cliente_a_associar.DT_CADASTRO else None
        card_data_for_session['type'] = tipo_cartao_db.DESC_CARTAO
        card_data_for_session['pending'] = 0.00

        card_data_for_session['entry_date'] = datetime.datetime.now().isoformat()
        session['card_data'] = card_data_for_session

        return jsonify({"success": True, "message": "Cartão ativado com sucesso"})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao ativar cartão: {e}")
        return jsonify({"success": False, "message": f"Erro interno ao ativar cartão: {str(e)}"}), 500

@app.route('/api/recharge-card', methods=['POST'])
def recharge_card():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401

    data = request.json
    if 'amount' not in data or not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({"success": False, "message": "Valor de recarga inválido"}), 400

    card_id = session['card_data']['id_cartao']
    card_to_recharge = Cartao.query.get(card_id)

    if not card_to_recharge:
        return jsonify({"success": False, "message": "Cartão não encontrado no banco de dados"}), 404

    saldo_existente = Saldo.query.filter_by(FK_ID_CARTAO=card_id).first()

    if not saldo_existente:
        # Cria um novo registro de saldo se não existir para este cartão
        new_saldo = Saldo(
            QTD_SALDO=0.00,
            FK_ID_CARTAO=card_id
        )
        db.session.add(new_saldo)
        db.session.flush() # Necessário para que o objeto new_saldo seja gerenciado pelo DB antes de ser alterado
        saldo_existente = new_saldo # Atribui o novo saldo para a variável de trabalho

    saldo_existente.QTD_SALDO += data['amount']
    db.session.commit()

    updated_card_data = card_to_recharge.to_dict()
    updated_card_data['balance'] = float(saldo_existente.QTD_SALDO)

    cliente_associado = card_to_recharge.clientes[0] if card_to_recharge.clientes else None
    if cliente_associado:
        updated_card_data['cpf'] = cliente_associado.CPF
        updated_card_data['name'] = cliente_associado.NM_CLIENTE
        updated_card_data['email'] = cliente_associado.EMAIL
        updated_card_data['phone'] = cliente_associado.TELEFONE
        updated_card_data['birth_date'] = cliente_associado.DT_NASC.strftime('%Y-%m-%d')
        updated_card_data['register_date'] = cliente_associado.DT_CADASTRO.strftime('%Y-%m-%d') if cliente_associado.DT_CADASTRO else None
    else:
        updated_card_data['cpf'] = session['card_data'].get('cpf')
        updated_card_data['name'] = session['card_data'].get('name')
        updated_card_data['email'] = session['card_data'].get('email')
        updated_card_data['phone'] = session['card_data'].get('phone')
        updated_card_data['birth_date'] = session['card_data'].get('birth_date')
        updated_card_data['register_date'] = session['card_data'].get('register_date')

    updated_card_data['type'] = card_to_recharge.tipo_cartao.DESC_CARTAO if card_to_recharge.tipo_cartao else session['card_data'].get('type')
    updated_card_data['pending'] = session['card_data'].get('pending', 0.00)

    updated_card_data['entry_date'] = session['card_data'].get('entry_date', datetime.datetime.now().isoformat())

    session['card_data'] = updated_card_data

    return jsonify({"success": True, "message": "Cartão recarregado com sucesso", "new_balance": float(saldo_existente.QTD_SALDO)})

@app.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401

    if 'pending' in session['card_data']:
        session['card_data']['pending'] = 0.00

    return jsonify({"success": True, "message": "Pagamento confirmado com sucesso (lógica de persistência de pagamentos deve ser implementada)"})

@app.route('/api/end-session', methods=['POST'])
def end_session():
    if 'card_data' in session:
        session.pop('card_data')
    return jsonify({"success": True, "message": "Sessão encerrada com sucesso"})

@app.route('/api/change-card-type', methods=['POST'])
def change_card_type():
    if 'card_data' not in session:
        return jsonify({"success": False, "message": "Nenhum cartão ativo na sessão"}), 401

    card_id = session['card_data']['id_cartao']
    card_to_update = Cartao.query.get(card_id)

    if not card_to_update:
        return jsonify({"success": False, "message": "Cartão não encontrado no banco de dados"}), 404

    current_type_desc = card_to_update.tipo_cartao.DESC_CARTAO if card_to_update.tipo_cartao else ''
    new_type_desc = 'pos' if current_type_desc == 'pre' else 'pre'

    new_type_db = TipoDeCartao.query.filter_by(DESC_CARTAO=new_type_desc).first()

    if not new_type_db:
        return jsonify({"success": False, "message": f"Tipo de cartão '{new_type_desc}' não configurado no banco de dados."}), 500

    card_to_update.FK_ID_TP_CARTAO = new_type_db.ID_TP_CARTAO
    db.session.commit()

    updated_card_data = card_to_update.to_dict()

    cliente_associado = card_to_update.clientes[0] if card_to_update.clientes else None
    if cliente_associado:
        updated_card_data['cpf'] = cliente_associado.CPF
        updated_card_data['name'] = cliente_associado.NM_CLIENTE
        updated_card_data['email'] = cliente_associado.EMAIL
        updated_card_data['phone'] = cliente_associado.TELEFONE
        updated_card_data['birth_date'] = cliente_associado.DT_NASC.strftime('%Y-%m-%d')
        updated_card_data['register_date'] = cliente_associado.DT_CADASTRO.strftime('%Y-%m-%d') if cliente_associado.DT_CADASTRO else None
    else:
        updated_card_data['cpf'] = session['card_data'].get('cpf')
        updated_card_data['name'] = session['card_data'].get('name')
        updated_card_data['email'] = session['card_data'].get('email')
        updated_card_data['phone'] = session['card_data'].get('phone')
        updated_card_data['birth_date'] = session['card_data'].get('birth_date')
        updated_card_data['register_date'] = session['card_data'].get('register_date')

    updated_card_data['type'] = new_type_db.DESC_CARTAO
    updated_card_data['pending'] = session['card_data'].get('pending', 0.00)

    updated_card_data['entry_date'] = session['card_data'].get('entry_date', datetime.datetime.now().isoformat())

    session['card_data'] = updated_card_data

    return jsonify({"success": True, "message": "Tipo de cartão alterado com sucesso", "new_type": new_type_desc})

if __name__ == '__main__':
    app.run(debug=True)