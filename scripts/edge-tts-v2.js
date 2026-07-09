#!/usr/bin/env node
/**
 * Edge TTS v2 - 直接 WebSocket 实现
 * 用法: node edge-tts-v2.js <input.txt> <output.mp3> [voice]
 */

const fs = require('fs');
const WebSocket = require('ws');

// Edge TTS 配置
const TRUSTED_CLIENT_TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
const WSS_URL = `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TRUSTED_CLIENT_TOKEN}&Authorization=bearer%20undefined`;

function generateId() {
  return Date.now().toString(36).toUpperCase() + Math.random().toString(36).substr(2, 9).toUpperCase();
}

async function synthesize(text, outputFile, voice = 'zh-CN-YunxiNeural') {
  return new Promise((resolve, reject) => {
    const requestId = generateId();
    const messageId = generateId();
    
    const url = `${WSS_URL}&X-RequestId=${requestId}`;
    
    const ws = new WebSocket(url, {
      headers: {
        'Origin': 'chrome-extension://jdiclpdcbbcmjlaiohcllnopdpnpgfil',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
      }
    });
    
    const audioChunks = [];
    let settled = false;
    
    ws.on('open', () => {
      console.log('✅ WebSocket 连接成功');
      
      // 发送配置
      const config = {
        context: {
          synthesis: {
            audio: {
              metadataoptions: {
                sentenceBoundaryEnabled: 'false',
                wordBoundaryEnabled: 'false'
              },
              outputFormat: 'audio-24khz-48kbitrate-mono-mp3'
            }
          }
        }
      };
      
      const configMsg = `Content-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n${JSON.stringify(config)}`;
      ws.send(configMsg);
      
      // 发送 SSML
      const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
        <voice name='${voice}'>
          <prosody rate='0%' pitch='0%'>${text}</prosody>
        </voice>
      </speak>`;
      
      const ssmlMsg = `X-RequestId:${messageId}\r\nContent-Type:application/ssml+xml\r\nPath:ssml\r\n\r\n${ssml}`;
      ws.send(ssmlMsg);
      console.log('📤 已发送 SSML');
    });
    
    ws.on('message', (data) => {
      const str = data.toString();
      
      // 检查是否是音频数据
      if (str.includes('Path:audio')) {
        const audioStart = str.indexOf('Path:audio') + 'Path:audio\r\n'.length;
        const binaryData = data.slice(audioStart);
        audioChunks.push(binaryData);
      }
      
      // 检查是否完成
      if (str.includes('Path:turn.end')) {
        console.log('✅ 合成完成');
        ws.close();
      }
    });
    
    ws.on('close', () => {
      if (audioChunks.length > 0 && !settled) {
        settled = true;
        const buffer = Buffer.concat(audioChunks);
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
        reject(new Error('超时（120秒）'));
      }
    }, 120000);
  });
}

// 主程序
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('用法: node edge-tts-v2.js <input.txt> <output.mp3> [voice]');
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

const text = fs.readFileSync(inputFile, 'utf8').trim();
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
