# 端到端代码流程（Zephyr -> 构建 -> Renode）

本文档把仓库中“端到端（e2e）”相关代码按调用顺序梳理出来，便于你理解 CI/本地测试到底走了哪条链路，以及每一步依赖/产物是什么。

---

## 1. 入口在哪里

### 1.1 GitHub Actions 工作流入口

`.github/workflows/e2e-test.yml` 里有两个 job：

- `e2e-test`
  - 运行：`python tests/e2e_test.py --skip-simulation`
- `e2e-test-with-sim`
  - 运行：`python tests/e2e_test.py`

注意：当前仓库中没有找到 `tests/e2e_test.py` 文件。若你直接依赖该工作流，CI 可能会因为入口脚本缺失而失败。

### 1.2 本地可运行的 E2E 示例入口

`tests/integration/test_zephyr_renode_e2e.py` 提供了一个可直接运行的“Zephyr -> 构建 -> Renode 脚本生成/校验”的端到端示例。

运行方式：

```bash
python tests/integration/test_zephyr_renode_e2e.py
```

---

## 2. `test_zephyr_renode_e2e.py` 的代码调用链（按 main 顺序）

该脚本的主流程位于 `main()`，核心函数依次为：

1. `check_prerequisites()`
2. `test_build_with_stloop()`
3. `test_generate_renode_script(elf_path)`
4. `test_renode_simulation(elf_path, script_path)`

### 2.1 `main()` 调度

伪代码：

```text
main()
  ok = check_prerequisites()
  ok, elf_path = test_build_with_stloop()
  ok, script_path = test_generate_renode_script(elf_path)
  ok = test_renode_simulation(elf_path, script_path)
  return
```

任何一步失败都会 `sys.exit(1)`。

---

## 3. 详细步骤：每一步做什么、依赖什么、产物是什么

### 3.1 前置条件检查：`check_prerequisites()`

在该函数中，脚本会做以下检查：

- 导入 `stloop.builder.check_zephyr_environment`、`stloop.simulators.renode.find_renode_bin`
- 检查 `west` 是否在 `PATH`
- 调用 `check_zephyr_environment()`：
  - 检查 `ZEPHYR_BASE` 是否存在且指向一个真实目录
- 检查工具链是否在 `PATH`：
  - `arm-none-eabi-gcc`
  - `cmake`
  - `ninja`
- 检查 Renode 是否存在（优先 `RENODE_BIN` 环境变量，否则查 `renode`/`Renode` 可执行文件）

产物：无（只做环境验证）。

---

### 3.2 构建固件：`test_build_with_stloop()`

该函数使用 `tests/integration/test_zephyr` 作为测试工程，并调用：

- `stloop.builder.build(project_dir, build_dir=project_dir/build_e2e, board="nucleo_f411re", use_zephyr=False)`

#### `stloop.builder.build()` 在做什么

入口逻辑（简化）：

```text
build()
  if _is_zephyr_project(project_dir):
    return _build_zephyr(project_dir, build_dir, use_zephyr=False)
  else:
    return _build_cmake(...)  # 非 Zephyr 项目时走 Cube/CMSIS 模式
```

当 `use_zephyr=False` 且检测到是 Zephyr 项目时，`_build_zephyr()` 会回退到标准 CMake 构建：

1. 走 `_build_cmake(project_dir, build_dir, board)`
2. `_build_cmake()` 内部：
   - `ensure_toolchain()`（确保工具链可用）
   - `_get_generator()`（选择 `Ninja` 或 `Unix Makefiles`）
   - 调用 `cmake -G <generator> -DBOARD=<board> -S <project_dir> -B <build_dir>`
   - 调用 `cmake --build <build_dir>`
   - 在 `build_dir` 下按若干 pattern 搜索 ELF 产物并返回

产物：

- `build_e2e/` 目录
- 一个 ELF 文件（由 `build_dir.glob()` 匹配返回，常见会包含 `*.elf*`）

---

### 3.3 生成 Renode 脚本：`test_generate_renode_script(elf_path)`

该函数会：

1. 构造 `RenodeConfig(mcu="STM32F411RE", show_gui=False, enable_uart=True)`
2. 调用 `stloop.simulators.renode.generate_resc_script(elf_path, mcu="STM32F411RE", config=config)`

#### `generate_resc_script()` 内部做什么

关键步骤：

- 选平台：
  - `PLATFORM_MAP` 将 `STM32F411RE` 映射到 `platforms/cpus/stm32f4.repl`
  - 如能定位到本机 Renode 安装目录下的 `platforms/`，会使用绝对路径替代
- 处理 ELF 路径：
  - Windows 下把反斜杠转换成正斜杠，保证 Renode 解析
- 生成 `.resc` 内容并写入文件：
  - 创建机器：`mach create "{mcu}"`
  - 加载平台描述：`machine LoadPlatformDescription @{platform}`
  - 加载固件：`sysbus LoadELF "{elf_path_str}"`
  - `enable_uart=True` 时：
    - `emulation CreateUartPtyTerminal ...`
    - `connector Connect sysbus.usart1 term`
  - 最后 `start`

产物：

- 在 `elf_path.parent/` 下写入 `simulation.resc`（默认输出路径）

---

### 3.4 仿真校验（当前脚本只“验证配置文件存在并提示命令”）：`test_renode_simulation`

该函数的行为是“轻量验证”而不是“真正启动 Renode 仿真”：

- 调用 `stloop.simulators.renode.find_renode_bin()`，确认 Renode 可用
- 校验：
  - `elf_path.exists()`
  - `script_path.exists()`
- 打印手动运行命令：
  - `renode --console {script_path}`

产物：无（只验证文件与环境）。

---

## 4. 代码与模块映射速查

- 端到端编排脚本：`tests/integration/test_zephyr_renode_e2e.py`
  - 负责 main 调度与把“固件/脚本路径”在步骤之间传递
- 构建能力：`stloop/builder.py`
  - `check_zephyr_environment()`：Zephyr SDK/环境检查
  - `build()` / `_build_zephyr()` / `_build_cmake()`：固件产物生成
- Renode 集成：`stloop/simulators/renode.py`
  - `find_renode_bin()`：定位 Renode 可执行文件
  - `generate_resc_script()`：生成 `.resc`

---

## 5. 与 CI 工作流的对应关系（重要）

当前本地可运行的 E2E 示例是 `tests/integration/test_zephyr_renode_e2e.py`，但工作流 `e2e-test.yml` 期望的入口是 `tests/e2e_test.py`（仓库里不存在）。

如果你的目标是让端到端在 CI 里“真正跑起来”，建议你：

- 让工作流调用 `tests/integration/test_zephyr_renode_e2e.py`（先跑通链路）
- 或补齐 `tests/e2e_test.py`，并把它内部实现成真正启动 Renode（当前 `test_renode_simulation` 只提示命令）

