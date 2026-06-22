# xuetangx-complete

> 学堂在线（xuetangx.com）/ 雨课堂 SPOC 课程自动刷课工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

一个通用化的学堂在线SPOC课程自动刷课工具，覆盖所有任务类型：

- 🎬 **视频**：心跳注入快速完成（不真实播放）
- 📝 **图文**：强制启用"我已看完"disabled按钮  
- 💬 **讨论**：复制第一条评论自动发送
- ✍️ **作业**：opencli读题 + 自动答题（判断/选择/填空）

**核心特性**：
- ✅ 不绑定账号/URL/CDP端口
- ✅ CDP端口自动扫描
- ✅ 课程信息自动解析
- ✅ 一键执行全流程

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Chrome

```bash
# 方式1：手动启动（推荐）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir=$HOME/.config/google-chrome-brush

# 方式2：自动启动（脚本会自动检测）
python3 scripts/auto_chrome.py
```

### 3. 登录学堂在线

在Chrome中访问 https://www.xuetangx.com 并登录。

### 4. 一键刷课

```bash
python3 scripts/brush_all.py --cdp-port 9223
```

---

## 命令行参数

```bash
python3 scripts/brush_all.py [OPTIONS]

Options:
  --cdp-port PORT      CDP端口（默认自动扫描）
  --skip-videos        跳过视频刷课
  --skip-articles      跳过图文任务点
  --skip-discussions   跳过讨论区
  --skip-homework      跳过作业（需要opencli）
  --comment-text TEXT  讨论区评论内容（默认"已阅"）
  --dry-run            只打印信息，不实际执行
```

---

## 踩坑记录

### 坑1：kg_learn_chapter API返回404

**问题**：SPOC课程调用 `/api/v1/lms/kg/kg_learn_chapter/` 返回404

**原因**：SPOC课程不支持该API

**解决**：改用Vue读取 `listName`
```javascript
const listEl = document.querySelector('.course-action-lesson-left');
const listName = listEl.__vue__.$data.listName;
```

---

### 坑2：sp字段必须为1

**问题**：设置sp=4（4倍速）被服务端拒绝

**原因**：服务端会检查sp字段，>1会被识别为刷课

**解决**：必须伪装成1倍速
```python
'sp': 1  # 不能>1
```

---

### 坑3：cp递增量必须匹配时间间隔

**问题**：cp每次增加固定值，被服务端拒绝

**原因**：服务端检查cp递增量与时间间隔的比例

**解决**：使用线性插值
```python
cp = round(duration * i / 79, 3)  # 从0线性递增到duration
```

---

### 坑4：时间戳必须单调递增

**问题**：使用当前时间戳，导致时间倒流

**原因**：服务端检查时间戳单调性

**解决**：使用递增时间戳
```python
ts = timestamp + (i * 5000)  # 每次加5000ms
```

---

### 坑5：图文按钮disabled

**问题**："我已看完"按钮默认disabled

**原因**：平台需要先浏览内容才能点击

**解决**：Vue层面强制启用
```javascript
// 1. 设置Vue finish状态
el.__vue__.$data.content.finish = true;

// 2. 移除disabled属性
btn.removeAttribute('disabled');
btn.className = btn.className.replace(/\bdisable\b/g, '').trim();
```

---

### 坑6：只用click()不够

**问题**：直接click()无效

**原因**：Vue组件需要完整的鼠标事件序列

**解决**：mousedown + mouseup + click 三连
```javascript
btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

---

### 坑7：讨论区textarea需要触发input事件

**问题**：设置textarea.value后不生效

**原因**：Vue的v-model依赖input事件

**解决**：手动触发input事件
```javascript
textarea.value = commentText;
const ev = new Event('input', {bubbles: true});
textarea.dispatchEvent(ev);
```

---

### 坑8：user-data-dir冲突

**问题**：Chrome无法启动

**原因**：user-data-dir被另一个Chrome实例锁定

**解决**：检测SingletonLock，自动切换目录
```python
lock_file = os.path.join(user_data_dir, 'SingletonLock')
if os.path.exists(lock_file):
    user_data_dir = user_data_dir + '_brush'
