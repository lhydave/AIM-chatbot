# 《AI 中的数学》AI 助教系统

这是一个基于《AI 中的数学》教材内容的 AI 助教系统，可以帮助学生解答《AI 中的数学》课程相关的问题。该系统使用了检索增强生成（RAG）技术，将教材内容转换为向量数据库，然后通过大语言模型（LLM）的 API 来实现智能问答。用户可以在对话框中输入问题，系统会自动检索相关教材内容，并生成针对性回答。本助教系统也可以用于其他课程，只要课程内容是用 latex 组织起来的，本系统就可以自动构建向量数据库，实现智能问答。

## 功能特点

- 基于教材内容的智能问答
- 实时对话界面，支持多轮问答
- 支持 Markdown 渲染
- 支持 LaTeX 数学公式显示，允许自定义数学指令和符号
- 智能检索相关教材内容
- 用户友好的 Web 界面

## 系统要求

- conda 24.5.0（推荐这个版本，其他版本未经过测试）
- Jina API Key（向量数据库的 embedding 模型，从[这个链接](https://jina.ai/embeddings/)获取）
- 火山方舟引擎 API Key，LLM ID（LLM，详见[这个链接](https://www.volcengine.com/product/ark)，按照教程获取）

## 安装步骤

1. 克隆项目仓库：
```bash
git clone https://github.com/lhydave/AIM-chatbot.git
cd AIM-chatbot
```

2. 创建并激活 Conda 环境：
```bash
conda create -n aim-chatbot python=3.11
conda activate aim-chatbot
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

4. 配置环境：
- 复制一份 `src/sample_config.toml` 到 `src/my_config.toml`
- 按照提示填写 `src/my_config.toml` 中的各种配置项，包括 tex 文件路径、Jina API Key、火山方舟引擎 API Key 和 LLM ID

## 运行应用

1. 启动应用：
```bash
cd src
streamlit run app.py
```

2. 在浏览器中打开 `http://localhost:8501`，即可开始使用

## 项目结构

```
AIM-chatbot/
├── LICENSE                 # MIT许可证
├── README.md              # 项目说明文档
├── requirements.txt       # Python依赖包列表
├── pytest.ini            # pytest配置文件
├── src/                  # 源代码目录
│   ├── __init__.py      
│   ├── app.py           # Web应用主程序（Streamlit）
│   ├── RAG.py           # RAG系统实现
│   ├── content_construct.py  # 文本处理和分割
│   ├── latex_defs.py    # LaTeX宏定义
│   ├── prompts.py       # 提示词配置
│   ├── util.py          # 工具函数
│   ├── my_config.toml   # 个人配置文件（需自行创建）
│   └── sample_config.toml  # 配置文件模板
├── tests/               # 测试目录
│   ├── test_content_construct.py  # 文本处理测试
│   └── test_utils.py    # 工具函数测试
└── storage/            # 向量数据库存储目录（自动创建）
```

## 注意事项

- 首次运行时需要构建向量数据库，存储在 `storage` 文件夹中，可能需要较长时间，请耐心等待
- 请确保教材文件格式为 tex，其他文本只会当成普通文本处理
- API 密钥请妥善保管，不要泄露（尤其在 fork 本项目时）

## 定制化

本项目可以用于其他课程的智能问答系统构建，以下是一些很容易定制的地方：

### 模型（参数）选择

你可以自由选择 Jina 的 embedding 模型和火山方舟上部署的的大语言模型，只需在 `src/my_config.toml` 中修改相关配置即可，请参考具体的 API 文档。

此外，你还可以设置 temperature，这一参数代表着 LLM 生成文本的随机性，数值越大，生成的文本越随机，数值越小，生成的文本越确定。你可以根据实际情况调整这一参数。只需要在 `src/my_config.toml` 中修改 `llm_temperature` 即可，数值范围为 0 到 1。

 我们还提供了一个参数`SIMILARITY_TOP_K`，这个参数代表着检索时返回的最相似的文本块数量，数值越大，返回的文本块越多，但是检索速度会变慢，和LLM的交互速度也会变慢。你可以根据实际情况调整这一参数。只需要在 `src/my_config.toml` 中修改 `similarity_top_k` 即可。

### 自定义 LaTeX 宏

你可以自由定制 LaTeX 的宏定义（即类似 `\newcommand` 或 `\DeclareMathOperator` 的命令），这样对话系统可以正确显示这些 latex 数学公式。要做到这一点，只需在 `src/latex_defs.py` 中修改 `LATEX_MACROS` 或 `LATEX_COMMANDS` 即可，格式请参考当前的定义。

### 选择 tex 素材文件

只需在 `src/my_config.toml` 中修改 `textbook_main_paths` 即可。当前支持多个主文件（即有 `\documentclass` 的文件），其他所有 tex 文件需要通过 `\input` 或 `\include` 命令（递归地）引入。只需声明主文件即可，系统会自动导入所有相关文件。

### 定制提示词

你可以自由修改 RAG 的相关提示词，只需在 `src/prompts.py` 中修改对应的提示词即可。这些提示词会影响 RAG 的生成结果，请谨慎修改。提示词的运行方式如下：
- 当用户输入一个问题的时候，系统会使用 `REWRITE_PROMPT` 作为提示词输入 LLM，这一提示词的功能是总结历史对话，然后拼接上当前问题，作为向量数据库的输入。
- 接下来，向量数据库会利用这个输入，检索相关的教材内容，然后利用 `QA_PROMPT` 作为提示词模板，将检索的内容、用户的消息拼接，输出给 LLM，生成回答。
- 在系统初始化时，我们还设置了 `FIRST_ROUND_MSG_USER` 和 `FIRST_ROUND_MSG_ASSISTANT` 作为预设的第一轮对话，这样可以让 LLM 更好地理解它的角色。

你可以根据自己的需求修改这些提示词，但要注意保持提示词的基本结构，比如确保 `QA_PROMPT` 中包含 `{context_str}` 和 `{query_str}` 这些占位符，确保 `REWRITE_PROMPT` 中包含 `{chat_history}` 和 `{question}` 这些占位符。

### 定制 Web 界面文字

你可以自由修改 Web 界面的各种文字，只需要修改 `src/app.py` 中的相关字符串即可。

如果你还需要更高级的定制化，下面是一些指导：

### 更广泛的模型选择

当前项目使用了 Jina 和火山方舟的 API，以及 `llama_index` 自带的向量数据库，如果你想使用其他的模型，需要修改 `src/RAG.py` 中的相关代码，以适应新的模型。
- 修改 `llama_index.embeddings` 相关的 `import` 语句，以及后续对应的应用语句，以适应新的 embedding 模型
- 修改 `llama_index.llms` 相关的 `import` 语句，以及后续对应的应用语句，以适应新的大语言模型
- 修改 `llama_index.core` 导入的 `VectorStoreIndex`、`SimpleDirectoryReader` 和 `StorageContext`，以适应新的向量数据库

### 更广泛的素材文件选择

如果你想使用其他格式的教材文件（例如 docx、pptx），请自行处理文件解析的过程，需要重新实现 `src/content_construct.py` 中的 `split_single_file` 函数，这个函数接受一个文件路径，和文本块大小，返回一个文本块列表，即将文件内容分割成一个个文本块。当前的实现是针对 tex 文件的，对 tex 的语法进行额外处理，以保持语义的完整性。

此外，Jina embedding 是一个多模态的 embedding 框架，支持多种数据类型的 embedding，如果你想使用其他格式的数据，可以参考 Jina 的文档，自行实现 embedding 模块。

### 更复杂的 RAG 交互逻辑

本项目使用了 `llama_index` 的 `BaseQueryEngine` 作为 RAG 实现，并使用 `CondenseQuestionChatEngine` 支持多轮对话。如果你想采用流式输出或者更加复杂的交互逻辑，需要重新实现 `src/RAG.py` 中的 `constructChatEngine` 和 `constructVecDB` 函数，请参考 `llama_index` 的相关文档。

### 更广泛的 Web 界面定制

本项目使用了 Streamlit 作为 Web 应用框架，如果你想要更加复杂的 Web 界面，可以参考 Streamlit 的文档，自行实现更加复杂的 Web 应用。