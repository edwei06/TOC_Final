import requests
import json
from datetime import datetime
import time
import requests
import concurrent.futures # 用於平行處理
from functools import partial
# ==========================================
# [必填] Moralis API Key
# 請去 https://admin.moralis.io/settings 取得
# ==========================================
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjIyMGNjNzAwLTFlOTUtNDU3Yy04ZmFhLThhZDY5NjRhZTE1OSIsIm9yZ0lkIjoiNDg1MjAxIiwidXNlcklkIjoiNDk5MTgwIiwidHlwZUlkIjoiMWM0ZGIzYmEtMjcxYS00Zjk5LWI4ZDAtNTI4NWEzZmU2ZjhmIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NjUyNDc5MzYsImV4cCI6NDkyMTAwNzkzNn0.6MIO3xXXMg7VSkV1brHKkxmHvX5v9bee6ET1Jrr___k"

SCAM_BLACKLIST = ["AAA"]
# 定義我們要支援的公鏈 (Moralis chain ID mapping)
SUPPORTED_CHAINS = {
    "eth": "Ethereum",
    "bsc": "BSC (Binance Smart Chain)",
    "polygon": "Polygon",
    "base": "Base",
    "avalanche": "Avalanche",
    "arbitrum": "Arbitrum One",
    "optimism": "Optimism"
}

def fetch_chain_data(chain_id, address, headers):
    """
    [內部工作函數] 負責去抓單一條鏈的資產
    """
    chain_name = SUPPORTED_CHAINS.get(chain_id, chain_id)
    assets = []
    
    print(f"    👉 正在掃描 {chain_name} ...")
    
    try:
        # 1. 抓取 Native Token (例如 ETH, BNB, MATIC)
        native_url = f"https://deep-index.moralis.io/api/v2.2/{address}/balance?chain={chain_id}"
        native_res = requests.get(native_url, headers=headers, timeout=10).json()
        native_bal = float(native_res.get("balance", 0)) / 10**18
        
        if native_bal > 0:
            # 為了省 API 呼叫，我們可以概略估算 Native Token 價格，或呼叫 Moralis Price
            # 這裡示範呼叫 Moralis Native Price Endpoint
            # 注意: 不同鏈的 Native wrapper address 不同，Moralis 提供這支 API 比較方便:
            # "https://deep-index.moralis.io/api/v2.2/erc20/0x.../price" 太麻煩
            # 這裡我們用一個小技巧: Moralis Wallet API 有時會漏掉 Native，所以我們分開抓比較保險
            # 為了 Demo 速度，若 Native 餘額很小 (<0.001) 我們可以先忽略價格查詢
            pass 

    except Exception as e:
        print(f"⚠️ {chain_name} Native 查詢失敗: {e}")

    # 2. 抓取 ERC20 Tokens (包含價格)
    token_url = f"https://deep-index.moralis.io/api/v2.2/wallets/{address}/tokens?chain={chain_id}&exclude_spam=true&exclude_unverified_contracts=true"
    
    try:
        token_res = requests.get(token_url, headers=headers, timeout=20).json()
        raw_tokens = token_res.get("result", [])
        
        for token in raw_tokens:
            symbol = token.get("symbol", "Unknown")
            
            # 黑名單過濾
            if symbol in SCAM_BLACKLIST or token.get("possible_spam"):
                continue

            decimals = int(token.get("decimals", 18))
            balance = float(token.get("balance", 0)) / (10 ** decimals)
            usd_value = token.get("usd_value")

            if usd_value is None: continue
            
            total_value = float(usd_value)

            # 價值過濾 (大於 1 USD)
            if total_value > 1.0:
                price = total_value / balance if balance > 0 else 0
                
                assets.append({
                    "chain": chain_name, # 標記這筆資產在哪條鏈
                    "symbol": symbol,
                    "type": "Token",
                    "balance": balance,
                    "price_usd": price,
                    "value_usd": total_value,
                    "token_address": token.get("token_address")
                })
                
    except Exception as e:
        print(f"⚠️ {chain_name} Token 列表查詢失敗: {e}")
        
    return assets

def get_wallet_portfolio(address):
    """
    多鏈平行查詢與整合
    """
    if "你的" in MORALIS_API_KEY:
        return {"error": "請先填入 Moralis API Key"}

    print(f"🔍 [Multi-Chain] 啟動多鏈掃描: {address}")
    
    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    all_assets = []
    
    # 使用 ThreadPoolExecutor 進行平行處理 (同時發出 7 個請求)
    # 這會讓總等待時間 = 最慢的那條鏈，而不是 7 條鏈相加
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        # 建立任務清單
        future_to_chain = {
            executor.submit(fetch_chain_data, chain_id, address, headers): chain_id 
            for chain_id in SUPPORTED_CHAINS.keys()
        }
        
        for future in concurrent.futures.as_completed(future_to_chain):
            chain_id = future_to_chain[future]
            try:
                data = future.result()
                all_assets.extend(data)
            except Exception as exc:
                print(f"❌ {chain_id} 執行發生例外: {exc}")

    # 排序：依照總價值 (USD)
    all_assets.sort(key=lambda x: x["value_usd"], reverse=True)
    
    # 計算總資產
    total_net_worth = sum(item["value_usd"] for item in all_assets)
    
    # 統計各鏈佔比 (給 LLM 用)
    chain_stats = {}
    for asset in all_assets:
        c = asset["chain"]
        chain_stats[c] = chain_stats.get(c, 0) + asset["value_usd"]

    return {
        "source": "Moralis Multi-Chain API",
        "address": address,
        "total_net_worth_usd": total_net_worth,
        "chain_stats": chain_stats, # 各鏈資產分佈
        "portfolio": all_assets[:20], # 取前 20 大資產 (因為多鏈，資產可能會比較多)
        "scanned_chains": list(SUPPORTED_CHAINS.values())
    }