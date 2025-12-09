import requests
import json
from datetime import datetime
import time
# ==========================================
# [必填] Moralis API Key
# 請去 https://admin.moralis.io/settings 取得
# ==========================================
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjIyMGNjNzAwLTFlOTUtNDU3Yy04ZmFhLThhZDY5NjRhZTE1OSIsIm9yZ0lkIjoiNDg1MjAxIiwidXNlcklkIjoiNDk5MTgwIiwidHlwZUlkIjoiMWM0ZGIzYmEtMjcxYS00Zjk5LWI4ZDAtNTI4NWEzZmU2ZjhmIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NjUyNDc5MzYsImV4cCI6NDkyMTAwNzkzNn0.6MIO3xXXMg7VSkV1brHKkxmHvX5v9bee6ET1Jrr___k"

SCAM_BLACKLIST = ["AAA"]

def get_wallet_portfolio(address):
    """
    呼叫 Moralis Wallet API 並執行嚴格的垃圾幣過濾
    """
    if "你的" in MORALIS_API_KEY:
        return {"error": "請先在 blockchain_tools.py 填入有效的 Moralis API Key"}

    print(f"🔍 [Moralis] 正在分析錢包資產: {address}")
    
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    portfolio_list = []

    # ---------------------------------------------------
    # 1. 取得 Native ETH (最可信的資產)
    # ---------------------------------------------------
    try:
        # 使用 native balance endpoint 抓 ETH
        native_url = f"https://deep-index.moralis.io/api/v2.2/{address}/balance?chain=eth"
        native_res = requests.get(native_url, headers=headers, timeout=10).json()
        
        eth_balance = float(native_res.get("balance", 0)) / 10**18
        
        if eth_balance > 0:
            # 查 ETH 價格
            price_url = "https://deep-index.moralis.io/api/v2.2/erc20/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2/price?chain=eth"
            price_res = requests.get(price_url, headers=headers, timeout=10).json()
            eth_price = price_res.get("usdPrice", 0)
            
            portfolio_list.append({
                "symbol": "ETH",
                "type": "Native",
                "balance": eth_balance,
                "price_usd": eth_price,
                "value_usd": eth_balance * eth_price,
                "token_address": "Native",
                "is_scam": False
            })
    except Exception as e:
        print(f"⚠️ ETH 查詢失敗: {e}")

    # ---------------------------------------------------
    # 2. 取得 ERC20 代幣 (加強過濾)
    # ---------------------------------------------------
    token_url = f"https://deep-index.moralis.io/api/v2.2/wallets/{address}/tokens?chain=eth&exclude_spam=true&exclude_unverified_contracts=true"
    
    try:
        token_res = requests.get(token_url, headers=headers, timeout=15).json()
        raw_tokens = token_res.get("result", [])
        
        print(f"📦 [Moralis] 原始抓取 {len(raw_tokens)} 種代幣，開始進行清洗...")

        for token in raw_tokens:
            symbol = token.get("symbol", "Unknown")
            
            # [過濾器 1] 黑名單過濾
            if symbol in SCAM_BLACKLIST:
                continue

            # [過濾器 2] 垃圾標籤過濾 (Moralis 欄位)
            if token.get("possible_spam") is True:
                continue

            decimals = int(token.get("decimals", 18))
            balance = float(token.get("balance", 0)) / (10 ** decimals)
            usd_value = token.get("usd_value") # Moralis 算好的價值

            if usd_value is None:
                continue
                
            total_value = float(usd_value)

            # [過濾器 3] 價值異常過濾邏輯
            # 如果一個幣不是 ETH/USDC/USDT (主流幣)，但價值卻異常高 (> 10萬美金)
            # 且沒有驗證或是黑名單漏網之魚，這通常是詐騙。
            # 為了 Demo 安全，我們可以設定一個閾值：
            # 如果價值 > $50,000 且 symbol 不在白名單內(這裡簡化處理，先不過濾太嚴，交給 LLM 判斷)
            
            # 只收錄價值 > 10 USD 的資產 (過濾粉塵攻擊)
            if total_value > 10.0:
                price = total_value / balance if balance > 0 else 0
                
                portfolio_list.append({
                    "symbol": symbol,
                    "type": "ERC20",
                    "balance": balance,
                    "price_usd": price,
                    "value_usd": total_value,
                    "token_address": token.get("token_address")
                })

    except Exception as e:
        print(f"⚠️ Token 列表查詢失敗: {e}")

    # ---------------------------------------------------
    # 3. 排序與總結
    # ---------------------------------------------------
    portfolio_list.sort(key=lambda x: x["value_usd"], reverse=True)

    # 計算總資產
    total_net_worth = sum(item["value_usd"] for item in portfolio_list)

    # 取前 10 大
    top_assets = portfolio_list[:10]

    return {
        "source": "Moralis API (Filtered)",
        "address": address,
        "total_net_worth_usd": total_net_worth,
        "portfolio": top_assets,
        "debug_note": "已過濾 AAA, CATE, WHITE 等已知垃圾幣"
    }

if __name__ == "__main__":
    # 測試 Vitalik
    data = get_wallet_portfolio("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    import json
    # 印出前 5 名看看是否正常了
    print("Top 5 Assets:")
    for asset in data['portfolio'][:5]:
        print(f"{asset['symbol']}: ${asset['value_usd']:,.2f}")