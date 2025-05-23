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
- uv
    - 安装请参考[这个链接](https://docs.astral.sh/uv/getting-started/installation/)
- Jina API 密钥
    - 向量数据库的 embedding 模型，从[这个链接](https://jina.ai/embeddings/)获取
- 火山方舟引擎 API Key，LLM ID
    - LLM，详见[这个链接](https://www.volcengine.com/docs/82379/1399008)，按照教程获取
- 终端命令行工具
    - 用于运行系统，可以在终端中输入命令
    - Mac 和 Linux 为终端（英文为 Terminal）
    - Windows 为 PowerShell 或者 cmd

## 教材准备

本系统需要使用《AI 中的数学》教材的 tex 文件作为输入，你可以从[这个链接](https://github.com/lhydave/AIM-textbook)获取教材的 tex 文件。请注意，你需要将*完整的文件夹*下载到本地，而不是只下载 main.tex 文件。

## 安装步骤

1. 下载本项目
- 你可以直接在该页面点击绿色的 `Code` 按钮，选择 `Download ZIP` 下载本项目，然后解压缩到本地
- 或者你可以使用 git 命令行工具（如果是Windows用户，请安装git），直接在终端中输入以下命令：
```bash
git clone https://github.com/lhydave/AIM-chatbot.git
```     

以下步骤都在终端中进行，如果遇到问题，请参考[遇到问题时候的检查方法](#遇到问题时候的检查方法)。

2. 在终端中进入项目目录，如果上一步使用了 git 命令行工具下载的项目，请直接进入项目目录：
```bash
cd AIM-chatbot
```

3. 安装 python 依赖
```bash
uv sync
```

4. 配置环境：
- 复制一份 [`src/sample_config.toml`](src/sample_config.toml) 到 `src/my_config.toml`
- 按照提示填写 `src/my_config.toml` 中的各种配置项，包括 tex 文件路径、Jina API Key、火山方舟引擎 API Key 和 LLM ID

## 运行应用

以下步骤都在终端中进行，如果遇到问题，请参考[遇到问题时候的检查方法](#遇到问题时候的检查方法)。

```bash
cd src
uv run streamlit run app.py
```

2. 在浏览器中打开 `http://localhost:8501`，即可开始使用（注意，这一步通常并不需要做，因为 streamlit 会自动打开浏览器）

> 首次运行时需要构建向量数据库，存储在 `storage` 文件夹中，可能需要较长时间，请耐心等待

## 遇到问题时候的检查方法

在运行软件的时候，可能会遇到一些问题，有一些问题可以在网页界面中直接看到，你可以通过搜索的方式试图解决。

如果问题出在构建向量数据库及之前的环节，那么网页不会正确加载，streamlit 应用会直接退出，此时，请遵循以下步骤：

1. 确保你已经按照前面的所有步骤操作
2. 确保你已经激活了 `aim-chatbot` 的 conda 环境
3. 确保你已经正确填写了 `src/my_config.toml` 中的配置项
3. 如果以上都没有问题，请使用命令行对话模式：

```bash
cd src
uv run RAG.py
```

此时，你可以在命令行中进行交互，任何错误都会在终端中显示，方便你进行调试。

### 常见错误汇总

- pip 安装依赖库不兼容：请确保你的 python 版本是 3.11，且 conda 创建环境的时候使用了 `--no-default-packages` 参数
- `ModuleNotFoundError` 错误：请确保你已经激活了 `aim-chatbot` 的 conda 环境，并确认 conda 的环境变量配置正确，如果你是 Mac 或者 Linux 系统，请确保 conda python 覆盖了系统 python
- 找不到某个 tex 文件：请确保你已经完整下载了教材的 tex 文件夹（而不是只有 `main.tex` 文件），并且正确填写了 `src/my_config.toml` 中的 `textbook_main_paths` 配置项
- `InvalidEndpointOrModel` 错误：请注意，如果使用接入点配置，LLM ID 是一个开头为`ep-`的字符串，如果不是这个格式，可能是配置错误
- 在终端中输入指令之后报错 `xxx is not a file or directory` 或者 `command not found: xxx`：请检查你的 xxx 安装过程中是否已经进行过环境变量配置。不同的 xxx 安装方法可能有不同的配置方法，一般性的配置方法请参考下面的链接：
    - [Windows 系统](https://blog.csdn.net/wangpaiblog/article/details/113532591)
    - [Mac 系统](https://pgzxc.github.io/posts/b577abb2.html)
    - [Linux 系统](https://zhuanlan.zhihu.com/p/557885534)
- `xxx.tex is not a file or directory` 错误：请确保你把整个 tex 文件夹下载到本地，而不是只下载了 `main.tex` 文件
- `tomllib` 相关的报错：请确保你已经正确填写了 `src/my_config.toml` 中的配置项，尤其是检查引号和括号是否匹配


## 组件

### 智能问答系统

主要功能是基于教材内容的智能问答，使用了检索增强生成（RAG）技术，将教材内容转换为向量数据库，然后通过大语言模型实现智能问答。

### 自动批改系统

自动批改系统组件是一个独立组件，它可以全流程自动化学生作业的批改。它和 [OpenReview](https://openreview.net/) 系统进行交互，从中获取学生提交的作业，LLM将学生回答与标准答案进行比较，并生成相应的反馈，并自动提交到 OpenReview 系统中。详细的使用说明和配置选项请参阅[自动批改系统文档](src/auto_marker/README.md)。

## 注意事项

- 首次运行时需要构建向量数据库，存储在 `storage` 文件夹中，可能需要较长时间，请耐心等待
- 请确保教材文件格式为 tex，其他文本只会当成普通文本处理
- API 密钥请妥善保管，不要泄露（尤其在 fork 本项目时）

## 定制化

本项目可以用于其他课程的智能问答系统构建，以下是一些很容易定制的地方：

### 模型（参数）选择

你可以自由选择 Jina 的 embedding 模型和火山方舟上部署的的大语言模型，只需在 `src/my_config.toml` 中修改相关配置即可，请参考具体的 API 文档。

此外，你还可以设置 temperature，这一参数代表着 LLM 生成文本的随机性，数值越大，生成的文本越随机，数值越小，生成的文本越确定。你可以根据实际情况调整这一参数。只需要在 `src/my_config.toml` 中修改 `llm_temperature` 即可，数值范围为 0 到 1。

 我们还提供了一个参数`similarity_top_k`，这个参数代表着检索时返回的最相似的文本块数量，数值越大，返回的文本块越多，但是检索速度会变慢，和LLM的交互速度也会变慢。你可以根据实际情况调整这一参数。只需要在 `src/my_config.toml` 中修改 `similarity_top_k` 即可。

### 自定义 LaTeX 宏

你可以自由定制 LaTeX 的宏定义（即类似 `\newcommand` 或 `\DeclareMathOperator` 的命令），这样对话系统可以正确显示这些 latex 数学公式。要做到这一点，只需在 [`src/latex_defs.py`](src/latex_defs.py) 中修改 `LATEX_MACROS` 或 `LATEX_COMMANDS` 即可，格式请参考当前的定义。

### 选择 tex 素材文件

只需在 `src/my_config.toml` 中修改 `textbook_main_paths` 即可。当前支持多个主文件（即有 `\documentclass` 的文件），其他所有 tex 文件需要通过 `\input` 或 `\include` 命令（递归地）引入。只需声明主文件即可，系统会自动导入所有相关文件。

### 定制提示词

你可以自由修改 RAG 的相关提示词，只需在 [`src/prompts.py`](src/prompts.py) 中修改对应的提示词即可。这些提示词会影响 RAG 的生成结果，请谨慎修改。提示词的运行方式如下：
- 当用户输入一个问题的时候，系统会使用 `REWRITE_PROMPT` 作为提示词输入 LLM，这一提示词的功能是总结历史对话，然后拼接上当前问题，作为向量数据库的输入。
- 接下来，向量数据库会利用这个输入，检索相关的教材内容，然后利用 `QA_PROMPT` 作为提示词模板，将检索的内容、用户的消息拼接，输出给 LLM，生成回答。
- 在系统初始化时，我们还设置了 `FIRST_ROUND_MSG_USER` 和 `FIRST_ROUND_MSG_ASSISTANT` 作为预设的第一轮对话，这样可以让 LLM 更好地理解它的角色。

你可以根据自己的需求修改这些提示词，但要注意保持提示词的基本结构，比如确保 `QA_PROMPT` 中包含 `{context_str}` 和 `{query_str}` 这些占位符，确保 `REWRITE_PROMPT` 中包含 `{chat_history}` 和 `{question}` 这些占位符。

### 定制 Web 界面文字

你可以自由修改 Web 界面的各种文字，只需要修改 [`src/app.py`](src/app.py) 中的相关字符串即可。

如果你还需要更高级的定制化，下面是一些指导：

### 更广泛的模型选择

当前项目使用了 Jina 和火山方舟的 API，以及 `llama_index` 自带的向量数据库，如果你想使用其他的模型，需要修改 [`src/RAG.py`](src/RAG.py) 中的相关代码，以适应新的模型。
- 修改 `llama_index.embeddings` 相关的 `import` 语句，以及后续对应的应用语句，以适应新的 embedding 模型
- 修改 `llama_index.llms` 相关的 `import` 语句，以及后续对应的应用语句，以适应新的大语言模型
- 修改 `llama_index.core` 导入的 `VectorStoreIndex`、`SimpleDirectoryReader` 和 `StorageContext`，以适应新的向量数据库

### 更广泛的素材文件选择

如果你想使用其他格式的教材文件（例如 docx、pptx），请自行处理文件解析的过程，需要重新实现 [`src/content_construct.py`](src/content_construct.py) 中的 `split_single_file` 函数，这个函数接受一个文件路径，和文本块大小，返回一个文本块列表，即将文件内容分割成一个个文本块。当前的实现是针对 tex 文件的，对 tex 的语法进行额外处理，以保持语义的完整性。

此外，Jina embedding 是一个多模态的 embedding 框架，支持多种数据类型的 embedding，如果你想使用其他格式的数据，可以参考 Jina 的文档，自行实现 embedding 模块。

### 更复杂的 RAG 交互逻辑

本项目使用了 `llama_index` 的 `BaseQueryEngine` 作为 RAG 实现，并使用 `CondenseQuestionChatEngine` 支持多轮对话。如果你想采用流式输出或者更加复杂的交互逻辑，需要重新实现 [`src/RAG.py`](src/RAG.py) 中的 `constructChatEngine` 和 `constructVecDB` 函数，请参考 `llama_index` 的相关文档。

### 更广泛的 Web 界面定制

本项目使用了 Streamlit 作为 Web 应用框架，如果你想要更加复杂的 Web 界面，可以参考 Streamlit 的文档，自行实现更加复杂的 Web 应用。