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


# Esta librería es un wrapper (envolvente) del conector pymysql para menjo de Mariadb con funciones asíncronas.

import aiomysql
from decimal import Decimal
from typing import Optional, Union, List, Dict
from .core_sync import Tabla, SQLLiteral
from logging import Logger
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pymysql.converters import conversions
from pymysql.constants import FIELD_TYPE
import json
import asyncio
import uuid
import time
import os
import math
from datetime import datetime, timezone, timedelta

# Creamos conversores personalizados
custom_conv = conversions.copy()
custom_conv[FIELD_TYPE.DATE] = str
custom_conv[FIELD_TYPE.DATETIME] = str
custom_conv[FIELD_TYPE.TIMESTAMP] = str
custom_conv[FIELD_TYPE.DECIMAL] = Decimal
custom_conv[FIELD_TYPE.NEWDECIMAL] = Decimal

class _PseudoPool:
    """Sustituto de aiomysql.Pool que NO reutiliza conexiones.
    - Mantiene interfaz mínima usada: acquire(), close(), wait_closed(), _closed.
    - Cada acquire() abre conexión con aiomysql.connect() y la cierra al salir del contexto.
    """
    def __init__(self, host: str, user: str, password: str, db: str, port: int, autocommit: bool = False):
        self._cfg = dict(host=host, user=user, password=password, db=db, port=port)
        self._autocommit = autocommit
        self._closed = False

    @asynccontextmanager
    async def acquire(self):
        cx = await aiomysql.connect(**self._cfg, autocommit=self._autocommit, conv=custom_conv)
        try:
            yield cx
        finally:
            try:
                if not cx.get_autocommit():
                    try:
                        await cx.rollback()
                    except Exception:
                        pass
            finally:
                cx.close()
                try:
                    await cx.wait_closed()
                except Exception:
                    pass

    def close(self):
        self._closed = True

    async def wait_closed(self):
        return


