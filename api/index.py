import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# SEGURANÇA: Chave para as sessões de login
app.secret_key = os.getenv("SECRET_KEY", "chave_mestra_123")

# BANCO DE DADOS: Prioriza a variável da Vercel, mas tem a sua URL como reserva
URL_RESERVA = "mongodb+srv://adersonsoliveira55_db_user:MqSM10DQ5YNhyOpB@contasemdia.9iqz23o.mongodb.net/?appName=ContasEmDia"
MONGO_URI = os.getenv("MONGO_URI", URL_RESERVA)

client = MongoClient(MONGO_URI)
db = client.get_database('conta_em_dia_db')
contas_col = db.contas

# SENHA DO SITE (Mude aqui se quiser)
SENHA_SISTEMA = "1234"


# --- PROTEÇÃO ---
@app.before_request
def verificar_acesso():
    rotas_abertas = ['login', 'static']
    if 'logado' not in session and request.endpoint not in rotas_abertas:
        return redirect(url_for('login'))


# --- ROTAS DE ACESSO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        if request.form.get('senha') == SENHA_SISTEMA:
            session['logado'] = True
            return redirect(url_for('index'))
        erro = "Senha incorreta!"
    return render_template('login.html', erro=erro)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ROTAS FINANCEIRAS ---
@app.route('/')
def index():
    # Busca todas as contas e ordena pela data de vencimento
    contas = list(contas_col.find().sort("vencimento", 1))
    return render_template('index.html', contas=contas)


@app.route('/add', methods=['POST'])
def add():
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor').replace(',', '.'))
    vencimento_str = request.form.get('vencimento')

    nova_conta = {
        "descricao": descricao,
        "valor": valor,
        "vencimento": datetime.strptime(vencimento_str, '%Y-%m-%d'),
        "pago": False
    }
    contas_col.insert_one(nova_conta)
    return redirect(url_for('index'))


@app.route('/pagar/<id>')
def pagar(id):
    contas_col.update_one({"_id": ObjectId(id)}, {"$set": {"pago": True}})
    return redirect(url_for('index'))


@app.route('/deletar/<id>')
def deletar(id):
    contas_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))