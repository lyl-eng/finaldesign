# AiNiee 项目代码分析报告

## 一、总体功能分析

### 1.1 项目定位
**AiNiee** 是一款基于 AI 的自动化翻译工具，主要用于游戏、书籍、字幕、文档等复杂长文本的批量翻译。项目采用 Python + PyQt5 开发，提供了完整的图形化界面和插件化架构。

### 1.2 核心功能模块

#### 1.2.1 文件读取与解析 (`ModuleFolders/FileReader/`)
**位置**: `ModuleFolders/FileReader/FileReader.py`

支持多种文件格式的读取：
- **游戏相关**: `MToolReader.py`, `TPPReader.py`, `TransReader.py`, `RenpyReader.py`, `ParatranzReader.py`, `VntReader.py`
- **文档格式**: `TxtReader.py`, `DocxReader.py`, `EpubReader.py`, `MdReader.py`, `BabeldocPdfReader.py`
- **字幕格式**: `SrtReader.py`, `AssReader.py`, `VttReader.py`, `LrcReader.py`
- **国际化**: `I18nextReader.py`, `PoReader.py`
- **自动检测**: `AutoTypeReader.py` (自动识别文件类型)

**设计模式**: 工厂模式 + 策略模式，每种 Reader 都继承自 `BaseReader`，通过 `FileReader` 统一分发。

#### 1.2.2 文件输出与生成 (`ModuleFolders/FileOutputer/`)
**位置**: `ModuleFolders/FileOutputer/FileOutputer.py`

与 Reader 对应，支持相同格式的文件输出：
- 支持双语输出（原文+译文）
- 支持单语译文输出
- 保持原文件目录结构

#### 1.2.3 缓存管理系统 (`ModuleFolders/Cache/`)
**位置**: `ModuleFolders/Cache/CacheManager.py`

核心数据结构：
- **CacheProject** (`CacheProject.py`): 项目级别的缓存容器
  - `project_id`: 项目唯一标识
  - `project_type`: 项目类型（如 Mtool, TPP, Trans 等）
  - `files`: 字典，存储所有文件的缓存信息
  - `stats_data`: 项目统计信息（翻译进度、token 消耗等）

- **CacheFile** (`CacheFile.py`): 文件级别的缓存
  - `storage_path`: 文件存储路径
  - `items`: 该文件中的所有文本项列表

- **CacheItem** (`CacheItem.py`): 单个文本项的缓存
  - `text_index`: 文本索引
  - `source_text`: 原文
  - `translated_text`: 译文
  - `polished_text`: 润色后的文本
  - `translation_status`: 翻译状态（未翻译/已翻译/已润色/已排除）
  - `lang_code`: 语言代码（用于语言检测）
  - `extra`: 额外属性字典（用于存储特定格式的元数据）

**缓存特性**:
- 使用 `msgspec` 进行高效的 JSON 序列化/反序列化
- 线程安全的读写操作（使用 `ThreadSafeCache`）
- 自动定时保存（默认 8 秒间隔）
- 支持断点续译（通过检查翻译状态）

#### 1.2.4 LLM 请求接口 (`ModuleFolders/LLMRequester/`)
**位置**: `ModuleFolders/LLMRequester/LLMRequester.py`

支持的 AI 平台：
- **OpenAI**: `OpenaiRequester.py` (GPT-3.5, GPT-4 等)
- **Anthropic**: `AnthropicRequester.py` (Claude)
- **Google**: `GoogleRequester.py` (Gemini)
- **Dashscope**: `DashscopeRequester.py` (阿里云通义千问)
- **Cohere**: `CohereRequester.py`
- **Amazon Bedrock**: `AmazonbedrockRequester.py`
- **Sakura**: `SakuraRequester.py` (专用于日语翻译的本地模型)
- **LocalLLM**: `LocalLLMRequester.py` (本地部署的 LLM)

