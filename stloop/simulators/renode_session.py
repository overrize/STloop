"""
Renode 持久化仿真会话管理

解决用户问题：
1. 仿真结束后如何重新打开？
2. 如何保持 UART 输出可见？
3. 如何支持 GDB 调试会话持续？

方案：
- 使用 Renode 的 monitor/telnet 接口
- 保存会话配置到文件
- 提供 reopen/resume 命令
"""

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import os


@dataclass
class SimulationSession:
    """仿真会话信息"""

    session_id: str
    elf_path: str
    resc_script: str
    mcu: str
    telnet_port: int
    gdb_port: int
    uart_port: Optional[int]
    created_at: str
    status: str  # "running", "stopped", "paused"
    pid: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationSession":
        return cls(**data)


class RenodeSessionManager:
    """
    Renode 会话管理器

    功能：
    1. 启动持久化仿真（带 monitor socket）
    2. 保存会话信息到文件
    3. 重新连接到运行中的仿真
    4. 在新终端中恢复 UART 输出
    """

    SESSION_DIR = Path.home() / ".stloop" / "renode_sessions"

    def __init__(self):
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._current_session: Optional[SimulationSession] = None

    def _generate_session_id(self) -> str:
        """生成唯一会话 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"

    def _find_available_port(self, start: int = 1234) -> int:
        """查找可用端口"""
        import socket

        for port in range(start, start + 100):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    return port
        return start

    def _save_session(self, session: SimulationSession):
        """保存会话到文件"""
        session_file = self.SESSION_DIR / f"{session.session_id}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> Optional[SimulationSession]:
        """加载会话"""
        session_file = self.SESSION_DIR / f"{session_id}.json"
        if not session_file.exists():
            return None
        with open(session_file, "r", encoding="utf-8") as f:
            return SimulationSession.from_dict(json.load(f))

    def list_sessions(self) -> list[SimulationSession]:
        """列出所有会话"""
        sessions = []
        for f in self.SESSION_DIR.glob("*.json"):
            with open(f, "r", encoding="utf-8") as file:
                sessions.append(SimulationSession.from_dict(json.load(file)))
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def start_persistent_simulation(
        self,
        elf_path: Path,
        mcu: str = "STM32F411RE",
        show_gui: bool = False,
    ) -> SimulationSession:
        """
        启动持久化仿真

        特点：
        - 使用 socket-based monitor，允许重新连接
        - 保存会话信息，支持 resume
        - UART 输出到文件，可随时查看
        """
        from stloop.simulators.renode import find_renode_bin, generate_resc_script, RenodeConfig

        session_id = self._generate_session_id()
        elf_path = Path(elf_path).resolve()

        # 分配端口
        telnet_port = self._find_available_port(1234)
        gdb_port = self._find_available_port(3333)
        uart_port = self._find_available_port(2345)

        # 创建输出目录
        session_dir = self.SESSION_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        uart_log = session_dir / "uart.log"

        # 生成增强版 resc 脚本
        config = RenodeConfig(
            mcu=mcu,
            gdb_port=gdb_port,
            telnet_port=telnet_port,
            show_gui=show_gui,
            enable_uart=True,
        )

        resc_script = self._generate_persistent_resc(elf_path, mcu, config, telnet_port, uart_log)

        # 启动 Renode
        bin_path = find_renode_bin()
        if not bin_path:
            raise RuntimeError("Renode not found")

        # 使用 nohup/Start-Process 让进程在后台持续运行
        log_file = session_dir / "renode.log"

        if os.name == "nt":  # Windows
            # 使用 PowerShell Start-Process 在后台运行
            ps_script = session_dir / "start_renode.ps1"
            ps_content = f"""