```

---

### 坑9：ref ID会变化

**问题**：opencli的ref ID每次刷新都变

**原因**：页面重新渲染

**解决**：每次操作前重新获取ref

---

### 坑10：80次心跳是经验值

**问题**：为什么是80次？

**原因**：
- 40次：部分视频进度只推到50%
- 60次：大部分100%，但偶尔漏掉
- 80次：100%成功，且不触发检测
- 100+次：浪费时间，增加风险

**解决**：使用80次作为默认值

---

## 发现心跳漏洞的过程

### 背景

2026年6月21日，我们开始研究学堂在线SPOC课程的自动刷课方案。目标是找到一种方法，可以在不真实观看视频的情况下完成课程任务。

### 第一阶段：网络请求抓包

**目标**：分析视频播放时浏览器发送的网络请求

**方法**：使用Playwright拦截网络请求
```python
page.on('request', lambda req: print(f'{req.method} {req.url}'))
page.on('response', lambda res: print(f'{res.status} {res.url}'))
```

**发现**：
- 视频播放时会定期发送 `POST /video-log/heartbeat/`
- 请求体是 `application/x-www-form-urlencoded` 格式
- 包含大量字段：cc, k, c, v, sp, cp, tp, ts, sq 等

### 第二阶段：分析请求字段

**关键发现1：cc字段**
```javascript
// 从cookie中找到
const cc = document.cookie.match(/cna=([^;]+)/)?.[1];
// 值：0325E954D654D7C80498CE5AAF1F53F5（32位hex）
```

**关键发现2：k字段**
```javascript
// 从cookie中找到
const userId = document.cookie.match(/\bk=(\d+)/)?.[1];
// 值：79159369
```

**关键发现3：c字段**
```javascript
// 从Vue组件中找到
const course_id = document.querySelector('.course-action-learn-space').__vue__.$data.course_id;
// 值：4005682
```

**关键发现4：v字段**
```javascript
// 从URL或Vue中找到
const video_id = window.location.href.match(/video\/(\d+)/)?.[1];
// 或者从Vue listName中获取
```

### 第三阶段：实验验证校验规则

**实验1：直接调用API**
```python
# 尝试1：直接curl调用
curl -X POST https://www.xuetangx.com/video-log/heartbeat/ \
  -d "cc=xxx&k=79159369&c=4005682&v=123456&sp=1&cp=0&tp=100&ts=1234567890&sq=1"
# 结果：403 Forbidden
# 原因：缺少cookie和CSRF token
```

**实验2：带cookie调用**
```python
# 尝试2：带cookie
cookies = {'cna': '0325E954D654D7C80498CE5AAF1F53F5', 'k': '79159369'}
# 结果：200 OK，但进度没变化
# 原因：缺少其他必要字段
```

**实验3：补全所有字段**
```python
# 尝试3：补全所有字段
body = {
    'cc': '0325E954D654D7C80498CE5AAF1F53F5',
    'k': '79159369',
    'et': 'play',
    'c': '4005682',
    'v': '123456',
    'classroomid': '29601185',
    'sign': 'hebnu08091009038',
    'sp': '1',
    'cp': '0',
    'tp': '100',
    'ts': '1234567890',
    'sq': '1'
}
# 结果：200 OK，进度变化了！
# 发现：成功了！
```

### 第四阶段：发现sp字段限制

**实验4：尝试不同sp值**
```python
# 尝试4a：sp=1（1倍速）
body['sp'] = '1'
# 结果：成功，进度正常推进

# 尝试4b：sp=4（4倍速）
body['sp'] = '4'
# 结果：200 OK，但进度没变化
# 发现：sp>1会被服务端拒绝！

# 尝试4c：sp=2（2倍速）
body['sp'] = '2'
# 结果：200 OK，但进度没变化
# 发现：sp必须=1
```

### 第五阶段：发现cp递增规则

**实验5：尝试不同cp值**
```python
# 尝试5a：cp每次+10
for i in range(80):
    body['cp'] = str(i * 10)  # 0, 10, 20, ..., 790
# 结果：失败，进度只推到50%
# 发现：cp递增量必须匹配时间间隔

# 尝试5b：cp线性递增
for i in range(80):
    body['cp'] = str(duration * i / 79)  # 从0线性递增到duration
# 结果：成功，进度推到100%
# 发现：cp必须线性递增
```

### 第六阶段：发现时间戳规则

**实验6：尝试不同时间戳**
```python
# 尝试6a：使用当前时间戳
for i in range(80):
    body['ts'] = str(int(time.time() * 1000))
# 结果：失败，时间倒流被识别
# 发现：时间戳必须单调递增

# 尝试6b：递增时间戳
timestamp = int(time.time() * 1000)
for i in range(80):
    body['ts'] = str(timestamp + (i * 5000))
# 结果：成功
# 发现：时间戳必须单调递增
```

### 第七阶段：确定心跳次数

**实验7：尝试不同次数**
```python
# 尝试7a：40次
for i in range(40):
    # 发送心跳
# 结果：部分视频进度只推到50%

# 尝试7b：60次
for i in range(60):
    # 发送心跳
# 结果：大部分100%，但偶尔漏掉

# 尝试7c：80次
for i in range(80):
    # 发送心跳
# 结果：100%成功，且不触发检测

# 尝试7d：100次
for i in range(100):
    # 发送心跳
# 结果：成功，但浪费时间
```

### 第八阶段：验证反作弊机制

**实验8：测试各种异常情况**
```python
# 测试8a：心跳间隔太短（0.5秒）
time.sleep(0.5)
# 结果：被识别为机器人，进度卡住

# 测试8b：心跳间隔太长（10秒）
time.sleep(10)
# 结果：成功，但浪费时间

# 测试8c：cp跳跃（不连续）
body['cp'] = '50'  # 直接跳到50
# 结果：失败，服务端检测到跳跃

