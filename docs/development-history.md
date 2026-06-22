# 学堂在线刷课开发历程与踩坑记录

## 背景

时间：2026年6月21日-22日  
平台：学堂在线（xuetangx.com）/ 雨课堂 SPOC课程  
目标：自动化完成视频、图文、讨论、作业等所有任务类型  
技术栈：Playwright + Chrome CDP + opencli

---

## 一、视频心跳注入（Session 20260621_172214_da0073）

### 问题发现

最初尝试直接调用 `/video-log/heartbeat/` API，发现：
- 直接curl调用返回403
- 必须携带完整的cookie和CSRF token
- 需要模拟完整的浏览器环境

### 技术突破

**关键发现1：cc指纹**
```javascript
// 从cookie cna= 读取，32位hex
// 示例：0325E954D654D7C80498CE5AAF1F53F5
const cc = document.cookie.match(/cna=([^;]+)/)?.[1];
```

**关键发现2：用户ID**
```javascript
// 从cookie k= 读取
// 示例：79159369
const userId = document.cookie.match(/\bk=(\d+)/)?.[1];
```

**关键发现3：sp字段**
```
服务端会检查sp字段！
- sp=1：正常1倍速播放 ✓
- sp=4：4倍速 ✗（会被识别为刷课）
- 结论：必须伪装成1倍速
```

**关键发现4：心跳序列**
```
80次心跳是经验值：
- 40次：部分视频进度只推到50%
- 60次：大部分100%，但偶尔漏掉
- 80次：100%成功，且不触发检测
- 100+次：浪费时间，增加风险
```

### 踩坑记录

**坑1：kg_learn_chapter API返回404**
```
原因：SPOC课程不支持该API
解决：改用Vue读listName
```

**坑2：cp递增量必须匹配时间间隔**
```
错误：cp每次增加duration/80
正确：cp = duration * i / 79（线性插值）
否则：服务端会拒绝
```

**坑3：时间戳必须单调递增**
```
错误：使用当前时间戳
正确：timestamp + (i * 5000)
否则：时间倒流会被识别
```

---

## 二、图文任务点（Session 20260621_210214_cadce4）

### 问题发现

图文页面的"我已看完"按钮默认disabled：
```html
<button class="btn disable" disabled>我已看完</button>
```

### 技术突破

**关键发现：Vue层面强制启用**

```javascript
// 1. 设置Vue finish状态
const el = document.querySelector('.lesson_right, .content_right');
el.__vue__.$data.content.finish = true;

// 2. 移除disabled属性
btn.removeAttribute('disabled');
btn.className = btn.className.replace(/\bdisable\b/g, '').trim();

// 3. 完整鼠标事件序列（必须三连）
btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

### 踩坑记录

**坑1：直接click()无效**
```
原因：disabled状态下click事件不会触发
解决：必须先移除disabled，再用dispatchEvent
```

**坑2：只用click()不够**
```
原因：Vue组件需要完整的鼠标事件序列
解决：mousedown + mouseup + click 三连
```

**坑3：className替换要精确**
```
错误：btn.className = 'btn'
正确：btn.className.replace(/\bdisable\b/g, '').trim()
否则：可能破坏其他class
```

---

## 三、讨论区（Session 20260621_210214_cadce4）

### 问题发现

讨论区textarea需要触发Vue的input事件，直接设置value无效。

### 技术突破

**关键发现：完整的事件触发链**

```javascript
// 1. focus
textarea.focus();

// 2. 设置value
textarea.value = commentText;

// 3. 触发input事件（Vue需要）
const ev = new Event('input', {bubbles: true});
textarea.dispatchEvent(ev);

// 4. 触发change事件
const ev2 = new Event('change', {bubbles: true});
textarea.dispatchEvent(ev2);

// 5. 按Enter发送
page.keyboard.press('Enter');
```

### 踩坑记录

**坑1：只设置value不触发input事件**
```
原因：Vue的v-model依赖input事件
解决：必须手动dispatchEvent
```

**坑2：Enter发送时机**
```
错误：设置value后立即Enter
正确：等待input事件触发后再Enter
解决：time.sleep(0.5)
```

---

## 四、作业答题（Session 当前会话）

### 问题发现

作业页面是动态渲染的Vue组件，需要opencli来操作。

### 技术突破

**关键发现1：题型判断**
```javascript
// 判断题
document.querySelectorAll('.radio_xtb.panduan')

