import os
import re
import json
import threading
import sqlparse
import requests
import pickle
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
import io

# Enhanced imports with fallbacks
try:
    from huggingface_hub import HfApi, upload_file, login
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

try:
    import boto3
    import botocore
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

# Configuration
DATABASE = "./soketDB"
TABLE_EXT = ".json"
BACKUP_EXT = ".backup"
CONFIG_FILE = "database_config.json"

class StorageType(Enum):
    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"
    HUGGINGFACE = "huggingface"
    AWS_S3 = "aws_s3"
    DROPBOX = "dropbox"

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    GROUP_BY = "GROUP_BY"
    JOIN = "JOIN"
    UNKNOWN = "UNKNOWN"

lock = threading.RLock()

class AdvancedNLU:
    """Advanced Natural Language Understanding for database queries"""
    
    def __init__(self):
        self.synonyms = {
            'show': ['display', 'list', 'get', 'find', 'retrieve'],
            'count': ['total', 'number of', 'how many'],
            'sum': ['total', 'add up', 'summarize'],
            'average': ['avg', 'mean'],
            'where': ['filter', 'with', 'having'],
            'order by': ['sort by', 'arrange by'],
            'group by': ['categorize by', 'organize by'],
            'limit': ['top', 'first', 'last'],
            'users': ['people', 'persons', 'customers'],
            'jobs': ['positions', 'roles', 'employment'],
            'orders': ['purchases', 'transactions'],
            'salary': ['pay', 'income', 'wage'],
            'age': ['years old'],
            'city': ['location', 'place']
        }
        
        self.patterns = {
            'count_query': r'(count|how many|number of).*?(users|jobs|orders)',
            'sum_query': r'(sum|total).*?(salary|age|amount)',
            'avg_query': r'(average|avg|mean).*?(salary|age)',
            'select_query': r'(show|display|list|get).*?(name|age|city|salary)',
            'where_query': r'(where|filter).*?(age|city|salary).*?(>|<|=|greater|less)',
            'group_by_query': r'(group by|categorize).*?(city|department)',
            'join_query': r'(join|combine).*?(users.*jobs|jobs.*users)'
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        text = text.lower().strip()
        
        # Replace synonyms
        for standard, alternatives in self.synonyms.items():
            for alt in alternatives:
                if alt in text:
                    text = text.replace(alt, standard)
        
        return text
    
    def detect_query_type(self, text: str) -> QueryType:
        """Detect the type of query from natural language"""
        text = self.normalize_text(text)
        
        if any(word in text for word in ['count', 'how many', 'number of']):
            return QueryType.COUNT
        elif any(word in text for word in ['sum', 'total of', 'add up']):
            return QueryType.SUM
        elif any(word in text for word in ['average', 'avg', 'mean']):
            return QueryType.AVG
        elif any(word in text for word in ['show', 'display', 'list']):
            return QueryType.SELECT
        elif any(word in text for word in ['insert', 'add', 'create new']):
            return QueryType.INSERT
        elif any(word in text for word in ['update', 'change', 'modify']):
            return QueryType.UPDATE
        elif any(word in text for word in ['delete', 'remove']):
            return QueryType.DELETE
        elif any(word in text for word in ['group by', 'categorize']):
            return QueryType.GROUP_BY
        elif any(word in text for word in ['join', 'combine']):
            return QueryType.JOIN
        
        return QueryType.UNKNOWN
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from natural language query"""
        text = self.normalize_text(text)
        entities = {
            'table': 'users',
            'columns': ['*'],
            'conditions': [],
            'aggregations': [],
            'group_by': [],
            'order_by': [],
            'limit': None
        }
        
        # Detect table
        if any(word in text for word in ['users', 'people', 'customers']):
            entities['table'] = 'users'
        elif any(word in text for word in ['jobs', 'positions', 'roles']):
            entities['table'] = 'jobs'
        elif any(word in text for word in ['orders', 'purchases']):
            entities['table'] = 'orders'
        
        # Detect columns
        if 'name' in text and 'age' in text:
            entities['columns'] = ['name', 'age']
        elif 'name' in text and 'city' in text:
            entities['columns'] = ['name', 'city']
        elif 'name' in text and 'salary' in text:
            entities['columns'] = ['name', 'salary']
        elif 'name' in text:
            entities['columns'] = ['name']
        elif 'age' in text:
            entities['columns'] = ['age']
        elif 'city' in text:
            entities['columns'] = ['city']
        elif 'salary' in text:
            entities['columns'] = ['salary']
        
        # Detect conditions
        if 'age' in text:
            if 'age greater than' in text or 'age >' in text:
                match = re.search(r'age\s*(?:greater than|>)\s*(\d+)', text)
                if match:
                    entities['conditions'].append(f"age > {match.group(1)}")
            elif 'age less than' in text or 'age <' in text:
                match = re.search(r'age\s*(?:less than|<)\s*(\d+)', text)
                if match:
                    entities['conditions'].append(f"age < {match.group(1)}")
            elif 'age' in text:
                match = re.search(r'age\s*(?:is|=)\s*(\d+)', text)
                if match:
                    entities['conditions'].append(f"age = {match.group(1)}")
        
        if 'city' in text:
            for city in ['london', 'paris', 'berlin', 'new york']:
                if city in text:
                    entities['conditions'].append(f"city = '{city.title()}'")
        
        if 'salary' in text:
            if 'salary greater than' in text or 'salary >' in text:
                match = re.search(r'salary\s*(?:greater than|>)\s*(\d+)', text)
                if match:
                    entities['conditions'].append(f"salary > {match.group(1)}")
        
        # Detect aggregations
        if 'count' in text:
            entities['aggregations'].append('COUNT(*)')
        if 'sum' in text and 'salary' in text:
            entities['aggregations'].append('SUM(salary)')
        if 'average' in text and 'age' in text:
            entities['aggregations'].append('AVG(age)')
        
        # Detect group by
        if 'by city' in text:
            entities['group_by'] = ['city']
        elif 'by department' in text:
            entities['group_by'] = ['department']
        
        # Detect limit
        if 'top' in text or 'first' in text:
            match = re.search(r'(?:top|first)\s*(\d+)', text)
            if match:
                entities['limit'] = match.group(1)
        
        return entities

class BackupManager:
    """Manage multiple backup storage providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        
        # Initialize enabled providers
        if config.get('google_drive_enabled', False) and GOOGLE_DRIVE_AVAILABLE:
            self.providers['google_drive'] = GoogleDriveBackup(config)
        
        if config.get('huggingface_enabled', False) and HUGGINGFACE_AVAILABLE:
            self.providers['huggingface'] = HuggingFaceBackup(config)
        
        if config.get('aws_s3_enabled', False) and AWS_AVAILABLE:
            self.providers['aws_s3'] = AWSBackup(config)
        
        if config.get('dropbox_enabled', False) and DROPBOX_AVAILABLE:
            self.providers['dropbox'] = DropboxBackup(config)
    
    def backup_database(self, project_name: str, local_path: str) -> Dict[str, str]:
        """Backup database to all enabled providers"""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                result = provider.backup(project_name, local_path)
                results[name] = f"✅ {result}"
            except Exception as e:
                results[name] = f"❌ {str(e)}"
        
        return results
    
    def restore_database(self, project_name: str, local_path: str, provider: str = None) -> str:
        """Restore database from specified provider or auto-detect"""
        if provider and provider in self.providers:
            return self.providers[provider].restore(project_name, local_path)
        
        # Auto-detect from any available provider
        for name, provider_instance in self.providers.items():
            try:
                if provider_instance.exists(project_name):
                    return provider_instance.restore(project_name, local_path)
            except:
                continue
        
        return "❌ No backup found in any provider"

class GoogleDriveBackup:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        creds = None
        token_file = self.config.get('google_token_file', 'token.json')
        credentials_file = self.config.get('google_credentials_file', 'credentials.json')
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/drive.file'])
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, ['https://www.googleapis.com/auth/drive.file'])
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def backup(self, project_name: str, local_path: str) -> str:
        folder_id = self._get_or_create_folder(project_name)
        
        for root, dirs, files in os.walk(local_path):
            for file in files:
                if file.endswith(('.json', '.backup')):
                    file_path = os.path.join(root, file)
                    self._upload_file(file_path, folder_id)
        
        return f"Backup completed to Google Drive"
    
    def _get_or_create_folder(self, folder_name: str) -> str:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, spaces='drive').execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata).execute()
            return folder['id']
    
    def _upload_file(self, file_path: str, folder_id: str):
        file_name = os.path.basename(file_path)
        
        # Check if file exists
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query).execute()
        existing_files = results.get('files', [])
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(io.FileIO(file_path, 'rb'), mimetype='application/json')
        
        if existing_files:
            self.service.files().update(fileId=existing_files[0]['id'], media_body=media).execute()
        else:
            self.service.files().create(body=file_metadata, media_body=media).execute()

