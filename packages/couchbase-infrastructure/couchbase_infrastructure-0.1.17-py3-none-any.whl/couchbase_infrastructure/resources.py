"""Resource management functions for Couchbase Capella infrastructure."""

import time
from typing import Dict

from rich.console import Console

from couchbase_infrastructure.client import CapellaClient
from couchbase_infrastructure.config import CapellaConfig

console = Console()


def create_project(client: CapellaClient, org_id: str, project_name: str) -> str:
    """Find or create a Capella project.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        project_name: Name of the project to create or find

    Returns:
        Project ID

    Raises:
        Exception: If project creation fails
    """
    console.print(f"   Searching for project named '[cyan]{project_name}[/cyan]'...")
    list_endpoint = f"/v4/organizations/{org_id}/projects"

    list_response = client.get(list_endpoint)

    if list_response.status_code == 200:
        for project in list_response.json().get("data", []):
            if project.get("name") == project_name:
                project_id = project.get("id")
                console.print(f"[green]✅ Found existing project.[/green] Project ID: [cyan]{project_id}[/cyan]")
                return project_id

    console.print(f"   Project not found. Creating a new project named '[cyan]{project_name}[/cyan]'...")
    create_endpoint = f"/v4/organizations/{org_id}/projects"
    payload = {
        "name": project_name,
        "description": "Project for Agent Application Hub samples.",
    }

    create_response = client.post(create_endpoint, json=payload)

    if create_response.status_code == 201:
        project_id = create_response.json().get("id")
        console.print(
            f"[green]✅ Successfully created new project.[/green] Project ID: [cyan]{project_id}[/cyan]"
        )
        return project_id
    else:
        raise Exception(
            f"Failed to create project. Status: {create_response.status_code}, "
            f"Response: {create_response.text}"
        )


def create_cluster(
    client: CapellaClient,
    org_id: str,
    project_id: str,
    cluster_name: str,
    config: CapellaConfig,
) -> str:
    """Create a free tier Capella cluster.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        project_id: Project ID
        cluster_name: Name for the cluster
        config: Configuration with cluster settings

    Returns:
        Cluster ID

    Raises:
        Exception: If cluster creation fails
    """
    endpoint = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/freeTier"
    payload = {
        "name": cluster_name,
        "cloudProvider": {
            "type": config.cluster_cloud_provider,
            "region": config.cluster_region,
            "cidr": config.cluster_cidr,
        },
    }

    response = client.post(endpoint, json=payload)

    if response.status_code == 202:
        cluster_id = response.json().get("id")
        console.print(f"   Cluster creation job submitted. Cluster ID: [cyan]{cluster_id}[/cyan]")
        return cluster_id
    elif response.status_code == 422 and "limited to provisioning one cluster" in response.text:
        console.print("   A free tier cluster already exists. Attempting to find it...")
        clusters_endpoint = f"/v4/organizations/{org_id}/projects/{project_id}/clusters"
        list_response = client.get(clusters_endpoint)

        if list_response.status_code == 200:
            clusters = list_response.json().get("data", [])
            if clusters:
                # Use the first cluster found (free tier only allows one cluster total)
                cluster = clusters[0]
                cluster_id = cluster.get("id")
                existing_name = cluster.get("name")
                console.print(
                    f"   [green]✅ Found existing free tier cluster:[/green] '[cyan]{existing_name}[/cyan]'. Using it."
                )
                if existing_name != cluster_name:
                    console.print(
                        f"   [yellow]Note: Requested name was '{cluster_name}', but using existing cluster '{existing_name}'[/yellow]"
                    )
                return cluster_id

        raise Exception(f"Failed to create or find free tier cluster. Response: {response.text}")
    else:
        raise Exception(
            f"Failed to create cluster. Status: {response.status_code}, Response: {response.text}"
        )


