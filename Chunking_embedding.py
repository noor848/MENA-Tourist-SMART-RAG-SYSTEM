import faiss
import pickle
from glob import glob
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Load model
print("Loading model...")
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

index = faiss.IndexFlatL2(768)
chunks = []
metadata = []

files = glob("arab_heritage_by_country/*/_COMPLETE_*.txt")
print(f"Found {len(files)} files\n")

for file in files:
    print(f"Processing: {file}")

    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()

    country = file.split('_COMPLETE_')[1].replace('.txt', '').replace('_', ' ').title()

    file_chunks = text_splitter.split_text(text)

    for chunk in file_chunks:
        vector = model.encode([chunk])
        index.add(vector)
        chunks.append(chunk)
        metadata.append({'country': country})

    print(f"  Added {len(file_chunks)} chunks\n")

faiss.write_index(index, "heritage.index")
with open("heritage.pkl", 'wb') as f:
    pickle.dump({'chunks': chunks, 'metadata': metadata}, f)

print(f"✅ DONE! Saved {len(chunks)} chunks to FAISS")