class HuggingFaceBackup:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = config.get('huggingface_token')
        self.repo_id = config.get('huggingface_repo_id')
        
        if self.token:
            login(token=self.token)
    
    def backup(self, project_name: str, local_path: str) -> str:
        api = HfApi()
        
        for root, dirs, files in os.walk(local_path):
            for file in files:
                if file.endswith(('.json', '.backup')):
                    file_path = os.path.join(root, file)
                    repo_path = f"{project_name}/{file}"
                    
                    try:
                        api.upload_file(
                            path_or_fileobj=file_path,
                            path_in_repo=repo_path,
                            repo_id=self.repo_id,
                            repo_type="dataset"
                        )
                    except Exception as e:
                        return f"Upload failed: {str(e)}"
        
        return "Backup completed to HuggingFace"

class AWSBackup:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bucket_name = config.get('aws_bucket_name')
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.get('aws_access_key'),
            aws_secret_access_key=config.get('aws_secret_key'),
            region_name=config.get('aws_region', 'us-east-1')
        )
    
    def backup(self, project_name: str, local_path: str) -> str:
        for root, dirs, files in os.walk(local_path):
            for file in files:
                if file.endswith(('.json', '.backup')):
                    file_path = os.path.join(root, file)
                    s3_key = f"{project_name}/{file}"
                    
                    try:
                        self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
                    except Exception as e:
                        return f"Upload failed: {str(e)}"
        
        return "Backup completed to AWS S3"

