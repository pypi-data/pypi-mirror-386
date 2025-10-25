"""
LFC Demo - REST API Library

This module provides REST API utilities for creating and managing Databricks resources:
- Pipeline management (create, edit, delete, start)
- Schema management (create, delete, tag)
- Job management (create, delete, run)
- Automatic cleanup scheduling
- Token management

Usage:
    from lfcdemolib import LfcScheduler, DbxRest
    
    # Create scheduler (required)
    scheduler = LfcScheduler()
    
    # In Databricks environment
    dbx = DbxRest(
        dbutils=dbutils,
        config=config,
        lfc_scheduler=scheduler
    )
    # dbx.cleanup_queue is automatically created
    # dbx.scheduler delegates to lfc_scheduler.scheduler
    
    # With custom configuration
    dbx = DbxRest(
        dbutils=dbutils,
        config=config,
        lfc_scheduler=scheduler,
        wait_sec=7200,
        target_catalog="dev"
    )
    
Note: Uses standard Python dataclass (not Pydantic) for maximum compatibility.
"""

# Standard imports
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
import base64
import functools
import importlib
import json
import queue
import re
import requests
import time

# Local imports
from .LfcScheduler import LfcScheduler

@dataclass
class DbxRest:
    """Databricks REST API manager with standard Python dataclass"""
    
    # Mandatory parameters
    dbutils: Any  # Required dbutils object
    config: Any  # Config dict or Pydantic model
    lfc_scheduler: LfcScheduler  # Required scheduler and cleanup queue manager
    
    # Configuration parameters
    wait_sec: int = 3600
    target_catalog: str = "main"
    cleanup_enabled: bool = True
    
    # Databricks client and derived properties
    w: Optional[WorkspaceClient] = None
    my_email: Optional[str] = None
    my_email_text: Optional[str] = None
    nine_char_id: Optional[str] = None
    source_catalog: Optional[str] = None
    source_schema: Optional[str] = None
    source_type: Optional[str] = None
    
    # Token and API configuration
    token_lifetime_seconds: Optional[int] = None
    api_token: Optional[str] = None
    workspace_url: Optional[str] = None
    
    # Pipeline and schema names
    gw_pipeline_name: Optional[str] = None
    ig_pipeline_name: Optional[str] = None
    target_schema: Optional[str] = None
    target_schema_path: Optional[str] = None
    
    # Date tags
    remove_after_yyyymmdd: Optional[str] = None
    remove_after_uc: Optional[str] = None
    
    # API URLs
    pipeline_api_url: Optional[str] = None
    uc_url: Optional[str] = None
    jobs_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    # Connection and secrets
    secrets_json: Optional[dict] = None
    connection_comment_json: Optional[dict] = None
    connection_spec: Optional[dict] = None
    
    # Cleanup queue
    cleanup_queue: Optional[queue.LifoQueue] = None
    
    # Scheduled job IDs tracking
    job_ids: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the Databricks REST API manager after dataclass creation"""
        self._setup_cleanup_queue()
        self.initialize()
    
    @property
    def scheduler(self):
        """Access scheduler from LfcScheduler instance"""
        return self.lfc_scheduler.scheduler
    
    def _setup_cleanup_queue(self):
        """Setup the cleanup queue"""
        if self.cleanup_queue is None:
            print("created cleanup_queue")
            self.cleanup_queue = queue.LifoQueue()
    
    def _get_config_value(self, key: str, default=None):
        """Safely get config value from dict or Pydantic model"""
        if hasattr(self.config, key):
            # Pydantic model or object with attributes
            return getattr(self.config, key, default)
        elif isinstance(self.config, dict):
            # Dictionary access
            return self.config.get(key, default)
        else:
            return default

    def initialize(self, re_calc=False):
        """Initialize all components"""
        # Core dependencies first
        self._setup_workspace_client()  # Must come before _setup_token (needs self.w)
        self._setup_user_info()         # Must come before _setup_nine_char_id (needs self.my_email_text)
        
        # Remaining functions without re_calc parameter
        self._setup_dates()
        self._setup_workspace_url()
        self._setup_api_urls()
        self._setup_cleanup_scheduler()

        # set connection info
        self.get_conn_cred()  # Calls: _setup_source_type, _setup_source_catalog, _setup_source_schema

        # Nine char ID setup - this will call its dependent functions internally
        self._setup_nine_char_id(re_calc=re_calc)  # Calls: _setup_token, _setup_names_and_paths
              
        self.print_config()

        return(self)
    
    def _setup_workspace_client(self):
        """Setup the Databricks workspace client"""
        if self.w is None:
            self.w = WorkspaceClient()
    
    def _setup_user_info(self):
        """Setup user information"""
        if self.my_email is None:
            self.my_email = self.w.current_user.me().user_name
            my_email_text_array = self.my_email.split("@")
            self.my_email_text = re.sub("[-.@]", "_", my_email_text_array[0])
    
    def _setup_nine_char_id(self,re_calc=False):
        """Setup nine character ID and dependent functions"""
        if re_calc or self.nine_char_id is None:
            try:
                # Use the passed-in dbutils object
                self.nine_char_id = self.dbutils.widgets.get("nine_char_id")
            except Exception as e:
                self.nine_char_id = ""
            
            if not self.nine_char_id:
                self.nine_char_id = hex(int(time.time_ns() / 100000000))[2:]

        # Call dependent functions that rely on nine_char_id
        self._setup_token(re_calc=re_calc)
        self._setup_headers()  # Must be after _setup_token since headers need api_token
        self._setup_names_and_paths(re_calc=re_calc)

        return(self)
    
    def _setup_token(self, re_calc=False):
        """Setup API token (called from _setup_nine_char_id)"""
        if re_calc or self.api_token is None:
            self.token_lifetime_seconds = self.wait_sec + 300  # token deleted 5 min after pipelines are deleted
            new_token = self.w.tokens.create(
                comment=f"lfcdddemo-{self.nine_char_id}-{self.source_type}", 
                lifetime_seconds=self.token_lifetime_seconds
            )
            self.api_token = new_token.token_value
    
    def _setup_names_and_paths(self, re_calc=False):
        """Setup pipeline and schema names (called from _setup_nine_char_id)"""
        if re_calc or self.gw_pipeline_name is None:
            self.gw_pipeline_name = f"{self.my_email_text}_{self.source_type}_{self.nine_char_id}_gw"
            self.ig_pipeline_name = f"{self.my_email_text}_{self.source_type}_{self.nine_char_id}_ig"
            self.target_schema = f"{self.my_email_text}_{self.source_type}_{self.nine_char_id}"
            self.target_schema_path = f"{self.target_catalog}.{self.target_schema}"
    
    def _setup_dates(self):
        """Setup date tags"""
        if self.remove_after_yyyymmdd is None:
            self.remove_after_yyyymmdd = datetime.today().strftime('%Y-%m-%d')
            self.remove_after_uc = datetime.today().strftime('%Y%m%d')
    
    def _setup_workspace_url(self):
        """Setup workspace URL"""
        if self.workspace_url is None:
            try:
                # Use the passed-in dbutils object
                self.workspace_url = "https://" + re.search(
                    r'\(([^)]+)\)', 
                    self.dbutils.notebook.entry_point.getDbutils().notebook().getContext().browserHostName().toString()
                ).group(1)
            except:
                # Fallback to workspace client config
                self.workspace_url = self.w.config.host
    
    def _setup_api_urls(self):
        """Setup API URLs"""
        if self.pipeline_api_url is None:
            self.pipeline_api_url = f"{self.workspace_url}/api/2.0/pipelines"
            self.uc_url = f"{self.workspace_url}/api/2.1/unity-catalog"
            self.jobs_url = f"{self.workspace_url}/api/2.1/jobs"
    
    def _setup_headers(self):
        """Setup API headers"""
        if self.headers is None:
            self.headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
    
    def _setup_cleanup_scheduler(self):
        """Setup the cleanup scheduler"""
        job_id=f"{self.config.source_connection_name}_{self.config.cdc_qbc}_execute_queued_functions"
        if job_id not in self.job_ids: 
            self.scheduler.add_job(
                self.execute_queued_functions, 
                'date', 
                run_date=datetime.now() + timedelta(seconds=self.wait_sec), 
                replace_existing=False, 
                id=job_id
            )
            self.job_ids[job_id] = job_id

    def _setup_source_catalog(self):
        """Setup source catalog (called from get_conn_cred)"""
        if self._get_config_value('source_catalog') is not None: 
            self.source_catalog = self._get_config_value('source_catalog')
            return


        if self.secrets_json is not None:
            self.source_catalog = self.secrets_json['catalog']
            return

    def _setup_source_schema(self):
        """Setup source schema (called from get_conn_cred)"""
        if self._get_config_value('source_schema') is not None: 
            self.source_schema = self._get_config_value('source_schema')
            return

        if self.secrets_json is not None:
            self.source_schema = self.secrets_json['schema']
            return

    def _setup_source_type(self):
        """Setup source type (called from get_conn_cred)"""
        if self.connection_spec is not None:
            # ConnectionInfo object has a connection_type attribute (enum)
            self.source_type = str(self.connection_spec.connection_type.value).casefold()

    def check_response(self, response, print_response:bool, method, url, data, headers):
        """Check and print API response"""
        if response.status_code == 200:
            if print_response: print("Response from API:\n{}".format(json.dumps(response.json(), indent=2, sort_keys=False)))
        else:
            print(f"Failed to retrieve data {method=}, {url=}, {data=} {headers=} error_code={response.status_code}, error_message={response.json().get('message', response.text)}")
    
    def dbx_rest_api(self, method: str, url: str, data: str = None, print_response=True):
        """Databricks API request function takes JSON only"""
        response = requests.request(method=method, url=url, headers=self.headers, data=data)
        self.check_response(response, print_response, method, url, data, self.headers )
        return response
    
    # Pipeline functions
    def create_pipeline(self, json_def: str, auto_delete=True):
        """Create a pipeline with optional auto-delete"""
        response = self.dbx_rest_api('post', self.pipeline_api_url, json_def)
        if auto_delete and response.status_code == 200:
            # the trailing comma is required to maintain tuple instead of string
            self.cleanup_queue.put((self.delete_pipeline, (response.json()["pipeline_id"],), {}))
        return response
    
    def edit_pipeline(self, id: str, json_def: str):
        """Edit an existing pipeline"""
        return self.dbx_rest_api('put', f"{self.pipeline_api_url}/{id}", json_def)
    
    def get_pipeline(self, id: str):
        """Get pipeline information"""
        return self.dbx_rest_api('get', f"{self.pipeline_api_url}/{id}")
    
    def delete_pipeline(self, id: str):
        """Delete a pipeline"""
        return self.dbx_rest_api('delete', f"{self.pipeline_api_url}/{id}")
    
    def start_pipeline(self, id: str, full_refresh: bool = False):
        """Start a pipeline with optional full refresh"""
        body = f"""
        {{
            "full_refresh": {str(full_refresh).lower()},
            "validate_only": false,
            "cause": "API_CALL"
        }}
        """
        return self.dbx_rest_api("post", f"{self.pipeline_api_url}/{id}/updates", body)
    
    def list_pipeline(self, filter: str):
        """List pipelines with optional filter"""
        body = "" if len(filter) == 0 else f"""{"filter": "{filter}"}"""
        response = requests.get(url=self.pipeline_api_url, headers=self.headers, data=body)
        self.check_response(response)
        return response
    
    # Schema functions
    def schema_create(self, target_catalog: str, target_schema: str, auto_delete=True, print_response=False):
        """Create a schema with optional auto-delete"""
        response = self.dbx_rest_api('post', f"{self.uc_url}/schemas", 
                                   json.dumps({"catalog_name": target_catalog, "name": target_schema}), 
                                   print_response=print_response)

        if auto_delete and response.status_code == 200:
            # the trailing comma is required to maintain tuple instead of string
            self.cleanup_queue.put((self.schema_delete, (f"{target_catalog}.{target_schema}",), {}))
        return response
    
    def schema_delete(self, catalog_schema: str, force=True):
        """Delete a schema"""
        data = {"force": force}
        return self.dbx_rest_api('delete', f"{self.uc_url}/schemas/{catalog_schema}", json.dumps(data))
    
    def schema_tags(self, catalog_schema: str, print_response=False):
        """Add tags to a schema"""
        return self.dbx_rest_api('post', f"{self.uc_url}/entity-tag-assignments",
            json.dumps({
                "entity_name": catalog_schema, 
                "entity_type": "schemas", 
                "tag_key": "RemoveAfter", 
                "tag_value": self.remove_after_yyyymmdd
            }), print_response=print_response)
    
    # Job functions
    def jobs_create(self, json_def: str, auto_delete=True):
        """Create a job with optional auto-delete"""
        response = self.dbx_rest_api('post', f"{self.jobs_url}/create", json_def)
        if auto_delete and response.status_code == 200:
            # the trailing comma is required to maintain tuple instead of string
            self.cleanup_queue.put((self.jobs_delete, (response.json()["job_id"],), {}))
        return response
    
    def jobs_delete(self, job_id: str):
        """Delete a job"""
        # Jobs delete uses POST method with job_id in the body
        delete_payload = json.dumps({"job_id": job_id})
        return self.dbx_rest_api('post', f"{self.jobs_url}/delete", delete_payload)
    
    def jobs_runnow(self, job_id: str):
        """Run a job now"""
        # Jobs run uses POST method with job_id in the body
        json_def = json.dumps({"job_id": job_id})
        return self.dbx_rest_api('post', f"{self.jobs_url}/run-now", json_def)
    
    # Cleanup functions
    def execute_queued_functions(self):
        """
        Retrieves and executes all functions currently in the queue.
        """
        if not self.cleanup_enabled:
            print("Skipping cleanup...")
            return

        print("Executing queued functions...")
        while not self.cleanup_queue.empty():
            func_args_kwargs = self.cleanup_queue.get()
            func = func_args_kwargs[0]
            try:
                args = func_args_kwargs[1]
            except Exception as e:
                args = []
            try:
                kwargs = func_args_kwargs[2]
            except Exception as e:
                kwargs = {}
            print(f"Running {args=}, {kwargs=}")
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Error executing function {func.__name__}: {e}")
            self.cleanup_queue.task_done()
        print("All queued functions executed.")
    
    def get_conn_cred(self):
        """Retrieve credentials from the secrets and setup dependent functions"""
        connection_name = self._get_config_value('source_connection_name')
        if connection_name is None or not connection_name: return

        connection_spec = self.w.connections.get(connection_name)
        connection_comment_json = json.loads(connection_spec.comment)
        secret_response = self.w.secrets.get_secret(
            scope=connection_comment_json['secrets']['scope'], 
            key=f"{connection_comment_json['secrets']['key']}_json"
        )
        
        # Decode base64 secret value (Databricks automatically base64 encodes secrets)
        import base64
        secret_value = base64.b64decode(secret_response.value).decode('utf-8')
        secrets_json = json.loads(secret_value)
        self.connection_name = connection_spec.name
        self.connection_spec = connection_spec
        self.connection_comment_json = connection_comment_json
        self.secrets_json = secrets_json
        
        # Call dependent functions that rely on connection credentials
        self._setup_source_type()
        self._setup_source_catalog()
        self._setup_source_schema()
    
    def disable_cleanup(self):
        """Disable cleanup functionality and update global variables"""
        self.cleanup_enabled = False
        return self
    
    def print_config(self):
        """Print current configuration"""
        print(f"my_email: {self.my_email}")
        print(f"my_email_text: {self.my_email_text}")
        print(f"nine_char_id: {self.nine_char_id}")
        print(f"gw_pipeline_name: {self.gw_pipeline_name}")
        print(f"ig_pipeline_name: {self.ig_pipeline_name}")
        print(f"target_schema_path: {self.target_schema_path}")
        print(f"workspace_url: {self.workspace_url}")

def main():
    """Main initialization function"""
    print("Initializing LFC Demo REST API Library...")
    
    # Note: dbutils must be passed in when creating DbxRest instance
    # In Databricks environment: dbx_rest = DbxRest(dbutils=dbutils)
    # For testing: dbx_rest = DbxRest(dbutils=mock_dbutils)
    print("⚠️  DbxRest now requires dbutils parameter:")
    print("   dbx_rest = DbxRest(dbutils=dbutils)")
    print("✅ LFC Demo REST API Library converted to standard Python dataclass!")
    print("🔧 Benefits:")
    print("   • No Pydantic dependencies")
    print("   • Maximum compatibility")
    print("   • Simple and clean structure")
    print("   • All functionality preserved")
    return None

if __name__ == "__main__":
    main()