**统一接口**: 所有 Requester 返回格式一致：`(skip, response_think, response_content, prompt_tokens, completion_tokens)`

#### 1.2.5 提示词构建系统 (`ModuleFolders/PromptBuilder/`)
**位置**: `ModuleFolders/PromptBuilder/PromptBuilder.py`

**核心功能**:
1. **系统提示词管理**: 
   - 支持多种预设（Common, COT, Think）
   - 支持中英文提示词模板
   - 动态替换语言占位符

2. **上下文构建**:
   - 支持上文关联（`previous_text_list`）
   - 构建翻译示例（`build_translation_sample`）
   - 术语表注入（通过配置中的 `prompt_dictionary_data`）

3. **专项提示词构建器**:
   - `PromptBuilderSakura.py`: 专用于 Sakura 模型的提示词格式
   - `PromptBuilderLocal.py`: 本地 LLM 的提示词格式
   - `PromptBuilderPolishing.py`: 润色任务的提示词构建

#### 1.2.6 任务执行引擎 (`ModuleFolders/TaskExecutor/`)
**位置**: `ModuleFolders/TaskExecutor/TaskExecutor.py`

**任务类型**:
1. **翻译任务** (`TranslatorTask.py`):
   - 批量文本分块翻译
   - 支持多轮翻译（处理翻译失败的条目）
   - 上下文关联翻译
   - 插件系统介入（文本过滤、预处理、后处理）

2. **润色任务** (`PolisherTask.py`):
   - 对已翻译文本进行优化
   - 保持原文风格的润色

**执行流程**:
```
1. 加载配置 → 2. 生成文本块（chunks）→ 3. 遍历块 → 4. 构建提示词 → 
5. 发送请求 → 6. 解析响应 → 7. 检查结果 → 8. 更新缓存 → 9. 保存进度
```

#### 1.2.7 插件系统 (`Base/PluginManager.py` + `PluginScripts/`)
**位置**: `Base/PluginManager.py`, `PluginScripts/PluginBase.py`

**已实现插件**:
1. **LanguageFilter** (`LanguageFilter/`): 语言过滤器，过滤不需要翻译的文本
2. **TextNormalizer** (`TextNormalizer/`): 文本规范化
3. **GeneralTextFilter** (`GeneralTextFilter/`): 通用文本过滤
4. **SpecialTextFilter** (`SpecialTextFilter/`): 特殊文本过滤（如代码、URL）
5. **TranslationCheckPlugin** (`TranslationCheckPlugin/`): 翻译质量检查
6. **BilingualPlugin** (`BilingualPlugin/`): 双语输出插件
7. **IncrementalFilePlugin** (`IncrementalFilePlugin/`): 增量文件处理
8. **TextLayoutRepairPlugin** (`TextLayoutRepairPlugin/`): 文本布局修复
9. **MToolOptimizer** (`MToolOptimizer/`): MTool 格式优化

**插件事件系统**:
- 插件通过 `add_event()` 注册感兴趣的事件
- 事件触发时，按优先级排序执行插件
- 支持启用/禁用插件

#### 1.2.8 用户界面 (`UserInterface/`)
**位置**: `UserInterface/AppFluentWindow.py`

**主要页面**:
1. **EditViewPage**: 主编辑视图
   - 文本列表展示
   - 原文/译文编辑
   - 搜索功能
   - 监控面板

2. **PlatformPage**: 接口管理页面
   - API 配置
   - 接口测试
   - 多平台管理

3. **TranslationSettingsPage**: 翻译设置
   - 提示词配置（系统提示词、角色设定、背景设定等）
   - 翻译参数（温度、最大 token 等）

4. **Table**: 表格管理
   - **PromptDictionaryPage**: AI 术语表
   - **ExclusionListPage**: 禁翻表（不需要翻译的内容）
   - **TextReplaceAPage/BPage**: 译前/译后替换规则