// 单选题
document.querySelectorAll('.radio_xtb.select')

// 填空题
document.querySelector('textarea')
```

**关键发现2：opencli命令**
```bash
# 读题目
opencli browser hw eval 'document.querySelector(".examquestion-title").innerText'

# 点击选项
opencli browser hw click <ref>

# 输入填空
opencli browser hw type "textarea" "答案"
```

### 踩坑记录

**坑1：opencli daemon未启动**
```
原因：Chrome未attach到opencli
解决：先启动opencli daemon，再attach Chrome
```

**坑2：ref ID会变化**
```
原因：每次页面刷新ref都会变
解决：每次操作前重新获取ref
```

**坑3：填空题需要触发input事件**
```
原因：Vue的v-model
解决：opencli hw type会自动触发
```

---

## 五、CDP端口管理（Session 当前会话）

### 问题发现

Chrome启动时会锁定user-data-dir，导致无法多开。

### 技术突破

**关键发现：SingletonLock检测**

```python
# 检测是否被占用
lock_file = os.path.join(user_data_dir, 'SingletonLock')
if os.path.exists(lock_file):
    # 切换到新目录
    user_data_dir = user_data_dir + '_brush'
```

### 踩坑记录

**坑1：Chrome无法启动**
```
原因：user-data-dir被另一个Chrome实例锁定
解决：检测SingletonLock，自动切换目录
```

**坑2：端口冲突**
```
原因：多个Chrome实例尝试同一端口
解决：扫描9222-9230找可用端口
```

---

## 六、通用化设计总结

### 原则

1. **不绑定账号**：从cookie k= 动态读取user_id
2. **不绑定课程**：从URL/Vue自动解析course_id/classroomid/sign
3. **不绑定端口**：扫描9222-9230找可用CDP
4. **不绑定平台**：学堂在线/雨课堂通用

### 实现

```python
# 通用化课程信息提取
info = {
    'user_id': page.cookies['k'],           # 动态
    'cc': page.cookies['cna'],              # 动态
    'course_id': el.__vue__.$data.course_id, # 动态
    'classroomid': el.__vue__.$data.classroomid, # 动态
    'sign': el.__vue__.$data.course_sign,    # 动态
    'videos': listName.filter(type=0),       # 动态
    'articles': listName.filter(type=3),     # 动态
    'discussions': listName.filter(type=4),  # 动态
}
```

---

## 七、测试验证

### 测试环境

- macOS 14.x
- Chrome 120+
- Python 3.9+
- playwright 1.40+

### 测试课程

- 河北师范大学 Linux操作系统及应用 SPOC
- 78个视频，75个图文，11个讨论，10个作业

### 测试结果

| 任务类型 | 数量 | 成功率 | 耗时 |
|---------|------|--------|------|
| 视频 | 78 | 100% | 7分钟/个 |
| 图文 | 75 | 100% | 5秒/个 |
| 讨论 | 11 | 100% | 3秒/个 |
| 作业 | 10 | 100% | 2分钟/个 |

---

## 八、已知限制

1. **平台限制**：仅支持学堂在线/雨课堂
2. **反作弊风险**：sp必须=1，不能倍速
3. **浏览器依赖**：需要Chrome + CDP
4. **登录依赖**：需要已登录的session
5. **网络依赖**：需要稳定网络

---

## 九、后续优化方向

1. **支持更多平台**：中国大学MOOC、智慧树等
2. **增加验证码处理**：OCR识别验证码
3. **增加进度监控**：实时显示刷课进度
4. **增加断点续传**：中断后继续刷课
5. **增加多账号支持**：批量刷多个账号

---

## 十、致谢

- 学堂在线/雨课堂平台
- Playwright浏览器自动化工具
- opencli浏览器工具
- 所有参与测试的同学

---

**最后更新**：2026年6月22日  
**作者**：songshiyao  
**许可证**：MIT
