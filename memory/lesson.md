# STLoop 开发经验教训

## 2026-03-17: Zephyr RTOS 集成问题

### 问题描述
用户要求在 STLoop 的交互流程中添加 Zephyr RTOS 选择步骤，但我的实现一直关注在构建阶段（build phase）的检测，而不是项目生成阶段（generation phase）。

### 错误分析
1. **注意力分散**：我错误地在 `builder.py` 和构建阶段添加 Zephyr 检测，而不是在交互式项目生成流程中添加步骤
2. **步骤位置错误**：用户明确给出了 STLoop 的界面（Step 2-4），我应该在 Step 3 和 Step 4 之间添加 RTOS 选择步骤
3. **没有及时记录**：应该在发现误解后立即记录到 memory，而不是继续错误方向

### 正确做法
在 `chat_rich.py` 的 `run_interactive_rich()` 函数中：
- Step 2: Describe Your Requirements
- Step 3: Additional Resources
- **Step 4: RTOS Selection** ← 新增
- Step 5: Preparing Dependencies（原 Step 4）
- Step 6: Code Generation（原 Step 5）
- Step 7: Build（原 Step 6）
- Step 8: Deploy & Test（原 Step 7）

### 关键代码位置
文件：`E:/bitloop_embedderdev-kind/stloop/chat_rich.py`
函数：`run_interactive_rich()`
添加点：在 Step 3 之后、Step 4（原）之前

### 学到的教训
1. **仔细阅读用户输入**：用户给出了明确的 ASCII 界面图，显示当前步骤，应该在这个基础上添加
2. **理解架构流程**：
   - 项目生成阶段（interactive generation）≠ 构建阶段（build）
   - RTOS 选择应该在生成时决定，影响代码模板和依赖
3. **及时确认理解**：如果不确定用户想要的步骤位置，应该立即询问而不是猜测
4. **保持专注**：当用户指出"注意力不集中"时，立即停止当前工作，重新理解需求

### 修复状态
- [x] 添加 `_select_rtos_ui()` 函数
- [x] 在 Step 3 后插入 RTOS 选择步骤
- [x] 更新所有后续步骤编号
- [x] 修改 `_ensure_cube_with_ui()` 支持 use_zephyr 参数
- [x] 记录到本文件

### 相关文件
- `stloop/chat_rich.py` - 主要修改
- `stloop/builder.py` - 支持函数
- `templates/zephyr/` - Zephyr 模板
