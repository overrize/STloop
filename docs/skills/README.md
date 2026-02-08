# Superpowers 风格 Cursor Skills

基于 [Superpowers](https://github.com/obra/superpowers) 方法论整理的 Cursor 技能。

## 技能列表

| 技能 | 用途 |
|------|------|
| **test-driven-development** | 实现功能/修 bug 前先写失败测试，RED-GREEN-REFACTOR |
| **systematic-debugging** | 排查 bug 时先找根因再修，四阶段流程 |
| **brainstorming** | 做功能前先澄清需求，产出设计再实现 |

## 安装

复制到 Cursor 可识别的 skills 目录：

**项目级（推荐）：**
```powershell
# 在项目根目录执行
New-Item -ItemType Directory -Force .cursor\skills
Copy-Item -Recurse docs\skills\* .cursor\skills\
```

**用户级（所有项目生效）：**
```powershell
New-Item -ItemType Directory -Force $env:USERPROFILE\.cursor\skills
Copy-Item -Recurse docs\skills\* $env:USERPROFILE\.cursor\skills\
```

## 使用

安装后，在对话中用 `@test-driven-development`、`@systematic-debugging` 或 `@brainstorming` 引用，或在相关场景下由 AI 自动应用。
