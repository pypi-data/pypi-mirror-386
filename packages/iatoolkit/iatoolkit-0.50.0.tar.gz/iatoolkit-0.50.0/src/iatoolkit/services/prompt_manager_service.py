# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from injector import inject
from iatoolkit.repositories.llm_query_repo import LLMQueryRepo

import logging
from iatoolkit.repositories.profile_repo import ProfileRepo
from collections import defaultdict
from iatoolkit.repositories.models import Prompt, PromptCategory, Company
import os
from iatoolkit.common.exceptions import IAToolkitException
import importlib.resources


class PromptService:
    @inject
    def __init__(self, llm_query_repo: LLMQueryRepo, profile_repo: ProfileRepo):
        self.llm_query_repo = llm_query_repo
        self.profile_repo = profile_repo

    def create_prompt(self,
                      prompt_name: str,
                      description: str,
                      order: int,
                      company: Company = None,
                      category: PromptCategory = None,
                      active: bool = True,
                      is_system_prompt: bool = False,
                      custom_fields: list = []
                      ):

        prompt_filename = prompt_name.lower() + '.prompt'
        if is_system_prompt:
            if not importlib.resources.files('iatoolkit.system_prompts').joinpath(prompt_filename).is_file():
                raise IAToolkitException(IAToolkitException.ErrorType.INVALID_NAME,
                                f'No existe el archivo de prompt de sistemas: {prompt_filename}')
        else:
            template_dir = f'companies/{company.short_name}/prompts'

            relative_prompt_path = os.path.join(template_dir, prompt_filename)
            if not os.path.exists(relative_prompt_path):
                raise IAToolkitException(IAToolkitException.ErrorType.INVALID_NAME,
                               f'No existe el archivo de prompt: {relative_prompt_path}')

        if custom_fields:
            for f in custom_fields:
                if ('data_key' not in f) or ('label' not in f):
                    raise IAToolkitException(IAToolkitException.ErrorType.INVALID_PARAMETER,
                               f'El campo custom_fields debe contener los campos: data_key y label')

                # add default value for data_type
                if 'type' not in f:
                    f['type'] = 'text'

        prompt = Prompt(
                company_id=company.id if company else None,
                name=prompt_name,
                description=description,
                order=order,
                category_id=category.id if category and not is_system_prompt else None,
                active=active,
                filename=prompt_filename,
                is_system_prompt=is_system_prompt,
                custom_fields=custom_fields
            )

        try:
            self.llm_query_repo.create_or_update_prompt(prompt)
        except Exception as e:
            raise IAToolkitException(IAToolkitException.ErrorType.DATABASE_ERROR,
                               f'error creating prompt "{prompt_name}": {str(e)}')

    def get_prompt_content(self, company: Company, prompt_name: str):
        try:
            user_prompt_content = []
            execution_dir = os.getcwd()

            # get the user prompt
            user_prompt = self.llm_query_repo.get_prompt_by_name(company, prompt_name)
            if not user_prompt:
                raise IAToolkitException(IAToolkitException.ErrorType.DOCUMENT_NOT_FOUND,
                                   f"No se encontró el prompt '{prompt_name}' para la empresa '{company.short_name}'")

            prompt_file = f'companies/{company.short_name}/prompts/{user_prompt.filename}'
            absolute_filepath = os.path.join(execution_dir, prompt_file)
            if not os.path.exists(absolute_filepath):
                raise IAToolkitException(IAToolkitException.ErrorType.FILE_IO_ERROR,
                                   f"El archivo para el prompt '{prompt_name}' no existe: {absolute_filepath}")

            try:
                with open(absolute_filepath, 'r', encoding='utf-8') as f:
                    user_prompt_content = f.read()
            except Exception as e:
                raise IAToolkitException(IAToolkitException.ErrorType.FILE_IO_ERROR,
                                   f"Error leyendo el archivo de prompt '{prompt_name}' en {absolute_filepath}: {e}")

            return user_prompt_content

        except IAToolkitException:
            # Vuelve a lanzar las IAToolkitException que ya hemos manejado
            # para que no sean capturadas por el siguiente bloque.
            raise
        except Exception as e:
            logging.exception(
                f"Error al obtener el contenido del prompt para la empresa '{company.short_name}' y prompt '{prompt_name}': {e}")
            raise IAToolkitException(IAToolkitException.ErrorType.PROMPT_ERROR,
                               f'Error al obtener el contenido del prompt "{prompt_name}" para la empresa {company.short_name}: {str(e)}')

    def get_system_prompt(self):
        try:
            system_prompt_content = []

            # read all the system prompts from the database
            system_prompts = self.llm_query_repo.get_system_prompts()

            for prompt in system_prompts:
                try:
                    content = importlib.resources.read_text('iatoolkit.system_prompts', prompt.filename)
                    system_prompt_content.append(content)
                except FileNotFoundError:
                    logging.warning(f"El archivo para el prompt de sistema no existe en el paquete: {prompt.filename}")
                except Exception as e:
                    raise IAToolkitException(IAToolkitException.ErrorType.FILE_IO_ERROR,
                                             f"Error leyendo el archivo de prompt del sistema '{prompt.filename}': {e}")

            # join the system prompts into a single string
            return "\n".join(system_prompt_content)

        except IAToolkitException:
            raise
        except Exception as e:
            logging.exception(
                f"Error al obtener el contenido del prompt de sistema: {e}")
            raise IAToolkitException(IAToolkitException.ErrorType.PROMPT_ERROR,
                               f'Error al obtener el contenido de los prompts de sistema": {str(e)}')

    def get_user_prompts(self, company_short_name: str) -> dict:
        try:
            # validate company
            company = self.profile_repo.get_company_by_short_name(company_short_name)
            if not company:
                return {'error': f'No existe la empresa: {company_short_name}'}

            # get all the prompts
            all_prompts = self.llm_query_repo.get_prompts(company)

            # Agrupar prompts por categoría
            prompts_by_category = defaultdict(list)
            for prompt in all_prompts:
                if prompt.active:
                    if prompt.category:
                        cat_key = (prompt.category.order, prompt.category.name)
                        prompts_by_category[cat_key].append(prompt)

            # Ordenar los prompts dentro de cada categoría
            for cat_key in prompts_by_category:
                prompts_by_category[cat_key].sort(key=lambda p: p.order)

            # Crear la estructura de respuesta final, ordenada por la categoría
            categorized_prompts = []

            # Ordenar las categorías por su 'order'
            sorted_categories = sorted(prompts_by_category.items(), key=lambda item: item[0][0])

            for (cat_order, cat_name), prompts in sorted_categories:
                categorized_prompts.append({
                    'category_name': cat_name,
                    'category_order': cat_order,
                    'prompts': [
                        {
                            'prompt': p.name,
                            'description': p.description,
                            'custom_fields': p.custom_fields,
                            'order': p.order
                        }
                        for p in prompts
                    ]
                })

            return {'message': categorized_prompts}

        except Exception as e:
            logging.error(f"Error en get_prompts: {e}")
            return {'error': str(e)}