class DropboxBackup:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.access_token = config.get('dropbox_access_token')
        self.dbx = dropbox.Dropbox(self.access_token) if self.access_token else None
    
    def backup(self, project_name: str, local_path: str) -> str:
        if not self.dbx:
            return "Dropbox not configured"
        
        for root, dirs, files in os.walk(local_path):
            for file in files:
                if file.endswith(('.json', '.backup')):
                    file_path = os.path.join(root, file)
                    dropbox_path = f"/{project_name}/{file}"
                    
                    with open(file_path, 'rb') as f:
                        try:
                            self.dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                        except Exception as e:
                            return f"Upload failed: {str(e)}"
        
        return "Backup completed to Dropbox"

class QueryOptimizer:
    """Optimize queries for better performance"""
    
    def __init__(self):
        self.query_cache = {}
        self.cache_size = 100
    
    def get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def cache_result(self, query: str, result: Any):
        """Cache query result"""
        if len(self.query_cache) >= self.cache_size:
            # Remove oldest entry
            self.query_cache.pop(next(iter(self.query_cache)))
        
        cache_key = self.get_cache_key(query)
        self.query_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def get_cached_result(self, query: str) -> Optional[Any]:
        """Get cached result for query"""
        cache_key = self.get_cache_key(query)
        cached = self.query_cache.get(cache_key)
        
        if cached and time.time() - cached['timestamp'] < 300:  # 5 minutes cache
            return cached['result']
        
        return None

