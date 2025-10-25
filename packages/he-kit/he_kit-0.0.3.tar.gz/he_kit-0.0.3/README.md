# Helicon kit

A project generator that bootstraps a FastAPI setup following Helicon's
standards and best practices.

## Start a new project

Run the following commands to initialize a new project:

```
mkdir helicon-app
cd helicon-app
uvx he-kit init
```

After answering the prompts you should have a fully runnable FastAPI setup.
You can verify that it works by running the test suite and starting the
development server:

```
uv run pytest
uv run he-kit dev
```

### Create a model and migrations

Helicon-kit users SQLModel and Alembic. To start working with models, first
create a new module in the `models/` directory. We'll call it `users.py`:

```
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
```

Make sure it is importable via `your_module_name.models` by importing it in
`models/__init__.py`:

```
from .users import *
```

Create the migrations and apply them:

```
uv run he-kit makemigrations "add user model"
uv run he-kit migrate
```

### Create and register a new router

Firstly we need to define some API schemas. We'll add them in the module
`schemas/users.py`:

```
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    name: str
    email: str


class UserRead(SQLModel):
    id: int
    name: str
    email: str
```

Note: as both schemas and models are derrived from `SQLModel` you can of
course create base classes and extend them to avoid repeating attributes.

We'll continue and a new module in the `routers/` directory. We'll stay on the
theme and call it `users.py`:

```
from he_kit.core.db import db_session
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.users import User
from ..schemas.users import UserCreate, UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(db_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    db_user = User.model_validate(user)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
```

And finally we register the router in `app.py`:

```
from he_kit.core.app import App

from .conf import settings
from .routers.users import router as user_router


def create_app():
    app = App(settings=settings)

    app.include_router(user_router, prefix="/users")

    return app


app = create_app()
```

### Writing tests

To verify that everything works we'll create a testmodule in
`tests/test_user_endpoints.py`:

```
def test_create_user(client):
    payload = {"name": "Alice", "email": "alice@example.com"}
    r = client.post("/users/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_list_users(client):
    payload = {"name": "Bob", "email": "bob@example.com"}
    r = client.post("/users/", json=payload)
    assert r.status_code == 200

    r = client.get("/users/")
    assert r.status_code == 200
    users = r.json()
    assert any(u["name"] == "Bob" for u in users)
```

Save the file and run the tests suite:

```
uv run pytest
```

## Local development setup

To install `he-kit` from local disk to try it out during development, you can
install it with `pip`:

```
mkdir test-dir
cd test-dir
uv venv
pip install -e ../path/to/he-kit
uv run he-kit ...
```
