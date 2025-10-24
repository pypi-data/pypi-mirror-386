# Copyright 2023 LiveAI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LiveAI Server APIs for Python

`pip install liveai-api`

Manage rooms, participants, egress, ingress, SIP, and Agent dispatch.

Primary entry point is `LiveAIAPI`.

See https://docs.liveai.io/reference/server/server-apis for more information.
"""

# flake8: noqa
# re-export packages from protocol
from liveai.protocol.agent_dispatch import *
from liveai.protocol.agent import *
from liveai.protocol.egress import *
from liveai.protocol.ingress import *
from liveai.protocol.models import *
from liveai.protocol.room import *
from liveai.protocol.webhook import *
from liveai.protocol.sip import *

from .twirp_client import TwirpError, TwirpErrorCode
from .liveai_api import LiveAIAPI
from .access_token import (
    InferenceGrants,
    ObservabilityGrants,
    VideoGrants,
    SIPGrants,
    AccessToken,
    TokenVerifier,
)
from .webhook import WebhookReceiver
from .version import __version__

__all__ = [
    "LiveAIAPI",
    "room_service",
    "egress_service",
    "ingress_service",
    "sip_service",
    "agent_dispatch_service",
    "InferenceGrants",
    "ObservabilityGrants",
    "VideoGrants",
    "SIPGrants",
    "AccessToken",
    "TokenVerifier",
    "WebhookReceiver",
    "TwirpError",
    "TwirpErrorCode",
]
