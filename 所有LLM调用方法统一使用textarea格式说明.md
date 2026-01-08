# 所有LLM调用方法统一使用textarea格式说明

## 🐛 问题背景

在多智能体翻译过程中，多版本生成步骤（步骤2）出现"期望1行，实际2行"的错误：

```
[WARNING] ❌ 解析失败或结果数量不匹配: 期望1行，实际2行
[WARNING] 📋 输入的原文：
[WARNING]    [1] Brown, W.J., DeWald, D.B., Emr, S.D., Plutner, H. and Balch, W.E. (1995) Role fo...
[WARNING] 📝 LLM返回的译文：
[WARNING]    [键0] Brown, W.J., DeWald, D.B., Emr, S.D., Plutner, H. 和 Balch, W.E. (1995)磷脂酰肌醇3-激酶...
[WARNING]    [键1] Davidson, H.W. (1995)渥曼青霉素导致组织蛋白酶D原的错误靶向...
```

## 🔍 根本原因

### 问题发生在哪个步骤？

- ✅ **步骤1（批量翻译）成功**："✅ 解析成功: 7 行译文"
- ❌ **步骤2（多版本生成）失败**："❌ 解析失败或结果数量不匹配: 期望1行，实际2行"

问题不是发生在批量翻译步骤，而是发生在**多版本生成**步骤！

### 为什么会失败？

#### 原因1：不同的方法使用了不同的响应格式

| 方法 | 原格式 | 解析器 | 问题 |
|------|--------|--------|------|
| `_multi_step_batch_translation` | ✅ `<textarea>` 标签 | ✅ ResponseExtractor | ✅ 健壮 |
| `_generate_version` | ❌ 直接文本 | ❌ `_extract_translation`（取最长行） | ❌ 不健壮 |
| `_select_and_fuse_versions` | ❌ 直接文本 | ❌ `_extract_translation` | ❌ 不健壮 |
| `_back_translate` | ❌ 直接文本 | ❌ `_extract_translation` | ❌ 不健壮 |
| `_refine_translation` | ❌ 直接文本 | ❌ `_extract_translation` | ❌ 不健壮 |

#### 原因2：简单的`_extract_translation`方法不够健壮

```python
def _extract_translation(self, response: str) -> str:
    """从LLM响应中提取译文"""
    lines = response.strip().split("\n")
    # 取第一行或最长的行作为译文
    translation = max(lines, key=len).strip()
    # 去除可能的引号
    translation = translation.strip('"').strip("'")
    return translation
```

这个方法太简单了，当LLM返回多行内容时（如参考文献列表），就会失败。

#### 原因3：原文本身包含多条引用

原文是参考文献，LLM可能会将其分成多条：

```
输入原文：
Brown, W.J., DeWald, D.B., Emr, S.D., Plutner, H. and Balch, W.E. (1995) Role fo...

LLM输出：
1. Brown, W.J., DeWald, D.B., Emr, S.D., Plutner, H. 和 Balch, W.E. (1995)磷脂酰肌醇3-激酶在哺乳动物细胞中新合成溶酶体酶分选和运输中的作用。
2. Davidson, H.W. (1995)渥曼青霉素导致组织蛋白酶D原的错误靶向。
...
```

LLM把一条长文本分成了多条，导致解析器认为是2行而不是1行。

## ✅ 解决方案

### 统一所有LLM调用方法，全部使用textarea格式和ResponseExtractor

修改了以下4个方法：

### 1. `_generate_version`（多版本生成）

#### 修改前
```python
system_prompt = f"""你是一位专业的翻译专家。{prompt_instruction}。
请直接输出译文，不要其他说明。"""

messages = [{
    "role": "user",
    "content": f"原文：{source_text}\n\n请提供{version_type}版本的翻译："
}]

# 使用简单的_extract_translation解析
if not skip and response_content:
    return self._extract_translation(response_content)
```

#### 修改后
```python
system_prompt = f"""你是一位专业的翻译专家。{prompt_instruction}。
重要：请将翻译结果以<textarea>标签包裹，格式如下：
<textarea>
1.译文内容
</textarea>"""

# 构建source_text_dict（单行）
source_text_dict = {"0": source_text}

user_prompt = f"""###待翻译文本
<textarea>
1.{source_text}
</textarea>"""

messages = [{"role": "user", "content": user_prompt}]

# 使用ResponseExtractor解析
if not skip and response_content:
    response_dict = ResponseExtractor.text_extraction(self, source_text_dict, response_content)
    response_dict = ResponseExtractor.remove_numbered_prefix(self, response_dict)
    
    if response_dict and "0" in response_dict:
        return response_dict["0"]
```

### 2. `_select_and_fuse_versions`（版本融合）

#### 修改前
```python
system_prompt = f"""请直接输出融合后的最佳译文，不要其他说明。"""

messages = [{
    "role": "user",
    "content": f"原文：{source_text}\n\n翻译版本：\n{versions_text}\n\n请评估并融合生成最佳译文："
}]

if not skip and response_content:
    fused = self._extract_translation(response_content)
    return fused if fused else list(versions.values())[0]
```

