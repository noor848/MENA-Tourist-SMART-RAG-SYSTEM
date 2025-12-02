# Multilingual RAG Agent for Heritage Data

A Retrieval-Augmented Generation (RAG) agent that uses a single English knowledge base while supporting multilingual queries and responses. Ask questions in Arabic or English and receive answers in the same language.

## Features

- **Single Index, Multilingual Support**: Uses only the English FAISS index but handles queries in multiple languages
- **Automatic Language Detection**: Detects whether questions are in Arabic or English using XLM-RoBERTa
- **Language-Matched Responses**: Automatically responds in the same language as the question
- **Multilingual Embeddings**: Uses `paraphrase-multilingual-mpnet-base-v2` for cross-lingual semantic search
- **Intelligent Query Rewriting**: Automatically rewrites queries when no relevant documents are found
- **Document Grading**: Filters retrieved documents for relevance before generating answers

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Question                            │
│                   (Arabic or English)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Language Detection                           │
│              (papluca/xlm-roberta-base-language-detection)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Retriever Node                             │
│    Encode query with multilingual model → Search English index  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Document Grader Node                         │
│              Filter documents for relevance                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Decision Node  │
                    └─────────────────┘
                     /       │        \
                    /        │         \
                   ▼         ▼          ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │ Generate │ │ Rewrite  │ │   End    │
            │  Answer  │ │  Query   │ │          │
            └──────────┘ └──────────┘ └──────────┘
                              │
                              │ (loops back to Retriever)
                              ▼
```

## Requirements

### Python Dependencies

```bash
pip install faiss-gpu  # or faiss-cpu
pip install sentence-transformers
pip install langchain-core
pip install langgraph
pip install langchain-ollama
pip install transformers
pip install torch
```

### Models

- **Embedding Model**: `paraphrase-multilingual-mpnet-base-v2` (auto-downloaded)
- **Language Detection**: `papluca/xlm-roberta-base-language-detection` (auto-downloaded)
- **LLM**: `aya-expanse:8b` (requires Ollama)

### Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the Aya Expanse model
ollama pull aya-expanse:8b
```

## Required Files

Place these files in the same directory as the script:

| File | Description |
|------|-------------|
| `heritage_english.index` | FAISS index file containing English document embeddings |
| `heritage_EN.pkl` | Pickle file containing document chunks and metadata |

### Pickle File Structure

The `.pkl` file should contain a dictionary with:

```python
{
    'chunks': ['chunk1 text', 'chunk2 text', ...],  # List of text chunks
    'metadata': [{'source': '...', ...}, ...]       # List of metadata dicts
}
```

## Usage

### Basic Usage

```python
from rag_agent_single_index import RAGAgent

# Initialize the agent
agent = RAGAgent()

# Ask questions in English
answer = agent.ask("What is the history of this heritage site?")

# Ask questions in Arabic
answer = agent.ask("ما هو تاريخ هذا الموقع التراثي؟")
```

### Running as Script

```bash
python rag_agent_single_index.py
```

## How It Works

1. **Query Processing**: When a question is submitted, the language detector identifies whether it's Arabic or English.

2. **Multilingual Retrieval**: The question is encoded using the multilingual sentence transformer. Since the model maps semantically similar texts to similar vectors regardless of language, an Arabic query can effectively retrieve relevant English documents.

3. **Document Grading**: Retrieved documents are evaluated for relevance to the question using the LLM.

4. **Decision Making**:
   - If relevant documents are found → Generate answer
   - If no relevant documents → Rewrite query and retry (up to 3 attempts)
   - If max attempts reached → Return "not found" message

5. **Answer Generation**: The LLM generates an answer using the relevant documents as context, responding in the same language as the original question.

## Configuration

### Adjusting Retrieval

```python
# In retriever_node method, change the number of documents retrieved:
distances, indices = self.index.search(query_vector, 10)  # Retrieve top 10
```

### Changing the LLM

```python
# In __init__ method:
self.llm = OllamaLLM(model="your-model-name")
```

### Using CPU Instead of GPU

```python
# In __init__ method:
self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device='cpu')
```

## Project Structure

```
.
├── rag_agent_single_index.py   # Main RAG agent code
├── heritage_english.index       # FAISS index file
├── heritage_EN.pkl             # Document chunks and metadata
└── README.md                   # This file
```

## Troubleshooting

### Common Issues

**"Could not load English index"**
- Ensure `heritage_english.index` and `heritage_EN.pkl` are in the same directory as the script
- Check file permissions

**"CUDA out of memory"**
- Switch to CPU mode by changing `device='cuda'` to `device='cpu'`
- Or use a smaller batch size for encoding

**Ollama connection error**
- Ensure Ollama is running: `ollama serve`
- Verify the model is installed: `ollama list`

**Poor retrieval results for Arabic queries**
- The multilingual model works best with well-formed queries
- Try rephrasing the question
- Ensure the English index contains relevant content

## License

[Add your license here]

## Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for multilingual embeddings
- [LangChain](https://langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [Ollama](https://ollama.com/) for local LLM inference
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search
