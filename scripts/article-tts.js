#!/usr/bin/env node
/**
 * 文章 TTS 生成脚本
 * 用法: node article-tts.js <article.html> [output.mp3]
 */

const fs = require('fs');
const path = require('path');
const { MsEdgeTTS, OUTPUT_FORMAT } = require('edge-tts');

// 从 HTML 提取文章文本
function extractText(html) {
  // 移除 script 和 style
  let text = html.replace(/<script[\s\S]*?<\/script>/gi, '');
  text = text.replace(/<style[\s\S]*?<\/style>/gi, '');
  
  // 提取 article 标签内容
  const articleMatch = text.match(/<article>([\s\S]*?)<\/article>/i);
  if (articleMatch) {
    text = articleMatch[1];
  }
  
  // 移除 HTML 标签
  text = text.replace(/<[^>]+>/g, ' ');
  
  // 解码 HTML 实体
  text = text.replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  
  // 清理空白
  text = text.replace(/\s+/g, ' ')
    .replace(/\n\s*\n/g, '\n')
    .trim();
  
  return text;
}

async function generateTTS(inputFile, outputFile) {
  const html = fs.readFileSync(inputFile, 'utf8');
  const text = extractText(html);
  
  if (!text) {
    console.error('❌ 无法提取文章文本');
    process.exit(1);
  }
  
  console.log(`📝 文章长度: ${text.length} 字符`);
  console.log(`🎙️ 生成语音中...`);
  
  const tts = new MsEdgeTTS();
  
  // 设置音色: zh-CN-YunxiNeural (年轻男性，有活力)
  await tts.setMetadata('zh-CN-YunxiNeural', OUTPUT_FORMAT.AUDIO_24KHZ_96KBITRATE_MONO_MP3);
  
  // 生成音频
  const subtitles = await tts.toFile(outputFile, text);
  
  console.log(`✅ 音频已生成: ${outputFile}`);
  console.log(`📊 字幕: ${subtitles.length} 条`);
  
  // 保存字幕文件
  const subtitleFile = outputFile.replace('.mp3', '.vtt');
  fs.writeFileSync(subtitleFile, subtitles);
  console.log(`✅ 字幕已保存: ${subtitleFile}`);
}

// 主程序
const args = process.argv.slice(2);
if (args.length < 1) {
  console.log('用法: node article-tts.js <article.html> [output.mp3]');
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1] || inputFile.replace('.html', '.mp3');

if (!fs.existsSync(inputFile)) {
  console.error(`❌ 文件不存在: ${inputFile}`);
  process.exit(1);
}

generateTTS(inputFile, outputFile).catch(err => {
  console.error('❌ 生成失败:', err.message);
  process.exit(1);
});