#### 修改后
```python
system_prompt = f"""重要：请将译文以<textarea>标签包裹，格式如下：
<textarea>
1.融合后的最佳译文
</textarea>"""

source_text_dict = {"0": source_text}

user_prompt = f"""原文：{source_text}

翻译版本：
{versions_text}

请评估并融合生成最佳译文：
<textarea>
1.
</textarea>"""

messages = [{"role": "user", "content": user_prompt}]

if not skip and response_content:
    response_dict = ResponseExtractor.text_extraction(self, source_text_dict, response_content)
    response_dict = ResponseExtractor.remove_numbered_prefix(self, response_dict)
    
    if response_dict and "0" in response_dict:
        return response_dict["0"]
```

### 3. `_back_translate`（回译）

#### 修改前
```python
system_prompt = f"""请将以下{target_lang}文本回译为{source_lang}。
请直接输出回译结果，不要其他说明。"""

messages = [{
    "role": "user",
    "content": f"请回译以下文本：\n{translated_text}"
}]

if not skip and response_content:
    return self._extract_translation(response_content)
```

#### 修改后
```python
system_prompt = f"""请将以下{target_lang}文本回译为{source_lang}。
重要：请将回译结果以<textarea>标签包裹，格式如下：
<textarea>
1.回译结果
</textarea>"""

source_text_dict = {"0": translated_text}

user_prompt = f"""请回译以下文本：
<textarea>
1.{translated_text}
</textarea>"""

messages = [{"role": "user", "content": user_prompt}]

if not skip and response_content:
    response_dict = ResponseExtractor.text_extraction(self, source_text_dict, response_content)
    response_dict = ResponseExtractor.remove_numbered_prefix(self, response_dict)
    
    if response_dict and "0" in response_dict:
        return response_dict["0"]
```

### 4. `_refine_translation`（翻译修正）

#### 修改前
```python
system_prompt = f"""请根据评估结果修正以下译文。
请直接输出修正后的译文，不要其他说明。"""

messages = [{
    "role": "user",
    "content": f"原文：{source_text}\n\n原译文：{translated_text}\n\n请修正译文："
}]

if not skip and response_content:
    refined = self._extract_translation(response_content)
    return refined if refined else translated_text
```

#### 修改后
```python
system_prompt = f"""请根据评估结果修正以下译文。
重要：请将修正后的译文以<textarea>标签包裹，格式如下：
<textarea>
1.修正后的译文
</textarea>"""

source_text_dict = {"0": source_text}

user_prompt = f"""原文：
<textarea>
1.{source_text}
</textarea>

原译文：{translated_text}

请修正译文：
<textarea>
1.
</textarea>"""

messages = [{"role": "user", "content": user_prompt}]

if not skip and response_content:
    response_dict = ResponseExtractor.text_extraction(self, source_text_dict, response_content)
    response_dict = ResponseExtractor.remove_numbered_prefix(self, response_dict)
    
    if response_dict and "0" in response_dict:
        return response_dict["0"]
```

## 🎁 修改后的优势

### 1. **统一性** ✅
- 所有LLM调用方法现在都使用相同的格式
- 与原TranslatorTask完全一致
- 易于维护和调试

### 2. **健壮性** ✅
- ResponseExtractor经过大量实战检验
- 能处理各种边缘情况
- 支持多行文本、嵌套引号、格式变化等

### 3. **可预测性** ✅
- LLM对textarea格式更熟悉
- 响应更规范
- 解析成功率更高

### 4. **降级机制** ✅
- 如果ResponseExtractor解析失败
- 会降级为简单的`_extract_translation`
- 确保始终有返回值

## 📊 修改前后对比

| 方法 | 修改前格式 | 修改后格式 | 解析器 | 健壮性 |
|------|-----------|-----------|--------|-------|
| `_multi_step_batch_translation` | ✅ textarea | ✅ textarea | ✅ ResponseExtractor | ✅ 高 |
| `_generate_version` | ❌ 直接文本 | ✅ textarea | ✅ ResponseExtractor | ✅ 高 |
| `_select_and_fuse_versions` | ❌ 直接文本 | ✅ textarea | ✅ ResponseExtractor | ✅ 高 |
| `_back_translate` | ❌ 直接文本 | ✅ textarea | ✅ ResponseExtractor | ✅ 高 |
| `_refine_translation` | ❌ 直接文本 | ✅ textarea | ✅ ResponseExtractor | ✅ 高 |

## 📝 总结

### 问题根源
多智能体系统中不同的LLM调用方法使用了不同的响应格式和解析器，导致在处理复杂文本（如参考文献）时解析失败。

### 解决方法
统一所有LLM调用方法，全部使用与原TranslatorTask相同的`<textarea>`格式和`ResponseExtractor`解析器。

### 预期效果
- ✅ 解析成功率大幅提升
- ✅ 减少"期望1行，实际2行"等错误
- ✅ 与原方法完全一致的健壮性
- ✅ 降级机制确保始终有返回值

---

**修改时间**: 2025-12-28  
**修改原因**: 统一所有LLM调用方法的响应格式，修复多版本生成步骤的解析失败问题

