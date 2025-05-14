import os
import PyPDF2
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
FEEDBACK_MODE = False   
def write_feedback(user_name, feedback_text):
    with open("feedback.txt", "a") as f:
        f.write(f"{user_name} says the session was: {feedback_text}\n")

FEEDBACK_STATE = {}
documents_path = 'data/' 
os.listdir(documents_path)

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

folder_path = documents_path
documents = load_documents_from_folder(folder_path)
documents.extend(load_documents_from_folder('data/resumes'))

print(f"Loaded {len(documents)} documents")
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


embedder = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text, chunk_size=300):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

chunks = []
chunk_sources = []

for doc in documents:
    for chunk in chunk_text(doc):
        chunks.append(chunk)
        chunk_sources.append(chunk) 

embeddings = embedder.encode(chunks, convert_to_numpy=True)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
import google.generativeai as genai

genai.configure(api_key=api_key) 
model = genai.GenerativeModel("gemini-1.5-flash")
def retrieve_relevant_chunks(query, k=3):
    query_embedding = embedder.encode([query])
    D, I = index.search(np.array(query_embedding), k)
    return [chunk_sources[i] for i in I[0]]

def generate_rag_response(query, user_id=None, user_input=None):
    global FEEDBACK_MODE

    if FEEDBACK_MODE:
        # Expect format: "Name: Feedback"
        try:
            name, feedback = user_input.split(":", 1)
            name = name.strip()
            feedback = feedback.strip()
            write_feedback(name, feedback)
            return f"✅ Thank you, {name}! Your feedback has been recorded."
        except ValueError:
            return "📝 What did you think of this session? Please include your name like this:\n\n**Your Name: Your feedback**"

    # If feedback mode is off, handle normal RAG
    context = "\n".join(retrieve_relevant_chunks(query))
    print("new\n")
    print(f"Context: {context}")
    prompt = f"Based on the following context:\n{context}\n\nAnswer the question: {query}"
    response = model.generate_content(prompt)
    return response.text


def is_feedback_mode():
    return FEEDBACK_MODE