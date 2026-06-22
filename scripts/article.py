#!/usr/bin/env python3
"""
图文任务点强制"标记看完"
绕过disabled按钮的关键技术
"""
import time

def mark_article_finished(page, article_id):
    """标记单个图文任务点为完成
    
    关键技术：绕过disabled的"我已看完"按钮
    1. 设置Vue finish状态
    2. 移除disabled属性和disable类名
    3. 用完整鼠标事件序列（mousedown/mouseup/click）
    
    参数：
        page: playwright page（需先navigate到图文页面）
        article_id: 图文ID
    
    返回：True成功
    """
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
            if (btn.textContent.includes('我已看完') || btn.textContent.includes('标记看完')) {
                targetBtn = btn;
                // 移除disabled属性
                btn.removeAttribute('disabled');
                // 移除disable类名
                btn.className = btn.className.replace(/\bdisable\b/g, '').trim();
                break;
            }
        }
        
        if (!targetBtn) return {ok: false, error: 'button not found'};
        
        // 3. 完整鼠标事件序列
        targetBtn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
        targetBtn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
        targetBtn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        
        return {ok: true};
    }''')
    
    return result.get('ok', False)

def batch_mark_articles(page, articles_info):
    """批量标记图文完成
    
    参数：
        page: playwright page（需先navigate到课程首页或任意页面）
        articles_info: [{id, name}] 图文列表
    
    返回：{success: [...], failed: [...]}
    """
    success = []
    failed = []
    
    for a in articles_info:
        article_id = a['id']
        name = a['name']
        
        try:
            ok = mark_article_finished(page, article_id)
            if ok:
                success.append({'id': article_id, 'name': name})
                print(f"  ✓ {article_id}: {name}")
            else:
                failed.append({'id': article_id, 'name': name, 'reason': 'button not found'})
                print(f"  ✗ {article_id}: {name}")
        except Exception as e:
            failed.append({'id': article_id, 'name': name, 'reason': str(e)})
            print(f"  ✗ {article_id}: {name} ({e})")
        
        time.sleep(0.5)
    
    return {'success': success, 'failed': failed}