# 测试8d：时间戳倒流
body['ts'] = '1234567890'  # 比上一次小
# 结果：失败，服务端检测到时间倒流
```

### 发现的后端校验规则总结

通过以上实验，我们发现了以下校验规则：

| 校验规则 | 发现实验 | 解决方案 |
|---------|---------|---------|
| **cc指纹** | 抓包发现 | 从cookie `cna=` 读取 |
| **用户ID** | 抓包发现 | 从cookie `k=` 读取 |
| **sp必须=1** | 实验4 | 固定值1 |
| **cp线性递增** | 实验5 | `cp = duration * i / 79` |
| **时间戳单调递增** | 实验6 | `ts = timestamp + (i * 5000)` |
| **心跳间隔5秒** | 实验7/8 | `time.sleep(5)` |
| **80次心跳** | 实验7 | 经验值，100%成功 |

### 关键洞察

**为什么后端会被骗？**

1. **后端只看数据，不看行为**：后端只检查心跳数据是否合理，不检查是否真的在播放视频
2. **后端信任客户端**：后端信任客户端发送的数据，没有做额外的验证
3. **校验规则简单**：只检查基本的数学关系（线性递增、时间单调等）
4. **没有行为分析**：没有分析用户行为模式（如鼠标移动、点击等）

**为什么是80次？**

- 这是通过大量实验得出的经验值
- 太少（如40次）会导致进度不完整
- 太多（如100+次）会增加被检测风险
- 80次是成功率和效率的最佳平衡点

---

## 技术细节

### 视频心跳注入

**API**: `POST https://www.xuetangx.com/video-log/heartbeat/`

**关键字段**：
| 字段 | 来源 | 说明 |
|------|------|------|
| `cc` | cookie `cna=` | 客户端指纹（32位hex） |
| `k` | cookie `k=` | 用户ID |
| `c` | Vue `course_id` | 课程ID |
| `v` | Vue `listName[].id` | 视频ID |
| `classroomid` | Vue或URL | 课堂ID |
| `sign` | Vue `course_sign` | 课程签名 |
| `sp` | 固定值1 | 播放倍速（必须=1） |
| `et` | play/heartbeat/ended | 事件类型 |
| `cp` | 线性递增 | 当前播放位置 |
| `tp` | 视频duration | 总时长 |
| `ts` | 时间戳ms | 单调递增 |
| `sq` | 从1递增 | 序号 |

**心跳序列**：80次
- 第1次: `et=play`
- 第2-79次: `et=heartbeat`
- 第80次: `et=ended`

**反作弊注意**：
- `sp`必须=1（>1会被识别为刷课）
- 间隔5秒，80次=7分钟/视频

---

### 图文"标记看完"

**问题**：按钮默认disabled

**解决方案**：
```javascript
// 1. 设置Vue finish状态
document.querySelector('.lesson_right').__vue__.$data.content.finish = true;

// 2. 移除disabled
btn.removeAttribute('disabled');
btn.className = btn.className.replace(/\bdisable\b/g, '').trim();

// 3. 完整鼠标事件序列
btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

---

### 讨论区发评论

```javascript
const textarea = document.querySelector('textarea[placeholder="发表你的观点"]');
textarea.focus();
textarea.value = commentText;
textarea.dispatchEvent(new Event('input', {bubbles: true}));
page.keyboard.press('Enter');
```

---

### 作业opencli答题

**支持题型**：
- 判断题：`class="radio_xtb panduan"`
- 单选题：`class="radio_xtb select"`
- 填空题：textarea

**流程**：
1. `opencli browser hw eval` 读题目
2. LLM分析给出答案
3. `opencli browser hw click` 点击选项
4. 提交

---

## 文件结构

```
xuetangx-complete/
├── README.md                   # 本文件
├── SKILL.md                    # Skill主文档
├── requirements.txt            # Python依赖
├── docs/
│   ├── development-history.md  # 开发历程
│   └── session-findings.md     # Session关键发现
├── references/
│   └── technical.md            # 技术参考
└── scripts/
    ├── brush_all.py            # 一键全刷（入口）
    ├── heartbeat.py            # 视频心跳注入
    ├── article.py              # 图文标记看完
    ├── discuss.py              # 讨论区发评论
    ├── homework.py             # 作业opencli答题
    ├── extract_course.py       # 课程信息提取
    └── auto_chrome.py          # CDP自动扫描
```

---

## 测试验证

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

## 已知限制

1. **平台限制**：仅支持学堂在线/雨课堂
2. **反作弊风险**：sp必须=1，不能倍速
3. **浏览器依赖**：需要Chrome + CDP
4. **登录依赖**：需要已登录的session
5. **网络依赖**：需要稳定网络

---

## 许可证

MIT

---

## 致谢

- 学堂在线/雨课堂平台
- Playwright浏览器自动化
- opencli浏览器工具

---

## 免责声明

本工具仅供学习研究使用，请勿用于违反平台规定的行为。使用本工具造成的一切后果由使用者自行承担。
