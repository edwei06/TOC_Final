import chromadb
from sentence_transformers import SentenceTransformer
import os

# 初始化 Embedding 模型 (會下載一個小模型到本地)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
# 初始化 ChromaDB Client
client = chromadb.Client()
collection = client.create_collection(name="blockchain_knowledge")

def load_documents(doc_folder="documents"):
    """
    讀取資料夾內的 txt 檔案並存入向量資料庫
    """
    ids = []
    documents = []
    metadatas = []
    
    for filename in os.listdir(doc_folder):
        if filename.endswith(".txt"):
            path = os.path.join(doc_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # 簡單切分段落 (可改進)
                chunks = content.split("\n\n") 
                for i, chunk in enumerate(chunks):
                    if len(chunk) > 50:
                        ids.append(f"{filename}_{i}")
                        documents.append(chunk)
                        metadatas.append({"source": filename})
    
    if documents:
        # 轉向量並存入 DB
        embeddings = embed_model.encode(documents).tolist()
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        print(f"Loaded {len(documents)} chunks into RAG.")

def search_knowledge(query, n_results=2):
    """
    搜尋最相關的文件
    """
    query_embed = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embed, n_results=n_results)
    
    # 整理回傳文字
    context_text = "\n".join(results['documents'][0])
    return context_text

# 第一次執行時載入
# load_documents()