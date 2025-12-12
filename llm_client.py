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
MODEL_NAME = "gemma3:4b" 

def query_llm_stream(prompt, system_prompt=""):
    """
    使用串流 (Streaming) 模式呼叫 LLM。
    """
    full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "temperature": 0.7 
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        # Timeout 設定為 120 秒，避免排隊時斷線
        with requests.post(OLLAMA_API_URL, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_obj = json.loads(decoded_line)
                        chunk = json_obj.get("response", "")
                        
                        # 有內容就 yield 出去
                        if chunk:
                            yield chunk
                            
                        if json_obj.get("done", False):
                            break
                    except ValueError:
                        continue
    except Exception as e:
        yield f"Error: {str(e)}"