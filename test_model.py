from sqlalchemy.schema import CreateTable
from app.database import engine
from app.models.tool import Tool

print(CreateTable(Tool.__table__).compile(engine))