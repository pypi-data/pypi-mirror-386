import os
import json
from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any, Tuple, Union
import pandas as pd
import numpy as np

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Text, DateTime, LargeBinary, ForeignKey, Boolean, func
    from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.sql import select, insert, update, delete
    from sqlalchemy.dialects import sqlite, postgresql
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False
    print("SQLAlchemy not available - this module requires SQLAlchemy")
    raise

try:
    import chromadb
except ModuleNotFoundError:
    print("chromadb not installed")
except OSError as e:
    print('os error importing chromadb:', e)
except NameError as e:
    print('name error importing chromadb:', e)
    chromadb = None


import logging 

def flush_messages(n: int, messages: list) -> dict:
    if n <= 0:
        return {
            "messages": messages,
            "output": "Error: 'n' must be a positive integer.",
        }

    removed_count = min(n, len(messages))
    del messages[-removed_count:]

    return {
        "messages": messages,
        "output": f"Flushed {removed_count} message(s). Context count is now {len(messages)} messages.",
    }

def create_engine_from_path(db_path: str) -> Engine:
    """Create SQLAlchemy engine from database path, detecting type"""
    if db_path.startswith('postgresql://') or db_path.startswith('postgres://'):
        return create_engine(db_path)
    else:
        
        if db_path.startswith('~/'):
            db_path = os.path.expanduser(db_path)
        return create_engine(f'sqlite:///{db_path}')

def get_db_connection(db_path: str = "~/npcsh_history.db") -> Engine:
    """Get SQLAlchemy engine"""
    return create_engine_from_path(db_path)