class AdvancedAItoSQL:
    """Advanced AI to SQL converter with better understanding"""
    
    def __init__(self):
        self.nlu = AdvancedNLU()
        self.optimizer = QueryOptimizer()
    
    def convert(self, prompt: str) -> str:
        """Convert natural language to SQL with advanced understanding"""
        
        # Check cache first
        cached_sql = self.optimizer.get_cached_result(prompt)
        if cached_sql:
            return cached_sql
        
        # Analyze query
        query_type = self.nlu.detect_query_type(prompt)
        entities = self.nlu.extract_entities(prompt)
        
        # Build SQL based on query type
        if query_type == QueryType.COUNT:
            sql = self._build_count_sql(entities)
        elif query_type == QueryType.SUM:
            sql = self._build_sum_sql(entities)
        elif query_type == QueryType.AVG:
            sql = self._build_avg_sql(entities)
        elif query_type == QueryType.GROUP_BY:
            sql = self._build_group_by_sql(entities)
        elif query_type == QueryType.SELECT:
            sql = self._build_select_sql(entities)
        else:
            sql = self._build_general_sql(entities)
        
        # Cache the result
        self.optimizer.cache_result(prompt, sql)
        
        return sql
    
    def _build_count_sql(self, entities: Dict) -> str:
        table = entities['table']
        conditions = " AND ".join(entities['conditions'])
        
        sql = f"SELECT COUNT(*) as count FROM {table}"
        if conditions:
            sql += f" WHERE {conditions}"
        
        return sql
    
    def _build_sum_sql(self, entities: Dict) -> str:
        table = entities['table']
        conditions = " AND ".join(entities['conditions'])
        
        # Determine what to sum
        if 'salary' in str(entities):
            column = 'salary'
        elif 'age' in str(entities):
            column = 'age'
        else:
            column = 'id'  # fallback
        
        sql = f"SELECT SUM({column}) as total FROM {table}"
        if conditions:
            sql += f" WHERE {conditions}"
        
        return sql
    
    def _build_avg_sql(self, entities: Dict) -> str:
        table = entities['table']
        conditions = " AND ".join(entities['conditions'])
        
        if 'age' in str(entities):
            column = 'age'
        elif 'salary' in str(entities):
            column = 'salary'
        else:
            column = 'id'
        
        sql = f"SELECT AVG({column}) as average FROM {table}"
        if conditions:
            sql += f" WHERE {conditions}"
        
        return sql
    
    def _build_group_by_sql(self, entities: Dict) -> str:
        table = entities['table']
        group_fields = entities['group_by']
        conditions = " AND ".join(entities['conditions'])
        
        if 'city' in group_fields:
            sql = f"SELECT city, COUNT(*) as count FROM {table}"
        elif 'department' in group_fields:
            sql = f"SELECT department, COUNT(*) as count FROM {table}"
        else:
            sql = f"SELECT {group_fields[0]}, COUNT(*) as count FROM {table}"
        
        if conditions:
            sql += f" WHERE {conditions}"
        
        sql += f" GROUP BY {group_fields[0]}"
        
        return sql
    
    def _build_select_sql(self, entities: Dict) -> str:
        table = entities['table']
        columns = ", ".join(entities['columns'])
        conditions = " AND ".join(entities['conditions'])
        limit = entities['limit']
        
        sql = f"SELECT {columns} FROM {table}"
        
        if conditions:
            sql += f" WHERE {conditions}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        return sql
    
    def _build_general_sql(self, entities: Dict) -> str:
        # Fallback to general SELECT
        return self._build_select_sql(entities)

