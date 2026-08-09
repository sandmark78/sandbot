#!/bin/bash
# 操作前强制检查 - 防止重复操作和滥用子agent
# 用法: source scripts/pre-operation-check.sh <操作类型>

OPERATION_TYPE="$1"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="/home/node/.openclaw/workspace/memory/operation-log.md"

# 记录操作
log_operation() {
    echo "## $TIMESTAMP - $OPERATION_TYPE" >> "$LOG_FILE"
    echo "状态: $1" >> "$LOG_FILE"
    echo "原因: $2" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
}

# 检查是否重复操作（30分钟内）
check_duplicate() {
    local operation="$1"
    
    if [ ! -f "$LOG_FILE" ]; then
        return 0
    fi
    
    # 检查最近30分钟内是否有相同操作
    local recent=$(grep -A2 "## " "$LOG_FILE" | grep -B1 "$operation" | tail -3)
    if [ -n "$recent" ]; then
        echo "⚠️  检测到重复操作: $operation"
        echo "最近记录:"
        echo "$recent"
        return 1
    fi
    
    return 0
}

# 检查是否应该spawn子agent
check_spawn_agent() {
    local task="$1"
    
    # 规则1: 对话中的bug修复 → 不spawn
    if [[ "$OPERATION_TYPE" == *"修复"* ]] || [[ "$OPERATION_TYPE" == *"bug"* ]]; then
        echo "❌ 对话中的bug修复：主agent直接做，不spawn子agent"
        log_operation "拒绝" "对话中的bug修复应该主agent直接做"
        return 1
    fi
    
    # 规则2: 检查/验证任务 → 不spawn
    if [[ "$task" == *"检查"* ]] || [[ "$task" == *"验证"* ]]; then
        echo "❌ 简单检查/验证任务：主agent直接做"
        log_operation "拒绝" "简单任务不需要spawn"
        return 1
    fi
    
    # 规则3: 检查最近是否已spawn过
    if ! check_duplicate "spawn"; then
        echo "❌ 最近已spawn过子agent，避免重复"
        log_operation "拒绝" "短时间内重复spawn"
        return 1
    fi
    
    log_operation "允许" "$task"
    return 0
}

# 主逻辑
case "$OPERATION_TYPE" in
    "spawn"*)
        check_spawn_agent "$OPERATION_TYPE"
        ;;
    "修复"*|"bug"*)
        echo "⚠️  检测到修复操作，主agent直接做，不spawn"
        log_operation "执行" "主agent直接修复"
        ;;
    *)
        check_duplicate "$OPERATION_TYPE"
        ;;
esac
