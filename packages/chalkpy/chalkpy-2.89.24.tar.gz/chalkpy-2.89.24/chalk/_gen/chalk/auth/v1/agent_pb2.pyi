from chalk._gen.chalk.auth.v1 import featurepermission_pb2 as _featurepermission_pb2
from chalk._gen.chalk.auth.v1 import permissions_pb2 as _permissions_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class AgentKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AGENT_KIND_UNSPECIFIED: _ClassVar[AgentKind]
    AGENT_KIND_USER: _ClassVar[AgentKind]
    AGENT_KIND_SERVICE_TOKEN: _ClassVar[AgentKind]
    AGENT_KIND_ENGINE: _ClassVar[AgentKind]
    AGENT_KIND_TENANT: _ClassVar[AgentKind]
    AGENT_KIND_METADATA_SERVICE: _ClassVar[AgentKind]

AGENT_KIND_UNSPECIFIED: AgentKind
AGENT_KIND_USER: AgentKind
AGENT_KIND_SERVICE_TOKEN: AgentKind
AGENT_KIND_ENGINE: AgentKind
AGENT_KIND_TENANT: AgentKind
AGENT_KIND_METADATA_SERVICE: AgentKind

class EnvironmentPermissions(_message.Message):
    __slots__ = ("permissions", "feature_permissions", "customer_claims")
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_CLAIMS_FIELD_NUMBER: _ClassVar[int]
    permissions: _containers.RepeatedScalarFieldContainer[_permissions_pb2.Permission]
    feature_permissions: _featurepermission_pb2.FeaturePermissions
    customer_claims: _containers.RepeatedCompositeFieldContainer[CustomClaim]
    def __init__(
        self,
        permissions: _Optional[_Iterable[_Union[_permissions_pb2.Permission, str]]] = ...,
        feature_permissions: _Optional[_Union[_featurepermission_pb2.FeaturePermissions, _Mapping]] = ...,
        customer_claims: _Optional[_Iterable[_Union[CustomClaim, _Mapping]]] = ...,
    ) -> None: ...

class TeamPermissions(_message.Message):
    __slots__ = ("permissions",)
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    permissions: _containers.RepeatedScalarFieldContainer[_permissions_pb2.Permission]
    def __init__(self, permissions: _Optional[_Iterable[_Union[_permissions_pb2.Permission, str]]] = ...) -> None: ...

class UserAgent(_message.Message):
    __slots__ = ("client_id", "user_id", "team_id", "permissions_by_environment", "impersonated", "team_permissions")
    class PermissionsByEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: EnvironmentPermissions
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[_Union[EnvironmentPermissions, _Mapping]] = ...
        ) -> None: ...

    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_ID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_BY_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    IMPERSONATED_FIELD_NUMBER: _ClassVar[int]
    TEAM_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    user_id: str
    team_id: str
    permissions_by_environment: _containers.MessageMap[str, EnvironmentPermissions]
    impersonated: bool
    team_permissions: TeamPermissions
    def __init__(
        self,
        client_id: _Optional[str] = ...,
        user_id: _Optional[str] = ...,
        team_id: _Optional[str] = ...,
        permissions_by_environment: _Optional[_Mapping[str, EnvironmentPermissions]] = ...,
        impersonated: bool = ...,
        team_permissions: _Optional[_Union[TeamPermissions, _Mapping]] = ...,
    ) -> None: ...

class CustomClaim(_message.Message):
    __slots__ = ("key", "values")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    key: str
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, key: _Optional[str] = ..., values: _Optional[_Iterable[str]] = ...) -> None: ...

class ServiceTokenAgent(_message.Message):
    __slots__ = (
        "id",
        "client_id",
        "team_id",
        "environment",
        "permissions",
        "custom_claims",
        "customer_claims",
        "feature_permissions",
        "team_permissions",
    )
    ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_ID_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_CLAIMS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_CLAIMS_FIELD_NUMBER: _ClassVar[int]
    FEATURE_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    TEAM_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    id: str
    client_id: str
    team_id: str
    environment: str
    permissions: _containers.RepeatedScalarFieldContainer[_permissions_pb2.Permission]
    custom_claims: _containers.RepeatedScalarFieldContainer[str]
    customer_claims: _containers.RepeatedCompositeFieldContainer[CustomClaim]
    feature_permissions: _featurepermission_pb2.FeaturePermissions
    team_permissions: _containers.RepeatedScalarFieldContainer[_permissions_pb2.Permission]
    def __init__(
        self,
        id: _Optional[str] = ...,
        client_id: _Optional[str] = ...,
        team_id: _Optional[str] = ...,
        environment: _Optional[str] = ...,
        permissions: _Optional[_Iterable[_Union[_permissions_pb2.Permission, str]]] = ...,
        custom_claims: _Optional[_Iterable[str]] = ...,
        customer_claims: _Optional[_Iterable[_Union[CustomClaim, _Mapping]]] = ...,
        feature_permissions: _Optional[_Union[_featurepermission_pb2.FeaturePermissions, _Mapping]] = ...,
        team_permissions: _Optional[_Iterable[_Union[_permissions_pb2.Permission, str]]] = ...,
    ) -> None: ...

class EngineAgent(_message.Message):
    __slots__ = ("id", "team_id", "project_id", "environment_id", "impersonated")
    ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_ID_FIELD_NUMBER: _ClassVar[int]
    IMPERSONATED_FIELD_NUMBER: _ClassVar[int]
    id: str
    team_id: str
    project_id: str
    environment_id: str
    impersonated: bool
    def __init__(
        self,
        id: _Optional[str] = ...,
        team_id: _Optional[str] = ...,
        project_id: _Optional[str] = ...,
        environment_id: _Optional[str] = ...,
        impersonated: bool = ...,
    ) -> None: ...

class MetadataServiceAgent(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TenantAgent(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Agent(_message.Message):
    __slots__ = ("user_agent", "service_token_agent", "engine_agent", "tenant_agent", "metadata_service_agent")
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    SERVICE_TOKEN_AGENT_FIELD_NUMBER: _ClassVar[int]
    ENGINE_AGENT_FIELD_NUMBER: _ClassVar[int]
    TENANT_AGENT_FIELD_NUMBER: _ClassVar[int]
    METADATA_SERVICE_AGENT_FIELD_NUMBER: _ClassVar[int]
    user_agent: UserAgent
    service_token_agent: ServiceTokenAgent
    engine_agent: EngineAgent
    tenant_agent: TenantAgent
    metadata_service_agent: MetadataServiceAgent
    def __init__(
        self,
        user_agent: _Optional[_Union[UserAgent, _Mapping]] = ...,
        service_token_agent: _Optional[_Union[ServiceTokenAgent, _Mapping]] = ...,
        engine_agent: _Optional[_Union[EngineAgent, _Mapping]] = ...,
        tenant_agent: _Optional[_Union[TenantAgent, _Mapping]] = ...,
        metadata_service_agent: _Optional[_Union[MetadataServiceAgent, _Mapping]] = ...,
    ) -> None: ...
