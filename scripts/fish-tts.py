#!/usr/bin/env python3
"""
Fish Audio TTS 脚本
用法: python3 fish-tts.py <input.txt> <output.mp3>
"""

import sys
import os
import requests

API_KEY = os.environ.get('FISH_AUDIO_API_KEY')
API_URL = 'https://api.fish.audio/v1/tts'

def text_to_speech(text, output_path):
    if not API_KEY:
        print("❌ 请设置环境变量 FISH_AUDIO_API_KEY")
        sys.exit(1)
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    
    data = {
        'text': text,
        'format': 'mp3',
        'mp3_bitrate': 128,
        'normalize': True,
        'latency': 'normal',
    }
    
    print(f"🎙️  正在生成语音...")
    print(f"   文本长度: {len(text)} 字符")
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ 语音已保存: {output_path}")
        print(f"   文件大小: {len(response.content) / 1024:.1f} KB")
    else:
        print(f"❌ API 错误: {response.status_code}")
        print(f"   {response.text}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 fish-tts.py <input.txt> <output.mp3>")
        print("环境变量: FISH_AUDIO_API_KEY")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text_to_speech(text, output_file)
