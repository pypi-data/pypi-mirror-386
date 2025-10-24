# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from iatoolkit.common.exceptions import IAToolkitException
from iatoolkit.services.prompt_manager_service import PromptService
from iatoolkit.repositories.llm_query_repo import LLMQueryRepo

from iatoolkit.repositories.models import Company, Function
from iatoolkit.services.excel_service import ExcelService
from iatoolkit.services.mail_service import MailService
from iatoolkit.common.util import Utility
from injector import inject
import logging
import os


class Dispatcher:
    @inject
    def __init__(self,
                 prompt_service: PromptService,
                 llmquery_repo: LLMQueryRepo,
                 util: Utility,
                 excel_service: ExcelService,
                 mail_service: MailService):
        self.prompt_service = prompt_service
        self.llmquery_repo = llmquery_repo
        self.util = util
        self.excel_service = excel_service
        self.mail_service = mail_service
        self.system_functions = _FUNCTION_LIST
        self.system_prompts = _SYSTEM_PROMPT

        self._company_registry = None
        self._company_instances = None

        self.tool_handlers = {
            "iat_generate_excel": self.excel_service.excel_generator,
            "iat_send_email": self.mail_service.send_mail,
        }

    @property
    def company_registry(self):
        """Lazy-loads and returns the CompanyRegistry instance."""
        if self._company_registry is None:
            from iatoolkit.company_registry import get_company_registry
            self._company_registry = get_company_registry()
        return self._company_registry

    @property
    def company_instances(self):
        """Lazy-loads and returns the instantiated company classes."""
        if self._company_instances is None:
            self._company_instances = self.company_registry.get_all_company_instances()
        return self._company_instances

    def start_execution(self):
        # initialize the system functions and prompts
        self.setup_iatoolkit_system()

        """Runs the startup logic for all registered companies."""
        for company in self.company_instances.values():
            company.register_company()
            company.start_execution()

        return True

    def setup_iatoolkit_system(self):
        # create system functions
        for function in self.system_functions:
            self.llmquery_repo.create_or_update_function(
                Function(
                    company_id=None,
                    system_function=True,
                    name=function['function_name'],
                    description= function['description'],
                    parameters=function['parameters']
                )
            )

        # create the system prompts
        i = 1
        for prompt in self.system_prompts:
            self.prompt_service.create_prompt(
                prompt_name=prompt['name'],
                description=prompt['description'],
                order=1,
                is_system_prompt=True,
            )
            i += 1

        # register in the database  every company class
        for company in self.company_instances.values():
            company.register_company()

    def dispatch(self, company_name: str, action: str, **kwargs) -> dict:
        company_key = company_name.lower()

        if company_key not in self.company_instances:
            available_companies = list(self.company_instances.keys())
            raise IAToolkitException(
                IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                f"Empresa '{company_name}' no configurada. Empresas disponibles: {available_companies}"
            )

        # check if action is a system function
        if action in self.tool_handlers:
            return  self.tool_handlers[action](**kwargs)

        company_instance = self.company_instances[company_name]
        try:
            return company_instance.handle_request(action, **kwargs)
        except IAToolkitException as e:
            # Si ya es una IAToolkitException, la relanzamos para preservar el tipo de error original.
            raise e

        except Exception as e:
            logging.exception(e)
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                               f"Error en function call '{action}': {str(e)}") from e

    def get_company_context(self, company_name: str, **kwargs) -> str:
        if company_name not in self.company_instances:
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                               f"Empresa no configurada: {company_name}")

        company_context = ''

        # read the company context from this list of markdown files,
        # company brief, credits, operation description, etc.
        context_dir = os.path.join(os.getcwd(), f'companies/{company_name}/context')
        context_files = self.util.get_files_by_extension(context_dir, '.md', return_extension=True)
        for file in context_files:
            filepath = os.path.join(context_dir, file)
            company_context += self.util.load_markdown_context(filepath)

        # add the schemas for every table or function call responses
        schema_dir = os.path.join(os.getcwd(), f'companies/{company_name}/schema')
        schema_files = self.util.get_files_by_extension(schema_dir, '.yaml', return_extension=True)
        for file in schema_files:
            schema_name = file.split('_')[0]
            filepath = os.path.join(schema_dir, file)
            company_context += self.util.generate_context_for_schema(schema_name, filepath)

        company_instance = self.company_instances[company_name]
        try:
            return company_context + company_instance.get_company_context(**kwargs)
        except Exception as e:
            logging.exception(e)
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                               f"Error en get_company_context de {company_name}: {str(e)}") from e

    def get_company_services(self, company: Company) -> list[dict]:
        # create the syntax with openai response syntax, for the company function list
        tools = []
        functions = self.llmquery_repo.get_company_functions(company)

        for function in functions:
            # make sure is always on
            function.parameters["additionalProperties"] = False

            ai_tool = {
                "type": "function",
                "name": function.name,
                "description": function.description,
                "parameters": function.parameters,
                "strict": True
            }
            tools.append(ai_tool)
        return tools

    def get_user_info(self, company_name: str, user_identifier: str) -> dict:
        if company_name not in self.company_instances:
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                                     f"Empresa no configurada: {company_name}")

        # source 2: external company user
        company_instance = self.company_instances[company_name]
        try:
            raw_user_data = company_instance.get_user_info(user_identifier)
        except Exception as e:
            logging.exception(e)
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                                     f"Error en get_user_info de {company_name}: {str(e)}") from e

        # always normalize the data for consistent structure
        return self._normalize_user_data(raw_user_data)

    def _normalize_user_data(self, raw_data: dict) -> dict:
        """
        Asegura que los datos del usuario siempre tengan una estructura consistente.
        """
        # default values
        normalized_user = {
            "id": raw_data.get("id", 0),
            "username": raw_data.get("id", 0),
            "user_email": raw_data.get("email", ""),
            "user_fullname": raw_data.get("user_fullname", ""),
            "is_local": False,
            "extras": raw_data.get("extras", {})
        }

        # get the extras from the raw data, if any
        extras = raw_data.get("extras", {})
        if isinstance(extras, dict):
            normalized_user.update(extras)

        return normalized_user

    def get_metadata_from_filename(self, company_name: str, filename: str) -> dict:
        if company_name not in self.company_instances:
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                               f"Empresa no configurada: {company_name}")

        company_instance = self.company_instances[company_name]
        try:
            return company_instance.get_metadata_from_filename(filename)
        except Exception as e:
            logging.exception(e)
            raise IAToolkitException(IAToolkitException.ErrorType.EXTERNAL_SOURCE_ERROR,
                               f"Error en get_metadata_from_filename de {company_name}: {str(e)}") from e

    def get_company_instance(self, company_name: str):
        """Returns the instance for a given company name."""
        return self.company_instances.get(company_name)



