"""
Multi-System Connector Test Script
Using Universal API Connector Package

This refactored version uses the universal-api-connector package
instead of direct requests calls.
"""

import os
import json
import requests  # Only for token fetching
from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from azure.ai.agents.models import ListSortOrder

# Import your universal API connector package
from universal_api_connector_v2 import APIConnector


load_dotenv()

# ==============================
# CONFIGURATION
# ==============================

SYSTEMS = {
    "SHAREPOINT": {
        "base_url": "https://graph.microsoft.com/v1.0",
        "site_path": os.getenv("SHAREPOINT_SITE_PATH"),
        "tenant_id": os.getenv("TENANT_ID"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "site_id": os.getenv("SHAREPOINT_SITE_ID"),
        "site_hostname": "nihilent.sharepoint.com",
        "list_name": os.getenv("SHAREPOINT_LIST_NAME", "VendorList"),
    }
}

AZURE_AI_CONFIG = {
    "tenant_id": os.getenv("AZURE_AI_TENANT_ID"),
    "client_id": os.getenv("AZURE_AI_CLIENT_ID"),
    "client_secret": os.getenv("AZURE_AI_CLIENT_SECRET"),
    "project_endpoint": os.getenv(
        "AZURE_AI_PROJECT_ENDPOINT",
        "https://p2pbuddyfoundry1.services.ai.azure.com/api/projects/P2PbuddyProject",
    ),
    "agent_id": os.getenv("AZURE_AI_AGENT_ID"),
}

CONFIDENCE_THRESHOLD = 0.70


# ==============================
# SHAREPOINT AUTH HANDLER
# ==============================

class SharePointGraphAuth:
    """
    Authentication handler for SharePoint via Microsoft Graph API.
    Uses OAuth2 with Microsoft Identity Platform v2.0.
    """
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
    
    def _fetch_token(self):
        """Fetch OAuth2 access token from Microsoft Identity Platform."""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            raise Exception(f"Token request failed: {response.text}")
        
        token_response = response.json()
        self.access_token = token_response["access_token"]
        
        # Set token expiry (usually 3600 seconds, refresh 60s early)
        expires_in = token_response.get("expires_in", 3600)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
    
    def get_auth_headers(self):
        """
        Get authentication headers for Microsoft Graph API.
        Automatically refreshes token if expired.
        """
        # Refresh token if expired or missing
        if not self.access_token or not self.token_expiry or datetime.now() >= self.token_expiry:
            self._fetch_token()
        
        return {'Authorization': f'Bearer {self.access_token}'}


# ==============================
# SHAREPOINT OPERATIONS (Using Universal API Connector)
# ==============================

def get_sharepoint_connector() -> APIConnector:
    """
    Create and return SharePoint connector using Universal API Connector.
    """
    config = SYSTEMS["SHAREPOINT"]
    
    # Create auth handler
    sharepoint_auth = SharePointGraphAuth(
        tenant_id=config["tenant_id"],
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )
    
    # Create connector with auth handler
    connector = APIConnector(
        base_url=config["base_url"],
        auth_handler=sharepoint_auth.get_auth_headers,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        timeout=30,
        log_level="INFO"
    )
    
    return connector


def get_sharepoint_list_items(connector: APIConnector, list_name: str = None, filters: dict = None) -> dict:
    """
    Get items from SharePoint list using Universal API Connector.
    
    Args:
        connector: APIConnector instance
        list_name: Name of the SharePoint list
        filters: Optional filters (vendor_name, country, etc.)
    
    Returns:
        Dict with list items
    """
    config = SYSTEMS["SHAREPOINT"]
    
    # Build site URL
    if config.get("site_id"):
        site_path = f"/sites/{config['site_id']}"
    else:
        site_path = f"/sites/{config['site_hostname']}:{config['site_path']}"
    
    # Get list name
    if not list_name:
        list_name = config.get("list_name", "VendorList")
    
    # Build endpoint
    endpoint = f"{site_path}/lists/{list_name}/items"
    
    # Use connector to make GET request
    try:
        response = connector.get(endpoint, params={"expand": "fields"})
        
        # Apply filters if provided
        if filters:
            items = response.get("value", [])
            filtered_items = filter_vendor_items(items, filters)
            return {"value": filtered_items}
        
        return response
        
    except Exception as e:
        return {"error": f"Failed to get list items: {str(e)}"}


def create_sharepoint_list_item(connector: APIConnector, list_name: str = None, data: dict = None) -> dict:
    """
    Create item in SharePoint list using Universal API Connector.
    
    Args:
        connector: APIConnector instance
        list_name: Name of the SharePoint list
        data: Item data (vendor_name, country, etc.)
    
    Returns:
        Created item data
    """
    config = SYSTEMS["SHAREPOINT"]
    
    # Build site URL
    if config.get("site_id"):
        site_path = f"/sites/{config['site_id']}"
    else:
        site_path = f"/sites/{config['site_hostname']}:{config['site_path']}"
    
    # Get list name
    if not list_name:
        list_name = config.get("list_name", "VendorList")
    
    # Build endpoint
    endpoint = f"{site_path}/lists/{list_name}/items"
    
    # Prepare item data
    now = datetime.now().isoformat()
    item_data = {
        "fields": {
            "Title": data.get("vendor_name", "Unknown Vendor"),
            "VendorName": data.get("vendor_name"),
            "Country": data.get("country"),
            "CreatedDate": now,
            "LastModified": now,
        }
    }
    
    # Use connector to make POST request
    try:
        response = connector.post(endpoint, json=item_data)
        return response
        
    except Exception as e:
        return {"error": f"Failed to create list item: {str(e)}"}


def filter_vendor_items(items: list, filters: dict) -> list:
    """
    Filter vendor items based on criteria.
    
    Args:
        items: List of SharePoint items
        filters: Filter criteria (vendor_name, country, etc.)
    
    Returns:
        Filtered list of items
    """
    filtered = []
    
    vendor_name = filters.get("vendor_name", "").lower()
    country = filters.get("country", "").lower()
    
    for item in items:
        fields = item.get("fields", {})
        match = True
        
        # Check vendor name filter
        if vendor_name:
            item_vendor = fields.get("VendorName", "").lower()
            if vendor_name not in item_vendor:
                match = False
        
        # Check country filter
        if country:
            item_country = fields.get("Country", "").lower()
            if country != item_country:
                match = False
        
        if match:
            filtered.append(item)
    
    return filtered


def normalize_vendor_data(data: dict) -> list:
    """
    Normalize SharePoint vendor list items to standard format.
    
    Args:
        data: SharePoint API response
    
    Returns:
        List of normalized vendor records
    """
    normalized = []
    items = data.get("value", []) if isinstance(data, dict) else data
    
    for item in items:
        fields = item.get("fields", {})
        normalized.append({
            "vendor_name": fields.get("VendorName") or fields.get("Title"),
            "country": fields.get("Country", "Unknown"),
            "item_id": item.get("id"),
            "created_date": fields.get("CreatedDate"),
            "last_modified": fields.get("LastModified"),
        })
    
    return normalized


# ==============================
# AZURE AI ASSISTANT (Not using connector - uses Azure SDK)
# ==============================

def query_azure_ai_assistant(utterance: str, entities: dict = None) -> dict:
    """
    Query Azure AI Foundry Agent.
    
    Note: This uses Azure SDK directly, not the Universal API Connector,
    because Azure AI Foundry has specialized SDK requirements.
    
    Args:
        utterance: User's question/query
        entities: Optional context entities
    
    Returns:
        Agent response
    """
    try:
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=AZURE_AI_CONFIG["tenant_id"],
            client_id=AZURE_AI_CONFIG["client_id"],
            client_secret=AZURE_AI_CONFIG["client_secret"],
        )
        
        # Create project client
        project = AIProjectClient(
            credential=credential,
            endpoint=AZURE_AI_CONFIG["project_endpoint"]
        )
        
        # Get agent
        agent = project.agents.get_agent(AZURE_AI_CONFIG["agent_id"])
        
        # Create thread
        thread = project.agents.threads.create()
        
        # Build context from entities
        context = []
        if entities:
            for k, v in entities.items():
                context.append(f"{k}: {v}")
        context_text = "Context: " + ", ".join(context) + "\n" if context else ""
        
        # Create message
        message = project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=context_text + f"Question: {utterance}"
        )
        
        # Run agent
        run = project.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        # Check for errors
        if run.status == "failed":
            return {"status": "error", "error": run.last_error}
        
        # Get messages
        messages = project.agents.messages.list(
            thread_id=thread.id,
            order=ListSortOrder.ASCENDING
        )
        
        # Extract response
        for msg in messages:
            if msg.role == "assistant" and msg.text_messages:
                return {
                    "status": "success",
                    "response": msg.text_messages[-1].text.value
                }
        
        return {"status": "success", "response": "No response received from the agent."}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==============================
