import requests
from datetime import datetime

# ==========================================
# [必填] Etherscan API Key
# 請去 https://etherscan.io/myapikey 申請一個免費的 (只需 Email)
# ==========================================
ETHERSCAN_API_KEY = "9SAG5ASPGHJFT7AEDD8B2GGIMCESBA68EB"

def wei_to_eth(wei_value):
    """
    將 Wei (最小單位) 轉換為 Ether
    """
    try:
        return float(wei_value) / 10**18
    except:
        return 0.0

def format_timestamp(timestamp):
    """
    將 Unix Timestamp 轉為易讀日期格式
    """
    try:
        dt_object = datetime.fromtimestamp(int(timestamp))
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def get_wallet_history(address, limit=5):
    """
    呼叫 Etherscan API V2 取得真實餘額與最近交易紀錄
    """
    # 簡單檢查 Key 是否填寫
    if "你的" in ETHERSCAN_API_KEY:
        return {"error": "請先在 blockchain_tools.py 填入有效的 Etherscan API Key"}

    print(f"🔍 正在查詢 Etherscan (V2 API): {address}")
    
    # ==========================================
    # V2 API URL 格式修正
    # 格式: https://api.etherscan.io/v2/api?chainid=1&...
    # chainid=1 代表以太坊主網 (Mainnet)
    # ==========================================
    
    # 1. 取得餘額 (Get Balance)
    balance_url = (
        f"https://api.etherscan.io/v2/api?"
        f"chainid=1&"
        f"module=account&"
        f"action=balance&"
        f"address={address}&"
        f"tag=latest&"
        f"apikey={ETHERSCAN_API_KEY}"
    )
    
    # 2. 取得最近交易 (Get Transaction List)
    tx_url = (
        f"https://api.etherscan.io/v2/api?"
        f"chainid=1&"
        f"module=account&"
        f"action=txlist&"
        f"address={address}&"
        f"startblock=0&"
        f"endblock=99999999&"
        f"page=1&"
        f"offset={limit}&"
        f"sort=desc&"
        f"apikey={ETHERSCAN_API_KEY}"
    )

    try:
        # 發送請求
        bal_res = requests.get(balance_url, timeout=10).json()
        tx_res = requests.get(tx_url, timeout=10).json()

        # [除錯用] 如果還是失敗，取消下面註解看錯誤訊息
        # print(f"[Debug] Balance: {bal_res}")
        # print(f"[Debug] Tx: {tx_res}")

        # 整理餘額 (V2 的成功 status 依然是 "1")
        current_balance = "0 ETH"
        if bal_res["status"] == "1":
            eth_val = wei_to_eth(bal_res["result"])
            current_balance = f"{eth_val:.4f} ETH"
        else:
            print(f"⚠️ 餘額查詢回傳非成功狀態: {bal_res.get('message')}")

        # 整理交易列表
        recent_activity = []
        if tx_res["status"] == "1":
            for tx in tx_res["result"]:
                direction = "OUT (轉出)" if tx["from"].lower() == address.lower() else "IN (轉入)"
                amount = wei_to_eth(tx["value"])
                
                # 簡單判斷互動對象
                interact_with = tx["to"] if tx["to"] else "Contract Creation"
                
                activity_str = (
                    f"時間: {format_timestamp(tx['timeStamp'])}, "
                    f"動作: {direction}, "
                    f"金額: {amount:.4f} ETH, "
                    f"對象: {interact_with[:8]}..."
                )
                recent_activity.append(activity_str)
        else:
            recent_activity.append("查無近期交易或地址無效 (或 API 次數限制)")

        # 回傳
        return {
            "source": "Etherscan Real-time Data (V2)",
            "address": address,
            "current_balance": current_balance,
            "recent_transactions": recent_activity
        }

    except Exception as e:
        return {"error": f"API 連線失敗: {str(e)}"}

# 測試用
if __name__ == "__main__":
    test_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    print(get_wallet_history(test_addr))