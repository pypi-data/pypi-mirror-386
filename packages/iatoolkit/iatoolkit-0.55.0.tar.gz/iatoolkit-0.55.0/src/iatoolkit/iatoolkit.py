# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from flask import Flask, url_for
from flask_session import Session
from flask_injector import FlaskInjector
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from iatoolkit.common.exceptions import IAToolkitException
from urllib.parse import urlparse
import redis
import logging
import os
from typing import Optional, Dict, Any
from iatoolkit.repositories.database_manager import DatabaseManager
from werkzeug.middleware.proxy_fix import ProxyFix
from injector import Binder, singleton, Injector
from importlib.metadata import version as _pkg_version, PackageNotFoundError

IATOOLKIT_VERSION = "0.55.0"

# global variable for the unique instance of IAToolkit
_iatoolkit_instance: Optional['IAToolkit'] = None


class IAToolkit:
    """
    IAToolkit main class
    """
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """
        Implementa el patrón Singleton
        """
        global _iatoolkit_instance
        if _iatoolkit_instance is None:
            _iatoolkit_instance = super().__new__(cls)
            _iatoolkit_instance._initialized = False
        return _iatoolkit_instance


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Diccionario opcional de configuración que sobrescribe variables de entorno
        """
        if self._initialized:
            return

        self.config = config or {}
        self.app = None
        self.db_manager = None
        self._injector = None
        self.version = IATOOLKIT_VERSION

    @classmethod
    def get_instance(cls) -> 'IAToolkit':
        # get the global IAToolkit instance
        global _iatoolkit_instance
        if _iatoolkit_instance is None:
            _iatoolkit_instance = cls()
        return _iatoolkit_instance

    def create_iatoolkit(self):
        """
            Creates, configures, and returns the Flask application instance.
            this is the main entry point for the application factory.
        """
        if self._initialized and self.app:
            return self.app

        self._setup_logging()

        # Step 1: Create the Flask app instance
        self._create_flask_instance()

        # Step 2: Set up the core components that DI depends on
        self._setup_database()

        # Step 3: Create the Injector and configure all dependencies in one place
        self._injector = Injector(self._configure_core_dependencies)

        # Step 4: Register routes using the fully configured injector
        self._register_routes()

        # Step 5: Initialize FlaskInjector. This is now primarily for request-scoped injections
        # and other integrations, as views are handled manually.
        FlaskInjector(app=self.app, injector=self._injector)

        # Step 6: initialize dispatcher and registered compaies
        self._init_dispatcher_and_company_instances()

        # Step 7: Finalize setup within the application context
        self._setup_redis_sessions()
        self._setup_cors()
        self._setup_additional_services()
        self._setup_cli_commands()
        self._setup_context_processors()

        # Step 8: define the download_dir for excel's
        self._setup_download_dir()



        logging.info(f"🎉 IAToolkit v{self.version} inicializado correctamente")
        self._initialized = True
        return self.app

    def _get_config_value(self, key: str, default=None):
        # get a value from the config dict or the environment variable
        return self.config.get(key, os.getenv(key, default))

    def _setup_logging(self):
        # Lee el nivel de log desde una variable de entorno, con 'INFO' como valor por defecto.
        log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_name, logging.INFO)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - IATOOLKIT - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
            force=True
        )

    def _register_routes(self):
        """Registers routes by passing the configured injector."""
        from iatoolkit.common.routes import register_views

        # Pass the injector to the view registration function
        register_views(self._injector, self.app)

        logging.info("✅ Routes registered.")

    def _create_flask_instance(self):
        static_folder = self._get_config_value('STATIC_FOLDER') or self._get_default_static_folder()
        template_folder = self._get_config_value('TEMPLATE_FOLDER') or self._get_default_template_folder()

        self.app = Flask(__name__,
                         static_folder=static_folder,
                         template_folder=template_folder)

        is_https = self._get_config_value('USE_HTTPS', 'false').lower() == 'true'
        is_dev = self._get_config_value('FLASK_ENV') == 'development'

        # get the iatoolkit domain
        parsed_url = urlparse(os.getenv('IATOOLKIT_BASE_URL'))
        domain = parsed_url.netloc

        try:
            self.version = _pkg_version("iatoolkit")
        except PackageNotFoundError:
            pass


        self.app.config.update({
            'VERSION': self.version,
            'SERVER_NAME': domain,
            'SECRET_KEY': self._get_config_value('FLASK_SECRET_KEY', 'iatoolkit-default-secret'),
            'SESSION_COOKIE_SAMESITE': "None" if is_https else "Lax",
            'SESSION_COOKIE_SECURE': is_https,
            'SESSION_PERMANENT': False,
            'SESSION_USE_SIGNER': True,
            'JWT_SECRET_KEY': self._get_config_value('JWT_SECRET_KEY', 'iatoolkit-jwt-secret'),
            'JWT_ALGORITHM': 'HS256',
            'JWT_EXPIRATION_SECONDS_CHAT': int(self._get_config_value('JWT_EXPIRATION_SECONDS_CHAT', 3600))
        })

        if parsed_url.scheme == 'https':
            self.app.config['PREFERRED_URL_SCHEME'] = 'https'

        # 2. ProxyFix para no tener problemas con iframes y rutas
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_proto=1)

        # Configuración para tokenizers en desarrollo
        if is_dev:
            os.environ["TOKENIZERS_PARALLELISM"] = "false"

    def _setup_database(self):
        database_uri = self._get_config_value('DATABASE_URI')
        if not database_uri:
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                "DATABASE_URI es requerida (config dict o variable de entorno)"
            )

        self.db_manager = DatabaseManager(database_uri)
        self.db_manager.create_all()
        logging.info("✅ Base de datos configurada correctamente")

    def _setup_redis_sessions(self):
        redis_url = self._get_config_value('REDIS_URL')
        if not redis_url:
            logging.warning("⚠️ REDIS_URL no configurada, usando sesiones en memoria")
            return

        try:
            url = urlparse(redis_url)
            redis_instance = redis.Redis(
                host=url.hostname,
                port=url.port,
                password=url.password,
                ssl=(url.scheme == "rediss"),
                ssl_cert_reqs=None
            )

            self.app.config.update({
                'SESSION_TYPE': 'redis',
                'SESSION_REDIS': redis_instance
            })

            Session(self.app)
            logging.info("✅ Redis y sesiones configurados correctamente")

        except Exception as e:
            logging.error(f"❌ Error configurando Redis: {e}")
            logging.warning("⚠️ Continuando sin Redis")

    def _setup_cors(self):
        """🌐 Configura CORS"""
        # Origins por defecto para desarrollo
        default_origins = [
            "http://localhost:5001",
            "http://127.0.0.1:5001",
            os.getenv('IATOOLKIT_BASE_URL')
        ]

        # Obtener origins adicionales desde configuración/env
        extra_origins = []
        for i in range(1, 11):  # Soporte para CORS_ORIGIN_1 a CORS_ORIGIN_10
            origin = self._get_config_value(f'CORS_ORIGIN_{i}')
            if origin:
                extra_origins.append(origin)

        all_origins = default_origins + extra_origins

        CORS(self.app,
             supports_credentials=True,
             origins=all_origins,
             allow_headers=[
                 "Content-Type", "Authorization", "X-Requested-With",
                 "X-Chat-Token", "x-chat-token"
             ],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

        logging.info(f"✅ CORS configurado para: {all_origins}")


    def _configure_core_dependencies(self, binder: Binder):
        """⚙️ Configures all system dependencies."""
        try:
            # Core dependencies
            binder.bind(Flask, to=self.app)
            binder.bind(DatabaseManager, to=self.db_manager, scope=singleton)

            # Bind all application components by calling the specific methods
            self._bind_repositories(binder)
            self._bind_services(binder)
            self._bind_infrastructure(binder)

            logging.info("✅ Dependencias configuradas correctamente")

        except Exception as e:
            logging.error(f"❌ Error configurando dependencias: {e}")
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                f"❌ Error configurando dependencias: {e}"
            )

    def _bind_repositories(self, binder: Binder):
        from iatoolkit.repositories.document_repo import DocumentRepo
        from iatoolkit.repositories.profile_repo import ProfileRepo
        from iatoolkit.repositories.llm_query_repo import LLMQueryRepo

        from iatoolkit.repositories.vs_repo import VSRepo
        from iatoolkit.repositories.tasks_repo import TaskRepo

        binder.bind(DocumentRepo, to=DocumentRepo)
        binder.bind(ProfileRepo, to=ProfileRepo)
        binder.bind(LLMQueryRepo, to=LLMQueryRepo)
        binder.bind(VSRepo, to=VSRepo)
        binder.bind(TaskRepo, to=TaskRepo)

    def _bind_services(self, binder: Binder):
        from iatoolkit.services.query_service import QueryService
        from iatoolkit.services.tasks_service import TaskService
        from iatoolkit.services.benchmark_service import BenchmarkService
        from iatoolkit.services.document_service import DocumentService
        from iatoolkit.services.prompt_manager_service import PromptService
        from iatoolkit.services.excel_service import ExcelService
        from iatoolkit.services.mail_service import MailService
        from iatoolkit.services.load_documents_service import LoadDocumentsService
        from iatoolkit.services.profile_service import ProfileService
        from iatoolkit.services.jwt_service import JWTService
        from iatoolkit.services.dispatcher_service import Dispatcher
        from iatoolkit.services.branding_service import BrandingService

        binder.bind(QueryService, to=QueryService)
        binder.bind(TaskService, to=TaskService)
        binder.bind(BenchmarkService, to=BenchmarkService)
        binder.bind(DocumentService, to=DocumentService)
        binder.bind(PromptService, to=PromptService)
        binder.bind(ExcelService, to=ExcelService)
        binder.bind(MailService, to=MailService)
        binder.bind(LoadDocumentsService, to=LoadDocumentsService)
        binder.bind(ProfileService, to=ProfileService)
        binder.bind(JWTService, to=JWTService)
        binder.bind(Dispatcher, to=Dispatcher)
        binder.bind(BrandingService, to=BrandingService)

    def _bind_infrastructure(self, binder: Binder):
        from iatoolkit.infra.llm_client import llmClient
        from iatoolkit.infra.llm_proxy import LLMProxy
        from iatoolkit.infra.google_chat_app import GoogleChatApp
        from iatoolkit.infra.mail_app import MailApp
        from iatoolkit.services.auth_service import AuthService
        from iatoolkit.common.util import Utility

        binder.bind(LLMProxy, to=LLMProxy, scope=singleton)
        binder.bind(llmClient, to=llmClient, scope=singleton)
        binder.bind(GoogleChatApp, to=GoogleChatApp)
        binder.bind(MailApp, to=MailApp)
        binder.bind(AuthService, to=AuthService)
        binder.bind(Utility, to=Utility)

    def _setup_additional_services(self):
        Bcrypt(self.app)

    def _init_dispatcher_and_company_instances(self):
        from iatoolkit.company_registry import get_company_registry
        from iatoolkit.services.dispatcher_service import Dispatcher

        # instantiate all the registered companies
        get_company_registry().instantiate_companies(self._injector)

        # use the dispatcher to start the execution of every company
        dispatcher = self._injector.get(Dispatcher)
        dispatcher.start_execution()

    def _setup_cli_commands(self):
        from iatoolkit.cli_commands import register_core_commands
        from iatoolkit.company_registry import get_company_registry

        # 1. Register core commands
        register_core_commands(self.app)
        logging.info("✅ Comandos CLI del núcleo registrados.")

        # 2. Register company-specific commands
        try:
            # Iterate through the registered company names
            all_company_instances = get_company_registry().get_all_company_instances()
            for company_name, company_instance in all_company_instances.items():
                company_instance.register_cli_commands(self.app)

        except Exception as e:
            logging.error(f"❌ Error durante el registro de comandos de compañías: {e}")

    def _setup_context_processors(self):
        # Configura context processors para templates
        @self.app.context_processor
        def inject_globals():
            from iatoolkit.common.session_manager import SessionManager
            from iatoolkit.services.profile_service import ProfileService

            profile_service = self._injector.get(ProfileService)
            user_profile = profile_service.get_current_session_info().get('profile', {})

            return {
                'url_for': url_for,
                'iatoolkit_version': self.version,
                'app_name': 'IAToolkit',
                'user_identifier': SessionManager.get('user_identifier'),
                'company_short_name': SessionManager.get('company_short_name'),
                'user_is_local': user_profile.get('user_is_local'),
                'user_email': user_profile.get('user_email'),
                'iatoolkit_base_url': os.environ.get('IATOOLKIT_BASE_URL', ''),
            }

    def _get_default_static_folder(self) -> str:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))  # .../src/iatoolkit
            return os.path.join(current_dir, "static")
        except:
            return 'static'

    def _get_default_template_folder(self) -> str:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))  # .../src/iatoolkit
            return os.path.join(current_dir, "templates")
        except:
            return 'templates'

    def get_injector(self) -> Injector:
        """Obtiene el injector actual"""
        if not self._injector:
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                f"❌ injector not initialized"
            )
        return self._injector

    def get_dispatcher(self):
        from iatoolkit.services.dispatcher_service import Dispatcher
        if not self._injector:
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                "App no inicializada. Llame a create_app() primero"
            )
        return self._injector.get(Dispatcher)

    def get_database_manager(self) -> DatabaseManager:
        if not self.db_manager:
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                "Database manager no inicializado"
            )
        return self.db_manager

    def _setup_download_dir(self):
        # 1. set the default download directory
        default_download_dir = os.path.join(os.getcwd(), 'iatoolkit-downloads')

        # 3. if user specified one, use it
        download_dir = self.app.config.get('IATOOLKIT_DOWNLOAD_DIR', default_download_dir)

        # 3. save it in the app config
        self.app.config['IATOOLKIT_DOWNLOAD_DIR'] = download_dir

        # 4. make sure the directory exists
        try:
            os.makedirs(download_dir, exist_ok=True)
        except OSError as e:
            raise IAToolkitException(
                IAToolkitException.ErrorType.CONFIG_ERROR,
                "No se pudo crear el directorio de descarga. Verifique que el directorio existe y tenga permisos de escritura."
            )
        logging.info(f"✅ download dir created in: {download_dir}")


def current_iatoolkit() -> IAToolkit:
    return IAToolkit.get_instance()

# Función de conveniencia para inicialización rápida
def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    toolkit = IAToolkit(config)
    toolkit.create_iatoolkit()

    return toolkit.app
