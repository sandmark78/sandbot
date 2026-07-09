#!/usr/bin/env node
/**
 * Edge TTS HTTP API
 */

const fs = require('fs');
const https = require('https');

const TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';

async function synthesize(text, outputFile, voice = 'zh-CN-YunxiNeural') {
  return new Promise((resolve, reject) => {
    const url = `https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TOKEN}&Authorization=bearer%20undefined`;
    
    const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
      <voice name='${voice}'>
        <prosody rate='0%' pitch='0%'>${text}</prosody>
      </voice>
    </speak>`;
    
    const options = {
      hostname: 'speech.platform.bing.com',
      path: `/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TOKEN}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3',
        'User-Agent': 'Mozilla/5.0'
      }
    };
    
    const req = https.request(options, (res) => {
      console.log('状态:', res.statusCode);
      
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        fs.writeFileSync(outputFile, buffer);
        console.log(`✅ 音频已保存: ${outputFile} (${(buffer.length / 1024).toFixed(1)} KB)`);
        resolve();
      });
    });
    
    req.on('error', reject);
    req.write(ssml);
    req.end();
  });
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('用法: node edge-tts-http.js <input.txt> <output.mp3> [voice]');
  process.exit(1);
}

const text = fs.readFileSync(args[0], 'utf8').trim();
const voice = args[2] || 'zh-CN-YunxiNeural';

console.log(`📝 文本: ${text.length} 字符`);
console.log(`🎙️ 音色: ${voice}`);

synthesize(text, args[1], voice)
  .then(() => console.log('✅ 完成'))
  .catch(err => {
    console.error('❌ 失败:', err.message);
    process.exit(1);
  });
