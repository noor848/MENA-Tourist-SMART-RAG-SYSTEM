import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from typing import List, Dict
from typing_extensions import TypedDict
from langchain_ollama import OllamaLLM


class LoadModels:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device='cuda')
        self.index = faiss.read_index("heritage.index")

        self.llm = OllamaLLM(model="mistral:7b")

        self.chunks = []
        self.metadata = []

    def read_file(self, file="heritage.pkl"):
        with open(file, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']

        print(f"✅ Loaded {len(self.chunks)} chunks\n")

    def ask_question(self, query, k=3):
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector, k)
        context_chunks = [self.chunks[idx] for idx in indices[0]]
        context = "\n\n".join(context_chunks)
        prompt = f"""You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Be concise and use the Arabic context to answer the question.

    Question: {query}
    Context: {context}

    Helpful Answer:"""

        print(f"🔍 Searching for: {query}")
        print("💭 Thinking...\n")

        answer = self.llm.invoke(prompt)

        print(f"💬 Answer:\n{answer}\n")

        print(f"📚 Sources:")
        for idx in indices[0]:
            print(f"  - {self.metadata[idx]['country']}")
        print()

        return answer

class AgentState(TypedDict):
    question: str
    Answer: str
    docs:list[str]
    historical_answer: list[str]


def retriever_node(model, state:AgentState):
    query_vector = model.encode([state['question']])
    distances, indices = model.index.search(query_vector, k=10)
    context_chunks = [model.chunks[idx] for idx in indices[0]]

    return {
        'question': state['question'],
        'Answer': '',
        'docs': context_chunks,
        'historical_answer': state['historical_answer'],
    }

def grader_docs_node(model, state:AgentState):
    question = state['question']
    docs= state['docs']

    prompt_template = """You are a grader. Your job is to check if a
    retrieved document is relevant to a user question.
    Respond with a *single word*: 'yes' if relevant, 'no' if not.

    Document: {document}
    Question: {question}

    Answer:"""

    prompt = PromptTemplate.from_template(prompt_template)
    grader_chain = prompt | model.llm | StrOutputParser()


    relevant_docs = []
    for doc in docs:
        try:
            result = grader_chain.invoke({"question": question, "document": doc})
            score = result.strip().lower()
            if "yes" in score:
                print("  -> Grader Decision: Relevant")
                relevant_docs.append(doc)
            else:
                print("  -> Grader Decision: NOT Relevant")
        except Exception as e:
            print(f"  -> Grader: Error - {e}")
            continue

    return {
    'question': question,
    'Answer': '',
    'docs': relevant_docs,
    }

def generate_node(model, state:AgentState):
    """Takes the question and documents, and generates an answer."""
    print("---NODE: GENERATE---")
    question = state["question"]
    documents = state["docs"]

    prompt_template = """You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Be concise.

    Question: {question}
    Context: {context}

    Helpful Answer:"""
    prompt = PromptTemplate.from_template(prompt_template)
    rag_chain = prompt | model.llm | StrOutputParser()

    generation = rag_chain.invoke({"context": "\n".join(documents), "question": question})

    return {
    'question': question,
    'Answer': generation,
    'docs': state["docs"],
    'historical_answer': state['historical_answer'],
    }





if __name__ == "__main__":
    model = LoadModels()
    model.read_file("heritage.pkl")
    while True:
        model.ask_question(input("ENTER Q\n"))
