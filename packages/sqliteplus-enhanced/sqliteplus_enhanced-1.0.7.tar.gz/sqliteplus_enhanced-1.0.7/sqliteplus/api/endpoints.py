import logging
from dataclasses import dataclass
from urllib.parse import parse_qs

import aiosqlite
from sqlite3 import OperationalError
from fastapi import APIRouter, HTTPException, Depends, Request

from sqliteplus.core.db import db_manager
from sqliteplus.core.schemas import CreateTableSchema, InsertDataSchema
from sqliteplus.auth.jwt import generate_jwt, verify_jwt
from sqliteplus.auth.users import get_user_service, UserSourceError

router = APIRouter()
logger = logging.getLogger(__name__)


def _escape_identifier(identifier: str) -> str:
    """Escapa identificadores siguiendo las reglas de SQLite."""

    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def _map_sql_error(exc: Exception, table_name: str) -> HTTPException:
    """Mapea errores operacionales de SQLite a respuestas HTTP apropiadas."""

    message = str(exc)
    normalized = message.lower()

    if "no such table" in normalized:
        return HTTPException(status_code=404, detail=f"Tabla '{table_name}' no encontrada")

    if "no such column" in normalized or "has no column named" in normalized:
        return HTTPException(
            status_code=400,
            detail=f"Columna inválida para la tabla '{table_name}': {message}",
        )

    if "may not be dropped" in normalized:
        return HTTPException(
            status_code=400,
            detail=(
                f"No se puede eliminar la tabla '{table_name}': {message}"
            ),
        )

    if "syntax error" in normalized:
        return HTTPException(
            status_code=400,
            detail=f"Error de sintaxis en la instrucción SQL: {message}",
        )

    if "more than one primary key" in normalized:
        return HTTPException(
            status_code=400,
            detail=(
                f"Definición inválida de clave primaria para la tabla '{table_name}': {message}"
            ),
        )

    logger.exception(
        "Error operacional inesperado durante operación SQL en la tabla %s: %s",
        table_name,
        message,
    )
    return HTTPException(
        status_code=500,
        detail="Error interno al ejecutar la operación en la base de datos",
    )

@dataclass
class _LoginForm:
    username: str
    password: str


async def _parse_login_form(request: Request) -> _LoginForm:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Credenciales faltantes")

    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Formulario inválido") from exc

    form_values = parse_qs(decoded, keep_blank_values=True)
    username = form_values.get("username", [""])[0]
    password = form_values.get("password", [""])[0]

    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuario o contraseña ausentes")

    return _LoginForm(username=username, password=password)


@router.post("/token", tags=["Autenticación"], summary="Obtener un token de autenticación", description="Genera un token JWT válido por 1 hora.")
async def login(form_data: _LoginForm = Depends(_parse_login_form)):
    try:
        user_service = get_user_service()
    except UserSourceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if user_service.verify_credentials(form_data.username, form_data.password):
        token = generate_jwt(form_data.username)
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Credenciales incorrectas")


@router.post("/databases/{db_name:path}/create_table", tags=["Gestión de Base de Datos"], summary="Crear una tabla", description="Crea una tabla en la base de datos especificada.")
async def create_table(db_name: str, table_name: str, schema: CreateTableSchema, user: str = Depends(verify_jwt)):
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    try:
        sanitized_columns = schema.normalized_columns()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    columns_def = ", ".join(
        f"{_escape_identifier(column)} {column_type}" for column, column_type in sanitized_columns.items()
    )
    query = f"CREATE TABLE IF NOT EXISTS {_escape_identifier(table_name)} ({columns_def})"
    try:
        await db_manager.execute_query(db_name, query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OperationalError, aiosqlite.OperationalError) as exc:
        raise _map_sql_error(exc, table_name) from exc
    return {"message": f"Tabla '{table_name}' creada en la base '{db_name}'."}


@router.post("/databases/{db_name:path}/insert", tags=["Operaciones CRUD"], summary="Insertar datos", description="Inserta un registro en una tabla.")
async def insert_data(db_name: str, table_name: str, schema: InsertDataSchema, user: str = Depends(verify_jwt)):
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    payload_values = schema.values
    columns = list(payload_values.keys())
    escaped_columns = ", ".join(_escape_identifier(column) for column in columns)
    placeholders = ", ".join(["?"] * len(columns))
    query = (
        f"INSERT INTO {_escape_identifier(table_name)} ({escaped_columns}) "
        f"VALUES ({placeholders})"
    )
    try:
        params = tuple(payload_values[column] for column in columns)
        row_id = await db_manager.execute_query(
            db_name,
            query,
            params,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Violación de restricción: {exc}",
        ) from exc
    except (OperationalError, aiosqlite.OperationalError) as exc:
        raise _map_sql_error(exc, table_name) from exc
    return {"message": "Datos insertados", "row_id": row_id}



@router.get("/databases/{db_name:path}/fetch", tags=["Operaciones CRUD"], summary="Consultar datos", description="Recupera todos los registros de una tabla.")
async def fetch_data(db_name: str, table_name: str, user: str = Depends(verify_jwt)):
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    query = f'SELECT * FROM "{table_name}"'
    try:
        data = await db_manager.fetch_query(db_name, query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OperationalError, aiosqlite.OperationalError) as exc:
        raise _map_sql_error(exc, table_name) from exc
        
    return {"data": data}


@router.delete("/databases/{db_name:path}/drop_table", tags=["Gestión de Base de Datos"], summary="Eliminar tabla", description="Elimina una tabla de la base de datos.")
async def drop_table(db_name: str, table_name: str, user: str = Depends(verify_jwt)):
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    query = f'DROP TABLE IF EXISTS "{table_name}"'
    try:
        await db_manager.execute_query(db_name, query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OperationalError, aiosqlite.OperationalError) as exc:
        raise _map_sql_error(exc, table_name) from exc
    return {"message": f"Tabla '{table_name}' eliminada de la base '{db_name}'."}
