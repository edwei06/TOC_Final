import requests
import json

# ==========================================
# [設定區] 請填入助教提供的資訊
# ==========================================

# 1. 你的 API Key (不要有空格)
API_KEY = "06d03eff510e2f734bcc806f20b892a5703c7820c13114e77af46ac56d658cf6" 

# 2. API 完整網址
# 注意：如果這是 Ollama 原生介面，通常結尾是 /api/generate 或 /api/chat
# 如果助教有改過路徑，請參照文件。我們先假設是標準 Ollama 路徑：
URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"

# 3. 模型名稱
MODEL_NAME = "gpt-oss:120b"

# ==========================================
def test_streaming():
    print(f"🔄 測試串流模式 (Streaming)...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "prompt": "你好，簡單自我介紹一下。", # 問個短一點的
        "stream": True  # <--- 開啟串流
    }

    try:
        # stream=True 允許我們分段接收資料
        response = requests.post(URL, json=payload, headers=headers, stream=True, timeout=30)
        
        print(f"📡 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 連線成功！正在接收回應：\n")
            print("-" * 30)
            
            # 逐行讀取回應
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_obj = json.loads(decoded_line)
                        # 印出片段文字，end='' 讓它不換行，看起來像打字機
                        chunk = json_obj.get("response", "")
                        print(chunk, end='', flush=True)
                        
                        if json_obj.get("done", False):
                            print("\n\n[完成]")
                            break
                    except:
                        pass
            print("-" * 30)
        else:
            print(f"❌ 錯誤: {response.text}")

    except Exception as e:
        print(f"\n💥 錯誤: {str(e)}")

if __name__ == "__main__":
    test_streaming()
def test_connection():
    print(f"🔄 正在嘗試連線到: {URL}")
    print(f"🔑 使用的模型: {MODEL_NAME}")
    
    # 設定 Headers (這是最關鍵的部分)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"  # 大多數 API Gateway 用這種格式
        # 如果失敗，可以試試看換成: "X-API-KEY": API_KEY
    }

    # 測試用的 Payload
    payload = {
        "model": MODEL_NAME,
        "prompt": "你好，請回應這是一個測試。",
        "stream": False
    }

    try:
        # 發送請求
        response = requests.post(URL, json=payload, headers=headers, timeout=10)
        
        # 印出狀態碼
        print(f"\n📡 HTTP 狀態碼: {response.status_code}")
        
        # 檢查是否成功 (200 OK)
        if response.status_code == 200:
            print("✅ 連線成功！伺服器回應：")
            try:
                data = response.json()
                # 試著印出回應內容，Ollama 通常在 'response' 欄位
                print(data.get("response", data)) 
            except:
                print(response.text)
        else:
            print("❌ 連線失敗。詳細錯誤內容：")
            print(response.text)
            
            # 常見錯誤提示
            if response.status_code == 403:
                print("\n[!] 403 Forbidden: 通常是 API Key 錯誤，或 Key 沒有權限。")
            elif response.status_code == 404:
                print("\n[!] 404 Not Found: 網址路徑錯了。可能是 /api/generate 或 /v1/chat/completions？")
            elif response.status_code == 401:
                print("\n[!] 401 Unauthorized: Header 格式錯誤，可能是 'Bearer ' 前綴的問題。")

    except Exception as e:
        print(f"\n💥 發生程式錯誤: {str(e)}")
def get_available_models():
    # Ollama 標準列出模型的路徑是 /api/tags
    url = f"{URL}/api/tags"
    
    print(f"🔍 正在查詢可用模型清單: {url}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📡 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ 成功！伺服器支援以下模型：")
            # Ollama 回傳格式通常是 {"models": [{"name": "llama3:latest"}, ...]}
            if "models" in data:
                for model in data["models"]:
                    print(f" - {model['name']}")
            else:
                print("格式與預期不同，原始回傳資料：")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ 無法取得清單。")
            print(response.text)

    except Exception as e:
        print(f"💥 發生錯誤: {str(e)}")
if __name__ == "__main__":
    # test_connection()
    # get_available_models()
    test_streaming()
#