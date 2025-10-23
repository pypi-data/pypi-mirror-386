#!/usr/bin/env python3
#-*- coding: UTF-8 -*-
# ----------------------------------------
# jjandres 2025 - 17-05-2025)
# ----------------------------------------
# pylint: disable=multiple-imports
# pylint: disable=line-too-long
# pylint: disable=trailing-whitespace
# pylint: disable=wrong-import-position
# pylint: disable=unused-import
# pylint: disable=import-error
# pylint: disable=unused-argument
# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=unused-variable
# pylint: disable=bare-except
# pylint: disable=protected-access
# pylint: disable=ungrouped-imports
# pylint: disable=wrong-import-order
# pylint: disable=redefined-builtin
# pylint: disable=unidiomatic-typecheck
# pylint: disable=singleton-comparison
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-lines
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=broad-except
# pylint: disable=too-many-arguments
# pylint: disable=broad-exception-raised
# pylint: disable=consider-using-f-string
# 
 

import bcrypt
import hashlib, hmac
import secrets
import json
import logging
from typing import Optional, List, Dict, Any, Union, Literal, Callable
from .core_sync import Columna  # o el path correcto según tu proyecto
from pydantic import BaseModel
from decimal import Decimal
from functools import wraps


def hash_password(plain_password: str) -> str:
    """
    Genera un hash seguro de una contraseña en texto plano.

    Args:
        plain_password (str): Contraseña original en texto plano.

    Returns:
        str: Hash seguro (en formato string) listo para almacenar en la base de datos.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode(), salt)
    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash almacenado.

    Args:
        plain_password (str): Contraseña introducida por el usuario.
        hashed_password (str): Hash previamente almacenado.

    Returns:
        bool: True si coinciden, False si no.
    """
    return bcrypt.checkpw(
        plain_password.encode(), 
        hashed_password.encode()
    )


def generar_api_key() -> str:
    """
    Genera una api_key aleatoria de ~43 caracteres seguros.
    - Returns:
        - str: cadena api_key aleatoria
    """
    return secrets.token_urlsafe(32)


def generar_api_secret() -> str:
    """
    Genera una api_key aleatoria de ~65 caracteres seguros
    - Returns:
        2-tuple:
        - str: cadena api_secret aleatoria.
        - str: cadena api_secret hasheada 
    """
    secreto = secrets.token_urlsafe(48)  # ~65 caracteres
    secreto_hash = hashlib.sha256(secreto.encode()).hexdigest()
    return secreto, secreto_hash  # Retorna secreto plano y su hash

def verificar_api_secret(api_secret: str, hashed_api_secret: str) -> bool:
    """
    Verifica si un API_SECRET en texto plano coincide con su hash SHA-256.

    Args:
        api_secret (str): API_SECRET en texto plano.
        hashed_api_secret (str): Hash SHA-256 (hex) previamente almacenado.

    Returns:
        bool: True si coinciden, False en caso contrario.
    """
    # Calcula el hash del secreto proporcionado
    calc_hash = hashlib.sha256(api_secret.encode()).hexdigest()
    # Compara de forma segura para evitar ataques de tiempo
    return hmac.compare_digest(calc_hash, hashed_api_secret)
   

def generar_lista_campos(campos, alias=None, excluir=None, prefijo_alias=None):
    """
    Genera una lista de campos SQL a partir de un diccionario, lista de strings o lista de objetos Columna,
    con alias opcional, campos a excluir y alias renombrado con prefijo.

    :param `campos`:           (Requerido) Diccionario {nombre_campo: Column}, lista de strings o lista de objetos Columna
    :param `alias`:            (Opcional) Alias para los campos (string), ej: 'u'
    :param `excluir`:          (Opcional) Lista de campos a excluir (lista de strings)
    :param `prefijo_alias`:    (Opcional) Prefijo para renombrar los campos con alias: <alias>.<campo> AS <prefijo><campo>
    :return:                   String con lista de campos separados por coma
    """
    excluir = excluir or []
    lista = []

    if isinstance(campos, dict):
        iterable = campos.items()
    elif isinstance(campos, list):
        if all(hasattr(col, 'nombre') for col in campos):
            iterable = [(col.nombre, col) for col in campos]
        else:
            iterable = [(nombre, None) for nombre in campos]
    else:
        raise TypeError("El parámetro 'campos' debe ser un dict, una lista de strings o una lista de objetos Columna.")

    for nombre, _ in iterable:
        if nombre in excluir:
            continue
        if alias:
            campo_sql = f"{alias}.{nombre}"
        else:
            campo_sql = nombre

        if prefijo_alias:
            alias_sql = f"{prefijo_alias}{nombre}"
            lista.append(f"{campo_sql} AS {alias_sql}")
        else:
            lista.append(campo_sql)

    return ", ".join(lista)


