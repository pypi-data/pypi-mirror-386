from pydantic import BaseModel, Field
from typing import Annotated
from maleo.enums.environment import Environment
from maleo.types.dict import OptStrToStrDict
from maleo.types.string import OptStr


class DatabaseIdentifierConfig(BaseModel):
    enabled: Annotated[
        bool, Field(True, description="Whether the database is enabled")
    ] = True
    environment: Annotated[
        Environment, Field(..., description="Database's environment")
    ]
    name: Annotated[str, Field(..., description="Database's name")]
    description: Annotated[
        OptStr, Field(None, description="Database's description")
    ] = None
    tags: Annotated[OptStrToStrDict, Field(None, description="Database's tags")] = None
