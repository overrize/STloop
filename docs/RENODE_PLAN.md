# 裸机 LL + Renode 仿真 — 实现计划

**目标**：在不动 RTOS 的前提下，先跑通现有流程（gen → build → flash），并用 Renode 做仿真验证，无需实体板即可验证 elf。

---

## 1. 前置条件

- 现有裸机流程：`stloop demo blink` / `gen` → `build` → 得到 `.elf`
- Renode：需安装 [Renode](https://renode.io/) 并加入 PATH（或配置 `RENODE_BIN`）
- 目标芯片：当前以 STM32F4（如 F411RE）为主，Renode 需有对应机器描述或通用 Cortex-M4 平台

---

## 2. 实现步骤

| 步骤 | 内容 | 说明 |
|------|------|------|
| 1 | 清理冗余（A） | 删除 `src/`、`main.py`，统一入口为 `python -m stloop` |
| 2 | 新增 `stloop/simulators/renode.py` | 封装：检测 `renode` 可执行文件、根据 target 选择 .repl、启动 Renode 加载 elf |
| 3 | CLI 子命令 `sim` / `run --sim` | 例如：`stloop demo blink --sim` 或 `stloop sim <project_dir>`，编译后在 Renode 中运行 elf |
| 4 | 提供 STM32F4.repl（或引用上游） | 若 Renode 已有 STM32 平台则复用；否则在项目中提供最小 .repl 脚本 |
| 5 | 文档与 CI | README 中说明安装 Renode、使用 `--sim`；CI 可选跑一条仿真用例（若 Renode 已装） |

---

## 3. 接口设计（占位已写在代码中）

- `stloop.simulators.renode.run(elf_path: Path, repl_path: Optional[Path] = None, timeout_sec: Optional[int] = None)`
  - 返回：子进程结果或通过/超时状态，便于后续做「仿真 N 秒无崩溃即通过」的简单测试。
- `stloop.simulators.renode.find_renode_bin() -> Optional[Path]`
  - 用于 check 或友好报错。

---

## 4. 与现有流程的关系

- **gen / build**：不变，仍产出裸机 elf。
- **flash**：不变，仍用 pyOCD 烧录实体板。
- **新增**：`--sim` 或 `sim` 子命令在 Renode 中跑 elf，作为「无板验证」路径。

优先级已确认为：**先裸机 + Renode**，Zephyr/FreeRTOS 后续再排。
