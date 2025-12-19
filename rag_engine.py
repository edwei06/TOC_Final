import os
import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import hashlib

# ==========================================
# [設定區]
# ==========================================
DB_PATH = "./chroma_db"  # 資料庫存在本地，實現持久化
COLLECTION_NAME = "blockchain_knowledge"
DOC_FOLDER = "documents"

class BlockchainRAG:
    def __init__(self):
        print("📚 [RAG] 初始化知識庫引擎...")
        
        # 1. 初始化 Embedding 模型 (使用輕量級模型)
        # 'all-MiniLM-L6-v2' 速度快，支援中英文，非常適合專題
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. 初始化 ChromaDB (PersistentClient 會把資料存到硬碟)
        self.client = chromadb.PersistentClient(path=DB_PATH)
        
        # 取得或建立 Collection
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        
        # 3. 自動檢查並載入文件
        self._ingest_documents()

    def _ingest_documents(self):
        """
        讀取 documents 資料夾，將新檔案切塊並存入向量資料庫
        """
        if not os.path.exists(DOC_FOLDER):
            os.makedirs(DOC_FOLDER)
            print(f"⚠️ 建立 {DOC_FOLDER} 資料夾，請放入 PDF 或 TXT 文件。")
            return

        # 取得目前 DB 裡已經有的檔案 ID (避免重複讀取)
        existing_ids = self.collection.get()['ids']
        existing_hashes = set([id.split('_')[0] for id in existing_ids]) # 簡單用檔名hash判斷

        print(f"📂 [RAG] 掃描文件資料夾: {DOC_FOLDER}")
        
        for filename in os.listdir(DOC_FOLDER):
            file_path = os.path.join(DOC_FOLDER, filename)
            
            # 產生簡單的 file hash (這裡用檔名代替，正式專案可用 content hash)
            file_hash = hashlib.md5(filename.encode()).hexdigest()
            
            if file_hash in existing_hashes:
                # print(f" - {filename} 已存在，跳過。")
                continue
            
            print(f"   👉 發現新文件，正在處理: {filename} ...")
            
            # 讀取文字內容
            text_content = ""
            if filename.endswith(".pdf"):
                text_content = self._read_pdf(file_path)
            elif filename.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            else:
                continue # 跳過不支援的格式

            if not text_content: continue

            # 切塊 (Chunking)
            chunks = self._chunk_text(text_content, chunk_size=400, overlap=50)
            
            # 準備寫入 DB
            ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "chunk_id": i} for i in range(len(chunks))]
            embeddings = self.embed_model.encode(chunks).tolist()

            self.collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"   ✅ 已存入 {len(chunks)} 個片段。")

    def _read_pdf(self, path):
        """讀取 PDF 文字"""
        try:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"❌ PDF 讀取失敗 {path}: {e}")
            return ""

    def _chunk_text(self, text, chunk_size=400, overlap=50):
        """
        簡單的滑動視窗切塊 (Sliding Window Chunking)
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # 簡單清理換行符號，讓語意更連貫
            chunk = chunk.replace('\n', ' ')
            chunks.append(chunk)
            
            # 移動視窗 (重疊 overlap)
            start += (chunk_size - overlap)
            
        return chunks

    def search(self, query, top_k=3):
        """
        核心功能：給定問題，找回最相關的 k 個片段
        """
        query_vec = self.embed_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_vec,
            n_results=top_k
        )
        
        # 整理回傳格式
        retrieved_data = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                retrieved_data.append(f"【來源: {meta['source']}】\n{doc}")
                
        return "\n\n".join(retrieved_data)

# 測試用
if __name__ == "__main__":
    rag = BlockchainRAG()
    # 測試搜尋
    print("\n🔍 測試搜尋: '比特幣的運作原理'")
    print(rag.search("比特幣的運作原理", top_k=2))