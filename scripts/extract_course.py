#!/usr/bin/env python3
"""
学银在线课程信息提取
通用化：不绑定账号/URL/CDP端口，自动从页面解析所有参数
"""
import urllib.request
import json
import time
import sys
import re

def scan_cdp_ports(ports=range(9222, 9231)):
    """扫描本地CDP端口，返回第一个可用的"""
    for port in ports:
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{port}/json/version')
            urllib.request.urlopen(req, timeout=2)
            return port
        except:
            continue
    return None

def connect_cdp(port):
    """通过CDP连接Chrome，返回ws_url, tab_url, tab_id"""
    try:
        req = urllib.request.Request(f'http://127.0.0.1:{port}/json')
        resp = urllib.request.urlopen(req, timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if 'xuetangx.com' in tab.get('url', ''):
                return tab['webSocketDebuggerUrl'], tab['url'], tab['id']
        if tabs:
            return tabs[0]['webSocketDebuggerUrl'], tabs[0]['url'], tabs[0]['id']
    except:
        pass
    return None, None, None

def extract_course_info(page):
    """从页面提取课程信息，通用化
    
    返回字典:
      user_id: 用户ID（从cookie k=读取）
      cc: 客户端指纹（从cookie cna=读取）
      course_id: 课程ID
      classroomid: 课堂ID
      sign: 课程签名
      videos: [{id, name}] 视频列表
      articles: [{id, name}] 图文列表
      discussions: [{id, name}] 讨论列表
    """
    cookies = page.cookies
    user_id = None
    cc = None
    for c in cookies:
        if c['name'] == 'k':
            user_id = c['value']
        if c['name'] == 'cna':
            cc = c['value']
    
    info = page.evaluate('''() => {
        const result = {};
        
        // 从course-action-learn-space读课程信息
        const el = document.querySelector('.course-action-learn-space');
        if (el && el.__vue__) {
            result.course_id = el.__vue__.$data.course_id;
            result.classroomid = el.__vue__.$data.classroomid;
            result.sign = el.__vue__.$data.course_sign;
        }
        
        // 从course-action-lesson-left读课程列表
        const listEl = document.querySelector('.course-action-lesson-left');
        if (listEl && listEl.__vue__) {
            const listName = listEl.__vue__.$data.listName;
            if (Array.isArray(listName)) {
                result.videos = listName.filter(item => item.leaf_type === 0).map(item => ({id: item.id, name: item.name}));
                result.articles = listName.filter(item => item.leaf_type === 3).map(item => ({id: item.id, name: item.name}));
                result.discussions = listName.filter(item => item.leaf_type === 4).map(item => ({id: item.id, name: item.name}));
            }
        }
        
        // 从URL提取sign和classroomid（备用）
        const url = window.location.href;
        const match = url.match(/space\/([^\/]+)\//);
        if (match) result.url_sign = match[1];
        const match2 = url.match(/learn\/space\/[^\/]+\/[^\/]+\/(\d+)\//);
        if (match2) result.url_classroomid = match2[1];
        
        return result;
    }''')
    
    return {
        'user_id': user_id,
        'cc': cc,
        'course_id': info.get('course_id'),
        'classroomid': info.get('classroomid') or info.get('url_classroomid'),
        'sign': info.get('sign') or info.get('url_sign'),
        'videos': info.get('videos', []),
        'articles': info.get('articles', []),
        'discussions': info.get('discussions', []),
    }

def check_login(page):
    """检查是否已登录（通过cookie k= 和 cna= 判断）"""
    cookies = page.cookies
    has_k = any(c['name'] == 'k' for c in cookies)
    has_cna = any(c['name'] == 'cna' for c in cookies)
    return has_k and has_cna

def get_video_info(page, video_id):
    """获取单个视频的信息（duration等）"""
    info = page.evaluate('''(video_id) => {
        const video = document.querySelector('video');
        if (!video) return null;
        return {
            duration: video.duration,
            currentTime: video.currentTime,
            src: video.src,
            playbackRate: video.playbackRate,
        };
    }''', video_id)
    return info
