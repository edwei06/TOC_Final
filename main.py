import streamlit as st
from agent_core import BlockchainAgent
from rag_engine import load_documents

# 設定頁面
st.set_page_config(page_title="Blockchain AI Agent", layout="wide")

# 初始化 Agent
if "agent" not in st.session_state:
    # 第一次啟動時載入文件
    # load_documents() # 確保有文件
    st.session_state.agent = BlockchainAgent()
    st.session_state.messages = []

# Sidebar
st.sidebar.title("系統狀態")
st.sidebar.markdown(f"目前狀態: **{st.session_state.agent.state}**")
st.sidebar.markdown("---")
st.sidebar.write("後端模型: gpt-oss-120b")
st.sidebar.write("功能模組: RAG / Etherscan API / Risk Engine")

# Main Chat Interface
st.title("🛡️ 區塊鏈知識與錢包助理")
st.caption("NCKU Final Project - Using Professor's LLM API")

# 顯示歷史訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 輸入框
user_input = st.chat_input("請輸入你的問題 (例：解釋 zk-Rollup, 幫我查這個錢包...)")

if user_input:
    # 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Agent 思考與回應
    with st.chat_message("assistant"):
        with st.spinner("Agent 正在思考與調度工具..."):
            response = st.session_state.agent.run(user_input)
            st.write(response)
    
    # 存入歷史
    st.session_state.messages.append({"role": "assistant", "content": response})

    # 強制更新 sidebar 狀態 (Streamlit特性)
    st.rerun()