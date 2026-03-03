# Playwriter Scraper

自动从 Civitai 和 PromptHero 爬取新 prompts，去重后更新到 GitHub Pages。

## 前提条件

1. **Arc 浏览器** 已启动并开启远程调试
   ```bash
   # Arc 默认监听 localhost:9222
   # 确认连接: curl http://localhost:9222/json/version
   ```

2. **Playwright** 已安装
   ```bash
   npm install -g playwright
   npx playwright install chromium
   ```

3. **Git 配置** 已完成（用于自动 push）
   ```bash
   cd /tmp/pv-check
   git config user.name "Your Name"
   git config user.email "your@email.com"
   ```

## 使用方法

### 手动执行

```bash
cd /tmp/pv-check/scrapers
python3 playwriter_scraper.py
```

### 定时执行（推荐）

使用 cron 每天自动运行：

```bash
# 编辑 crontab
crontab -e

# 添加任务（每天 10:00 执行）
0 10 * * * cd /tmp/pv-check/scrapers && python3 playwriter_scraper.py >> output/cron.log 2>&1
```

## 工作流程

1. **加载现有数据** - 读取 `data/prompts.json`
2. **爬取 Civitai** - 优先使用 API，失败则用浏览器自动化
3. **爬取 PromptHero** - 使用浏览器自动化（SPA 页面需要 JS）
4. **NSFW 过滤** - 跳过包含敏感词的 prompts
5. **去重** - 基于 content_hash 和图片 URL 去重
6. **分配 ID** - 格式: `YYYYMMDD_src_NNN`
7. **保存数据** - 更新 `data/prompts.json`
8. **Git 提交** - 自动 commit + push 到 GitHub
9. **记录日志** - 写入 `scrapers/output/scrape_log.json`

## 数据源

### Civitai
- **API**: `https://civitai.com/api/v1/images`
- **参数**: sort=Most Reactions, period=Week, nsfw=None
- **目标**: 50 条/次

### PromptHero
- **URL**: `https://prompthero.com/prompts?sort=popular&time=week`
- **方法**: 浏览器自动化（Next.js SPA）
- **目标**: 20 条/次

## NSFW 过滤

自动跳过包含以下关键词的 prompts：
- nsfw, nude, naked, topless, erotic
- sexy lingerie, bondage, explicit
- hentai, xxx, porn, sex

## 去重逻辑

1. **文本去重**: 基于 prompt 文本的 MD5 hash（前 12 位）
2. **图片去重**: 检查图片 URL 是否已存在
3. **双重保障**: 同时满足才认为是新 prompt

## 日志格式

```json
{
  "timestamp": "2026-03-03 17:30:00",
  "stats": {
    "civitai_api": 45,
    "prompthero_browser": 18,
    "new_unique": 52,
    "total": 902,
    "sources": ["civitai", "prompthero"]
  }
}
```

## 故障排查

### Arc 浏览器未连接
```bash
# 检查 Arc 是否开启远程调试
curl http://localhost:9222/json/version

# 如果失败，重启 Arc 并确保开启调试模式
```

### Playwright 错误
```bash
# 重新安装浏览器
npx playwright install --force chromium
```

### Git push 失败
```bash
# 检查 Git 配置
git config --list

# 手动 push 测试
cd /tmp/pv-check
git push origin main
```

### 无新数据
- 检查数据源网站是否可访问
- 查看 `scrapers/output/scrape_log.json` 了解详情
- 尝试调整爬取参数（limit, period 等）

## 性能优化

- **API 优先**: Civitai API 比浏览器自动化快 10 倍
- **并发控制**: 避免同时爬取多个源（防止被限流）
- **增量更新**: 只爬取新内容，不重复处理
- **日志轮转**: 只保留最近 100 条日志

## 扩展数据源

要添加新数据源，参考现有代码：

```python
def scrape_newsource_browser(limit=20):
    """Scrape NewSource via browser"""
    script = """
    // Playwright script here
    """
    output = playwriter_execute(script, timeout=30)
    return parse_output(output)
```

然后在 `main()` 中调用并合并结果。