5. **Settings**: 应用设置
   - **TaskSettingsPage**: 任务设置（线程数、超时时间等）
   - **OutputSettingsPage**: 输出设置（文件名后缀、目录结构等）
   - **PluginsSettingsPage**: 插件管理

#### 1.2.9 简易执行器 (`ModuleFolders/SimpleExecutor/`)
**位置**: `ModuleFolders/SimpleExecutor/SimpleExecutor.py`

处理简单任务：
- **API 测试**: 测试接口配置是否正确
- **术语表翻译**: 批量翻译术语表中的术语
- **表格翻译/润色**: 在表格界面直接翻译/润色文本
- **术语提取**: 使用 NER 提取文本中的术语
- **实体翻译**: 基于上下文的术语翻译并保存

#### 1.2.10 文本处理 (`ModuleFolders/TextProcessor/`)
**位置**: `ModuleFolders/TextProcessor/TextProcessor.py`

**功能**:
1. **译前替换**: 根据配置规则替换原文中的特定内容
2. **代码提取**: 提取文本中的代码片段（避免被翻译）
3. **占位符处理**: 标记代码位置，翻译后还原
4. **空白字符处理**: 保持原文的空格和换行格式
5. **正则规则应用**: 支持自定义正则表达式规则

### 1.3 辅助功能模块

#### 1.3.1 响应提取器 (`ModuleFolders/ResponseExtractor/`)
从 LLM 响应中提取翻译结果，支持多种格式解析。

#### 1.3.2 响应检查器 (`ModuleFolders/ResponseChecker/`)
检查 LLM 返回的翻译质量，验证格式正确性。

#### 1.3.3 请求限制器 (`ModuleFolders/RequestLimiter/`)
控制 API 请求频率（RPM/TPM 限制），防止超过接口限制。

#### 1.3.4 NER 处理器 (`ModuleFolders/NERProcessor/`)
命名实体识别，用于术语提取功能。

#### 1.3.5 版本管理器 (`UserInterface/VersionManager/`)
检查应用更新，下载新版本。

---

## 二、结构分析

### 2.1 整体架构

AiNiee 采用**事件驱动 + 插件化**的架构设计：

```
┌─────────────────────────────────────────────────────────────┐
│                    应用入口 (AiNiee.py)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌─────────▼──────────┐
│  AppFluentWindow │    │   Base (基类)       │
│   (主窗口)        │◄───┤  - 事件系统         │
└───────┬──────────┘    │  - 配置管理         │
        │               │  - 多语言           │
        │               └─────────┬──────────┘
        │                         │
        │         ┌───────────────┼───────────────┐
        │         │               │               │
┌───────▼─────────▼──┐  ┌─────────▼─────────┐  ┌─▼──────────────┐
│  PluginManager     │  │  EventManager     │  │ CacheManager   │
│  (插件管理器)       │  │  (事件管理器)      │  │ (缓存管理)      │
└───────┬────────────┘  └───────────────────┘  └─┬──────────────┘
        │                                         │
        │     ┌───────────────────────────────────┘
        │     │
┌───────▼─────▼──────────────────────────────────────────┐
│              TaskExecutor (任务执行器)                   │
│  ┌──────────────┐          ┌──────────────┐           │
│  │TranslatorTask│          │ PolisherTask │           │
│  └──────┬───────┘          └──────┬───────┘           │
└─────────┼─────────────────────────┼────────────────────┘
          │                         │
          │    ┌────────────────────┘
          │    │
    ┌─────▼────▼─────────────────────────────────────┐
    │        核心处理流程                              │
    │  ┌─────────────────────────────────────────┐   │
    │  │ 1. FileReader → 读取文件                │   │
    │  │ 2. CacheManager → 加载/创建缓存         │   │
    │  │ 3. TextProcessor → 文本预处理           │   │
    │  │ 4. PromptBuilder → 构建提示词           │   │
    │  │ 5. LLMRequester → 发送请求             │   │
    │  │ 6. ResponseExtractor → 提取结果        │   │
    │  │ 7. ResponseChecker → 检查结果          │   │
    │  │ 8. CacheManager → 更新缓存             │   │
    │  │ 9. FileOutputer → 输出文件             │   │
    │  └─────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────┘
```

