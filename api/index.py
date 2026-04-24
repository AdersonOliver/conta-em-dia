import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv("SECRET_KEY", "chave_segura_fluxo_2026")

# CONEXÃO BANCO
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
    try:
        hoje = datetime.now()
        mes_sel = int(request.args.get('mes', hoje.month))
        ano_sel = int(request.args.get('ano', hoje.year))

        inicio_mes = datetime(ano_sel, mes_sel, 1)
        if mes_sel == 12:
            fim_mes = datetime(ano_sel + 1, 1, 1)
        else:
            fim_mes = datetime(ano_sel, mes_sel + 1, 1)

        query = {"vencimento": {"$gte": inicio_mes, "$lt": fim_mes}}
        movimentacoes = list(movimentacoes_col.find(query).sort("vencimento", 1))

        # SOMA SEGURA (Ignora valores nulos ou tipos errados)
        total_entradas = 0
        total_saidas = 0
        for item in movimentacoes:
            v = item.get('valor', 0)
            if not isinstance(v, (int, float)): v = 0  # Segurança extra

            if item.get('tipo') == 'entrada':
                total_entradas += v
            else:
                total_saidas += v

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
    except Exception as e:
        return f"Erro no servidor: {str(e)}"  # Mostra o erro na tela para facilitar


@app.route('/add', methods=['POST'])
def add():
    try:
        descricao = request.form.get('descricao')
        valor_raw = request.form.get('valor', '0').replace(',', '.')
        valor = float(valor_raw) if valor_raw else 0.0
        vencimento_str = request.form.get('vencimento')
        tipo = request.form.get('tipo', 'saida')

        nova_mov = {
            "descricao": descricao,
            "valor": valor,
            "vencimento": datetime.strptime(vencimento_str, '%Y-%m-%d'),
            "tipo": tipo,
            "pago": False
        }
        movimentacoes_col.insert_one(nova_mov)
        data_obj = datetime.strptime(vencimento_str, '%Y-%m-%d')
        return redirect(url_for('index', mes=data_obj.month, ano=data_obj.year))
    except:
        return redirect(url_for('index'))


@app.route('/pagar/<id>')
def pagar(id):
    movimentacoes_col.update_one({"_id": ObjectId(id)}, {"$set": {"pago": True}})
    return redirect(request.referrer or url_for('index'))


@app.route('/deletar/<id>')
def deletar(id):
    movimentacoes_col.delete_one({"_id": ObjectId(id)})
    return redirect(request.referrer or url_for('index'))