class FiltroCampo(BaseModel):
    """Crea modelo para definir un filtro de campo SQL."""
    op: Literal["=", "!=", ">", "<", ">=", "<=", "like", "in", "between"]
    valor: Any
    


def construir_condiciones_sql(filtros: dict[str, dict[str, Union[str, Any]]], alias: Optional[dict[str, str]] = None) -> tuple[str, list[Any]]:
    """
    Construye una cláusula WHERE SQL a partir de un diccionario de filtros.

    Cada entrada del diccionario debe tener la forma:
        campo: {"op": operador_sql, "valor": valor_o_lista}

    Operadores soportados (case-insensitive):
        '=', '!=', '>', '<', '>=', '<=', 'like', 'in', 'between'

    Parámetros:
        - `filtros`:    Diccionario de filtros con campo, operador y valor.
        - `alias`:      Diccionario opcional con alias por campo, p.ej. {'nombre_campo': 'a.nombre_alias'}

    Returns:
        (condiciones_sql, valores): la cláusula WHERE (sin "WHERE") y la lista de parámetros.
    """
    condiciones: List[str] = []
    valores: List[Any] = []

    def _col(campo: str) -> str:
        return alias.get(campo, campo) if alias else campo

    def _is_seq(x: Any) -> bool:
        return isinstance(x, (list, tuple))

    for campo, cond in (filtros or {}).items():
        if not isinstance(cond, dict):
            # Compatibilidad: ignorar entradas mal formadas
            continue

        op_raw = cond.get("op")
        val = cond.get("valor")
        if not isinstance(op_raw, str):
            # Compatibilidad: ignorar operador inválido
            continue

        op = op_raw.strip().lower()
        campo_sql = _col(campo)

        # Operadores simples y nulos
        if op in {"=", "!="}:
            # None -> IS NULL / IS NOT NULL
            if val is None:
                condiciones.append(f"{campo_sql} IS {'NOT ' if op == '!=' else ''}NULL")
                continue

            # List/Tuple -> IN / NOT IN
            if _is_seq(val):
                seq = list(val)
                if not seq:
                    # Compatibilidad: ignorar si viene vacío
                    continue
                placeholders = ", ".join(["%s"] * len(seq))
                condiciones.append(f"{campo_sql} {'NOT ' if op == '!=' else ''}IN ({placeholders})")
                valores.extend(seq)
                continue

            # Escalar
            condiciones.append(f"{campo_sql} {op} %s")
            valores.append(val)
            continue

        if op in {">", "<", ">=", "<="}:
            condiciones.append(f"{campo_sql} {op} %s")
            valores.append(val)
            continue

        if op == "like":
            if val is None:
                # Compatibilidad: ignorar filtro inválido
                continue
            condiciones.append(f"{campo_sql} LIKE %s")
            valores.append(val)
            continue

        if op == "in":
            if not _is_seq(val):
                # Compatibilidad: ignorar si no es lista/tupla
                continue
            seq = list(val)
            if not seq:
                # Compatibilidad: ignorar IN vacío
                continue
            placeholders = ", ".join(["%s"] * len(seq))
            condiciones.append(f"{campo_sql} IN ({placeholders})")
            valores.extend(seq)
            continue

        if op == "between":
            # Acepta [desde, hasta] o {"desde": x, "hasta": y}
            desde = hasta = None
            if isinstance(val, dict):
                desde = val.get("desde", None)
                hasta = val.get("hasta", None)
            elif _is_seq(val) and len(val) >= 2:
                desde, hasta = val[0], val[1]
            elif val is None:
                # Compatibilidad: ignorar
                continue
            else:
                # Compatibilidad/utility: si viene solo un valor, tratar como '='
                condiciones.append(f"{campo_sql} = %s")
                valores.append(val)
                continue

            if desde is not None and hasta is not None:
                condiciones.append(f"{campo_sql} BETWEEN %s AND %s")
                valores.extend([desde, hasta])
            elif desde is not None:
                condiciones.append(f"{campo_sql} >= %s")
                valores.append(desde)
            elif hasta is not None:
                condiciones.append(f"{campo_sql} <= %s")
                valores.append(hasta)
            # si ambos None, no añadimos nada (compatibilidad)
            continue

        # Operador no soportado: compatibilidad -> ignorar
        continue

    condiciones_sql = " AND ".join(condiciones)
    return condiciones_sql, valores


