# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol


class ChannelInfoProtocol(Protocol):
    id: str
    app_id: str
    resource_url: str
    token_provider: str
    channel_factory: str
    endpoint: str
