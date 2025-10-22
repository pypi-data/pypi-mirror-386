"""
Semantic Model Deployer - DirectLake mode for Fabric Lakehouses
Uses duckrun's authentication. Works anywhere duckrun works.
"""

import requests
import json
import time
import base64


class FabricRestClient:
    """Fabric REST API client using duckrun's authentication."""
    
    def __init__(self):
        self.base_url = "https://api.fabric.microsoft.com"
        self.token = None
        self._get_token()
    
    def _get_token(self):
        """Get Fabric API token using duckrun's auth module"""
        from duckrun.auth import get_fabric_api_token
        self.token = get_fabric_api_token()
        if not self.token:
            raise Exception("Failed to get Fabric API token")
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get(self, endpoint: str):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response
    
    def post(self, endpoint: str, json: dict = None):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self._get_headers(), json=json)
        response.raise_for_status()
        return response


def get_workspace_id(workspace_name_or_id, client):
    """Get workspace ID by name or validate if already a GUID"""
    import re
    
    # Check if input is already a GUID
    guid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if guid_pattern.match(workspace_name_or_id):
        # It's already a GUID, verify it exists
        try:
            response = client.get(f"/v1/workspaces/{workspace_name_or_id}")
            workspace_name = response.json().get('displayName', workspace_name_or_id)
            print(f"✓ Found workspace: {workspace_name}")
            return workspace_name_or_id
        except:
            raise ValueError(f"Workspace with ID '{workspace_name_or_id}' not found")
    
    # It's a name, search for it
    response = client.get("/v1/workspaces")
    workspaces = response.json().get('value', [])
    
    workspace_match = next((ws for ws in workspaces if ws.get('displayName') == workspace_name_or_id), None)
    if not workspace_match:
        raise ValueError(f"Workspace '{workspace_name_or_id}' not found")
    
    workspace_id = workspace_match['id']
    print(f"✓ Found workspace: {workspace_name_or_id}")
    return workspace_id


def get_lakehouse_id(lakehouse_name_or_id, workspace_id, client):
    """Get lakehouse ID by name or validate if already a GUID"""
    import re
    
    # Check if input is already a GUID
    guid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if guid_pattern.match(lakehouse_name_or_id):
        # It's already a GUID, verify it exists
        try:
            response = client.get(f"/v1/workspaces/{workspace_id}/lakehouses")
            items = response.json().get('value', [])
            lakehouse_match = next((item for item in items if item.get('id') == lakehouse_name_or_id), None)
            if lakehouse_match:
                lakehouse_name = lakehouse_match.get('displayName', lakehouse_name_or_id)
                print(f"✓ Found lakehouse: {lakehouse_name}")
                return lakehouse_name_or_id
            else:
                raise ValueError(f"Lakehouse with ID '{lakehouse_name_or_id}' not found")
        except Exception as e:
            raise ValueError(f"Lakehouse with ID '{lakehouse_name_or_id}' not found: {e}")
    
    # It's a name, search for it
    response = client.get(f"/v1/workspaces/{workspace_id}/lakehouses")
    items = response.json().get('value', [])
    
    lakehouse_match = next((item for item in items if item.get('displayName') == lakehouse_name_or_id), None)
    if not lakehouse_match:
        raise ValueError(f"Lakehouse '{lakehouse_name_or_id}' not found")
    
    lakehouse_id = lakehouse_match['id']
    print(f"✓ Found lakehouse: {lakehouse_name_or_id}")
    return lakehouse_id


def get_dataset_id(dataset_name, workspace_id, client):
    """Get dataset ID by name"""
    response = client.get(f"/v1/workspaces/{workspace_id}/semanticModels")
    items = response.json().get('value', [])
    
    dataset_match = next((item for item in items if item.get('displayName') == dataset_name), None)
    if not dataset_match:
        raise ValueError(f"Dataset '{dataset_name}' not found")
    
    return dataset_match['id']


