---
name: xuetangx-complete
description: |
  学银在线/学堂在线/雨课堂 SPOC 刷课助手。
  覆盖视频心跳注入(heartbeat POST /video-log/heartbeat/)、
  图文任务点强制"标记看完"(disabled按钮绕过)、
  讨论区自动复制评论发送、
  作业 opencli 自动答题(选择/判断/填空)。
  通用：不绑定账号/URL/CDP端口/课程sign。
  适用：用户已有合法登录态但没时间手动刷完课程。
  触发词：刷课、视频心跳、标记看完、讨论、作业答题、学堂在线、xuetangx、雨课堂、SPOC
---

# 学银在线全流程刷课 Skill

## 概述

一个skill覆盖学银在线SPOC课程的所有任务类型：
- **视频**：心跳注入快速完成（不真实播放）
- **图文**：强制启用"我已看完"disabled按钮
- **讨论**：复制第一条评论发送
- **作业**：opencli读题 + 自动答题（判断/选择/填空）

通用设计：CDP端口自动扫描、课程信息自动解析、不绑定账号。

## 前置条件

1. Chrome已登录目标平台（或有session cookies）
2. 已打开目标课程的任意一个页面
3. Python环境已安装（playwright/requests）
4. （作业可选）opencli已安装

## 完整流程

```bash
python3 ~/.hermes/skills/xuetangx-complete/scripts/brush_all.py --cdp-port 9223
```

自动执行：
1. 扫描CDP端口，接管Chrome
2. 从URL/Vue自动解析 course_id, classroom_id, sign
3. 刷视频（心跳注入，5s间隔×80次=7分钟/视频）
4. 刷图文（强制"标记看完"）
5. 刷讨论（复制评论发送）
6. 刷作业（opencli答题，可选）

## 技术细节

### 视频心跳注入

**API**: POST https://www.xuetangx.com/video-log/heartbeat/

**关键字段**:
- `cc`: 客户端指纹（从cookie `cna=` 读取，32位hex）
- `k`: 用户ID（从cookie `k=79159369` 读取）
- `c`: 课程ID（从Vue `__vue__.$data.course_id` 读取）
- `v`: 视频ID（从URL路径 `/video/{id}` 或Vue `__vue__.$data.listName[].id` 读取）
- `classroomid`: 课堂ID（从Vue或URL解析）
- `sp`: 1（伪装1倍速）
- `et`: play/heartbeat/ended（事件类型序列）
- `cp`: 当前播放位置（0→duration，线性递增）
- `tp`: 总时长（视频duration）
- `ts`: 时间戳（从epoch毫秒，单调递增）
- `sq`: 序号（从1单调递增）

**心跳序列设计**:
- 第1个：et=play
- 第2~79个：et=heartbeat
- 第80个：et=ended
- cp从0线性递增到duration
- ts每次加5000（5秒间隔）
- sq从1每次加1
- sp始终为1（伪装1倍速播放）

**反作弊注意**:
- sp必须=1（服务端会检查，sp>1可能被识别为刷课）
- cp递增量需匹配时间间隔（cp_delta / ts_delta ≈ duration / 80）

### 图文"标记看完"

**问题**: "我已看完"按钮默认disabled（class="btn disable"）

**解决方案（从Vue层面强制启用）**:
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

// 3. 点击（需要完整鼠标事件序列）
btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

### 讨论区发评论

```javascript
// 1. 找到textarea并触发focus
const textarea = document.querySelector('textarea[placeholder="发表你的观点"]');
textarea.focus();

// 2. 设置value并触发Vue input事件
textarea.value = commentText;
const ev = new Event('input', {bubbles: true});
textarea.dispatchEvent(ev);

// 3. 按Enter发送
// 用page.keyboard.press('Enter')
```

### 作业 opencli 答题

**支持的题型**:
- **判断题**: class `radio_xtb panduan`（对错两个选项）
- **单选题**: class `radio_xtb select`
- **填空题**: textarea

**答题流程**:
1. `opencli browser hw eval` 读题目文本
2. LLM分析题目，给出答案
3. 选择题：用`opencli browser hw click <ref>`点击选项
4. 填空题：用`opencli browser hw type "textarea" "答案"`
5. 提交：用`opencli browser hw click <ref>`点击"提交"按钮

**注意**: opencli的browser hw需要先启动opencli daemon并attach Chrome

## 通用化设计

- **CDP端口**: 自动扫描9220-9230，不硬编码
- **账号**: 从cookie `k=` 读user_id，不绑定
- **课程**: 从URL/Vue自动解析sign/cid/classroomid
- **视频ID**: 从Vue `listName[].id`自动获取

## 已知坑

1. `kg_learn_chapter` API对SPOC课程可能返回404，改用Vue读listName
2. `sp=4`会被服务端拒绝，必须sp=1
3. 图文按钮disabled需要Vue层面强制enable，不能直接click
4. opencli作业填写textarea时可能需要多次触发input事件
5. 真实4倍速播放（方案B）只有中间进度才用，0%进度必须用心跳注入

## 文件结构

```
scripts/
  brush_all.py          # 一键全刷（视频+图文+讨论+作业）
  heartbeat.py          # 单视频心跳注入
  article.py            # 单图文标记看完
  discuss.py            # 单讨论发评论
  homework.py           # 单作业opencli答题
  extract_course.py     # 课程信息提取（通用）
  auto_chrome.py        # CDP自动扫描+接管
```