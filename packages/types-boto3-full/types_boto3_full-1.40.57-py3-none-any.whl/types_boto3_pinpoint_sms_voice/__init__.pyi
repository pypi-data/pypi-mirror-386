"""
Main interface for pinpoint-sms-voice service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_pinpoint_sms_voice/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_pinpoint_sms_voice import (
        Client,
        PinpointSMSVoiceClient,
    )

    session = Session()
    client: PinpointSMSVoiceClient = session.client("pinpoint-sms-voice")
    ```
"""

from .client import PinpointSMSVoiceClient

Client = PinpointSMSVoiceClient

__all__ = ("Client", "PinpointSMSVoiceClient")
