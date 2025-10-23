from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from dnastack import ServiceEndpoint as Endpoint


class Context(BaseModel):
    dnastack_schema_version: float = Field(alias='model_version', default=1.0)

    # For debugging
    guid:  str = Field(default_factory=lambda: str(uuid4()))

    # This is the short-type-to-service-id map.
    defaults: Dict[str, str] = Field(default_factory=lambda: {})

    endpoints: List[Endpoint] = Field(default_factory=lambda: [])
    
    # Store subject token for token exchange authentication if provided
    platform_subject_token: Optional[str] = Field(default=None)
