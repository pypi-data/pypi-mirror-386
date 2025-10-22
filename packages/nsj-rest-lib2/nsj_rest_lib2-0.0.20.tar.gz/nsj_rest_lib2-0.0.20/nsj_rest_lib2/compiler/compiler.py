import re

from typing import Any

from nsj_rest_lib2.compiler.compiler_structures import (
    ComponentsCompilerStructure,
    IndexCompilerStructure,
    PropertiesCompilerStructure,
)
from nsj_rest_lib2.compiler.dto_compiler import DTOCompiler
from nsj_rest_lib2.compiler.edl_model.entity_model_base import EntityModelBase
from nsj_rest_lib2.compiler.edl_model.entity_model_root import EntityModelRoot
from nsj_rest_lib2.compiler.edl_model.primitives import REGEX_EXTERNAL_REF
from nsj_rest_lib2.compiler.entity_compiler import EntityCompiler
from nsj_rest_lib2.compiler.model import CompilerResult, RelationDependency
from nsj_rest_lib2.compiler.property_compiler import EDLPropertyCompiler

from nsj_rest_lib2.compiler.util.type_naming_util import (
    compile_dto_class_name,
    compile_entity_class_name,
    compile_namespace_keys,
)

from nsj_rest_lib2.compiler.edl_model.entity_model import EntityModel

from nsj_rest_lib2.settings import get_logger

# TODO GET e POST de relacionamentos 1X1
# TODO Revisar compilação de valores default (sensível a tipos)
# TODO Implementar suporte a conjuntos
# TODO Autenticação nas rotas
# TODO Atualizar o status da entidade pelo worker de compilação (e talvez parar uma compilação, quando se delete uma entidade)
# TODO Classes Abstratas
# TODO Partial Classes
# TODO Migrations
# TODO Criar imagem docker base para as aplicações, usando venv (para poderem atualizar o pydantic)

# TODO Suporte ao "min_items" dos relacionamentos no RestLib1