### 2.2 事件系统架构

**事件定义** (`Base/Base.py` - `Event` 类):
- 任务事件: `TASK_START`, `TASK_UPDATE`, `TASK_STOP`, `TASK_COMPLETED`
- 应用事件: `APP_SHUT_DOWN`, `APP_UPDATE_CHECK`
- 表格事件: `TABLE_TRANSLATE_START`, `TABLE_UPDATE`
- 术语事件: `TERM_EXTRACTION_START`, `GLOSS_TASK_START`

**事件管理器** (`Base/EventManager.py`):
- 使用 PyQt5 的 `pyqtSignal` 实现线程安全的事件分发
- 单例模式，全局唯一实例
- 支持订阅/取消订阅机制

**事件流转**:
```python
# 1. 组件订阅事件
task_executor.subscribe(Base.EVENT.TASK_START, handler)

# 2. 触发事件
ui_component.emit(Base.EVENT.TASK_START, {"continue_status": False})

# 3. EventManager 分发事件
EventManager.signal.emit(event, data)  # 通过 Qt 信号

# 4. 订阅者接收并处理
def handler(event, data):
    # 处理逻辑
```

### 2.3 插件系统架构

**插件基类** (`PluginScripts/PluginBase.py`):
```python
class PluginBase:
    def __init__(self):
        self.name = "插件名称"
        self.events = []  # 感兴趣的事件列表
    
    def on_event(self, event_name, config, event_data):
        # 事件处理逻辑
        pass
```

**插件加载流程**:
1. `PluginManager.load_plugins_from_directory()`: 扫描目录
2. 动态导入 Python 模块
3. 查找继承自 `PluginBase` 的类
4. 实例化插件并调用 `load()` 方法
5. 根据 `events` 列表注册到对应的事件

**插件执行流程**:
```python
# 1. 触发插件事件
plugin_manager.broadcast_event("text_filter", config, cache_project)

# 2. PluginManager 查找注册了该事件的插件
# 3. 按优先级排序
sorted_plugins = sorted(plugins, key=lambda x: priority, reverse=True)

# 4. 过滤启用的插件
enabled_plugins = [p for p in sorted_plugins if enabled]

# 5. 依次执行
for plugin in enabled_plugins:
    plugin.on_event("text_filter", config, cache_project)
```

### 2.4 缓存系统架构

**三层缓存结构**:
```
CacheProject (项目级)
    ├── CacheFile (文件级)
    │       ├── CacheItem (文本项)
    │       ├── CacheItem
    │       └── ...
    ├── CacheFile
    └── ...
```

**缓存生命周期**:
1. **创建阶段**: 
   - `FileReader.read_files()` → 读取文件并创建 `CacheProject`
   - 存储到 `CacheManager.project`

2. **使用阶段**:
   - `TaskExecutor` 通过 `CacheManager` 访问缓存
   - 更新翻译状态和结果
   - 生成文本块（chunks）

3. **持久化阶段**:
   - 定时保存（8 秒间隔）
   - 手动保存（用户触发）
   - 应用关闭时保存

**线程安全**:
- 使用 `ThreadSafeCache` 基类
- 通过 `@dataclass` + `threading.Lock()` 实现
- 所有读写操作都加锁保护

### 2.5 文件读写系统架构

**设计模式**: 工厂模式 + 策略模式

**Reader 注册流程**:
```python
# 1. FileReader 初始化
file_reader = FileReader()

# 2. 自动注册所有 Reader
file_reader._register_system_reader()
  ├── register_reader(TxtReader)
  ├── register_reader(DocxReader)
  └── ...

# 3. 存储到字典
reader_factory_dict[project_type] = reader_class
```

