import os
import tempfile
import sqlite3
from npcpy.memory.command_history import CommandHistory, save_conversation_message, start_new_conversation


def test_command_history_creation():
    """Test CommandHistory database creation"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert "command_history" in tables
        assert "conversation_history" in tables
        print(f"Created database with tables: {tables}")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_add_command():
    """Test adding commands to history"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        history.add_command(
            command="test command",
            subcommands=["sub1", "sub2"],
            output="test output",
            location="/test/path"
        )
        
        last_command = history.get_last_command()
        assert last_command is not None
        assert last_command["command"] == "test command"
        print(f"Added command: {last_command}")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_add_conversation():
    """Test adding conversation messages"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        conversation_id = "test_conv_123"
        
        history.add_conversation(
            role="user",
            content="Hello, how are you?",
            conversation_id=conversation_id,
            directory_path="/test/path"
        )
        
        history.add_conversation(
            role="assistant", 
            content="I'm doing well, thank you!",
            conversation_id=conversation_id,
            directory_path="/test/path"
        )
        
        conversations = history.get_conversations_by_id(conversation_id)
        assert len(conversations) == 2
        assert conversations[0]["role"] == "user"
        assert conversations[1]["role"] == "assistant"
        print(f"Added {len(conversations)} conversation messages")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_save_conversation_message():
    """Test save_conversation_message function"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        conversation_id = start_new_conversation()
        
        save_conversation_message(
            history,
            conversation_id,
            "user",
            "What is the weather like?",
            wd="/test/path"
        )
        
        conversations = history.get_conversations_by_id(conversation_id)
        assert len(conversations) == 1
        assert conversations[0]["content"] == "What is the weather like?"
        print(f"Saved conversation message with ID: {conversation_id}")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_add_attachment():
    """Test adding attachments to messages"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        
        conversation_id = "test_conv_123"
        message_id = generate_message_id()
        
        history.add_conversation(
            role="user",
            content="Test message with attachment",
            conversation_id=conversation_id,
            directory_path="/test/path",
            message_id=message_id
        )
        
        
        attachment_data = b"Test file content"
        
        history.add_attachment(
            message_id=message_id,
            attachment_name="test.txt",
            attachment_type="text/plain",
            attachment_data=attachment_data
        )
        
        attachments = history.get_message_attachments(message_id)
        assert len(attachments) == 1
        assert attachments[0]["attachment_name"] == "test.txt"
        print(f"Added attachment: {attachments[0]}")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_search_commands():
    """Test command search functionality"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        
        history.add_command("ls -la", [], "file listing", "/home")
        history.add_command("cd /tmp", [], "changed directory", "/home")
        history.add_command("python script.py", [], "script output", "/tmp")
        
        
        results = history.search_commands("python")
        assert len(results) >= 1
        assert any("python" in cmd["command"] for cmd in results)
        print(f"Found {len(results)} commands matching 'python'")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_search_conversations():
    """Test conversation search functionality"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        conversation_id = "search_test_conv"
        
        
        history.add_conversation(
            "user", "How do I install Python?", conversation_id, "/test"
        )
        history.add_conversation(
            "assistant", "You can install Python from python.org", conversation_id, "/test"
        )
        
        
        results = history.search_conversations("Python")
        assert len(results) >= 1
        print(f"Found {len(results)} conversations mentioning 'Python'")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_get_messages_by_npc():
    """Test getting messages by NPC"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        history.add_conversation(
            "user", "Hello assistant", "conv1", "/test", npc="test_npc"
        )
        history.add_conversation(
            "assistant", "Hello user", "conv1", "/test", npc="test_npc"
        )
        
        messages = history.get_messages_by_npc("test_npc", n_last=10)
        assert len(messages) >= 2
        print(f"Found {len(messages)} messages from test_npc")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_jinx_execution_logging():
    """Test jinx execution logging"""
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        history = CommandHistory(temp_db)
        
        message_id = generate_message_id()
        
        history.save_jinx_execution(
            triggering_message_id=message_id,
            conversation_id="test_conv",
            npc_name="test_npc",
            jinx_name="test_jinx",
            jinx_inputs={"input": "test"},
            jinx_output="test output",
            status="success"
        )
        
        print("Successfully logged jinx execution")
        
        history.close()
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_start_new_conversation():
    """Test starting new conversation"""
    conversation_id = start_new_conversation()
    assert conversation_id is not None
    assert len(conversation_id) > 0
    print(f"Started new conversation: {conversation_id}")
    
    
    conversation_id_with_prepend = start_new_conversation("test_")
    assert conversation_id_with_prepend.startswith("test_")
    print(f"Started conversation with prepend: {conversation_id_with_prepend}")
