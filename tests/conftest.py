import os
from dotenv import load_dotenv

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

load_dotenv()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if 'sqlite' in TEST_DATABASE_URL else {}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

@pytest.fixture(scope='function')
def db_session():
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope='function')
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

