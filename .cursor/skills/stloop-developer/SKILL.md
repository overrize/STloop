---
name: stloop-developer
description: STLoop 维护者与开发者 skill。用于开发、扩展、调试 STLoop 项目。当用户修改 STLoop 源码、添加新芯片支持、调整生成流程或贡献代码时使用。
---

# STLoop 开发者 Skill

## 项目结构

```
workspace_root/           # 用户工作区（STloop 的上一级）
├── STloop/               # 本仓库
│   ├── stloop/           # 包
│   ├── templates/        # CMake+LL 模板
│   └── .cursor/skills/   # 本 skill
├── my_project/           # 用户生成的项目（与 STloop 同级）
│   ├── src/
│   ├── .cursor/skills/stloop-project/  # 自动创建，用户可扩展
│   └── manuals/          # 可选：项目手册
├── manuals/              # 预存手册（可选）
└── cube/                 # STM32Cube 包（F1/F4/F7 等）
```

## 核心约定

- **功能与业务解耦**：生成的项目放在 workspace_root，不在 STloop 内部
- **Cube 按芯片系列**：F1→STM32CubeF1，F4→STM32CubeF4，F7→STM32CubeF7
- **用户 skill**：放在用户项目 `.cursor/skills/` 中
- **预存手册**：可放在 workspace_root/manuals 或项目内

## 芯片与 Cube 映射

| 芯片系列 | Cube 包 |
|----------|---------|
| F1 | STM32CubeF1 |
| F4 | STM32CubeF4 |
| F7 | STM32CubeF7 |
| H7 | STM32CubeH7 |
| L4 | STM32CubeL4 |
| G4 | STM32CubeG4 |

从手册文件名或自然语言推断：`stm32f405`→F4，`stm32f103`→F1。

## 关键路径

- `_paths.get_workspace_root()`：STloop 上一级
- `_paths.get_projects_dir()`：生成项目根
- `_paths.get_manuals_dir()`：预存手册
- `_paths.get_cube_dir(family)`：cube/STM32Cube{Family}

## 改动记录

重要改动应追加到 `docs/LESSONS.md`。
