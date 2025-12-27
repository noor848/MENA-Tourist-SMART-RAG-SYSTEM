from fastmcp import FastMCP
from rag_gemni import RAGAgent
import json
import os

# Initialize FastMCP server
mcp = FastMCP("MENA Tourism RAG - Gemini")

print("🔄 Initializing RAG Agent with Gemini API...")

# ✅ Initialize with error handling
try:
    rag_agent = RAGAgent()
    print(f"✅ RAG Agent loaded with {len(rag_agent.chunks)} chunks")
    agent_ready = True
except Exception as e:
    print(f"❌ Failed to initialize RAG Agent: {e}")
    rag_agent = None
    agent_ready = False


@mcp.tool()
def query_tourism_rag(question: str) -> str:
    """
    Query the MENA Tourism RAG system powered by Google Gemini.

    Args:
        question: The tourism question (supports English and Arabic)

    Returns:
        JSON string with the answer and metadata
    """
    if not agent_ready or rag_agent is None:
        return json.dumps({
            "error": "RAG Agent is not initialized",
            "status": "failed",
            "suggestion": "Check if GEMINI_API_KEY is set and index files are present"
        }, ensure_ascii=False, indent=2)

    try:
        print(f"\n🔍 Received question: {question}")
        answer = rag_agent.ask(question)

        return json.dumps({
            "answer": answer,
            "question": question,
            "status": "success",
            "powered_by": "Google Gemini 2.0 Flash"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "question": question,
            "status": "failed"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def check_rag_status() -> str:
    """Check if the RAG system is loaded and ready"""
    if not agent_ready or rag_agent is None:
        return json.dumps({
            "status": "offline ❌",
            "error": "RAG Agent not initialized",
            "env_check": {
                "GEMINI_API_KEY": "✅ Set" if os.getenv("GEMINI_API_KEY") else "❌ Missing",
                "index_files": "❌ Check logs for file loading errors"
            }
        }, indent=2)

    return json.dumps({
        "status": "online ☁️",
        "chunks_loaded": len(rag_agent.chunks),
        "llm_model": "gemini-2.0-flash-exp",
        "languages": ["English", "Arabic"],
        "deployment": "FastMCP + Gemini",
        "index_ready": rag_agent.index is not None
    }, indent=2)


if __name__ == "__main__":
    print("🚀 Starting MENA Tourism RAG with Gemini...")
    mcp.run()