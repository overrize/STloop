# STLoop 重构与扩展 — 决策清单

基于项目分析整理的执行顺序、环境与优先级确认。

---

## 1. 执行顺序建议

| 选项 | 说明 | 建议 |
|------|------|------|
| **A** | 先清理冗余（删除 `src/`、`main.py` 等） | ✅ **推荐先做** — 改动小、风险低，避免新旧两套代码并存 |
| **B** | 直接开始 Zephyr/Renode 集成 | ❌ 不推荐 — 在冗余与臃肿代码上叠加会加大维护成本 |
| **C** | 先完成 client 重构再添加新功能 | ⚠️ 可选 — 若时间紧可 A→功能；若重视可维护性可 A→C→功能 |

**推荐路径**：**A（清理）→ 再选 C 或直接加功能**

- 先做 **A**：删除 `src/` 五文件、`main.py`（并更新 README/DEMO_GUIDE 为 `python -m stloop`），可选清理 `demos/blink` 仅 `.gitkeep` 或保留占位。
- 然后二选一：
  - **稳一点**：做 **C**（拆 `client.py` → project_generator / cube_manager / template_manager），再加裸机/Renode 或 rtos。
  - **快一点**：A 做完后直接做「裸机 LL + Renode」或 Zephyr，把 client 重构排到后面。

---

## 2. 需要你确认的项

### 2.1 Zephyr 环境

- [ ] **是否已安装 Zephyr SDK 和 west？**
  - 若 **是**：可把 Zephyr RTOS 支持排进近期计划。
  - 若 **否**：建议优先做「裸机 LL + Renode 仿真」，Zephyr 等环境就绪后再加。

### 2.2 功能优先级（请勾选你最需要先实现的）

- [x] **裸机 LL 库 + Renode 仿真** — 先跑通现有流程（gen/build/flash），用仿真验证，不动 RTOS。**← 已选优先**
- [ ] **Zephyr RTOS 支持** — 新建 `rtos/` 子包，支持 Zephyr 工程与 west 构建。
- [ ] **FreeRTOS 支持** — 新建 `rtos/` 子包，支持 FreeRTOS 工程。

---

## 3. 已达成共识的结论（来自分析）

- **冗余**：`src/` 下 5 个旧文件已迁移到 `stloop/`，可安全删除；入口推荐统一为 `python -m stloop`。
- **client.py**：约 283 行，建议拆为 project_generator / cube_manager / template_manager（可放在 A 之后或与功能并行）。
- **demos/blink**：目前仅 `.gitkeep`，可保留占位或后续用新模板补全。
- **架构**：后续可增加 `rtos/`（Zephyr/FreeRTOS）、`simulators/renode.py`、以及将 `llm/` 抽成独立子包。

---

## 4. 已确认与下一步

- **优先级已确认**：优先做 **裸机 LL + Renode 仿真**。
- **建议执行顺序**：先做 **A（清理冗余）**，再实现 Renode 仿真（见 `docs/RENODE_PLAN.md`）。

待你确认：
1. 是否先执行 **A**（删除 `src/`、`main.py`，更新文档）？
2. Zephyr 是否已安装？（仅影响后续 RTOS 排期）
