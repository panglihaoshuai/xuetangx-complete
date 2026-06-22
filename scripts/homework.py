#!/usr/bin/env python3
"""
作业 opencli 自动答题
支持：判断题、单选题、填空题
"""
import subprocess
import time
import re

def opencli_eval(js_code):
    """执行opencli browser hw eval"""
    cmd = ['opencli', 'browser', 'hw', 'eval', js_code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()

def opencli_click(ref):
    """点击opencli元素ref"""
    cmd = ['opencli', 'browser', 'hw', 'click', ref]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()

def opencli_type(selector, text):
    """在opencli元素中输入文本"""
    cmd = ['opencli', 'browser', 'hw', 'type', selector, text]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()

def read_question(page):
    """读取当前作业题目
    
    返回：{type, question, options, answer_type}
      type: 'judge' | 'choice' | 'fill'
      question: 题目文本
      options: [{ref, text}] 选项列表
      answer_type: '对错' | '选择' | '填空'
    """
    # 读取题目
    question = opencli_eval('document.querySelector(".examquestion-title").innerText')
    
    # 判断题型
    html = opencli_eval('document.querySelector(".examquestion-main").innerHTML')
    
    if 'radio_xtb panduan' in html:
        # 判断题
        options = []
        # 找"对""错"按钮
        for ref in ['对', '错']:
            btn_ref = opencli_eval(f'''
                [...document.querySelectorAll('.radio_xtb')].find(el => el.innerText.trim() === '{ref}')?.ref
            ''')
            options.append({'ref': btn_ref, 'text': ref})
        return {
            'type': 'judge',
            'question': question,
            'options': options,
            'answer_type': '对错'
        }
    elif 'radio_xtb select' in html:
        # 单选题
        options = []
        option_els = opencli_eval('''JSON.stringify([...document.querySelectorAll('.radio_xtb')].map((el, i) => ({
            ref: el.getAttribute('data-ref') || (i+1).toString(),
            text: el.innerText.trim()
        })))''')
        # 解析options
        return {
            'type': 'choice',
            'question': question,
            'options': eval(option_els) if option_els else [],
            'answer_type': '选择'
        }
    else:
        # 填空题
        textarea_ref = opencli_eval('document.querySelector("textarea")?.ref || "textarea"')
        return {
            'type': 'fill',
            'question': question,
            'options': [],
            'answer_type': '填空'
        }

def answer_question(page, question_info, llm_answer):
    """答题
    
    参数：
        page: playwright page
        question_info: read_question()返回的字典
        llm_answer: LLM给出的答案（'对'|'错'|'A'|'B'|...|'文本'）
    
    返回：True成功
    """
    qtype = question_info['type']
    options = question_info['options']
    
    if qtype == 'judge':
        # 判断题：选对或错
        answer = llm_answer.strip()
        if answer in ['对', 'A', 'True', 'true', 'T', 't']:
            ref = options[0]['ref'] if options else None
        else:
            ref = options[1]['ref'] if len(options) > 1 else None
        
        if ref:
            opencli_click(ref)
            time.sleep(0.5)
            # 点提交
            submit_ref = opencli_eval('document.querySelector(".submit-btn")?.ref || "submit"')
            opencli_click(submit_ref)
            return True
    
    elif qtype == 'choice':
        # 单选题
        answer = llm_answer.strip().upper()
        # 映射 A=0, B=1, C=2, D=3
        index = ord(answer) - ord('A') if answer.isalpha() else int(answer)
        if 0 <= index < len(options):
            ref = options[index]['ref']
            opencli_click(ref)
            time.sleep(0.5)
            submit_ref = opencli_eval('document.querySelector(".submit-btn")?.ref || "submit"')
            opencli_click(submit_ref)
            return True
    
    elif qtype == 'fill':
        # 填空题
        answer = llm_answer.strip()
        textarea_ref = opencli_eval('document.querySelector("textarea")?.ref || "textarea"')
        opencli_type(textarea_ref, answer)
        time.sleep(0.5)
        submit_ref = opencli_eval('document.querySelector(".submit-btn")?.ref || "submit"')
        opencli_click(submit_ref)
        return True
    
    return False
