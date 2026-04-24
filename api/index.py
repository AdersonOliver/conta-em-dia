import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# CHAVE DE SEGURANÇA: Necessária para usar 'session'.
# No Vercel, você pode adicionar uma variável chamada SECRET_KEY.
app.secret_key = os.getenv("SECRET_KEY", "chave-secreta-muito-dificil-123")

# CONEXÃO MONGODB: Lendo da variável de ambiente que configuramos na Vercel
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database('conta_em_dia_db')
contas_col = db.contas

# SENHA DE ACESSO: A senha que você e sua esposa vão digitar (pode mudar aqui)
SENHA_SISTEMA = "1234"


# --- PROTEÇÃO DE ACESSO ---
@app.before_request
def verificar_acesso():
    # Rotas que NÃO precisam de login: a página de login e os arquivos CSS/Imagens
    rotas_abertas = ['login', 'static']

    if 'logado' not in session and request.endpoint not in rotas_abertas:
        return render_template('login.html')


# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        if senha_digitada == SENHA_SISTEMA:
            session['logado'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro="Senha incorreta!")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))


# --- ROTAS DO SISTEMA ---
@app.route('/')
def index():
    contas = list(contas_col.find().sort("vencimento", 1))
    return render_template('index.html', contas=contas)


@app.route('/add', methods=['POST'])
def add():
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor'))
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