def check_dataset_exists(dataset_name, workspace_id, client):
    """Check if dataset already exists"""
    try:
        get_dataset_id(dataset_name, workspace_id, client)
        print(f"⚠️  Dataset '{dataset_name}' already exists")
        return True
    except:
        print(f"✓ Dataset name '{dataset_name}' is available")
        return False


def refresh_dataset(dataset_name, workspace_id, client, dataset_id=None):
    """Refresh a dataset and monitor progress using Power BI API"""
    
    # If dataset_id not provided, look it up by name
    if not dataset_id:
        dataset_id = get_dataset_id(dataset_name, workspace_id, client)
    
    payload = {
        "type": "full",
        "commitMode": "transactional",
        "maxParallelism": 10,
        "retryCount": 2,
        "objects": []
    }
    
    # Use Power BI API for refresh (not Fabric API)
    powerbi_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes"
    headers = client._get_headers()
    
    response = requests.post(powerbi_url, headers=headers, json=payload)
    
    if response.status_code in [200, 202]:
        print(f"✓ Refresh initiated")
        
        # For 202, get the refresh_id from the Location header
        if response.status_code == 202:
            location = response.headers.get('Location')
            if location:
                refresh_id = location.split('/')[-1]
                print("   Monitoring refresh progress...")
                max_attempts = 60
                for attempt in range(max_attempts):
                    time.sleep(5)
                    
                    # Check refresh status using Power BI API
                    status_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes/{refresh_id}"
                    status_response = requests.get(status_url, headers=headers)
                    status_response.raise_for_status()
                    status = status_response.json().get('status')
                    
                    if status == 'Completed':
                        print(f"✓ Refresh completed successfully")
                        return
                    elif status == 'Failed':
                        error = status_response.json().get('serviceExceptionJson', '')
                        raise Exception(f"Refresh failed: {error}")
                    elif status == 'Cancelled':
                        raise Exception("Refresh was cancelled")
                    
                    if attempt % 6 == 0:
                        print(f"   Status: {status}...")
                
                raise Exception(f"Refresh timed out")
    else:
        response.raise_for_status()


def download_bim_from_github(url_or_path):
    """
    Load BIM file from URL, local file path, or workspace/model format.
    
    Args:
        url_or_path: Can be:
            - Local file path: "model.bim"
            - URL: "https://..."
            - Workspace/Model: "workspace_name/semantic_model_name"
        
    Returns:
        BIM content as dictionary
    """
    import os
    import tempfile
    
    # Check if it's a local file path
    if os.path.exists(url_or_path):
        print(f"Loading BIM file from local path...")
        with open(url_or_path, 'r', encoding='utf-8') as f:
            bim_content = json.load(f)
        print(f"✓ BIM file loaded from: {url_or_path}")
    # Check if it's a URL
    elif url_or_path.startswith(('http://', 'https://')):
        print(f"Downloading BIM file from URL...")
        response = requests.get(url_or_path)
        response.raise_for_status()
        bim_content = response.json()
        print(f"✓ BIM file downloaded from URL")
    # Check if it's workspace/model format
    elif "/" in url_or_path and not os.path.exists(url_or_path):
        print(f"Downloading BIM from workspace/model...")
        parts = url_or_path.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid workspace/model format: '{url_or_path}'. Expected: 'workspace_name/model_name'")
        
        ws_name, model_name = parts
        
        # Download BIM from the semantic model
        client = FabricRestClient()
        ws_id = get_workspace_id(ws_name, client)
        
        # Get semantic model ID
        response = client.get(f"/v1/workspaces/{ws_id}/semanticModels")
        models = response.json().get('value', [])
        model = next((m for m in models if m.get('displayName') == model_name), None)
        
        if not model:
            raise ValueError(f"Semantic model '{model_name}' not found in workspace '{ws_name}'")
        
        model_id = model.get('id')
        
        # Get definition using Items API with TMSL format
        definition_url = f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items/{model_id}/getDefinition"
        headers = client._get_headers()
        response = requests.post(f"{definition_url}?format=TMSL", headers=headers)
        response.raise_for_status()
        
        # Handle long-running operation
        if response.status_code == 202:
            operation_id = response.headers.get('x-ms-operation-id')
            max_attempts = 30
            
            for attempt in range(max_attempts):
                time.sleep(2)
                
                status_url = f"https://api.fabric.microsoft.com/v1/operations/{operation_id}"
                status_response = requests.get(status_url, headers=headers)
                status = status_response.json().get('status')
                
                if status == 'Succeeded':
                    result_url = f"https://api.fabric.microsoft.com/v1/operations/{operation_id}/result"
                    result_response = requests.get(result_url, headers=headers)
                    result_data = result_response.json()
                    break
                elif status == 'Failed':
                    error = status_response.json().get('error', {})
                    raise Exception(f"Download operation failed: {error.get('message')}")
                elif attempt == max_attempts - 1:
                    raise Exception("Download operation timed out")
        else:
            result_data = response.json()
        
        # Extract BIM content
        definition = result_data.get('definition', {})
        parts = definition.get('parts', [])
        
        bim_part = next((p for p in parts if p.get('path', '').endswith('.bim')), None)
        if not bim_part:
            raise Exception("No BIM file found in semantic model definition")
        
        # Decode BIM
        import base64
        bim_payload = bim_part.get('payload', '')
        bim_content_str = base64.b64decode(bim_payload).decode('utf-8')
        bim_content = json.loads(bim_content_str)
        
        print(f"✓ BIM downloaded from {ws_name}/{model_name}")
    else:
        raise ValueError(f"Invalid BIM source: '{url_or_path}'. Must be a valid file path, URL, or 'workspace/model' format.")
    
    print(f"  - Tables: {len(bim_content.get('model', {}).get('tables', []))}")
    print(f"  - Relationships: {len(bim_content.get('model', {}).get('relationships', []))}")
    return bim_content


