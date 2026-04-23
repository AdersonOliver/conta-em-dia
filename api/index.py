import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Conexão com MongoDB (Use sua URI do Atlas aqui para testar local)
MONGO_URI = "mongodb+srv://adersonsoliveira55_db_user:MqSM10DQ5YNhyOpB@contasemdia.9iqz23o.mongodb.net/?appName=ContasEmDia"
client = MongoClient(MONGO_URI)
db = client.get_database('conta_em_dia_db')
contas_col = db.contas


@app.route('/')
def index():
    # Busca contas e ordena por data de vencimento (1 = ascendente)
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


# Para o Vercel
app = app