**Reader 调用流程**:
```python
# 1. 根据项目类型获取 Reader
reader_factory = file_reader.reader_factory_dict[project_type]

# 2. 创建 Reader 实例
reader = DirectoryReader(reader_factory, exclude_rules)

# 3. 读取目录
cache_project = reader.read_source_directory(source_path)
```

**Writer 流程类似**，但方向相反。

### 2.6 翻译任务执行流程

**详细流程图**:
```
1. UI 触发 TASK_START 事件
   ↓
2. TaskExecutor.task_start() 接收事件
   ↓
3. 加载配置 (TaskConfig.initialize())
   ↓
4. 配置翻译平台 (prepare_for_translation())
   ↓
5. 触发插件事件: text_filter, preproces_text
   ↓
6. 循环翻译轮次 (round_limit + 1 次)
   ├─ 6.1 生成待翻译文本块 (generate_item_chunks)
   ├─ 6.2 遍历每个块
   │    ├─ 创建 TranslatorTask
   │    ├─ 设置文本项和上文
   │    ├─ 预处理 (TextProcessor.replace_all)
   │    ├─ 构建提示词 (PromptBuilder.generate_prompt)
   │    ├─ 发送请求 (LLMRequester.sent_request)
   │    ├─ 提取结果 (ResponseExtractor.text_extraction)
   │    ├─ 检查结果 (ResponseChecker.check_response)
   │    └─ 更新缓存项状态
   ├─ 6.3 触发插件事件: postproces_text
   └─ 6.4 检查停止状态
   ↓
7. 所有文本翻译完成
   ↓
8. 触发 TASK_COMPLETED 事件
```

**文本分块策略**:
- 按 token 数量或行数限制分块
- 支持上文关联（previous_line_count）
- 每个块独立处理，失败可重试

### 2.7 配置管理系统

**配置存储** (`Resource/config.json`):
- 使用 JSON 格式存储
- 线程安全的读写（`CONFIG_FILE_LOCK`）
- 支持深度合并（`fill_config`）

**配置加载**:
1. 读取 `config.json`
2. 合并默认配置（`load_config_from_default()`）
3. 应用到各个组件

**配置结构**:
```json
{
  "api_settings": {
    "translate": "platform_tag",
    "polish": "platform_tag"
  },
  "platforms": {
    "platform_tag": {
      "api_url": "...",
      "api_key": "...",
      "model": "..."
    }
  },
  "translation_prompt_selection": {...},
  "prompt_dictionary_data": [...],  // 术语表
  "exclusion_list_data": [...],     // 禁翻表
  "pre_translation_data": [...],    // 译前替换
  "post_translation_data": [...]    // 译后替换
}
```

---

## 三、数据结构分析

### 3.1 核心数据结构

#### 3.1.1 CacheProject
**位置**: `ModuleFolders/Cache/CacheProject.py`

```python
@dataclass(repr=False)
class CacheProject(ThreadSafeCache, ExtraMixin):
    project_id: str = ''              # 项目唯一标识
    project_type: str = ''            # 项目类型（Mtool, TPP, Trans 等）
    project_name: str = ''            # 项目名称
    stats_data: CacheProjectStatistics = None  # 统计信息
    files: dict[str, CacheFile] = field(default_factory=dict)  # 文件字典
    detected_encoding: str = "utf-8"  # 检测到的文件编码
    detected_line_ending: str = "\n"  # 检测到的换行符
    extra: dict[str, Any] = field(default_factory=dict)  # 额外属性
```

**关键方法**:
- `add_file(file: CacheFile)`: 添加文件到项目
- `get_file(storage_path: str)`: 根据路径获取文件
- `items_iter(project_types)`: 迭代所有文本项（支持过滤文件类型）
- `count_items(status)`: 统计指定状态的文本项数量

