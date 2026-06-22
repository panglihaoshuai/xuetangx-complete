# 作业 opencli 答题技术参考

## opencli 安装和配置

```bash
# 安装
npm install -g opencli

# 启动daemon
opencli daemon start

# attach到Chrome（需要Chrome已启动CDP）
opencli attach chrome --port 9223
```

## 题型处理

### 判断题

**HTML结构**：
```html
<div class="radio_xtb panduan" data-answer="true">对</div>
<div class="radio_xtb panduan" data-answer="false">错</div>
```

**答题流程**：
```bash
# 读题目
opencli browser hw eval 'document.querySelector(".examquestion-title").innerText'

# 读选项
opencli browser hw eval 'document.querySelector(".radio_xtb.panduan").innerText'

# 点击选项（假设"对"的ref是3）
opencli browser hw click 3

# 提交
opencli browser hw click <submit-ref>
```

### 单选题

**HTML结构**：
```html
<div class="radio_xtb select">A</div>
<div class="radio_xtb select">B</div>
<div class="radio_xtb select">C</div>
<div class="radio_xtb select">D</div>
```

**答题流程**：
```bash
# 读题目
opencli browser hw eval 'document.querySelector(".examquestion-title").innerText'

# 读所有选项
opencli browser hw eval 'JSON.stringify([...document.querySelectorAll(".radio_xtb")].map((el, i) => ({ref: i+1, text: el.innerText})))'

# 点击选项（假设B的ref是2）
opencli browser hw click 2

# 提交
opencli browser hw click <submit-ref>
```

### 填空题

**HTML结构**：
```html
<textarea placeholder="请输入答案"></textarea>
```

**答题流程**：
```bash
# 读题目
opencli browser hw eval 'document.querySelector(".examquestion-title").innerText'

# 输入答案
opencli browser hw type "textarea" "答案内容"

# 提交
opencli browser hw click <submit-ref>
```

## 常用opencli命令

```bash
# 读元素文本
opencli browser hw eval 'document.querySelector(".selector").innerText'

# 读元素HTML
opencli browser hw eval 'document.querySelector(".selector").innerHTML'

# 点击元素
opencli browser hw click <ref>

# 输入文本
opencli browser hw type "selector" "text"

# 读取页面URL
opencli browser hw eval 'window.location.href'

# 读取所有匹配元素
opencli browser hw eval 'JSON.stringify([...document.querySelectorAll(".class")].map(el => el.innerText))'
```

## 答题策略

### LLM读题答题

```python
# 伪代码
question = opencli_eval('document.querySelector(".examquestion-title").innerText')
options = opencli_eval('JSON.stringify([...document.querySelectorAll(".radio_xtb")].map(el => el.innerText))')

# 调用LLM分析
answer = llm_analyze(question, options)  # 返回 "A"/"B"/"对"/"错"/"填空内容"

# 执行答题
if answer in ["对", "A"]:
    opencli_click(ref_for_对_or_A)
elif answer in ["错", "B"]:
    opencli_click(ref_for_错_or_B)
else:
    opencli_type("textarea", answer)
```

### 提交后验证

```bash
# 检查是否进入下一题
opencli browser hw eval 'document.querySelector(".examquestion-title").innerText'

# 检查进度
opencli browser hw eval 'document.querySelector(".progress").innerText'

# 检查得分（如果有）
opencli browser hw eval 'document.querySelector(".score").innerText'
```

## 注意事项

1. **ref是动态的**：每次页面刷新后ref会变，需要重新获取
2. **Vue组件**：点击后可能需要等待Vue更新DOM
3. **提交按钮**：通常是 `.submit-btn` 或 ref在题目下方
4. **多题循环**：答完一题后，需要等待页面更新再读下一题
5. **填空题触发事件**：type后可能需要触发Vue的input事件
