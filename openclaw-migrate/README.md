# OpenClaw 备份迁移工具

专为 OpenClaw 设计的备份、恢复、迁移工具。

## 功能

- 🔍 **扫描** - 全盘扫描 OpenClaw 相关文件
- 💾 **备份** - 备份配置、记忆、workspace
- 📥 **恢复** - 从备份恢复
- 🚀 **迁移** - 一键迁移到远程服务器

## 一键运行

```bash
bash <(curl -sL https://raw.githubusercontent.com/mango082888-bit/vps-tools/main/openclaw-migrate/migrate.sh)
```

## 备份内容

- `~/.openclaw/` 标准目录
- 自定义 workspace 路径
- MEMORY.md、AGENTS.md 等记忆文件
- openclaw.json 配置文件

## 支持系统

- ✅ macOS
- ✅ Linux / VPS
- ✅ Windows (WSL)