**设计特点**:
- 使用 `@dataclass` 简化数据类定义
- 继承 `ThreadSafeCache` 提供线程安全
- 使用 `ExtraMixin` 支持动态属性扩展
- `files` 字典的 key 是文件的存储路径（相对路径）

#### 3.1.2 CacheFile
**位置**: `ModuleFolders/Cache/CacheFile.py`

```python
@dataclass(repr=False)
class CacheFile(ThreadSafeCache, ExtraMixin):
    storage_path: str = ''            # 文件存储路径（相对于输入目录）
    file_name: str = ''               # 文件名
    file_project_type: str = ''       # 文件的项目类型
    items: list[CacheItem] = field(default_factory=list)  # 文本项列表
    extra: dict[str, Any] = field(default_factory=dict)   # 额外属性
```

**关键方法**:
- `get_item(text_index: int)`: 根据索引获取文本项
- `add_item(item: CacheItem)`: 添加文本项

#### 3.1.3 CacheItem
**位置**: `ModuleFolders/Cache/CacheItem.py`

```python
@dataclass(repr=False)
class CacheItem(ThreadSafeCache, ExtraMixin):
    text_index: int = 0               # 文本索引（在文件中的行号）
    translation_status: int = 0       # 翻译状态（0=未翻译, 1=已翻译, 2=已润色, 7=已排除）
    model: str = ''                   # 使用的模型名称
    source_text: str = ''             # 原文
    translated_text: str = None       # 译文（可选）
    polished_text: str = None         # 润色后的文本（可选）
    text_to_detect: str = None        # 用于语言检测的文本
    lang_code: tuple[str, float, list[str]] | None = None  # 语言代码 (代码, 置信度, 备选列表)
    extra: dict[str, Any] = field(default_factory=dict)    # 额外属性
```

**关键属性**:
- `final_text`: 属性，返回最终文本（优先级：润色 > 翻译 > 原文）
- `token_count`: 属性，返回原文的 token 数量
- `get_token_count(text)`: 类方法，计算任意文本的 token 数

**翻译状态枚举** (`TranslationStatus`):
```python
class TranslationStatus:
    UNTRANSLATED = 0  # 待翻译
    TRANSLATED = 1    # 已翻译
    POLISHED = 2      # 已润色
    EXCLUDED = 7      # 已排除
```

#### 3.1.4 CacheProjectStatistics
**位置**: `ModuleFolders/Cache/CacheProject.py`

```python
@dataclass(repr=False)
class CacheProjectStatistics(ThreadSafeCache):
    total_requests: int = 0           # 总请求数
    error_requests: int = 0           # 错误请求数
    start_time: float = field(default_factory=time.time)  # 开始时间
    total_line: int = 0               # 总行数（需要翻译的文本数量）
    line: int = 0                     # 已翻译行数
    token: int = 0                    # Token 总数（估算）
    total_completion_tokens: int = 0  # 实际消耗的完成 token
    time: float = 0.0                 # 总耗时
```

**用途**: 用于监控翻译进度，显示在 UI 的监控面板中。

### 3.2 线程安全机制

**ThreadSafeCache 基类** (`ModuleFolders/Cache/BaseCache.py`):
```python
class ThreadSafeCache:
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    
    # 所有继承类都自动获得线程锁
```

**使用方式**:
```python
with self._lock:  # 加锁
    # 读写操作
    self.files[path] = file
```

### 3.3 插件数据结构

**PluginBase 属性**:
```python
class PluginBase:
    name: str = "插件名称"
    description: str = "插件描述"
    visibility: bool = True          # 是否在设置中显示
    default_enable: bool = True      # 默认启用状态
    events: list[dict] = []          # 事件列表
    
    # events 格式:
    # [
    #     {"event": "text_filter", "priority": 500},
    #     {"event": "preproces_text", "priority": 400}
    # ]
```