class EDLCompiler:
    def __init__(self) -> None:
        self._properties_compiler = EDLPropertyCompiler()
        self._dto_compiler = DTOCompiler()
        self._entity_compiler = EntityCompiler()

    def compile_models(
        self, entity_models: dict[str, EntityModel]
    ) -> list[CompilerResult]:

        compiler_results = []
        for entity_model_id in entity_models:
            entity_model = entity_models[entity_model_id]
            compiler_result = self._compile_model(entity_model, entity_models)
            if compiler_result:
                compiler_results.append(compiler_result)

        return compiler_results

    def compile_model_from_edl(
        self,
        edl_json: dict[str, Any],
        dependencies_edls: list[dict[str, Any]],
    ) -> CompilerResult | None:
        entity_model = EntityModel(**edl_json)

        entity_models = []
        for dependency_edl in dependencies_edls:
            if "mixin" in dependency_edl and dependency_edl["mixin"]:
                dependency_entity_model = EntityModelRoot(**dependency_edl)
            else:
                dependency_entity_model = EntityModel(**dependency_edl)
            entity_models.append(dependency_entity_model)

        return self.compile_model(entity_model, entity_models)

    def compile_model(
        self,
        entity_model: EntityModelBase,
        dependencies_models: list[tuple[str, EntityModelBase]],
    ) -> CompilerResult | None:
        entity_models = {}
        for dependency_entity_model in dependencies_models:
            complete_entity_id = dependency_entity_model[0]
            entity_models[complete_entity_id] = dependency_entity_model[1]

        return self._compile_model(entity_model, entity_models)

    def _compile_model(
        self,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        escopo: str | None = None,
        prefx_class_name: str = "",
    ) -> CompilerResult | None:
        if entity_model.mixin:
            return None

        if escopo is None and (isinstance(entity_model, EntityModel)):
            escopo = entity_model.escopo

        if not escopo:
            raise Exception(f"Escopo não definido para a entidade: {entity_model.id}.")

        # Tratando dos dados base para a extensão parcial
        partial_metadata: dict[str, str] | None = None
        partial_base_model: EntityModel | None = None
        if isinstance(entity_model, EntityModel) and entity_model.partial_of:
            if entity_model.partial_of not in entity_models:
                raise Exception(
                    f"Entidade base '{entity_model.partial_of}' não encontrada para a extensão parcial '{entity_model.id}'."
                )

            base_model_candidate = entity_models[entity_model.partial_of]
            if not isinstance(base_model_candidate, EntityModel):
                raise Exception(
                    f"Entidade base '{entity_model.partial_of}' da extensão parcial '{entity_model.id}' é inválida."
                )

            self._validate_partial_model(entity_model, base_model_candidate, entity_models)
            partial_metadata = self._build_partial_metadata(
                entity_model, base_model_candidate
            )
            partial_base_model = base_model_candidate

        # Criando um mapa de índices por nome de property
        # TODO Implementar tratamento dos índices de apoio às query (não de unicidade)
        map_indexes_by_property: dict[str, list[IndexCompilerStructure]] = {}
        map_unique_by_property: dict[str, IndexCompilerStructure] = {}
        self._make_unique_map_by_property(
            map_indexes_by_property, map_unique_by_property, entity_model, entity_models
        )

        # Criando uma cópia das coleções necessárias à compilação das properties
        # (a ideia é ser possível alterar as coleções sem afetar a entidade modelo,
        # o que será necessário para o tratamento de traits, etc - os quais serão
        # uma classe nova, resultado da união dessas propriedades).
        properties_structure = PropertiesCompilerStructure()
        self._make_properties_structures(
            properties_structure, entity_model, entity_models
        )

        # Criando a lista de atributos do DTO e da Entity; e recuperando as chaves primarias
        (
            ast_dto_attributes,
            ast_entity_attributes,
            props_pk,
            aux_classes,
            related_imports,
            relations_dependencies,
            fixed_filters,
        ) = self._properties_compiler.compile(
            properties_structure,
            map_unique_by_property,
            escopo,
            entity_model,
            entity_models,
            prefx_class_name,
        )

        # Adicionando os imports da extensão parcial
        if partial_metadata:
            related_imports.append(
                (
                    partial_metadata["module"],
                    partial_metadata["dto_class"],
                    partial_metadata["entity_class"],
                )
            )

        related_imports = self._deduplicate_related_imports(related_imports)

        # Gerando o buffer para os códigos de DTO e Entity
        dto_code = ""
        entity_code = ""
        relations_dependencies_complete = []

        # Carregando a estrutura de compilação dos components
        components_structure = ComponentsCompilerStructure()
        self._make_components_structures(
            components_structure, entity_model, entity_models
        )

        # Gerando o código das entidades filhas (components)
        for component_key in components_structure.components:
            component = components_structure.components[component_key]
            component_compiled = self._compile_model(
                component,
                entity_models,
                escopo,
                prefx_class_name=f"{prefx_class_name}_{entity_model.id}",
            )

            if not component_compiled:
                raise Exception(
                    f"Erro ao compilar o component '{component_key}' da entidade '{entity_model.id}'. Gerou saída None, como se fosse um mixin."
                )

            # Guardando o código gerado no buffer
            if component_compiled.dto_code:
                dto_code += component_compiled.dto_code + "\n\n"
            if component_compiled.entity_code:
                entity_code += component_compiled.entity_code + "\n\n"
            if component_compiled.relations_dependencies:
                relations_dependencies_complete.extend(
                    component_compiled.relations_dependencies
                )

        # Gerando o código do DTO
        dto_class_name, code_dto = self._dto_compiler.compile(
            entity_model,
            ast_dto_attributes,
            aux_classes,
            related_imports,
            fixed_filters,
            prefx_class_name,
            partial_metadata,
        )

        # Gerando o código da Entity
        entity_class_name, code_entity = self._entity_compiler.compile(
            entity_model,
            ast_entity_attributes,
            props_pk,
            prefx_class_name,
            partial_metadata,
        )

        # Extendendo os buffers com os códigos gerados
        dto_code += code_dto
        entity_code += code_entity

        # Adicionando as dependências das relações
        relations_dependencies_complete.extend(relations_dependencies)

        # Adicionando as dependências da extensão parcial
        if partial_metadata and partial_base_model:
            relation_dependency = RelationDependency()
            if not partial_base_model.api or not partial_base_model.api.resource:
                raise Exception(
                    f"Entidade base '{partial_base_model.id}' não possui configuração de API necessária para extensão parcial."
                )
            relation_dependency.entity_resource = partial_base_model.api.resource
            relation_dependency.entity_scope = partial_base_model.escopo
            relation_dependency.tenant = partial_base_model.tenant
            relation_dependency.grupo_empresarial = partial_base_model.grupo_empresarial
            relations_dependencies_complete.append(relation_dependency)

        # Construindo o resultado
        compiler_result = CompilerResult()
        compiler_result.entity_class_name = entity_class_name
        compiler_result.entity_code = entity_code
        compiler_result.dto_class_name = dto_class_name
        compiler_result.dto_code = dto_code

        # Compilando questões das APIs
        if isinstance(entity_model, EntityModel):
            compiler_result.api_expose = entity_model.api.expose
            compiler_result.api_resource = entity_model.api.resource
            compiler_result.api_verbs = entity_model.api.verbs
            compiler_result.relations_dependencies = relations_dependencies_complete

        get_logger().debug(f"código gerado para a entidade: {entity_model.id}")
        get_logger().debug("DTO Code:")
        get_logger().debug(f"\n{dto_code}")
        get_logger().debug("Entity Code:")
        get_logger().debug(f"\n{entity_code}")

        return compiler_result

    def _validate_partial_model(
        self,
        partial_model: EntityModel,
        base_model: EntityModel,
        entity_models: dict[str, EntityModel],
    ) -> None:
        base_properties_structure = PropertiesCompilerStructure()
        self._make_properties_structures(
            base_properties_structure,
            base_model,
            entity_models,
        )
        aggregated_base_properties = set(base_properties_structure.properties.keys())

        duplicated_properties = aggregated_base_properties.intersection(
            set(partial_model.properties.keys())
        )
        if duplicated_properties:
            raise Exception(
                f"Extensão parcial '{partial_model.id}' redefine propriedades da entidade base '{base_model.id}': {sorted(duplicated_properties)}."
            )

        lists_to_check = {
            "required": partial_model.required,
            "main_properties": partial_model.main_properties,
            "partition_data": partial_model.partition_data,
            "search_properties": partial_model.search_properties,
            "metric_label": partial_model.metric_label,
        }

        for list_name, values in lists_to_check.items():
            if not values:
                continue

            conflicts = [
                value
                for value in values
                if isinstance(value, str) and value in aggregated_base_properties
            ]
            if conflicts:
                raise Exception(
                    f"Extensão parcial '{partial_model.id}' utiliza propriedades da entidade base '{base_model.id}' em '{list_name}': {conflicts}."
                )

        link = partial_model.repository.link_to_base
        if not link:
            raise Exception(
                f"Extensão parcial '{partial_model.id}' requer configuração 'link_to_base' no bloco 'repository'."
            )

        if not link.base_property:
            raise Exception(
                f"Extensão parcial '{partial_model.id}' requer 'base_property' definido em 'link_to_base'."
            )

        if not link.column:
            raise Exception(
                f"Extensão parcial '{partial_model.id}' requer 'column' definido em 'link_to_base'."
            )

        if link.base_property not in aggregated_base_properties:
            raise Exception(
                f"'base_property' '{link.base_property}' não corresponde a uma propriedade da entidade base '{base_model.id}'."
            )

        # if not base_model.api or not base_model.api.resource:
        #     raise Exception(
        #         f"Entidade base '{base_model.id}' não possui configuração de API compatível com extensões parciais."
        #     )

    def _build_partial_metadata(
        self, partial_model: EntityModel, base_model: EntityModel
    ) -> dict[str, str]:
        link = partial_model.repository.link_to_base
        if link is None:
            raise Exception(
                f"Extensão parcial '{partial_model.id}' está sem configuração 'link_to_base'."
            )

        grupo_key, tenant_key, default_key = compile_namespace_keys(
            base_model.tenant, base_model.grupo_empresarial
        )
        namespace = self._resolve_namespace_key(
            base_model.tenant,
            base_model.grupo_empresarial,
            grupo_key,
            tenant_key,
            default_key,
        )

        return {
            "module": namespace,
            "dto_class": compile_dto_class_name(base_model.id),
            "entity_class": compile_entity_class_name(base_model.id),
            "relation_field": link.column,
            "related_entity_field": link.base_property,
        }

    def _resolve_namespace_key(
        self,
        tenant: str | int | None,
        grupo_empresarial,
        grupo_key: str,
        tenant_key: str,
        default_key: str,
    ) -> str:
        has_tenant = tenant not in (None, 0, "0")
        has_grupo = (
            grupo_empresarial
            and str(grupo_empresarial) != "00000000-0000-0000-0000-000000000000"
        )

        if has_tenant and has_grupo:
            return grupo_key
        if has_tenant:
            return tenant_key
        return default_key

    def _deduplicate_related_imports(
        self, related_imports: list[tuple[str, str, str]]
    ) -> list[tuple[str, str, str]]:
        deduped: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str, str]] = set()

        for import_tuple in related_imports:
            if import_tuple in seen:
                continue
            seen.add(import_tuple)
            deduped.append(import_tuple)

        return deduped

    def _make_components_structures(
        self,
        components_structure: ComponentsCompilerStructure,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
    ):
        if not entity_model:
            return

        # Populando com os components da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_components_structures(
                components_structure,
                super_model,
                entity_models,
            )

        # Populando com os components do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_components_structures(
                components_structure,
                trait_model,
                entity_models,
            )

        # Populando com os components da entidade atual
        if entity_model.components:
            components_structure.components.update(entity_model.components)

    def _make_properties_structures(
        self,
        properties_structure: PropertiesCompilerStructure,
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
    ):
        if not entity_model:
            return

        # Populando com as propriedades dos mixins
        if entity_model.mixins:
            for mixin_id in entity_model.mixins:
                if mixin_id not in entity_models:
                    raise Exception(f"Mixin '{mixin_id}' não encontrado.")

                mixin_model = entity_models[mixin_id]
                self._make_properties_structures(
                    properties_structure,
                    mixin_model,
                    entity_models,
                )

        # Populando com as propriedades da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_properties_structures(
                properties_structure,
                super_model,
                entity_models,
            )

        # Populando com as propriedades do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_properties_structures(
                properties_structure,
                trait_model,
                entity_models,
            )

        # Populando com as propriedades da entidade atual
        properties_structure.properties.update(entity_model.properties)
        if entity_model.main_properties:
            for main_property in entity_model.main_properties:
                if not isinstance(main_property, str):
                    continue

                if "/" in main_property:
                    path_parts = [
                        part.strip() for part in main_property.split("/") if part
                    ]
                    if len(path_parts) < 2 or not path_parts[0]:
                        raise Exception(
                            f"Propriedade resumo inválida '{main_property}' na entidade '{entity_model.id}'."
                        )

                    relation_name = path_parts[0]
                    resume_path_parts = path_parts[1:]
                    resume_field = ".".join(resume_path_parts)

                    if relation_name not in properties_structure.main_properties:
                        properties_structure.main_properties.append(relation_name)

                    resume_fields = properties_structure.main_resume_fields.setdefault(
                        relation_name, []
                    )

                    if resume_field and resume_field not in resume_fields:
                        resume_fields.append(resume_field)
                else:
                    if main_property not in properties_structure.main_properties:
                        properties_structure.main_properties.append(main_property)
        if entity_model.required:
            properties_structure.required.extend(entity_model.required)
        if entity_model.partition_data:
            properties_structure.partition_data.extend(entity_model.partition_data)
        if entity_model.search_properties:
            properties_structure.search_properties.extend(
                entity_model.search_properties
            )
        if entity_model.metric_label:
            properties_structure.metric_label.extend(entity_model.metric_label)

        if entity_model.trait_properties:
            properties_structure.trait_properties.update(entity_model.trait_properties)

        if entity_model.extends_properties:
            properties_structure.extends_properties.update(
                entity_model.extends_properties
            )

        if entity_model.composed_properties:
            properties_structure.composed_properties.update(
                entity_model.composed_properties
            )

        if entity_model.repository.properties:
            properties_structure.entity_properties.update(
                entity_model.repository.properties
            )

    def _make_unique_map_by_property(
        self,
        map_indexes_by_property: dict[str, list[IndexCompilerStructure]],
        map_unique_by_property: dict[str, IndexCompilerStructure],
        entity_model: EntityModelBase,
        entity_models: dict[str, EntityModel],
        deep: int = 1,
    ):

        if not entity_model:
            return

        # Populando com as uniques da superclasse (extends)
        if entity_model.extends:
            super_model = entity_models[entity_model.extends]

            self._make_unique_map_by_property(
                map_indexes_by_property,
                map_unique_by_property,
                super_model,
                entity_models,
                deep=deep + 1,
            )

        # Populando com as uniques do trait
        if entity_model.trait_from:
            trait_model = entity_models[entity_model.trait_from]

            self._make_unique_map_by_property(
                map_indexes_by_property,
                map_unique_by_property,
                trait_model,
                entity_models,
                deep=deep + 1,
            )

        # Varrendo e organizando os índices
        if entity_model.repository.indexes:
            for index in entity_model.repository.indexes:
                for pkey in index.columns:
                    if index.unique:
                        if pkey in map_unique_by_property:
                            if deep > 1:
                                get_logger().warning(
                                    f"Propriedade '{pkey}' possui mais de um índice de unicidade (sendo um herdado). Por isso a replicação (herdada) será ignorada."
                                )
                                continue
                            else:
                                raise Exception(
                                    f"Propriedade '{pkey}' possui mais de um índice de unicidade."
                                )  # TODO Verificar esse modo de tratar erros

                        map_unique_by_property[pkey] = IndexCompilerStructure(
                            index, deep > 1
                        )
                    else:
                        list_index = map_indexes_by_property.setdefault(pkey, [])
                        list_index.append(IndexCompilerStructure(index, deep > 1))

    def list_dependencies(
        self, edl_json: dict[str, Any]
    ) -> tuple[list[str], EntityModelBase]:
        if edl_json.get("mixin", False):
            entity_model = EntityModelRoot(**edl_json)
        else:
            entity_model = EntityModel(**edl_json)

        return (self._list_dependencies(entity_model), entity_model)

    def _list_dependencies(self, entity_model: EntityModelBase) -> list[str]:
        entities: list[str] = []

        # Adicionando dependências por mixins
        if entity_model.mixins:
            entities.extend(entity_model.mixins)

        # Adicionando dependências por traits
        if entity_model.extends:
            entities.append(entity_model.extends)

        # Adicionando dependências por traits
        if entity_model.trait_from:
            entities.append(entity_model.trait_from)

        # Adicionando dependências por classes parciais
        if isinstance(entity_model, EntityModel) and entity_model.partial_of:
            entities.append(entity_model.partial_of)

        # Populando com as dependências de propriedades de relacionamento
        relations = self._list_dependencies_relations(entity_model)

        components_dependency_list = []
        if entity_model.components is not None:
            for component in entity_model.components:
                components_dependency_list.extend(
                    self._list_dependencies(entity_model.components[component])
                )

        relations.extend(components_dependency_list)

        entities.extend(relations)

        return entities

    def _list_dependencies_relations(self, entity_model) -> list[str]:
        entities = []

        # Relacionamento 1_N
        for pkey in entity_model.properties:
            prop = entity_model.properties[pkey]

            if isinstance(prop.type, str):
                external_match = re.match(REGEX_EXTERNAL_REF, prop.type)
                if external_match:
                    external_dependency = external_match.group(0)
                    entities.append(external_dependency)

        return entities


