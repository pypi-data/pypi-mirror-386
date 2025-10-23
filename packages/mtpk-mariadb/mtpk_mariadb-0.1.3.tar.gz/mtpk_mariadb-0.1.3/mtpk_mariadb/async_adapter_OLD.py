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

# Creamos conversores personalizados
custom_conv = conversions.copy()
custom_conv[FIELD_TYPE.DATE] = str
custom_conv[FIELD_TYPE.DATETIME] = str
custom_conv[FIELD_TYPE.TIMESTAMP] = str
custom_conv[FIELD_TYPE.DECIMAL] = Decimal
custom_conv[FIELD_TYPE.NEWDECIMAL] = Decimal

class AsyncDatabase:
    """
    Clase AsyncDatabase para entornos asíncronos como FastAPI con Uvicorn.
    Usa aiomysql como backend de conexión.
    """

    def __init__(self, host: str, user: str, password: str, db: str, port: int = 3306, logger: Optional[Logger] = None):
        """
        Inicializa la configuración de conexión.

        - Args:
            - `host`      (str): Dirección del servidor de base de datos.
            - `user`      (str): Usuario.
            - `password`  (str): Contraseña.
            - `db`        (str): Nombre de la base de datos.
            - `port`      (int): Puerto de conexión (default 3306).
            - `logger`    (Logger, opcional): Logger para eventos e informes.
        """
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.logger = logger
        self.pool = None
        self.tablas: Dict[str, Tabla] = {}
        self.ultimo_insert_id: Optional[int] = None
    
                    
    # @asynccontextmanager
    # async def transaccion_OLD(self):
    #     """
    #     Context manager para ejecutar múltiples operaciones dentro de una transacción.
    #     """
    #     await self.conectar()
    #     async with self.pool.acquire() as conexion:
    #         try:
    #             await conexion.begin()
    #             yield conexion
    #             await conexion.commit()
    #         except Exception as e:
    #             try:
    #                 await conexion.rollback()
    #             except Exception as rollback_error:
    #                 if self.logger:
    #                     self.logger.error(f"❌ Fallo en rollback: {rollback_error}")
    #            raise e
    
    # Bandera transaccional por coroutine (no global)
    _tx_flag: ContextVar[bool] = ContextVar("mtpk_tx_flag", default=False)

    def en_transaccion(self) -> bool:
        """Devuelve True si, en esta coroutine, hay una transacción abierta por este AsyncDatabase."""
        return self._tx_flag.get()

    # @asynccontextmanager
    # async def transaccion_OLD(self):
    #     """
    #     Abre una conexión directa (sin pool) para una transacción/operación puntual.
    #     Se cierra SIEMPRE al salir.

    #     Args:
    #         autocommit (bool): Si True, cada consulta se confirma automáticamente.
    #                         Si False, se abre transacción explícita con BEGIN/COMMIT.
    #     """
    #     await self.conectar()
    #     async with self.pool.acquire() as conexion:
    #         try:
    #             await conexion.begin()
    #             # --- AQUI encendemos la bandera y guardamos el token para restaurar luego ---
    #             token = self._tx_flag.set(True)

    #             try:
    #                 yield conexion
    #                 await conexion.commit()
    #             except Exception as e:
    #                 try:
    #                     await conexion.rollback()
    #                 except Exception as rollback_error:
    #                     if self.logger:
    #                         self.logger.error(f"❌ Fallo en rollback: {rollback_error}")
    #                 raise e
    #             finally:
    #                 # --- AQUI restauramos el valor anterior de la bandera pase lo que pase ---
    #                 self._tx_flag.reset(token)

    #         except Exception:
    #             raise        
    
    @asynccontextmanager
    async def transaccion(self):
        """
        Abre una transacción usando una conexión del pool.
        Se asegura commit/rollback y restaura la bandera de transacción (_tx_flag).
        """
        await self.conectar()
        async with self.pool.acquire() as conexion:
            # Comenzamos la transacción y encendemos bandera solo si begin() tuvo éxito
            await conexion.begin()
            token = self._tx_flag.set(True)
            try:
                # Cede el control al bloque del llamante
                yield conexion
            except Exception as e:
                # Si algo falla dentro, intentamos rollback
                try:
                    await conexion.rollback()
                except Exception as rollback_error:
                    if self.logger:
                        self.logger.error("❌ Fallo en rollback: %s", rollback_error)
                # Repropaga la excepción original
                raise
            else:
                # Si no hubo excepción, intentamos commit
                try:
                    await conexion.commit()
                except Exception as commit_error:
                    # Si el commit falla, intentamos rollback defensivo y repropagamos
                    try:
                        await conexion.rollback()
                    except Exception as rollback_error:
                        if self.logger:
                            self.logger.error("❌ Fallo en rollback tras error de commit: %s", rollback_error)
                    raise
            finally:
                # Restablece la bandera pase lo que pase
                self._tx_flag.reset(token)

    @asynccontextmanager
    async def transaccion_simple(self, autocommit: bool = False):
        """
        Abre una conexión directa (sin pool) para una transacción/operación puntual.
        Se cierra SIEMPRE al salir.
        """
        cx = await aiomysql.connect(
            host=self.host, user=self.user, password=self.password,
            db=self.db, port=self.port, autocommit=autocommit, conv=custom_conv
        )
        try:
            if not autocommit:
                await cx.begin()
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
            cx.close()
            try:
                await cx.wait_closed()
            except Exception:
                pass 
                    
    async def conectar(self):
        """
        Crea un pool de conexiones asíncronas si no está ya activo.
        """
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                user=self.user,
                password=self.password,
                db=self.db,
                port=self.port,
                autocommit=False,
                conv = custom_conv,
                minsize=0,      # 🔑 no abre ninguna conexión por adelantado
                maxsize=10,     # o el valor que uses normalmente
                pool_recycle=1800  # recomendable: reciclar conexiones largas
            )

    
    async def cerrar(self) -> None:
        """
        Cierra el pool de conexiones aiomysql asociado.
        """
        try:
            if hasattr(self, "pool") and self.pool:
                if not getattr(self.pool, "_closed", False):
                    self.pool.close()
                    await self.pool.wait_closed()
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
        tabla.set_database(self)

    def get_tabla(self, nombre: str) -> Tabla:
        """
        Recupera una tabla registrada por su nombre.

        - Args:
            `nombre` (str): Nombre de la tabla.

        Returns:
            Tabla: Objeto de tabla registrada.
        """
        if nombre not in self.tablas:
            raise KeyError(f"La tabla '{nombre}' no está registrada.")
        return self.tablas[nombre]

    
    # async def query_multi_action_OLD(self, sql: str, lista_valores: List[tuple], conexion=None) -> int:
    #     """
    #     Ejecuta múltiples acciones SQL con la misma sentencia y diferentes valores usando `executemany`.

    #     - Args:
    #         - `sql` (str): Consulta SQL con placeholders (%s).
    #         - `lista_valores` (List[tuple]): Lista de tuplas con los valores a aplicar.
    #         - `conexion` (aiomysql.Connection, opcional): Conexión activa.

    #     Returns:
    #         int: Número total de filas afectadas.
    #     """
    #     if not lista_valores:
    #         return 0

    #     propia = False
    #     if conexion is None:
    #         await self.conectar()
    #         conexion = await self.pool.acquire()
    #         propia = True

    #     total_filas = 0
    #     try:
            
    #         async with conexion.cursor() as cursor:
    #             # Ejecuta todas las filas en un único paso
    #             total_filas = await cursor.executemany(sql, lista_valores)
    #             self.ultimo_insert_id = cursor.lastrowid

    #         if propia:
    #             await conexion.commit()

    #         return total_filas

    #     except Exception as e:
    #         if propia:
    #             await conexion.rollback()
    #         raise

    #     finally:
    #         if propia:
    #             self.pool.release(conexion)

    async def query_multi_action(self, sql: str, lista_valores: List[tuple], conexion=None) -> int:
        """
        Ejecuta múltiples acciones SQL con la misma sentencia y diferentes valores usando `executemany`.

        - Args:
            - `sql` (str): Consulta SQL con placeholders (%s).
            - `lista_valores` (List[tuple]): Lista de tuplas con los valores a aplicar.
            - `conexion` (aiomysql.Connection, opcional): Conexión activa.

        Returns:
            int: Número total de filas afectadas.
        """
        if conexion is not None:
            async with conexion.cursor() as cursor:
                total_filas = await cursor.executemany(sql, lista_valores)
                self.ultimo_insert_id = cursor.lastrowid
                return total_filas
        else:
            await self.conectar()
            async with self.pool.acquire() as conexion:
                try:
                    async with conexion.cursor() as cursor:
                        total_filas = await cursor.executemany(sql, lista_valores)
                        self.ultimo_insert_id = cursor.lastrowid
                    await conexion.commit()
                    return total_filas
                except Exception:
                    await conexion.rollback()
                    raise


    async def query(self, sql: str, params=None, conexion=None, uno: bool = False):
        """
        Ejecuta una consulta SQL, detectando automáticamente si es de lectura o acción.

        - Args:
            - `sql`         (str): Consulta SQL.
            - `params`      (tuple o dict, opcional): Parámetros para la consulta.
            - `conexion`    (aiomysql.Connection, opcional): Conexión externa si se desea controlar la transacción.
            - `uno` (bool): Si True, se espera un único resultado (SELECT).

        Returns:
            List[Dict] si es SELECT, o int si es acción (nº de filas afectadas).
        """
        comando = sql.strip().split()[0].upper()
        if comando in {"SELECT", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"}:
            return await self._query_select(sql, params, conexion, uno)
        else:
            return await self._query_accion(sql, params, conexion)
           
    # async def _query_select_OLD(self, sql: str, params=None, conexion=None, uno: bool = False) -> List[Dict]:
    #     """
    #     Ejecuta una consulta de lectura (SELECT, SHOW, DESC...).

    #     - Args:
    #         - `sql`         (str): Consulta SQL de lectura.
    #         - `params`      (tuple o dict, opcional): Parámetros de la consulta.
    #         - `conexion`    (aiomysql.Connection, opcional): Conexión a reutilizar si se gestiona externamente.
    #         - `uno`         (bool): Si True, se espera un único resultado.

    #     Returns:
    #         List[Dict]: Lista de resultados como diccionarios.
    #     """
    #     propia = False
    #     if conexion is None:
    #         await self.conectar()
    #         conexion = await self.pool.acquire()
    #         propia = True

    #     try:
    #         async with conexion.cursor(aiomysql.DictCursor) as cursor:
    #             await cursor.execute(sql, params)
    #             if uno:
    #                 return await cursor.fetchone()
    #             return await cursor.fetchall()
    #     finally:
    #         if propia:
    #             self.pool.release(conexion)
    
    async def _query_select(self, sql: str, params=None, conexion=None, uno: bool = False) -> List[Dict]:
        """
        Ejecuta una consulta de lectura (SELECT, SHOW, DESC...).

        - Args:
            - `sql`         (str): Consulta SQL de lectura.
            - `params`      (tuple o dict, opcional): Parámetros de la consulta.
            - `conexion`    (aiomysql.Connection, opcional): Conexión a reutilizar si se gestiona externamente.
            - `uno`         (bool): Si True, se espera un único resultado.

        Returns:
            List[Dict]: Lista de resultados como diccionarios.
        """
        if conexion is not None:
            async with conexion.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                if uno:
                    return await cursor.fetchone()
                return await cursor.fetchall()
        else:
            await self.conectar()
            async with self.pool.acquire() as conexion:
                async with conexion.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, params)
                    if uno:
                        return await cursor.fetchone()
                    return await cursor.fetchall()


    # async def _query_accion_OLD(self, sql: str, params=None, conexion=None) -> int:
    #     """
    #     Ejecuta una acción de escritura (INSERT, UPDATE, DELETE, etc.).
    #     Guarda `ultimo_insert_id` si aplica.

    #     - Args:
    #         - `sql`         (str): Sentencia SQL.
    #         - `params`      (tuple o dict, opcional): Parámetros de la consulta.
    #         - `conexion`    (aiomysql.Connection, opcional): Conexión a reutilizar.

    #     Returns:
    #         int: Número de filas afectadas por la operación.
    #     """
    #     propia = False
    #     if conexion is None:
    #         await self.conectar()
    #         conexion = await self.pool.acquire()
    #         propia = True

    #     try:
    #         async with conexion.cursor() as cursor:
    #             filas = await cursor.execute(sql, params)
    #             self.ultimo_insert_id = cursor.lastrowid
    #             if propia:
    #                 await conexion.commit()
    #             return filas
    #     except Exception as e:
    #         if propia:
    #             await conexion.rollback()
    #         if self.logger:
    #             self.logger.error(f"Error en _query_accion: {e}")
    #         raise
    #     finally:
    #         if propia:
    #             self.pool.release(conexion)
    
    async def _query_accion(self, sql: str, params=None, conexion=None) -> int:
        """
        Ejecuta una acción de escritura (INSERT, UPDATE, DELETE, etc.).
        Guarda `ultimo_insert_id` si aplica.

        - Args:
            - `sql`         (str): Sentencia SQL.
            - `params`      (tuple o dict, opcional): Parámetros de la consulta.
            - `conexion`    (aiomysql.Connection, opcional): Conexión a reutilizar.

        Returns:
            int: Número de filas afectadas por la operación.
        """
        if conexion is not None:
            async with conexion.cursor() as cursor:
                filas = await cursor.execute(sql, params)
                self.ultimo_insert_id = cursor.lastrowid
                return filas
        else:
            await self.conectar()
            async with self.pool.acquire() as conexion:
                try:
                    async with conexion.cursor() as cursor:
                        filas = await cursor.execute(sql, params)
                        self.ultimo_insert_id = cursor.lastrowid
                    await conexion.commit()
                    return filas
                except Exception as e:
                    await conexion.rollback()
                    if self.logger:
                        self.logger.error(f"Error en _query_accion: {e}")
                    raise
    
    # async def call_proc_OLD(self, nombre: str, parametros: tuple = (), conexion=None, uno: bool = True) -> Optional[Union[dict, List[dict]]]:
    #     """
    #     Ejecuta un procedimiento almacenado.

    #     - Si el procedimiento devuelve un resultado (por SELECT), se recupera y se retorna.
    #     - Si no devuelve nada, retorna None.
        
    #     Args:
    #         nombre (str): Nombre del procedimiento.
    #         parametros (tuple): Parámetros a pasar.
    #         conexion (aiomysql.Connection, opcional): Conexión activa (para transacción).
    #         uno (bool): Si True, retorna solo una fila (fetchone), si False, todas (fetchall).

    #     Returns:
    #         dict, list[dict] o None: Resultado devuelto por el procedimiento, si existe.
    #     """
    #     propia = False
    #     if conexion is None:
    #         await self.conectar()
    #         conexion = await self.pool.acquire()
    #         propia = True

    #     try:
    #         sql = f"CALL {nombre}({', '.join(['%s'] * len(parametros))})" if parametros else f"CALL {nombre}()"
    #         async with conexion.cursor(aiomysql.DictCursor) as cursor:
    #             await cursor.execute(sql, parametros)
    #             try:
    #                 return await cursor.fetchone() if uno else await cursor.fetchall()
    #             except Exception:
    #                 return None  # El procedimiento no devolvió nada
    #     except Exception as e:
    #         if propia:
    #             await conexion.rollback()
    #         if self.logger:
    #             self.logger.error(f"Error en call_proc('{nombre}'): {e}")
    #         raise
    #     finally:
    #         if propia:
    #             self.pool.release(conexion)
                
    async def call_proc(self, nombre: str, parametros: tuple = (), conexion=None, uno: bool = True) -> Optional[Union[dict, List[dict]]]:
        """
        Ejecuta un procedimiento almacenado.

        - Si el procedimiento devuelve un resultado (por SELECT), se recupera y se retorna.
        - Si no devuelve nada, retorna None.
        
        Args:
            nombre (str): Nombre del procedimiento.
            parametros (tuple): Parámetros a pasar.
            conexion (aiomysql.Connection, opcional): Conexión activa (para transacción).
            uno (bool): Si True, retorna solo una fila (fetchone), si False, todas (fetchall).

        Returns:
            dict, list[dict] o None: Resultado devuelto por el procedimiento, si existe.
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
            await self.conectar()
            async with self.pool.acquire() as conexion:
                try:
                    async with conexion.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(sql, parametros)
                        try:
                            return await cursor.fetchone() if uno else await cursor.fetchall()
                        except Exception:
                            return None
                except Exception as e:
                    await conexion.rollback()
                    if self.logger:
                        self.logger.error(f"Error en call_proc('{nombre}'): {e}")
                    raise




class DictCursorWrapper:
    """
    Envoltura para un cursor asyncmy que devuelve resultados como diccionarios.
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

