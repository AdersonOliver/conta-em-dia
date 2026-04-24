import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv("SECRET_KEY", "chave_fluxo_mensal_2026")

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
    # Lógica de Filtro por Mês e Ano
    hoje = datetime.now()
    mes_sel = int(request.args.get('mes', hoje.month))
    ano_sel = int(request.args.get('ano', hoje.year))

    # Define o intervalo do mês para a consulta no MongoDB
    inicio_mes = datetime(ano_sel, mes_sel, 1)
    if mes_sel == 12:
        fim_mes = datetime(ano_sel + 1, 1, 1)
    else:
        fim_mes = datetime(ano_sel, mes_sel + 1, 1)

    query = {"vencimento": {"$gte": inicio_mes, "$lt": fim_mes}}
    movimentacoes = list(movimentacoes_col.find(query).sort("vencimento", 1))

    total_entradas = sum(item.get('valor', 0) for item in movimentacoes if item.get('tipo') == 'entrada')
    total_saidas = sum(item.get('valor', 0) for item in movimentacoes if item.get('tipo') == 'saida')
    saldo = total_entradas - total_saidas

    meses_nome = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    return render_template('index.html',
                           movimentacoes=movimentacoes,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           saldo=saldo,
                           mes_atual=mes_sel,
                           ano_atual=ano_sel,
                           meses_nome=meses_nome)


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
    # Redireciona para o mês do lançamento feito
    data_obj = datetime.strptime(vencimento_str, '%Y-%m-%d')
    return redirect(url_for('index', mes=data_obj.month, ano=data_obj.year))


@app.route('/pagar/<id>')
def pagar(id):
    movimentacoes_col.update_one({"_id": ObjectId(id)}, {"$set": {"pago": True}})
    return redirect(request.referrer or url_for('index'))


@app.route('/deletar/<id>')
def deletar(id):
    movimentacoes_col.delete_one({"_id": ObjectId(id)})
    return redirect(request.referrer or url_for('index'))