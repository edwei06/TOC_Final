import re
import json
from llm_client import query_llm_stream
from rag_engine import search_knowledge
from blockchain_tools import get_wallet_history

class BlockchainAgent:
    def __init__(self):
        self.state = "IDLE"
        self.context = {}

    def run(self, user_input):
        self.state = "CLASSIFY_INTENT"
        intent = self._classify_intent(user_input)
        
        # 預設變數
        final_prompt = user_input
        sys_prompt = "你是一個熱心的區塊鏈助教。"

        if intent == "KNOWLEDGE_QA":
            self.state = "RAG_RETRIEVAL"
            context = search_knowledge(user_input)
            
            self.state = "GENERATING_ANSWER"
            final_prompt = f"參考資料：{context}\n\n使用者問題：{user_input}\n請根據資料回答，若資料不足可自行補充。"
            sys_prompt = "你是一個區塊鏈教學助教，擅長解釋專有名詞。"

        elif intent == "WALLET_ANALYSIS":
            self.state = "FETCHING_CHAIN_DATA"
            # 抓取地址
            address_match = re.search(r'0x[a-fA-F0-9]{40}', user_input)
            # 如果使用者沒給地址，就預設用 Vitalik 的地址做 Demo
            address = address_match.group(0) if address_match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            
            # 呼叫 V2 API
            chain_data = get_wallet_history(address)
            
            self.state = "ANALYZING_DATA"
            final_prompt = (
                f"使用者查詢地址：{address}\n"
                f"這是從 Etherscan (V2) 抓取的真實數據：\n{json.dumps(chain_data, ensure_ascii=False, indent=2)}\n\n"
                f"請分析以下幾點：\n"
                f"1. 目前餘額 (ETH)。\n"
                f"2. 最近一筆交易的時間與行為 (IN/OUT)。\n"
                f"3. 根據數據或已知資訊，判斷這個錢包的角色 (例如：是一般散戶、巨鯨還是合約)。"
            )
            sys_prompt = "你是一個專業的鏈上數據分析師，請用條列式清楚呈現分析結果。"

        self.state = "IDLE"
        # 回傳 Generator
        return query_llm_stream(final_prompt, sys_prompt)

    def _classify_intent(self, text):
        if re.search(r'0x[a-fA-F0-9]{40}', text) or "錢包" in text or "地址" in text or "Vitalik" in text:
            return "WALLET_ANALYSIS"
        elif "是什麼" in text or "教學" in text or "解釋" in text:
            return "KNOWLEDGE_QA"
        return "GENERAL_CHAT"