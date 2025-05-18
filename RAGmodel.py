import os
import pickle
import PyPDF2
from dotenv import load_dotenv
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# === Feedback System ===
FEEDBACK_MODE = False
FEEDBACK_STATE = {}

def write_feedback(user_name, feedback_text):
    with open("feedback.txt", "a") as f:
        f.write(f"{user_name} says the session was: {feedback_text}\n")

# === Document Loader ===
def load_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if filename.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as file:
                documents.append(file.read())

        elif filename.endswith(".pdf"):
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                documents.append(text)
    return documents

# === Load and Chunk Data ===
documents_path = 'data/'
documents = load_documents_from_folder(documents_path)
documents.extend(load_documents_from_folder(os.path.join(documents_path, 'resumes')))

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, chunk_size=300):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

# === Load or Build FAISS Index ===
if os.path.exists("faiss_index.index") and os.path.exists("chunks.pkl"):
    index = faiss.read_index("faiss_index.index")
    with open("chunks.pkl", "rb") as f:
        chunk_sources = pickle.load(f)
    print("✅ Loaded prebuilt FAISS index and chunks.")
else:
    print("🔄 Building FAISS index from scratch...")
    chunks = []
    chunk_sources = []
    for doc in documents:
        for chunk in chunk_text(doc):
            chunks.append(chunk)
            chunk_sources.append(chunk)

    embeddings = embedder.encode(chunks, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, "faiss_index.index")
    with open("chunks.pkl", "wb") as f:
        pickle.dump(chunk_sources, f)
    print("✅ Index built and saved.")

# === Generative Model Setup ===
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

def retrieve_relevant_chunks(query, k=3):
    query_embedding = embedder.encode([query])
    D, I = index.search(np.array(query_embedding), k)
    return [chunk_sources[i] for i in I[0]]

# === Main Response Function ===
def generate_rag_response(query, user_id=None, user_input=None):
    global FEEDBACK_MODE

    if FEEDBACK_MODE:
        # Feedback handling code remains the same
        try:
            name, feedback = user_input.split(":", 1)
            name = name.strip()
            feedback = feedback.strip()
            write_feedback(name, feedback)
            return f"✅ Thank you, {name}! Your feedback has been recorded."
        except ValueError:
            return "📝 What did you think of this session? Please include your name like this:\n\n**Your Name: Your feedback**"

    # Enhanced RAG mode with improved prompt
    context = "\n".join(retrieve_relevant_chunks(query))
    
    prompt = f"""You are EventBro, an enthusiastic and knowledgeable assistant for the AI Workshop. 
    Your goal is to provide helpful, accurate information about the workshop in a friendly and engaging way.

    CONTEXT INFORMATION:
    {context}

    USER QUERY: {query}

    Please follow these guidelines:
    1. Answer based ONLY on the context provided. If the information isn't in the context, say you don't have that specific information.
    2. Be concise and to the point, but also warm and approachable,Avoid unnecessary greeting
    3. Use a conversational tone with occasional emoji where appropriate.
    4. If asked about schedule details, speaker information, or workshop content, highlight the most relevant points.
    5. For technical questions, provide clear explanations without unnecessary jargon.
    6. If someone asks where to find something at the workshop, give specific directions if available in the context.
    7. Always be helpful and positive about the workshop experience.

    If you don't know the answer or if the context doesn't contain relevant information, politely say so and suggest the person check with workshop staff or the official program.
    """
    
    response = model.generate_content(prompt)
    return response.text

def is_feedback_mode():
    return FEEDBACK_MODE
