"""
Embedding the textbook into vector database.
"""

from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.llms.deepseek import DeepSeek
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
    jinaai_api_key,
    jinaai_model,
    deepseek_api_key,
    deepseek_model,
    db_dir,
)
import os


def constructVecDB(bookSplitted: list[str]):
    Settings.embed_model = JinaEmbedding(
        api_key=jinaai_api_key,
        model=jinaai_model,
        # choose `retrieval.passage` to get passage embeddings
        task="retrieval.passage",
    )
    Settings.llm = DeepSeek(model=deepseek_model, api_key=deepseek_api_key)

    if not os.path.exists(db_dir):

        temp_dir = "temp_docs"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        for i, text in enumerate(bookSplitted):
            with open(os.path.join(temp_dir, f"doc_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(text)

        documents = SimpleDirectoryReader(temp_dir).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=db_dir)

        # Remove temporary files first
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        # Remove the empty directory
        os.rmdir(temp_dir)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=db_dir)
        index = load_index_from_storage(storage_context)
    return index.as_query_engine()


def constructChatEngine(query_engine: BaseQueryEngine):
    # 默认的重写问题的 prompt
    custom_prompt = PromptTemplate(
        """根据对话内容（Human和assistant之间的对话）和Human的后续消息，将消息重写为一个单独的问题，该问题要包含对话中少量重要的上下文，主要关注当前问题，遵循所给资料回答，尽量详细。
<Chat History> {chat_history}
<Follow Up Message> {question}
<Standalone question>
"""
    )

    custom_chat_history = [
        ChatMessage(
            role=MessageRole.USER,
            content="你好assistant，我们今天讨论的是《AI中的数学》，我是一个刚上大学的学生，请你做我的老师，尽量详尽回答。尽量少发散思维，主要按照我给你的资料讲解。超出的范围请回答不知道，但你不知道可能是因为数据检索不到位，所以不要说书里没有。",
        ),
        ChatMessage(
            role=MessageRole.ASSISTANT, content="好的，我会尽量用简单易懂的方式详细给你讲懂的。"
        ),
    ]

    return CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=custom_prompt,
        chat_history=custom_chat_history,
        verbose=True,
    )

if __name__ == '__main__':
    from content_construct import split_book
    from config import textbookMainPath,maxChunkSize
    bookSplitted = split_book(textbookMainPath,maxChunkSize)
    queryEngine = constructVecDB(bookSplitted)
    chatbot = constructChatEngine(queryEngine)
    
    while True:
        try:
            user_input = input()
            if user_input.lower() == 'exit':
                break
            chatResponse = chatbot.chat(user_input)
            print(chatResponse)
        except KeyboardInterrupt:
            print("\n退出程序")
            break
        except Exception as e:
            print(f"发生错误: {e}")