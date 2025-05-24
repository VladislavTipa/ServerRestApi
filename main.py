from fastapi import FastAPI
import threading
import uvicorn
from api.endpoints import router

app = FastAPI()
app.include_router(router)

def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    from db.init_db import create_tables
    from gui.main_gui import MainGui

    create_tables()

    # Запуск API в отдельном потоке
    threading.Thread(target=run_api, daemon=True).start()

    # Запуск GUI
    MainGui()
