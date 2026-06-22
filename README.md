# xuetangx-complete

> 学银在线/学堂在线/雨课堂 SPOC 刷课助手

## 简介

一个通用化的学银在线SPOC课程自动刷课工具，覆盖所有任务类型：

- 🎬 **视频**：心跳注入快速完成（不真实播放）
- 📝 **图文**：强制启用"我已看完"disabled按钮  
- 💬 **讨论**：复制第一条评论自动发送
- ✍️ **作业**：opencli读题 + 自动答题（判断/选择/填空）

**核心特性**：
- ✅ 不绑定账号/URL/CDP端口
- ✅ CDP端口自动扫描
- ✅ 课程信息自动解析
- ✅ 一键执行全流程

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

### 3. 登录学银在线

在Chrome中访问 https://www.xuetangx.com 并登录。

### 4. 一键刷课

```bash
python3 scripts/brush_all.py --cdp-port 9223
```

## 功能详解

### 视频心跳注入

**原理**：通过伪造heartbeat序列欺骗服务端

**API**: `POST https://www.xuetangx.com/video-log/heartbeat/`

**关键字段**：
| 字段 | 来源 | 说明 |
|------|------|------|
| `cc` | cookie `cna=` | 客户端指纹（32位hex） |
| `k` | cookie `k=` | 用户ID |
| `c` | Vue `__vue__.$data.course_id` | 课程ID |
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

### 讨论区发评论

```javascript
const textarea = document.querySelector('textarea[placeholder="发表你的观点"]');
textarea.focus();
textarea.value = commentText;
textarea.dispatchEvent(new Event('input', {bubbles: true}));
page.keyboard.press('Enter');
```

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

## 文件结构

```
xuetangx-complete/
├── SKILL.md                    # Skill主文档
├── README.md                   # 本文件
├── requirements.txt            # Python依赖
├── references/
│   └── technical.md            # 技术参考（API/Vue结构/坑）
└── scripts/
    ├── brush_all.py            # 一键全刷（入口）
    ├── heartbeat.py            # 视频心跳注入
    ├── article.py              # 图文标记看完
    ├── discuss.py              # 讨论区发评论
    ├── homework.py             # 作业opencli答题
    ├── extract_course.py       # 课程信息提取
    └── auto_chrome.py          # CDP自动扫描
```

## 已知问题

1. **kg_learn_chapter API返回404**：SPOC课程可能不支持，改用Vue读listName
2. **sp=4被拒绝**：必须sp=1
3. **图文按钮disabled**：需要Vue层面强制enable
4. **user-data-dir冲突**：Chrome SingletonLock会导致无法启动
5. **心跳间隔**：5秒间隔80次=7分钟/视频，不要超过2倍速

## 技术细节

详见 [references/technical.md](references/technical.md)

## 许可证

MIT

## 致谢

- 学堂在线/雨课堂平台
- Playwright浏览器自动化
- opencli浏览器工具

## 免责声明

本工具仅供学习研究使用，请勿用于违反平台规定的行为。使用本工具造成的一切后果由使用者自行承担。
