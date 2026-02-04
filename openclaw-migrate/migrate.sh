#!/bin/bash
# OpenClaw 备份迁移脚本 v1.0
# 支持: macOS / Linux / Windows (WSL)

set -e

VERSION="1.0.0"
BACKUP_DIR="/tmp/openclaw-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

show_banner() {
    echo "=========================================="
    echo "   🦞 OpenClaw 备份迁移工具 v${VERSION}"
    echo "=========================================="
    echo ""
}

show_menu() {
    echo "请选择操作:"
    echo ""
    echo "  1) 扫描 - 扫描本机 OpenClaw 相关文件"
    echo "  2) 整体备份 - 备份全部数据(配置+记忆)"
    echo "  3) 仅备份记忆 - 只备份 MEMORY.md 和日志"
    echo "  4) 恢复 - 从备份恢复"
    echo "  5) 迁移 - 迁移到远程服务器"
    echo "  0) 退出"
    echo ""
    read -p "请输入选项 [0-5]: " choice
}

# 检测系统类型
detect_os() {
    case "$(uname -s)" in
        Darwin*) OS="macos"; HOME_DIR="$HOME" ;;
        Linux*)  OS="linux"; HOME_DIR="$HOME" ;;
        MINGW*|CYGWIN*|MSYS*) OS="windows"; HOME_DIR="$USERPROFILE" ;;
        *) OS="unknown" ;;
    esac
    log_info "检测到系统: $OS"
}

# 扫描 OpenClaw 相关文件
scan_openclaw() {
    log_info "开始扫描 OpenClaw 相关文件..."
    echo ""
    
    FOUND_PATHS=()
    
    # 1. 标准路径
    STANDARD_PATH="$HOME_DIR/.openclaw"
    if [ -d "$STANDARD_PATH" ]; then
        log_ok "标准路径: $STANDARD_PATH"
        FOUND_PATHS+=("$STANDARD_PATH")
        
        # 读取自定义 workspace
        if [ -f "$STANDARD_PATH/openclaw.json" ]; then
            WORKSPACE=$(grep -o '"workspace"[[:space:]]*:[[:space:]]*"[^"]*"' "$STANDARD_PATH/openclaw.json" 2>/dev/null | head -1 | cut -d'"' -f4)
            if [ -n "$WORKSPACE" ] && [ -d "$WORKSPACE" ]; then
                log_ok "自定义 Workspace: $WORKSPACE"
                FOUND_PATHS+=("$WORKSPACE")
            fi
        fi
    else
        log_warn "标准路径不存在: $STANDARD_PATH"
    fi
    
    echo ""
    log_info "全盘扫描关键文件..."
    
    # 2. 全盘扫描关键文件
    echo "  搜索 MEMORY.md..."
    MEMORY_FILES=$(find / -name "MEMORY.md" -type f 2>/dev/null | grep -v "node_modules" | head -20)
    
    echo "  搜索 openclaw.json..."
    CONFIG_FILES=$(find / -name "openclaw.json" -type f 2>/dev/null | head -10)
    
    echo "  搜索 AGENTS.md..."
    AGENTS_FILES=$(find / -name "AGENTS.md" -type f 2>/dev/null | grep -v "node_modules" | head -10)
    
    echo "  搜索 openclaw-workspace..."
    WORKSPACE_DIRS=$(find / -type d -name "*openclaw*workspace*" 2>/dev/null | head -10)
    
    echo ""
    log_info "=== 扫描结果 ==="
    echo ""
    
    if [ -n "$MEMORY_FILES" ]; then
        echo "📝 MEMORY.md 文件:"
        echo "$MEMORY_FILES" | while read f; do echo "   $f"; done
    fi
    
    if [ -n "$CONFIG_FILES" ]; then
        echo "⚙️  配置文件:"
        echo "$CONFIG_FILES" | while read f; do echo "   $f"; done
    fi
    
    if [ -n "$AGENTS_FILES" ]; then
        echo "🤖 AGENTS.md 文件:"
        echo "$AGENTS_FILES" | while read f; do echo "   $f"; done
    fi
    
    if [ -n "$WORKSPACE_DIRS" ]; then
        echo "📁 Workspace 目录:"
        echo "$WORKSPACE_DIRS" | while read f; do echo "   $f"; done
    fi
    
    echo ""
}

