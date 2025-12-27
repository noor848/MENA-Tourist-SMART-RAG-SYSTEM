from fastmcp import FastMCP
from rag_gemni import RAGAgent
import json
import os

# Initialize FastMCP server
mcp = FastMCP("MENA Tourism RAG - Gemini")

# ✅ Lazy loading - DON'T initialize here!
rag_agent = None
agent_ready = False
initialization_error = None

print("🚀 Starting MENA Tourism RAG with Gemini...")
print("⏳ Agent will initialize on first query (lazy loading)")


def get_agent():
    """Lazy load the RAG agent on first use"""
    global rag_agent, agent_ready, initialization_error

    if agent_ready and rag_agent is not None:
        return rag_agent

    if initialization_error is not None:
        return None

    try:
        print("🔄 Initializing RAG Agent (first request)...")
        rag_agent = RAGAgent()
        agent_ready = True
        print(f"✅ RAG Agent loaded with {len(rag_agent.chunks)} chunks")
        return rag_agent
    except Exception as e:
        initialization_error = str(e)
        print(f"❌ Failed to initialize RAG Agent: {e}")
        return None


@mcp.tool()
def query_tourism_rag(question: str) -> str:
    """
    Query the MENA Tourism RAG system powered by Google Gemini.

    Args:
        question: The tourism question (supports English and Arabic)

    Returns:
        JSON string with the answer and metadata
    """
    agent = get_agent()

    if agent is None:
        return json.dumps({
            "error": f"RAG Agent initialization failed: {initialization_error}",
            "status": "failed",
            "suggestion": "Check if GEMINI_API_KEY is set and index files are present"
        }, ensure_ascii=False, indent=2)

    try:
        print(f"\n🔍 Received question: {question}")
        answer = agent.ask(question)

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
    agent = get_agent()

    if agent is None:
        return json.dumps({
            "status": "initializing ⏳" if initialization_error is None else "offline ❌",
            "error": initialization_error or "Agent not yet loaded",
            "env_check": {
                "GEMINI_API_KEY": "✅ Set" if os.getenv("GEMINI_API_KEY") else "❌ Missing"
            },
            "note": "Agent will initialize on first query"
        }, indent=2)

    return json.dumps({
        "status": "online ☁️",
        "chunks_loaded": len(agent.chunks),
        "llm_model": "gemini-2.0-flash-exp",
        "languages": ["English", "Arabic"],
        "deployment": "FastMCP + Gemini",
        "index_ready": agent.index is not None
    }, indent=2)


if __name__ == "__main__":
    mcp.run()