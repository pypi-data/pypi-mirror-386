"""Text translation utilities for Shadowstep framework.

This module provides the YandexTranslate class for translating text
from Russian to English using the Yandex Cloud Translate API.
"""

import logging
import os
import re

import requests

from shadowstep.exceptions.shadowstep_exceptions import (
    ShadowstepMissingYandexTokenError,
    ShadowstepTranslationFailedError,
)
from shadowstep.utils.utils import get_current_func_name


class YandexTranslate:
    """Provide functionality to authenticate and translate text using Yandex Cloud Translate API."""

    def __init__(self, folder_id: str) -> None:
        """Initialize the YandexTranslate instance with the specified folder ID.

        Args:
            folder_id (str): The Yandex Cloud folder ID used for translations.

        """
        self.logger = logging.getLogger()
        self.folder_id = folder_id
        self._iam_token = self._get_iam_token()

    def _get_iam_token(self) -> str:
        """Retrieve the IAM token using the OAuth token from the environment.

        Returns:
            str: The IAM token.

        """
        oauth_token = os.getenv("yandexPassportOauthToken")  # noqa: SIM112
        if not oauth_token:
            raise ShadowstepMissingYandexTokenError

        url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        response = requests.post(url, json={"yandexPassportOauthToken": oauth_token}, timeout=30)
        response.raise_for_status()
        return response.json()["iamToken"]

    def _contains_cyrillic(self, text: str) -> bool:
        """Check if the given text contains any Cyrillic characters.

        Args:
            text (str): Text to analyze.

        Returns:
            bool: True if Cyrillic characters are found, otherwise False.

        """
        return bool(re.search(r"[а-яА-Я]", text))  # noqa: RUF001

    def translate(self, text: str) -> str:
        """Translate a single text string from Russian to English if it contains Cyrillic.

        Args:
            text (str): The string to translate.

        Returns:
            str: Translated string (or original if not translated).

        """
        self.logger.debug("%s", get_current_func_name())
        self.logger.debug("text=%s", text)
        if not self._contains_cyrillic(text):
            return text  # No translation needed

        url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._iam_token}",
        }
        body = {
            "folderId": self.folder_id,
            "texts": [text],
            "sourceLanguageCode": "ru",
            "targetLanguageCode": "en",
        }

        response = requests.post(url, headers=headers, json=body, timeout=30)
        self.logger.debug("response.text=%s", response.text)
        response.raise_for_status()
        translations = response.json().get("translations", [])

        if not translations:
            raise ShadowstepTranslationFailedError

        translated = translations[0]["text"]
        self.logger.debug("translated=%s", translated)
        return translated
