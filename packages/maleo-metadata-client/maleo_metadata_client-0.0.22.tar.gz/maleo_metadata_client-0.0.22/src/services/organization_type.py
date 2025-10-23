import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Literal, overload
from uuid import UUID
from maleo.client.maleo.config import MaleoMetadataClientConfig
from maleo.client.maleo.service import MaleoClientService
from maleo.database.enums import Connection
from maleo.database.utils import build_cache_key
from maleo.enums.cardinality import Cardinality
from maleo.enums.connection import Header
from maleo.logging.enums import Level
from maleo.metadata.constants.organization_type import ORGANIZATION_TYPE_RESOURCE
from maleo.metadata.schemas.organization_type import (
    ReadMultipleParameter,
    ReadSingleParameter,
    StandardOrganizationTypeSchema,
    FullOrganizationTypeSchema,
)
from maleo.metadata.enums.organization_type import Granularity, IdentifierType
from maleo.metadata.utils.organization_type import get_schema_model
from maleo.schemas.connection import ConnectionContext
from maleo.schemas.exception.factory import Factory as MaleoExceptionFactory
from maleo.schemas.operation.action.resource import ReadResourceOperationAction
from maleo.schemas.operation.enums import OperationType, Target
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.resource import (
    ReadMultipleResourceOperation,
    ReadSingleResourceOperation,
)
from maleo.schemas.pagination import StrictPagination
from maleo.schemas.response import (
    MultipleDataResponse,
    ReadMultipleDataResponse,
    SingleDataResponse,
    ReadSingleDataResponse,
)
from maleo.schemas.security.authorization import (
    OptAnyAuthorization,
    AnyAuthorization,
    Factory as AuthorizationFactory,
)
from maleo.schemas.security.impersonation import OptImpersonation
from maleo.types.dict import OptStrToStrDict
from maleo.utils.merger import merge_dicts


class OrganizationTypeClientService(MaleoClientService[MaleoMetadataClientConfig]):
    resource = ORGANIZATION_TYPE_RESOURCE

    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadMultipleDataResponse[
        StandardOrganizationTypeSchema, StrictPagination, None
    ]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadMultipleDataResponse[
        FullOrganizationTypeSchema, StrictPagination, None
    ]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadSingleDataResponse[StandardOrganizationTypeSchema, None]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadSingleDataResponse[FullOrganizationTypeSchema, None]: ...
    async def read(
        self,
        cardinality: Cardinality,
        granularity: Granularity,
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter | ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> (
        ReadMultipleDataResponse[StandardOrganizationTypeSchema, StrictPagination, None]
        | ReadMultipleDataResponse[FullOrganizationTypeSchema, StrictPagination, None]
        | ReadSingleDataResponse[StandardOrganizationTypeSchema, None]
        | ReadSingleDataResponse[FullOrganizationTypeSchema, None]
    ):
        redis_client = self._redis.manager.client.get(Connection.ASYNC)
        data_model_cls = get_schema_model(granularity)

        executed_at = datetime.now(tz=timezone.utc)

        # Define arguments being used in this function
        positional_arguments = [cardinality, granularity]
        keyword_arguments = {
            "authorization": (
                authorization.model_dump(mode="json")
                if authorization is not None
                else None
            ),
            "parameters": parameters.model_dump(mode="json"),
        }

        # Define full function string
        ext = f"({json.dumps(positional_arguments)}|{json.dumps(keyword_arguments)})"

        # Define full cache_key
        cache_key = build_cache_key(ext, namespace=self._namespace)

        if parameters.use_cache:
            # Initialize cache operation context
            operation_context = deepcopy(self._operation_context)
            operation_context.target.type = Target.CACHE

            redis_response_str = await redis_client.get(cache_key)

            if redis_response_str is not None:
                operation_timestamp = Timestamp.completed_now(executed_at)
                if cardinality is Cardinality.MULTIPLE:
                    response = ReadMultipleDataResponse[
                        data_model_cls, StrictPagination, None
                    ].model_validate_json(redis_response_str)
                    ReadMultipleResourceOperation[
                        data_model_cls, StrictPagination, None
                    ](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        action=resource_operation_action,
                        resource=self.resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully retrieved {cardinality} {granularity} organization types from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    ).log(
                        self._logger, Level.INFO
                    )
                elif cardinality is Cardinality.SINGLE:
                    response = ReadSingleDataResponse[
                        data_model_cls, None
                    ].model_validate_json(redis_response_str)
                    ReadSingleResourceOperation[data_model_cls, None](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        action=resource_operation_action,
                        resource=self.resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully retrieved {cardinality} {granularity} organization type from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    ).log(self._logger, Level.INFO)

                return response  # type: ignore

        operation_context = deepcopy(self._operation_context)
        operation_context.target.type = Target.MICROSERVICE

        async with self._http_client_manager.get() as http_client:
            base_headers = {
                Header.CONTENT_TYPE.value: "application/json",
                Header.X_OPERATION_ID.value: str(operation_id),
            }
            if impersonation is not None:
                base_headers[Header.X_USER_ID.value] = str(impersonation.user_id)
                if impersonation.organization_id is not None:
                    base_headers[Header.X_ORGANIZATION_ID.value] = str(
                        impersonation.organization_id
                    )

            if headers is not None:
                headers = merge_dicts(base_headers, headers)
            else:
                headers = base_headers

            if authorization is not None:
                auth = AuthorizationFactory.httpx_auth(
                    scheme=authorization.scheme, authorization=authorization.credentials
                )
            else:
                auth = None

            if isinstance(parameters, ReadMultipleParameter):
                url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/"
            elif isinstance(parameters, ReadSingleParameter):
                if parameters.identifier_type is IdentifierType.ID:
                    url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/{parameters.identifier_value}"
                else:
                    url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/{parameters.identifier_type}/{parameters.identifier_value}"

            params = parameters.to_query_params()

            response = await http_client.get(
                url, params=params, headers=headers, auth=auth
            )

            operation_timestamp = Timestamp.completed_now(executed_at)

            if response.is_error:
                raise MaleoExceptionFactory.from_httpx(
                    response,
                    operation_type=OperationType.REQUEST,
                    application_context=self._application_context,
                    operation_id=operation_id,
                    operation_context=operation_context,
                    operation_action=resource_operation_action,
                    operation_timestamp=operation_timestamp,
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    logger=self._logger,
                )

            if isinstance(parameters, ReadMultipleParameter):
                validated_response = MultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].model_validate(response.json())
                service_response = ReadMultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].new(
                    data=validated_response.data,
                    pagination=validated_response.pagination,
                )
                ReadMultipleResourceOperation[data_model_cls, StrictPagination, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    action=resource_operation_action,
                    resource=ORGANIZATION_TYPE_RESOURCE,
                    timestamp=operation_timestamp,
                    summary=f"Successfully retrieved multiple {granularity} organization types from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                ).log(self._logger, Level.INFO)
            elif isinstance(parameters, ReadSingleParameter):
                validated_response = SingleDataResponse[
                    data_model_cls, None
                ].model_validate(response.json())
                service_response = ReadSingleDataResponse[data_model_cls, None].new(
                    data=validated_response.data,
                )
                ReadSingleResourceOperation[data_model_cls, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    action=resource_operation_action,
                    resource=ORGANIZATION_TYPE_RESOURCE,
                    timestamp=operation_timestamp,
                    summary=f"Successfully retrieved single {granularity} organization type from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                ).log(self._logger, Level.INFO)

            return service_response  # type: ignore
