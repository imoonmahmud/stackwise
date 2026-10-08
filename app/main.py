from fastapi import FastAPI

app = FastAPI()

@app.get('/health', name='health_check')
def health_check():
    return {'status': 'ok'}