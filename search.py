import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph

from typing_extensions import TypedDict
from langchain_ollama import OllamaLLM


class AgentState(TypedDict):
    question: str
    Answer: str
    docs: list[str]
    historical_questions: list[str]


class RAGAgent:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device='cuda')
        self.index = faiss.read_index("heritage.index")
        self.llm = OllamaLLM(model="mistral:7b")
        self.app = self.build_graph()


        self.chunks = []
        self.metadata = []

        self.read_file("heritage.pkl")

    def read_file(self, file="heritage.pkl"):
        with open(file, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']

        print(f"✅ Loaded {len(self.chunks)} chunks\n")

    def retriever_node(self, state: AgentState):
        print("---NODE: RETRIEVE---")
        query_vector = self.model.encode([state['question']])
        distances, indices = self.index.search(query_vector, 10)
        context_chunks = [self.chunks[idx] for idx in indices[0]]

        return {
            'question': state['question'],
            'Answer': state.get('Answer', ''),
            'docs': context_chunks,
            'historical_questions': state['historical_questions'],
        }

    def grader_docs_node(self, state: AgentState):
        print("---NODE: GRADE DOCUMENTS---")
        question = state['question']
        docs = state['docs']

        prompt_template = """You are a grader. Your job is to check if a
retrieved document is relevant to a user question.
Respond with a *single word*: 'yes' if relevant, 'no' if not.

Document: {document}
Question: {question}

Answer:"""

        prompt = PromptTemplate.from_template(prompt_template)
        grader_chain = prompt | self.llm | StrOutputParser()

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

        print(f"  -> Found {len(relevant_docs)} relevant documents")

        return {
            'question': question,
            'Answer': state.get('Answer', ''),
            'docs': relevant_docs,
            'historical_questions': state['historical_questions'],
        }

    def generate_node(self, state: AgentState):
        print("---NODE: GENERATE---")
        question = state["question"]
        documents = state["docs"]

        prompt_template = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Answer in the same language as the question (Arabic, English, or French).

Question: {question}
Context: {context}

Helpful Answer:"""

        prompt = PromptTemplate.from_template(prompt_template)
        rag_chain = prompt | self.llm | StrOutputParser()

        generation = rag_chain.invoke({
            "context": "\n\n".join(documents),
            "question": question
        })

        print(f"✅ Generated answer")

        return {
            'question': question,
            'Answer': generation,
            'docs': documents,
            'historical_questions': state['historical_questions'],
        }

    def rewriter_node(self, state: AgentState):
        print("---NODE: REWRITE QUERY---")
        question = state["question"]
        historical_questions = state["historical_questions"]

        if question in historical_questions:
            return {
                "question": question,
                "Answer": "Could not find relevant information after multiple attempts.",
                "docs": [],
                "historical_questions": historical_questions
            }

        historical_questions.append(question)

        prompt_template = """You are a query rewriter. Rewrite the following question to be
a concise and specific search query for a vector database.
Respond ONLY with the rewritten query, nothing else.

Original Question: {question}

Rewritten Query:"""

        prompt = PromptTemplate.from_template(prompt_template)
        rewrite_chain = prompt | self.llm | StrOutputParser()

        new_question = rewrite_chain.invoke({"question": question}).strip()
        print(f"  -> Rewritten: {new_question}")

        return {
            "question": new_question,
            "Answer": "",
            "docs": [],
            "historical_questions": historical_questions
        }

    def decision_node(self, state: AgentState):
        print("---NODE: DECISION---")

        # If we have relevant docs, generate answer
        if state['docs'] and len(state['docs']) > 0:
            print("  -> Decision: GENERATE (found relevant docs)")
            return "generate"

        # If we've tried too many times, end
        if len(state['historical_questions']) >= 3:
            print("  -> Decision: END (too many attempts)")
            return "end"

        # Otherwise, rewrite query
        print("  -> Decision: REWRITE (no relevant docs)")
        return "rewrite"

    def build_graph(self):
        """Build the LangGraph workflow"""
        graph = StateGraph(AgentState)

        graph.add_node("retriever", self.retriever_node)
        graph.add_node("grader", self.grader_docs_node)
        graph.add_node("generate", self.generate_node)
        graph.add_node("rewriter", self.rewriter_node)

        graph.set_entry_point("retriever")

        graph.add_edge("retriever", "grader")

        graph.add_conditional_edges(
            "grader",
            self.decision_node,
            {
                "generate": "generate",
                "rewrite": "rewriter",
                "end": END
            }
        )

        graph.add_edge("rewriter", "retriever")

        graph.add_edge("generate", END)

        return graph.compile()

    def ask(self, question: str):
        """Ask a question using the RAG agent"""
        result = self.app.invoke({
            "question": question,
            "Answer": "",
            "docs": [],
            "historical_questions": []
        })

        print("\n" + "=" * 70)
        print("FINAL ANSWER")
        print("=" * 70)
        print(result['Answer'])
        print("=" * 70 + "\n")

        return result['Answer']


if __name__ == "__main__":
    agent = RAGAgent()

    print("\n🤖 RAG Agent Ready! Ask questions about Arab heritage.\n")

    while True:
        question = input("❓ Your question (or 'quit' to exit): ").strip()

        if question.lower() == 'quit':
            print("Goodbye! 👋")
            break

        if question:
            try:
                agent.ask(question)
            except Exception as e:
                print(f"❌ Error: {e}\n")