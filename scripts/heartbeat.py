#!/usr/bin/env python3
"""
视频心跳注入
通用化：cc/user_id/course_id/classroomid/sign 都从页面动态提取
"""
import time
import random

def inject_heartbeat(page, video_id, duration, cc, user_id, course_id, classroomid, sign):
    """注入单个视频的心跳序列
    
    参数：
        page: playwright page
        video_id: 视频ID（int）
        duration: 视频时长（秒，float）
        cc: 客户端指纹（32位hex，从cookie cna=读取）
        user_id: 用户ID（从cookie k=读取）
        course_id: 课程ID（从Vue读取）
        classroomid: 课堂ID（从Vue读取）
        sign: 课程签名（从Vue或URL读取）
    
    返回：True成功，False失败
    """
    timestamp = int(time.time() * 1000)  # 当前时间戳ms
    
    # 构造80次心跳序列
    for i in range(80):
        # 事件类型：play -> heartbeat -> ended
        if i == 0:
            et = 'play'
        elif i == 79:
            et = 'ended'
        else:
            et = 'heartbeat'
        
        # 当前播放位置：从0线性递增到duration
        cp = round(duration * i / 79, 3)
        
        # 时间戳：每次加5000ms（5秒间隔）
        ts = timestamp + (i * 5000)
        
        # 序号
        sq = i + 1
        
        # 构造请求体
        body = {
            'cc': cc,
            'k': user_id,
            'et': et,
            'c': course_id,
            'v': video_id,
            'classroomid': classroomid,
            'sign': sign,
            'sp': 1,
            'cp': cp,
            'tp': duration,
            'ts': ts,
            'sq': sq,
            'g': 0,
            'ls': 0,
            'sd': 0,
            'sk': random.randint(1, 10),
            'pt': 0,
            'xt': 0,
            'ppt': 0,
            'sl': 0,
        }
        
        # 通过fetch发送
        result = page.evaluate('''async (body) => {
            try {
                const resp = await fetch('/video-log/heartbeat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '',
                    },
                    body: new URLSearchParams(body),
                });
                return {status: resp.status, ok: resp.ok};
            } catch (e) {
                return {error: e.message};
            }
        }''', body)
        
        if not result.get('ok'):
            return False
        
        # 间隔：加一点随机性（模拟真人）
        time.sleep(0.05 + random.random() * 0.1)
    
    return True

def batch_inject(page, videos_info, course_info):
    """批量注入心跳
    
    参数：
        page: playwright page
        videos_info: [{id, name}] 视频列表
        course_info: extract_course_info()返回的字典
    
    返回：{success: [...], failed: [...]}
    """
    cc = course_info['cc']
    user_id = course_info['user_id']
    course_id = course_info['course_id']
    classroomid = course_info['classroomid']
    sign = course_info['sign']
    
    success = []
    failed = []
    
    for v in videos_info:
        video_id = v['id']
        name = v['name']
        
        # 获取视频duration
        video_info = page.evaluate('''() => {
            const video = document.querySelector('video');
            return video ? video.duration : 0;
        }''')
        
        if not video_info or video_info <= 0:
            failed.append({'id': video_id, 'name': name, 'reason': 'no video element'})
            continue
        
        duration = video_info
        
        ok = inject_heartbeat(page, video_id, duration, cc, user_id, course_id, classroomid, sign)
        if ok:
            success.append({'id': video_id, 'name': name})
            print(f"  ✓ {video_id}: {name}")
        else:
            failed.append({'id': video_id, 'name': name, 'reason': 'inject failed'})
            print(f"  ✗ {video_id}: {name}")
    
    return {'success': success, 'failed': failed}
