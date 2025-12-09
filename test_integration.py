import time
import json
import requests
import re
from blockchain_tools import get_wallet_portfolio
# ==========================================
# [設定區]
# ==========================================
API_KEY = "06d03eff510e2f734bcc806f20b892a5703c7820c13114e77af46ac56d658cf6"  # 請填入你的 Key
OLLAMA_API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
MODEL_NAME = "gpt-oss:20b"

# 測試用 Vitalik 的錢包 (資產豐富，適合測試 Moralis)
TEST_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
TEST_ADDRESS = "0x0ADA3111B866fF1aD0477F0C5D2e8eD35A36Eb5b"
def stream_llm_response(prompt):
    full_prompt = f"System: 你是一個華爾街等級的加密貨幣資產分析師，請根據提供的真實數據進行分析。\nUser: {prompt}\nAssistant:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": True,
        "options": {"temperature": 0.3} # 降低溫度，讓數學計算準一點
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    print(f"\n🚀 [LLM] 開始分析資產配置... (Timeout: 120s)")
    
    try:
        with requests.post(OLLAMA_API_URL, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    try:
                        json_obj = json.loads(decoded)
                        chunk = json_obj.get("response", "")
                        if chunk:
                            print(chunk, end='', flush=True)
                    except: pass
            print("\n\n✅ 完成")
    except Exception as e:
        print(f"❌ LLM Error: {e}")

def run_moralis_test():
    print("=" * 60)
    print("🛠️  Moralis API (Value Sorted) + Integration Test")
    print("=" * 60)

    # 1. 呼叫 Moralis
    print(f"\n1️⃣  正在透過 Moralis 掃描鏈上資產: {TEST_ADDRESS} ...")
    portfolio_data = get_wallet_portfolio(TEST_ADDRESS)
    
    if "error" in portfolio_data:
        print(f"❌ Error: {portfolio_data['error']}")
        return

    # 2. [Debug] 輸出前 3 名資產確認排序正確
    print("\n🧐 [DEBUG] 確認排序結果 (Top 3):")
    for i, asset in enumerate(portfolio_data['portfolio'][:3]):
        print(f"   #{i+1} {asset['symbol']}: ${asset['value_usd']:,.2f}")

    # 3. 準備 Prompt
    assets_str = ""
    for item in portfolio_data.get("portfolio", []):
        assets_str += (
            f"- {item['symbol']}: 數量 {item['balance']:.2f}, "
            f"總價值 ${item['value_usd']:.2f} USD\n"
        )
    
    total_worth = portfolio_data.get("total_net_worth_usd", 0)

    print("\n2️⃣  正在組裝 Prompt ...")
    user_prompt = (
        f"請分析以下以太坊錢包的資產配置。\n"
        f"【總資產淨值】: ${total_worth:,.2f} USD\n\n"
        f"【前十大持倉資產】:\n{assets_str}\n\n"
        f"【任務】:\n"
        f"1. 製作資產分佈 Markdown 表格（幣種、價值、佔比）。\n"
        f"2. [資安檢測]：Vitalik 的錢包常收到詐騙空投。如果你在清單中看到非主流的可疑代幣（例如名字很奇怪、且價值異常高的幣），請在分析中特別標註為「高風險/疑似詐騙空投」，並提醒使用者不要隨意互動。\n"
        f"3. 分析此人的真實投資風格（排除掉那些疑似詐騙幣後）。"
    )

    # 4. 呼叫 LLM
    stream_llm_response(user_prompt)

if __name__ == "__main__":
    run_moralis_test()