# TEST FUNCTIONS
# ==============================

def test_sharepoint_lookup():
    """Test SharePoint vendor lookup using Universal API Connector."""
    print("\n" + "="*70)
    print("TEST 1: SharePoint Vendor Lookup (Using Universal API Connector)")
    print("="*70)
    
    try:
        # Create connector
        print("\n→ Creating SharePoint connector...")
        connector = get_sharepoint_connector()
        print("✓ Connector created successfully")
        
        # Test 1: Get all vendors
        print("\n→ Test 1a: Getting all vendors...")
        result = get_sharepoint_list_items(connector)
        
        if "error" in result:
            print(f"✗ Error: {result['error']}")
        else:
            all_vendors = normalize_vendor_data(result)
            print(f"✓ Retrieved {len(all_vendors)} vendors")
            
            # Show first 3
            for vendor in all_vendors[:3]:
                print(f"  - {vendor['vendor_name']} ({vendor['country']})")
        
        # Test 2: Get vendors filtered by country
        print("\n→ Test 1b: Getting vendors from India...")
        result = get_sharepoint_list_items(
            connector,
            filters={"country": "India"}
        )
        
        if "error" in result:
            print(f"✗ Error: {result['error']}")
        else:
            india_vendors = normalize_vendor_data(result)
            print(f"✓ Retrieved {len(india_vendors)} vendors from India")
            print("\nVendors from India:")
            print(json.dumps(india_vendors, indent=2))
        
        # Test 3: Create new vendor (commented out to avoid creating test data)
        # print("\n→ Test 1c: Creating new vendor...")
        # new_vendor = create_sharepoint_list_item(
        #     connector,
        #     data={
        #         "vendor_name": "Test Vendor Ltd",
        #         "country": "India"
        #     }
        # )
        # if "error" in new_vendor:
        #     print(f"✗ Error: {new_vendor['error']}")
        # else:
        #     print(f"✓ Created vendor: {new_vendor.get('id')}")
        
        # Close connector
        connector.close()
        print("\n✓ SharePoint tests completed")
        
    except Exception as e:
        print(f"\n✗ SharePoint test failed: {e}")
        import traceback
        traceback.print_exc()


