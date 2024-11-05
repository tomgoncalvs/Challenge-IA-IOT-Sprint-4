import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database.database import create_connection

def criar_clusters(cluster_id, nome, ticket_medio, intervalo_dias):
    engine = create_connection()
    
    if engine is None:
        print("Não foi possível conectar ao banco.")
        return
    
    try:
        update_query = text("""
            UPDATE cluster_names 
            SET nome = :nome, ticket_medio = :ticket_medio, intervalo_dias = :intervalo_dias 
            WHERE cluster_id = :cluster_id
        """)
        with engine.connect() as connection:
            connection.execute(update_query, {
                "nome": nome, 
                "ticket_medio": ticket_medio, 
                "intervalo_dias": intervalo_dias, 
                "cluster_id": cluster_id
            })
        
        query = "SELECT * FROM usuarios"
        df_usuarios = pd.read_sql(query, engine)
        
        cluster = df_usuarios[(df_usuarios['ticket_medio'] > ticket_medio) & 
                              (df_usuarios['intervalo_dias'] <= intervalo_dias)]
        
        insert_query = text("""
            INSERT INTO clusters (cluster_id, usuario_id, update_date) 
            VALUES (:cluster_id, :usuario_id, :update_date)
        """)
        check_exists_query = text("""
            SELECT COUNT(*) FROM clusters WHERE cluster_id = :cluster_id AND usuario_id = :usuario_id
        """)
        
        with engine.connect() as connection:
            for _, row in cluster.iterrows():
                result = connection.execute(check_exists_query, {
                    "cluster_id": cluster_id, 
                    "usuario_id": row['id']
                })
                exists = result.scalar()
                
                if not exists:
                    connection.execute(insert_query, {
                        "cluster_id": cluster_id, 
                        "usuario_id": row['id'], 
                        "update_date": datetime.now().strftime('%Y-%m-%d')
                    })
        
        print(f"Cluster '{nome}' criado e salvo com sucesso!")
        
    except Exception as e:
        print(f"Erro ao criar clusters: {e}")

def inserir_dados_iniciais():
    engine = create_connection()
    
    if engine is None:
        print("Não foi possível conectar ao banco.")
        return
    
    try:
        usuarios = [
            {'nome': 'João Silva', 'idade': 34, 'cidade': 'São Paulo', 'ticket_medio': 45.50, 'intervalo_dias': 25},
            {'nome': 'Maria Oliveira', 'idade': 28, 'cidade': 'Rio de Janeiro', 'ticket_medio': 32.00, 'intervalo_dias': 40},
            {'nome': 'Carlos Souza', 'idade': 41, 'cidade': 'Belo Horizonte', 'ticket_medio': 70.00, 'intervalo_dias': 20},
            {'nome': 'Ana Paula', 'idade': 29, 'cidade': 'São Paulo', 'ticket_medio': 60.00, 'intervalo_dias': 15}
        ]
        
        insert_query = text("""
            INSERT INTO usuarios (nome, idade, cidade, ticket_medio, intervalo_dias) 
            VALUES (:nome, :idade, :cidade, :ticket_medio, :intervalo_dias)
        """)
        
        with engine.connect() as connection:
            for usuario in usuarios:
                connection.execute(insert_query, usuario)
        
        print("Dados iniciais inseridos com sucesso!")
        
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")

def get_cluster_data(cluster_id):
    engine = create_connection()
    query = text("SELECT nome, ticket_medio, intervalo_dias FROM cluster_names WHERE cluster_id = :cluster_id")
    
    with engine.connect() as connection:
        result = connection.execute(query, {"cluster_id": cluster_id}).fetchone()
        
    if result:
        # Acessando as colunas usando _mapping para suportar nomes de coluna
        return {
            "nome": result._mapping["nome"],
            "ticket_medio": result._mapping["ticket_medio"],
            "intervalo_dias": result._mapping["intervalo_dias"]
        }
    else:
        return None

