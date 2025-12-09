import re
import json
from llm_client import query_llm_stream
from rag_engine import search_knowledge
from blockchain_tools import get_wallet_portfolio

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
            # 如果沒給地址，預設用 Vitalik 的做 Demo
            address = address_match.group(0) if address_match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            
            # 呼叫 Moralis API (已過濾)
            portfolio_data = get_wallet_portfolio(address)
            
            # 整理資產字串給 LLM
            assets_str = ""
            for item in portfolio_data.get("portfolio", []):
                assets_str += (
                    f"- {item['symbol']}: 數量 {item['balance']:.2f}, "
                    f"總值 ${item['value_usd']:.2f}\n"
                )
            total_worth = portfolio_data.get("total_net_worth_usd", 0)

            self.state = "ANALYZING_DATA"
            final_prompt = (
                f"請分析以下以太坊錢包地址 {address} 的資產配置。\n"
                f"【總資產淨值】: ${total_worth:,.2f} USD\n\n"
                f"【前十大持倉資產 (已按價值排序)】:\n{assets_str}\n\n"
                f"【分析任務】:\n"
                f"1. 請製作一個 Markdown 表格，列出前 5 大資產的「幣種、價值(USD)、佔總資產百分比」。\n"
                f"2. [資安檢測]：若清單中有非主流且價值異常高的代幣，請標註為「疑似詐騙空投」並提醒風險。\n"
                f"3. 分析此人的投資風格（例如：巨鯨、DeFi 玩家、或避險者）。"
            )
            sys_prompt = "你是一個專業的華爾街加密貨幣資產分析師。"

        self.state = "IDLE"
        # 回傳 Generator
        return query_llm_stream(final_prompt, sys_prompt)

    def _classify_intent(self, text):
        if re.search(r'0x[a-fA-F0-9]{40}', text) or "錢包" in text or "地址" in text or "Vitalik" in text or "資產" in text:
            return "WALLET_ANALYSIS"
        elif "是什麼" in text or "教學" in text or "解釋" in text:
            return "KNOWLEDGE_QA"
        return "GENERAL_CHAT"