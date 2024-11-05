from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from models.clustering import criar_clusters, get_cluster_data
from models.prediction_model import train_model, predict_potential_users, sugerir_clusters_para_usuarios, get_or_create_analysis
from database.database import create_connection
import pandas as pd
from sqlalchemy import text, Table, Column, Integer, ForeignKey, MetaData, DateTime, Text
from datetime import datetime
import secrets
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

metadata = MetaData()

analises_usuario_cluster = Table(
    'analises_usuario_cluster', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), nullable=False),
    Column('cluster_id', Integer, ForeignKey('cluster_names.cluster_id'), nullable=False),
    Column('analise', Text, nullable=False),
    Column('data_analise', DateTime, default=datetime.utcnow)
)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/view_clusters')
def view_clusters():
    engine = create_connection()
    query = """
        SELECT cn.cluster_id, cn.nome, cn.ticket_medio, cn.intervalo_dias, COUNT(c.usuario_id) AS num_usuarios
        FROM cluster_names cn
        LEFT JOIN clusters c ON cn.cluster_id = c.cluster_id
        GROUP BY cn.cluster_id
    """
    clusters = pd.read_sql(query, engine)
    clusters = clusters.to_dict(orient='records')
    return render_template('view_clusters.html', clusters=clusters)

@app.route('/add_cluster', methods=['GET', 'POST'])
def add_cluster():
    if request.method == 'POST':
        nome = request.form['nome']
        ticket_medio = float(request.form['ticket_medio'])
        intervalo_dias = int(request.form['intervalo_dias'])
        engine = create_connection()
        query = text("""
            INSERT INTO cluster_names (nome, ticket_medio, intervalo_dias) 
            VALUES (:nome, :ticket_medio, :intervalo_dias)
        """)
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(query, {"nome": nome, "ticket_medio": ticket_medio, "intervalo_dias": intervalo_dias})
                cluster_id = connection.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                
                if cluster_id:
                    transaction.commit()
                    criar_clusters(cluster_id, nome, ticket_medio, intervalo_dias)
                else:
                    transaction.rollback()
            except Exception as e:
                transaction.rollback()
                flash(f"Erro ao criar o cluster: {str(e)}", "danger")
        return redirect(url_for('view_clusters'))
    return render_template('add_cluster.html')

@app.route('/edit_cluster_name', methods=['POST'])
def edit_cluster_name():
    cluster_id = request.form['cluster_id']
    novo_nome = request.form['novo_nome']
    engine = create_connection()
    query = text("UPDATE cluster_names SET nome = :novo_nome WHERE cluster_id = :cluster_id")
    with engine.connect() as connection:
        connection.execute(query, {"novo_nome": novo_nome, "cluster_id": cluster_id})
    return redirect(url_for('view_clusters'))

@app.route('/update_cluster', methods=['GET'])
def update_cluster():
    train_model()
    potential_users = predict_potential_users()
    engine = create_connection()
    clusters_query = "SELECT cluster_id, nome FROM cluster_names"
    clusters = pd.read_sql(clusters_query, engine)
    clusters = clusters.to_dict(orient='records')
    return render_template('suggest_users.html', suggestions=potential_users, clusters=clusters)

@app.route('/sugerir_clusters')
def sugerir_clusters():
    sugestoes = sugerir_clusters_para_usuarios()
    return render_template('suggest_users.html', sugestoes=sugestoes)

@app.route('/get_analysis', methods=['POST'])
def get_analysis():
    data = request.get_json()
    usuario_id = data['usuario_id']
    cluster_id = data['cluster_id']
    engine = create_connection()
    
    query_usuario = text("SELECT nome, ticket_medio, intervalo_dias FROM usuarios WHERE id = :usuario_id")
    query_cluster = text("SELECT nome, ticket_medio, intervalo_dias FROM cluster_names WHERE cluster_id = :cluster_id")
    
    with engine.connect() as connection:
        usuario = connection.execute(query_usuario, {"usuario_id": usuario_id}).fetchone()
        cluster = connection.execute(query_cluster, {"cluster_id": cluster_id}).fetchone()
    
    if usuario and cluster:
        usuario_info = {
            "nome": usuario._mapping['nome'],
            "ticket_medio": usuario._mapping['ticket_medio'],
            "intervalo_dias": usuario._mapping['intervalo_dias']
        }
        cluster_info = {
            "nome": cluster._mapping['nome'],
            "ticket_medio": cluster._mapping['ticket_medio'],
            "intervalo_dias": cluster._mapping['intervalo_dias']
        }
        
        with engine.connect() as connection:
            existing_analysis = connection.execute(
                select(analises_usuario_cluster.c.analise)
                .where(analises_usuario_cluster.c.usuario_id == usuario_id)
                .where(analises_usuario_cluster.c.cluster_id == cluster_id)
            ).fetchone()
        
        if existing_analysis:
            analise = existing_analysis.analise
        else:
            analise = get_or_create_analysis(usuario_id, cluster_id, usuario_info, cluster_info)
            insert_analysis_query = insert(analises_usuario_cluster).values(
                usuario_id=usuario_id,
                cluster_id=cluster_id,
                analise=analise,
                data_analise=datetime.utcnow()
            )
            with engine.connect() as connection:
                connection.execute(insert_analysis_query)

        return jsonify({
            "analise": analise,
            "usuario_nome": usuario_info["nome"],
            "usuario_ticket_medio": usuario_info["ticket_medio"],
            "cluster_nome": cluster_info["nome"],
            "cluster_ticket_medio": cluster_info["ticket_medio"]
        })
    return jsonify({"error": "Dados de usuário ou cluster não encontrados"}), 404

