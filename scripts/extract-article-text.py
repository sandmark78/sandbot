#!/usr/bin/env python3
"""
从文章 HTML 提取纯正文（用于 TTS）
只提取正文内容，过滤掉导航、元数据、付费提示等
"""

import re
import sys
from html.parser import HTMLParser

class ArticleTextExtractor(HTMLParser):
    """HTML 解析器，提取文章正文"""
    
    def __init__(self):
        super().__init__()
        self.result = []
        self.current_tag = None
        self.skip_depth = 0
        self.in_article = False
        self.article_depth = 0
        self.skip_h1_title = False  # 专门用于跳过 h1.article-title
        self.skip_h2h3_title = False  # 用于跳过 h2/h3 章节标题
        self.skip_script = False  # 用于跳过 script/style 标签
        
        # 需要跳过的 class
        self.skip_classes = {
            'article-meta', 'quick-glance', 'source-note', 'article-img',
            'why-box', 'paywall', 'article-label', 'audio-player',
            'tip-jar', 'subscribe-banner', 'author-sign', 'back-link',
            'bottom-quote', 'bottom-source', 'data-cards', 'compare-box',
            'capability-box', 'metaphor-box', 'conclusion', 'info-bar',
            'site-header', 'site-footer', 'featured', 'icon-list'
        }
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # 进入 article 标签
        if tag == 'article':
            self.in_article = True
            self.article_depth = 1
            return
        
        if not self.in_article:
            return
            
        # 跟踪 article 内的嵌套深度
        if tag == 'article':
            self.article_depth += 1
        
        # 检查是否需要跳过
        if 'class' in attrs_dict:
            classes = attrs_dict['class'].split()
            if any(c in self.skip_classes for c in classes):
                self.skip_depth += 1
                return
        
        # 如果正在跳过，增加深度计数
        if self.skip_depth > 0 and tag == 'div':
            self.skip_depth += 1
            return
        
        # 如果正在跳过，不处理其他标签
        if self.skip_depth > 0:
            return
        
        # 跳过 script 和 style 标签
        if tag in ['script', 'style']:
            self.skip_script = True
            return
        
        # 跳过文章主标题（h1.article-title）
        if tag == 'h1' and 'class' in attrs_dict and 'article-title' in attrs_dict['class']:
            self.skip_h1_title = True
            return
        
        # 跳过章节标题（h2/h3）- TTS 不需要读出章节标题
        if tag in ['h2', 'h3']:
            self.skip_h2h3_title = True
            return
        
        self.current_tag = tag
        
        # 处理段落
        if tag == 'p':
            self.result.append('\n')
        
        # 处理列表项
        elif tag == 'li':
            self.result.append('\n· ')
        
        # 处理引用
        elif tag == 'blockquote':
            self.result.append('\n')
    
    def handle_endtag(self, tag):
        if not self.in_article:
            return
        
        # 结束 script/style 标签
        if tag in ['script', 'style']:
            self.skip_script = False
            return
        
        # 离开 article 标签
        if tag == 'article':
            self.article_depth -= 1
            if self.article_depth == 0:
                self.in_article = False
            return
        
        # 如果正在跳过 h1 标题
        if self.skip_h1_title and tag == 'h1':
            self.skip_h1_title = False
            return
        
        # 如果正在跳过 h2/h3 标题
        if self.skip_h2h3_title and tag in ['h2', 'h3']:
            self.skip_h2h3_title = False
            return
        
        # 如果正在跳过，减少深度
        if self.skip_depth > 0:
            if tag == 'div':
                self.skip_depth -= 1
            return
        
        # 处理段落结束
        if tag == 'p':
            self.result.append('\n')
        
        # 处理列表项结束
        elif tag == 'li':
            self.result.append('\n')
    
    def handle_data(self, data):
        if not self.in_article or self.skip_depth > 0 or self.skip_h1_title or self.skip_h2h3_title or self.skip_script:
            return
        
        text = data.strip()
        if text:
            # 过滤音频播放器控制文字
            if re.match(r'^\d+:\d+/', text):
                return
            self.result.append(text)
    
    def get_text(self):
        text = ''.join(self.result)
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 清理章节编号（如 "1·" "2·"）
        text = re.sub(r'(\n\n)\d+·', r'\1', text)
        # 移除副标题（如果和标题重复）
        lines = text.split('\n')
        if len(lines) > 1:
            # 找到第一个非空行
            first_line = ''
            for line in lines:
                if line.strip():
                    first_line = line.strip()
                    break
            # 如果第二行和第一行相同，移除第二行
            new_lines = []
            found_first = False
            for line in lines:
                if line.strip() == first_line and not found_first:
                    found_first = True
                    new_lines.append(line)
                elif line.strip() == first_line and found_first:
                    # 跳过重复的标题
                    continue
                else:
                    new_lines.append(line)
            text = '\n'.join(new_lines)
        
        # 不过滤英文（保留原文）
        # 只合并多个空格
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()


def extract_article_text(html_file):
    """提取文章正文"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. 提取文章主标题
    title_match = re.search(r'<h1 class="article-title">(.*?)</h1>', html, re.DOTALL)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
    
    # 2. 使用 HTML 解析器提取正文
    parser = ArticleTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    
    # 3. 清理残留
    text = re.sub(r'🔒.*', '', text)
    text = re.sub(r'MEMBERS ONLY.*', '', text)
    text = re.sub(r'本文发布 \d+ 天后免费开放全文。', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # 4. 不添加标题（标题已经在 HTML <title> 中，TTS 不需要再读）
    # 直接返回正文
    full_text = text
    
    # 5. 限制长度（约 8000 字符 ≈ 5-6 分钟音频）
    if len(full_text) > 8000:
        full_text = full_text[:8000] + "\n\n今天就聊到这里。"
    
    return full_text


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 extract-article-text.py <article.html>")
        sys.exit(1)
    
    text = extract_article_text(sys.argv[1])
    
    # 输出到文件或标准输出
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ 提取完成: {sys.argv[2]}")
        print(f"   长度: {len(text)} 字符")
    else:
        print(text)
