---
name: stloop-project
description: 本 STM32 项目的 Cursor skill。在此项目中用自然语言描述需求、修改 main.c、添加外设时使用。
---

# STM32 项目 Skill

本 skill 适用于由 STLoop 生成的嵌入式项目。AI 助手应结合本项目的手册、原理图和需求进行代码生成与修改。

## 项目约定

- 主代码：`src/main.c`
- 头文件：`inc/main.h`
- 编译：`cmake -B build -DCUBE_ROOT=<STM32Cube路径> . && cmake --build build`
- 烧录：`pyocd flash build/stm32_app.elf`

## 可引用资源

- 手册：`manuals/` 下的 PDF
- 原理图：项目根目录或 `docs/` 下的原理图文件

## 使用方式

在 Cursor 中 @ 提及本 skill，或在此目录下添加更多项目专属 skill。
