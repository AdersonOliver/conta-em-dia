import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv("SECRET_KEY", "chave_mestra_123")

URL_RESERVA = "mongodb+srv://adersonsoliveira55_db_user:MqSM10DQ5YNhyOpB@contasemdia.9iqz23o.mongodb.net/?appName=ContasEmDia"
MONGO_URI = os.getenv("MONGO_URI", URL_RESERVA)

client = MongoClient(MONGO_URI)
db = client.get_database('conta_em_dia_db')
movimentacoes_col = db.contas  # Mantive o nome da coleção para não perder seus dados

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


@app.route('/')
def index():
    # Busca todas as movimentações
    movimentacoes = list(movimentacoes_col.find().sort("vencimento", 1))

    total_entradas = 0
    total_saidas = 0

    for item in movimentacoes:
        # Se não tiver o campo 'tipo', assumimos que é 'saida' (pelas contas antigas)
        tipo = item.get('tipo', 'saida')
        valor = item.get('valor', 0)

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
    tipo = request.form.get('tipo')  # Novo campo: entrada ou saida

    nova_movimentacao = {
        "descricao": descricao,
        "valor": valor,
        "vencimento": datetime.strptime(vencimento_str, '%Y-%m-%d'),
        "tipo": tipo,
        "pago": False
    }
    movimentacoes_col.insert_one(nova_movimentacao)
    return redirect(url_for('index'))

# ... (Mantenha as rotas /pagar e /deletar como estão)