# iatoolkit system prompts
_SYSTEM_PROMPT = [
    {'name': 'query_main', 'description':'main prompt de iatoolkit'},
    {'name': 'format_styles', 'description':'formatos y estilos de salida'},
    {'name': 'sql_rules', 'description':'instrucciones para generar sql'}
]


# iatoolkit  function calls
_FUNCTION_LIST = [
    {
        "name": "iat_generate_excel",
        "description": "Generador de Excel."
                    "Genera un archivo Excel (.xlsx) a partir de una lista de diccionarios. "
                    "Cada diccionario representa una fila del archivo. "
                    "el archivo se guarda en directorio de descargas."
                    "retorna diccionario con filename, attachment_token (para enviar archivo por mail)"
                    "content_type y download_link",
        "function_name": "iat_generate_excel",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Nombre del archivo de salida (ejemplo: 'reporte.xlsx')",
                    "pattern": "^.+\\.xlsx?$"
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Nombre de la hoja dentro del Excel",
                    "minLength": 1
                },
                "data": {
                    "type": "array",
                    "description": "Lista de diccionarios. Cada diccionario representa una fila.",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number"},
                                {"type": "boolean"},
                                {"type": "null"},
                                {
                                    "type": "string",
                                    "format": "date"
                                }
                            ]
                        }
                    }
                }
            },
            "required": ["filename", "sheet_name", "data"]
        }
    },
    {
        'name': 'Envio de mails',
         'description':  "iatoolkit mail system. "        
            "envia mails cuando un usuario lo solicita."
            "Si no te indican quien envia el correo utiliza la dirección iatoolkit@iatoolkit.com",
         'function_name': "iat_send_email",
         'parameters': {
            "type": "object",
            "properties": {
                "from_email": {"type": "string","description": "dirección de correo electrónico  que esta enviando el email."},
                "recipient": {"type": "string", "description": "email del destinatario"},
                "subject": {"type": "string", "description": "asunto del email"},
                "body": {"type": "string", "description": "HTML del email"},
                "attachments": {
                    "type": "array",
                    "description": "Lista de archivos adjuntos codificados en base64",
                    "items": {
                      "type": "object",
                      "properties": {
                        "filename": {
                          "type": "string",
                          "description": "Nombre del archivo con su extensión (ej. informe.pdf)"
                        },
                        "content": {
                          "type": "string",
                          "description": "Contenido del archivo en b64."
                        },
                        "attachment_token": {
                          "type": "string",
                          "description": "token para descargar el archivo."
                        }
                      },
                      "required": ["filename", "content", "attachment_token"],
                      "additionalProperties": False
                    }
                }
            },
            "required": ["from_email","recipient", "subject", "body", "attachments"]
        }
     }
]