**PluginManager 内部结构**:
```python
class PluginManager:
    event_plugins: dict[str, list[PluginBase]]  # 事件 -> 插件列表映射
    # 示例: {"text_filter": [plugin1, plugin2], ...}
    
    plugins_enable: dict[str, bool]  # 插件启用状态
    # 示例: {"LanguageFilter": True, ...}
```

### 3.4 配置数据结构

**TaskConfig** (`ModuleFolders/TaskConfig/TaskConfig.py`):
动态从 `config.json` 加载配置，主要属性包括：
- `api_settings`: API 设置（翻译/润色使用的平台）
- `platforms`: 平台配置字典
- `target_language`: 目标语言
- `source_language`: 源语言
- `translation_prompt_selection`: 提示词选择配置
- `round_limit`: 最大翻译轮次
- `actual_thread_counts`: 实际线程数
- `tpm_limit`, `rpm_limit`: Token/请求限制
- `prompt_dictionary_data`: 术语表数据
- `exclusion_list_data`: 禁翻表数据
- `pre_translation_data`: 译前替换数据
- `post_translation_data`: 译后替换数据

### 3.5 文本处理数据结构

**TextProcessor 内部状态**:
```python
class TextProcessor:
    # 预编译的正则表达式
    RE_DIGITAL_SEQ_PRE: re.Pattern      # 数字序号前缀
    RE_DIGITAL_SEQ_REC: re.Pattern      # 数字序号（中文格式）
    RE_WHITESPACE_AFFIX: re.Pattern     # 空白字符前后缀
    RE_JA_AFFIX: re.Pattern             # 日语字符前后缀
    
    # 替换规则（编译后的正则列表）
    pre_translation_rules_compiled: list
    post_translation_rules_compiled: list
    auto_compiled_patterns: list        # 自动代码提取规则
```

**文本分块数据结构**:
```python
# generate_item_chunks() 返回:
chunks: List[List[CacheItem]]          # 文本块列表，每个块包含多个 CacheItem
previous_chunks: List[List[CacheItem]]  # 对应的上文块列表
file_paths: List[str]                  # 每个块对应的文件路径
```

### 3.6 提示词构建数据结构

**PromptBuilder 的提示词格式**:
```python
# 消息格式（OpenAI 格式）
messages = [
    {
        "role": "system",
        "content": system_prompt  # 系统提示词
    },
    {
        "role": "user",
        "content": user_content   # 用户内容（包含原文、示例等）
    }
]

# 原文字典格式
source_text_dict = {
    "0": "第一行原文",
    "1": "第二行原文",
    ...
}

# 响应提取后的格式
response_dict = {
    "0": "第一行译文",
    "1": "第二行译文",
    ...
}
```

### 3.7 文件读写数据结构

**Reader 返回格式**:
```python
# FileReader.read_files() 返回 CacheProject
cache_project: CacheProject
    ├── project_id: str
    ├── project_type: str
    ├── files: dict[str, CacheFile]
    │       ├── "path/to/file1.txt": CacheFile
    │       │       ├── storage_path: "path/to/file1.txt"
    │       │       ├── items: [CacheItem, CacheItem, ...]
    │       │       └── ...
    │       └── "path/to/file2.txt": CacheFile
    └── ...
```

**Writer 输入格式**:
```python
# FileOutputer.output_translated_content() 参数
cache_data: CacheProject      # 缓存项目
output_path: str              # 输出路径
input_path: str               # 输入路径（用于保持目录结构）
config: dict                  # 输出配置
    ├── translated_suffix: str      # 译文文件后缀
    ├── bilingual_suffix: str       # 双语文件后缀
    └── bilingual_order: str        # 双语排序（原文优先/译文优先）
```

### 3.8 响应数据结构

**LLMRequester 返回格式**:
```python
# sent_request() 返回元组
(
    skip: bool,                    # 是否跳过（请求失败）
    response_think: str,           # 思考过程（如果有）
    response_content: str,         # 响应内容
    prompt_tokens: int,            # 输入 token 数
    completion_tokens: int         # 输出 token 数
)
```

