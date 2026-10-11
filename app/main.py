from fastapi import FastAPI

from app.routes import tools
from app.routes import categories
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get('/health', name='health_check')
def health_check():
    return {'status': 'ok'}

app.include_router(tools.router)
app.include_router(categories.router)



#fronend

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)