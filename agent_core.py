import re
import json
from llm_client import query_llm
from rag_engine import search_knowledge
from blockchain_tools import get_wallet_history

class BlockchainAgent:
    def __init__(self):
        self.state = "IDLE"
        self.context = {}

    def run(self, user_input):
        self.state = "CLASSIFY_INTENT"
        intent = self._classify_intent(user_input)
        
        response = ""

        if intent == "KNOWLEDGE_QA":
            self.state = "RAG_RETRIEVAL"
            # 搜尋知識庫
            context = search_knowledge(user_input)
            
            self.state = "GENERATING_ANSWER"
            prompt = f"參考資料：{context}\n\n使用者問題：{user_input}\n請根據參考資料回答，若資料不足則用你的知識補充。"
            response = query_llm(prompt, system_prompt="你是一個區塊鏈教學助教。")
        elif intent == "WALLET_ANALYSIS":
            self.state = "FETCHING_CHAIN_DATA"
            address_match = re.search(r'0x[a-fA-F0-9]{40}', user_input)
            address = address_match.group(0) if address_match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

            # 呼叫真實 API
            chain_data = get_wallet_history(address)

            self.state = "ANALYZING_DATA"
            # 這裡把 JSON 直接 dump 給 LLM 看
            prompt = (
                f"使用者查詢地址 {address}。\n"
                f"這是從 Etherscan 抓取的真實數據：\n{json.dumps(chain_data, ensure_ascii=False, indent=2)}\n\n"
                f"任務：\n"
                f"1. 告訴使用者這個錢包還有多少錢。\n"
                f"2. 總結最近幾筆交易在做什麼（轉入還是轉出？）。\n"
                f"3. 根據這些行為判斷這是不是一個活躍的錢包。"
            )
            response = query_llm(prompt, system_prompt="你是一個專業的區塊鏈數據分析師，請用白話文解釋數據。")
        else:
            self.state = "CHATTING"
            response = query_llm(user_input, system_prompt="你是一個熱心的區塊鏈助教，請簡短回應。")

        self.state = "IDLE"
        return response

    def _classify_intent(self, text):
        # 簡單規則判斷
        if re.search(r'0x[a-fA-F0-9]{40}', text) or "錢包" in text or "地址" in text:
            return "WALLET_ANALYSIS"
        elif "是什麼" in text or "原理" in text or "教學" in text:
            return "KNOWLEDGE_QA"
        return "GENERAL_CHAT"