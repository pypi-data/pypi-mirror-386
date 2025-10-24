
from dataclasses import dataclass


@dataclass
class TestrailConfig:
    """Config for testrail uploader."""

    login: str = None
    password: str = None
    api_url: str = None
    custom_fields_matcher: dict = None
