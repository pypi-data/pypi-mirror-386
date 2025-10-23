以下是将您的 AsyncCallAI 库与 RAG Knowledge Base & AI Toolkit 整合的完整 README：

# AsyncCallAI & RAG Knowledge Base - 智能AI对话与知识库系统

一个功能强大的Python工具包，集成了异步AI对话调用、RAG（检索增强生成）知识库构建、云存储操作和数据处理等多种功能。特别适用于需要结合外部知识进行智能对话和数据管理的场景。

## 🚀 核心功能

### 1. **异步AI对话系统 (AsyncCallAi)**
基于异步编程的高效AI对话调用库，支持批量并发处理多个对话请求：

- 🚀 **异步并发**：使用 asyncio 实现高效的批量请求处理
- 🐱 **角色扮演**：支持自定义系统提示词，实现角色扮演功能
- 🔧 **灵活配置**：可自定义API密钥和基础URL
- 🛡️ **错误处理**：完善的异常处理机制
- 📝 **结果展示**：清晰的请求-响应结果输出

### 2. **RAG知识库系统 (P_RAGKnowledgeBase)**
基于检索增强生成架构的知识库管理系统，支持多种数据源构建向量数据库：

- **PDF文档处理**：自动提取PDF文本并分割为向量块
- **原始文本处理**：直接处理结构化或非结构化文本
- **数据库Schema构建**：将数据库表结构转换为可检索的知识
- **智能文本分割**：使用重叠分块保持上下文连贯性

### 3. **AI模型调用 (CallAi & CallBailianApp)**
支持多种AI服务接口的统一调用：

- **OpenAI兼容接口**：支持任何兼容OpenAI API的模型服务
- **阿里云百炼平台**：专为阿里云DashScope应用设计
- **RAG增强对话**：可结合知识库上下文生成更准确的回答
- **灵活的提示词管理**：支持动态修改系统提示词模板

### 4. **云存储集成 (OSSHandler)**
阿里云OSS对象存储的便捷操作接口：

- **文件上传下载**：本地与OSS间的文件同步
- **Excel数据处理**：直接从OSS读取Excel文件为DataFrame
- **格式验证**：自动验证文件类型和存在性

### 5. **数据导出与邮件发送 (ExportToEmail)**
将数据处理结果自动化发送：

- **Excel导出**：DataFrame自动转换为Excel格式
- **邮件发送**：支持HTML格式邮件和附件
- **临时文件管理**：自动清理生成的临时文件

## 🛠 安装依赖

```bash
pip install openai httpx python-dotenv pandas oss2 sentence-transformers faiss-cpu PyPDF2 langchain dashscope
```

## ⚙️ 环境配置

创建 `.env` 文件配置必要的环境变量：

```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=your_base_url

# 阿里云OSS配置
ACCESS_KEY_ID=your_access_key_id
ACCESS_KEY_SECRET=your_access_key_secret
ENDPOINT=your_oss_endpoint
BUCKET_NAME=your_bucket_name

# 邮件服务配置
email_sender=your_email@163.com
email_password=your_smtp_password
```

## 📚 使用示例

### 1. **异步AI对话 - 基础用法**

```python
from async_ai_toolkit import AsyncCallAi
import asyncio

async def main():
    # 初始化异步AI客户端
    obj = AsyncCallAi()
    
    # 设置猫咪角色提示词
    obj.prompt = """你现在是一只刚满1岁的小奶猫，会用人类的话和我聊天，超黏人超可爱！"""
    
    # 批量对话处理
    prompts = [
        "解释什么是异步编程",
        "写一个简单的Python列表推导式示例",
        "总结并发与并行的区别"
    ]
    
    # 并发执行所有对话请求
    await obj.chat(prompts)

# 运行
if __name__ == '__main__':
    asyncio.run(main())
```

### 2. **RAG知识库构建与检索**

```python
from async_ai_toolkit import P_RAGKnowledgeBase, AsyncCallAi
import asyncio

async def rag_example():
    # 构建知识库
    kb = P_RAGKnowledgeBase(chunk_size=500, chunk_overlap=50)
    kb.build_from_pdf("document.pdf")
    
    # 初始化AI客户端
    ai = AsyncCallAi()
    ai.prompt = "你是一个专业的助手，请根据知识库内容回答问题。"
    
    # RAG增强对话
    question = "文档中提到的关键技术是什么？"
    response = await ai.get_openai_response(question)  # 普通回答
    
    # 结合知识库的RAG回答
    rag_response = await ai.get_openai_response(question, knowledge_base=kb)
    
    return response, rag_response

asyncio.run(rag_example())
```

### 3. **完整业务流程示例**

```python
from async_ai_toolkit import AsyncCallAi, P_RAGKnowledgeBase, OSSHandler, ExportToEmail
import asyncio
import pandas as pd

async def complete_workflow():
    """完整的业务处理流程：知识库构建 → AI分析 → 结果导出"""
    
    # 1. 从OSS获取数据
    oss = OSSHandler()
    df = oss.get_excel_from_oss("business_data.xlsx")
    
    # 2. 构建业务知识库
    kb = P_RAGKnowledgeBase()
    kb.build_from_text("业务规则文档内容...")
    
    # 3. AI分析数据
    ai = AsyncCallAi()
    ai.prompt = "你是一个业务分析师，请分析数据并提供见解。"
    
    analysis_prompts = [
        f"分析销售趋势: {df['sales'].tail(10).tolist()}",
        f"客户分布情况: {df['customers'].describe().to_dict()}"
    ]
    
    results = await ai.chat(analysis_prompts)
    
    # 4. 导出结果到邮箱
    result_df = pd.DataFrame(results)
    email_result = ExportToEmail(
        df=result_df,
        receiver="team@company.com",
        subject="业务分析报告"
    )
    
    return email_result

# 执行完整流程
asyncio.run(complete_workflow())
```

