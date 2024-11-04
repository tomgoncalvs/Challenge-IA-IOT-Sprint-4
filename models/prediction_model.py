import os
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from database.database import create_connection
from datetime import datetime
from sqlalchemy import text
import openai

# Configure a chave de API
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL_PATH = "modelo_cluster.pkl"

def load_data():
    engine = create_connection()
    query = """
        SELECT u.id, u.ticket_medio, u.intervalo_dias,
               COALESCE(cf.pertence_ao_cluster, 0) AS pertence_ao_cluster
        FROM usuarios u
        LEFT JOIN (
            SELECT usuario_id, MAX(pertence_ao_cluster) AS pertence_ao_cluster
            FROM cluster_feedback
            GROUP BY usuario_id
        ) cf ON u.id = cf.usuario_id
    """
    df = pd.read_sql(query, engine)
    print(f"Total de registros carregados: {len(df)}")
    return df

def train_model():
    df = load_data()
    X = df[['ticket_medio', 'intervalo_dias']]
    y = df['pertence_ao_cluster']
    
    model = RandomForestClassifier()
    model.fit(X, y)
    
    with open(MODEL_PATH, 'wb') as file:
        pickle.dump(model, file)
    
    print("Modelo treinado e salvo com sucesso!")

def load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as file:
            model = pickle.load(file)
        return model
    else:
        train_model()
        return load_model()

def predict_potential_users():
    engine = create_connection()
    
    clusters_query = """
        SELECT cluster_id, nome, ticket_medio, intervalo_dias
        FROM cluster_names
    """
    clusters_df = pd.read_sql(clusters_query, engine)
    
    usuarios_query = """
        SELECT u.id, u.nome, u.ticket_medio, u.intervalo_dias
        FROM usuarios u
        LEFT JOIN clusters c ON u.id = c.usuario_id
        WHERE c.cluster_id IS NULL
    """
    usuarios_df = pd.read_sql(usuarios_query, engine)
    
    sugestoes = []
    
    for _, usuario in usuarios_df.iterrows():
        usuario_id = usuario['id']
        usuario_nome = usuario['nome']
        usuario_ticket_medio = usuario['ticket_medio']
        usuario_intervalo_dias = usuario['intervalo_dias']
        
        for _, cluster in clusters_df.iterrows():
            cluster_id = cluster['cluster_id']
            cluster_nome = cluster['nome']
            cluster_ticket_medio = cluster['ticket_medio']
            cluster_intervalo_dias = cluster['intervalo_dias']
            
            if usuario_ticket_medio >= cluster_ticket_medio and usuario_intervalo_dias <= cluster_intervalo_dias:
                sugestoes.append({
                    "usuario_id": usuario_id,
                    "usuario_nome": usuario_nome,
                    "cluster_id": cluster_id,
                    "cluster_nome": cluster_nome,
                    "usuario_ticket_medio": usuario_ticket_medio,
                    "usuario_intervalo_dias": usuario_intervalo_dias,
                    "cluster_ticket_medio": cluster_ticket_medio,
                    "cluster_intervalo_dias": cluster_intervalo_dias
                })
    
    print("Sugestões de clusters geradas:", sugestoes)
    return sugestoes

def obter_ou_gerar_analise(usuario_id, cluster_id, usuario, cluster):
    if usuario_id is None or cluster_id is None:
        print("Erro: ID do usuário ou do cluster está ausente.")
        return "ID do usuário ou do cluster está ausente."

    engine = create_connection()
    
    query = text("""
        SELECT analise FROM analises_usuario_cluster 
        WHERE usuario_id = :usuario_id AND cluster_id = :cluster_id
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"usuario_id": usuario_id, "cluster_id": cluster_id}).fetchone()
    
    if result:
        return result['analise']
    
    # Caso contrário, gerar uma nova análise com o ChatGPT usando o endpoint de chat
    messages = [
        {
            "role": "system",
            "content": "Você é um especialista em CRM."
        },
        {
            "role": "user",
            "content": (
                f"Analise o usuário '{usuario['nome']}' e o cluster '{cluster['nome']}'. "
                f"Explique o motivo da sugestão para esse cluster, as características que o tornam um bom candidato, "
                f"e forneça uma estimativa sobre o potencial de compras futuras do usuário. "
                f"Dados do usuário: Ticket Médio = {usuario['ticket_medio']}, Intervalo de Dias = {usuario['intervalo_dias']}. "
                f"Requisitos do Cluster: Ticket Médio = {cluster['ticket_medio']}, Intervalo de Dias = {cluster['intervalo_dias']}. "
                "A análise deve ter no máximo 150 caracteres."
            )
        }
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        analise = response['choices'][0]['message']['content'].strip()
        
        insert_query = text("""
            INSERT INTO analises_usuario_cluster (usuario_id, cluster_id, analise)
            VALUES (:usuario_id, :cluster_id, :analise)
        """)
        with engine.connect() as connection:
            connection.execute(insert_query, {
                "usuario_id": usuario_id,
                "cluster_id": cluster_id,
                "analise": analise
            })
        
        return analise
    except Exception as e:
        print(f"Erro ao gerar análise com ChatGPT: {e}")
        return "Análise indisponível no momento."

def get_or_create_analysis(usuario_id, cluster_id, usuario, cluster):
    return obter_ou_gerar_analise(usuario_id, cluster_id, usuario, cluster)

def sugerir_clusters_para_usuarios():
    return predict_potential_users()
