# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol

from microsoft_agents.hosting.core.authorization import AccessTokenProviderBase

from .channel_protocol import ChannelProtocol


class ChannelFactoryProtocol(Protocol):
    def create_channel(self, token_access: AccessTokenProviderBase) -> ChannelProtocol:
        pass
