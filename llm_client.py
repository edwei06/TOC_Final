import requests
import json

# ==========================================
# [必填] 請在此填入助教提供的連線資訊
# ==========================================
# 1. 教授 Server 的 IP (或是完整 URL，看助教給的文件)
OLLAMA_API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate" 

# 2. 你的 API Key
API_KEY = "06d03eff510e2f734bcc806f20b892a5703c7820c13114e77af46ac56d658cf6"

# 3. 指定的模型名稱 (確認助教指定的是不是這個名字)
MODEL_NAME = "gpt-oss:120b" 
# ==========================================
def query_llm(prompt, system_prompt=""):
    """
    發送請求給學校 API。
    為了讓 Agent 邏輯好寫，這裡暫時使用 stream=False (一次回傳)，
    並設定較長的 timeout 等待大模型運算。
    """
    full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,  # Agent 邏輯需要完整字串，先不開串流
        "options": {
            "temperature": 0.7 
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        # 設定 timeout=120 (兩分鐘)，避免大模型算太久報錯
        response = requests.post(
            OLLAMA_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.Timeout:
        return "錯誤：模型回應超時 (Timeout)。請稍後再試，或告知助教模型負載過高。"
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"

# 測試用
if __name__ == "__main__":
    print("正在測試正式 client...")
    print(query_llm("你好，請簡短回答這是不是正式連線？"))