def update_bim_for_directlake(bim_content, workspace_id, lakehouse_id, schema_name):
    """Update BIM file for DirectLake mode"""
    
    new_url = f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}"
    expression_name = None
    
    # Update or create DirectLake expression
    if 'model' in bim_content and 'expressions' in bim_content['model']:
        for expr in bim_content['model']['expressions']:
            if 'DirectLake' in expr['name'] or expr.get('kind') == 'm':
                expression_name = expr['name']
                expr['expression'] = [
                    "let",
                    f"    Source = AzureStorage.DataLake(\"{new_url}\", [HierarchicalNavigation=true])",
                    "in",
                    "    Source"
                ]
                break
    
    if not expression_name:
        expression_name = f"DirectLake - {schema_name}"
        if 'expressions' not in bim_content['model']:
            bim_content['model']['expressions'] = []
        
        bim_content['model']['expressions'].append({
            "name": expression_name,
            "kind": "m",
            "expression": [
                "let",
                f"    Source = AzureStorage.DataLake(\"{new_url}\", [HierarchicalNavigation=true])",
                "in",
                "    Source"
            ],
            "lineageTag": f"directlake-{schema_name}-source"
        })
    
    # Update table partitions for DirectLake
    if 'tables' in bim_content['model']:
        for table in bim_content['model']['tables']:
            if 'partitions' in table:
                for partition in table['partitions']:
                    if 'source' in partition:
                        partition['mode'] = 'directLake'
                        partition['source'] = {
                            "type": "entity",
                            "entityName": partition['source'].get('entityName', table['name']),
                            "expressionSource": expression_name,
                            "schemaName": schema_name
                        }
    
    print(f"✓ Updated BIM for DirectLake")
    print(f"  - OneLake URL: {new_url}")
    print(f"  - Schema: {schema_name}")
    
    return bim_content


