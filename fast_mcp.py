from fastmcp import FastMCP
from rag_gemni import RAGAgent
import json

# Initialize FastMCP server
mcp = FastMCP("MENA Tourism RAG - Gemini")

print("🔄 Initializing RAG Agent with Gemini API...")
rag_agent = RAGAgent()
print(f"✅ RAG Agent loaded with {len(rag_agent.chunks)} chunks")


@mcp.tool()
def query_tourism_rag(question: str) -> str:
    """
    Query the MENA Tourism RAG system powered by Google Gemini.

    Args:
        question: The tourism question (supports English and Arabic)

    Returns:
        JSON string with the answer and metadata
    """
    print(f"\n🔍 Received question: {question}")
    answer = rag_agent.ask(question)

    return json.dumps({
        "answer": answer,
        "question": question,
        "status": "success",
        "powered_by": "Google Gemini 2.0 Flash"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def check_rag_status() -> str:
    """Check if the RAG system is loaded and ready"""
    return json.dumps({
        "status": "online ☁️",
        "chunks_loaded": len(rag_agent.chunks),
        "llm_model": "gemini-2.0-flash-exp",
        "languages": ["English", "Arabic"],
        "deployment": "FastMCP + Gemini"
    }, indent=2)


if __name__ == "__main__":
    print("🚀 Starting MENA Tourism RAG with Gemini...")
    mcp.run()