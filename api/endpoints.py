from fastapi import APIRouter, HTTPException, Query, Request
from db.db_config import get_engine
from db.meta import load_metadata
from sqlalchemy import select, update, insert

router = APIRouter()
metadata = load_metadata()
engine = get_engine()

@router.get("/GetFromTable")
def get_by_id(table: str, id: int = Query(...)):
    try:
        table_obj = metadata.tables[table]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Таблица '{table}' не найдена")

    pk_column = [c for c in table_obj.columns if c.primary_key]
    if not pk_column:
        raise HTTPException(status_code=400, detail="Нет первичного ключа в таблице")

    stmt = select(table_obj).where(pk_column[0] == id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()

    if result is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return result

@router.get("/GetAllFromTable")
def get_all(table: str):
    try:
        table_obj = metadata.tables[table]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Таблица '{table}' не найдена")

    stmt = select(table_obj)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().all()
    return result

@router.get("/GetAllTables")
def get_all_tables():
    return list(metadata.tables.keys())

@router.post("/SetFieldValue")
def set_field(table: str, id: int, field: str, value: str):
    try:
        table_obj = metadata.tables[table]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Таблица '{table}' не найдена")

    if field not in table_obj.columns:
        raise HTTPException(status_code=400, detail=f"Поле '{field}' не найдено в таблице")

    pk_column = [c for c in table_obj.columns if c.primary_key]
    if not pk_column:
        raise HTTPException(status_code=400, detail="Нет первичного ключа в таблице")

    stmt = update(table_obj).where(pk_column[0] == id).values({field: value})
    with engine.connect() as conn:
        with conn.begin():
            result = conn.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Запись не найдена или не обновлена")
    return {"success": True}

@router.post("/AddRecordToTable")
def add_record(table: str, request: Request):
    try:
        table_obj = metadata.tables[table]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Таблица '{table}' не найдена")

    values = dict(request.query_params)
    values.pop("table", None)

    for column in table_obj.columns:
        if column.name in values:
            raw_val = values[column.name]
            if raw_val == "":
                values[column.name] = None
            elif isinstance(column.type.python_type, int):
                try:
                    values[column.name] = int(raw_val)
                except:
                    pass
            elif isinstance(column.type.python_type, float):
                try:
                    values[column.name] = float(raw_val)
                except:
                    pass

    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(insert(table_obj).values(**values))
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка вставки: {e}")

@router.get("/GetByField")
def get_by_field(table: str, field: str, value: str):
    try:
        table_obj = metadata.tables[table]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Таблица '{table}' не найдена")

    if field not in table_obj.columns:
        raise HTTPException(status_code=400, detail=f"Поле '{field}' не найдено в таблице")

    stmt = select(table_obj).where(table_obj.c[field] == value)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().all()

    if not result:
        raise HTTPException(status_code=404, detail="Ничего не найдено")
    return result