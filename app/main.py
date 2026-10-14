from fastapi import FastAPI

from app.routes import tools
from app.routes import categories
from app.routes import features
from app.routes import pricing_plans
from app.routes import solution
from app.routes import comparisons
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get('/health', name='health_check')
def health_check():
    return {'status': 'ok'}

app.include_router(tools.router)
app.include_router(categories.router)
app.include_router(features.router)
app.include_router(pricing_plans.router)
app.include_router(solution.router)
app.include_router(comparisons.router)



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