@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    user_id = request.form['user_id']
    cluster_id = request.form['cluster_id']
    pertence_ao_cluster = request.form['pertence_ao_cluster'].lower() == 'true'
    engine = create_connection()
    usuario_query = text("SELECT ticket_medio, intervalo_dias FROM usuarios WHERE id = :user_id")
    
    with engine.connect() as connection:
        usuario = connection.execute(usuario_query, {"user_id": user_id}).fetchone()
    
    if usuario:
        ticket_medio = usuario['ticket_medio']
        intervalo_dias = usuario['intervalo_dias']
        feedback_query = text("""
            INSERT INTO cluster_feedback (usuario_id, cluster_id, ticket_medio, intervalo_dias, pertence_ao_cluster) 
            VALUES (:usuario_id, :cluster_id, :ticket_medio, :intervalo_dias, :pertence_ao_cluster)
        """)
        with engine.connect() as connection:
            connection.execute(feedback_query, {
                "usuario_id": user_id,
                "cluster_id": cluster_id,
                "ticket_medio": ticket_medio,
                "intervalo_dias": intervalo_dias,
                "pertence_ao_cluster": pertence_ao_cluster
            })
    return redirect(url_for('update_cluster'))

@app.route('/add_user_to_cluster', methods=['POST'])
def add_user_to_cluster():
    try:
        user_id = int(request.form['user_id'])
        cluster_id = int(request.form['cluster_id'])
        engine = create_connection()

        query_check = text("SELECT 1 FROM cluster_names WHERE cluster_id = :cluster_id")
        with engine.connect() as connection:
            result = connection.execute(query_check, {"cluster_id": cluster_id}).fetchone()
            if result is None:
                flash(f"Erro: o cluster_id {cluster_id} não existe.", "danger")
                return jsonify({"success": False, "error": "Cluster não encontrado"})
        
        query_insert = text("""
            INSERT INTO clusters (cluster_id, usuario_id, update_date)
            VALUES (:cluster_id, :user_id, :update_date)
        """)

        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(query_insert, {
                    "cluster_id": cluster_id,
                    "user_id": user_id,
                    "update_date": datetime.now().strftime('%Y-%m-%d')
                })
                transaction.commit()
                flash("Usuário adicionado ao cluster com sucesso.", "success")
                return jsonify({"success": True, "user_id": user_id, "cluster_id": cluster_id})
            except Exception as e:
                transaction.rollback()
                flash(f"Erro ao adicionar usuário ao cluster: {str(e)}", "danger")
                return jsonify({"success": False, "error": str(e)})
    except ValueError:
        flash("Erro: IDs de usuário ou cluster inválidos.", "danger")
        return jsonify({"success": False, "error": "IDs inválidos"})

@app.route('/gerar_campanha', methods=['GET', 'POST'])
def gerar_campanha():
    engine = create_connection()

    if request.method == 'POST':
        data = request.get_json()
        cluster_id = data.get('cluster_id')
        produtos = data.get('produtos', [])
        cluster_data = get_cluster_data(cluster_id)
        prompt = f"""
        Você é um especialista em marketing digital. Crie uma campanha promocional para o cluster '{cluster_data['nome']}', que tem um ticket médio de {cluster_data['ticket_medio']} e uma frequência de compra de {cluster_data['intervalo_dias']} dias.
        Os produtos principais são: {', '.join(produtos)}. Destaque suas vantagens e incentive a fidelização.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "Você é um especialista em marketing."},
                          {"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            campanha_gerada = response['choices'][0]['message']['content'].strip()
            return jsonify({"success": True, "campanha": campanha_gerada})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    produtos_cluster = {
        1: ["Geladeira Side-by-Side", "Forno Elétrico Premium", "Máquina de Lavar Roupa Avançada", "Fogão Gourmet"],
        2: ["Aspirador de Pó Inteligente", "Secadora de Roupas Digital", "Micro-ondas com Convecção", "Liquidificador de Alta Potência"],
        3: ["Purificador de Água de Alta Qualidade", "Cafeteira Expresso Automática", "Lava-louças Silenciosa", "Aquecedor de Ambiente Eficiente"],
        4: ["Ar Condicionado Split Inverter", "Chaleira Elétrica Rápida", "Torradeira com Controle Digital", "Exaustor Ultra Silencioso"],
    }
    
    query = "SELECT cluster_id, nome FROM cluster_names"
    clusters = []
    with engine.connect() as connection:
        result = connection.execute(text(query))
        clusters = [{"cluster_id": row[0], "nome": row[1], "produtos": produtos_cluster.get(row[0], ["Geladeira Side-by-Side", "Ar Condicionado Split Inverter", "Chaleira Elétrica Rápida", "Torradeira com Controle Digital", "Exaustor Ultra Silencioso"])} for row in result]

    return render_template('gerar_campanha.html', clusters=clusters)

@app.route('/get_cluster_users/<int:cluster_id>')
def get_cluster_users(cluster_id):
    engine = create_connection()
    query = """
        SELECT u.id, u.nome, u.idade, u.cidade, u.ticket_medio, u.intervalo_dias
        FROM usuarios u
        JOIN clusters c ON u.id = c.usuario_id
        WHERE c.cluster_id = :cluster_id
    """
    users = pd.read_sql(text(query), engine, params={"cluster_id": cluster_id})
    return jsonify(users.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