### 4. **数据库Schema智能问答**

```python
from async_ai_toolkit import AsyncCallAi, construct_schema
import asyncio

async def database_assistant():
    # 构建数据库Schema知识库
    schema_dict, schema_text = construct_schema(
        desc_path="table_desc.xlsx",
        sample_data_path="sample_data.xlsx", 
        table_name="database.users"
    )
    
    # 初始化数据库助手AI
    ai = AsyncCallAi()
    ai.prompt = f"""你是一个数据库专家，请基于以下表结构回答问题：
    
    {schema_text}
    
    请用专业的SQL术语回答用户问题。"""
    
    # 数据库相关问题
    questions = [
        "如何查询所有活跃用户？",
        "用户表的索引结构是怎样的？",
        "写一个统计用户注册量的SQL"
    ]
    
    # 批量获取专业回答
    answers = await ai.chat(questions)
    
    for q, a in zip(questions, answers):
        print(f"Q: {q}")
        print(f"A: {a}\n")

asyncio.run(database_assistant())
```

## 🔧 核心类详解

### AsyncCallAi - 异步AI对话

**主要方法：**
- `async chat(text_list)`: 批量处理对话请求
- `async get_openai_response(text, knowledge_base=None)`: 单个对话请求，支持知识库增强
- `prompt`属性: 获取或设置系统提示词模板

**异步优势：**
```python
# 传统同步方式（顺序执行，总时间=各请求时间之和）
results = []
for prompt in prompts:
    result = sync_ai.chat(prompt)  # 等待上一个完成
    results.append(result)

# 异步方式（并发执行，总时间≈最慢请求时间）
tasks = [async_ai.get_openai_response(prompt) for prompt in prompts]
results = await asyncio.gather(*tasks)  # 同时发起所有请求
```

### P_RAGKnowledgeBase - 知识库管理

**主要方法：**
- `build_from_pdf(file_path)`: 从PDF文件构建向量知识库
- `build_from_text(text)`: 从原始文本构建知识库  
- `build_from_schema(schema)`: 从数据库Schema字典构建知识库
- `search(query, k=3)`: 检索相关知识片段

## 🎯 应用场景

### 智能客服系统
```python
async def customer_service():
    ai = AsyncCallAi()
    ai.prompt = "你是专业的客服助手，请友好回答用户问题。"
    
    # 批量处理用户咨询
    user_questions = await get_pending_questions()  # 从数据库获取待处理问题
    responses = await ai.chat(user_questions)
    
    # 保存回答到数据库
    await save_responses(responses)
```

### 文档智能分析
```python
async def document_analysis():
    # 构建文档知识库
    kb = P_RAGKnowledgeBase()
    kb.build_from_pdf("research_paper.pdf")
    
    ai = AsyncCallAi()
    ai.prompt = "请基于文档内容回答技术问题。"
    
    # RAG增强的技术问答
    technical_questions = [
        "论文的主要贡献是什么？",
        "实验方法部分的关键步骤有哪些？",
        "研究结论对实际应用有什么意义？"
    ]
    
    return await ai.chat(technical_questions, knowledge_base=kb)
```

### 数据报告自动化
```python
async def automated_reporting():
    # 从多个数据源构建知识库
    kb = P_RAGKnowledgeBase()
    kb.build_from_pdf("business_guidelines.pdf")
    kb.build_from_text("季度业绩数据...")
    
    ai = AsyncCallAi()
    ai.prompt = "基于业务知识库分析数据并生成报告。"
    
    analysis_requests = [
        "分析本季度销售趋势",
        "评估市场风险因素", 
        "提供下季度业务建议"
    ]
    
    reports = await ai.chat(analysis_requests, knowledge_base=kb)
    
    # 自动发送报告邮件
    for report in reports:
        ExportToEmail(df=pd.DataFrame([report]), receiver="management@company.com")
```

## ⚡ 性能优势

### 并发处理对比
| 场景 | 同步处理 | 异步处理 |
|------|----------|----------|
| 10个API请求 | 30秒（3秒/个） | 3秒（并发） |
| 100个对话 | 300秒 | 30秒 |
| 混合操作 | 顺序执行 | 并行执行 |

### 代码示例
```python
import asyncio
import time

async def benchmark():
    ai = AsyncCallAi()
    prompts = [f"问题{i}" for i in range(10)]
    
    # 异步并发
    start = time.time()
    results = await ai.chat(prompts)
    async_time = time.time() - start
    
    print(f"异步处理10个请求: {async_time:.2f}秒")
    return results

asyncio.run(benchmark())
```

## 🔄 扩展开发

项目采用模块化设计，易于扩展：

- **添加新的AI服务**：继承基础AI类实现特定接口
- **支持新的文件格式**：在相应处理器中添加格式解析逻辑  
- **自定义知识库来源**：实现新的`build_from_*`方法
- **集成其他云服务**：添加新的处理器类

## ⚠️ 注意事项

1. **异步环境**：确保在异步环境中使用（asyncio、Jupyter等）
2. **API限制**：合理控制并发数量，避免触发API限制
3. **资源管理**：及时关闭连接，清理临时文件
4. **错误处理**：所有操作都有完善的异常处理机制
