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

首先，确保你的路径在 `src` 目录下，然后运行以下命令：

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

## 工作流程

0. **准备工作**：准备好配置文件、API 密钥、作业 ID 等信息，注意事项：
   - 确保配置文件里的problem_list已经严格按照要求填写，特别是子问题的格式以及英文标点符号的要求，否则可能会导致系统无法正确解析，请参考样例配置文件
1. **下载提交**：从 OpenReview 下载学生提交
2. **加载参考资料**：加载标准答案和问题描述，该部分由教学团队提供，请确保参考答案和问题描述的格式正确
3. **处理提交**：解析提交内容，提取关键部分
4. **批改**：使用 LLM 评估学生答案与标准答案的匹配度
5. **发布LLM批改**：将自动批改结果发布回 OpenReview
6. **人工校验**：查看和修改批改结果
7. **发布人工批改**：将最终批改结果发布回 OpenReview

## 自动邮件通知的学生作业解析错误

系统包含一个自动邮件通知组件，用于向作业格式存在问题的学生发送提醒邮件。此功能可以在下载和处理学生提交后执行，自动分析日志文件中的警告信息，并向提交有问题的相关学生发送个性化的通知邮件。

### 功能特点

- **自动解析日志**：分析下载和处理阶段的日志文件，提取与学生相关的警告信息
- **分类警告信息**：将警告信息按类型分为提交问题、格式问题、题目编号问题、子问题问题等
- **个性化邮件**：根据学生的具体问题生成个性化的邮件内容
- **支持多种邮箱**：支持多种学校邮箱服务器配置
- **支持测试模式**：提供dry-run模式，可以预览邮件内容而不实际发送

### 使用方法

在使用前，请确保已经下载和处理了学生的提交，并生成了相应的日志文件。然后，在 [`src`](../) 目录下运行以下命令：

```bash
python email_notifier.py --hw_id <作业ID> [选项]
```

### 参数说明

- `--hw_id`：必需，作业ID，例如"1"表示作业1
- `--download_log`：可选，下载日志文件路径（默认：`../log/marker_hw{hw_id}_download.log`）
- `--process_log`：可选，处理日志文件路径（默认：`../log/marker_hw{hw_id}_process.log`）
- `--sender_email`：可选，发件人邮箱地址
- `--sender_password`：可选，发件人邮箱密码
- `--dry_run`：可选，测试模式，只打印邮件内容而不发送
- `--log_file`：可选，指定通知系统的日志文件路径

### 使用示例

1. **测试模式**（查看邮件内容但不发送）：
   ```bash
   python email_notifier.py --hw_id 1 --dry_run
   ```

   如果内容较多，也可以将输出保存到文件中：
   ```bash
   python email_notifier.py --hw_id 1 --dry_run > email_content.txt
   ```
   这样，邮件内容会保存在 `email_content.txt` 文件中。

2. **发送邮件**：
   ```bash
   python email_notifier.py --hw_id 1 --sender_email your_email@pku.edu.cn --sender_password your_password
   ```

3. **使用自定义日志文件**：
   ```bash
   python email_notifier.py --hw_id 1 --download_log custom_download.log --process_log custom_process.log --sender_email your_email@pku.edu.cn --sender_password your_password
   ```

### 邮件内容示例

系统会根据学生的具体问题生成个性化的邮件，例如：

```
张三同学（学号 1234567890），

你好！我们在自动批改系统中发现您提交的作业存在以下问题，请您及时检查并修正：

提交问题：
- HW1-1234567890-张三 submission has duplicate files

文件格式问题：
- Problem 1a in submission 1-1234567890-张三 has ill-formatted content

这些问题可能导致自动批改系统无法正确识别您的答案。请确保：
1. 章节和问题的格式正确
2. 对于有子问题的题目，正确标注子问题编号
3. 提交的文件使用正确的模板（LaTeX或Markdown）

如有任何疑问，请联系课程助教。

此致，
AI中的数学课助教团队
```

> **注意**：确保发送邮件前已经获得相应的邮箱权限，特别是使用学校邮箱时可能需要特殊的SMTP设置或应用专用密码。

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

参考答案应采用与学生提交相同的 LaTeX 格式，放置在配置文件中指定的参考资料目录中。文件命名应为 `HW{作业ID}-answer.tex`。也可参考 [`sample-problem-material.tex`](sample-problem-material.tex) 文件。

### 如何创建问题描述？

问题描述同样使用 LaTeX 格式，命名为 `HW{作业ID}-description.tex`，放置在参考资料目录中。也可参考 [`sample-problem-material.tex`](sample-problem-material.tex) 文件。

### 如何处理人工校验？

系统会在 `human_marks` 目录中为每个提交创建一个 Markdown 文件，您可以直接编辑这些文件来修改批改内容。完成编辑后，运行 `--post-human` 步骤发布修改后的结果。
