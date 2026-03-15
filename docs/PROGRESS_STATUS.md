# STLoop 当前进度一览

**更新**：基于当前代码库与决策清单的对照。

---

## 已完成的活（同事 / 当前会话）

### 1. 终端 UI 层（同事）

- **位置**：`stloop/ui/`
- **内容**：
  - **主题** `theme.py`：Embedder 风格配色（品牌色 #00D4FF、深色背景、硬件/外设/寄存器等样式）
  - **控制台** `console.py`：基于 Rich 的全局 Console、`get_console()` / `create_console()`
  - **组件** `components/`：
    - `header.py`：启动画面、Logo、标题、footer、分区标题、清屏
    - `panels.py`：信息/错误/成功/警告/代码面板
    - `progress.py`：进度条、spinner、步骤指示 `StepIndicator`
- **测试**：根目录有 `test_ui.py`、`test_ui_simple.py` 用于验证 UI 组件
- **状态**：UI 包已就绪，**尚未接入** `chat.py` 或 CLI 主流程（chat 仍用普通 print）

### 2. Renode 仿真占位（本会话）

- **位置**：`stloop/simulators/`
- **内容**：
  - `renode.py`：`find_renode_bin()`、`run(elf_path, repl_path=None, timeout_sec=None)`
  - `__init__.py`：导出 `find_renode_bin`、`renode_run`
- **状态**：接口与占位实现已有，**尚未接 CLI**（无 `stloop demo blink --sim` 或 `stloop sim`）

### 3. 决策与计划文档（本会话）

- **`docs/DECISION_CHECKLIST.md`**：执行顺序建议、优先级（裸机+Renode 已勾选）、待确认项
- **`docs/RENODE_PLAN.md`**：裸机 + Renode 的实现步骤（清理 → renode 封装 → CLI → .repl → 文档/CI）

---

## 尚未做的活

| 项 | 说明 | 建议 |
|----|------|------|
| **A. 清理冗余** | 删除 `src/`（5 个旧文件）、`main.py`，文档改为 `python -m stloop` | 建议先做 |
| **client 拆分** | 将 `client.py` 拆成 project_generator / cube_manager / template_manager | 可选，可排在 A 或 Renode 之后 |
| **Renode CLI** | 增加 `--sim` 或 `sim` 子命令，调用 `stloop.simulators.renode.run` | 按 RENODE_PLAN 在 A 之后做 |
| **UI 接入** | 在 chat 或 CLI 中改用 `stloop.ui.get_console()` 和 components | 可选；需在 `pyproject.toml` 增加 `rich` 依赖 |
| **.repl 与 CI** | 提供/引用 STM32 用 .repl、CI 中可选跑仿真 | 见 RENODE_PLAN 步骤 4、5 |

---

## 依赖与注意事项

- **Rich**：`stloop/ui` 依赖 `rich`，当前 **未** 在 `pyproject.toml` 的 `dependencies` 中声明，若要在主流程使用 UI，需加上 `rich` 并确保安装。
- **入口**：推荐统一用 `python -m stloop`；`main.py` 仍存在且为兼容入口，清理 A 会删掉并更新 README/DEMO_GUIDE。

---

## 建议的下一步（不冲突）

1. **你 / 同事**：执行 **A（清理）**，然后按 `RENODE_PLAN.md` 接 Renode CLI（`--sim` / `sim`）。
2. **你 / 同事**：若希望 chat 用新 UI，在 `pyproject.toml` 加 `rich`，再在 `chat.py` 里接入 `get_console()` 与 components（可逐步替换 print）。
3. 两人可并行时：一人做 A + Renode CLI，另一人做 UI 依赖与 chat 接入，互不重叠。