def fetch_messages_for_conversation(engine: Engine, conversation_id: str):
    query = text("""
        SELECT role, content, timestamp
        FROM conversation_history
        WHERE conversation_id = :conversation_id
        ORDER BY timestamp ASC
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"conversation_id": conversation_id})
        return [
            {
                "role": row.role,
                "content": row.content,
                "timestamp": row.timestamp,
            }
            for row in result
        ]

def deep_to_dict(obj):
    """
    Recursively convert objects that have a 'to_dict' method to dictionaries,
    otherwise drop them from the output.
    """
    if isinstance(obj, dict):
        return {key: deep_to_dict(val) for key, val in obj.items()}

    if isinstance(obj, list):
        return [deep_to_dict(item) for item in obj]

    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict", None)):
        return deep_to_dict(obj.to_dict())

    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj

    return None

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return deep_to_dict(obj)
        except TypeError:
            return super().default(obj)

def show_history(command_history, args):
    if args:
        search_results = command_history.search_commands(args[0])
        if search_results:
            return "\n".join(
                [f"{item['id']}. [{item['timestamp']}] {item['command']}" for item in search_results]
            )
        else:
            return f"No commands found matching '{args[0]}'"
    else:
        all_history = command_history.get_all_commands()
        return "\n".join([f"{item['id']}. [{item['timestamp']}] {item['command']}" for item in all_history])

def query_history_for_llm(command_history, query):
    results = command_history.search_commands(query)
    formatted_results = [
        f"Command: {r['command']}\nOutput: {r['output']}\nLocation: {r['location']}" for r in results
    ]
    return "\n\n".join(formatted_results)

def setup_chroma_db(collection, description='', db_path: str = ''):
    """Initialize Chroma vector database without a default embedding function"""
    if db_path == '':
        db_path = os.path.expanduser('~/npcsh_chroma_db')
        
    try:
        client = chromadb.PersistentClient(path=db_path)

        try:
            collection = client.get_collection(collection)
            print("Connected to existing facts collection")
        except ValueError:
            collection = client.create_collection(
                name=collection,
                metadata={"description": description},
            )
            print("Created new facts collection")

        return client, collection
    except Exception as e:
        print(f"Error setting up Chroma DB: {e}")
        raise

def init_kg_schema(engine: Engine):
    """Creates the multi-scoped, path-aware KG tables using SQLAlchemy"""
    
    
    metadata = MetaData()
    
    kg_facts = Table('kg_facts', metadata,
        Column('statement', Text, nullable=False),
        Column('team_name', String(255), nullable=False),
        Column('npc_name', String(255), nullable=False),
        Column('directory_path', Text, nullable=False),
        Column('source_text', Text),
        Column('type', String(100)),
        Column('generation', Integer),
        Column('origin', String(100)),
        
        schema=None
    )
    
    kg_concepts = Table('kg_concepts', metadata,
        Column('name', Text, nullable=False),
        Column('team_name', String(255), nullable=False),
        Column('npc_name', String(255), nullable=False),
        Column('directory_path', Text, nullable=False),
        Column('generation', Integer),
        Column('origin', String(100)),
        schema=None
    )
    
    kg_links = Table('kg_links', metadata,
        Column('source', Text, nullable=False),
        Column('target', Text, nullable=False),
        Column('team_name', String(255), nullable=False),
        Column('npc_name', String(255), nullable=False),
        Column('directory_path', Text, nullable=False),
        Column('type', String(100), nullable=False),
        schema=None
    )
    
    kg_metadata = Table('kg_metadata', metadata,
        Column('key', String(255), nullable=False),
        Column('team_name', String(255), nullable=False),
        Column('npc_name', String(255), nullable=False),
        Column('directory_path', Text, nullable=False),
        Column('value', Text),
        schema=None
    )
    
    
    metadata.create_all(engine, checkfirst=True)

def load_kg_from_db(engine: Engine, team_name: str, npc_name: str, directory_path: str) -> Dict[str, Any]:
    """Loads the KG for a specific scope (team, npc, path) from database."""
    kg = {
        "generation": 0,
        "facts": [],
        "concepts": [],
        "concept_links": [],
        "fact_to_concept_links": {},
        "fact_to_fact_links": []
    }
    
    with engine.connect() as conn:
        try:
            
            result = conn.execute(text("""
                SELECT value FROM kg_metadata 
                WHERE team_name = :team AND npc_name = :npc AND directory_path = :path AND key = 'generation'
            """), {"team": team_name, "npc": npc_name, "path": directory_path})
            
            row = result.fetchone()
            if row:
                kg['generation'] = int(row.value)

            
            result = conn.execute(text("""
                SELECT statement, source_text, type, generation, origin FROM kg_facts 
                WHERE team_name = :team AND npc_name = :npc AND directory_path = :path
            """), {"team": team_name, "npc": npc_name, "path": directory_path})
            
            kg['facts'] = [
                {
                    "statement": row.statement,
                    "source_text": row.source_text,
                    "type": row.type,
                    "generation": row.generation,
                    "origin": row.origin
                }
                for row in result
            ]

            
            result = conn.execute(text("""
                SELECT name, generation, origin FROM kg_concepts 
                WHERE team_name = :team AND npc_name = :npc AND directory_path = :path
            """), {"team": team_name, "npc": npc_name, "path": directory_path})
            
            kg['concepts'] = [
                {"name": row.name, "generation": row.generation, "origin": row.origin}
                for row in result
            ]

            
            links = {}
            result = conn.execute(text("""
                SELECT source, target, type FROM kg_links 
                WHERE team_name = :team AND npc_name = :npc AND directory_path = :path
            """), {"team": team_name, "npc": npc_name, "path": directory_path})
            
            for row in result:
                if row.type == 'fact_to_concept':
                    if row.source not in links:
                        links[row.source] = []
                    links[row.source].append(row.target)
                elif row.type == 'concept_to_concept':
                    kg['concept_links'].append((row.source, row.target))
                elif row.type == 'fact_to_fact':
                    kg['fact_to_fact_links'].append((row.source, row.target))
            
            kg['fact_to_concept_links'] = links
            
        except SQLAlchemyError:
            
            init_kg_schema(engine)
    
    return kg

def save_kg_to_db(engine: Engine, kg_data: Dict[str, Any], team_name: str, npc_name: str, directory_path: str):
    """Saves a knowledge graph dictionary to the database, ignoring duplicates."""
    try:
        with engine.begin() as conn:
            
            facts_to_save = [
                {
                    "statement": fact['statement'],
                    "team_name": team_name,
                    "npc_name": npc_name,
                    "directory_path": directory_path,
                    "generation": fact.get('generation', 0),
                    "origin": fact.get('origin', 'organic')
                }
                for fact in kg_data.get("facts", [])
            ]
            
            if facts_to_save:
                
                if 'sqlite' in str(engine.url):
                    stmt = text("""
                        INSERT OR IGNORE INTO kg_facts 
                        (statement, team_name, npc_name, directory_path, generation, origin)
                        VALUES (:statement, :team_name, :npc_name, :directory_path, :generation, :origin)
                    """)
                else:
                    stmt = text("""
                        INSERT INTO kg_facts 
                        (statement, team_name, npc_name, directory_path, generation, origin)
                        VALUES (:statement, :team_name, :npc_name, :directory_path, :generation, :origin)
                        ON CONFLICT (statement, team_name, npc_name, directory_path) DO NOTHING
                    """)
                
                for fact in facts_to_save:
                    conn.execute(stmt, fact)

            
            concepts_to_save = [
                {
                    "name": concept['name'],
                    "team_name": team_name,
                    "npc_name": npc_name,
                    "directory_path": directory_path,
                    "generation": concept.get('generation', 0),
                    "origin": concept.get('origin', 'organic')
                }
                for concept in kg_data.get("concepts", [])
            ]
            
            if concepts_to_save:
                if 'sqlite' in str(engine.url):
                    stmt = text("""
                        INSERT OR IGNORE INTO kg_concepts 
                        (name, team_name, npc_name, directory_path, generation, origin)
                        VALUES (:name, :team_name, :npc_name, :directory_path, :generation, :origin)
                    """)
                else:
                    stmt = text("""
                        INSERT INTO kg_concepts 
                        (name, team_name, npc_name, directory_path, generation, origin)
                        VALUES (:name, :team_name, :npc_name, :directory_path, :generation, :origin)
                        ON CONFLICT (name, team_name, npc_name, directory_path) DO NOTHING
                    """)
                
                for concept in concepts_to_save:
                    conn.execute(stmt, concept)

            
            if 'sqlite' in str(engine.url):
                stmt = text("""
                    INSERT OR REPLACE INTO kg_metadata (key, value, team_name, npc_name, directory_path)
                    VALUES ('generation', :generation, :team_name, :npc_name, :directory_path)
                """)
            else:
                stmt = text("""
                    INSERT INTO kg_metadata (key, value, team_name, npc_name, directory_path)
                    VALUES ('generation', :generation, :team_name, :npc_name, :directory_path)
                    ON CONFLICT (key, team_name, npc_name, directory_path) 
                    DO UPDATE SET value = EXCLUDED.value
                """)
            
            conn.execute(stmt, {
                "generation": str(kg_data.get('generation', 0)),
                "team_name": team_name,
                "npc_name": npc_name,
                "directory_path": directory_path
            })

            
            conn.execute(text("""
                DELETE FROM kg_links 
                WHERE team_name = :team_name AND npc_name = :npc_name AND directory_path = :directory_path
            """), {"team_name": team_name, "npc_name": npc_name, "directory_path": directory_path})
            
            
            for fact, concepts in kg_data.get("fact_to_concept_links", {}).items():
                for concept in concepts:
                    conn.execute(text("""
                        INSERT INTO kg_links (source, target, type, team_name, npc_name, directory_path)
                        VALUES (:source, :target, 'fact_to_concept', :team_name, :npc_name, :directory_path)
                    """), {
                        "source": fact, "target": concept,
                        "team_name": team_name, "npc_name": npc_name, "directory_path": directory_path
                    })
            
            for c1, c2 in kg_data.get("concept_links", []):
                conn.execute(text("""
                    INSERT INTO kg_links (source, target, type, team_name, npc_name, directory_path)
                    VALUES (:source, :target, 'concept_to_concept', :team_name, :npc_name, :directory_path)
                """), {
                    "source": c1, "target": c2,
                    "team_name": team_name, "npc_name": npc_name, "directory_path": directory_path
                })
            
            for f1, f2 in kg_data.get("fact_to_fact_links", []):
                conn.execute(text("""
                    INSERT INTO kg_links (source, target, type, team_name, npc_name, directory_path)
                    VALUES (:source, :target, 'fact_to_fact', :team_name, :npc_name, :directory_path)
                """), {
                    "source": f1, "target": f2,
                    "team_name": team_name, "npc_name": npc_name, "directory_path": directory_path
                })
            
    except Exception as e:
        print(f"Failed to save KG for scope '({team_name}, {npc_name}, {directory_path})': {e}")

def generate_message_id() -> str:
    return str(uuid.uuid4())

class CommandHistory:
    def __init__(self, db: Union[str, Engine] = "~/npcsh_history.db"):
        
        if isinstance(db, str):
            self.engine = create_engine_from_path(db)
            self.db_path = db
        elif isinstance(db, Engine):
            self.engine = db
            self.db_path = str(db.url)
        else:
            raise TypeError(f"Unsupported type for CommandHistory db parameter: {type(db)}")

        self._initialize_schema()

    def _initialize_schema(self):
        """Creates all necessary tables."""
        metadata = MetaData()
        
        
        Table('command_history', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('timestamp', String(50)),
            Column('command', Text),
            Column('subcommands', Text),
            Column('output', Text),
            Column('location', Text)
        )
        
        
        Table('conversation_history', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('message_id', String(50), unique=True, nullable=False),
            Column('timestamp', String(50)),
            Column('role', String(20)),
            Column('content', Text),
            Column('conversation_id', String(100)),
            Column('directory_path', Text),
            Column('model', String(100)),
            Column('provider', String(100)),
            Column('npc', String(100)),
            Column('team', String(100))
        )
        
        
        Table('message_attachments', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('message_id', String(50), ForeignKey('conversation_history.message_id', ondelete='CASCADE'), nullable=False),
            Column('attachment_name', String(255)),
            Column('attachment_type', String(100)),
            Column('attachment_data', LargeBinary),
            Column('attachment_size', Integer),
            Column('upload_timestamp', String(50)),
            Column('file_path', Text) 
        )
        
        
        Table('jinx_execution_log', metadata,
            Column('execution_id', Integer, primary_key=True, autoincrement=True),
            Column('triggering_message_id', String(50), ForeignKey('conversation_history.message_id', ondelete='CASCADE'), nullable=False),
            Column('response_message_id', String(50), ForeignKey('conversation_history.message_id', ondelete='SET NULL')),
            Column('conversation_id', String(100), nullable=False),
            Column('timestamp', String(50), nullable=False),
            Column('npc_name', String(100)),
            Column('team_name', String(100)),
            Column('jinx_name', String(100), nullable=False),
            Column('jinx_inputs', Text),
            Column('jinx_output', Text),
            Column('status', String(50), nullable=False),
            Column('error_message', Text),
            Column('duration_ms', Integer)
        )
        
        Table('memory_lifecycle', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('message_id', String(50), nullable=False),
            Column('conversation_id', String(100), nullable=False),
            Column('npc', String(100), nullable=False),
            Column('team', String(100), nullable=False),
            Column('directory_path', Text, nullable=False),
            Column('timestamp', String(50), nullable=False),
            Column('initial_memory', Text, nullable=False),
            Column('final_memory', Text),
            Column('status', String(50), nullable=False),
            Column('model', String(100)),
            Column('provider', String(100)),
            Column('created_at', DateTime, default=func.now())
        )
                
        
        metadata.create_all(self.engine, checkfirst=True)
        
        
        with self.engine.begin() as conn:
            
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_jinx_log_trigger_msg ON jinx_execution_log (triggering_message_id)",
                "CREATE INDEX IF NOT EXISTS idx_jinx_log_convo_id ON jinx_execution_log (conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_jinx_log_jinx_name ON jinx_execution_log (jinx_name)",
                "CREATE INDEX IF NOT EXISTS idx_jinx_log_timestamp ON jinx_execution_log (timestamp)"
            ]
            
            for idx_query in index_queries:
                try:
                    conn.execute(text(idx_query))
                except SQLAlchemyError:
                    
                    pass
        
        
        init_kg_schema(self.engine)

    def _execute_returning_id(self, stmt: str, params: Dict = None) -> Optional[int]:
        """Execute INSERT and return the generated ID"""
        with self.engine.begin() as conn:
            result = conn.execute(text(stmt), params or {})
            return result.lastrowid if hasattr(result, 'lastrowid') else None

    def _fetch_one(self, stmt: str, params: Dict = None) -> Optional[Dict]:
        """Fetch a single row"""
        with self.engine.connect() as conn:
            result = conn.execute(text(stmt), params or {})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def _fetch_all(self, stmt: str, params: Dict = None) -> List[Dict]:
        """Fetch all rows"""
        with self.engine.connect() as conn:
            result = conn.execute(text(stmt), params or {})
            return [dict(row._mapping) for row in result]

    def add_command(self, command, subcommands, output, location):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stmt = """
            INSERT INTO command_history (timestamp, command, subcommands, output, location)
            VALUES (:timestamp, :command, :subcommands, :output, :location)
        """
        params = {
            "timestamp": timestamp,
            "command": command,
            "subcommands": str(subcommands),
            "output": str(output),
            "location": location
        }
        
        with self.engine.begin() as conn:
            conn.execute(text(stmt), params)


    def add_conversation(
        self, 
        message_id,
        timestamp,
        role, 
        content, 
        conversation_id, 
        directory_path,
        model=None, 
        provider=None, 
        npc=None, 
        team=None,
        attachments=None,
    ):
        if isinstance(content, (dict, list)):
            content = json.dumps(content, cls=CustomJSONEncoder)

        stmt = """
            INSERT INTO conversation_history
            (message_id, timestamp, role, content, conversation_id, directory_path, model, provider, npc, team)
            VALUES (:message_id, :timestamp, :role, :content, :conversation_id, :directory_path, :model, :provider, :npc, :team)
        """
        params = {
            "message_id": message_id, "timestamp": timestamp, "role": role, "content": content,
            "conversation_id": conversation_id, "directory_path": directory_path, "model": model,
            "provider": provider, "npc": npc, "team": team
        }
        with self.engine.begin() as conn:
            conn.execute(text(stmt), params)

        if attachments:
            for attachment in attachments:
                self.add_attachment(
                    message_id=message_id,
                    name=attachment.get("name"),
                    attachment_type=attachment.get("type"),
                    data=attachment.get("data"),
                    size=attachment.get("size"),
                    file_path=attachment.get("path") 
                )

        return message_id

    def add_memory_to_database(self, message_id: str, conversation_id: str, npc: str, team: str, 
                            directory_path: str, initial_memory: str, status: str, 
                            model: str = None, provider: str = None, final_memory: str = None):
        """Store a memory entry in the database"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stmt = """
            INSERT INTO memory_lifecycle 
            (message_id, conversation_id, npc, team, directory_path, timestamp, 
            initial_memory, final_memory, status, model, provider)
            VALUES (:message_id, :conversation_id, :npc, :team, :directory_path, 
                    :timestamp, :initial_memory, :final_memory, :status, :model, :provider)
        """
        
        params = {
            "message_id": message_id, "conversation_id": conversation_id,
            "npc": npc, "team": team, "directory_path": directory_path,
            "timestamp": timestamp, "initial_memory": initial_memory,
            "final_memory": final_memory, "status": status,
            "model": model, "provider": provider
        }
        
        return self._execute_returning_id(stmt, params)
    def get_memories_for_scope(
        self,
        npc: str,
        team: str,
        directory_path: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        
        query = """
            SELECT id, initial_memory, final_memory, 
                status, timestamp, created_at
            FROM memory_lifecycle
            WHERE npc = :npc AND team = :team AND directory_path = :path
        """
        params = {"npc": npc, "team": team, "path": directory_path}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        
        query += " ORDER BY created_at DESC"
        data =self._fetch_all(query, params)
        return  data

    def search_memory(self, query: str, npc: str = None, team: str = None, 
                    directory_path: str = None, status_filter: str = None, limit: int = 10):
        """Search memories with hierarchical scope"""
        conditions = ["LOWER(initial_memory) LIKE LOWER(:query) OR LOWER(final_memory) LIKE LOWER(:query)"]
        params = {"query": f"%{query}%"}
        
        if status_filter:
            conditions.append("status = :status")
            params["status"] = status_filter
        
        
        order_parts = []
        if npc:
            order_parts.append(f"CASE WHEN npc = '{npc}' THEN 1 ELSE 2 END")
        if team:
            order_parts.append(f"CASE WHEN team = '{team}' THEN 1 ELSE 2 END")
        if directory_path:
            order_parts.append(f"CASE WHEN directory_path = '{directory_path}' THEN 1 ELSE 2 END")
        
        order_clause = ", ".join(order_parts) + ", created_at DESC" if order_parts else "created_at DESC"
        
        stmt = f"""
            SELECT * FROM memory_lifecycle 
            WHERE {' AND '.join(conditions)}
            ORDER BY {order_clause}
            LIMIT :limit
        """
        params["limit"] = limit
        
        return self._fetch_all(stmt, params)

    def get_memory_examples_for_context(self, npc: str, team: str, directory_path: str,
                                    n_approved: int = 10, n_rejected: int = 10):
        """Get recent approved and rejected memories for learning context"""
        
        approved_stmt = """
            SELECT initial_memory, final_memory, status FROM memory_lifecycle
            WHERE status IN ('human-approved', 'model-approved')
            ORDER BY 
                CASE WHEN npc = :npc AND team = :team AND directory_path = :path THEN 1
                    WHEN npc = :npc AND team = :team THEN 2  
                    WHEN team = :team THEN 3
                    ELSE 4 END,
                created_at DESC
            LIMIT :n_approved
        """
        
        rejected_stmt = """
            SELECT initial_memory, status FROM memory_lifecycle
            WHERE status IN ('human-rejected', 'model-rejected')
            ORDER BY 
                CASE WHEN npc = :npc AND team = :team AND directory_path = :path THEN 1
                    WHEN npc = :npc AND team = :team THEN 2
                    WHEN team = :team THEN 3  
                    ELSE 4 END,
                created_at DESC
            LIMIT :n_rejected
        """
        
        params = {"npc": npc, "team": team, "path": directory_path, 
                "n_approved": n_approved, "n_rejected": n_rejected}
        
        approved = self._fetch_all(approved_stmt, params)
        rejected = self._fetch_all(rejected_stmt, params)
        
        return {"approved": approved, "rejected": rejected}

    def get_pending_memories(self, limit: int = 50):
        """Get memories pending human approval"""
        stmt = """
            SELECT * FROM memory_lifecycle 
            WHERE status = 'pending_approval'
            ORDER BY created_at ASC
            LIMIT :limit
        """
        return self._fetch_all(stmt, {"limit": limit})

    def update_memory_status(self, memory_id: int, new_status: str, final_memory: str = None):
        """Update memory status and optionally final_memory"""
        stmt = """
            UPDATE memory_lifecycle 
            SET status = :status, final_memory = :final_memory
            WHERE id = :memory_id
        """
        params = {"status": new_status, "final_memory": final_memory, "memory_id": memory_id}
        
        with self.engine.begin() as conn:
            conn.execute(text(stmt), params)
            
    def add_attachment(self, message_id, name, attachment_type, data, size, file_path=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stmt = """
            INSERT INTO message_attachments 
            (message_id, attachment_name, attachment_type, attachment_data, attachment_size, upload_timestamp, file_path)
            VALUES (:message_id, :name, :type, :data, :size, :timestamp, :file_path)
        """
        params = {
            "message_id": message_id,
            "name": name,
            "type": attachment_type,
            "data": data,
            "size": size,
            "timestamp": timestamp,
            "file_path": file_path
        }
        with self.engine.begin() as conn:
            conn.execute(text(stmt), params)

    def save_jinx_execution(
        self, 
        triggering_message_id: str, 
        conversation_id: str, 
        npc_name: Optional[str],
        jinx_name: str, 
        jinx_inputs: Dict, 
        jinx_output: Any, status: str,
        team_name: Optional[str] = None, 
        error_message: Optional[str] = None,
        response_message_id: Optional[str] = None, 
        duration_ms: Optional[int] = None
    ):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            inputs_json = json.dumps(jinx_inputs, cls=CustomJSONEncoder)
        except TypeError:
            inputs_json = json.dumps(str(jinx_inputs))
        
        try:
            if isinstance(jinx_output, (str, int, float, bool, list, dict, type(None))):
                outputs_json = json.dumps(jinx_output, cls=CustomJSONEncoder)
            else:
                outputs_json = json.dumps(str(jinx_output))
        except TypeError:
            outputs_json = json.dumps(f"Non-serializable output: {type(jinx_output)}")

        stmt = """
            INSERT INTO jinx_execution_log
            (triggering_message_id, conversation_id, timestamp, npc_name, team_name,
             jinx_name, jinx_inputs, jinx_output, status, error_message, response_message_id, duration_ms)
             VALUES (:triggering_message_id, :conversation_id, :timestamp, :npc_name, :team_name,
                     :jinx_name, :jinx_inputs, :jinx_output, :status, :error_message, :response_message_id, :duration_ms)
        """
        params = {
            "triggering_message_id": triggering_message_id,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "npc_name": npc_name,
            "team_name": team_name,
            "jinx_name": jinx_name,
            "jinx_inputs": inputs_json,
            "jinx_output": outputs_json,
            "status": status,
            "error_message": error_message,
            "response_message_id": response_message_id,
            "duration_ms": duration_ms
        }
        
        return self._execute_returning_id(stmt, params)

    def get_full_message_content(self, message_id):
        stmt = "SELECT content FROM conversation_history WHERE message_id = :message_id ORDER BY timestamp ASC"
        rows = self._fetch_all(stmt, {"message_id": message_id})
        return "".join(row['content'] for row in rows)

    def update_message_content(self, message_id, full_content):
        stmt = "UPDATE conversation_history SET content = :content WHERE message_id = :message_id"
        with self.engine.begin() as conn:
            conn.execute(text(stmt), {"content": full_content, "message_id": message_id})

    def get_message_attachments(self, message_id) -> List[Dict]:
        stmt = """
            SELECT 
                id, 
                message_id, 
                attachment_name, 
                attachment_type, 
                attachment_size, 
                upload_timestamp
            FROM message_attachments WHERE message_id = :message_id
        """
        return self._fetch_all(stmt, {"message_id": message_id})

    def get_attachment_data(self, attachment_id) -> Optional[Tuple[bytes, str, str]]:
        stmt = "SELECT attachment_data, attachment_name, attachment_type FROM message_attachments WHERE id = :attachment_id"
        row = self._fetch_one(stmt, {"attachment_id": attachment_id})
        if row:
            return row['attachment_data'], row['attachment_name'], row['attachment_type']
        return None, None, None

    def delete_attachment(self, attachment_id) -> bool:
        stmt = "DELETE FROM message_attachments WHERE id = :attachment_id"
        try:
            with self.engine.begin() as conn:
                conn.execute(text(stmt), {"attachment_id": attachment_id})
            return True
        except Exception as e:
            print(f"Error deleting attachment {attachment_id}: {e}")
            return False

    def get_last_command(self) -> Optional[Dict]:
        stmt = "SELECT * FROM command_history ORDER BY id DESC LIMIT 1"
        return self._fetch_one(stmt)

    def get_most_recent_conversation_id(self) -> Optional[Dict]:
        stmt = "SELECT conversation_id FROM conversation_history ORDER BY id DESC LIMIT 1"
        return self._fetch_one(stmt)

    def get_last_conversation(self, conversation_id) -> Optional[Dict]:
        stmt = """
            SELECT * FROM conversation_history 
            WHERE conversation_id = :conversation_id and role = 'user'
            ORDER BY id DESC LIMIT 1
        """
        return self._fetch_one(stmt, {"conversation_id": conversation_id})

    def get_messages_by_npc(self, npc, n_last=20) -> List[Dict]:
        stmt = """
            SELECT * FROM conversation_history WHERE npc = :npc
            ORDER BY timestamp DESC LIMIT :n_last
        """
        return self._fetch_all(stmt, {"npc": npc, "n_last": n_last})

    def get_messages_by_team(self, team, n_last=20) -> List[Dict]:
        stmt = """
            SELECT * FROM conversation_history WHERE team = :team
            ORDER BY timestamp DESC LIMIT :n_last
        """
        return self._fetch_all(stmt, {"team": team, "n_last": n_last})

    def get_message_by_id(self, message_id) -> Optional[Dict]:
        stmt = "SELECT * FROM conversation_history WHERE message_id = :message_id"
        return self._fetch_one(stmt, {"message_id": message_id})

    def get_most_recent_conversation_id_by_path(self, path) -> Optional[Dict]:
        stmt = """
            SELECT conversation_id FROM conversation_history WHERE directory_path = :path
            ORDER BY timestamp DESC LIMIT 1
        """
        return self._fetch_one(stmt, {"path": path})

    def get_last_conversation_by_path(self, directory_path) -> Optional[List[Dict]]:
        result_dict = self.get_most_recent_conversation_id_by_path(directory_path)
        if result_dict and result_dict.get('conversation_id'):
            convo_id = result_dict['conversation_id']
            return self.get_conversations_by_id(convo_id)
        return None

    def get_conversations_by_id(self, conversation_id: str) -> List[Dict[str, Any]]:
        stmt = """
            SELECT id, message_id, timestamp, role, content, conversation_id,
                    directory_path, model, provider, npc, team
            FROM conversation_history WHERE conversation_id = :conversation_id 
            ORDER BY timestamp ASC
        """
        results = self._fetch_all(stmt, {"conversation_id": conversation_id})
        
        for message_dict in results:
            attachments = self.get_message_attachments(message_dict["message_id"])
            if attachments:
                message_dict["attachments"] = attachments
        return results

    def get_npc_conversation_stats(self, start_date=None, end_date=None) -> pd.DataFrame:
        date_filter = ""
        params = {}
        
        if start_date and end_date:
            date_filter = "WHERE timestamp BETWEEN :start_date AND :end_date"
            params = {"start_date": start_date, "end_date": end_date}
        elif start_date:
            date_filter = "WHERE timestamp >= :start_date"
            params = {"start_date": start_date}
        elif end_date:
            date_filter = "WHERE timestamp <= :end_date"
            params = {"end_date": end_date}

        
        if 'sqlite' in str(self.engine.url):
            group_concat_models = "GROUP_CONCAT(DISTINCT model)"
            group_concat_providers = "GROUP_CONCAT(DISTINCT provider)"
        else:
            
            group_concat_models = "STRING_AGG(DISTINCT model, ',')"
            group_concat_providers = "STRING_AGG(DISTINCT provider, ',')"

        query = f"""
        SELECT
            npc,
            COUNT(*) as total_messages,
            AVG(LENGTH(content)) as avg_message_length,
            COUNT(DISTINCT conversation_id) as total_conversations,
            COUNT(DISTINCT model) as models_used,
            COUNT(DISTINCT provider) as providers_used,
            {group_concat_models} as model_list,
            {group_concat_providers} as provider_list,
            MIN(timestamp) as first_conversation,
            MAX(timestamp) as last_conversation
        FROM conversation_history
        {date_filter}
        GROUP BY npc
        ORDER BY total_messages DESC
        """
        
        try:
            df = pd.read_sql(sql=text(query), con=self.engine, params=params)
            return df
        except Exception as e:
            print(f"Error fetching conversation stats with pandas: {e}")
            return pd.DataFrame(columns=[
                'npc', 'total_messages', 'avg_message_length', 'total_conversations',
                'models_used', 'providers_used', 'model_list', 'provider_list',
                'first_conversation', 'last_conversation'
            ])

    def get_command_patterns(self, timeframe='day') -> pd.DataFrame:
        
        if 'sqlite' in str(self.engine.url):
            time_group_formats = {
                'hour': "strftime('%Y-%m-%d %H', timestamp)",
                'day': "strftime('%Y-%m-%d', timestamp)",
                'week': "strftime('%Y-%W', timestamp)",
                'month': "strftime('%Y-%m', timestamp)"
            }
        else:
            
            time_group_formats = {
                'hour': "TO_CHAR(timestamp::timestamp, 'YYYY-MM-DD HH24')",
                'day': "TO_CHAR(timestamp::timestamp, 'YYYY-MM-DD')",
                'week': "TO_CHAR(timestamp::timestamp, 'YYYY-WW')",
                'month': "TO_CHAR(timestamp::timestamp, 'YYYY-MM')"
            }
        
        time_group = time_group_formats.get(timeframe, time_group_formats['day'])

        
        if 'sqlite' in str(self.engine.url):
            substr_func = "SUBSTR"
            instr_func = "INSTR"
        else:
            substr_func = "SUBSTRING"
            instr_func = "POSITION"

        query = f"""
        WITH parsed_commands AS (
            SELECT
                {time_group} as time_bucket,
                CASE
                    WHEN command LIKE '/%%' THEN {substr_func}(command, 2, {instr_func}({substr_func}(command, 2), ' ') - 1)
                    WHEN command LIKE 'npc %%' THEN {substr_func}(command, 5, {instr_func}({substr_func}(command, 5), ' ') - 1)
                    ELSE command
                END as base_command
            FROM command_history
            WHERE timestamp IS NOT NULL
        )
        SELECT
            time_bucket,
            base_command,
            COUNT(*) as usage_count
        FROM parsed_commands
        WHERE base_command IS NOT NULL AND base_command != ''
        GROUP BY time_bucket, base_command
        ORDER BY time_bucket DESC, usage_count DESC
        """
        
        try:
            df = pd.read_sql(sql=text(query), con=self.engine)
            return df
        except Exception as e:
            print(f"Error fetching command patterns with pandas: {e}")
            return pd.DataFrame(columns=['time_period', 'command', 'count'])

    def search_commands(self, search_term: str) -> List[Dict]:
        """Searches command history table for a term."""
        stmt = """
            SELECT id, timestamp, command, subcommands, output, location
            FROM command_history
            WHERE LOWER(command) LIKE LOWER(:search_term) OR LOWER(output) LIKE LOWER(:search_term)
            ORDER BY timestamp DESC
            LIMIT 5
        """
        like_term = f"%{search_term}%"
        return self._fetch_all(stmt, {"search_term": like_term})

    def search_conversations(self, search_term: str) -> List[Dict]:
        """Searches conversation history table for a term."""
        stmt = """
            SELECT id, message_id, timestamp, role, content, conversation_id, directory_path, model, provider, npc, team
            FROM conversation_history
            WHERE LOWER(content) LIKE LOWER(:search_term)
            ORDER BY timestamp DESC
            LIMIT 5
        """
        like_term = f"%{search_term}%"
        return self._fetch_all(stmt, {"search_term": like_term})
    
    def get_all_commands(self, limit: int = 100) -> List[Dict]:
        """Gets the most recent commands."""
        stmt = """
            SELECT id, timestamp, command, subcommands, output, location
            FROM command_history
            ORDER BY id DESC
            LIMIT :limit
        """
        return self._fetch_all(stmt, {"limit": limit})

    def close(self):
        """Dispose of the SQLAlchemy engine."""
        if self.engine:
            try:
                self.engine.dispose()
                logging.info("Disposed SQLAlchemy engine.")
            except Exception as e:
                print(f"Error disposing SQLAlchemy engine: {e}")
        self.engine = None

def start_new_conversation(prepend: str = None) -> str:
    """
    Starts a new conversation and returns a unique conversation ID.
    """
    if prepend is None:
        prepend = 'npcsh'
    return f"{prepend}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def save_conversation_message(
    command_history: CommandHistory,
    conversation_id: str,
    role: str,
    content: str,
    wd: str = None,
    model: str = None,
    provider: str = None,
    npc: str = None,
    team: str = None,
    attachments: List[Dict] = None,
    message_id: str = None,
    ):
    """
    Saves a conversation message linked to a conversation ID with optional attachments.
    """
    if wd is None:
        wd = os.getcwd()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if message_id is None:
        message_id = generate_message_id()


    return command_history.add_conversation(
        message_id, 
        timestamp, 
        role, 
        content, 
        conversation_id, 
        wd, 
        model=model, 
        provider=provider, 
        npc=npc, 
        team=team, 
        attachments=attachments)
def retrieve_last_conversation(
    command_history: CommandHistory, conversation_id: str
    ) -> str:
    """
    Retrieves and formats all messages from the last conversation.
    """
    last_message = command_history.get_last_conversation(conversation_id)
    if last_message:
        return last_message['content']  
    return "No previous conversation messages found."

def save_attachment_to_message(
    command_history: CommandHistory,
    message_id: str,
    file_path: str,
    attachment_name: str = None,
    attachment_type: str = None,
    ):
    """
    Helper function to save a file from disk as an attachment.
    """
    try:
        if not attachment_name:
            attachment_name = os.path.basename(file_path)

        if not attachment_type:
            _, ext = os.path.splitext(file_path)
            if ext:
                attachment_type = ext.lower()[1:]

        with open(file_path, "rb") as f:
            data = f.read()

        command_history.add_attachment(
            message_id=message_id,
            attachment_name=attachment_name,
            attachment_type=attachment_type,
            attachment_data=data,
            attachment_size=len(data),
        )
        return True
    except Exception as e:
        print(f"Error saving attachment: {str(e)}")
        return False

def get_available_tables(db_path_or_engine: Union[str, Engine]) -> List[Tuple[str]]:
    """
    Gets the available tables in the database.
    """
    if isinstance(db_path_or_engine, str):
        engine = create_engine_from_path(db_path_or_engine)
    else:
        engine = db_path_or_engine
    
    try:
        with engine.connect() as conn:
            if 'sqlite' in str(engine.url):
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'command_history'"
                ))
            else:
                
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name != 'command_history'
                """))
            
            return [row[0] for row in result]
    except Exception as e:
        print(f"Error getting available tables: {e}")
        return []