import re
import json
from llm_client import query_llm_stream
# from rag_engine import search_knowledge
from blockchain_tools import get_wallet_portfolio
from rag_engine import BlockchainRAG
class BlockchainAgent:
    def __init__(self):
        self.state = "IDLE"
        # 初始化 RAG (這會自動載入 documents 資料夾)
        self.rag = BlockchainRAG() 
        self.context = {}

    def run(self, user_input):
        self.state = "CLASSIFY_INTENT"
        intent = self._classify_intent(user_input)
        
        # 用於 Debug，讓你在 Terminal 看到現在跑去哪了
        print(f"🤖 [State Machine] User Input: {user_input} -> Detected Intent: {intent}")

        # 預設變數
        final_prompt = user_input
        sys_prompt = "你是一個熱心的區塊鏈助教。"

        if intent == "KNOWLEDGE_QA":
            self.state = "RAG_RETRIEVAL"
            print(f"📚 [RAG] 正在搜尋知識庫...")
            
            # 1. 呼叫搜尋 (這步保留，因為我們不知道使用者的問題是否在知識庫裡)
            retrieved_context = self.rag.search(user_input, top_k=3)
            
            self.state = "GENERATING_ANSWER"
            
            # 2. 構建 Prompt (混合模式 Hybrid Mode)
            # 邏輯：優先使用 RAG 資料 -> 如果資料無關 -> 使用 LLM 內建知識
            final_prompt = (
                f"你是一個聰明的區塊鏈助教。使用者提出了一個問題，請依照以下邏輯回答：\n\n"
                f"1. **【優先】參考資料檢索**：\n"
                f"   請先閱讀下方的【參考資料】。如果資料中包含問題的答案（例如關於 TOC Coin、特定專案細節），請**務必引用資料**來回答。\n"
                f"2. **【後補】通用知識補充**：\n"
                f"   如果【參考資料】與使用者的問題**完全無關**（例如使用者問 '什麼是 ETH'，但資料是關於 '詐騙防治'），或者資料不足以回答，\n"
                f"   請**忽略參考資料**，直接使用你身為 LLM 的豐富區塊鏈知識來進行詳盡的教學與回答。\n\n"
                f"【參考資料 (Context)】:\n{retrieved_context}\n\n"
                f"【使用者問題】: {user_input}"
            )
            
            # System Prompt 也要稍微放寬，鼓勵它在必要時展現知識
            sys_prompt = "你是一個樂於助人的區塊鏈專家。優先根據參考資料回答，但若資料不足，請用你的專業知識補充。"

        elif intent == "WALLET_ANALYSIS":
            self.state = "FETCHING_CHAIN_DATA"
            
            # 抓取地址
            address_match = re.search(r'0x[a-fA-F0-9]{40}', user_input)
            address = address_match.group(0) if address_match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            
            # 呼叫 多鏈 API
            portfolio_data = get_wallet_portfolio(address)
            
            # ... (中間資產字串處理邏輯保持不變) ...
            assets_str = ""
            for item in portfolio_data.get("portfolio", []):
                assets_str += (f"- [{item['chain']}] {item['symbol']}: 價值 ${item['value_usd']:.2f}\n")
            
            chain_dist_str = ", ".join([f"{k}: ${v:,.0f}" for k,v in portfolio_data.get("chain_stats", {}).items() if v > 0])
            total_worth = portfolio_data.get("total_net_worth_usd", 0)

            self.state = "ANALYZING_DATA"
            final_prompt = (
                f"請對以太坊錢包 {address} 進行全鏈資產分析。\n"
                f"【總資產淨值】: ${total_worth:,.2f} USD\n"
                f"【公鏈資產分佈】: {chain_dist_str}\n\n"
                f"【前 20 大持倉資產】:\n{assets_str}\n\n"
                f"【分析任務】:\n"
                f"1. 製作資產總覽表格。\n"
                f"2. 分析跨鏈行為與投資風格。\n"
                f"3. 進行資安風險提示。"
            )
            sys_prompt = "你是一個精通多鏈生態的資深加密貨幣分析師。"

        self.state = "IDLE"
        return query_llm_stream(final_prompt, sys_prompt)

    def _classify_intent(self, text):
        """
        決定狀態機的轉移路徑
        """
        text = text.lower() # 轉小寫以利比對

        # 1. 錢包分析意圖 (優先級最高，因為特徵最明顯)
        if re.search(r'0x[a-fA-F0-9]{40}', text):
            return "WALLET_ANALYSIS"
        if any(k in text for k in ["錢包", "地址", "vitalik", "資產", "持倉", "portfolio", "balance"]):
            return "WALLET_ANALYSIS"

        # 2. 知識問答意圖 (擴充關鍵字)
        # 這裡加入了 "什麼是", "toc", "定義" 等等
        rag_keywords = [
            "是什麼", "什麼是", "解釋", "教學", "原理", "定義", "介紹", 
            "what is", "how to", "toc", "token", "概念", "意思"
        ]
        if any(k in text for k in rag_keywords):
            return "KNOWLEDGE_QA"

        # 3. 預設狀態
        return "GENERAL_CHAT"