def add_allowed_cidr(
    client: CapellaClient,
    org_id: str,
    project_id: str,
    cluster_id: str,
    cidr: str = "0.0.0.0/0",
) -> Dict:
    """Add an allowed CIDR to the cluster for network access.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        project_id: Project ID
        cluster_id: Cluster ID
        cidr: CIDR block to allow (default: 0.0.0.0/0)

    Returns:
        CIDR information

    Raises:
        Exception: If CIDR addition fails
    """
    endpoint = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/{cluster_id}/allowedcidrs"

    payload = {"cidr": cidr, "comment": "Allow access for agent hub development"}

    console.print(f"   Adding allowed CIDR [cyan]{cidr}[/cyan] to cluster...")

    response = client.post(endpoint, json=payload)

    if response.status_code == 201:
        console.print(f"   [green]✅ Successfully added allowed CIDR: {cidr}[/green]")
        return response.json()
    elif response.status_code == 422:
        # Check if CIDR already exists
        console.print("   Checking if CIDR already exists...")
        list_response = client.get(endpoint)

        if list_response.status_code == 200:
            cidrs = list_response.json().get("data", [])
            for existing_cidr in cidrs:
                if existing_cidr.get("cidr") == cidr:
                    console.print(f"   [green]✅ CIDR {cidr} already exists[/green]")
                    return existing_cidr

        raise Exception(f"Failed to add allowed CIDR. Response: {response.text}")
    else:
        raise Exception(
            f"Failed to add allowed CIDR. Status: {response.status_code}, Response: {response.text}"
        )


def load_sample_data(
    client: CapellaClient,
    org_id: str,
    project_id: str,
    cluster_id: str,
    bucket_name: str = "travel-sample",
) -> None:
    """Load sample data bucket into the cluster.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        project_id: Project ID
        cluster_id: Cluster ID
        bucket_name: Name of sample bucket to load

    Raises:
        Exception: If sample data loading fails
    """
    endpoint = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/{cluster_id}/sampleBuckets"
    payload = {"name": bucket_name}

    response = client.post(endpoint, json=payload)

    if response.status_code in [201, 422]:
        console.print(f"[green]✅ `{bucket_name}` bucket load command accepted.[/green]")
        bucket_check_url = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/{cluster_id}/buckets"
        start_time = time.time()

        while time.time() - start_time < 300:
            bucket_list_response = client.get(bucket_check_url)
            if any(
                b.get("name") == bucket_name
                for b in bucket_list_response.json().get("data", [])
            ):
                console.print(f"[green]✅ `{bucket_name}` bucket is ready.[/green]")
                return
            time.sleep(10)

        raise Exception(f"Timeout waiting for {bucket_name} bucket to become available.")
    else:
        raise Exception(
            f"Failed to load {bucket_name}. Status: {response.status_code}, "
            f"Response: {response.text}"
        )


