from pydantic import BaseModel, ConfigDict, Field


class Server(BaseModel):
    class Flavor(BaseModel):
        id: str | None = Field(default=None, exclude=True)
        name: str | None = Field(
            default=None,
            validation_alias="original_name",
        )
        model_config = ConfigDict(validate_by_name=True)

    class Image(BaseModel):
        id: str | None = Field(default=None)

    class IPAddress(BaseModel):
        addr: str
        version: int
        type: str = Field(validation_alias="OS-EXT-IPS:type")

        model_config = ConfigDict(validate_by_name=True)

    class VolumeAttachment(BaseModel):
        id: str
        delete_on_termination: bool

    class SecurityGroup(BaseModel):
        name: str

    id: str
    name: str
    hostname: str | None = None
    description: str | None = None
    status: str | None = None
    flavor: Flavor | None = None
    image: Image | None = None
    addresses: dict[str, list[IPAddress]] | None = None
    key_name: str | None = None
    security_groups: list[SecurityGroup] | None = None
    accessIPv4: str | None = None
    accessIPv6: str | None = None
    attached_volumes: list[VolumeAttachment] | None = Field(default=None)


class Flavor(BaseModel):
    id: str
    name: str
    vcpus: int
    ram: int
    disk: int
    swap: int | None = None
    is_public: bool = Field(validation_alias="os-flavor-access:is_public")

    model_config = ConfigDict(validate_by_name=True)
