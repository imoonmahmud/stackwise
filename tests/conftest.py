import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
import app.models as _models  # noqa: F401  (registers every model; don't write `import app.models`, it would replace the `app` above)
from app.models.user import User
from app.core.security import hash_password, create_access_token

load_dotenv()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
assert TEST_DATABASE_URL and TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"), \
    "Refusing to run: TEST_DATABASE_URL must point to a database whose name ends with _test"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def _db_override(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def editor_token(db_session):
    user = User(email="editor@stackwise.com", hashed_password=hash_password("securepassword123"),
                role="editor", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return create_access_token(user.id)


@pytest.fixture
def anon_client(_db_override):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client(_db_override, editor_token):
    with TestClient(app, headers={"Authorization": f"Bearer {editor_token}"}) as c:
        yield c