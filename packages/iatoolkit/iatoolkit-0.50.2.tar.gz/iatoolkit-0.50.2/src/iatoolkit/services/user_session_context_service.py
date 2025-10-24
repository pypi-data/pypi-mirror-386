# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from iatoolkit.infra.redis_session_manager import RedisSessionManager
from typing import List, Dict, Optional
import json
import logging


class UserSessionContextService:
    """
    Gestiona el contexto de la sesión del usuario usando un único Hash de Redis por sesión.
    Esto mejora la atomicidad y la eficiencia.
    """

    def _get_session_key(self, company_short_name: str, user_identifier: str) -> Optional[str]:
        """Devuelve la clave única de Redis para el Hash de sesión del usuario."""
        user_identifier = (user_identifier or "").strip()
        if not company_short_name or not user_identifier:
            return None
        return f"session:{company_short_name}/{user_identifier}"

    def clear_all_context(self, company_short_name: str, user_identifier: str):
        """Limpia el contexto de sesión para un usuario de forma atómica."""
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            # RedisSessionManager.remove(session_key)
            # 'profile_data' should not be deleted
            RedisSessionManager.hdel(session_key, 'context_version')
            RedisSessionManager.hdel(session_key, 'context_history')
            RedisSessionManager.hdel(session_key, 'last_response_id')

    def clear_llm_history(self, company_short_name: str, user_identifier: str):
        """Limpia solo los campos relacionados con el historial del LLM (ID y chat)."""
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            RedisSessionManager.hdel(session_key, 'last_response_id', 'context_history')

    def get_last_response_id(self, company_short_name: str, user_identifier: str) -> Optional[str]:
        session_key = self._get_session_key(company_short_name, user_identifier)
        if not session_key:
            return None
        return RedisSessionManager.hget(session_key, 'last_response_id')

    def save_last_response_id(self, company_short_name: str, user_identifier: str, response_id: str):
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            RedisSessionManager.hset(session_key, 'last_response_id', response_id)

    def save_context_history(self, company_short_name: str, user_identifier: str, context_history: List[Dict]):
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            try:
                history_json = json.dumps(context_history)
                RedisSessionManager.hset(session_key, 'context_history', history_json)
            except (TypeError, ValueError) as e:
                logging.error(f"Error al serializar context_history para {session_key}: {e}")

    def get_context_history(self, company_short_name: str, user_identifier: str) -> Optional[List[Dict]]:
        session_key = self._get_session_key(company_short_name, user_identifier)
        if not session_key:
            return None

        history_json = RedisSessionManager.hget(session_key, 'context_history')
        if not history_json:
            return []

        try:
            return json.loads(history_json)
        except json.JSONDecodeError:
            return []

    def save_profile_data(self, company_short_name: str, user_identifier: str, data: dict):
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            try:
                data_json = json.dumps(data)
                RedisSessionManager.hset(session_key, 'profile_data', data_json)
            except (TypeError, ValueError) as e:
                logging.error(f"Error al serializar profile_data para {session_key}: {e}")

    def get_profile_data(self, company_short_name: str, user_identifier: str) -> dict:
        session_key = self._get_session_key(company_short_name, user_identifier)
        if not session_key:
            return {}

        data_json = RedisSessionManager.hget(session_key, 'profile_data')
        if not data_json:
            return {}

        try:
            return json.loads(data_json)
        except json.JSONDecodeError:
            return {}

    def save_context_version(self, company_short_name: str, user_identifier: str, version: str):
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            RedisSessionManager.hset(session_key, 'context_version', version)

    def get_context_version(self, company_short_name: str, user_identifier: str) -> Optional[str]:
        session_key = self._get_session_key(company_short_name, user_identifier)
        if not session_key:
            return None
        return RedisSessionManager.hget(session_key, 'context_version')

    def save_prepared_context(self, company_short_name: str, user_identifier: str, context: str, version: str):
        """Guarda un contexto de sistema pre-renderizado y su versión, listos para ser enviados al LLM."""
        session_key = self._get_session_key(company_short_name, user_identifier)
        if session_key:
            RedisSessionManager.hset(session_key, 'prepared_context', context)
            RedisSessionManager.hset(session_key, 'prepared_context_version', version)

    def get_and_clear_prepared_context(self, company_short_name: str, user_identifier: str) -> tuple:
        """Obtiene el contexto preparado y su versión, y los elimina para asegurar que se usan una sola vez."""
        session_key = self._get_session_key(company_short_name, user_identifier)
        if not session_key:
            return None, None

        pipe = RedisSessionManager.pipeline()
        pipe.hget(session_key, 'prepared_context')
        pipe.hget(session_key, 'prepared_context_version')
        pipe.hdel(session_key, 'prepared_context', 'prepared_context_version')
        results = pipe.execute()

        # results[0] es el contexto, results[1] es la versión
        return (results[0], results[1]) if results else (None, None)

    # --- Métodos de Bloqueo ---
    def acquire_lock(self, lock_key: str, expire_seconds: int) -> bool:
        """Intenta adquirir un lock. Devuelve True si se adquiere, False si no."""
        # SET con NX (solo si no existe) y EX (expiración) es una operación atómica.
        return RedisSessionManager.set(lock_key, "1", ex=expire_seconds, nx=True)

    def release_lock(self, lock_key: str):
        """Libera un lock."""
        RedisSessionManager.remove(lock_key)

    def is_locked(self, lock_key: str) -> bool:
        """Verifica si un lock existe."""
        return RedisSessionManager.exists(lock_key)