def create_database_user(
    client: CapellaClient,
    org_id: str,
    project_id: str,
    cluster_id: str,
    username: str,
    bucket_name: str = "travel-sample",
    recreate_if_exists: bool = False,
) -> str:
    """Create a database user with access to the specified bucket.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        project_id: Project ID
        cluster_id: Cluster ID
        username: Username for the database user
        bucket_name: Bucket to grant access to
        recreate_if_exists: If True, delete and recreate user if it already exists

    Returns:
        User password (empty string if user already exists and recreate_if_exists=False)

    Raises:
        Exception: If user creation fails
    """
    endpoint = f"/v4/organizations/{org_id}/projects/{project_id}/clusters/{cluster_id}/users"

    # First, check if user already exists
    list_response = client.get(endpoint)

    if list_response.status_code == 200:
        existing_users = list_response.json().get("data", [])
        for user in existing_users:
            if user.get("name") == username:
                if recreate_if_exists:
                    # Delete existing user to recreate with new password
                    user_id = user.get("id")
                    delete_endpoint = f"{endpoint}/{user_id}"
                    console.print(
                        f"   Database user '[cyan]{username}[/cyan]' already exists. "
                        "Deleting to recreate with new password..."
                    )
                    delete_response = client.delete(delete_endpoint)
                    if delete_response.status_code != 204:
                        raise Exception(
                            f"Failed to delete existing user. Status: {delete_response.status_code}, "
                            f"Response: {delete_response.text}"
                        )
                    console.print(f"   User '[cyan]{username}[/cyan]' deleted successfully.")
                    # Continue to create new user below
                    break
                else:
                    console.print(
                        f"   Database user '[cyan]{username}[/cyan]' already exists. "
                        "Skipping creation."
                    )
                    return "existing_user_password_not_retrievable"

    # Create new user if doesn't exist
    payload = {
        "name": username,
        "access": [
            {
                "privileges": ["data_reader", "data_writer"],
                "resources": {
                    "buckets": [{"name": bucket_name, "scopes": [{"name": "*"}]}]
                },
            },
            {
                "privileges": ["analytics_reader", "analytics_writer", "analytics_manager"],
                "resources": {
                    "buckets": [{"name": bucket_name, "scopes": [{"name": "*"}]}]
                },
            }
        ],
    }

    response = client.post(endpoint, json=payload)

    if response.status_code == 201:
        data = response.json()
        console.print(f"   Database user '[cyan]{username}[/cyan]' created successfully.")
        return data["password"]
    else:
        raise Exception(
            f"Failed to create DB user. Status: {response.status_code}, Response: {response.text}"
        )


