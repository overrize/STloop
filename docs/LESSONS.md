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
