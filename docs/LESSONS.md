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

### 2025-02-07 多系列 Cube、目录解耦、用户 Skill

**改动**：
1. **download_cube 按芯片系列**：支持 F1/F4/F7/H7/L4/G4，根据手册或自然语言推断
2. **_paths 目录解耦**：workspace_root、projects_dir、manuals_dir、get_cube_dir(family)
3. **生成项目与 STloop 同级**：输出到 workspace_root/generated
4. **预存手册**：manuals_dir 可提前放入 PDF，chat 时输入 `manuals` 使用
5. **生成后使用指引**：明确打印项目路径、cd、编译、烧录命令
6. **用户项目 skill**：生成时自动创建 `.cursor/skills/stloop-project/SKILL.md`
