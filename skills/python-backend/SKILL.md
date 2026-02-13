---
name: python-backend
description: Python backend development — API design, database operations, authentication, background processing, and ML serving. Use when building Python APIs, data pipelines, or ML-integrated services.
---

# Python Backend

Python backends power most AI/ML services, internal tools, and data pipelines. This skill covers the patterns that actually matter in production: API design, database operations, authentication, background processing, and ML serving.

This is not a list of technologies you know. It's a protocol for building backends that work — with specific patterns for specific situations, failure modes to avoid, and decisions to make deliberately rather than by default.

**Workspace constraint:** All code must be Python 3.9 compatible. Use `typing.Optional[X]` not `X | None`. Use `typing.Union[X, Y]` not `X | Y`. Use `list[X]` only in 3.9+ contexts where `from __future__ import annotations` is present.

---

## Architecture Patterns

### Choosing a Framework

| Signal | Framework | Why |
|--------|-----------|-----|
| Async API, microservice, ML serving, WebSocket | **FastAPI** | Native async, Pydantic validation, auto OpenAPI docs, dependency injection |
| Full web app with admin panel, ORM, forms, auth out of the box | **Django** | Batteries included, mature ecosystem, Django REST Framework for APIs |
| Lightweight service, legacy integration, simple webhook handler | **Flask** | Minimal footprint, synchronous by default, huge middleware ecosystem |
| High-performance async without Pydantic overhead | **Starlette** | FastAPI is built on this — use directly when you want less magic |

**Default to FastAPI** unless there's a specific reason not to. It has the best developer experience for API-first services.

---

## Reference Implementations

### FastAPI + SQLAlchemy + Pydantic

**When:** Building an async API with a relational database.
**Why:** This is the standard stack. Pydantic handles validation, SQLAlchemy handles persistence, FastAPI ties them together.
**Watch out:** Don't mix sync and async database calls. Use `AsyncSession` throughout or `Session` throughout — never both.

```python
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, EmailStr

app = FastAPI()

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True  # Pydantic v2

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    import bcrypt
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    new_user = User(email=user.email, password=hashed.decode(), name=user.name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
```

### JWT Authentication

**When:** Stateless auth for APIs (mobile clients, SPAs, microservices).
**Why:** No server-side session storage. Token carries identity.
**Watch out:** Always set expiration. Never store sensitive data in the payload (it's base64, not encrypted). Rotate secrets.

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### CSV/Data Processing Endpoint

**When:** Users upload data files for processing.
**Why:** pandas for ETL is battle-tested. FastAPI's `UploadFile` handles streaming.
**Watch out:** Validate column presence before processing. Set file size limits. Don't load unbounded data into memory.

```python
import pandas as pd
from fastapi import UploadFile, HTTPException

@app.post("/api/upload-csv")
async def process_csv(file: UploadFile):
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(413, "File too large")

    df = pd.read_csv(file.file)

    required_columns = ["id", "name", "email"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Missing columns: {missing}")

    df = df.dropna(subset=["email"])
    df["email"] = df["email"].str.lower().str.strip()

    return {
        "total_rows": len(df),
        "unique_emails": int(df["email"].nunique()),
        "summary": df.describe().to_dict(),
    }
```

### Background Tasks (Celery)

**When:** Long-running operations (email, reports, ML training) that shouldn't block the request.
**Why:** Celery is the standard. Redis as broker is the simplest setup.
**Watch out:** Task arguments must be serializable (no ORM objects, no file handles). Always handle task failure with retries and dead-letter queues.

```python
from celery import Celery

celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, user_id: int):
    try:
        send_email(user_id)
    except Exception as exc:
        raise self.retry(exc=exc)

@app.post("/api/send-email/{user_id}")
async def trigger_email(user_id: int):
    send_email_task.delay(user_id)
    return {"message": "Email queued"}
```

### ML Model Inference

**When:** Serving predictions from a trained model.
**Why:** Load once at startup, predict on each request.
**Watch out:** Model loading is slow — do it at startup, not per-request. Use `typing.List[float]` for 3.9 compat. Validate input dimensions.

```python
import pickle
from typing import List
import numpy as np
from pydantic import BaseModel

# Load at startup
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

class PredictionRequest(BaseModel):
    features: List[float]

@app.post("/api/predict")
async def predict(request: PredictionRequest):
    X = np.array([request.features])
    prediction = model.predict(X)
    probability = model.predict_proba(X)
    return {
        "prediction": int(prediction[0]),
        "probability": float(probability[0][1]),
    }
```

---

## Database Patterns

### Connection Pooling

Always configure pool size explicitly. Defaults are usually too small for production, too large for development.

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,           # Concurrent connections
    max_overflow=10,       # Burst capacity
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle connections every 30 min
)
```

### Migrations with Alembic

```bash
alembic init alembic            # Setup
alembic revision --autogenerate -m "add users table"  # Generate
alembic upgrade head            # Apply
alembic downgrade -1            # Rollback one step
```

**Rules:**
- Every schema change goes through Alembic. No exceptions.
- Review autogenerated migrations before applying — they miss data migrations, column renames, and constraint changes.
- Test rollback (`downgrade`) for every migration.

### Transaction Boundaries

```python
async def transfer_funds(db: AsyncSession, from_id: int, to_id: int, amount: float):
    async with db.begin():  # Explicit transaction
        sender = await db.get(Account, from_id)
        receiver = await db.get(Account, to_id)
        if sender.balance < amount:
            raise HTTPException(400, "Insufficient funds")
        sender.balance -= amount
        receiver.balance += amount
    # Commits on exit, rolls back on exception
