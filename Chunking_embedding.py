import faiss
import pickle
from glob import glob
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import re

# --- Configuration ---
INDEX_NAME = "global_heritage.index"
METADATA_NAME = "global_heritage_metadata.pkl"
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2' # Suitable for EN and AR
# ---

# 1. Define the exact files to process
FILES_TO_PROCESS = [
    "Dataset/_ALL_ARAB_HERITAGE_EN.txt",
    "Dataset/_ALL_ARAB_HERITAGE_AR.txt"
]

# Load model and text splitter
print(f"Loading model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Initialize FAISS Index and lists (Dimension: 768 for the selected model)
index = faiss.IndexFlatL2(768)
chunks = []
metadata = []

print(f"Found {len(FILES_TO_PROCESS)} global files to process.\n")

for file in FILES_TO_PROCESS:
    if not os.path.exists(file):
        print(f"⚠️ Warning: File not found: {file}. Skipping.")
        continue

    print(f"Processing: {file}")

    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 2. Extract Language from the filename
    if '_EN.txt' in file:
        language = "English"
        language_code = "EN"
    elif '_AR.txt' in file:
        language = "Arabic"
        language_code = "AR"
    else:
        language = "Unknown"
        language_code = "UN"

    # Split the entire consolidated file into chunks
    file_chunks = text_splitter.split_text(text)
    
    # 3. Encode and add to FAISS
    vector_list = model.encode(file_chunks)
    index.add(vector_list)

    for chunk in file_chunks:
        chunks.append(chunk)
        # Simplified metadata: only includes language
        metadata.append({'language': language, 'source_file': os.path.basename(file)})

    print(f"    Added {len(file_chunks)} chunks for {language} ({language_code}).")
    print(f"    Total chunks indexed so far: {len(chunks)}\n")

# 4. Save the index and metadata
faiss.write_index(index, INDEX_NAME)
with open(METADATA_NAME, 'wb') as f:
    pickle.dump({'chunks': chunks, 'metadata': metadata}, f)

print(f"✅ DONE! Saved {len(chunks)} total chunks to FAISS index: {INDEX_NAME}")