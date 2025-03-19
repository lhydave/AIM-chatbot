# 自动批改系统

## 概述

自动批改系统是 AIM-chatbot 系统的一个独立组件，用于对学生作业的自动批改。它和 [OpenReview](https://openreview.net/) 系统进行交互，从中获取学生提交的作业，LLM 将学生回答与标准答案进行比较，并生成相应的反馈，并自动提交到 OpenReview 系统中。

## 功能特点

- 批改全自动化：从下载、处理到批改、发布，全程自动化
- 支持多种提交格式：Markdown 或 LaTeX
- 支持多种题型：章节结构、子问题、分类讨论、表格、数学公式、代码和算法（暂时不支持图片）
- 使用异步批改：支持并行批改多个学生提交，显著提高效率
- 高度定制化：支持自定义配置，包括 LLM 参数、文件路径、作业 ID、批改提示等
- 日志记录：记录全流程的详细信息，方便追踪和调试
- 大模型与人工校验结合：使用大语言模型（LLM）进行批改，同时有人类可读的批改结果，方便人工校验


## 使用方法

自动批改系统通过命令行应用程序运行。工作流程通常包含下载、处理、批改和发布结果这几个步骤，这些步骤可以单独或组合执行。

### 基本用法

```bash
python marker_app.py [--config path/to/config.toml] [步骤选项] [其他选项]
```

### 参数说明

- `--config` 或 `-c`: 可选，配置文件路径（默认：`./auto_marker/my_marker_config.toml`）
- 工作流步骤选项（可单独或组合使用）：
  - `--download`: 从 OpenReview 下载提交
  - `--reference`: 加载参考资料（标准答案和问题描述）
  - `--process`: 处理提交
  - `--mark`: 批改提交
  - `--post`: 将批改发布到 OpenReview
- `--log-level` 或 `-l`: 可选，日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

### 使用示例

1. **完整工作流程**（下载、加载参考资料、处理、批改、发布）：
   ```bash
   python marker_app.py --download --reference --process --mark --post
   ```

2. **仅下载提交**：
   ```bash
   python marker_app.py --download
   ```

3. **处理和批改但不发布**：
   ```bash
   python marker_app.py --process --mark
   ```

4. **使用自定义配置文件并设置日志级别**：
   ```bash
   python marker_app.py -c ./my_custom_config.toml --download --process --mark --post -l DEBUG
   ```

5. **仅处理已下载的提交**：
   ```bash
   python marker_app.py --reference --process
   ```

### 一般工作流逻辑

典型的批改流程按照以下顺序执行：

1. **配置**：准备好配置文件，包括作业 ID、API 密钥等设置
2. **下载（--download）**：从 OpenReview 平台下载学生提交到 `raw_submissions` 目录
3. **加载参考资料（--reference）**：从指定位置加载标准答案和问题描述
4. **处理（--process）**：解析提交内容，将其结构化并提取问题答案，存储到 `processed_submissions`
5. **批改（--mark）**：使用 LLM 对处理后的提交内容进行批改，生成批改结果
6. **发布（--post）**：将批改结果上传至 OpenReview 平台

您可以根据需要选择执行部分步骤。例如，如果提交已下载但需要重新批改，可以只运行 `--mark --post` 步骤。

> **注意**：确保在运行步骤前已准备好前置步骤所需的数据。例如，要运行 `--mark` 步骤，必须已有处理好的提交数据。

## 配置文件

系统使用 TOML 格式的配置文件，请参考 `src/auto_marker/sample_marker_config.toml` 创建您自己的配置文件。主要配置项包括 OpenReview 连接信息、LLM API 设置、文件路径、作业 ID 和批改提示模板。

## 提交格式

系统支持 Markdown 或 LaTeX 格式的提交，包含以下特性：

- 章节结构（标题和子标题）
- 子问题结构
- 分类讨论
- 图片支持
- 表格支持
- LaTeX 数学公式
- 代码和算法

样例可以参考 `src/auto_marker/sample-homework/sample-markdown-homework.md` 和 `src/auto_marker/sample-homework/sample-latex-homework.tex` 文件。

> *注意：请严格按照样例格式提交作业，否则可能导致系统出现错误。*

## 工作流程

1. **下载提交**：从 OpenReview 下载学生提交
2. **加载参考资料**：加载标准答案和问题描述
3. **处理提交**：解析提交内容，提取关键部分
4. **批改**：使用 LLM 评估学生答案与标准答案的匹配度
5. **发布批改**：将批改结果发布回 OpenReview

## 存储内容

系统运行后会生成以下文件：

- **原始提交**：保存在 `raw_submissions/HW{作业ID}` 目录中，包括学生的 PDF 文件、原始压缩包和解压缩后的所有文件
- **处理后的提交**：保存在 `processed_submissions/HW{作业ID}` 目录中
  - `{学生ID}-{学生姓名}.json`: 包含解析后的提交内容和批改结果
  - `{学生ID}-{学生姓名}-marks.md`: 包含批改结果的 Markdown 格式文件，可直接发布到 OpenReview
- **批改日志**：保存在 `mark_logs/HW{作业ID}` 目录中，每个问题一个日志文件，记录了和 LLM 的所有交互，包括思考内容
- **系统日志**：保存在 `log` 目录中，每个步骤一个日志文件，记录了系统运行的详细信息

## 常见问题

### 如何创建参考答案？

参考答案应采用与学生提交相同的 Markdown 格式，放置在配置文件中指定的参考资料目录中。文件命名应为 `HW{作业ID}-answer.md`。也可参考 `src/auto_marker/sample-problem-material.md` 文件。

### 如何创建问题描述？

问题描述同样使用 Markdown 格式，命名为 `HW{作业ID}-description.md`，放置在参考资料目录中。也可参考 `src/auto_marker/sample-problem-material.md` 文件。
