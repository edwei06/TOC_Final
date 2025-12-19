import streamlit as st
import time
from agent_core import BlockchainAgent

# 在 Sidebar 或 Main Page 顯示狀態機
st.sidebar.markdown("### Agent 內部狀態機 (FSM)")

# 使用 Graphviz 定義狀態機
fsm_graph = """
digraph G {
    // 設定圖表方向與屬性
    rankdir=LR;
    node [shape=circle, style=filled, color=lightblue, fontname="Helvetica"];
    edge [fontname="Helvetica", fontsize=10];

    // 定義狀態節點
    IDLE [label="IDLE\n(待機)", shape=doublecircle, color=lightgrey];
    CLASSIFY [label="CLASSIFY\nINTENT", shape=box, color=gold];
    
    // 知識問答分支
    RAG [label="RAG\nRETRIEVAL", color=lightgreen];
    GEN_ANS [label="GENERATING\nANSWER", color=lightgreen];
    
    // 錢包分析分支
    FETCH [label="FETCHING\nCHAIN DATA", color=salmon];
    ANALYSIS [label="ANALYZING\nDATA", color=salmon];
    
    // 一般閒聊分支
    CHAT [label="CHATTING", color=lightyellow];

    // 定義轉移路徑 (Transitions)
    IDLE -> CLASSIFY [label="User Input"];
    
    CLASSIFY -> RAG [label="Intent: KNOWLEDGE_QA"];
    RAG -> GEN_ANS [label="Context Found"];
    GEN_ANS -> IDLE [label="Response Streamed"];
    
    CLASSIFY -> FETCH [label="Intent: WALLET_ANALYSIS"];
    FETCH -> ANALYSIS [label="API Data Ready"];
    ANALYSIS -> IDLE [label="Response Streamed"];
    
    CLASSIFY -> CHAT [label="Intent: GENERAL_CHAT"];
    CHAT -> IDLE [label="Response Streamed"];
}
"""

# 渲染圖表
st.sidebar.graphviz_chart(fsm_graph)
st.markdown("### 系統架構資料流 (DAG)")

dag_graph = """
digraph DAG {
    rankdir=TB;
    node [shape=box, style=rounded, fontname="Helvetica"];

    // 定義節點
    User [label="User Input", shape=ellipse, style=filled, color=lightgrey];
    Classifier [label="Intent Classifier\n(Regex/Keyword)", color=gold];
    
    subgraph cluster_tools {
        label = "External Tools";
        style = dashed;
        color = grey;
        
        Moralis [label="Moralis Multi-Chain API\n(Parallel Threads)", color=salmon];
        RAG [label="RAG Engine\n(ChromaDB + Embedding)", color=lightgreen];
    }
    
    PromptEng [label="Prompt Engineering\n(Context + Data Aggregation)"];
    LLM [label="LLM Inference\n(gpt-oss:120b)", style=filled, color=lightblue];
    StreamUI [label="Streamlit UI\n(Streaming Output)", shape=ellipse, style=filled, color=lightgrey];

    // 定義資料流向
    User -> Classifier;
    
    Classifier -> Moralis [label="Address/Wallet"];
    Classifier -> RAG [label="Question/Concept"];
    Classifier -> PromptEng [label="Chat History"];
    
    Moralis -> PromptEng [label="Portfolio JSON"];
    RAG -> PromptEng [label="Retrieved Chunks"];
    
    PromptEng -> LLM [label="Final Prompt"];
    LLM -> StreamUI [label="Token Stream"];
}
"""

st.graphviz_chart(dag_graph)
# 1. 基本設定
st.set_page_config(page_title="Blockchain AI Agent", layout="wide", page_icon="🛡️")

# 2. 初始化 Agent
if "agent" not in st.session_state:
    st.session_state.agent = BlockchainAgent()
    st.session_state.messages = []

# Sidebar
st.sidebar.title("區塊鏈助理")
st.sidebar.caption("NCKU Final Project Demo")
st.sidebar.info(
    """
    **Backend Status:**
    - Model: gpt-oss:120b
    - API: Moralis (Filtered)
    - Latency: High (School Server)
    """
)
if st.button("清除對話"):
    st.session_state.messages = []
    st.rerun()

# 主標題
st.title("區塊鏈知識與錢包分析 Agent")

# 3. 顯示歷史訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 4. 輸入框與邏輯
if user_input := st.chat_input("輸入問題 (例：查 Vitalik 錢包資產、解釋 ERC-721...)"):
    
    # 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Agent 回應區塊
    with st.chat_message("assistant"):
        response_generator = None
        
        # 使用 st.status 顯示多階段狀態
        with st.status("Agent 正在運作中...", expanded=True) as status:
            
            # 階段 1: 意圖分析與工具呼叫
            st.write("分析使用者意圖...")
            time.sleep(0.5) 
            
            if "錢包" in user_input or "0x" in user_input or "Vitalik" in user_input or "資產" in user_input:
                st.write("連線 Moralis API 掃描鏈上資產...")
                st.write("執行詐騙代幣過濾 (Anti-Spam Filter)...")
            elif "解釋" or "什麼" in user_input:
                st.write("檢索 RAG 知識庫...")
            
            # 階段 2: 呼叫 LLM
            st.write("正在排隊等待學校 Server (gpt-oss:120b)... 這可能需要 20-40 秒...")
            
            try:
                # 真正的執行點
                response_generator = st.session_state.agent.run(user_input)
                status.update(label="LLM 開始生成回應", state="complete", expanded=False)
            except Exception as e:
                status.update(label="發生錯誤", state="error")
                st.error(f"系統錯誤: {e}")

        # 階段 3: 顯示結果 (Streaming)
        if response_generator:
            full_response = st.write_stream(response_generator)
            
            # 存入歷史
            st.session_state.messages.append({"role": "assistant", "content": full_response})