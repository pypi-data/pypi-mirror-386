import os

from flask import request
from typing import Callable

from nsj_rest_lib.controller.controller_util import DEFAULT_RESP_HEADERS
from nsj_rest_lib.controller.route_base import RouteBase
from nsj_rest_lib.dto.dto_base import DTOBase
from nsj_rest_lib.dto.queued_data_dto import QueuedDataDTO
from nsj_rest_lib.entity.entity_base import EntityBase
from nsj_rest_lib.exception import MissingParameterException, NotFoundException
from nsj_rest_lib.injector_factory_base import NsjInjectorFactoryBase
from nsj_rest_lib.settings import get_logger

from nsj_gcf_utils.json_util import json_dumps, JsonLoadException
from nsj_gcf_utils.rest_error_util import format_json_error


class PatchRoute(RouteBase):
    def __init__(
        self,
        url: str,
        http_method: str,
        dto_class: DTOBase,
        entity_class: EntityBase,
        dto_response_class: DTOBase = None,
        injector_factory: NsjInjectorFactoryBase = NsjInjectorFactoryBase,
        service_name: str = None,
        handle_exception: Callable = None,
        custom_before_update: Callable = None,
        custom_after_update: Callable = None,
    ):
        super().__init__(
            url=url,
            http_method=http_method,
            dto_class=dto_class,
            entity_class=entity_class,
            dto_response_class=dto_response_class,
            injector_factory=injector_factory,
            service_name=service_name,
            handle_exception=handle_exception,
        )
        self.custom_before_update = custom_before_update
        self.custom_after_update = custom_after_update

    def handle_request(
        self,
        id: str,
        query_args: dict[str, any] = None,
        body: dict[str, any] = None,
    ):
        """
        Tratando requisições HTTP Put para inserir uma instância de uma entidade.
        """

        with self._injector_factory() as factory:
            try:
                # Recuperando os dados do corpo da requisição
                if os.getenv("ENV", "").lower() != "erp_sql":
                    data = request.json
                else:
                    data = body

                # Convertendo os dados para o DTO
                data = self._dto_class(validate_read_only=True, **data)

                # Montando os filtros de particao de dados
                partition_filters = {}

                for field in data.partition_fields:
                    value = getattr(data, field)
                    if value is None:
                        raise MissingParameterException(field)
                    elif value is not None:
                        partition_filters[field] = value

                # Construindo os objetos
                service = self._get_service(factory)

                # Chamando o service (método insert)
                data = service.partial_update(
                    dto=data,
                    id=id,
                    aditional_filters=partition_filters,
                    custom_before_update=self.custom_before_update,
                    custom_after_update=self.custom_after_update,
                )

                if data is not None:
                    # Verificando se houve um enfileiramento (pelo custom_after_update)
                    if isinstance(data, QueuedDataDTO):
                        queued_data: QueuedDataDTO = data
                        resp_headers = {
                            **DEFAULT_RESP_HEADERS,
                            "Location": queued_data.status_url,
                        }
                        return ("", 202, resp_headers)

                    # Convertendo para o formato de dicionário
                    dict_data = data.convert_to_dict()

                    # Retornando a resposta da requuisição
                    return (json_dumps(dict_data), 200, {**DEFAULT_RESP_HEADERS})
                else:
                    # Retornando a resposta da requuisição
                    return ("", 204, {**DEFAULT_RESP_HEADERS})
            except JsonLoadException as e:
                get_logger().warning(e)
                if self._handle_exception is not None:
                    return self._handle_exception(e)
                else:
                    return (format_json_error(e), 400, {**DEFAULT_RESP_HEADERS})
            except MissingParameterException as e:
                get_logger().warning(e)
                if self._handle_exception is not None:
                    return self._handle_exception(e)
                else:
                    return (format_json_error(e), 400, {**DEFAULT_RESP_HEADERS})
            except ValueError as e:
                get_logger().warning(e)
                if self._handle_exception is not None:
                    return self._handle_exception(e)
                else:
                    return (format_json_error(e), 400, {**DEFAULT_RESP_HEADERS})
            except NotFoundException as e:
                get_logger().warning(e)
                if self._handle_exception is not None:
                    return self._handle_exception(e)
                else:
                    return (format_json_error(e), 404, {**DEFAULT_RESP_HEADERS})
            except Exception as e:
                get_logger().exception(e)
                if self._handle_exception is not None:
                    return self._handle_exception(e)
                else:
                    return (
                        format_json_error(f"Erro desconhecido: {e}"),
                        500,
                        {**DEFAULT_RESP_HEADERS},
                    )
