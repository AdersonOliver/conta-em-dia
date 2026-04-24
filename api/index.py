import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv("SECRET_KEY", "fluxo_caixa_2026_key")

# CONEXÃO COM O BANCO
URL_RESERVA = "mongodb+srv://adersonsoliveira55_db_user:MqSM10DQ5YNhyOpB@contasemdia.9iqz23o.mongodb.net/?appName=ContasEmDia"
MONGO_URI = os.getenv("MONGO_URI", URL_RESERVA)
client = MongoClient(MONGO_URI)
db = client.get_database('conta_em_dia_db')
movimentacoes_col = db.contas

SENHA_SISTEMA = "1234"


@app.before_request
def verificar_acesso():
    if 'logado' not in session and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))


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


@app.route('/')
def index():
    movimentacoes = list(movimentacoes_col.find().sort("vencimento", 1))

    total_entradas = 0
    total_saidas = 0

    for item in movimentacoes:
        valor = item.get('valor', 0)
        tipo = item.get('tipo', 'saida')
        if tipo == 'entrada':
            total_entradas += valor
        else:
            total_saidas += valor

    saldo = total_entradas - total_saidas

    return render_template('index.html',
                           movimentacoes=movimentacoes,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           saldo=saldo)


@app.route('/add', methods=['POST'])
def add():
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor').replace(',', '.'))
    vencimento_str = request.form.get('vencimento')
    tipo = request.form.get('tipo')

    nova_mov = {
        "descricao": descricao,
        "valor": valor,
        "vencimento": datetime.strptime(vencimento_str, '%Y-%m-%d'),
        "tipo": tipo,
        "pago": False
    }
    movimentacoes_col.insert_one(nova_mov)
    return redirect(url_for('index'))


@app.route('/pagar/<id>')
def pagar(id):
    movimentacoes_col.update_one({"_id": ObjectId(id)}, {"$set": {"pago": True}})
    return redirect(url_for('index'))


@app.route('/deletar/<id>')
def deletar(id):
    movimentacoes_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))