**ResponseExtractor 提取结果**:
```python
# text_extraction() 返回字典
response_dict: dict[str, str]  # {索引: 译文}
    # 示例: {"0": "译文1", "1": "译文2"}
```

### 3.9 事件数据结构

**事件触发格式**:
```python
# emit() 方法参数
event: int                  # 事件ID（如 Base.EVENT.TASK_START）
data: dict                  # 事件数据字典

# 示例:
self.emit(Base.EVENT.TASK_START, {
    "continue_status": False,
    "current_mode": TaskType.TRANSLATION
})
```

### 3.10 UI 数据结构

**表格数据格式** (用于术语表、禁翻表等):
```python
# 术语表数据
prompt_dictionary_data: list[dict]
    # [{"src": "原文", "dst": "译文", "info": "注释"}, ...]

# 禁翻表数据
exclusion_list_data: list[dict]
    # [{"regex": "正则表达式", "type": "类型"}, ...]

# 替换表数据
pre_translation_data: list[dict]   # 译前替换
post_translation_data: list[dict]  # 译后替换
    # [{"src": "源文本", "dst": "目标文本"}, ...]
```

---

## 四、关键技术实现细节

### 4.1 线程安全实现

项目大量使用线程操作（翻译任务在后台线程执行），所有共享数据结构都实现了线程安全：

1. **缓存对象**: 继承 `ThreadSafeCache`，使用 `threading.Lock()`
2. **配置文件**: 使用全局锁 `Base.CONFIG_FILE_LOCK`
3. **事件系统**: 使用 PyQt5 的 `pyqtSignal`（线程安全）

### 4.2 序列化与反序列化

**缓存序列化**:
- 使用 `msgspec` 库（比标准 `json` 更快）
- 支持旧版缓存格式兼容（`_read_from_old_content`）
- 原子写入（先写临时文件，再替换）

### 4.3 Token 计算

使用 `tiktoken` 库计算 token 数量：
```python
@cache  # 缓存计算结果
def get_token_count(cls, text) -> int:
    return len(tiktoken.get_encoding("cl100k_base").encode(text))
```

### 4.4 语言检测

使用 `langdetect` 库检测文本语言：
- 结果存储为 `(语言代码, 置信度, 备选列表)` 元组
- 支持默认语言回退

### 4.5 简繁转换

使用 `opencc` 库进行中文简繁转换：
- 支持多种预设（`s2t`, `t2s` 等）
- 在导出时统一转换

---

## 五、设计模式总结

1. **单例模式**: `EventManager`, `PluginManager`（实际是全局单例）
2. **工厂模式**: `FileReader`, `FileOutputer`（Reader/Writer 工厂）
3. **策略模式**: 不同 Reader/Writer 实现不同策略
4. **观察者模式**: 事件系统（发布-订阅）
5. **模板方法模式**: `Base` 类作为基类模板
6. **装饰器模式**: `@cache`, `@cached_property` 等

---

## 六、总结

AiNiee 项目是一个设计良好的 AI 翻译工具，具有以下特点：

**优点**:
1. 模块化设计，职责清晰
2. 插件系统灵活，易于扩展
3. 支持多种文件格式和 AI 平台
4. 线程安全，支持并发处理
5. 缓存机制完善，支持断点续译

**改进空间**:
1. 某些方法缺少文档字符串
2. 部分代码存在重复（如 `fill_config`）
3. 错误处理可以更完善
4. 可以增加更多单元测试

**技术栈**:
- **GUI**: PyQt5 + qfluentwidgets
- **AI 接口**: 多种 LLM API
- **数据处理**: msgspec, rapidjson
- **文本处理**: tiktoken, langdetect, opencc
- **其他**: tqdm (进度条), rich (彩色日志)

---

*分析完成时间: 2025年1月*

