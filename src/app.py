"""
Create the Web UI for the chatbot.
"""

import streamlit as st
from content_construct import split_contents
from config import TEXTBOOK_MAIN_PATHS, MAX_CHUNK_SIZE  # 从config导入预设配置
from RAG import constructVecDB, constructChatEngine
from util import processResponse
import os


# 设置页面
st.set_page_config(
    page_title="《AI中的数学》AI助教",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",  # 隐藏侧边栏
)


# 初始化系统
def init_system():
    try:
        # 分割教材
        bookSplitted = split_contents(TEXTBOOK_MAIN_PATHS, MAX_CHUNK_SIZE)

        # 构建向量数据库
        query_engine = constructVecDB(bookSplitted)

        # 创建聊天引擎
        st.session_state.chat_engine = constructChatEngine(query_engine)

        # 初始化对话历史
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "我是《AI中的数学》的AI助教，欢迎来和我讨论课程内容！",
            }
        ]
    except Exception as e:
        st.error(f"系统初始化失败: {str(e)}")
        os._exit(1)  # 初始化失败时完全退出


# 应用启动时自动初始化
if "initialized" not in st.session_state:
    with st.spinner("系统初始化中，请稍候..."):
        init_system()
    st.session_state.initialized = True

# 主界面
st.title("📖 《AI中的数学》AI助教")
st.caption("基于教材的智能问答系统")

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"],unsafe_allow_html=True)

# 用户输入处理
if prompt := st.chat_input("请输入您的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 获取回答
    try:
        with st.spinner("正在思考..."):
            response = st.session_state.chat_engine.chat(prompt)
        print(response.response)
        response_processed = processResponse(response.response)

        # 添加助手消息
        with st.chat_message("assistant"):
            st.markdown(response_processed, unsafe_allow_html=True)
        st.session_state.messages.append(
            {"role": "assistant", "content": response_processed}
        )
    except Exception as e:
        st.error(f"请求失败: {str(e)}")
        st.session_state.messages.append(
            {"role": "assistant", "content": "抱歉，处理请求时出现错误"}
        )
