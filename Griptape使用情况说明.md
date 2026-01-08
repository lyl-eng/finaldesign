# Griptape框架使用说明

## 当前状态

**✅ Griptape框架已集成并正在使用**

本项目现在**真正使用Griptape框架**来构建和管理多智能体工作流。

## 实现架构

### 1. Griptape Tools

在 `ModuleFolders/MultiAgent/GriptapeTools.py` 中，我们将自定义Agent的功能封装为Griptape Tools：

- **PreprocessingTool**: 预处理工具，封装了文本结构拆解和语域风格识别功能
- **TerminologyTool**: 术语识别工具，封装了NER、领域术语、文化负载词识别功能
- **TranslationTool**: 翻译工具，封装了多步骤翻译、多版本融合、回译验证功能

这些Tools继承自 `griptape.tools.BaseTool`，并实现了 `@BaseTool.activities` 装饰器来定义工具的活动。

### 2. Griptape Agents

在 `ModuleFolders/MultiAgent/WorkflowManager.py` 中，我们创建了三个Griptape Agent：

- **PreprocessingAgent**: 预处理Agent，配备PreprocessingTool
- **TerminologyEntityAgent**: 术语识别Agent，配备TerminologyTool
- **TranslationRefinementAgent**: 翻译Agent，配备TranslationTool

每个Agent都使用自定义的 `OpenAiChatPromptDriver`，支持DeepSeek等OpenAI兼容的API。

### 3. Griptape Workflow

工作流使用 `griptape.structures.Workflow` 来编排：

```python
# 创建Workflow
self.griptape_workflow = Workflow()

# 创建Tasks（使用ToolkitTask）
task1 = ToolkitTask("...", tools=[preprocessing_tool], agent=preprocessing_agent)
task2 = ToolkitTask("...", tools=[terminology_tool], agent=terminology_agent)
task3 = ToolkitTask("...", tools=[translation_tool], agent=translation_agent)

# 添加任务到工作流
self.griptape_workflow.add_task(task1)
self.griptape_workflow.add_task(task2)
self.griptape_workflow.add_task(task3)
```

### 4. 执行流程

当调用 `execute_workflow()` 时：

1. 将 `CacheProject` 转换为JSON字符串
2. 调用 `self.griptape_workflow.run(initial_input)` 执行Griptape工作流
3. Griptape按顺序执行所有Tasks，每个Task使用对应的Agent和Tool
4. 从工作流输出中提取结果

## LLM配置

Griptape Agents使用自定义的 `OpenAiChatPromptDriver`，配置如下：

- **API URL**: 从 `TaskConfig` 获取，支持DeepSeek等自定义API
- **API Key**: 从 `TaskConfig` 获取
- **Model**: 从 `TaskConfig` 获取（默认 "deepseek-chat"）
- **Temperature/Top_p**: 从平台配置获取

## 工作流执行

Griptape工作流会自动处理：

- **任务依赖**: Task2依赖Task1的输出，Task3依赖Task2的输出
- **Agent调用**: 每个Task由对应的Agent执行
- **Tool调用**: Agent通过Tool来执行具体的功能
- **结果传递**: 前一个Task的输出自动传递给下一个Task

## 回退机制

如果Griptape工作流执行失败，系统会自动回退到直接调用Agent的模式（`_execute_fallback_workflow`），确保系统的稳定性。

## 依赖要求

确保安装了Griptape：

```bash
pip install griptape[all]>=0.20.0
```

## 总结

✅ **Griptape框架已完全集成**
✅ **使用Griptape的Workflow、Agent、Task和Tool架构**
✅ **支持自定义LLM（DeepSeek等）**
✅ **实现了完整的多智能体工作流编排**

系统现在真正基于Griptape框架运行，而不是简单的自定义实现。