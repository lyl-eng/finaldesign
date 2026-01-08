# 多智能体翻译系统使用说明

## 概述

本模块实现了基于Griptape框架的多智能体翻译工作流系统，将传统的线性翻译流程转变为开放、协作和迭代优化的智能工作流。

## 系统架构

### Agent组成

1. **PreprocessingAgent (译前预处理Agent)**
   - 文本结构拆解：按段落、逻辑块、章节边界切分
   - 语域与风格识别：自动判断领域（法律、文学、新闻等）和语体风格（正式、口语化等）

2. **TerminologyEntityAgent (术语与实体Agent)**
   - 智能术语识别：
     - 命名实体（NER）：人名、地名、机构名等
     - 领域术语：专业词汇和短语
     - 文化负载词：缺乏直接对等表达的词汇
   - 知识库集成（RAG）：利用外部资源查证术语
   - 全局一致性控制：确保术语翻译在全文中保持一致

3. **TranslationRefinementAgent (翻译与优化Agent)**
   - 多步骤引导翻译：理解—分解—转换—润色
   - 多版本生成与融合：生成直译版、意译版、风格化版并智能融合
   - 回译验证与自我修正（TEaR）：回译验证、质量评估、自动修正

4. **HumanCollaborationNode (人机协作节点)**
   - 在关键质量控制节点提供人工介入
   - 术语审核、翻译审核、错误修正

### 工作流程

```
输入文件
  ↓
[PreprocessingAgent] 译前预处理
  ├─ 文本结构拆解
  └─ 语域风格识别
  ↓
[TerminologyEntityAgent] 术语识别
  ├─ NER识别
  ├─ 领域术语识别
  ├─ 文化负载词识别
  ├─ 知识库查证
  └─ 构建术语库
  ↓
[HumanCollaborationNode] 人工审核（可选）
  └─ 术语审核
  ↓
[TranslationRefinementAgent] 翻译执行
  ├─ 多步骤翻译
  ├─ 多版本生成
  ├─ 版本融合
  ├─ 回译验证
  └─ 自我修正
  ↓
[HumanCollaborationNode] 人工审核（可选）
  └─ 翻译审核
  ↓
输出文件
```

## 使用方法

### 1. 启用多智能体模式

在配置文件中设置 `use_multi_agent_mode: true`，或在UI界面中启用多智能体模式选项。

### 2. 配置要求

- 确保已安装Griptape框架：`pip install griptape[all]`
- 配置LLM API（支持OpenAI、Anthropic、Google等）
- 配置NER模型（用于命名实体识别）

### 3. 执行翻译

1. 加载源文件
2. 选择"开始翻译"
3. 系统会自动执行多智能体工作流
4. 在需要时进行人工审核

## 配置说明

### 多智能体模式配置

在 `Resource/config.json` 中添加：

```json
{
  "use_multi_agent_mode": true,
  "multi_agent": {
    "enable_human_intervention": true,
    "terminology_review_threshold": 10,
    "translation_review_threshold": 0.8
  }
}
```

### NER模型配置

确保NER模型文件位于 `Resource/Models/ner/` 目录下。

## 功能特性

### 1. 智能术语识别

- 自动识别命名实体、领域术语、文化负载词
- 使用LLM进行语境感知和语义推理
- 支持外部知识库查证（RAG）

### 2. 全局一致性保障

- 构建项目专属术语库
- 在翻译过程中强制使用规范译法
- 确保全书术语翻译一致

### 3. 多版本翻译融合

- 生成多个翻译版本（直译、意译、风格化）
- 使用LLM智能评选和融合
- 达到最佳翻译效果

### 4. 回译验证（TEaR）

- 自动回译验证
- 质量评估和问题识别
- 自我修正机制

### 5. 人机协作

- 关键节点人工介入
- 术语审核界面
- 翻译审核界面

## Memory机制

系统会存储以下信息到Memory中：

- 已翻译文本摘要
- 原文分析结果
- 读者倾向分析
- 翻译风格指南
- 领域和风格信息

这些信息会动态加载到prompt中，提升翻译质量。

## 注意事项

1. **性能考虑**：多智能体模式会进行多次LLM调用，可能比传统模式慢
2. **成本考虑**：多版本生成和回译验证会增加API调用成本
3. **人工介入**：建议在关键术语首次出现时进行人工审核
4. **Griptape集成**：当前版本使用简化的工作流实现，完整Griptape集成需要进一步开发

## 扩展开发

### 添加新的Agent

1. 继承 `BaseAgent` 类
2. 实现 `execute()` 方法
3. 在 `WorkflowManager` 中注册

### 自定义工作流

修改 `WorkflowManager.execute_workflow()` 方法，调整Agent执行顺序和交互方式。

## 故障排除

### Griptape未安装

如果Griptape未安装，系统会自动使用简化的工作流实现，功能不受影响。

### NER识别失败

检查NER模型文件是否存在，路径是否正确。

### LLM调用失败

检查API配置是否正确，网络连接是否正常。

## 未来改进

1. 完整的Griptape工作流集成
2. 更智能的版本融合算法
3. 增强的RAG知识库集成
4. 更完善的人工协作界面
5. 工作流可视化
