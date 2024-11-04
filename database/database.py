from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

def create_connection():
    try:
        # Construir a URI de conexão usando pymysql
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME')
        
        connection_string = f"mysql+pymysql://{user}:{password}@{host}/{database}"
        engine = create_engine(connection_string)
        
        # Testar a conexão
        with engine.connect() as connection:
            print("Conexão com o MySQL estabelecida com sucesso!")
        
        return engine
    except Exception as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None
