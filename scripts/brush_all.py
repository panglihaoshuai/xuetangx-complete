#!/usr/bin/env python3
"""
学银在线全流程刷课
一键执行：视频心跳注入 + 图文标记看完 + 讨论复制评论 + 作业答题（可选）

通用化设计：
- CDP端口自动扫描
- 课程信息自动从页面提取
- 不绑定账号/URL

用法：
  python3 brush_all.py [--cdp-port 9223] [--skip-homework] [--skip-videos]
"""
import sys
import os
import argparse
import time
import json

# 添加当前目录到path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_chrome import ensure_chrome, scan_cdp_ports
from extract_course import extract_course_info, check_login, connect_cdp
from heartbeat import batch_inject
from article import batch_mark_articles
from discuss import batch_post_discussions

def main():
    parser = argparse.ArgumentParser(description='学银在线全流程刷课')
    parser.add_argument('--cdp-port', type=int, default=None, help='CDP端口（默认自动扫描）')
    parser.add_argument('--skip-videos', action='store_true', help='跳过视频刷课')
    parser.add_argument('--skip-articles', action='store_true', help='跳过图文任务点')
    parser.add_argument('--skip-discussions', action='store_true', help='跳过讨论区')
    parser.add_argument('--skip-homework', action='store_true', help='跳过作业（需要opencli）')
    parser.add_argument('--comment-text', default='已阅', help='讨论区评论内容')
    parser.add_argument('--dry-run', action='store_true', help='只打印信息，不实际执行')
    args = parser.parse_args()
    
    print("=" * 60)
    print("学银在线全流程刷课")
    print("=" * 60)
    
    # 1. 确保Chrome已启动
    port, user_data_dir = ensure_chrome(port=args.cdp_port, auto_start=True)
    if not port:
        print("❌ 无法连接Chrome，请手动启动Chrome --remote-debugging-port=9223")
        sys.exit(1)
    
    print(f"✓ CDP端口: {port}")
    
    # 2. 连接Chrome
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("需要playwright: pip install playwright")
        sys.exit(1)
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        page = browser.contexts[0].pages[0]
        
        # 3. 检查登录
        if not check_login(page):
            print("❌ 未登录，请先登录学银在线")
            sys.exit(1)
        
        print("✓ 已登录")
        
        # 4. 提取课程信息
        info = extract_course_info(page)
        
        print(f"✓ 课程ID: {info['course_id']}")
        print(f"✓ 课堂ID: {info['classroomid']}")
        print(f"✓ 签名: {info['sign']}")
        print(f"✓ 视频数: {len(info['videos'])}")
        print(f"✓ 图文数: {len(info['articles'])}")
        print(f"✓ 讨论数: {len(info['discussions'])}")
        
        if args.dry_run:
            print("\n[dry-run] 不执行实际操作")
            return
        
        # 5. 刷视频
        if not args.skip_videos and info['videos']:
            print(f"\n{'='*40}")
            print(f"开始刷视频（{len(info['videos'])}个）")
            print('='*40)
            
            result = batch_inject(page, info['videos'], info)
            print(f"\n视频结果: 成功{len(result['success'])}个，失败{len(result['failed'])}个")
        
        # 6. 刷图文
        if not args.skip_articles and info['articles']:
            print(f"\n{'='*40}")
            print(f"开始刷图文（{len(info['articles'])}个）")
            print('='*40)
            
            result = batch_mark_articles(page, info['articles'])
            print(f"\n图文结果: 成功{len(result['success'])}个，失败{len(result['failed'])}个")
        
        # 7. 刷讨论
        if not args.skip_discussions and info['discussions']:
            print(f"\n{'='*40}")
            print(f"开始刷讨论（{len(info['discussions'])}个）")
            print('='*40)
            
            result = batch_post_discussions(page, info['discussions'], args.comment_text)
            print(f"\n讨论结果: 成功{len(result['success'])}个，失败{len(result['failed'])}个")
        
        # 8. 作业（可选）
        if not args.skip_homework:
            print(f"\n{'='*40}")
            print("作业答题需要opencli，请手动完成")
            print("或使用: python3 homework.py")
            print('='*40)
        
        # 9. 最终报告
        print(f"\n{'='*60}")
        print("完成！")
        print('='*60)

if __name__ == '__main__':
    main()
