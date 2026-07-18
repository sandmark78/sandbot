#!/usr/bin/env python3
"""
给文章添加音频播放器
用法: python3 add-audio-player.py <article.html>
"""

import sys
import re
import os

def add_audio_player(article_path):
    """给文章添加音频播放器"""
    
    # 获取音频文件路径
    article_dir = os.path.dirname(article_path)
    article_name = os.path.basename(article_path).replace('.html', '')
    audio_path = f"audio/{article_name}.mp3"
    full_audio_path = os.path.join(article_dir, audio_path)
    
    # 检查音频文件是否存在
    if not os.path.exists(full_audio_path):
        print(f"❌ 音频文件不存在: {full_audio_path}")
        return False
    
    # 读取文章
    with open(article_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 检查是否已有播放器
    if 'class="audio-player"' in html:
        print("✅ 文章已有音频播放器，替换 AUDIO_FILE_PLACEHOLDER")
        # 替换 AUDIO_FILE_PLACEHOLDER 为实际的音频文件路径
        html = html.replace('AUDIO_FILE_PLACEHOLDER', audio_path)
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    
    # CSS 样式
    audio_css = '''
/* Audio Player */
.audio-player { background: var(--bg-warm); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 18px; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
.audio-player .play-btn { width: 36px; height: 36px; border-radius: 50%; background: var(--accent); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all var(--transition); }
.audio-player .play-btn:hover { background: var(--accent-hover); transform: scale(1.05); }
.audio-player .play-btn svg { width: 16px; height: 16px; fill: white; }
.audio-player .player-info { flex: 1; min-width: 0; }
.audio-player .player-title { font-size: 0.78rem; font-weight: 500; color: var(--text-muted); margin-bottom: 4px; }
.audio-player .progress-bar { width: 100%; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; cursor: pointer; }
.audio-player .progress-fill { height: 100%; background: var(--accent); width: 0%; transition: width 0.1s linear; }
.audio-player .time-display { font-size: 0.72rem; color: var(--text-dim); font-variant-numeric: tabular-nums; margin-top: 4px; }
.audio-player audio { display: none; }
'''
    
    # HTML 播放器
    audio_html = f'''
  <div class="audio-player">
    <button class="play-btn" onclick="toggleAudio()">
      <svg id="playIcon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      <svg id="pauseIcon" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
    </button>
    <div class="player-info">
      <div class="player-title">🎙️ 听文章</div>
      <div class="progress-bar" onclick="seekAudio(event)">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <div class="time-display"><span id="currentTime">0:00</span> / <span id="duration">--:--</span></div>
    </div>
    <audio id="articleAudio" ontimeupdate="updateProgress()" onended="resetPlayBtn()">
      <source src="{audio_path}" type="audio/mpeg">
    </audio>
  </div>
'''
    
    # JavaScript
    audio_js = '''
<script>
function toggleAudio() {
  const audio = document.getElementById("articleAudio");
  const playIcon = document.getElementById("playIcon");
  const pauseIcon = document.getElementById("pauseIcon");
  if (audio.paused) {
    audio.play();
    playIcon.style.display = "none";
    pauseIcon.style.display = "block";
  } else {
    audio.pause();
    playIcon.style.display = "block";
    pauseIcon.style.display = "none";
  }
}
function updateProgress() {
  const audio = document.getElementById("articleAudio");
  const progress = document.getElementById("progressFill");
  const currentTime = document.getElementById("currentTime");
  const duration = document.getElementById("duration");
  if (audio.duration) {
    const percent = (audio.currentTime / audio.duration) * 100;
    progress.style.width = percent + "%";
    currentTime.textContent = formatTime(audio.currentTime);
    duration.textContent = formatTime(audio.duration);
  }
}
function seekAudio(e) {
  const audio = document.getElementById("articleAudio");
  const bar = e.currentTarget;
  const rect = bar.getBoundingClientRect();
  const percent = (e.clientX - rect.left) / rect.width;
  audio.currentTime = percent * audio.duration;
}
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins + ":" + (secs < 10 ? "0" : "") + secs;
}
function resetPlayBtn() {
  document.getElementById("playIcon").style.display = "block";
  document.getElementById("pauseIcon").style.display = "none";
}
</script>
'''
    
    # 1. 添加 CSS（在 </style> 之前）
    if '/* Audio Player */' not in html:
        html = html.replace('</style>', audio_css + '</style>')
    
    # 2. 添加播放器 HTML（在 article-meta 之后）
    # 找到 article-meta 的结束标签
    meta_end = html.find('</div>', html.find('class="article-meta"'))
    if meta_end != -1:
        insert_pos = meta_end + 6  # </div> 的长度
        html = html[:insert_pos] + audio_html + html[insert_pos:]
    
    # 3. 添加 JavaScript（在 </body> 之前）
    html = html.replace('</body>', audio_js + '</body>')
    
    # 写回文件
    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 已添加音频播放器: {article_path}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 add-audio-player.py <article.html>")
        sys.exit(1)
    
    success = add_audio_player(sys.argv[1])
    sys.exit(0 if success else 1)
