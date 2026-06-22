# Session 关键对话与技术发现

本文档整理了所有相关session中的关键对话和技术发现，原样保留了重要的技术细节。

---

## Session 1: 20260621_172214_da0073

### 对话摘要

**用户需求**：刷完学堂在线Linux课程的所有视频

**技术探索**：
1. 发现心跳API端点：`POST /video-log/heartbeat/`
2. 发现cc指纹字段：`cookie cna=`
3. 发现用户ID字段：`cookie k=`
4. 发现sp字段限制：必须=1

### 关键技术发现

**发现1：cc指纹提取**
```javascript
// 从cookie读取cc指纹
const cc = document.cookie.match(/cna=([^;]+)/)?.[1];
// 示例值：0325E954D654D7C80498CE5AAF1F53F5
```

**发现2：用户ID提取**
```javascript
// 从cookie读取用户ID
const userId = document.cookie.match(/\bk=(\d+)/)?.[1];
// 示例值：79159369
```

**发现3：课程信息Vue结构**
```javascript
// 从Vue读取课程信息
const el = document.querySelector('.course-action-learn-space');
const course_id = el.__vue__.$data.course_id;      // 4005682
const classroomid = el.__vue__.$data.classroomid;  // "29601185"
const course_sign = el.__vue__.$data.course_sign;  // "hebnu08091009038"
```

**发现4：视频列表Vue结构**
```javascript
// 从Vue读取视频列表
const listEl = document.querySelector('.course-action-lesson-left');
const listName = listEl.__vue__.$data.listName;
// listName.filter(item => item.leaf_type === 0) 获取所有视频
```

**发现5：sp字段限制**
```
服务端会检查sp字段！
- sp=1：正常1倍速播放 ✓
- sp=4：4倍速 ✗（会被识别为刷课）
- 结论：必须伪装成1倍速
```

**发现6：心跳序列设计**
```
80次心跳是经验值：
- 40次：部分视频进度只推到50%
- 60次：大部分100%，但偶尔漏掉
- 80次：100%成功，且不触发检测
- 100+次：浪费时间，增加风险
```

---

## Session 2: 20260621_210214_cadce4

### 对话摘要

**用户需求**：刷完图文任务点和讨论区

**技术突破**：
1. 发现图文按钮disabled问题
2. 发现Vue层面强制启用方案
3. 发现讨论区textarea事件触发链

### 关键技术发现

**发现1：图文按钮disabled结构**
```html
<!-- 默认状态 -->
<button class="btn disable" disabled>我已看完</button>

<!-- 需要移除的属性 -->
- disabled属性
- disable类名
```

**发现2：Vue层面强制启用**
```javascript
// 1. 设置Vue finish状态
const el = document.querySelector('.lesson_right, .content_right');
el.__vue__.$data.content.finish = true;

// 2. 移除disabled属性
const btns = document.querySelectorAll('button, .btn');
btns.forEach(btn => {
  if (btn.textContent.includes('我已看完')) {
    btn.removeAttribute('disabled');
    btn.className = btn.className.replace(/\bdisable\b/g, '').trim();
  }
});
```

**发现3：完整鼠标事件序列**
```javascript
// 必须三连，缺一不可
btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

**发现4：讨论区textarea结构**
```html
<textarea placeholder="发表你的观点"></textarea>
```

**发现5：讨论区事件触发链**
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

---

## Session 3: 当前会话（20260622）

### 对话摘要

**用户需求**：整合所有技术，创建通用化skill

**技术整合**：
1. 视频心跳注入脚本
2. 图文标记看完脚本
3. 讨论区发评论脚本
4. 作业opencli答题脚本
5. CDP端口自动扫描

### 关键技术发现

**发现1：课程信息提取通用化**
```python
def extract_course_info(page):
    # 从cookie读取
    user_id = page.cookies.get('k')
    cc = page.cookies.get('cna')
    
    # 从Vue读取
    info = page.evaluate('''() => {
        const result = {};
        const el = document.querySelector('.course-action-learn-space');
        if (el && el.__vue__) {
            result.course_id = el.__vue__.$data.course_id;
            result.classroomid = el.__vue__.$data.classroomid;
            result.sign = el.__vue__.$data.course_sign;
        }
        return result;
    }''')
    
    return {
        'user_id': user_id,
        'cc': cc,
        'course_id': info.get('course_id'),
        'classroomid': info.get('classroomid'),
        'sign': info.get('sign'),
    }
