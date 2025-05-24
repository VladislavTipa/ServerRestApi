from sqlalchemy import MetaData, inspect
from db.db_config import get_engine

# Загрузка структуры БД
def load_metadata():
    engine = get_engine()
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata

# Получение информации о таблицах и связях
def get_db_schema_info():
    engine = get_engine()
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    schema_info = {}

    for table in tables:
        columns = inspector.get_columns(table)
        foreign_keys = inspector.get_foreign_keys(table)

        schema_info[table] = {
            "columns": columns,
            "foreign_keys": foreign_keys
        }

    return schema_info