def test_azure_ai_query():
    """Test Azure AI query."""
    print("\n" + "="*70)
    print("TEST 2: Azure AI Assistant Query")
    print("="*70)
    
    try:
        print("\n→ Querying Azure AI Assistant...")
        utterance = "I need to register a supplier, what steps should I follow?"
        entities = {"country": "India"}
        
        response = query_azure_ai_assistant(utterance, entities)
        
        if response.get("status") == "error":
            print(f"✗ Error: {response['error']}")
        else:
            print("✓ AI Response received:")
            print("\nQuestion:", utterance)
            print("Context:", entities)
            print("\nResponse:")
            print(response.get("response", "No response"))
        
        print("\n✓ Azure AI test completed")
        
    except Exception as e:
        print(f"\n✗ Azure AI test failed: {e}")
        import traceback
        traceback.print_exc()


def test_combined_workflow():
    """Test combined workflow: AI query + SharePoint lookup."""
    print("\n" + "="*70)
    print("TEST 3: Combined Workflow")
    print("="*70)
    
    try:
        # Step 1: User asks a question
        user_question = "I need to register a supplier in India, what steps should I follow?"
        print(f"\n→ User Question: {user_question}")
        
        # Step 2: Query Azure AI for guidance
        print("\n→ Step 1: Getting AI guidance...")
        ai_response = query_azure_ai_assistant(
            user_question,
            entities={"country": "India"}
        )
        
        if ai_response.get("status") == "error":
            print(f"✗ AI Query failed: {ai_response['error']}")
        else:
            print("✓ AI Guidance:")
            print(ai_response.get("response", "No response"))
        
        # Step 3: Look up existing vendors in SharePoint
        print("\n→ Step 2: Checking existing vendors in India...")
        connector = get_sharepoint_connector()
        
        vendors_result = get_sharepoint_list_items(
            connector,
            filters={"country": "India"}
        )
        
        if "error" in vendors_result:
            print(f"✗ SharePoint lookup failed: {vendors_result['error']}")
        else:
            vendors = normalize_vendor_data(vendors_result)
            print(f"✓ Found {len(vendors)} existing vendors in India")
            
            if vendors:
                print("\nExisting vendors:")
                for vendor in vendors[:5]:
                    print(f"  - {vendor['vendor_name']}")
        
        connector.close()
        
        # Step 4: Combine results
        print("\n→ Step 3: Combined results:")
        workflow_result = {
            "timestamp": datetime.now().isoformat(),
            "user_question": user_question,
            "ai_guidance": ai_response.get("response", ""),
            "existing_vendors_count": len(vendors) if "error" not in vendors_result else 0,
            "existing_vendors": vendors[:5] if "error" not in vendors_result else []
        }
        
        print(json.dumps(workflow_result, indent=2))
        
        # Save to file
        output_file = f"workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        print("\n✓ Combined workflow test completed")
        
    except Exception as e:
        print(f"\n✗ Combined workflow test failed: {e}")
        import traceback
        traceback.print_exc()


