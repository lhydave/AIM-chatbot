# 自动批改系统

## 概述

自动批改系统是 AIM-chatbot 系统的一个独立组件，用于对学生作业的自动批改。它和 [OpenReview](https://openreview.net/) 系统进行交互，从中获取学生提交的作业，LLM 将学生回答与标准答案进行比较，并生成相应的反馈，并自动提交到 OpenReview 系统中。

## 功能特点

- 批改全自动化：从下载、处理到批改、发布，全程自动化
- 支持多种提交格式：Markdown 或 LaTeX
- 支持多种题型：章节结构、子问题、分类讨论、表格、数学公式、代码和算法（暂时不支持图片）
- 精确到题目批改：针对学生提交的单个文件，支持解析出每个问题答案并分别批改
- 使用异步批改：支持并行批改多个学生提交，显著提高效率
- 高度定制化：支持自定义配置，包括 LLM 参数、文件路径、作业 ID、批改提示等
- 日志记录：记录全流程的详细信息，方便追踪和调试
- 大模型与人工校验结合：使用大语言模型（LLM）进行批改，同时有人类可读的批改结果，方便人工校验和修改


## 使用方法

自动批改系统通过命令行应用程序运行。工作流程通常包含下载、加载参考资料、处理、批改和发布结果这几个步骤，这些步骤可以单独或组合执行。

### 基本用法

```bash
python marker_app.py [--config path/to/config.toml] [步骤选项] [其他选项]
```

### 参数说明

- `--config` 或 `-c`: 可选，配置文件路径（默认：`./auto_marker/my_marker_config.toml`）
- 工作流步骤选项（可单独或组合使用）：
  - `--download`: 从 OpenReview 下载提交，如果已经下载过，则不会重复下载，而是会把内容加载到系统中
  - `--reference`: 加载参考资料（标准答案和问题描述）
  - `--process`: 处理提交
  - `--mark`: 批改提交
  - `--post-llm`: 将LLM批改结果发布到 OpenReview
  - `--post-human`: 将人工校验后的批改结果发布到 OpenReview
- `--log-level` 或 `-l`: 可选，日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

### 使用示例

1. **完整工作流程**（下载、加载参考资料、处理、批改、发布LLM结果）：
   ```bash
   python marker_app.py --download --reference --process --mark --post-llm
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
   python marker_app.py -c ./my_custom_config.toml --download --process --mark --post-llm -l DEBUG
   ```

5. **仅处理已下载的提交**：
   ```bash
   python marker_app.py --reference --process
   ```

6. **人工校验后发布结果**：
   ```bash
   python marker_app.py --post-human
   ```

### 一般工作流逻辑

典型的批改流程按照以下顺序执行：

1. **配置**：准备好配置文件，包括作业 ID、API 密钥等设置
2. **下载（--download）**：从 OpenReview 平台下载学生提交到 `raw_submissions` 目录
3. **加载参考资料（--reference）**：从指定位置加载标准答案和问题描述
4. **处理（--process）**：解析提交内容，将其结构化并提取问题答案，存储到 `processed_submissions`
5. **批改（--mark）**：使用 LLM 对处理后的提交内容进行批改，生成批改结果
6. **发布LLM结果（--post-llm）**：将自动批改结果上传至 OpenReview 平台
7. **人工校验和发布（--post-human）**：查看和修改批改结果，然后将最终结果上传至 OpenReview 平台

您可以根据需要选择执行部分步骤。例如，如果提交已下载但需要重新批改，可以只运行 `--mark --post-llm` 步骤。

> **注意**：确保在运行步骤前已准备好前置步骤所需的数据。例如，要运行 `--mark` 步骤，必须已有处理好的提交数据。
> 
> 特别注意，尽管课程可以设置提交的格式要求，但是人难免会忽略或者错误理解这一格式要求，因此，如果对可靠性要求很高，请务必人工核查保证--process步骤之后对题目的分解是正确的。系统日志会把所有可能出现的问题记录下来，方便人工核查。

## 配置文件

系统使用 TOML 格式的配置文件，请参考 [`sample_marker_config.toml`](sample_marker_config.toml) 文件，创建您自己的配置文件。主要配置项包括 OpenReview 连接信息、LLM API 设置、文件路径、作业 ID 和批改提示模板。

## 提交格式

系统支持 Markdown 或 LaTeX 格式的提交，包含以下特性：

- 章节结构（标题和子标题）
- 子问题结构
- 分类讨论
- 表格支持
- LaTeX 数学公式
- 代码和算法

样例可以参考 [`sample-homework/sample-markdown-homework.md`](sample-homework/sample-markdown-homework.md) 和 [`sample-homework/sample-latex-homework.tex`](sample-homework/sample-tex-homework.tex) 文件。

> *注意：请严格按照样例格式提交作业，否则可能导致系统出现错误。*

## 工作流程以及人工校验的步骤

0. **准备工作**：准备好配置文件、API 密钥、作业 ID 等信息，注意事项：
   1. 确保配置文件里的problem_list已经严格按照要求填写，特别是子问题的格式以及英文标点符号的要求，否则可能会导致系统无法正确解析，请参考样例配置文件
1. **下载提交**：从 OpenReview 下载学生提交，可能需要做的人工校验包括：
   1. 检查提交的标题格式是否正确，如果不正确，系统会跳过这一提交并报告 warning
       - **解决方案**：请到 OpenReview 平台人工将标题格式修改为正确格式
   2. 检查每个学生每次作业是否有重复提交，系统会忽略重复提交并报告 warning 
      - **解决方案**：请到 OpenReview 平台人工删除重复提交
   3. 检查提交的压缩包中是否恰好包含一个 `.tex` 或 `.md` 文件，如果不是，系统会报告 warning
      - **解决方案**：请将解压出来的文件进行人工整理，如果缺失文件，请与学生进行联系
2. **加载参考资料**：加载标准答案和问题描述，该部分由教学团队提供，请确保参考答案和问题描述的格式正确
3. **处理提交**：解析提交内容，提取关键部分，可能需要做的人工校验包括：
   1. 每个提交是否解析出来了所有的问题回答、包括子问题回答，如果没有，系统会报告warning并使用默认回答来替代
      - **解决方案**：请检查学生提交是否符合格式要求，如果不符合，可以自行修改（如果不符合的程度较低）或者要求学生重新提交（如果不符合的程度太高）。
   2. 每个提交是否解析出来了额外的子问题，如果有，系统会报告warning
      - **解决方案**：请检查学生提交是否符合格式要求，如果不符合，可以自行修改（如果不符合的程度较低）或者要求学生重新提交（如果不符合的程度太高）。例如，学生可能用 `####` 来分割非子问题的内容，这样会导致系统错误地将其解析为子问题。
4. **批改**：使用 LLM 评估学生答案与标准答案的匹配度
5. **发布LLM批改**：将自动批改结果发布回 OpenReview
6. **人工校验**：查看和修改批改结果
7. **发布人工批改**：将最终批改结果发布回 OpenReview

## 存储内容

系统运行后会生成以下文件：

- **原始提交**：保存在 `raw_submissions/HW{作业ID}` 目录中，包括学生的 PDF 文件、原始压缩包和解压缩后的所有文件
- **处理后的提交**：保存在 `processed_submissions/HW{作业ID}` 目录中
  - `submission{提交编号}-{学生ID}-{学生姓名}.json`: 包含解析后的提交内容和批改结果
  - `submission{提交编号}-{学生ID}-{学生姓名}-llm_marks.md`: 包含LLM批改结果的 Markdown 格式文件，可直接发布到 OpenReview
- **人工批改文件**：保存在 `human_marks/HW{作业ID}` 目录中
  - `submission{提交编号}-{学生ID}-{学生姓名}.pdf`: 学生提交的PDF文件，方便查看原始内容
  - `submission{提交编号}-{学生ID}-{学生姓名}-human_marks.md`: LLM批改结果的副本，用于人工修改后发布
- **批改日志**：保存在 `mark_logs/HW{作业ID}` 目录中，每个问题一个日志文件（格式为 `submission{提交编号}_{问题ID}.txt`），记录了和 LLM 的所有交互，包括思考内容（如果有）
- **系统日志**：保存在 `log` 目录中，每个步骤一个日志文件，记录了系统运行的详细信息

## 常见问题

### 如何创建参考答案？

参考答案应采用与学生提交相同的 Markdown 格式，放置在配置文件中指定的参考资料目录中。文件命名应为 `HW{作业ID}-answer.md`。也可参考 [`sample-problem-material.md`](sample-problem-material.md) 文件。

### 如何创建问题描述？

问题描述同样使用 Markdown 格式，命名为 `HW{作业ID}-description.md`，放置在参考资料目录中。也可参考 [`sample-problem-material.md`](sample-problem-material.md) 文件。

### 如何处理人工校验？

系统会在 `human_marks` 目录中为每个提交创建一个 Markdown 文件，您可以直接编辑这些文件来修改批改内容。完成编辑后，运行 `--post-human` 步骤发布修改后的结果。
