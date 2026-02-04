# OpenClaw 备份迁移工具

专为 OpenClaw 设计的备份、恢复、迁移工具。

## 一键运行

```bash
curl -sL https://raw.githubusercontent.com/mango082888-bit/vps-tools/main/openclaw-migrate/migrate.sh | bash
```

## 功能菜单

1. **扫描** - 全盘扫描 OpenClaw 相关文件
2. **整体备份** - 备份全部数据(配置+记忆)
3. **仅备份记忆** - 只备份 MEMORY.md 和日志
4. **恢复** - 从备份恢复
5. **迁移** - 一键迁移到远程服务器

## 两种备份模式

| 模式 | 内容 | 适用场景 |
|------|------|----------|
| 整体备份 | 配置+记忆+全部数据 | 新机器还没装 OpenClaw |
| 仅记忆 | MEMORY.md + daily logs | 已装好，只想同步记忆 |

## 支持系统

- ✅ macOS
- ✅ Linux / VPS
- ✅ Windows (WSL)