def test_payload_processing():
    """Test processing the original payload structure."""
    print("\n" + "="*70)
    print("TEST 4: Payload Processing")
    print("="*70)
    
    # Original payload
    payload = {
        "intents": [
            {
                "name": "search_text",
                "Source_System": "SHAREPOINT",
                "utterance": "I need to register a supplier, what steps should I follow?",
                "confidence": 0.85
            },
            {
                "name": "search_text",
                "Source_System": "SHAREPOINT",
                "utterance": "The supplier doesn't appear in the system, what's the next step?",
                "confidence": 0.60
            },
            {
                "name": "vendor_lookup",
                "Source_System": "SHAREPOINT",
                "confidence": 0.88
            }
        ],
        "entities": [
            {
                "type": "country",
                "value": "India"
            }
        ]
    }
    
    print("\n→ Processing payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Extract high-confidence intents
        print(f"\n→ Filtering high-confidence intents (>={CONFIDENCE_THRESHOLD})...")
        high_conf_intents = [
            intent for intent in payload["intents"]
            if intent.get("confidence", 0) >= CONFIDENCE_THRESHOLD
        ]
        print(f"✓ Found {len(high_conf_intents)} high-confidence intents")
        
        # Extract entities
        entities_dict = {}
        for entity in payload.get("entities", []):
            entities_dict[entity["type"]] = entity["value"]
        print(f"✓ Extracted entities: {entities_dict}")
        
        # Process SharePoint intents
        connector = get_sharepoint_connector()
        
        for intent in high_conf_intents:
            if intent.get("Source_System") == "SHAREPOINT":
                print(f"\n→ Processing intent: {intent['name']}")
                
                if intent["name"] == "vendor_lookup":
                    # Lookup vendors
                    result = get_sharepoint_list_items(
                        connector,
                        filters=entities_dict
                    )
                    
                    if "error" not in result:
                        vendors = normalize_vendor_data(result)
                        print(f"  ✓ Found {len(vendors)} vendors")
                
                elif intent["name"] == "search_text" and "utterance" in intent:
                    # Query AI for guidance
                    response = query_azure_ai_assistant(
                        intent["utterance"],
                        entities_dict
                    )
                    
                    if response.get("status") != "error":
                        print(f"  ✓ Got AI response")
        
        connector.close()
        print("\n✓ Payload processing completed")
        
    except Exception as e:
        print(f"\n✗ Payload processing failed: {e}")
        import traceback
        traceback.print_exc()


# ==============================
# MAIN
# ==============================

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 Multi-System Connector Tests (Using Universal API Connector)")
    print("="*70)
    
    print("\n📋 Configuration:")
    print(f"  SharePoint Site: {SYSTEMS['SHAREPOINT']['site_hostname']}")
    print(f"  SharePoint List: {SYSTEMS['SHAREPOINT']['list_name']}")
    print(f"  Azure AI Endpoint: {AZURE_AI_CONFIG['project_endpoint']}")
    print(f"  Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    
    # Check configuration
    if not SYSTEMS["SHAREPOINT"]["tenant_id"] or not SYSTEMS["SHAREPOINT"]["client_id"]:
        print("\n⚠️  WARNING: Missing SharePoint configuration!")
        print("  Please set environment variables in .env file")
        response = input("\n  Continue with mock tests? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run tests
    try:
        test_payload_processing()
        test_sharepoint_lookup()
        test_azure_ai_query()
        test_combined_workflow()
        
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()