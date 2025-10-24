"""Nacos Block and Task examples - simple and focused."""

from prefect import flow, task
from dochain_block import NacosBlock


# Business Tasks using Block
@task
def get_nacos_config(data_id: str, group: str, block_name: str = "nacos-prod") -> str:
    """Get configuration from Nacos using Block client."""
    client = NacosBlock.load(block_name).get_client()
    return client.get_config(data_id, group)


@task
def publish_nacos_config(data_id: str, content: str, group: str, block_name: str = "nacos-prod") -> bool:
    """Publish configuration to Nacos using Block client."""
    client = NacosBlock.load(block_name).get_client()
    return client.publish_config(data_id, content, group)


@task
def test_nacos_connection(block_name: str = "nacos-prod") -> str:
    """Test Nacos connection using Block built-in test."""
    nacos_block = NacosBlock.load(block_name)
    return nacos_block.test()


@task
def list_nacos_services(block_name: str = "nacos-prod") -> list:
    """List services from Nacos using Block client."""
    client = NacosBlock.load(block_name).get_client()
    return client.list_services()


# Flow example
@flow
def config_management_flow():
    """Configuration management flow using Nacos Block and Tasks."""

    # Load Nacos Block (connection management)
    nacos_block = NacosBlock.load("my-nacos")

    print("=== Nacos Block Test ===")
    test_result = test_nacos_connection()
    print(test_result)

    print("\n=== Configuration Operations ===")

    # Get configuration
    try:
        config = get_nacos_config("app.properties", "DEFAULT_GROUP")
        print(f"Got config: {len(config)} characters")
    except Exception as e:
        print(f"Get config failed: {e}")

    # Publish configuration
    try:
        publish_result = publish_nacos_config(
            data_id="new.properties",
            content="server.port=8080\napp.name=test-app\n",
            group="API_GROUP"
        )
        print(f"Published config: {publish_result}")
    except Exception as e:
        print(f"Publish config failed: {e}")

    # List services
    try:
        services = list_nacos_services()
        print(f"Services: {len(services)} found")
    except Exception as e:
        print(f"List services failed: {e}")


# Block configuration example
def setup_nacos_block():
    """Create and save Nacos Block configuration."""

    # Production Block (username/password)
    prod_nacos = NacosBlock(
        name="nacos-prod",
        server_url="https://nacos.prod.example.com",
        username="nacos-admin",
        password="secure-password",
        namespace="production"
    )
    prod_nacos.save("nacos-prod")
    print("Production Nacos Block saved")

    # Development Block (access key)
    dev_nacos = NacosBlock(
        name="nacos-dev",
        server_url="http://localhost:8848",
        access_key="LTAI_dev_key",
        secret_key="dev_secret",
        namespace="dev"
    )
    dev_nacos.save("nacos-dev")
    print("Development Nacos Block saved")


if __name__ == "__main__":
    # Example: Setup Blocks first
    setup_nacos_block()

    print("\n" + "="*50)
    print("Nacos Example: Block provides client, Tasks do business")
    print("="*50)

    # Run the flow
    config_management_flow()