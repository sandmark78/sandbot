#!/usr/bin/env node
/**
 * Google Translate TTS 脚本
 * 用法: node google-tts.js <input.txt> <output.mp3>
 */

const fs = require('fs');
const https = require('https');
const path = require('path');

// 从 HTML 提取纯文本
function extractText(input) {
  let text = input;
  
  // 如果是 HTML，提取 article 内容
  if (input.includes('<article>')) {
    const match = input.match(/<article>([\s\S]*?)<\/article>/i);
    if (match) text = match[1];
  }
  
  // 移除 HTML 标签
  text = text.replace(/<[^>]+>/g, ' ');
  
  // 解码 HTML 实体
  text = text.replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&middot;/g, '·');
  
  // 清理空白
  text = text.replace(/\s+/g, ' ').trim();
  
  return text;
}

// 分割文本（Google TTS 有长度限制）
function splitText(text, maxLength = 200) {
  const sentences = text.match(/[^.!?。！？]+[.!?。！？]?/g) || [text];
  const chunks = [];
  let current = '';
  
  for (const sentence of sentences) {
    if ((current + sentence).length > maxLength) {
      if (current) chunks.push(current.trim());
      current = sentence;
    } else {
      current += sentence;
    }
  }
  if (current) chunks.push(current.trim());
  
  return chunks;
}

// 下载单个音频片段
function downloadChunk(text, lang = 'zh-CN') {
  return new Promise((resolve, reject) => {
    const encoded = encodeURIComponent(text);
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=${lang}&client=tw-ob`;
    
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        resolve(Buffer.concat(chunks));
      });
    }).on('error', reject);
  });
}

async function generateTTS(inputFile, outputFile) {
  const input = fs.readFileSync(inputFile, 'utf8');
  const text = extractText(input);
  
  console.log(`📝 文本长度: ${text.length} 字符`);
  
  // 分割文本
  const chunks = splitText(text);
  console.log(`📦 分成 ${chunks.length} 段`);
  
  // 下载所有片段
  const audioChunks = [];
  for (let i = 0; i < chunks.length; i++) {
    console.log(`🎙️ 下载第 ${i + 1}/${chunks.length} 段...`);
    try {
      const audio = await downloadChunk(chunks[i]);
      audioChunks.push(audio);
      // 避免请求太快
      await new Promise(r => setTimeout(r, 500));
    } catch (err) {
      console.error(`❌ 第 ${i + 1} 段失败:`, err.message);
    }
  }
  
  if (audioChunks.length === 0) {
    throw new Error('没有成功下载任何音频');
  }
  
  // 合并音频
  const finalAudio = Buffer.concat(audioChunks);
  fs.writeFileSync(outputFile, finalAudio);
  
  console.log(`✅ 音频已保存: ${outputFile} (${(finalAudio.length / 1024).toFixed(1)} KB)`);
}

// 主程序
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('用法: node google-tts.js <input.html|input.txt> <output.mp3>');
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1];

if (!fs.existsSync(inputFile)) {
  console.error(`❌ 文件不存在: ${inputFile}`);
  process.exit(1);
}

generateTTS(inputFile, outputFile)
  .then(() => console.log('✅ 完成'))
  .catch(err => {
    console.error('❌ 失败:', err.message);
    process.exit(1);
  });
