from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Generic
from .config.subscription import SubscriptionConfigT
from .types import R, MessageController


class SubscriptionHandler(BaseModel, Generic[SubscriptionConfigT, R]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Annotated[
        SubscriptionConfigT, Field(..., description="Subscription config")
    ]
    controller: Annotated[
        MessageController[R], Field(..., description="Message controller")
    ]


class SubscriptionHandlers(BaseModel):
    pass
