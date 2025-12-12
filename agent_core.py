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
            address = address_match.group(0) if address_match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            
            # 呼叫 多鏈 API
            portfolio_data = get_wallet_portfolio(address)
            
            # 整理資產字串 (加入 Chain 資訊)
            assets_str = ""
            for item in portfolio_data.get("portfolio", []):
                assets_str += (
                    f"- [{item['chain']}] {item['symbol']}: "
                    f"數量 {item['balance']:.2f}, "
                    f"價值 ${item['value_usd']:.2f}\n"
                )
            
            # 整理鏈上分佈
            chain_dist_str = ", ".join([f"{k}: ${v:,.0f}" for k,v in portfolio_data.get("chain_stats", {}).items() if v > 0])
            total_worth = portfolio_data.get("total_net_worth_usd", 0)

            self.state = "ANALYZING_DATA"
            final_prompt = (
                f"請對以太坊錢包 {address} 進行全鏈資產分析。\n"
                f"【總資產淨值】: ${total_worth:,.2f} USD\n"
                f"【公鏈資產分佈】: {chain_dist_str}\n\n"
                f"【前 20 大持倉資產】:\n{assets_str}\n\n"
                f"【分析任務】:\n"
                f"1. **資產總覽表格**：列出前 5 大資產，欄位包含「代幣、所在公鏈、價值(USD)、佔比」。\n"
                f"2. **跨鏈行為分析**：觀察使用者的資產分佈。他是集中在 Ethereum 主網，還是活躍於 Layer 2 (如 Arbitrum, Optimism) 或其他公鏈 (BSC, Polygon)？這代表什麼樣的使用者畫像？\n"
                f"3. **風險提示**：檢查是否有過度集中於單一資產或單一公鏈的風險。"
            )
            sys_prompt = "你是一個精通多鏈生態的資深加密貨幣分析師。"

        self.state = "IDLE"
        return query_llm_stream(final_prompt, sys_prompt)

    def _classify_intent(self, text):
        if re.search(r'0x[a-fA-F0-9]{40}', text) or "錢包" in text or "地址" in text or "Vitalik" in text or "資產" in text:
            return "WALLET_ANALYSIS"
        elif "是什麼" in text or "教學" in text or "解釋" in text:
            return "KNOWLEDGE_QA"
        return "GENERAL_CHAT"