```

### Preventing N+1 Queries

```python
from sqlalchemy.orm import selectinload
from sqlalchemy import select

# BAD: N+1 — fetches users, then one query per user for posts
users = await db.execute(select(User))
for user in users.scalars():
    print(user.posts)  # Each triggers a query

# GOOD: Eager load in one query
stmt = select(User).options(selectinload(User.posts))
users = await db.execute(stmt)
```

---

## Testing Patterns

### Project Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, no I/O
│   ├── test_models.py
│   └── test_utils.py
├── integration/         # Database, external services
│   ├── test_api.py
│   └── test_db.py
└── e2e/                 # Full request cycle
    └── test_flows.py
```

### Key Fixtures

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture
async def db_session():
    """Fresh database session per test, rolled back after."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    """Test client with overridden DB dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_payment_processing(client):
    with patch("app.services.stripe.charge", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "ch_123", "status": "succeeded"}
        response = await client.post("/api/pay", json={"amount": 1000})
        assert response.status_code == 200
        mock.assert_called_once()
```

### Strategy

- **Unit tests** for business logic, validation, transformations. No I/O.
- **Integration tests** for database queries, API endpoints with test DB.
- **E2E tests** sparingly — full request flows that test the critical path.
- Ratio: 70% unit / 25% integration / 5% e2e.

---

## Anti-Patterns

### The God Endpoint

**Pattern:** One route that accepts a `type` parameter and does completely different things based on its value. `/api/do?type=create_user&data=...` and `/api/do?type=send_email&data=...`.

**Reality:** Impossible to test, document, or rate-limit independently. Every change risks breaking unrelated functionality.

**Fix:** One route per action. REST resources or explicit action endpoints. `/api/users` POST, `/api/emails` POST.

### The Sync Trap

**Pattern:** Calling `requests.get()` or `time.sleep()` inside an `async def` handler.

**Reality:** Blocks the entire event loop. One slow external call freezes all concurrent requests.

**Fix:** Use `httpx.AsyncClient` instead of `requests`. Use `asyncio.sleep()` instead of `time.sleep()`. If you must use sync code, run it in `asyncio.to_thread()`.

### The Migration Mess

**Pattern:** Making schema changes directly in the database or in raw SQL files. "We'll add Alembic later."

**Reality:** Later never comes. Two months in, nobody knows what the schema should be, rollback is impossible, and the production database has drifted from the code.

**Fix:** `alembic init` in the first hour of the project. Every schema change is a migration. No exceptions.

### The Bare Exception

**Pattern:** `except: pass` or `except Exception: logger.error("something failed")` with no re-raise.

**Reality:** Errors disappear silently. The system appears to work but produces wrong results. Debugging becomes archaeology.

**Fix:** Catch specific exceptions. Always log the full traceback. Re-raise if you can't meaningfully handle it. `except Exception as e: logger.exception("Context: %s", context); raise`

### The requirements.txt Lie

**Pattern:** `fastapi`, `sqlalchemy`, `pandas` — no version pins.

**Reality:** Works today, breaks tomorrow when a dependency releases a breaking change. "But it worked on my machine" — yes, with the versions you happened to have installed.

**Fix:** Pin exact versions: `fastapi==0.109.0`. Use `pip freeze > requirements.txt` or better, use `poetry.lock` / `pip-compile`. Lock files are not optional.

---

## Quick Reference Card

```
FRAMEWORK:  FastAPI (default) | Django (admin/full-stack) | Flask (lightweight)
COMPAT:     Python 3.9+ — use Optional[X], List[X], Dict[K,V] from typing

SCAFFOLD:   fastapi + uvicorn + sqlalchemy + alembic + pydantic + pytest
            pip install "fastapi[standard]" sqlalchemy[asyncio] alembic

DATABASE:   alembic init alembic
            alembic revision --autogenerate -m "description"
            alembic upgrade head

ASYNC:      httpx.AsyncClient (not requests)
            asyncio.sleep (not time.sleep)
            asyncio.to_thread(sync_func) for unavoidable sync

TEST:       pytest + pytest-asyncio + httpx
            conftest.py: db fixture with rollback, client fixture
            70% unit / 25% integration / 5% e2e

PATTERNS:   get_db() dependency → yield session
            Pydantic models for all I/O boundaries
            selectinload() to prevent N+1
            Explicit transactions with db.begin()
            Load ML models at startup, not per-request

DEPLOY:     uvicorn app.main:app --host 0.0.0.0 --port 8000
            gunicorn -k uvicorn.workers.UvicornWorker (production)
```

## Cross-Skill Integration

- **security** → Auth patterns, input validation, secrets management
- **devops** → Dockerfile, CI/CD pipeline, deployment config
- **data-analysis** → Database query patterns, ORM best practices
- **skill-lifecycle** → Runtime monitoring of backend services
