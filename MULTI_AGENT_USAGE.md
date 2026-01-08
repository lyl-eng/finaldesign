# 多智能体翻译系统使用说明

## ✅ 已完成的功能

### 1. Planning Agent（规划Agent）
- **功能**：任务分析、执行计划制定、资源评估
- **位置**：`ModuleFolders/MultiAgent/PlanningAgent.py`
- **集成**：已自动集成到WorkflowManager，在翻译开始前自动执行

### 2. GUI进度同步
- **功能**：实时显示翻译进度到底部进度条和监控页面
- **实现**：所有Agent通过`progress_callback`发送进度事件
- **显示内容**：当前进度、总数、阶段、消息

### 3. Agent流程展示界面
- **功能**：可视化展示多智能体工作流的执行状态
- **位置**：`UserInterface/EditView/AgentFlow/AgentFlowPage.py`
- **包含Agent**：
  - 规划Agent
  - 预处理Agent
  - 术语Agent
  - 翻译Agent

---

## 🎮 如何使用

### 步骤1：启动应用
```bash
python AiNiee.py
```

### 步骤2：加载翻译项目
1. 在启动页面选择"新建项目"或"继续项目"
2. 选择要翻译的文件

### 步骤3：查看Agent流程界面
1. 点击底部的 **向上箭头按钮** (↑)
2. 第一次点击：切换到**监控页面**（显示翻译统计）
3. 第二次点击：切换到**Agent流程页面**（显示Agent状态）
4. 第三次点击：回到**主页面**（文件列表）

### 步骤4：开始翻译
1. 确保已配置好API Key和模型
2. 点击底部的"开始翻译"按钮
3. 观察Agent流程页面的变化：
   - 规划Agent → 蓝色运行中 → 绿色完成
   - 预处理Agent → 蓝色运行中 → 绿色完成
   - 术语Agent → 蓝色运行中 → 绿色完成
   - 翻译Agent → 蓝色运行中（显示进度条）→ 绿色完成

### 步骤5：查看详细进度
1. 切换到**监控页面**查看：
   - 累计时间
   - 翻译行数
   - Token消耗
   - 平均速度
   - 波形图
2. 底部进度条实时显示："已完成/总数"

---

## 📊 Agent流程页面说明

### Agent卡片状态
- **灰色圆点** ●：等待执行
- **蓝色圆点** ●：执行中
- **绿色圆点** ●：执行完成
- **红色圆点** ●：执行失败

### 进度条
- 显示当前Agent的执行进度（0-100%）
- 翻译Agent会显示实时进度（并行翻译）

### 状态消息
- 显示当前Agent正在做什么
- 例如："已翻译 50/337 个单元"

---

## 🔍 查看Planning Agent输出

在命令行/控制台中查看Planning Agent的分析结果：

```
============================================================
阶段0: 任务规划与分析
============================================================
[PlanningAgent] 开始执行任务规划
✓ 任务分析完成: 337 个文本单元, 复杂度=complex, 预计时间=3370秒
✓ 执行计划: 并发数=15, 批次大小=200
✓ 资源评估: tokens≈337000, 成本≈$0.45, API调用≈1011次
[PlanningAgent] 任务规划完成
```

---

## 🐛 故障排查

### 问题1：Agent流程页面不显示
**解决方法**：
- 确保已导入`AgentFlowPage`
- 检查是否添加到`stacked_widget`
- 尝试多次点击箭头按钮

### 问题2：进度不更新
**解决方法**：
- 查看控制台是否有错误
- 确认`progress_callback`已正确传递
- 检查是否启用了多智能体模式

### 问题3：Planning Agent不执行
**解决方法**：
- 查看控制台日志
- 确认`PlanningAgent`已导入
- 检查`execute_workflow`中的Planning阶段

---

## 🎨 自定义

### 修改并发数
编辑 `PlanningAgent._create_execution_plan()`:
```python
"max_workers": 10,  # 改为你想要的并发数
```

### 修改Agent卡片样式
编辑 `AgentFlowPage.py`:
```python
self.setFixedSize(280, 180)  # 修改卡片大小
```

### 添加更多Agent
1. 在`AgentFlowPage.create_agent_cards()`中添加新Agent定义
2. 在`update_agent_flow()`中添加stage映射

---

## 📝 日志查看

### 关键日志位置
- **Planning阶段**：搜索`阶段0: 任务规划与分析`
- **Preprocessing阶段**：搜索`[PreprocessingTool]`
- **Terminology阶段**：搜索`[TerminologyTool]`
- **Translation阶段**：搜索`[TranslationTool]`

### 进度事件
搜索日志中的：
```
[WorkflowManager] 共享状态已初始化
✓ 任务分析完成
开始执行Griptape工作流
Griptape工作流执行完成
```

---

## 🚀 性能优化建议

1. **调整并发数**：根据API限制和机器性能
2. **批次大小**：根据文本复杂度调整
3. **启用缓存**：避免重复翻译
4. **监控资源**：观察Token消耗和成本

---

## 🆘 获取帮助

如果遇到问题：
1. 查看控制台日志
2. 检查`debug.txt`（如果存在）
3. 查看`Resource/config.json`配置
4. 检查API Key和网络连接

---

## 📦 技术架构

```
MultiAgentTaskExecutor
    ↓ (创建)
WorkflowManager
    ↓ (初始化)
PlanningAgent → 任务分析与规划
    ↓
Griptape Workflow
    ↓
Task1 → PreprocessingTool → PreprocessingAgent
    ↓
Task2 → TerminologyTool → TerminologyEntityAgent
    ↓
Task3 → TranslationTool → TranslationRefinementAgent (并行翻译)
    ↓
progress_callback → GUI更新
    ├─ BottomCommandBar (进度条)
    ├─ MonitoringPage (统计数据)
    └─ AgentFlowPage (Agent状态)
```

---

## ✨ 新特性说明

### 并行翻译
- 使用`ThreadPoolExecutor`并行处理
- 最多10个并发线程（可调整）
- 每完成一个单元就更新进度

### 防止重复调用
- 翻译完成后自动返回结果
- 避免LLM重复调用工具
- 节省API成本

### 智能规划
- 自动分析任务复杂度
- 预估资源消耗
- 动态调整执行计划

---

**祝您使用愉快！** 🎉

