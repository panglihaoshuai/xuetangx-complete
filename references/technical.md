# 学银在线技术参考

## API端点

### 心跳注入
- **URL**: POST https://www.xuetangx.com/video-log/heartbeat/
- **Content-Type**: application/x-www-form-urlencoded
- **关键字段**:
  - `cc`: 客户端指纹（cookie `cna=`，32位hex）
  - `k`: 用户ID（cookie `k=79159369`）
  - `c`: 课程ID（Vue `__vue__.$data.course_id`）
  - `v`: 视频ID（Vue `listName[].id`）
  - `classroomid`: 课堂ID（Vue或URL）
  - `sign`: 课程签名（Vue `course_sign` 或 URL路径）
  - `sp`: 1（必须为1，不能>1）
  - `et`: play/heartbeat/ended
  - `cp`: 当前播放位置（线性递增）
  - `tp`: 总时长（视频duration）
  - `ts`: 时间戳ms（单调递增）
  - `sq`: 序号（从1递增）

## Vue组件结构

### 课程信息
```
.course-action-learn-space.__vue__.$data
  ├── course_id: int
  ├── classroomid: str
  ├── course_sign: str
  ├── course_name: str
  └── ...
```

### 课程列表
```
.course-action-lesson-left.__vue__.$data
  └── listName: [
        {id: int, name: str, leaf_type: int, ...},
        ...
      ]
      leaf_type: 0=视频, 3=图文, 4=讨论, 6=作业
```

### 图文页面
```
.lesson_right.content_right.__vue__.$data
  ├── content: {finish: bool, ...}
  ├── leaf_id: int
  └── ...
```

## 通用化要点

### 1. CDP端口
- 扫描9222-9230找可用端口
- 检测user-data-dir是否被占用（SingletonLock）
- 如被占用，切换到新目录

### 2. 用户ID
- 从cookie `k=79159369` 读取
- 通用化：不硬编码，动态读取

### 3. 客户端指纹(cc)
- 从cookie `cna=` 读取
- 32位hex，如 `0325E954D654D7C80498CE5AAF1F53F5`
- 不能跨浏览器复用

### 4. 心跳序列设计
- 总共80次
- 第1次: et=play, cp=0, sq=1
- 第2-79次: et=heartbeat, cp线性递增, sq递增
- 第80次: et=ended, cp=duration, sq=80
- ts每次+5000（5秒间隔）
- sp始终=1（伪装1倍速）

### 5. 反作弊注意
- sp必须=1（>1会被识别为刷课）
- cp递增量需匹配时间间隔
- 加随机性（0.05-0.15秒间隔波动）
- 不要短时间密集请求

## 已知坑

1. **kg_learn_chapter API返回404**：SPOC课程可能不支持，改用Vue读listName
2. **图文按钮disabled**：需要Vue层面强制enable + mousedown/mouseup/click序列
3. **讨论区textarea**：需要focus + 设置value + 触发input事件 + Enter
4. **作业填空题**：opencli的hw type需要触发Vue的input事件
5. **user-data-dir冲突**：Chrome SingletonLock会导致新Chrome无法启动
6. **心跳间隔**：5秒间隔80次=7分钟/视频，不要超过2倍速
7. **cookie路径**：学银在线cookie在根域名，无需指定path