class AsyncDatabase:
    """
    Clase AsyncDatabase para entornos asíncronos como FastAPI con Uvicorn.
    Usa aiomysql como backend de conexión.
    """

    def __init__(self, host: str, user: str, password: str, db: str, port: int = 3306, logger: Optional[Logger] = None):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.logger = logger

        # Mantenemos el atributo pool por compatibilidad
        self.pool = None

        # Para compatibilidad con la gestión de tablas / sync
        self.tablas: Dict[str, Tabla] = {}

        # Último insert id (cuando aplique)
        self.ultimo_insert_id: Optional[int] = None

        # Bandera de transacción por coroutine
        self._tx_flag: ContextVar[bool] = ContextVar("mtpk_tx_flag", default=False)

    def en_transaccion(self) -> bool:
        """Indica si hay una transacción abierta en esta coroutine."""
        return self._tx_flag.get()

        
    @asynccontextmanager
    async def transaccion(self, autocommit: bool = False):
        """
        Contexto de transacción con compatibilidad hacia atrás.

        Params:
            autocommit (bool): Se mantiene por compatibilidad con transaccion_simple().
                - False (por defecto): se hace BEGIN/COMMIT/ROLLBACK.
                - True: NO se hace BEGIN/COMMIT/ROLLBACK; se cede la conexión tal cual.
                        Útil para operaciones sueltas que quieren controlar su propio commit,
                        o para simples lecturas.

        Nota:
            Aunque internamente ya no hay pool real, `self.pool.acquire()` usa _PseudoPool
            y abre/cierra una conexión por bloque.
        """
        if self.pool is None:
            await self.conectar()

        token = self._tx_flag.set(True)
        try:
            async with self.pool.acquire() as cx:
                try:
                    # Ajuste del modo autocommit en la conexión
                    # aiomysql expone `.autocommit(flag)` (no awaitable)
                    await cx.autocommit(autocommit)
                except Exception:
                    pass

                if not autocommit:
                    # Modo transaccional clásico
                    try:
                        await cx.begin()
                    except Exception:
                        # Algunos conectores pueden no requerir begin explícito
                        pass

                try:
                    yield cx
                    if not autocommit:
                        await cx.commit()
                except Exception:
                    if not autocommit:
                        try:
                            await cx.rollback()
                        except Exception:
                            pass
                    raise
        finally:
            self._tx_flag.reset(token)

    transaccion_simple = transaccion # Alias de transaccion
    
    
    # @asynccontextmanager
    # async def transaccion_simple(self, autocommit: bool = False):
    #     """
    #     Abre una conexión directa (sin pool) para una transacción/operación puntual.
    #     Se cierra SIEMPRE al salir.
    #     """
    #     cx = await aiomysql.connect(
    #         host=self.host, user=self.user, password=self.password,
    #         db=self.db, port=self.port, autocommit=autocommit, conv=custom_conv
    #     )
    #     try:
    #         if not autocommit:
    #             try:
    #                 await cx.begin()
    #             except Exception:
    #                 pass
    #         yield cx
    #         if not autocommit:
    #             try:
    #                 await cx.commit()
    #             except Exception:
    #                 try:
    #                     await cx.rollback()
    #                 except Exception:
    #                     pass
    #                 raise
    #     finally:
    #         cx.close()
    #         try:
    #             await cx.wait_closed()
    #         except Exception:
    #             pass

    async def conectar(self):
        """
        Crea un 'pool' compatible si no está ya activo. En realidad es un _PseudoPool:
        cada acquire() abre/cierra su propia conexión (sin reutilización).
        """
        if self.pool is None or getattr(self.pool, "_closed", False):
            self.pool = _PseudoPool(
                host=self.host, user=self.user, password=self.password,
                db=self.db, port=self.port, autocommit=False
            )
        return self.pool

    async def cerrar(self) -> None:
        """
        No-op seguro: mantiene compatibilidad con código que esperaba cerrar un pool.
        """
        try:
            if hasattr(self, "pool") and self.pool:
                try:
                    self.pool.close()
                    # _PseudoPool.wait_closed() existe y no hace nada; si fuera un pool real, esperaría.
                    await self.pool.wait_closed()
                except Exception:
                    pass
            self.pool = None
        except Exception as e:
            if self.logger:
                self.logger.error("Error cerrando pool: %s", e, exc_info=True)

    def add_tabla(self, tabla: Tabla):
        """
        Añade un objeto `Tabla` a la base de datos.

        - Args:
            - `tabla` (Tabla): Objeto que representa una tabla definida por el usuario.
        """
        self.tablas[tabla.nombre] = tabla

    def get_tabla(self, nombre: str) -> Tabla:
        """
        Recupera un objeto `Tabla` anteriormente añadido (o lanza KeyError si no existe).
        """
        if nombre not in self.tablas:
            raise KeyError(f"La tabla '{nombre}' no está registrada.")
        return self.tablas[nombre]

    async def query_multi_action(self, sql: str, lista_valores: List[tuple], conexion=None) -> int:
        """
        Ejecuta múltiples acciones SQL con la misma sentencia y diferentes valores usando `executemany`.

        - Si se pasa `conexion`, NO se hace commit ni rollback aquí (compatibilidad con transacciones externas).
        - Si NO se pasa `conexion`, se abre una conexión propia (vía _PseudoPool.acquire()) y se hace commit.
        """
        if not lista_valores:
            return 0

        if conexion is not None:
            async with conexion.cursor() as cursor:
                total_filas = await cursor.executemany(sql, lista_valores)
                self.ultimo_insert_id = cursor.lastrowid
                return total_filas
        else:
            if self.pool is None:
                await self.conectar()

            async with self.pool.acquire() as cx:
                try:
                    async with cx.cursor() as cursor:
                        total_filas = await cursor.executemany(sql, lista_valores)
                        self.ultimo_insert_id = cursor.lastrowid
                    await cx.commit()
                    return total_filas
                except Exception:
                    try:
                        await cx.rollback()
                    except Exception:
                        pass
                    raise

    async def query(self, sql: str, params=None, conexion=None, uno: bool = False):
        """
        Ejecuta una consulta SQL detectando si es de lectura o de acción según la primera palabra del SQL.

        Si comienza por SELECT/SHOW/DESC/DESCRIBE/EXPLAIN → delega en `_query_select`.
        En caso contrario → delega en `_query_accion`.

        Gestión de conexión:
        - Si `conexion` es None, abre y cierra conexión internamente y gestiona commit/rollback cuando proceda.
        - Si `conexion` no es None, reutiliza la transacción/conn proporcionada y NO hace commit/rollback.

        Args:
            sql (str): Sentencia SQL completa.
            params (Any, opcional): Parámetros de la consulta (tuple/list/dict según driver).
            conexion (Any, opcional): Conexión o transacción activa a reutilizar.
            uno (bool, opcional): Solo para lecturas; si True retorna una sola fila.

        Returns:
            Any: 
            - Lectura: lista de filas o una sola fila si `uno=True` (formato según `_query_select`).
            - Acción: resultado/contador según `_query_accion` (p. ej., filas afectadas, lastrowid, etc.).

        Raises:
            Exception: Re-lanza errores del driver/adapter subyacente.

        Nota:
            La detección del tipo de sentencia se basa en `sql.strip().split()[0].upper()`.
        """

        comando = sql.strip().split()[0].upper() if sql else ""
        if comando in {"SELECT", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"}:
            return await self._query_select(sql, params, conexion, uno)
        else:
            return await self._query_accion(sql, params, conexion)

    async def _query_select(self, sql: str, params=None, conexion=None, uno: bool = False) -> Union[List[Dict], Dict, None]:
        """
        SELECT/SHOW/etc. Si `conexion` es None, usa una conexión propia vía _PseudoPool.
        Devuelve el número de filas obtenidas
        """
        if conexion is not None:
            async with conexion.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                if uno:
                    return await cursor.fetchone()
                return await cursor.fetchall()
        else:
            if self.pool is None:
                await self.conectar()
            async with self.pool.acquire() as cx:
                async with cx.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, params)
                    if uno:
                        return await cursor.fetchone()
                    return await cursor.fetchall()

    async def _query_accion(self, sql: str, params=None, conexion=None) -> int:
        """
        INSERT/UPDATE/DELETE/etc. Guarda `ultimo_insert_id` cuando aplique.
        Devuelve el número de filas afectadas
        """
        if conexion is not None:
            async with conexion.cursor() as cursor:
                filas = await cursor.execute(sql, params)
                self.ultimo_insert_id = cursor.lastrowid
                return filas
        else:
            if self.pool is None:
                await self.conectar()

            async with self.pool.acquire() as cx:
                try:
                    async with cx.cursor() as cursor:
                        filas = await cursor.execute(sql, params)
                        self.ultimo_insert_id = cursor.lastrowid
                    await cx.commit()
                    return filas
                except Exception as e:
                    try:
                        await cx.rollback()
                    except Exception:
                        pass
                    if self.logger:
                        self.logger.error("Error en _query_accion: %s", e)
                    raise

    async def call_proc(self, nombre: str, parametros: tuple = (), conexion=None, uno: bool = True) -> Optional[Union[dict, List[dict]]]:
        """
        Ejecuta un procedimiento almacenado.
        - Si devuelve SELECT, retorna dict/list; si no devuelve nada, None.
        - Si `conexion` es None, abre/cierra conexión propia.
        """
        sql = f"CALL {nombre}({', '.join(['%s'] * len(parametros))})" if parametros else f"CALL {nombre}()"

        if conexion is not None:
            async with conexion.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, parametros)
                try:
                    return await cursor.fetchone() if uno else await cursor.fetchall()
                except Exception:
                    return None
        else:
            if self.pool is None:
                await self.conectar()
            async with self.pool.acquire() as cx:
                try:
                    async with cx.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(sql, parametros)
                        try:
                            resultado = await cursor.fetchone() if uno else await cursor.fetchall()
                        except Exception:
                            resultado = None
                    await cx.commit()
                    return resultado
                except Exception as e:
                    try:
                        await cx.rollback()
                    except Exception:
                        pass
                    if self.logger:
                        self.logger.error("Error en call_proc('%s'): %s", nombre, e)
                    raise


class DictCursorWrapper:
    """
    Envoltura para un cursor async (compatibilidad con código previo si se usaba).
    """
    def __init__(self, cursor):
        self._cursor = cursor
        self._columns = None

    async def execute(self, *args, **kwargs):
        resultado = await self._cursor.execute(*args, **kwargs)
        self._columns = [desc[0] for desc in self._cursor.description]
        return resultado

    async def fetchone(self) -> dict | None:
        row = await self._cursor.fetchone()
        if row is None or self._columns is None:
            return None
        return dict(zip(self._columns, row))

    async def fetchall(self) -> list[dict]:
        rows = await self._cursor.fetchall()
        if self._columns is None:
            self._columns = [desc[0] for desc in self._cursor.description]
        return [dict(zip(self._columns, row)) for row in rows]

    async def close(self):
        await self._cursor.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