class database:
    """Fully enhanced database with all features"""
    
    def __init__(self, project_name: str, config: Dict[str, Any] = None):
        self.project_name = project_name
        self.config = config or self._load_config()
        self.project_path = os.path.join(DATABASE, project_name)
        
        # Create project directory
        os.makedirs(self.project_path, exist_ok=True)
        
        # Initialize components
        self.ai_converter = AdvancedAItoSQL()
        self.backup_manager = BackupManager(self.config)
        self.query_optimizer = QueryOptimizer()
        self.lock = threading.RLock()
        
        # Initialize storage
        self._initialize_storage()
        
        # Create system tables
        self._create_system_tables()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'primary_storage': 'local',
            'backup_enabled': True,
            'auto_backup_hours': 24,
            'query_cache_enabled': True,
            'google_drive_enabled': False,
            'huggingface_enabled': False,
            'aws_s3_enabled': False,
            'dropbox_enabled': False
        }
        
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        
        return default_config
    
    def _initialize_storage(self):
        """Initialize primary storage"""
        storage_type = self.config.get('primary_storage', 'local')
        
        if storage_type == 'google_drive' and GOOGLE_DRIVE_AVAILABLE:
            self.storage = GoogleDriveBackup(self.config)
        elif storage_type == 'huggingface' and HUGGINGFACE_AVAILABLE:
            self.storage = HuggingFaceBackup(self.config)
        else:
            self.storage = None  # Use local storage
    
    def _create_system_tables(self):
        """Create system tables for metadata"""
        system_tables = {
            'system_queries': ['query_id', 'query_text', 'execution_time', 'timestamp'],
            'system_tables': ['table_name', 'column_count', 'row_count', 'created_at'],
            'system_backups': ['backup_id', 'provider', 'timestamp', 'size']
        }
        
        for table, columns in system_tables.items():
            if not self._table_exists(table):
                self.execute(f"CREATE TABLE {table} ({', '.join(columns)})")
    
    def _table_exists(self, table: str) -> bool:
        """Check if table exists"""
        return os.path.exists(os.path.join(self.project_path, f"{table}{TABLE_EXT}"))
    
    def execute(self, query: str) -> Any:
        """Execute SQL query with enhanced features"""
        
        # Check cache
        if self.config.get('query_cache_enabled', True):
            cached_result = self.query_optimizer.get_cached_result(query)
            if cached_result is not None:
                return cached_result
        
        with self.lock:
            try:
                # Parse and validate query
                parsed_query = self._parse_query(query)
                
                # Execute query
                result = self._execute_parsed_query(parsed_query)
                
                # Cache result
                if self.config.get('query_cache_enabled', True):
                    self.query_optimizer.cache_result(query, result)
                
                # Log query
                self._log_query(query, "success")
                
                return result
                
            except Exception as e:
                self._log_query(query, f"error: {str(e)}")
                return f"❌ Query execution failed: {str(e)}"
    
    def query(self, natural_language: str) -> Any:
        """Execute natural language query"""
        try:
            # Convert natural language to SQL
            sql = self.ai_converter.convert(natural_language)
            print(f"🤖 AI Translated: {sql}")
            
            # Execute the SQL
            return self.execute(sql)
            
        except Exception as e:
            return f"❌ AI translation failed: {e}"
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse SQL query into structured format"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Basic query type detection
        query_upper = query.upper()
        
        if query_upper.startswith('SELECT'):
            return {'type': 'SELECT', 'query': query}
        elif query_upper.startswith('INSERT'):
            return {'type': 'INSERT', 'query': query}
        elif query_upper.startswith('UPDATE'):
            return {'type': 'UPDATE', 'query': query}
        elif query_upper.startswith('DELETE'):
            return {'type': 'DELETE', 'query': query}
        elif query_upper.startswith('CREATE'):
            return {'type': 'CREATE', 'query': query}
        elif query_upper.startswith('DROP'):
            return {'type': 'DROP', 'query': query}
        else:
            return {'type': 'UNKNOWN', 'query': query}
    
    def _execute_parsed_query(self, parsed_query: Dict[str, Any]) -> Any:
        """Execute parsed query"""
        query_type = parsed_query['type']
        query = parsed_query['query']
        
        if query_type == 'SELECT':
            return self._execute_select(query)
        elif query_type == 'INSERT':
            return self._execute_insert(query)
        elif query_type == 'UPDATE':
            return self._execute_update(query)
        elif query_type == 'DELETE':
            return self._execute_delete(query)
        elif query_type == 'CREATE':
            return self._execute_create(query)
        elif query_type == 'DROP':
            return self._execute_drop(query)
        else:
            return "❌ Unsupported query type"
    
    def _execute_select(self, query: str) -> Any:
        """Execute SELECT query"""
        # Parse SELECT query (simplified implementation)
        # This would be expanded with full SQL parsing
        match = re.match(r"SELECT\s+(.+?)\s+FROM\s+(\w+)", query, re.IGNORECASE)
        if not match:
            return "❌ Invalid SELECT query"
        
        columns = match.group(1)
        table = match.group(2)
        
        # Read table data
        data = self._read_table(table)
        if data is None:
            return f"❌ Table '{table}' not found"
        
        # Simple column filtering (basic implementation)
        if columns != "*":
            selected_columns = [col.strip() for col in columns.split(",")]
            filtered_data = []
            for row in data:
                filtered_row = {col: row.get(col) for col in selected_columns if col in row}
                filtered_data.append(filtered_row)
            data = filtered_data
        
        return data
    
    def _execute_insert(self, query: str) -> str:
        """Execute INSERT query"""
        match = re.match(r"INSERT INTO\s+(\w+)\s+DATA\s*=\s*(.+)", query, re.IGNORECASE | re.DOTALL)
        if not match:
            return "❌ Invalid INSERT query"
        
        table = match.group(1)
        data_str = match.group(2)
        
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return "❌ Invalid data format"
        
        existing_data = self._read_table(table) or []
        
        if isinstance(data, dict):
            existing_data.append(data)
        elif isinstance(data, list):
            existing_data.extend(data)
        
        self._write_table(table, existing_data)
        return f"✅ Data inserted into '{table}'"
    
    def _execute_create(self, query: str) -> str:
        """Execute CREATE TABLE query"""
        match = re.match(r"CREATE TABLE\s+(\w+)\s*\((.+)\)", query, re.IGNORECASE)
        if not match:
            return "❌ Invalid CREATE TABLE query"
        
        table = match.group(1)
        columns = [col.strip().split()[0] for col in match.group(2).split(",")]
        
        if self._table_exists(table):
            return f"❌ Table '{table}' already exists"
        
        self._write_table(table, [])
        
        # Store metadata
        metadata = {"columns": columns, "created_at": datetime.now().isoformat()}
        self._write_metadata(table, metadata)
        
        # Update system tables
        self._update_system_tables()
        
        return f"✅ Table '{table}' created with columns: {columns}"
    
    # Implement other execution methods (_execute_update, _execute_delete, _execute_drop) similarly
    
    def _read_table(self, table: str) -> Optional[List[Dict]]:
        """Read table data"""
        file_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading table {table}: {e}")
            return None
    
    def _write_table(self, table: str, data: List[Dict]):
        """Write table data"""
        file_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _write_metadata(self, table: str, metadata: Dict):
        """Write table metadata"""
        meta_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}.meta")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _log_query(self, query: str, status: str):
        """Log query to system table"""
        query_log = {
            'query_id': hashlib.md5(f"{query}{time.time()}".encode()).hexdigest()[:8],
            'query_text': query[:500],  # Limit length
            'execution_time': time.time(),
            'timestamp': datetime.now().isoformat(),
            'status': status
        }
        
        # Append to system queries
        system_queries = self._read_table('system_queries') or []
        system_queries.append(query_log)
        self._write_table('system_queries', system_queries)
    
    def _update_system_tables(self):
        """Update system tables with current database state"""
        tables = self.list_tables()
        
        system_tables_data = []
        for table in tables:
            if table.startswith('system_'):
                continue
            
            data = self._read_table(table) or []
            metadata = self._read_metadata(table) or {}
            
            system_tables_data.append({
                'table_name': table,
                'column_count': len(metadata.get('columns', [])),
                'row_count': len(data),
                'created_at': metadata.get('created_at', datetime.now().isoformat())
            })
        
        self._write_table('system_tables', system_tables_data)
    
    def _read_metadata(self, table: str) -> Optional[Dict]:
        """Read table metadata"""
        meta_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}.meta")
        if not os.path.exists(meta_path):
            return None
        
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def backup(self) -> Dict[str, str]:
        """Backup database to all enabled providers"""
        return self.backup_manager.backup_database(self.project_name, self.project_path)
    
    def restore(self, provider: str = None) -> str:
        """Restore database from backup"""
        return self.backup_manager.restore_database(self.project_name, self.project_path, provider)
    
    def list_tables(self) -> List[str]:
        """List all tables in database"""
        tables = []
        if os.path.exists(self.project_path):
            for file in os.listdir(self.project_path):
                if file.endswith(TABLE_EXT) and not file.endswith('.meta'):
                    tables.append(file[:-len(TABLE_EXT)])
        return tables
    
    def table_info(self, table: str) -> Optional[Dict]:
        """Get information about a table"""
        data = self._read_table(table)
        metadata = self._read_metadata(table)
        
        if data is None or metadata is None:
            return None
        
        return {
            'table_name': table,
            'columns': metadata.get('columns', []),
            'row_count': len(data),
            'created_at': metadata.get('created_at'),
            'storage': self.config.get('primary_storage', 'local')
        }
    
    def query_history(self, limit: int = 10) -> List[Dict]:
        """Get query history"""
        queries = self._read_table('system_queries') or []
        return queries[-limit:]
    
    def performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        tables = self.list_tables()
        total_rows = 0
        total_size = 0
        
        for table in tables:
            if table.startswith('system_'):
                continue
            
            data = self._read_table(table) or []
            total_rows += len(data)
            
            table_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
            if os.path.exists(table_path):
                total_size += os.path.getsize(table_path)
        
        return {
            'total_tables': len([t for t in tables if not t.startswith('system_')]),
            'total_rows': total_rows,
            'total_size_bytes': total_size,
            'cache_hits': len(self.query_optimizer.query_cache),
            'backup_providers': list(self.backup_manager.providers.keys())
        }