import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from langchain_ollama import OllamaLLM
from transformers import pipeline


class AgentState(TypedDict):
    question: str
    Answer: str
    docs: list[str]
    historical_questions: list[str]
    language: str


class RAGAgent:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device='cuda')

        # Language detection model
        self.language_detector = pipeline(
            "text-classification",
            model="papluca/xlm-roberta-base-language-detection"
        )

        # Language-specific indices and data
        self.indices = {}
        self.chunks_dict = {}
        self.metadata_dict = {}

        # Load Arabic index
        self.load_index("arabic", "heritage_arabic.index", "heritage_AR.pkl")

        # Load English index
        self.load_index("english", "heritage_english.index", "heritage_EN.pkl")

        self.llm = OllamaLLM(model="aya-expanse:8b")
        self.app = self.build_graph()

    def load_index(self, language: str, index_file: str, pkl_file: str):
        """Load FAISS index and pickle data for a specific language"""
        try:
            self.indices[language] = faiss.read_index(index_file)

            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
                self.chunks_dict[language] = data['chunks']
                self.metadata_dict[language] = data['metadata']

            print(f"✅ Loaded {language} index with {len(self.chunks_dict[language])} chunks")
        except Exception as e:
            print(f"⚠️  Warning: Could not load {language} index: {e}")
            self.indices[language] = None
            self.chunks_dict[language] = []
            self.metadata_dict[language] = []

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        try:
            result = self.language_detector(text)[0]
            detected_lang = result['label']
            confidence = result['score']

            print(f"🔍 Detected language: {detected_lang} (confidence: {confidence:.2f})")

            # Map detected language to our supported languages
            if detected_lang == 'ar':
                return 'arabic'
            elif detected_lang == 'en':
                return 'english'
            else:
                print(f"⚠️  Language '{detected_lang}' not supported. Defaulting to English.")
                return 'unsupported'

        except Exception as e:
            print(f"❌ Error detecting language: {e}")
            return 'unsupported'

    def retriever_node(self, state: AgentState):
        print("---NODE: RETRIEVE---")

        language = state['language']

        # Check if language is supported
        if language == 'unsupported':
            return {
                'question': state['question'],
                'Answer': 'Sorry, only Arabic and English are supported.',
                'docs': [],
                'historical_questions': state['historical_questions'],
                'language': language
            }

        # Check if index exists for this language
        if language not in self.indices or self.indices[language] is None:
            return {
                'question': state['question'],
                'Answer': f'Sorry, {language} index is not available.',
                'docs': [],
                'historical_questions': state['historical_questions'],
                'language': language
            }

        # Retrieve from language-specific index
        query_vector = self.model.encode([state['question']])
        distances, indices = self.indices[language].search(query_vector, 10)
        context_chunks = [self.chunks_dict[language][idx] for idx in indices[0]]

        return {
            'question': state['question'],
            'Answer': state.get('Answer', ''),
            'docs': context_chunks,
            'historical_questions': state['historical_questions'],
            'language': language
        }

    def grader_docs_node(self, state: AgentState):
        print("---NODE: GRADE DOCUMENTS---")
        question = state['question']
        docs = state['docs']
        language = state['language']

        # Language-specific grading prompt
        if language == 'arabic':
            prompt_template = """أنت مُقيّم. مهمتك هي التحقق مما إذا كانت الوثيقة المسترجعة ذات صلة بسؤال المستخدم.
أجب بكلمة واحدة فقط: 'yes' إذا كانت ذات صلة، 'no' إذا لم تكن كذلك.

الوثيقة: {document}
السؤال: {question}

الإجابة:"""
        else:
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
            'language': language
        }

    def generate_node(self, state: AgentState):
        print("---NODE: GENERATE---")
        question = state["question"]
        documents = state["docs"]
        language = state["language"]

        # Language-specific generation prompt
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

        # Language-specific rewriting prompt
        if language == 'arabic':
            prompt_template = """أنت مُعيد صياغة الاستعلامات. أعد صياغة السؤال التالي ليصبح
استعلام بحث موجز ومحدد لقاعدة بيانات متجهية.
قدم فقط الاستعلام المُعاد صياغته، لا شيء آخر.

السؤال الأصلي: {question}

الاستعلام المُعاد صياغته:"""
        else:
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
            "historical_questions": historical_questions,
            "language": language
        }

    def decision_node(self, state: AgentState):
        print("---NODE: DECISION---")

        # If language is unsupported, end immediately
        if state['language'] == 'unsupported':
            print("  -> Decision: END (unsupported language)")
            return "end"

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
        # Detect language first
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

