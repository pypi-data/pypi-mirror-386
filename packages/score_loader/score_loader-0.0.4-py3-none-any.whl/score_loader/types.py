from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator, conint

PortInt = conint(ge=1, le=65535)


class Metadata(BaseModel):
    name: str
    annotations: Dict[str, str] = Field(default_factory=dict)
    # allow arbitrary extra keys at this level (e.g., "other-key", "foo", etc.)
    model_config = ConfigDict(extra="allow")


class HTTPHeader(BaseModel):
    name: str
    value: str


class HTTPGet(BaseModel):
    scheme: Optional[str] = None
    host: Optional[str] = None
    path: str
    port: int
    httpHeaders: Optional[List[HTTPHeader]] = None


class Probe(BaseModel):
    httpGet: HTTPGet


class ResourceSpec(BaseModel):
    memory: Optional[str] = None
    cpu: Optional[str] = None


class ContainerResource(BaseModel):
    limits: Optional[ResourceSpec] = None
    requests: Optional[ResourceSpec] = None


class FileSpec(BaseModel):
    mode: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None
    noExpand: Optional[bool] = None

    # Enforce that exactly one of source or content is set
    @model_validator(mode="after")
    def validate_source_or_content(self):
        if not (self.source or self.content):
            raise ValueError(
                "One of 'source' or 'content' must be provided in file spec."
            )
        return self


class VolumeSpec(BaseModel):
    source: str
    path: Optional[str] = None
    readOnly: Optional[bool] = None


class Container(BaseModel):
    image: str
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    variables: Optional[Dict[str, str]] = None
    files: Optional[Dict[str, FileSpec]] = None
    volumes: Optional[Dict[str, VolumeSpec]] = None
    resources: Optional[ContainerResource] = None
    livenessProbe: Optional[Probe] = None
    readinessProbe: Optional[Probe] = None


class ResourceMetadata(BaseModel):
    annotations: Optional[Dict[str, str]] = None
    model_config = ConfigDict(
        extra="forbid"
    )  # keep metadata tight; change to 'allow' if needed


class Resource(BaseModel):
    type: str
    resource_class: Optional[str] = Field(
        None, alias="class"
    )  # accept YAML key 'class'
    id: Optional[str] = None
    metadata: Optional[ResourceMetadata] = None
    params: Optional[Dict[str, Any]] = None  # values can be any JSON/YAML scalar/object

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,  # lets you pass 'resource_class' in Python, or 'class' in YAML
    )


class PortSpec(BaseModel):
    port: PortInt
    protocol: str = "TCP"  # optional, defaults to TCP
    targetPort: Optional[PortInt] = None

    model_config = ConfigDict(extra="forbid")  # keep the schema tight


class Service(BaseModel):
    ports: Dict[str, PortSpec] = Field(..., description="Map of port-name to PortSpec")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_non_empty_ports(self):
        if not self.ports:
            raise ValueError("service.ports must contain at least one entry")
        return self


class ScoreSpec(BaseModel):
    apiVersion: str
    metadata: Metadata
    containers: Dict[str, Container] = Field(default_factory=dict)
    resources: Dict[str, Resource] = Field(default_factory=dict)
    service: Optional[Service] = None