def get_files_from_directory(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".json") or file.endswith(".yml") or file.endswith(".yaml"):
            files.append(os.path.join(directory, file))
    return files


if __name__ == "__main__":
    import argparse
    import json
    import os
    import yaml

    parser = argparse.ArgumentParser(
        description="Compila arquivos EDL para classes Python"
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Diretório com arquivos .json para compilar",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    files = get_files_from_directory(args.directory)

    entities = {}
    for file in files:
        with open(file, "r") as f:
            if file.endswith(".json"):
                edl = json.load(f)
            else:
                edl = yaml.safe_load(f)

        # Instanciando o objeto de modelo de entidade a partir do JSON,
        # e já realizando as validações básicas de tipo e estrutura.
        print(f"Validando arquivo: {file}")
        if edl.get("mixin", False):
            entity_model = EntityModelRoot(**edl)
        else:
            entity_model = EntityModel(**edl)

        complete_entity_id = f"{entity_model.escopo}/{entity_model.id}"
        entities[complete_entity_id] = entity_model

    compiler = EDLCompiler()
    compiler_results = compiler.compile_models(entities)

    with open("output_compilacao_local.py", "w") as f:
        for compiler_result in compiler_results:
            f.write("==========================================================\n")
            f.write(f"Entity: {compiler_result.entity_class_name}\n")
            f.write(f"{compiler_result.entity_code}\n")
            f.write("\n")
            f.write("==========================================================\n")
            f.write(f"DTO: {compiler_result.dto_class_name}\n")
            f.write(f"{compiler_result.dto_code}\n")
            f.write("\n")
            f.write("==========================================================\n")
            f.write(f"API Expose: {compiler_result.api_expose}\n")
            f.write(f"API Route Path: {compiler_result.api_resource}\n")
            f.write(f"API Verbs: {compiler_result.api_verbs}\n")
            f.write("==========================================================\n")
            f.write("\n")
