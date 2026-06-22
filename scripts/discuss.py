#!/usr/bin/env python3
"""
讨论区自动复制评论发送
"""
import time

def post_discussion_comment(page, discussion_id, comment_text):
    """在讨论区发送评论
    
    参数：
        page: playwright page（需先navigate到讨论页面）
        discussion_id: 讨论ID
        comment_text: 评论内容
    
    返回：True成功
    """
    result = page.evaluate('''(commentText) => {
        // 1. 找到textarea并触发focus
        const textarea = document.querySelector('textarea[placeholder="发表你的观点"]');
        if (!textarea) return {ok: false, error: 'textarea not found'};
        
        textarea.focus();
        
        // 2. 设置value并触发Vue input事件
        textarea.value = commentText;
        const ev = new Event('input', {bubbles: true});
        textarea.dispatchEvent(ev);
        
        // 3. 触发change事件（Vue需要）
        const ev2 = new Event('change', {bubbles: true});
        textarea.dispatchEvent(ev2);
        
        return {ok: true};
    }''', comment_text)
    
    if not result.get('ok'):
        return False
    
    # 4. 按Enter发送
    page.keyboard.press('Enter')
    time.sleep(1)
    
    return True

def batch_post_discussions(page, discussions_info, comment_text="已阅"):
    """批量发送讨论评论
    
    参数：
        page: playwright page
        discussions_info: [{id, name}] 讨论列表
        comment_text: 评论内容（默认"已阅"）
    
    返回：{success: [...], failed: [...]}
    """
    success = []
    failed = []
    
    for d in discussions_info:
        discussion_id = d['id']
        name = d['name']
        
        try:
            ok = post_discussion_comment(page, discussion_id, comment_text)
            if ok:
                success.append({'id': discussion_id, 'name': name})
                print(f"  ✓ {discussion_id}: {name}")
            else:
                failed.append({'id': discussion_id, 'name': name, 'reason': 'send failed'})
                print(f"  ✗ {discussion_id}: {name}")
        except Exception as e:
            failed.append({'id': discussion_id, 'name': name, 'reason': str(e)})
            print(f"  ✗ {discussion_id}: {name} ({e})")
        
        time.sleep(1)
    
    return {'success': success, 'failed': failed}
