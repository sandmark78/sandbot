#!/usr/bin/env node
/**
 * Edge TTS 直接调用脚本（不依赖第三方 TTS 库）
 * 用法: node edge-tts-direct.js <input.txt> <output.mp3> [voice]
 */

const fs = require('fs');
const WebSocket = require('ws');

// Edge TTS 配置
const TRUSTED_CLIENT_TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
const WSS_URL = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1';

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

// 生成唯一 ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

async function synthesize(text, outputFile, voice = 'zh-CN-YunxiNeural') {
  return new Promise((resolve, reject) => {
    const messageId = generateId();
    const requestId = generateId();
    
    const url = `${WSS_URL}?TrustedClientToken=${TRUSTED_CLIENT_TOKEN}&Authorization=bearer%20undefined&X-RequestId=${requestId}`;
    
    const ws = new WebSocket(url, {
      headers: {
        'Origin': 'chrome-extension://jdiclpdcbbcmjlaiohcllnopdpnpgfil',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    
    const audioData = [];
    let settled = false;
    
    ws.on('open', () => {
      // 发送配置
      const config = `Content-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n
      {
        "context": {
          "synthesis": {
            "audio": {
              "metadataoptions": {
                "sentenceBoundaryEnabled": "false",
                "wordBoundaryEnabled": "false"
              },
              "outputFormat": "audio-24khz-48kbitrate-mono-mp3"
            }
          }
        }
      }`;
      ws.send(config);
      
      // 发送 SSML
      const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
        <voice name='${voice}'>
          <prosody rate='0%' pitch='0%'>${text}</prosody>
        </voice>
      </speak>`;
      
      const message = `X-RequestId:${messageId}\r\nContent-Type:application/ssml+xml\r\nPath:ssml\r\n\r\n${ssml}`;
      ws.send(message);
    });
    
    ws.on('message', (data) => {
      const str = data.toString();
      
      // 检查是否是音频数据
      if (str.includes('Path:audio')) {
        // 提取二进制音频数据
        const audioStart = str.indexOf('Path:audio') + 'Path:audio\r\n'.length;
        const binaryData = data.slice(audioStart);
        audioData.push(binaryData);
      }
      
      // 检查是否完成
      if (str.includes('Path:turn.end')) {
        ws.close();
      }
    });
    
    ws.on('close', () => {
      if (audioData.length > 0) {
        const buffer = Buffer.concat(audioData);
        fs.writeFileSync(outputFile, buffer);
        console.log(`✅ 音频已保存: ${outputFile} (${(buffer.length / 1024).toFixed(1)} KB)`);
        resolve();
      } else if (!settled) {
        settled = true;
        reject(new Error('没有收到音频数据'));
      }
    });
    
    ws.on('error', (err) => {
      if (!settled) {
        settled = true;
        reject(err);
      }
    });
    
    // 超时处理
    setTimeout(() => {
      if (!settled) {
        settled = true;
        ws.close();
        reject(new Error('超时'));
      }
    }, 120000);
  });
}

// 主程序
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('用法: node edge-tts-direct.js <input.html|input.txt> <output.mp3> [voice]');
  console.log('');
  console.log('可用音色:');
  console.log('  zh-CN-YunxiNeural    (年轻男性，有活力) ← 默认');
  console.log('  zh-CN-YunjianNeural  (成熟男性，稳重)');
  console.log('  zh-CN-XiaoyiNeural   (女性，活泼)');
  console.log('  zh-CN-YunyangNeural  (男性，新闻播报风)');
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1];
const voice = args[2] || 'zh-CN-YunxiNeural';

if (!fs.existsSync(inputFile)) {
  console.error(`❌ 文件不存在: ${inputFile}`);
  process.exit(1);
}

const input = fs.readFileSync(inputFile, 'utf8');
const text = extractText(input);

console.log(`📝 文本长度: ${text.length} 字符`);
console.log(`🎙️ 音色: ${voice}`);
console.log(`🎵 输出: ${outputFile}`);
console.log('');

synthesize(text, outputFile, voice)
  .then(() => {
    console.log('✅ 完成');
  })
  .catch(err => {
    console.error('❌ 失败:', err.message);
    process.exit(1);
  });
