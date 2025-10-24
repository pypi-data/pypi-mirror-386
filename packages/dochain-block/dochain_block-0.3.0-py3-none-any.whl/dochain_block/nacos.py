"""Nacos authentication block for dochain-block."""

from __future__ import annotations

from nacos import NacosClient
from prefect.blocks.core import Block
from pydantic import Field, HttpUrl, SecretStr


class NacosBlock(Block):
    """Nacos connection block - provides configured Nacos client.

    Simple, focused block that only manages connection parameters.
    Business operations should be done in Prefect Tasks using the client.
    """

    _block_type_name = "Nacos Connection"
    _logo_url = "https://nacos.io/img/nacos-logo.png"

    server_url: HttpUrl = Field(
        ...,
        description="Nacos server URL (e.g., http://localhost:8848)"
    )

    namespace: str = Field(
        default="public",
        description="Nacos namespace ID (defaults to 'public')"
    )

    username: SecretStr | None = Field(
        None,
        description="Nacos username (for username/password auth)"
    )

    password: SecretStr | None = Field(
        None,
        description="Nacos password (for username/password auth)"
    )

    access_key: SecretStr | None = Field(
        None,
        description="Nacos access key (ak for cloud auth)"
    )

    secret_key: SecretStr | None = Field(
        None,
        description="Nacos secret key (sk for cloud auth)"
    )

    def get_client(self) -> NacosClient:
        """Get configured Nacos client for operations."""
        server_addresses = str(self.server_url).rstrip('/')

        # Build client config based on available auth
        config = {
            "server_addresses": server_addresses,
            "namespace": self.namespace,
        }

        if self.username and self.password:
            config.update({
                "username": self.username.get_secret_value(),
                "password": self.password.get_secret_value(),
            })
        elif self.access_key and self.secret_key:
            config.update({
                "ak": self.access_key.get_secret_value(),
                "sk": self.secret_key.get_secret_value(),
            })

        return NacosClient(**config)

    def test(self) -> str:
        """Lightweight connectivity test.

        Returns:
            Test result message
        """
        try:
            client = self.get_client()
            # Lightweight test - just try to get configs list
            client.get_configs_list()
            return "✅ Nacos connection successful"
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"