def create_dataset_from_bim(dataset_name, bim_content, workspace_id, client):
    """Create semantic model from BIM using Fabric REST API and return the dataset ID"""
    # Convert to base64
    bim_json = json.dumps(bim_content, indent=2)
    bim_base64 = base64.b64encode(bim_json.encode('utf-8')).decode('utf-8')
    
    pbism_content = {"version": "1.0"}
    pbism_json = json.dumps(pbism_content)
    pbism_base64 = base64.b64encode(pbism_json.encode('utf-8')).decode('utf-8')
    
    payload = {
        "displayName": dataset_name,
        "definition": {
            "parts": [
                {
                    "path": "model.bim",
                    "payload": bim_base64,
                    "payloadType": "InlineBase64"
                },
                {
                    "path": "definition.pbism",
                    "payload": pbism_base64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    response = client.post(
        f"/v1/workspaces/{workspace_id}/semanticModels",
        json=payload
    )
    
    print(f"✓ Semantic model created")
    
    # Handle long-running operation and return the dataset ID
    if response.status_code == 202:
        operation_id = response.headers.get('x-ms-operation-id')
        print(f"   Waiting for operation to complete...")
        
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            
            # Check if operation is complete by getting the status
            status_response = client.get(f"/v1/operations/{operation_id}")
            status = status_response.json().get('status')
            
            if status == 'Succeeded':
                print(f"✓ Operation completed")
                
                # Now get the result (only after status is Succeeded)
                try:
                    result_response = client.get(f"/v1/operations/{operation_id}/result")
                    result_data = result_response.json()
                    dataset_id = result_data.get('id')
                    if dataset_id:
                        return dataset_id
                except:
                    # If result endpoint fails, fallback to searching by name
                    pass
                
                # Fallback: search for the dataset by name
                return get_dataset_id(dataset_name, workspace_id, client)
                
            elif status == 'Failed':
                error = status_response.json().get('error', {})
                raise Exception(f"Operation failed: {error.get('message')}")
            elif attempt == max_attempts - 1:
                raise Exception(f"Operation timed out")
    
    # For non-async responses (status 200/201)
    result_data = response.json()
    dataset_id = result_data.get('id')
    if dataset_id:
        return dataset_id
    else:
        # Fallback: search for the dataset by name
        return get_dataset_id(dataset_name, workspace_id, client)


def deploy_semantic_model(workspace_name_or_id, lakehouse_name_or_id, schema_name, dataset_name, 
                         bim_url_or_path, wait_seconds=5):
    """
    Deploy a semantic model using DirectLake mode.
    
    Args:
        workspace_name_or_id: Name or GUID of the target workspace
        lakehouse_name_or_id: Name or GUID of the lakehouse
        schema_name: Schema name (e.g., 'dbo', 'staging')
        dataset_name: Name for the semantic model
        bim_url_or_path: URL to the BIM file or local file path (e.g., 'model.bim' or 'https://...')
        wait_seconds: Seconds to wait before refresh (default: 5)
    
    Returns:
        1 for success, 0 for failure
    
    Examples:
        # Using a URL
        dr = Duckrun.connect("My Workspace/My Lakehouse.lakehouse/dbo")
        dr.deploy("https://raw.githubusercontent.com/.../model.bim")
        
        # Using a local file
        dr.deploy("./my_model.bim")
        dr.deploy("C:/path/to/model.bim")
    """
    print("=" * 70)
    print("Semantic Model Deployment (DirectLake)")
    print("=" * 70)
    
    client = FabricRestClient()
    
    try:
        # Step 1: Get workspace ID
        print("\n[Step 1/6] Getting workspace information...")
        workspace_id = get_workspace_id(workspace_name_or_id, client)
        
        # Step 2: Check if dataset exists
        print(f"\n[Step 2/6] Checking if dataset '{dataset_name}' exists...")
        dataset_exists = check_dataset_exists(dataset_name, workspace_id, client)
        
        if dataset_exists:
            print(f"\n✓ Dataset exists - refreshing...")
            
            if wait_seconds > 0:
                print(f"   Waiting {wait_seconds} seconds...")
                time.sleep(wait_seconds)
            
            print("\n[Step 6/6] Refreshing semantic model...")
            refresh_dataset(dataset_name, workspace_id, client)
            
            print("\n" + "=" * 70)
            print("🎉 Refresh Completed!")
            print("=" * 70)
            print(f"Dataset: {dataset_name}")
            print("=" * 70)
            return 1
        
        # Step 3: Get lakehouse ID
        print(f"\n[Step 3/6] Finding lakehouse...")
        lakehouse_id = get_lakehouse_id(lakehouse_name_or_id, workspace_id, client)
        
        # Step 4: Download and update BIM
        print("\n[Step 4/6] Loading and configuring BIM file...")
        bim_content = download_bim_from_github(bim_url_or_path)
        
        modified_bim = update_bim_for_directlake(bim_content, workspace_id, lakehouse_id, schema_name)
        modified_bim['name'] = dataset_name
        modified_bim['id'] = dataset_name
        
        # Step 5: Deploy and get the dataset ID
        print("\n[Step 5/6] Deploying semantic model...")
        dataset_id = create_dataset_from_bim(dataset_name, modified_bim, workspace_id, client)
        print(f"   Dataset ID: {dataset_id}")
        
        if wait_seconds > 0:
            print(f"   Waiting {wait_seconds} seconds before refresh...")
            time.sleep(wait_seconds)
        
        # Step 6: Refresh using the dataset ID returned from creation
        print("\n[Step 6/6] Refreshing semantic model...")
        refresh_dataset(dataset_name, workspace_id, client, dataset_id=dataset_id)
        
        print("\n" + "=" * 70)
        print("🎉 Deployment Completed!")
        print("=" * 70)
        print(f"Dataset: {dataset_name}")
        print(f"Workspace: {workspace_name_or_id}")
        print(f"Lakehouse: {lakehouse_name_or_id}")
        print(f"Schema: {schema_name}")
        print("=" * 70)
        
        return 1
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Deployment Failed")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print(f"  - Verify workspace '{workspace_name_or_id}' exists")
        print(f"  - Verify lakehouse '{lakehouse_name_or_id}' exists")
        print(f"  - Ensure tables exist in '{schema_name}' schema")
        print(f"  - Check tables are in Delta format")
        print("=" * 70)
        return 0


def copy_model(ws_source, model_name, destination, new_model_name=None, wait_seconds=5):
    """
    Copy a semantic model from one workspace to another.
    
    This is a convenience function that downloads a BIM file from a source workspace
    and deploys it to a destination lakehouse in one operation.
    
    Args:
        ws_source: Source workspace name or GUID
        model_name: Name of the semantic model to copy
        destination: Destination in format "workspace/lakehouse.lakehouse/schema"
        new_model_name: Name for the new semantic model (default: same as source)
        wait_seconds: Seconds to wait before refresh (default: 5)
    
    Returns:
        1 for success, 0 for failure
    
    Examples:
        # Copy to same workspace, different lakehouse
        copy_model("My Workspace", "Sales Model", "My Workspace/Target Lakehouse.lakehouse/dbo")
        
        # Copy to different workspace with new name
        copy_model("Source WS", "Production Model", "Target WS/Data Lake.lakehouse/analytics", 
                   new_model_name="Production Model - Copy")
        
        # Using the connect pattern
        import duckrun
        duckrun.semantic_model.copy_model("Source", "Model", "Target/LH.lakehouse/dbo")
    """
    import tempfile
    import os
    
    print("=" * 70)
    print("Semantic Model Copy Operation")
    print("=" * 70)
    
    try:
        # Parse destination
        parts = destination.split("/")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid destination format: '{destination}'. "
                "Expected format: 'workspace/lakehouse.lakehouse/schema'"
            )
        
        ws_dest, lakehouse, schema = parts
        
        # Remove .lakehouse suffix if present
        if lakehouse.endswith(".lakehouse"):
            lakehouse = lakehouse[:-10]
        
        # Use source model name if new name not provided
        if not new_model_name:
            new_model_name = model_name
        
        print(f"\nSource:")
        print(f"  Workspace: {ws_source}")
        print(f"  Model: {model_name}")
        print(f"\nDestination:")
        print(f"  Workspace: {ws_dest}")
        print(f"  Lakehouse: {lakehouse}")
        print(f"  Schema: {schema}")
        print(f"  New Model Name: {new_model_name}")
        
        # Step 1: Download BIM from source
        print("\n" + "-" * 70)
        print("[Step 1/2] Downloading BIM from source workspace...")
        print("-" * 70)
        
        client = FabricRestClient()
        ws_source_id = get_workspace_id(ws_source, client)
        
        # Use temporary file for BIM content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bim', delete=False, encoding='utf-8') as tmp_file:
            temp_bim_path = tmp_file.name
            
            # Get semantic model ID
            response = client.get(f"/v1/workspaces/{ws_source_id}/semanticModels")
            models = response.json().get('value', [])
            model = next((m for m in models if m.get('displayName') == model_name), None)
            
            if not model:
                raise ValueError(f"Semantic model '{model_name}' not found in workspace '{ws_source}'")
            
            model_id = model.get('id')
            print(f"✓ Found source model: {model_name} (ID: {model_id})")
            
            # Get definition using Items API with TMSL format
            print("  Downloading BIM definition...")
            definition_url = f"https://api.fabric.microsoft.com/v1/workspaces/{ws_source_id}/items/{model_id}/getDefinition"
            headers = client._get_headers()
            response = requests.post(f"{definition_url}?format=TMSL", headers=headers)
            response.raise_for_status()
            
            # Handle long-running operation
            if response.status_code == 202:
                operation_id = response.headers.get('x-ms-operation-id')
                max_attempts = 30
                
                for attempt in range(max_attempts):
                    time.sleep(2)
                    
                    status_url = f"https://api.fabric.microsoft.com/v1/operations/{operation_id}"
                    status_response = requests.get(status_url, headers=headers)
                    status = status_response.json().get('status')
                    
                    if status == 'Succeeded':
                        result_url = f"https://api.fabric.microsoft.com/v1/operations/{operation_id}/result"
                        result_response = requests.get(result_url, headers=headers)
                        result_data = result_response.json()
                        break
                    elif status == 'Failed':
                        error = status_response.json().get('error', {})
                        raise Exception(f"Download operation failed: {error.get('message')}")
                    elif attempt == max_attempts - 1:
                        raise Exception("Download operation timed out")
            else:
                result_data = response.json()
            
            # Extract BIM content
            definition = result_data.get('definition', {})
            parts = definition.get('parts', [])
            
            bim_part = next((p for p in parts if p.get('path', '').endswith('.bim')), None)
            if not bim_part:
                raise Exception("No BIM file found in semantic model definition")
            
            # Decode and save BIM
            import base64
            bim_payload = bim_part.get('payload', '')
            bim_content = base64.b64decode(bim_payload).decode('utf-8')
            bim_json = json.loads(bim_content)
            
            # Write to temp file
            json.dump(bim_json, tmp_file, indent=2)
            
            print(f"✓ BIM downloaded successfully")
            print(f"  - Tables: {len(bim_json.get('model', {}).get('tables', []))}")
            print(f"  - Relationships: {len(bim_json.get('model', {}).get('relationships', []))}")
        
        # Step 2: Deploy to destination
        print("\n" + "-" * 70)
        print("[Step 2/2] Deploying to destination workspace...")
        print("-" * 70)
        
        result = deploy_semantic_model(
            workspace_name_or_id=ws_dest,
            lakehouse_name_or_id=lakehouse,
            schema_name=schema,
            dataset_name=new_model_name,
            bim_url_or_path=temp_bim_path,
            wait_seconds=wait_seconds
        )
        
        # Clean up temp file
        try:
            os.unlink(temp_bim_path)
        except:
            pass
        
        if result == 1:
            print("\n" + "=" * 70)
            print("🎉 Copy Operation Completed!")
            print("=" * 70)
            print(f"Source: {ws_source}/{model_name}")
            print(f"Destination: {ws_dest}/{lakehouse}/{schema}/{new_model_name}")
            print("=" * 70)
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Copy Operation Failed")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print(f"  - Verify source workspace '{ws_source}' and model '{model_name}' exist")
        print(f"  - Verify destination workspace and lakehouse exist")
        print(f"  - Ensure you have permissions for both workspaces")
        print("=" * 70)
        return 0

