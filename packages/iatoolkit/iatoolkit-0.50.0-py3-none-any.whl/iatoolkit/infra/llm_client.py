# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from iatoolkit.infra.llm_proxy import LLMProxy
from iatoolkit.repositories.models import Company, LLMQuery
from iatoolkit.repositories.llm_query_repo import LLMQueryRepo
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from iatoolkit.common.util import Utility
from injector import inject
import time
import markdown2
import os
import logging
import json
from iatoolkit.common.exceptions import IAToolkitException
import threading
import re
import tiktoken
from typing import Dict, Optional, List
from iatoolkit.services.dispatcher_service import Dispatcher

CONTEXT_ERROR_MESSAGE = 'Tu consulta supera el límite de contexto, recarga la página para limpiarlo (esto demora un poco ...)'

class llmClient:
    _llm_clients_cache = {}      # class attribute, for the clients cache
    _clients_cache_lock = threading.Lock()  # secure lock cache access

    @inject
    def __init__(self,
                 llmquery_repo: LLMQueryRepo,
                 llm_proxy_factory: LLMProxy,
                 util: Utility
                 ):
        self.llmquery_repo = llmquery_repo
        self.llm_proxy_factory = llm_proxy_factory
        self.util = util
        self._dispatcher = None # Cache for the lazy-loaded dispatcher

        # get the model from the environment variable
        self.model = os.getenv("LLM_MODEL", "")
        if not self.model:
            raise IAToolkitException(IAToolkitException.ErrorType.API_KEY,
                               "La variable de entorno 'LLM_MODEL' no está configurada.")

        # library for counting tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4o")

        # max number of sql retries
        self.MAX_SQL_RETRIES = 1

    @property
    def dispatcher(self) -> 'Dispatcher':
        """Lazy-loads and returns the Dispatcher instance."""
        if self._dispatcher is None:
            # Import what you need, right when you need it.
            from iatoolkit import current_iatoolkit
            from iatoolkit.services.dispatcher_service import Dispatcher
            # Use the global context proxy to get the injector, then get the service
            self._dispatcher = current_iatoolkit().get_injector().get(Dispatcher)
        return self._dispatcher


    def invoke(self,
               company: Company,
               user_identifier: str,
               previous_response_id: str,
               question: str,
               context: str,
               tools: list[dict],
               text: dict,
               context_history: Optional[List[Dict]] = None,
               ) -> dict:

        f_calls = []  # keep track of the function calls executed by the LLM
        f_call_time = 0
        response = None
        sql_retry_count = 0
        force_tool_name = None
        reasoning = {}

        if 'gpt-5' in self.model:
            text['verbosity'] = "low"
            reasoning = {"effort": 'minimal'}

        try:
            start_time = time.time()
            logging.info(f"calling llm model '{self.model}' with {self.count_tokens(context)} tokens...")

            # get the proxy for the company
            llm_proxy = self.llm_proxy_factory.create_for_company(company)

            # here is the first call to the LLM
            try:
                input_messages = [{
                    "role": "user",
                    "content": context
                }]

                response = llm_proxy.create_response(
                    model=self.model,
                    previous_response_id=previous_response_id,
                    context_history=context_history,
                    input=input_messages,
                    tools=tools,
                    text=text,
                    reasoning=reasoning,
                )
                stats = self.get_stats(response)

            except Exception as e:
                # if the llm api fails: context, api-key, etc
                # log the error and envolve in our own exception
                error_message = f"Error calling LLM API: {str(e)}"
                logging.error(error_message)

                # in case of context error
                if "context_length_exceeded" in str(e):
                    error_message = CONTEXT_ERROR_MESSAGE

                raise IAToolkitException(IAToolkitException.ErrorType.LLM_ERROR, error_message)

            while True:
                # check if there are function calls to execute
                function_calls = False
                stats_fcall = {}
                for tool_call in response.output:
                    if tool_call.type != "function_call":
                        continue

                    # execute the function call through the dispatcher
                    fcall_time = time.time()
                    function_name = tool_call.name
                    args = json.loads(tool_call.arguments)
                    logging.info(f"start execution fcall: {function_name}")
                    try:
                        result = self.dispatcher.dispatch(
                            company_name=company.short_name,
                            action=function_name,
                            **args
                        )
                        force_tool_name = None
                    except IAToolkitException as e:
                        if (e.error_type == IAToolkitException.ErrorType.DATABASE_ERROR and
                            sql_retry_count < self.MAX_SQL_RETRIES):
                            sql_retry_count += 1
                            sql_query_with_error = args.get('query', 'No se pudo extraer la consulta.')
                            original_db_error = str(e.__cause__) if e.__cause__ else str(e)

                            logging.warning(
                                    f"Error de SQL capturado, intentando corregir con el LLM (Intento {sql_retry_count}/{self.MAX_SQL_RETRIES}).")
                            result = self._create_sql_retry_prompt(function_name, sql_query_with_error, original_db_error)

                            # force the next call to be this function
                            force_tool_name = function_name
                        else:
                            error_message = f"Error en dispatch para '{function_name}' tras {sql_retry_count} reintentos: {str(e)}"
                            raise IAToolkitException(IAToolkitException.ErrorType.CALL_ERROR, error_message)
                    except Exception as e:
                        error_message = f"Dispatch error en {function_name} con args {args} -******- {str(e)}"
                        raise IAToolkitException(IAToolkitException.ErrorType.CALL_ERROR, error_message)

                    # add  the return value into the list of messages
                    input_messages.append({
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": str(result)
                    })
                    function_calls = True

                    # log the function call parameters and execution time in secs
                    elapsed = time.time() - fcall_time
                    f_call_identity = {function_name:args, 'time': f'{elapsed:.1f}' }
                    f_calls.append(f_call_identity)
                    f_call_time += elapsed

                    logging.info(f"end execution {function_name} in {elapsed:.1f} secs.")

                if not function_calls:
                    break           # no function call answer to send back to llm

                # send results back to the LLM
                tool_choice_value = "auto"
                if force_tool_name:
                    tool_choice_value = "required"

                response = llm_proxy.create_response(
                    model=self.model,
                    input=input_messages,
                    previous_response_id=response.id,
                    context_history=context_history,
                    reasoning=reasoning,
                    tool_choice=tool_choice_value,
                    tools=tools,
                    text=text
                )
                stats_fcall = self.add_stats(stats_fcall, self.get_stats(response))

            # save the statistices
            stats['response_time']=int(time.time() - start_time)
            stats['sql_retry_count'] = sql_retry_count
            stats['model'] = response.model

            # decode the LLM response
            decoded_response = self.decode_response(response)

            # save the query and response
            query = LLMQuery(user_identifier=user_identifier,
                             task_id=0,
                             company_id=company.id,
                             query=question,
                             output=decoded_response.get('answer', ''),
                             valid_response=decoded_response.get('status', False),
                             response=self.serialize_response(response, decoded_response),
                             function_calls=f_calls,
                             stats=self.add_stats(stats, stats_fcall),
                             answer_time=stats['response_time']
                             )
            self.llmquery_repo.add_query(query)
            logging.info(f"finish llm call in {int(time.time() - start_time)} secs..")
            if function_calls:
                logging.info(f"time within the function calls {f_call_time:.1f} secs.")

            return {
                'valid_response': decoded_response.get('status', False),
                'answer': self.format_html(decoded_response.get('answer', '')),
                'stats': stats,
                'answer_format': decoded_response.get('answer_format', ''),
                'error_message': decoded_response.get('error_message', ''),
                'aditional_data': decoded_response.get('aditional_data', {}),
                'response_id': response.id,
                'query_id': query.id,
            }
        except SQLAlchemyError as db_error:
            # rollback
            self.llmquery_repo.session.rollback()
            logging.error(f"Error de base de datos: {str(db_error)}")
            raise db_error
        except OperationalError as e:
            logging.error(f"Operational error: {str(e)}")
            raise e
        except Exception as e:
            error_message= str(e)

            # log the error in the llm_query table
            query = LLMQuery(user_identifier=user_identifier,
                             task_id=0,
                             company_id=company.id,
                             query=question,
                             output=error_message,
                             response=response.output_text if response else {},
                             valid_response=False,
                             function_calls=f_calls,
                             )
            self.llmquery_repo.add_query(query)

            # in case of context error
            if "context_length_exceeded" in str(e):
                error_message = CONTEXT_ERROR_MESSAGE
            elif "string_above_max_length" in str(e):
                error_message = 'La respuesta es muy extensa, trata de filtrar/restringuir tu consulta'

            raise IAToolkitException(IAToolkitException.ErrorType.LLM_ERROR, error_message)

    def set_company_context(self,
            company: Company,
            company_base_context: str,
            model) -> str:

        logging.info(f"initializing model '{model}' with company context: {self.count_tokens(company_base_context)} tokens...")

        llm_proxy = self.llm_proxy_factory.create_for_company(company)
        try:
            response = llm_proxy.create_response(
                model=model,
                input=[{
                    "role": "system",
                    "content": company_base_context
                }]
            )

        except Exception as e:
            error_message = f"Error calling LLM API: {str(e)}"
            logging.error(error_message)
            raise IAToolkitException(IAToolkitException.ErrorType.LLM_ERROR, error_message)

        return response.id

    def decode_response(self, response) -> dict:
        message = response.output_text
        decoded_response = {
            "status": False,
            "output_text": message,
            "answer": "",
            "aditional_data": {},
            "answer_format": "",
            "error_message": ""
        }

        if response.status != 'completed':
            decoded_response[
                'error_message'] = f'LLM ERROR {response.status}: no se completo tu pregunta, intenta de nuevo ...'
            return decoded_response

        if isinstance(message, dict):
            if 'answer' not in message or 'aditional_data' not in message:
                decoded_response['error_message'] = 'El llm respondio un diccionario invalido: missing "answer" key'
                return decoded_response

            decoded_response['status'] = True
            decoded_response['answer'] = message.get('answer', '')
            decoded_response['aditional_data'] = message.get('aditional_data', {})
            decoded_response['answer_format'] = "dict"
            return decoded_response

        clean_message = re.sub(r'^\s*//.*$', '', message, flags=re.MULTILINE)

        if not ('```json' in clean_message or clean_message.strip().startswith('{')):
            decoded_response['status'] = True
            decoded_response['answer'] = clean_message
            decoded_response['answer_format'] = "plaintext"
            return decoded_response

        try:
            # prepare the message for json load
            json_string = clean_message.strip()
            if json_string.startswith('```json'):
                json_string = json_string[7:]
            if json_string.endswith('```'):
                json_string = json_string[:-3]

            response_dict = json.loads(json_string.strip())
        except Exception as e:
            # --- ESTRATEGIA DE RESPALDO (FALLBACK) CON RESCATE DE DATOS ---
            decoded_response['error_message'] = f'Error decodificando JSON: {str(e)}'

            # Intenta rescatar el contenido de "answer" con una expresión regular más robusta.
            # Este patrón busca "answer": "..." y captura todo hasta que encuentra "," y "aditional_data".
            # re.DOTALL es crucial para que `.` coincida con los saltos de línea en el HTML.
            match = re.search(r'"answer"\s*:\s*"(.*?)"\s*,\s*"aditional_data"', clean_message, re.DOTALL)

            if match:
                # ¡Éxito! Se encontró y extrajo el "answer".
                # Se limpia el contenido de escapes JSON para obtener el HTML puro.
                rescued_answer = match.group(1).replace('\\n', '\n').replace('\\"', '"')

                decoded_response['status'] = True
                decoded_response['answer'] = rescued_answer
                decoded_response['answer_format'] = "plaintext_fallback_rescued"
            else:
                # Si la regex no encuentra nada, usar el texto completo como último recurso.
                decoded_response['status'] = True
                decoded_response['answer'] = clean_message
                decoded_response['answer_format'] = "plaintext_fallback_full"
        else:
            # --- SOLO SE EJECUTA SI EL TRY FUE EXITOSO ---
            if 'answer' not in response_dict or 'aditional_data' not in response_dict:
                decoded_response['error_message'] = f'faltan las claves "answer" o "aditional_data" en el JSON'

                # fallback
                decoded_response['status'] = True
                decoded_response['answer'] = str(response_dict)
                decoded_response['answer_format'] = "json_fallback"
            else:
                # El diccionario JSON es perfecto.
                decoded_response['status'] = True
                decoded_response['answer'] = response_dict.get('answer', '')
                decoded_response['aditional_data'] = response_dict.get('aditional_data', {})
                decoded_response['answer_format'] = "json_string"

        return decoded_response

    def serialize_response(self, response, decoded_response):
        response_dict = {
            "format": decoded_response.get('answer_format', ''),
            "error_message": decoded_response.get('error_message', ''),
            "output": decoded_response.get('output_text', ''),
            "id": response.id,
            "model": response.model,
            "status": response.status,
        }
        return response_dict

    def get_stats(self, response):
        stats_dict = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens
        }
        return stats_dict

    def add_stats(self, stats1: dict, stats2: dict) -> dict:
        stats_dict = {
            "input_tokens": stats1.get('input_tokens', 0) + stats2.get('input_tokens', 0),
            "output_tokens": stats1.get('output_tokens', 0) + stats2.get('output_tokens', 0),
            "total_tokens": stats1.get('total_tokens', 0) + stats2.get('total_tokens', 0),
        }
        return stats_dict


    def _create_sql_retry_prompt(self, function_name: str, sql_query: str, db_error: str) -> str:
        return f"""
        ## ERROR DE EJECUCIÓN DE HERRAMIENTA

        **Estado:** Fallido
        **Herramienta:** `{function_name}`

        La ejecución de la consulta SQL falló.

        **Error específico de la base de datos:**
        {db_error}
        **Consulta SQL que causó el error:**
        sql {sql_query}

        **INSTRUCCIÓN OBLIGATORIA:**
        1.  Analiza el error y corrige la sintaxis de la consulta SQL anterior.
        2.  Llama a la herramienta `{function_name}` **OTRA VEZ**, inmediatamente, con la consulta corregida.
        3.  **NO** respondas al usuario con este mensaje de error. Tu ÚNICA acción debe ser volver a llamar a la herramienta con la solución.
        """

    def format_html(self, answer: str):
        html_answer = markdown2.markdown(answer).replace("\n", "")
        return html_answer

    def count_tokens(self, text):
        # Codifica el texto y cuenta la cantidad de tokens
        tokens = self.encoding.encode(text)
        return len(tokens)