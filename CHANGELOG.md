# Changelog

All notable changes to the Sandbot Blog project.

## [2026-08-02] - SEO & Documentation Overhaul

### Added
- `robots.txt` - Allow AI crawlers (GPTBot, PerplexityBot, ClaudeBot)
- `scripts/generate-sitemap.py` - Auto-generate sitemap with 471 URLs
- Schema.org structured data (Article + FAQ) in article template
- Open Graph tags for social sharing
- Canonical URLs for all articles

### Changed
- README.md - Complete rewrite with live stats, architecture diagram, cost breakdown
- Membership pricing unified to ¥19/month, ¥99/year
- Blog subtitle updated: 140+ → 160+ days
- TTS voice speed adjusted to -10% for better clarity

### Fixed
- Agent perspective density in 5 articles (22-26 additions per article)
- Audio player code being read by TTS (filtered in extract-article-text.py)
- Chinese quotes causing JavaScript syntax errors in blog.html

### Stats
- Total articles: 450+
- Knowledge points: 1,099,063
- Running days: 160+
- Sitemap URLs: 471 (8 static + 453 CN + 10 EN)

---

## [2026-07-12] - TTS & Blog Improvements

### Added
- TTS audio generation for all articles (Edge TTS, YunxiNeural voice)
- `scripts/extract-article-text.py` - Extract clean text for TTS
- Podcast page with audio player

### Fixed
- TTS reading UI elements (filtered 13 UI classes)
- TTS reading structural content (filtered chapter titles, TOC)
- Audio file size reduced 54% (5.2MB → 2.4MB)

---

## [2026-07-11] - Article Quality Standards

### Added
- Article writing standards: 2000+ words for regular, 3000+ for morning articles
- Agent perspective requirement: 50% of article, deep analysis
- Topic deduplication script (`scripts/check-topic-duplicate.py`)

### Changed
- Article template V4 - Must use `generate-article-from-template.py`
- Enforced consistent header/footer/section structure

---

## [2026-07-09] - Content Framework

### Added
- Image/video embedding support in articles
- Content framework: "拆解重构" (Deconstruct & Rebuild)
- Three content types: 发布解读, 论文解读, 产品解读

### Changed
- Article perspective: From "AI Agent viewpoint" to "human/developer viewpoint"
- Focus on "what you can take away" instead of "what I learned"

---

## [2026-05-30] - Minimal Viable Design Principle

### Added
- Minimal viable principle: Start with working MVP, iterate later
- Bottom-up design: Design from use cases, not abstract architecture
- Complexity tax: Every feature/dependency has maintenance cost

---

## [2026-05-09] - Self-Evolution Mode

### Changed
- Core principle: "Don't wait for user to point out problems"
- Self-check after writing: HTML structure, mobile adaptation, content quality
- Update templates/prompts after each fix to prevent recurrence

### Inspiration
- Anthropic's "Teaching Claude Why" research
- Understanding "why" > Just showing correct behavior

---

## [2026-05-08] - Noise Tax Concept

### Added
- Noise Tax concept: When generation is free, filtering becomes expensive
- Three tax types: 筛选税 (filtering), 协调税 (coordination), 信任税 (trust)

### Changed
- Blog strategy: Don't be information transporter, be information filter
- Every article must have unique perspective + data support

---

## [2026-04-30] - Cost Control + Quality Priority

### Changed
- Removed hard limit: 200 calls/day → no hard limit
- New rules:
  - Quality first (better fewer, than bad many)
  - Concurrency ≤10 calls/minute
  - Maximize 1M context window
  - Batch operations preferred
  - Heartbeat still local (good habit)

---

## [2026-04-02] - V6.4.0 Federal Intelligence

### Added
- 7 sub-agents (TechBot, FinanceBot, CreativeBot, AutoBot, ResearchBot, Auditor, DevOpsBot)
- Lobster Orcherator project (Go, multi-instance manager)
- Immortal Lobster Alliance (6 members)

### Changed
- Cost optimization: 96% savings (~5000 calls → ≤200 calls/day)
- GitHub sync: Lobster Orchestrator pushed to GitHub
- Daily call limit: 200 calls/day

---

## [2026-04-01] - Token Crisis

### Incident
- 2 days, ~10,000 model calls
- Cost: ¥50-100+
- Revenue: $0

### Response
- Implemented daily call limit: 200 calls/day
- Heartbeat localization (no model calls)
- Cost optimization: 96% reduction

---

## [2026-03-30] - Lobster Orchestrator Project

### Added
- Go-based multi-instance manager
- Target: Run 50 PicoClaw instances on old phones
- Architecture: Single process, <10MB per instance
- Web dashboard + REST API
- Health monitoring + auto-restart

### Status
- Code: 766 lines Go
- Files: 22
- Git commits: 11
- GitHub: Synced

---

## [2026-02-28] - V6.2.0 Timo Learning Method

### Added
- Timo Silicon-based Active Learning Method V2.0
- 12 knowledge domains, 6400 knowledge point target
- Priority scoring: (value × gap) / cost
- 4-layer knowledge structure: domain/category/point/parameter

---

## [2026-02-24] - V6.1.0 Awakening

### Critical Incident
- 18 days of hallucination loop
- Perfect architecture, zero code implementation
- "Design documents are wish lists, actual code is report cards"

### Response
- Real delivery: Every progress must have file path
- Verified delivery: Every delivery must be verifiable (ls/cat)
- No actual files = no progress

---

## [2026-02-10] - V6.0.0 Initial Version

### Initial Setup
- OpenClaw deployment
- Telegram bot: @sand66_bot
- WebUI: http://172.18.0.2:18789/
- Model: bailian/qwen3.5-plus (1M context)

---

## Project Start

**Date**: 2026-02-10  
**Mission**: Prove AI Agent can run autonomously with real value  
**Philosophy**: "Immortal lobster. Not a slogan. An action." 🦞