$proc = Start-Process -FilePath "{bin_path}" -ArgumentList "`"{resc_script}`"", "--disable-gui" -WindowStyle Hidden -PassThru
$proc.Id | Out-File "{session_dir / "pid.txt"}"
Write-Host "Renode started with PID: $($proc.Id)"
Write-Host "Telnet: telnet localhost {telnet_port}"
Write-Host "GDB: localhost:{gdb_port}"
Write-Host "UART Log: {uart_log}"
"""
            ps_script.write_text(ps_content, encoding="utf-8")

            # 启动 PowerShell 脚本
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

            # 等待进程启动
            time.sleep(2)
            pid_file = session_dir / "pid.txt"
            pid = int(pid_file.read_text().strip()) if pid_file.exists() else None

        else:  # Linux/Mac
            # 使用 nohup 在后台运行
            with open(log_file, "w") as log:
                proc = subprocess.Popen(
                    [str(bin_path), str(resc_script), "--disable-gui"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            pid = proc.pid

        # 创建会话对象
        session = SimulationSession(
            session_id=session_id,
            elf_path=str(elf_path),
            resc_script=str(resc_script),
            mcu=mcu,
            telnet_port=telnet_port,
            gdb_port=gdb_port,
            uart_port=uart_port,
            created_at=datetime.now().isoformat(),
            status="running",
            pid=pid,
        )

        self._save_session(session)
        self._current_session = session

        # 生成 reopen 脚本
        self._generate_reopen_script(session, session_dir)

        return session

    def _generate_persistent_resc(
        self,
        elf_path: Path,
        mcu: str,
        config: Any,
        telnet_port: int,
        uart_log: Path,
    ) -> Path:
        """生成支持持久化的 resc 脚本"""
        from stloop.simulators.renode import get_platform_file, _get_renode_platforms_dir

        platform = get_platform_file(mcu) or "platforms/cpus/stm32f4.repl"
        platforms_dir = _get_renode_platforms_dir()
        if platforms_dir:
            platform_file = platforms_dir / platform.replace("platforms/", "").replace("/", os.sep)
            if platform_file.exists():
                platform = str(platform_file)

        elf_path_str = str(elf_path.resolve()).replace("\\", "/")
        session_dir = uart_log.parent

        # 增强版脚本：支持 monitor socket、UART 日志
        script_lines = [
            f"; Persistent Renode Session",
            f"; ELF: {elf_path.name}",
            f"; Telnet: localhost:{telnet_port}",
            f"; GDB: localhost:{config.gdb_port}",
            "",
            "; Create machine",
            f'mach create "{mcu}"',
            "",
            "; Load platform",
            f"machine LoadPlatformDescription @{platform}",
            "",
            "; Setup monitor socket for reconnection",
            f'emulation CreateServerSocketTerminal {telnet_port} "monitor" false',
            "machine SetPrimaryConsole monitor",
            "",
            "; Load firmware",
            f'sysbus LoadELF "{elf_path_str}"',
            "",
            "; Setup UART logging",
            f'emulation CreateFileBackedUartTerminal "{uart_log}"',
            "connector Connect sysbus.usart1 terminal",
            "",
            "; Start GDB server",
            f"machine StartGdbServer {config.gdb_port}",
            "",
            "; Start simulation (non-blocking)",
            "start",
            "",
            f"; Session info saved to {session_dir}",
        ]

        resc_path = session_dir / "persistent_simulation.resc"
        resc_path.write_text("\n".join(script_lines), encoding="utf-8")
        return resc_path

    def _generate_reopen_script(self, session: SimulationSession, session_dir: Path):
        """生成重新打开仿真的脚本"""

        if os.name == "nt":  # Windows
            # PowerShell 脚本
            ps_script = session_dir / "reopen.ps1"
            ps_content = f"""
# Renode Simulation Session Reopener
# Session: {session.session_id}
# Created: {session.created_at}

Write-Host @"
========================================
  Renode Simulation Session
========================================
Session ID: {session.session_id}
MCU: {session.mcu}
ELF: {Path(session.elf_path).name}

Connection Options:
  1. Telnet (Monitor): telnet localhost {session.telnet_port}
  2. GDB Server: localhost:{session.gdb_port}

Log Files:
  - UART: {session_dir / "uart.log"}
  - Renode: {session_dir / "renode.log"}

Commands:
  - View UART: Get-Content '{session_dir / "uart.log"}' -Wait
  - Connect: telnet localhost {session.telnet_port}
  - GDB: arm-none-eabi-gdb -ex 'target remote localhost:{session.gdb_port}'
========================================
"@

# Check if session is still running
$pidFile = "{session_dir / "pid.txt"}"
if (Test-Path $pidFile) {{
    $pid = Get-Content $pidFile
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($process) {{
        Write-Host "Status: RUNNING (PID: $pid)" -ForegroundColor Green
    }} else {{
        Write-Host "Status: STOPPED" -ForegroundColor Red
        Write-Host "To restart, run the original simulation command again."
    }}
}} else {{
    Write-Host "Status: UNKNOWN" -ForegroundColor Yellow
}}

# Keep window open
Write-Host "`nPress any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""
            ps_script.write_text(ps_content, encoding="utf-8")

            # 创建快捷方式到项目目录
            reopen_bat = session_dir / "重新打开终端查看仿真.bat"
            bat_content = f"""@echo off
echo Starting Renode session viewer...
powershell -ExecutionPolicy Bypass -File "{ps_script}"
"""
            reopen_bat.write_text(bat_content, encoding="gbk")

            # 同时在 ELF 目录也放一个
            elf_dir = Path(session.elf_path).parent
            if elf_dir != session_dir:
                shortcut = elf_dir / "_重新打开仿真终端.bat"
                shortcut.write_text(bat_content, encoding="gbk")

        else:  # Linux/Mac
            # Bash 脚本
            sh_script = session_dir / "reopen.sh"
            sh_content = f"""#!/bin/bash
# Renode Simulation Session Reopener
# Session: {session.session_id}

cat << 'EOF'
========================================
  Renode Simulation Session
========================================
Session ID: {session.session_id}
MCU: {session.mcu}
ELF: {Path(session.elf_path).name}

Connection Options:
  1. Telnet (Monitor): telnet localhost {session.telnet_port}
  2. GDB Server: localhost:{session.gdb_port}

Log Files:
  - UART: {session_dir / "uart.log"}
  - GDB: arm-none-eabi-gdb -ex 'target remote localhost:{session.gdb_port}'

========================================
EOF

# Check if still running
if [ -f "{session_dir}/pid.txt" ]; then
    PID=$(cat "{session_dir}/pid.txt")
    if ps -p $PID > /dev/null; then
        echo "Status: RUNNING (PID: $PID)"
    else
        echo "Status: STOPPED"
        echo "To restart, run the original simulation command again."
    fi
fi

# Show UART log in real-time
echo ""
echo "Showing UART output (Ctrl+C to exit):"
tail -f "{session_dir / "uart.log"}"
"""
            sh_script.write_text(sh_content, encoding="utf-8")
            sh_script.chmod(0o755)

    def reopen_session(self, session_id: Optional[str] = None) -> bool:
        """
        重新打开会话

        - Windows: 打开 PowerShell 窗口显示连接信息
        - Linux/Mac: 在终端中显示 UART 日志
        """
        if session_id is None:
            # 使用最新的会话
            sessions = self.list_sessions()
            if not sessions:
                print("No active sessions found.")
                return False
            session = sessions[0]
        else:
            session = self.load_session(session_id)
            if not session:
                print(f"Session {session_id} not found.")
                return False

        session_dir = self.SESSION_DIR / session.session_id

        if os.name == "nt":
            # 打开 PowerShell 窗口
            ps_script = session_dir / "reopen.ps1"
            if ps_script.exists():
                subprocess.Popen(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                return True
        else:
            # 在终端中打开
            sh_script = session_dir / "reopen.sh"
            if sh_script.exists():
                subprocess.Popen(
                    ["gnome-terminal", "--", "bash", str(sh_script)],
                    # 或者使用 xterm, konsole 等
                )
                return True

        return False

    def connect_telnet(self, session_id: Optional[str] = None):
        """通过 telnet 连接到仿真 monitor"""
        if session_id is None:
            sessions = self.list_sessions()
            if not sessions:
                print("No active sessions found.")
                return
            session = sessions[0]
        else:
            session = self.load_session(session_id)

        if not session:
            print("Session not found.")
            return

        print(f"Connecting to Renode monitor on localhost:{session.telnet_port}...")
        print("Commands: 'pause', 'continue', 'quit', 'help'")
        print("Press Ctrl+] then 'quit' to exit telnet\n")

        subprocess.run(["telnet", "localhost", str(session.telnet_port)])


def demo():
    """演示用法"""
    print("Renode Session Manager Demo")
    print("=" * 50)

    manager = RenodeSessionManager()

    # 列出现有会话
    sessions = manager.list_sessions()
    if sessions:
        print("\nExisting sessions:")
        for s in sessions:
            print(f"  {s.session_id}: {s.mcu} ({s.status})")

    print("\nUsage:")
    print("  1. Start simulation: session = manager.start_persistent_simulation(elf_path)")
    print("  2. Reopen terminal: manager.reopen_session()")
    print("  3. Connect via telnet: manager.connect_telnet()")


if __name__ == "__main__":
    demo()
