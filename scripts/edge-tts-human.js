#!/usr/bin/env node
/**
 * Edge TTS 人味版 - 带情感和自然停顿
 * 用法: node edge-tts-human.js <input.txt> <output.mp3> [voice]
 * 
 * 优化：
 * - 语速减慢 10%（更自然）
 * - 音调微调（更温暖）
 * - 自动添加停顿（句间 500ms，段间 800ms）
 * - 情感风格：cheerful（默认）
 */

const fs = require('fs');
const { WebSocket } = require('ws');

const TRUSTED_CLIENT_TOKEN = '6A5AA1D4EAFF4E9937434BFDDF20062A';
const WSS_URL = `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TRUSTED_CLIENT_TOKEN}&Authorization=bearer%20undefined`;

// 添加 SSML 情感和停顿
function buildSSML(text, voice, style = 'cheerful') {
  // 自动在句号、问号、感叹号后添加停顿
  const textWithBreaks = text
    .replace(/([。！？.!?])/g, '$1<break time="500ms"/>')
    .replace(/([；;])/g, '$1<break time="300ms"/>')
    .replace(/([，,])/g, '$1<break time="200ms"/>');
  
  // 分段（每段之间更长停顿）
  const paragraphs = textWithBreaks.split(/\n+/).filter(p => p.trim());
  const paragraphsWithBreaks = paragraphs.join('<break time="800ms"/>');
  
  return `<speak version='1.0' xml:lang='zh-CN'>
  <voice name='${voice}'>
    <mstts:express-as style='${style}' styledegree='1.5' xmlns:mstts='http://www.w3.org/2001/mstts'>
      <prosody rate='-10%' pitch='+2Hz' volume='+5%'>
        ${paragraphsWithBreaks}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>`;
}

async function synthesize(text, outputFile, voice = 'zh-CN-YunxiNeural', style = 'cheerful') {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WSS_URL, {
      headers: {
        'Origin': 'chrome-extension://jdiclldmzoormflkhnlfdcgppfmhnmll',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    const audioChunks = [];
    let settled = false;

    ws.on('open', () => {
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

      const ssml = buildSSML(text, voice, style);
      const ssmlMsg = `Content-Type:application/ssml+xml\r\nPath:ssml\r\nX-RequestId:script-${Date.now()}\r\n\r\n${ssml}`;
      ws.send(ssmlMsg);
    });

    ws.on('message', (data) => {
      const str = data.toString();
      
      if (str.includes('Path:audio')) {
        const audioStart = str.indexOf('Path:audio\r\n') + 'Path:audio\r\n'.length;
        const binaryData = data.slice(audioStart);
        audioChunks.push(binaryData);
      }

      if (str.includes('Path:turn.end')) {
        if (audioChunks.length > 0 && !settled) {
          settled = true;
          const buffer = Buffer.concat(audioChunks);
          fs.writeFileSync(outputFile, buffer);
          ws.close();
          resolve(buffer.length);
        }
      }
    });

    ws.on('error', (err) => {
      if (!settled) {
        settled = true;
        reject(err);
      }
    });

    setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error('Timeout'));
      }
    }, 30000);
  });
}

async function main() {
  const [,, inputFile, outputFile, voice = 'zh-CN-YunxiNeural', style = 'cheerful'] = process.argv;
  
  if (!inputFile || !outputFile) {
    console.log('用法: node edge-tts-human.js <input.txt> <output.mp3> [voice] [style]');
    console.log('语音: zh-CN-YunxiNeural (男), zh-CN-XiaoxiaoNeural (女)');
    console.log('风格: cheerful, sad, angry, fearful, disaffectionated, enthusiastic, gentle, lively, serious');
    process.exit(1);
  }

  const text = fs.readFileSync(inputFile, 'utf-8').trim();
  console.log(`🎙️  生成人味语音...`);
  console.log(`   语音: ${voice}`);
  console.log(`   风格: ${style}`);
  console.log(`   文本: ${text.length} 字符`);

  try {
    const size = await synthesize(text, outputFile, voice, style);
    console.log(`✅ 已保存: ${outputFile}`);
    console.log(`   大小: ${(size / 1024).toFixed(1)} KB`);
  } catch (err) {
    console.error(`❌ 错误: ${err.message}`);
    process.exit(1);
  }
}

main();
