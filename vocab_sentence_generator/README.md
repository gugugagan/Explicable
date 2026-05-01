# Anki Vocabulary Sentence Generator / 单词句子生成器

一个 1-2 天 MVP 规模的桌面工具：导入 CSV 单词表，按每日背词数量自动分组，为每组生成 AI prompt，可调用 OpenAI 生成英文例句、中文翻译和中文释义，最后导出 Markdown。

## 功能

- 导入 CSV，容错识别 `word` / `vocabulary` / `Word` 等单词列，以及 `pos` / `part_of_speech` 等词性列
- 按每日背词数量稳定分组，尽量混合 noun、verb、adjective、adverb 等词性
- 为每组输出 JSON 配置文件
- 无 API Key 时自动使用 mock 模式，保证完整流程可跑通
- 支持 `easy`、`medium`、`hard` 例句难度
- 导出 `output/vocabulary_plan.md`
- PySide6 GUI，支持按钮选择 CSV，也支持拖拽 CSV 到路径框

## 安装依赖

建议使用 Python 3.11+。

```powershell
cd vocab_sentence_generator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 运行

```powershell
python main.py
```

默认输出结构：

```text
output/
  configs/
    group_001.json
    group_002.json
  vocabulary_plan.md
```

## CSV 格式示例

最低要求包含单词和词性两列：

```csv
word,pos
apple,noun
eat,verb
fresh,adjective
quickly,adverb
```

也支持常见同义列名，例如：

```csv
Vocabulary,part_of_speech,Chinese Meaning
apple,noun,苹果
eat,verb,吃
```

## 配置 OpenAI API Key

不配置 API Key 时，程序会自动进入 mock 模式。

临时配置当前 PowerShell 会话：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
$env:OPENAI_MODEL="gpt-4.1-mini"
python main.py
```

长期写入 Windows 用户环境变量：

```powershell
setx OPENAI_API_KEY "你的 API Key"
setx OPENAI_MODEL "gpt-4.1-mini"
```

重新打开终端后生效。

## 打包成 exe

安装 PyInstaller：

```powershell
pip install pyinstaller
```

打包：

```powershell
pyinstaller --noconsole --onefile --name VocabSentenceGenerator main.py
```

生成文件位于：

```text
dist/VocabSentenceGenerator.exe
```

打包后的程序会把 `output` 目录创建在 exe 所在目录。

## 当前 MVP 限制

- 分组策略是稳定、可预测的简单词性轮询，不会真正理解词义关系
- OpenAI 返回内容按 JSON 解析，若模型输出不规范会自动回退到 mock 占位内容
- GUI 生成 Markdown 时为同步调用，词表很大或网络较慢时界面可能短暂停顿
- mock 模式只生成占位例句和占位释义，不代表真实学习内容

## 后续可扩展方向

- 用词义相似度、主题聚类或语法模板改进分组算法
- 增加 Anki CSV / TSV 直接导出
- 增加后台线程和进度条，避免长时间 AI 调用阻塞 UI
- 增加 Prompt 模板编辑器
- 增加生成结果预览与单组重试
- 增加本地模型或其他 AI Provider 适配器
