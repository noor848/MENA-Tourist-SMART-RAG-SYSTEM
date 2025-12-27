import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI  # ✅ Gemini API
from transformers import pipeline
import os


class AgentState(TypedDict):
    question: str
    Answer: str
    docs: list[str]
    historical_questions: list[str]
    language: str


class RAGAgent:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/LaBSE', device='cpu')
        # Language detection model
        self.language_detector = pipeline(
            "text-classification",
            model="papluca/xlm-roberta-base-language-detection",
            device=-1
        )

        # Single English index for all queries
        self.index = None
        self.chunks = []
        self.metadata = []

        # Load only English index
        self.load_index("heritage_english.index", "heritage_EN.pkl")

        # ✅ Use Gemini API
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Free & fast model
            google_api_key="AIzaSyBaPL88mkeJqv4klqGcgmta_cqCXTFTHr4",  # Direct API key
            temperature=0
        )

        self.app = self.build_graph()

    def load_index(self, index_file: str, pkl_file: str):
        """Load FAISS index and pickle data (English only)"""
        try:
            self.index = faiss.read_index(index_file)

            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']

            print(f"✅ Loaded English index with {len(self.chunks)} chunks")
        except Exception as e:
            print(f"❌ Error: Could not load English index: {e}")
            self.index = None
            self.chunks = []
            self.metadata = []

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        try:
            result = self.language_detector(text)[0]
            detected_lang = result['label']
            confidence = result['score']

            print(f"🔍 Detected language: {detected_lang} (confidence: {confidence:.2f})")

            if detected_lang == 'ar':
                return 'arabic'
            elif detected_lang == 'en':
                return 'english'
            else:
                print(f"⚠️  Language '{detected_lang}' detected. Will respond in English.")
                return 'english'

        except Exception as e:
            print(f"❌ Error detecting language: {e}")
            return 'english'

    def retriever_node(self, state: AgentState):
        print("---NODE: RETRIEVE---")

        if self.index is None:
            return {
                'question': state['question'],
                'Answer': 'Sorry, the index is not available.',
                'docs': [],
                'historical_questions': state['historical_questions'],
                'language': state['language']
            }

        query_vector = self.model.encode([state['question']])
        distances, indices = self.index.search(query_vector, 10)
        context_chunks = [self.chunks[idx] for idx in indices[0]]

        return {
            'question': state['question'],
            'Answer': state.get('Answer', ''),
            'docs': context_chunks,
            'historical_questions': state['historical_questions'],
            'language': state['language']
        }

    def grader_docs_node(self, state: AgentState):
        print("---NODE: GRADE DOCUMENTS---")
        question = state['question']
        docs = state['docs']
        language = state['language']

        prompt_template = """You are a grader. Your job is to check if a retrieved document is relevant to a user question.
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
            'language': language
        }

    def generate_node(self, state: AgentState):
        print("---NODE: GENERATE---")
        question = state["question"]
        documents = state["docs"]
        language = state["language"]

        if language == 'arabic':
            prompt_template = """أنت مساعد للإجابة على الأسئلة.
استخدم أجزاء السياق المسترجعة التالية للإجابة على السؤال.
إذا كنت لا تعرف الإجابة، قل فقط أنك لا تعرف.
يجب أن تكون الإجابة بالعربية.

السؤال: {question}
السياق: {context}

الإجابة المفيدة:"""
        else:
            prompt_template = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
The answer should be in English.

Question: {question}
Context: {context}

Helpful Answer:"""

        prompt = PromptTemplate.from_template(prompt_template)
        rag_chain = prompt | self.llm | StrOutputParser()

        generation = rag_chain.invoke({
            "context": "\n\n".join(documents),
            "question": question
        })

        print(f"✅ Generated answer in {language}")

        return {
            'question': question,
            'Answer': generation,
            'docs': documents,
            'historical_questions': state['historical_questions'],
            'language': language
        }

    def rewriter_node(self, state: AgentState):
        print("---NODE: REWRITE QUERY---")
        question = state["question"]
        historical_questions = state["historical_questions"]
        language = state["language"]

        if question in historical_questions:
            error_msg = "لم أتمكن من إيجاد معلومات ذات صلة بعد محاولات متعددة." if language == 'arabic' else "Could not find relevant information after multiple attempts."
            return {
                "question": question,
                "Answer": error_msg,
                "docs": [],
                "historical_questions": historical_questions,
                "language": language
            }

        historical_questions.append(question)

        prompt_template = """You are a query rewriter. Rewrite the following question to be a concise and specific search query for a vector database.
Keep the query in the same language as the original question.
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
            "historical_questions": historical_questions,
            "language": language
        }

    def decision_node(self, state: AgentState):
        print("---NODE: DECISION---")

        if state['docs'] and len(state['docs']) > 0:
            print("  -> Decision: GENERATE (found relevant docs)")
            return "generate"

        if len(state['historical_questions']) >= 3:
            print("  -> Decision: END (too many attempts)")
            return "end"

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
        language = self.detect_language(question)

        result = self.app.invoke({
            "question": question,
            "Answer": "",
            "docs": [],
            "historical_questions": [],
            "language": language
        })

        print("\n" + "=" * 70)
        print("FINAL ANSWER")
        print("=" * 70)
        print(result['Answer'])
        print("=" * 70 + "\n")

        return result['Answer']


# Example usage
if __name__ == "__main__":
    agent = RAGAgent()

    # Test
    print("\n🇸🇦 Testing Arabic question:")
    agent.ask("ما أهم المناطق التاريخية في مدينة غزة؟")