def deploy_ai_model(
    client: CapellaClient,
    org_id: str,
    model_name: str,
    deployment_name: str,
    model_type: str,
    config: CapellaConfig,
) -> str:
    """Deploy an AI model using Capella AI Services.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        model_name: Catalog model name (e.g., 'nvidia/llama-3.2-nv-embedqa-1b-v2')
        deployment_name: Name for the deployment
        model_type: Type of model ('embedding' or 'llm')
        config: Configuration with model settings

    Returns:
        Model ID

    Raises:
        Exception: If model deployment fails
    """
    endpoint = f"/v4/organizations/{org_id}/aiServices/models"

    # First, check if model already exists
    console.print(f"   Checking if model '[cyan]{deployment_name}[/cyan]' already exists...")
    try:
        list_response = client.get(endpoint)

        if list_response.status_code == 200:
            response_data = list_response.json()
            data_list = response_data.get("data", [])
            console.print(f"   Found {len(data_list)} existing model(s).")

            for item in data_list:
                # FIXED: According to OpenAPI spec, each item has a "model" key
                model_data = item.get("model", {})
                
                # Extract model info
                existing_name = model_data.get("name", "")
                model_id = model_data.get("id", "")
                status = model_data.get("status", "unknown")
                existing_config = model_data.get("config", {})
                existing_catalog_model = existing_config.get("catalogModelName", "")

                # Skip if no name found
                if not existing_name:
                    continue

                # Try case-insensitive match on deployment name
                if existing_name.lower() == deployment_name.lower():
                    console.print(
                        f"   [green]✅ Model '{existing_name}' already exists "
                        f"(Status: {status}).[/green] Model ID: [cyan]{model_id}[/cyan]"
                    )
                    
                    # Check if the catalog model matches
                    if existing_catalog_model == model_name:
                        console.print(f"   ✅ Model config matches. Reusing existing model.")
                        return model_id
                    else:
                        console.print(
                            f"   [yellow]⚠️  Warning: Existing model uses different catalog model "
                            f"('{existing_catalog_model}' vs '{model_name}'). "
                            f"Reusing existing model anyway.[/yellow]"
                        )
                        return model_id

    except Exception as e:
        console.print(f"   Warning: Could not check existing models: {e}")

    # Set compute size based on model type
    if model_type == "embedding":
        cpu = config.embedding_model_cpu
        gpu_memory = config.embedding_model_gpu_memory
    else:
        cpu = config.llm_model_cpu
        gpu_memory = config.llm_model_gpu_memory

    # Build the payload
    payload = {
        "name": deployment_name,
        "catalogModelName": model_name,
        "cloudConfig": {
            "provider": "aws",
            "region": config.ai_model_region,
            "compute": {"cpu": cpu, "gpuMemory": gpu_memory},
        },
    }

    console.print(
        f"   Creating {model_type} model '[cyan]{deployment_name}[/cyan]' "
        f"with catalog model '[cyan]{model_name}[/cyan]'..."
    )
    console.print(f"   Using compute: [yellow]{cpu} vCPUs, {gpu_memory}GB GPU[/yellow]")

    response = client.post(endpoint, json=payload)

    if response.status_code == 202:
        model_id = response.json().get("id")
        console.print(
            f"   {model_type.title()} model '[cyan]{deployment_name}[/cyan]' "
            f"deployment job submitted. Model ID: [cyan]{model_id}[/cyan]"
        )
        return model_id
    elif response.status_code in [400, 422]:
        error_text = response.text.lower()
        if "duplicate" in error_text or "already exists" in error_text:
            console.print(
                f"   [yellow]Model '[cyan]{deployment_name}[/cyan]' already exists. "
                "Searching more carefully...[/yellow]"
            )
            # Try one more thorough search
            list_response = client.get(endpoint)
            if list_response.status_code == 200:
                response_data = list_response.json()
                data_list = response_data.get("data", [])
                console.print(f"   Searching through {len(data_list)} models...")

                for item in data_list:
                    model_data = item.get("model", {})
                    existing_name = model_data.get("name", "")
                    model_id = model_data.get("id", "")

                    if existing_name:
                        console.print(f"     Checking: '{existing_name}' (ID: {model_id})")

                        if existing_name.lower() == deployment_name.lower():
                            console.print(
                                f"   [green]✅ Found existing model![/green] "
                                f"Model ID: [cyan]{model_id}[/cyan]"
                            )
                            return model_id

                # If we still can't find it, provide helpful error
                console.print(
                    f"   [red]❌ Model '{deployment_name}' reported as duplicate but not found in list.[/red]"
                )
                console.print(
                    f"   [yellow]Please check the Capella UI manually and either:[/yellow]"
                )
                console.print(
                    f"   [yellow]  1. Delete the existing model with the same name, or[/yellow]"
                )
                console.print(
                    f"   [yellow]  2. Use a different deployment name in your config[/yellow]"
                )

        raise Exception(
            f"Failed to create {model_type} model. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
    else:
        raise Exception(
            f"Failed to create {model_type} model '{deployment_name}'. "
            f"Status: {response.status_code}, Response: {response.text}"
        )


def create_ai_api_key(
    client: CapellaClient, org_id: str, region: str = "us-east-1"
) -> str:
    """Create an API key for accessing AI models.

    Args:
        client: CapellaClient instance
        org_id: Organization ID
        region: AWS region where models are deployed

    Returns:
        API key token

    Raises:
        Exception: If API key creation fails
    """
    endpoint = f"/v4/organizations/{org_id}/aiServices/models/apiKeys"

    # 180 days expiry
    payload = {
        "name": "agent-hub-api-key",
        "description": "API key for agent hub models",
        "expiry": 180,
        "allowedCIDRs": ["0.0.0.0/0"],
        "region": region,
    }

    console.print(f"   Creating API key for models in region [cyan]{region}[/cyan]...")

    response = client.post(endpoint, json=payload)

    if response.status_code == 201:
        data = response.json()
        api_key = data.get("token")
        key_id = data.get("id")
        console.print("[green]✅ API key created successfully.[/green]")
        console.print(f"   Key ID: [cyan]{key_id}[/cyan]")
        if api_key:
            console.print(f"   Token: [cyan]{api_key[:20]}...[/cyan]")
        return api_key
    else:
        raise Exception(
            f"Failed to create API key. Status: {response.status_code}, Response: {response.text}"
        )
