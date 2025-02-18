"""
Embedding the textbook into vector database and construct the RAG chatbot.
"""

from typing import Any
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
import tomllib
from prompts import (
    QA_PROMPT,
    REWRITE_PROMPT,
    FIRST_ROUND_MSG_ASSISTANT,
    FIRST_ROUND_MSG_USER,
)
import os


def constructVecDB(bookSplitted: list[str], config: dict[str, Any]):
    # Configure the global settings
    Settings.embed_model = JinaEmbedding(
        api_key=config["embedding_api_key"],
        model=config["embedding_model"],
        task=config["embedding_task"],
    )
    Settings.llm = OpenAILike(
        model=config["llm_model"],
        api_base=config["llm_api_base"],
        temperature=config["llm_temperature"],
        api_key=config["llm_api_key"],
        is_chat_model=True,
    )  # type: ignore
    # This part is already set above, so we can remove the duplicate Settings configuration

    if not os.path.exists(config["db_dir"]):
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
        index.storage_context.persist(persist_dir=config["db_dir"])

        # Remove temporary files first
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        # Remove the empty directory
        os.rmdir(temp_dir)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=config["db_dir"])
        index = load_index_from_storage(storage_context)

    # 新增回答阶段的 Prompt
    qa_prompt = PromptTemplate(QA_PROMPT)
    query_engine = index.as_query_engine(
        text_qa_template=qa_prompt,
        similarity_top_k=config["similarity_top_k"],
        verbose=True,  # 绑定回答模板
    )
    return query_engine


def constructChatEngine(query_engine: BaseQueryEngine):
    # 默认的重写问题的 prompt
    rewrite_prompt = PromptTemplate(REWRITE_PROMPT)

    custom_chat_history = [
        ChatMessage(
            role=MessageRole.USER,
            content=FIRST_ROUND_MSG_USER,
        ),
        ChatMessage(
            role=MessageRole.ASSISTANT,
            content=FIRST_ROUND_MSG_ASSISTANT,
        ),
    ]

    return CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=rewrite_prompt,
        chat_history=custom_chat_history,
        verbose=True,
    )


if __name__ == "__main__":
    from content_construct import split_contents
    import tomllib

    # choose your configuration file here
    config_path = "./my_config.toml"
    with open(config_path, "br") as f:
        config = tomllib.load(f)

    print("Book splitting started...")
    bookSplitted = split_contents(
        config["textbook_main_paths"], config["max_chunk_size"]
    )
    print("Book splitting completed.")
    print("Vector database construction started...")
    queryEngine = constructVecDB(bookSplitted, config)
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
