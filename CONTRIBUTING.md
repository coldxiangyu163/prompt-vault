# 🤝 Contributing to PromptVault

感谢你对 PromptVault 的关注！我们欢迎社区贡献新的 AI 生图提示词。以下是参与贡献的指南。

## 📝 如何提交 Prompt

最简单的方式是通过 **GitHub Issue 模板**提交：

1. 前往 [Issues](https://github.com/coldxiangyu163/prompt-vault/issues/new/choose)
2. 选择 **🎨 Submit a Prompt** 模板
3. 填写表单：
   - **Prompt 标题**：简短描述（必填）
   - **Prompt 内容**：完整的提示词文本（必填）
   - **AI 工具**：使用的生成工具（必填）
   - **效果预览图**：生成效果的图片链接（可选）
   - **来源链接**：原始出处（可选）
   - **风格标签**：如 `infographic, poster, 3D`（可选）
4. 提交后，维护者会审核并收录到 `data/prompts.json`

## 📊 数据格式说明

所有提示词存储在 `data/prompts.json` 中，每条记录的字段如下：

```json
{
  "id": "20260301_001",
  "prompt": "完整的提示词文本...",
  "images": ["images/example.png"],
  "tags": ["infographic", "poster", "3D"],
  "style": "photorealistic",
  "source_url": "https://x.com/username/status/...",
  "author": "@username",
  "tool": "Gemini",
  "created_at": "2026-03-01",
  "collected_at": "2026-03-01T12:00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 格式: `YYYYMMDD_NNN`，日期+序号 |
| `prompt` | string | ✅ | 完整的提示词文本 |
| `images` | string[] | ✅ | 预览图路径数组，放在 `images/` 目录下 |
| `tags` | string[] | ✅ | 风格标签，用于筛选 |
| `style` | string | ❌ | 风格分类（如 photorealistic, cartoon, illustration） |
| `source_url` | string | ❌ | 原始来源链接 |
| `author` | string | ❌ | 作者（如 `@username`） |
| `tool` | string | ✅ | AI 工具名称 |
| `created_at` | string | ✅ | 创建日期 `YYYY-MM-DD` |
| `collected_at` | string | ❌ | 收录时间 ISO 8601 格式 |

### 常用标签参考

- **风格**: `infographic`, `poster`, `3D`, `illustration`, `cartoon`, `photorealistic`, `pixel-art`
- **主题**: `portrait`, `landscape`, `product`, `food`, `architecture`, `fashion`
- **技法**: `bento`, `glassmorphism`, `flat-design`, `isometric`, `minimalist`

### 常用工具名称

- `Gemini` / `Nano Banana Pro` / `Nano Banana`
- `Midjourney`
- `DALL-E`
- `Stable Diffusion`
- `Flux`
- `ChatGPT`

## 🛠️ 本地开发

### 环境要求

- Git
- 任意静态文件服务器（Python 3 / Node.js / VS Code Live Server）

### 快速开始

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/<your-username>/prompt-vault.git
cd prompt-vault

# 2. 启动本地服务器
python3 -m http.server 8080
# 或
npx serve .

# 3. 打开浏览器
open http://localhost:8080
```

### 项目结构

```
prompt-vault/
├── index.html          # 主页面（单页应用）
├── style.css           # 样式（暗色主题 + 毛玻璃效果）
├── app.js              # 前端逻辑（筛选、搜索、分页、弹窗）
├── data/
│   └── prompts.json    # 提示词数据（核心数据文件）
├── images/             # 本地预览图
├── scrapers/           # 数据采集脚本
└── docs/               # 文档和截图
```

### 开发预览

修改代码后，刷新浏览器即可看到效果。本项目是纯静态项目，无需编译构建。

- 修改 `prompts.json` 后刷新即可看到新数据
- 修改 `style.css` 调整样式
- 修改 `app.js` 调整交互逻辑

## 📏 代码规范

### 基本原则

- **纯原生技术栈**：HTML + CSS + Vanilla JavaScript，不使用任何框架
- **零构建依赖**：无需 npm install，无需 webpack/vite
- **单文件架构**：逻辑集中在 `app.js`，样式集中在 `style.css`

### JavaScript 规范

- 使用 ES6+ 语法（`const`/`let`、箭头函数、模板字符串）
- 避免全局变量污染，使用模块化组织
- 函数和变量使用 camelCase 命名
- 添加必要的注释说明

### CSS 规范

- 使用 CSS 变量管理主题色
- 遵循 BEM 或语义化命名
- 响应式设计使用 `@media` 查询
- 暗色主题为默认主题

### JSON 数据规范

- `prompts.json` 必须是合法的 JSON 格式
- 新增数据追加到数组末尾
- `id` 不能重复
- 图片文件放在 `images/` 目录下，使用相对路径引用

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: add new prompt batch from @username
fix: fix search not working on mobile
docs: update contributing guide
style: adjust card hover animation
```

## 🐛 报告问题

发现 Bug？请通过 [Bug Report](https://github.com/coldxiangyu163/prompt-vault/issues/new?template=bug-report.yml) 模板提交。

## 💬 联系我们

- GitHub Issues: [prompt-vault/issues](https://github.com/coldxiangyu163/prompt-vault/issues)
- 作者: [@coldxiangyu](https://github.com/coldxiangyu163)

---

再次感谢你的贡献！每一条优质的提示词都能帮助更多人创作出精彩的 AI 图片。 ✨
