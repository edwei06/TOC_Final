import streamlit as st
import time
from agent_core import BlockchainAgent

# 1. 基本設定
st.set_page_config(page_title="Blockchain AI Agent", layout="wide", page_icon="🛡️")

# 2. 初始化 Agent
if "agent" not in st.session_state:
    st.session_state.agent = BlockchainAgent()
    st.session_state.messages = []

# Sidebar
st.sidebar.title("🔗 區塊鏈助理")
st.sidebar.caption("NCKU Final Project Demo")
st.sidebar.info(
    """
    **Backend Status:**
    - Model: gpt-oss:120b
    - API: Etherscan V2 (Mainnet)
    - Latency: High (School Server)
    """
)
if st.button("🗑️ 清除對話"):
    st.session_state.messages = []
    st.rerun()

# 主標題
st.title("🛡️ 區塊鏈知識與錢包分析 Agent")

# 3. 顯示歷史訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 4. 輸入框與邏輯
if user_input := st.chat_input("輸入問題 (例：查 Vitalik 錢包、解釋 ZK-Rollup...)"):
    
    # 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Agent 回應區塊
    with st.chat_message("assistant"):
        response_generator = None
        
        # 使用 st.status 顯示多階段狀態，安撫使用者等待的情緒
        with st.status("Agent 正在運作中...", expanded=True) as status:
            
            # 階段 1: 意圖分析與工具呼叫
            st.write("🔍 分析使用者意圖...")
            time.sleep(0.5) # 假裝思考一下，優化體驗
            
            if "錢包" in user_input or "0x" in user_input or "Vitalik" in user_input:
                st.write("🔗 連線 Etherscan V2 API 獲取真實數據...")
            elif "解釋" in user_input:
                st.write("📚 檢索 RAG 知識庫...")
            
            # 階段 2: 呼叫 LLM
            st.write("正在排隊等待學校 Server (gpt-oss:120b)... 這可能需要 20-40 秒...")
            
            try:
                # 真正的執行點
                response_generator = st.session_state.agent.run(user_input)
                status.update(label="✅ LLM 開始生成回應", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ 發生錯誤", state="error")
                st.error(f"系統錯誤: {e}")

        # 階段 3: 顯示結果 (Streaming)
        if response_generator:
            # write_stream 會把接收到的字串一段一段印出來
            # 即使學校伺服器是一次噴出來，st.write_stream 處理起來也會比較滑順一點
            full_response = st.write_stream(response_generator)
            
            # 存入歷史
            st.session_state.messages.append({"role": "assistant", "content": full_response})