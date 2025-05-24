from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "testbase"
DB_USER = "postgres"
DB_PASSWORD = "12345"

def get_engine() -> Engine:
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(url, echo=False, future=True)
    return engine
