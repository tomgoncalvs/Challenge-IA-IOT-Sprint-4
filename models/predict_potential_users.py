import os
import openai
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from database.database import create_connection
from datetime import datetime
from sqlalchemy import text
from dotenv import load_dotenv

# Carrega a chave de API do ChatGPT
load_dotenv()
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

def generate_analysis_text(usuario, cluster):
    prompt = (
        f"Analise o usuário {usuario['nome']} com ticket médio de {usuario['ticket_medio']} e intervalo de dias de "
        f"{usuario['intervalo_dias']}. O cluster sugerido é '{cluster['nome']}', que exige um ticket médio mínimo de "
        f"{cluster['ticket_medio']} e um intervalo máximo de {cluster['intervalo_dias']} dias. "
        f"Explique por que este usuário é um bom candidato para este cluster em até 100 caracteres."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    analysis_text = response.choices[0].message['content'].strip()
    return analysis_text

def get_or_create_analysis(usuario_id, cluster_id, usuario, cluster):
    # Verifica se as IDs estão presentes
    if not usuario_id or not cluster_id:
        print("Erro: ID do usuário ou do cluster está ausente.")
        print(f"Dados do usuário: {usuario}")
        print(f"Dados do cluster: {cluster}")
        return "ID do usuário ou do cluster ausente."

    engine = create_connection()
    
    # Verifica se a análise já existe para o usuário e o cluster
    query_check = text("""
        SELECT analise FROM analises_usuario_cluster
        WHERE usuario_id = :usuario_id AND cluster_id = :cluster_id
    """)
    
    with engine.connect() as connection:
        result = connection.execute(query_check, {"usuario_id": usuario_id, "cluster_id": cluster_id}).fetchone()
        
        if result:
            return result['analise']
        else:
            # Gera uma nova análise, caso não exista
            prompt = (
                f"Como especialista em CRM, analise o usuário '{usuario['nome']}' e o cluster '{cluster['nome']}'. "
                f"Explique o motivo da sugestão para esse cluster, as características que o tornam um bom candidato, "
                f"e forneça uma estimativa sobre o potencial de compras futuras do usuário. "
                f"Dados do usuário: Ticket Médio = {usuario['ticket_medio']}, Intervalo de Dias = {usuario['intervalo_dias']}. "
                f"Requisitos do Cluster: Ticket Médio = {cluster['ticket_medio']}, Intervalo de Dias = {cluster['intervalo_dias']}."
            )

            try:
                response = openai.Completion.create(
                    engine="gpt-4",
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.7
                )
                analise = response.choices[0].text.strip()[:150]  # Limita a 150 caracteres

                # Armazena a nova análise no banco de dados
                insert_query = text("""
                    INSERT INTO analises_usuario_cluster (usuario_id, cluster_id, analise, data_analise)
                    VALUES (:usuario_id, :cluster_id, :analise, :data_analise)
                """)
                connection.execute(insert_query, {
                    "usuario_id": usuario_id,
                    "cluster_id": cluster_id,
                    "analise": analise,
                    "data_analise": datetime.now()
                })
                
                return analise
            except Exception as e:
                print(f"Erro ao gerar análise com ChatGPT: {e}")
                return "Análise indisponível no momento."


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
                analise = get_or_create_analysis(usuario_id, cluster_id, usuario, cluster)
                
                sugestoes.append({
                    "usuario_id": usuario_id,
                    "usuario_nome": usuario_nome,
                    "cluster_id": cluster_id,
                    "cluster_nome": cluster_nome,
                    "analise": analise,
                    "usuario_ticket_medio": usuario_ticket_medio,
                    "cluster_ticket_medio": cluster_ticket_medio,
                    "usuario_intervalo_dias": usuario_intervalo_dias,
                    "cluster_intervalo_dias": cluster_intervalo_dias
                })
    
    return sugestoes
