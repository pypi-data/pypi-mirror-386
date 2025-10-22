import hashlib
import hmac
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from qore_client.settings import ACCESS_KEY, SECRET_KEY


class QoreAuth:
    """Authentication logic for Qore API"""

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ):
        """
        Initialize authentication with keys or JWT token

        :param access_key: Qore API 인증에 사용되는 Access Key
        :param secret_key: Qore API 인증에 사용되는 Secret Key
        :param jwt_token: JWT 토큰 (access_key/secret_key 대신 사용 가능)
        """
        self.__jwt_token = jwt_token
        self.__access_key = access_key or ACCESS_KEY
        self.__secret_key = secret_key or SECRET_KEY

        # JWT 토큰이 있으면 access_key/secret_key 불필요
        if not self.__jwt_token:
            if not self.__access_key or not self.__secret_key:
                raise ValueError("Either jwt_token or (access_key and secret_key) must be provided")

    def generate_headers(self, credential_source: str) -> Dict[str, Any]:
        """Generate authentication headers for API requests"""
        # JWT 토큰이 있으면 Bearer 토큰 사용
        if self.__jwt_token:
            return {
                "Authorization": f"Bearer {self.__jwt_token}",
            }

        # 없으면 기존 HMAC 서명 방식 사용
        return {
            "X-API-ACCESS-KEY": self.__access_key,
            "X-API-SIGNATURE": self.generate_signature(credential_source=credential_source),
        }

    def generate_signature(self, credential_source: str) -> str:
        """Generate HMAC signature for authentication"""
        if self.__secret_key is None:
            raise TypeError("Secret key is None, cannot create signature.")
        signature = hmac.new(
            self.__secret_key.encode(), credential_source.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    def get_credential_source(
        self, method: str, path: str, params: Dict[str, Any], body: bytes | str | None = None
    ) -> str:
        """Generate credential source string for signing"""
        query_string = urlencode(params)
        if isinstance(body, bytes):
            try:
                data_string = body.decode("utf-8")
            except UnicodeDecodeError:
                # UTF-8로 디코딩할 수 없는 바이너리 데이터의 경우 해시값 사용
                import hashlib

                data_string = hashlib.sha256(body).hexdigest()
        elif isinstance(body, str):
            data_string = body
        else:
            data_string = ""

        combined_string = f"{query_string}{data_string}"
        return f"{method}:{path}:{combined_string}"

    @property
    def access_key(self) -> str:
        """Get the access key"""
        if self.__access_key is None:
            raise ValueError("Access key is not set")
        return self.__access_key
