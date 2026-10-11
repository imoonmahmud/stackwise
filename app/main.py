from fastapi import FastAPI

from app.routes import tools
from app.routes import categories

app = FastAPI()

@app.get('/health', name='health_check')
def health_check():
    return {'status': 'ok'}

app.include_router(tools.router)
app.include_router(categories.router)