from mem0 import MemoryClient
from dotenv import load_dotenv
import os

load_dotenv()

mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

# Define memory function tools
def search_memory(query: str, user_id: str) -> dict:
    """Search through past conversations and memories"""
    # For Platform API, user_id goes in filters
    filters = {"user_id": user_id}
    memories = mem0.search(query, filters=filters)
    if memories.get('results', []):
        memory_list = memories['results']
        memory_context = "\n".join([f"- {mem['memory']}" for mem in memory_list])
        return {"status": "success", "memories": memory_context}
    return {"status": "no_memories", "message": "No relevant memories found"}

def save_memory(messages, user_id: str) -> dict:
    """Save important information to memory
    
    Args:
        content: Can be a string or a list of message dicts with 'role' and 'content' keys
        user_id: The user's unique identifier
    """
    try:
        result = mem0.add(messages, user_id=user_id)
        return {"status": "success", "message": "Information saved to memory", "result": result}
    except Exception as e:
        return {"status": "error", "message": f"Failed to save memory: {str(e)}"}