# 备份功能
backup_openclaw() {
    log_info "开始备份 OpenClaw..."
    
    BACKUP_NAME="openclaw-backup-${TIMESTAMP}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    # 备份标准路径
    STANDARD_PATH="$HOME_DIR/.openclaw"
    if [ -d "$STANDARD_PATH" ]; then
        log_info "备份 $STANDARD_PATH ..."
        cp -r "$STANDARD_PATH" "$BACKUP_PATH/dot-openclaw"
        log_ok "标准路径备份完成"
    fi
    
    # 读取并备份自定义 workspace
    if [ -f "$STANDARD_PATH/openclaw.json" ]; then
        WORKSPACE=$(grep -o '"workspace"[[:space:]]*:[[:space:]]*"[^"]*"' "$STANDARD_PATH/openclaw.json" 2>/dev/null | head -1 | cut -d'"' -f4)
        if [ -n "$WORKSPACE" ] && [ -d "$WORKSPACE" ] && [ "$WORKSPACE" != "$STANDARD_PATH/workspace" ]; then
            log_info "备份自定义 Workspace: $WORKSPACE ..."
            mkdir -p "$BACKUP_PATH/custom-workspace"
            cp -r "$WORKSPACE"/* "$BACKUP_PATH/custom-workspace/" 2>/dev/null || true
            echo "$WORKSPACE" > "$BACKUP_PATH/custom-workspace/.original_path"
            log_ok "自定义 Workspace 备份完成"
        fi
    fi
    
    # 生成备份信息
    cat > "$BACKUP_PATH/backup-info.json" << EOFINFO
{
    "version": "${VERSION}",
    "timestamp": "${TIMESTAMP}",
    "hostname": "$(hostname)",
    "os": "${OS}",
    "standard_path": "${STANDARD_PATH}",
    "custom_workspace": "${WORKSPACE:-none}"
}
EOFINFO
    
    # 打包
    ARCHIVE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    cd "$BACKUP_DIR"
    tar -czf "$ARCHIVE" "$BACKUP_NAME"
    rm -rf "$BACKUP_PATH"
    
    ARCHIVE_SIZE=$(du -h "$ARCHIVE" | cut -f1)
    echo ""
    log_ok "备份完成!"
    echo "   📦 文件: $ARCHIVE"
    echo "   📊 大小: $ARCHIVE_SIZE"
    echo ""
}

# 仅备份记忆
backup_memory_only() {
    log_info "开始备份记忆文件..."
    
    BACKUP_NAME="openclaw-memory-${TIMESTAMP}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    STANDARD_PATH="$HOME_DIR/.openclaw"
    
    # 备份标准 workspace 中的记忆
    if [ -d "$STANDARD_PATH/workspace" ]; then
        mkdir -p "$BACKUP_PATH/workspace"
        [ -f "$STANDARD_PATH/workspace/MEMORY.md" ] && cp "$STANDARD_PATH/workspace/MEMORY.md" "$BACKUP_PATH/workspace/"
        [ -f "$STANDARD_PATH/workspace/AGENTS.md" ] && cp "$STANDARD_PATH/workspace/AGENTS.md" "$BACKUP_PATH/workspace/"
        [ -f "$STANDARD_PATH/workspace/SOUL.md" ] && cp "$STANDARD_PATH/workspace/SOUL.md" "$BACKUP_PATH/workspace/"
        [ -f "$STANDARD_PATH/workspace/USER.md" ] && cp "$STANDARD_PATH/workspace/USER.md" "$BACKUP_PATH/workspace/"
        [ -d "$STANDARD_PATH/workspace/memory" ] && cp -r "$STANDARD_PATH/workspace/memory" "$BACKUP_PATH/workspace/"
        log_ok "标准 workspace 记忆备份完成"
    fi
    
    # 备份自定义 workspace 中的记忆
    if [ -f "$STANDARD_PATH/openclaw.json" ]; then
        WORKSPACE=$(grep -o '"workspace"[[:space:]]*:[[:space:]]*"[^"]*"' "$STANDARD_PATH/openclaw.json" 2>/dev/null | head -1 | cut -d'"' -f4)
        if [ -n "$WORKSPACE" ] && [ -d "$WORKSPACE" ]; then
            mkdir -p "$BACKUP_PATH/custom-workspace"
            [ -f "$WORKSPACE/MEMORY.md" ] && cp "$WORKSPACE/MEMORY.md" "$BACKUP_PATH/custom-workspace/"
            [ -f "$WORKSPACE/AGENTS.md" ] && cp "$WORKSPACE/AGENTS.md" "$BACKUP_PATH/custom-workspace/"
            [ -f "$WORKSPACE/SOUL.md" ] && cp "$WORKSPACE/SOUL.md" "$BACKUP_PATH/custom-workspace/"
            [ -f "$WORKSPACE/USER.md" ] && cp "$WORKSPACE/USER.md" "$BACKUP_PATH/custom-workspace/"
            [ -d "$WORKSPACE/memory" ] && cp -r "$WORKSPACE/memory" "$BACKUP_PATH/custom-workspace/"
            echo "$WORKSPACE" > "$BACKUP_PATH/custom-workspace/.original_path"
            log_ok "自定义 workspace 记忆备份完成"
        fi
    fi
    
    # 生成备份信息
    cat > "$BACKUP_PATH/backup-info.json" << EOFINFO
{
    "type": "memory-only",
    "version": "${VERSION}",
    "timestamp": "${TIMESTAMP}",
    "hostname": "$(hostname)"
}
EOFINFO
    
    # 打包
    ARCHIVE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    cd "$BACKUP_DIR"
    tar -czf "$ARCHIVE" "$BACKUP_NAME"
    rm -rf "$BACKUP_PATH"
    
    ARCHIVE_SIZE=$(du -h "$ARCHIVE" | cut -f1)
    echo ""
    log_ok "记忆备份完成!"
    echo "   📦 文件: $ARCHIVE"
    echo "   📊 大小: $ARCHIVE_SIZE"
    echo ""
}

# 辅助函数：仅恢复记忆文件
restore_memory_files() {
    local SRC="$1"
    local STANDARD_PATH="$HOME_DIR/.openclaw"
    
    # 从 dot-openclaw/workspace 恢复记忆
    if [ -d "$SRC/dot-openclaw/workspace" ]; then
        mkdir -p "$STANDARD_PATH/workspace/memory"
        [ -f "$SRC/dot-openclaw/workspace/MEMORY.md" ] && cp "$SRC/dot-openclaw/workspace/MEMORY.md" "$STANDARD_PATH/workspace/"
        [ -f "$SRC/dot-openclaw/workspace/AGENTS.md" ] && cp "$SRC/dot-openclaw/workspace/AGENTS.md" "$STANDARD_PATH/workspace/"
        [ -f "$SRC/dot-openclaw/workspace/SOUL.md" ] && cp "$SRC/dot-openclaw/workspace/SOUL.md" "$STANDARD_PATH/workspace/"
        [ -f "$SRC/dot-openclaw/workspace/USER.md" ] && cp "$SRC/dot-openclaw/workspace/USER.md" "$STANDARD_PATH/workspace/"
        [ -d "$SRC/dot-openclaw/workspace/memory" ] && cp -r "$SRC/dot-openclaw/workspace/memory"/* "$STANDARD_PATH/workspace/memory/" 2>/dev/null
        log_ok "标准 workspace 记忆恢复完成"
    fi
    
    # 从 workspace 目录恢复（仅记忆备份格式）
    if [ -d "$SRC/workspace" ]; then
        mkdir -p "$STANDARD_PATH/workspace/memory"
        [ -f "$SRC/workspace/MEMORY.md" ] && cp "$SRC/workspace/MEMORY.md" "$STANDARD_PATH/workspace/"
        [ -d "$SRC/workspace/memory" ] && cp -r "$SRC/workspace/memory"/* "$STANDARD_PATH/workspace/memory/" 2>/dev/null
        log_ok "记忆文件恢复完成"
    fi
    
    # 恢复自定义 workspace 记忆
    if [ -d "$SRC/custom-workspace" ]; then
        ORIG_PATH=$(cat "$SRC/custom-workspace/.original_path" 2>/dev/null)
        if [ -n "$ORIG_PATH" ]; then
            mkdir -p "$ORIG_PATH/memory"
            [ -f "$SRC/custom-workspace/MEMORY.md" ] && cp "$SRC/custom-workspace/MEMORY.md" "$ORIG_PATH/"
            [ -d "$SRC/custom-workspace/memory" ] && cp -r "$SRC/custom-workspace/memory"/* "$ORIG_PATH/memory/" 2>/dev/null
            log_ok "自定义 workspace 记忆恢复完成"
        fi
    fi
}

# 恢复功能
restore_openclaw() {
    log_info "恢复 OpenClaw 备份..."
    
    echo ""
    echo "选择恢复模式:"
    echo "  1) 整体恢复 - 恢复全部数据"
    echo "  2) 仅恢复记忆 - 只恢复 MEMORY.md 和日志"
    read -p "请选择 [1-2]: " restore_mode
    
    read -p "请输入备份文件路径: " ARCHIVE
    
    if [ ! -f "$ARCHIVE" ]; then
        log_err "文件不存在: $ARCHIVE"
        return 1
    fi
    
    RESTORE_DIR="/tmp/openclaw-restore-$$"
    mkdir -p "$RESTORE_DIR"
    
    log_info "解压备份..."
    tar -xzf "$ARCHIVE" -C "$RESTORE_DIR"
    
    BACKUP_FOLDER=$(ls "$RESTORE_DIR" | head -1)
    RESTORE_PATH="$RESTORE_DIR/$BACKUP_FOLDER"
    
    # 显示备份信息
    if [ -f "$RESTORE_PATH/backup-info.json" ]; then
        echo ""
        log_info "备份信息:"
        cat "$RESTORE_PATH/backup-info.json"
        echo ""
    fi
    
    read -p "确认恢复? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        rm -rf "$RESTORE_DIR"
        return 0
    fi
    
    if [ "$restore_mode" = "1" ]; then
        # 整体恢复
        if [ -d "$RESTORE_PATH/dot-openclaw" ]; then
            log_info "恢复到 $HOME_DIR/.openclaw ..."
            rm -rf "$HOME_DIR/.openclaw"
            cp -r "$RESTORE_PATH/dot-openclaw" "$HOME_DIR/.openclaw"
            log_ok "标准路径恢复完成"
        fi
        
        if [ -d "$RESTORE_PATH/custom-workspace" ]; then
            ORIG_PATH=$(cat "$RESTORE_PATH/custom-workspace/.original_path" 2>/dev/null)
            if [ -n "$ORIG_PATH" ]; then
                read -p "恢复自定义 Workspace 到 $ORIG_PATH? (y/n): " ws_confirm
                if [ "$ws_confirm" = "y" ]; then
                    mkdir -p "$ORIG_PATH"
                    cp -r "$RESTORE_PATH/custom-workspace"/* "$ORIG_PATH/" 2>/dev/null || true
                    rm -f "$ORIG_PATH/.original_path"
                    log_ok "自定义 Workspace 恢复完成"
                fi
            fi
        fi
    else
        # 仅恢复记忆
        restore_memory_files "$RESTORE_PATH"
    fi
    
    rm -rf "$RESTORE_DIR"
    echo ""
    log_ok "恢复完成! 请重启 OpenClaw 服务"
}

# 迁移到远程服务器
migrate_openclaw() {
    log_info "迁移 OpenClaw 到远程服务器..."
    
    echo ""
    echo "选择迁移模式:"
    echo "  1) 整体迁移 - 迁移全部数据"
    echo "  2) 仅迁移记忆 - 只迁移 MEMORY.md 和日志"
    read -p "请选择 [1-2]: " migrate_mode
    
    read -p "远程服务器 (user@host): " REMOTE
    read -p "SSH 端口 [22]: " PORT
    PORT=${PORT:-22}
    
    # 根据模式选择备份
    if [ "$migrate_mode" = "1" ]; then
        backup_openclaw
        ARCHIVE=$(ls -t ${BACKUP_DIR}/openclaw-backup-*.tar.gz 2>/dev/null | head -1)
    else
        backup_memory_only
        ARCHIVE=$(ls -t ${BACKUP_DIR}/openclaw-memory-*.tar.gz 2>/dev/null | head -1)
    fi
    
    if [ -z "$ARCHIVE" ]; then
        log_err "备份失败"
        return 1
    fi
    
    log_info "传输到远程服务器..."
    scp -P "$PORT" "$ARCHIVE" "${REMOTE}:/tmp/"
    
    REMOTE_FILE="/tmp/$(basename $ARCHIVE)"
    
    log_info "远程恢复..."
    if [ "$migrate_mode" = "1" ]; then
        # 整体恢复
        ssh -p "$PORT" "$REMOTE" "bash -s" << EOFREMOTE
cd /tmp
tar -xzf "$REMOTE_FILE"
BACKUP_FOLDER=\$(ls -d openclaw-backup-* 2>/dev/null | head -1)
if [ -d "\$BACKUP_FOLDER/dot-openclaw" ]; then
    rm -rf ~/.openclaw
    cp -r "\$BACKUP_FOLDER/dot-openclaw" ~/.openclaw
    echo "整体恢复完成"
fi
rm -rf "\$BACKUP_FOLDER" "$REMOTE_FILE"
EOFREMOTE
    else
        # 仅记忆恢复
        ssh -p "$PORT" "$REMOTE" "bash -s" << EOFREMOTE
cd /tmp
tar -xzf "$REMOTE_FILE"
BACKUP_FOLDER=\$(ls -d openclaw-memory-* 2>/dev/null | head -1)
mkdir -p ~/.openclaw/workspace/memory
[ -f "\$BACKUP_FOLDER/workspace/MEMORY.md" ] && cp "\$BACKUP_FOLDER/workspace/MEMORY.md" ~/.openclaw/workspace/
[ -d "\$BACKUP_FOLDER/workspace/memory" ] && cp -r "\$BACKUP_FOLDER/workspace/memory"/* ~/.openclaw/workspace/memory/ 2>/dev/null
echo "记忆恢复完成"
rm -rf "\$BACKUP_FOLDER" "$REMOTE_FILE"
EOFREMOTE
    fi
    
    log_ok "迁移完成!"
}

# 主函数
main() {
    show_banner
    detect_os
    
    while true; do
        show_menu
        case $choice in
            1) scan_openclaw ;;
            2) backup_openclaw ;;
            3) backup_memory_only ;;
            4) restore_openclaw ;;
            5) migrate_openclaw ;;
            0) echo "再见!"; exit 0 ;;
            *) log_err "无效选项" ;;
        esac
        echo ""
        read -p "按回车继续..."
    done
}

main "$@"
