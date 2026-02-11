# 测试报告问题分析与修复方案

参考：`E:\stloop_test\STloop_Test_Report.md`

---

## 问题一：Demo Blink 编译失败 — 缺少 linker script

### 现象
```
CMake Error: No linker script .ld in project dir or under
  E:/stloop_test/cube/STM32CubeF4-1.28.3 (checked CMSIS, Drivers, Projects)
```

### 根因
- `demo_blink` 使用**外部 cube**（不内嵌），直接 `build(project_dir, cube_path=self.cube_path)`
- 未调用 `_ensure_linker_startup_in_project`，工程目录无 `.ld` 和 `startup_*.s`
- cube 可能不含 Projects 或 .ld（如 STM32CubeF4-1.28.3 精简版）

### 修复方案
在 `demo_blink` 中，build 前补充 linker/startup：
```python
# 在 build 之前
self._ensure_linker_startup_in_project(
    project_dir, self.cube_path,
    startup_pat="f411", linker_pat="F411"  # demo 默认 STM32F411RE
)
```
Demo 使用默认芯片 F411，无需 chip_config（CMake 有默认值）。

---

## 问题二：_embed_cube 递归复制 (RecursionError)

### 现象
`test_embed_cube_skips_when_already_embedded` 报 RecursionError：`shutil.copytree` 无限递归。

### 根因
当 `cube_path` 与 `project_dir` 为同一目录或存在包含关系时，`dest = project_dir/cube/STM32CubeF4` 会落在 `cube_path` 内，导致 `copytree(source, dest)` 出现「源包含目标」的递归复制。

典型场景：测试中 `cube_path=tmp_path`、`project_dir=tmp_path` 时，`dest=tmp_path/cube/STM32CubeF4`，复制 `tmp_path` 到 `tmp_path/cube/...` 会递归进入自身。

### 修复方案
在 `_embed_cube` 开头增加路径校验，避免 dest 在 source 内：
```python
dest_resolved = dest.resolve()
src_resolved = Path(cube_path).resolve()
if dest_resolved == src_resolved or str(dest_resolved).startswith(str(src_resolved) + os.sep):
    raise ValueError(
        f"目标路径 {dest} 不能位于源路径 {cube_path} 内，会导致递归复制"
    )
```

---

## 实施顺序

1. **Demo Blink**：在 `demo_blink` 中 build 前调用 `_ensure_linker_startup_in_project`
2. **递归防护**：在 `_embed_cube` 中增加 dest/src 路径校验
