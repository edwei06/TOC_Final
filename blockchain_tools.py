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
    呼叫 Etherscan API 取得真實餘額與最近交易紀錄
    """
    # 檢查 API Key 是否填寫
    if "你的" in ETHERSCAN_API_KEY:
        return {"error": "請先在 blockchain_tools.py 填入有效的 Etherscan API Key"}

    print(f"🔍 正在查詢 Etherscan: {address}")
    
    # 1. 取得餘額 (Get Balance)
    balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
    
    # 2. 取得最近交易 (Get Transaction List)
    # sort=desc 代表從最新的開始抓
    tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={ETHERSCAN_API_KEY}"

    try:
        # 發送請求
        bal_res = requests.get(balance_url, timeout=10).json()
        tx_res = requests.get(tx_url, timeout=10).json()

        # 整理餘額
        current_balance = "0 ETH"
        if bal_res["status"] == "1":
            eth_val = wei_to_eth(bal_res["result"])
            current_balance = f"{eth_val:.4f} ETH"

        # 整理交易列表
        recent_activity = []
        if tx_res["status"] == "1":
            for tx in tx_res["result"]:
                # 判斷是轉入還是轉出
                # 注意：API 回傳的地址通常是全小寫，建議都轉小寫比對
                direction = "OUT (轉出)" if tx["from"].lower() == address.lower() else "IN (轉入)"
                
                # 計算金額
                amount = wei_to_eth(tx["value"])
                
                # 簡單判斷互動對象 (若是合約互動，to 可能是空值或合約地址)
                interact_with = tx["to"] if tx["to"] else "Contract Creation"
                
                # 組合人類可讀的描述
                activity_str = (
                    f"時間: {format_timestamp(tx['timeStamp'])}, "
                    f"動作: {direction}, "
                    f"金額: {amount:.4f} ETH, "
                    f"對象: {interact_with[:8]}..." # 只顯示前幾碼避免太長
                )
                recent_activity.append(activity_str)
        else:
            recent_activity.append("查無近期交易或地址無效")

        # 回傳給 Agent 的結構化資料
        return {
            "source": "Etherscan Real-time Data",
            "address": address,
            "current_balance": current_balance,
            "recent_transactions": recent_activity,
            "note": "僅顯示最近 5 筆一般交易 (Internal/Token 轉帳不在此限)"
        }

    except Exception as e:
        return {"error": f"API 連線失敗: {str(e)}"}

# 測試用
if __name__ == "__main__":
    # 這裡可以用 Vitalik 的錢包地址測試
    test_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    print(get_wallet_history(test_addr))