def resolver_orden_sql(orden: str, alias: Optional[dict[str, str]] = None) -> str:
    """
    Convierte una cadena de orden (como 'nombre DESC') en una cláusula SQL segura,
    aplicando alias si están definidos.

    Ejemplo:
        orden = "nombre DESC"
        alias = {"nombre": "a.nombre"}
        => "a.nombre DESC"

    Si el campo no está en alias, se usa tal cual (bajo tu responsabilidad).

    Args:
        orden (str): Campo o campos por los que ordenar, separados por coma.
        alias (dict[str, str], optional): Diccionario de alias.

    Returns:
        str: Expresión segura de ordenación SQL.
    """
    if not orden:
        return ""

    campos_orden = []
    for parte in orden.split(","):
        tokens = parte.strip().split()
        campo = tokens[0]
        direccion = tokens[1].upper() if len(tokens) > 1 and tokens[1].upper() in {"ASC", "DESC"} else "ASC"

        campo_sql = alias.get(campo, campo) if alias else campo
        campos_orden.append(f"{campo_sql} {direccion}")

    return ", ".join(campos_orden)

# def normalizar_resultado(
#     campos_decimal: Optional[List[str]] = None,
#     campos_json: Optional[List[str]] = None,
#     campos_fecha: Optional[List[str]] = None,
#     logger: Optional[logging.Logger] = None
# ) -> Callable:
#     """
#     Decorador que normaliza campos específicos de un resultado de consulta:
#     - Convierte valores a Decimal si no son None y aún no lo son.
#     - Convierte strings JSON a dict o list si son válidos.
#     - Convierte fechas a string ISO si se desea.

#     Args:
#         campos_decimal (list[str]): Campos que deben convertirse a Decimal.
#         campos_json (list[str]): Campos con JSON serializado como str.
#         campos_fecha (list[str]): Campos de tipo datetime o date que se quieren como str.
#         logger (Logger, opcional): Logger para salida de depuración.

#     Returns:
#         Callable: Decorador para funciones async que devuelven dict o list[dict].
#     """
#     campos_decimal = campos_decimal or []
#     campos_json = campos_json or []
#     campos_fecha = campos_fecha or []

#     def decorador(func: Callable) -> Callable:
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             if logger:
#                 logger.warning(f"⏳ Ejecutando función decorada: {func.__name__}") #@log
#             resultado = await func(*args, **kwargs)

#             def procesar_fila(fila: dict) -> dict:
#                 for campo in campos_decimal:
#                     valor = fila.get(campo)
#                     if logger:
#                         logger.warning(f"🔍 Campo decimal '{campo}': {valor} ({type(valor)})") #@log
#                     if valor is None or isinstance(valor, Decimal):
#                         continue
#                     try:
#                         fila[campo] = Decimal(str(valor))
#                     except Exception as e:
#                         if logger:
#                             logger.warning(f"⚠️ No se pudo convertir '{campo}' a Decimal: {e}") #@log

#                 for campo in campos_json:
#                     valor = fila.get(campo)
#                     if logger:
#                         logger.warning(f"📦 Campo JSON '{campo}': {valor} ({type(valor)})") #@log
#                     if isinstance(valor, str) and valor.strip():
#                         try:
#                             fila[campo] = json.loads(valor)
#                         except Exception as e:
#                             if logger:
#                                 logger.warning(f"⚠️ No se pudo parsear '{campo}' como JSON: {e}") #@log

#                 for campo in campos_fecha:
#                     valor = fila.get(campo)
#                     if valor and hasattr(valor, 'isoformat'):
#                         if logger:
#                             logger.warning(f"📅 Campo fecha '{campo}' → {valor.isoformat()}") #@log
#                         fila[campo] = valor.isoformat()

#                 return fila

#             if isinstance(resultado, list):
#                 return [procesar_fila(f) for f in resultado if isinstance(f, dict)]
#             elif isinstance(resultado, dict):
#                 return procesar_fila(resultado)
#             return resultado

#         return wrapper
#     return decorador