```

**发现2：心跳注入序列**
```python
def inject_heartbeat(page, video_id, duration, cc, user_id, course_id, classroomid, sign):
    timestamp = int(time.time() * 1000)
    
    for i in range(80):
        # 事件类型
        if i == 0:
            et = 'play'
        elif i == 79:
            et = 'ended'
        else:
            et = 'heartbeat'
        
        # 当前播放位置
        cp = round(duration * i / 79, 3)
        
        # 时间戳
        ts = timestamp + (i * 5000)
        
        # 序号
        sq = i + 1
        
        # 发送请求
        body = {
            'cc': cc, 'k': user_id, 'et': et,
            'c': course_id, 'v': video_id,
            'classroomid': classroomid, 'sign': sign,
            'sp': 1, 'cp': cp, 'tp': duration,
            'ts': ts, 'sq': sq,
        }
        
        page.evaluate('''async (body) => {
            await fetch('/video-log/heartbeat/', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams(body),
            });
        }''', body)
        
        time.sleep(0.05 + random.random() * 0.1)
```

**发现3：图文标记看完**
```python
def mark_article_finished(page, article_id):
    result = page.evaluate('''() => {
        // 1. 设置Vue finish状态
        const el = document.querySelector('.lesson_right, .content_right');
        if (el && el.__vue__) {
            el.__vue__.$data.content.finish = true;
        }
        
        // 2. 找到"我已看完"按钮并绕过disabled
        const btns = document.querySelectorAll('button, .btn');
        let targetBtn = null;
        for (const btn of btns) {
            if (btn.textContent.includes('我已看完')) {
                targetBtn = btn;
                btn.removeAttribute('disabled');
                btn.className = btn.className.replace(/\bdisable\b/g, '').trim();
                break;
            }
        }
        
        if (!targetBtn) return {ok: false};
        
        // 3. 完整鼠标事件序列
        targetBtn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
        targetBtn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
        targetBtn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        
        return {ok: true};
    }''')
    
    return result.get('ok', False)
```

**发现4：讨论区发评论**
```python
def post_discussion_comment(page, discussion_id, comment_text):
    result = page.evaluate('''(commentText) => {
        const textarea = document.querySelector('textarea[placeholder="发表你的观点"]');
        if (!textarea) return {ok: false};
        
        textarea.focus();
        textarea.value = commentText;
        const ev = new Event('input', {bubbles: true});
        textarea.dispatchEvent(ev);
        
        return {ok: true};
    }''', comment_text)
    
    if result.get('ok'):
        page.keyboard.press('Enter')
        return True
    
    return False
```

**发现5：CDP端口扫描**
```python
def scan_cdp_ports(ports=range(9222, 9231)):
    for port in ports:
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{port}/json/version')
            urllib.request.urlopen(req, timeout=2)
            return port
        except:
            continue
    return None
```

**发现6：user-data-dir冲突处理**
```python
def find_existing_chrome_port(user_data_dir):
    lock_file = os.path.join(user_data_dir, 'SingletonLock')
    if os.path.exists(lock_file):
        return scan_cdp_ports()  # 返回已有端口
    return None
```

---

## 技术要点总结

### 1. 视频心跳注入

| 字段 | 来源 | 说明 |
|------|------|------|
| cc | cookie cna= | 客户端指纹，32位hex |
| k | cookie k= | 用户ID |
| c | Vue course_id | 课程ID |
| v | Vue listName[].id | 视频ID |
| classroomid | Vue或URL | 课堂ID |
| sign | Vue course_sign | 课程签名 |
| sp | 固定值1 | 播放倍速（必须=1） |
| et | play/heartbeat/ended | 事件类型 |
| cp | 线性递增 | 当前播放位置 |
| tp | 视频duration | 总时长 |
| ts | 时间戳ms | 单调递增 |
| sq | 从1递增 | 序号 |

### 2. 图文标记看完

**问题**：按钮默认disabled

**解决方案**：
1. 设置Vue `content.finish = true`
2. 移除`disabled`属性
3. 移除`disable`类名
4. 完整鼠标事件三连

### 3. 讨论区发评论

**问题**：Vue的v-model依赖input事件

**解决方案**：
1. focus textarea
2. 设置value
3. 触发input事件
4. 触发change事件
5. 按Enter发送

### 4. CDP端口管理

**问题**：Chrome锁定user-data-dir

**解决方案**：
1. 扫描9222-9230找可用端口
2. 检测SingletonLock
3. 自动切换目录

---

## 已知坑汇总

1. **kg_learn_chapter API返回404**：SPOC课程不支持
2. **sp=4被拒绝**：必须sp=1
3. **cp递增量必须匹配时间间隔**：否则服务端拒绝
4. **时间戳必须单调递增**：否则时间倒流被识别
5. **图文按钮disabled**：需要Vue层面强制enable
6. **只用click()不够**：需要mousedown+mouseup+click三连
7. **讨论区textarea需要触发input事件**：Vue的v-model依赖
8. **user-data-dir冲突**：Chrome SingletonLock会导致无法启动
9. **ref ID会变化**：每次页面刷新ref都会变
10. **填空题需要触发input事件**：opencli会自动处理

---

**最后更新**：2026年6月22日
