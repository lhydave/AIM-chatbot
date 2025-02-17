"""
Embedding the textbook into vector database and construct the RAG chatbot.
"""

from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core import PromptTemplate
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from config import (
    EMBEDDING_API_KEY,
    EMBEDDING_MODEL,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_API_BASE,
    DB_DIR,
    LLM_TEMPERATURE,
    SIMILARITY_TOP_K,
)
import os


def constructVecDB(bookSplitted: list[str]):
    Settings.embed_model = JinaEmbedding(
        api_key=EMBEDDING_API_KEY,
        model=EMBEDDING_MODEL,
        # choose `retrieval.passage` to get passage embeddings
        task="retrieval.passage",
    )
    Settings.llm = OpenAILike(
        model=LLM_MODEL,
        api_base=LLM_API_BASE,
        temperature=LLM_TEMPERATURE,
        api_key=LLM_API_KEY,
        is_chat_model=True) # type: ignore

    if not os.path.exists(DB_DIR):

        temp_dir = "temp_docs"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        for i, text in enumerate(bookSplitted):
            with open(
                os.path.join(temp_dir, f"doc_{i}.txt"), "w", encoding="utf-8"
            ) as f:
                f.write(text)
        documents = SimpleDirectoryReader(temp_dir).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=DB_DIR)

        # Remove temporary files first
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        # Remove the empty directory
        os.rmdir(temp_dir)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=DB_DIR)
        index = load_index_from_storage(storage_context)
    # 新增回答阶段的 Prompt
    qa_prompt = PromptTemplate(
        """现在你是《AI中的数学》的课程助教，请严格基于以下课程资料片段（来自AI中的数学教材）给出User（学生）消息的相应回复。

课程资料：{context_str}
用户的消息：{query_str}

要求做到：
- 课程资料中的表格、定理、证明等 latex 环境无法正确显示，请转换为 Markdown 语法。
- 课程资料中的 \\Cref和 \\ref 不会正确显示，请把他们换成自然语言。
- 包含数学公式时使用 Markdown LaTeX 格式，行间公式单独成行。
- 如同老师给学生解答的过程，从浅到深，由具体到一般，非常详细，由流畅的文字+展示组成，而不是简单几条大纲。

你的回复："""
    )
    query_engine = index.as_query_engine(
        text_qa_template=qa_prompt,
        similarity_top_k=SIMILARITY_TOP_K,
        verbose=True,  # 绑定回答模板
    )
    return query_engine


def constructChatEngine(query_engine: BaseQueryEngine):
    # 默认的重写问题的 prompt
    custom_prompt = PromptTemplate(
        """总结对话历史（User和assistant的对话），写一个概要，然后将这个概要拼接上下面User的最新消息，模版为（方括号不要出现）：
        
[这里填入对话概要]最新User现在跟你说：[这里填入最新消息]。

<对话历史> {chat_history}
<最新消息> {question}
<拼接后的新消息>
"""
    )

    custom_chat_history = [
        ChatMessage(
            role=MessageRole.USER,
            content="现在你是《AI中的数学》的课程助教，接下来每一轮User都会给你相应的课程资料、你们曾经的对话和User的最新消息，请你和User交流。在每次对话开始的时候，User都会强调你的回答准则，请注意。",
        ),
        ChatMessage(
            role=MessageRole.ASSISTANT,
            content="好的，我会遵照你的要求回答。",
        ),
    ]

    return CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=custom_prompt,
        chat_history=custom_chat_history,
        verbose=True,
    )


if __name__ == "__main__":
    from content_construct import split_contents
    from config import TEXTBOOK_MAIN_PATHS, MAX_CHUNK_SIZE

    print("Book splitting started...")
    bookSplitted = split_contents(TEXTBOOK_MAIN_PATHS, MAX_CHUNK_SIZE)
    print("Book splitting completed.")
    print("Vector database construction started...")
    queryEngine = constructVecDB(bookSplitted)
    print("Vector database construction completed.")
    print("Chat engine initialization started...")
    chatbot = constructChatEngine(queryEngine)
    print("Chat engine initialization completed. Ready for chat!")

    while True:
        try:
            user_input = input()
            if user_input.lower() == "exit":
                break
            chatResponse = chatbot.chat(user_input)
            print(chatResponse)
            print("回复输出结束")
        except KeyboardInterrupt:
            print("\n退出程序")
            break
        except Exception as e:
            print(f"发生错误: {e}")
