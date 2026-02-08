# STLoop 开发经验与改动记录

> 后续改动请追加到本文档，作为项目经验沉淀。

## 变更记录

### 2025-02-07 下载失败重试与替代方案

**问题**：
- 从 GitHub 下载 STM32CubeF4 时出现 HTTP 502 Bad Gateway（国内网络/代理不稳定）
- 失败后直接退出，用户无重试机会
- 单一下载源，无备选方案

**改动**：
1. **自动重试**：下载失败时自动重试 3 次，每次间隔 2 秒
2. **交互式重试**：chat 流程中捕获下载失败后，提示「是否重试？(y/n)」
3. **download_cube 改为抛异常**：不再 `sys.exit(1)`，由调用方决定是否重试或退出
4. **替代下载说明**：在失败提示中补充手动下载方式
   - 官方: https://www.st.com/en/embedded-software/stm32cubef4.html
   - GitHub: https://github.com/STMicroelectronics/STM32CubeF4/releases
   - 国内若 GitHub 不可用，可配置代理或手动下载后解压到 `cube/STM32CubeF4`

**下载方式分析**：
| 方式 | 优点 | 缺点 |
|------|------|------|
| GitHub releases | 无需登录，可自动化 | 国内易 502/超时 |
| ST 官网 | 官方源 | 需登录，链接可能变动 |
| 手动下载 | 可靠 | 需用户操作 |

**建议**：保留 GitHub 自动下载，失败时提示手动方式并支持重试。

### 2025-02-08 生成项目目录与自包含

**问题**：
- 生成项目在 STloop 工具内的 `output/generated`，与工具耦合
- 项目引用外部 cube 路径，无法独立复制、上传 git、二次开发

**需求**：功能与业务解耦；生成项目自包含 cube，便于用户复制/二次开发

**改动**：
1. **输出到 STloop 上一级**：`_paths.get_projects_dir()` 返回 workspace 根，生成 `{workspace}/generated`
2. **项目内嵌 cube**：gen 时复制 cube 到 `project/cube/STM32CubeF4`，项目自包含
3. **CMake 兼容**：支持 Cube 不同版本的 `system_stm32f4xx.c` 路径（Templates/ 或 Source/）
4. **推广原则**：类似改动（目录解耦、自包含）应推广到其他功能，记录于 LESSONS 与 developer skill

**类比检查（避免遗漏）**：
- CLI gen：default 输出改为 `get_projects_dir()/generated`，build 时不传 cube_path（用项目内嵌）
- CLI build：项目有内嵌 cube 则不传 cube_path，否则 ensure_cube 后用 client.cube_path

### 2025-02-08 芯片动态配置

**问题**：CMake 硬编码 STM32F411xE，用户手册为 F405 等时编译配置错误。目录查找应动态配置，按用户给的手册推断芯片。

**改动**：
- `chip_config.infer_chip(prompt, datasheet_paths)` 从手册文件名或自然语言推断芯片
- gen 时写入 `chip_config.cmake`（MCU_DEVICE, STARTUP_PATTERN, LINKER_PATTERN）
- CMake 动态按 pattern 在 cube 中查找 startup_*.s 和 *.ld
- 支持 F401/F405/F407/F410/F411/F412/F413/F427/F429/F437/F439/F446/F469/F479

**原则**：不以默认芯片为准，按用户手册/需求推断后动态配置。

### 2025-02-08 build 优先使用项目内嵌 cube

**问题**：chat 调用 build(out) 时，client 传 self.cube_path（外部）覆盖了项目内嵌 cube。

**改动**：client.build 检测项目有 `cube/STM32CubeF4/Drivers` 时，传 cube_path=None 让 builder 用项目内嵌。

### 2025-02-07 linker 脚本 (.ld) 来源

**问题**：`No linker script .ld found under .../cube/STM32CubeF4/Drivers`，CMake 在 Drivers 下找不到 `.ld`。

**分析**：
- **cmsis_device_f4 不包含 GCC linker 脚本**：ST 在 [issue #10](https://github.com/STMicroelectronics/cmsis_device_f4/issues/10) 明确说明，F4 等 legacy 系列由 CubeIDE/CubeMX 生成，不再在 CMSIS 仓库提供
- **linker 脚本实际位置**：完整 STM32CubeF4 的 `Projects/[Board]/Examples|Applications/.../[IDE]/.../[MCU]_FLASH.ld`，例如 `Projects/STM32F411RE-Nucleo/Examples/Blink/SW4STM32/STM32F411RETx_FLASH.ld`
- **Drivers 目录本身不含 .ld**：仅含 HAL/CMSIS 源码，不包含各芯片的链接脚本

**改动**：
- CMake 在 CMSIS_DEVICE、Drivers 未找到后，回退到 `Projects/**/*.ld` 查找
- 完整 cube（含 Projects）下载后即可正常编译
