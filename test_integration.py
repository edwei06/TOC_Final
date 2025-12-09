import time
import json
import requests
import re
from blockchain_tools import get_wallet_history

# ==========================================
# [設定區]
# ==========================================
API_KEY = "06d03eff510e2f734bcc806f20b892a5703c7820c13114e77af46ac56d658cf6"  # 請填入你的 Key
OLLAMA_API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
MODEL_NAME = "gpt-oss:20b"

# Vitalik 的錢包 (確保有資料)
TEST_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" 
# ==========================================

def stream_llm_response(prompt, system_prompt):
    """
    獨立的測試函式，用來精準控制 Timeout 與觀察延遲
    """
    full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": True,  # 開啟串流
        "options": {
            "temperature": 0.7
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    print(f"\n🚀 [LLM] 開始發送請求... (Timeout 設定為 120秒)")
    start_time = time.time()
    
    try:
        # 重點：timeout=120，給伺服器 2 分鐘的時間準備第一個字
        with requests.post(OLLAMA_API_URL, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            
            print(f"✅ [LLM] 連線建立成功！(耗時: {time.time() - start_time:.2f} 秒)")
            print("📝 [LLM] 開始接收回應 (Streaming):")
            print("-" * 50)

            first_token_received = False
            token_count = 0 
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_obj = json.loads(decoded_line)
                        chunk = json_obj.get("response", "")
                        
                        if chunk:
                            if not first_token_received:
                                first_token_time = time.time() - start_time
                                print(f"\n[數據] 收到第一個字耗時: {first_token_time:.2f} 秒\n")
                                first_token_received = True
                            
                            # 修改這裡：每收到 5 個字就換行印時間，證明它是活的
                            token_count += 1
                            print(chunk, end='', flush=True)
                            
                            # Debug 用：觀察是不是真的在流動 (會破壞排版，但能驗證機制)
                            print(f"[{time.time():.2f}]", end='', flush=True) 
                        if json_obj.get("done", False):
                            print("\n\n" + "-" * 50)
                            print("✅ [LLM] 回應結束")
                            break
                    except ValueError:
                        continue
    except requests.exceptions.Timeout:
        print("\n❌ [Timeout] 伺服器超過 120 秒沒有回應任何數據。伺服器可能過載。")
    except Exception as e:
        print(f"\n❌ [Error] 發生錯誤: {str(e)}")

def run_integration_test():
    print("=" * 50)
    print("🛠️  開始整合測試：Etherscan API + LLM Stream")
    print("=" * 50)

    # --- 步驟 1: 取得鏈上數據 ---
    print(f"\n1️⃣  正在呼叫 Etherscan API 查詢: {TEST_ADDRESS} ...")
    chain_data = get_wallet_history(TEST_ADDRESS)
    
    # 檢查是否拿到錯誤
    if "error" in chain_data:
        print(f"❌ Etherscan 錯誤: {chain_data['error']}")
        return

    # 將資料轉成 JSON 字串 (模擬傳給 LLM 的樣子)
    data_str = json.dumps(chain_data, ensure_ascii=False, indent=2)
    print(f"✅ 取得數據成功！資料長度: {len(data_str)} 字元")
    # print(data_str) # 如果想看詳細資料可以打開這行

    # --- 步驟 2: 組裝 Prompt ---
    print("\n2️⃣  正在組裝 Prompt ...")
    user_prompt = (
        f"使用者查詢地址 {TEST_ADDRESS}。\n"
        f"這是從 Etherscan 抓取的真實數據：\n{data_str}\n\n"
        f"任務：\n"
        f"1. 告訴使用者這個錢包現在餘額有多少 ETH。\n"
        f"2. 簡單總結最近一筆交易的時間與行為。\n"
        f"3. 這是 Vitalik (以太坊創辦人) 的錢包，請在分析中加入這個背景知識。"
    )
    
    system_prompt = "你是一個區塊鏈數據分析師，請用繁體中文回答。"
    
    print(f"Prompt 預覽:\n---Start---\n{user_prompt[:150]}...\n(省略中間數據)...\n---End---")

    # --- 步驟 3: 呼叫 LLM ---
    print("\n3️⃣  呼叫 LLM 進行分析 ...")
    stream_llm_response(user_prompt, system_prompt)

if __name__ == "__main__":
    run_integration_test()