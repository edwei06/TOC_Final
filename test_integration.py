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
    full_prompt = f"System: 分析師模式。\nUser: {prompt}\nAssistant:"
    payload = {
        "model": MODEL_NAME, "prompt": full_prompt, "stream": True, "options": {"temperature": 0.3}
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    print(f"\n🚀 [LLM] 開始分析多鏈資產... (Timeout: 120s)")
    try:
        with requests.post(OLLAMA_API_URL, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    try:
                        json_obj = json.loads(decoded)
                        chunk = json_obj.get("response", "")
                        if chunk: print(chunk, end='', flush=True)
                    except: pass
            print("\n\n✅ 完成")
    except Exception as e:
        print(f"❌ LLM Error: {e}")

def run_multichain_test():
    print("=" * 60)
    print("🛠️  Multi-Chain (7 Chains) Integration Test")
    print("=" * 60)

    start_t = time.time()
    print(f"\n1️⃣  正在平行掃描 7 條公鏈: {TEST_ADDRESS} ...")
    portfolio_data = get_wallet_portfolio(TEST_ADDRESS)
    
    print(f"⏱️  API 掃描耗時: {time.time() - start_t:.2f} 秒") # 觀察平行處理效果

    if "error" in portfolio_data:
        print(f"❌ Error: {portfolio_data['error']}")
        return

    # Debug: 顯示各鏈分佈
    print("\n📊 [DEBUG] 各鏈資產分佈:")
    for chain, val in portfolio_data['chain_stats'].items():
        if val > 100: # 只顯示大於 100 鎂的
            print(f"   - {chain}: ${val:,.2f}")

    # 組裝 Prompt
    assets_str = ""
    for item in portfolio_data.get("portfolio", []):
        assets_str += (f"- [{item['chain']}] {item['symbol']}: 價值 ${item['value_usd']:.2f}\n")
    
    total_worth = portfolio_data.get("total_net_worth_usd", 0)
    
    print("\n2️⃣  呼叫 LLM 分析 ...")
    user_prompt = (
        f"分析錢包 {TEST_ADDRESS}。\n總資產: ${total_worth:,.2f}\n"
        f"前 20 大持倉:\n{assets_str}\n"
        f"請分析其跨鏈資產配置與投資風格。"
    )
    
    stream_llm_response(user_prompt)

if __name__ == "__main__":
    run_multichain_test()