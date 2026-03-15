"""
MCU 数据库

包含支持的微控制器信息：
- STM32 系列
- ESP32 系列
- nRF52 系列
- RP2040
- RISC-V
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class MCUFamily(str, Enum):
    """MCU 系列"""

    STM32 = "STM32"
    ESP32 = "ESP32"
    NRF52 = "nRF52"
    RP2 = "RP2"
    RISCV = "RISC-V"


class CoreType(str, Enum):
    """处理器核心类型"""

    CORTEX_M0 = "Cortex-M0"
    CORTEX_M3 = "Cortex-M3"
    CORTEX_M4 = "Cortex-M4"
    CORTEX_M7 = "Cortex-M7"
    CORTEX_M33 = "Cortex-M33"
    XTENSA = "Xtensa LX7"
    XTENSA_DUAL = "Xtensa LX7 (Dual)"
    RISCV = "RISC-V"


@dataclass
class Peripheral:
    """外设信息"""

    name: str
    available: bool = True
    count: int = 1
    description: str = ""


@dataclass
class MCUInfo:
    """MCU 详细信息"""

    name: str
    family: MCUFamily
    core: CoreType
    frequency_mhz: int
    package: str
    flash_kb: int
    ram_kb: int
    peripherals: List[Peripheral] = field(default_factory=list)
    description: str = ""

    # 开发工具链支持
    supports_cmsis: bool = False
    supports_hal: bool = False
    supports_zephyr: bool = False
    supports_arduino: bool = False

    def get_peripheral_names(self) -> List[str]:
        """获取外设名称列表"""
        return [p.name for p in self.peripherals if p.available]


# ============================================
# STM32 系列
# ============================================

STM32_F4_SERIES = [
    MCUInfo(
        name="STM32F411RE",
        family=MCUFamily.STM32,
        core=CoreType.CORTEX_M4,
        frequency_mhz=100,
        package="LQFP-64",
        flash_kb=512,
        ram_kb=128,
        peripherals=[
            Peripheral("UART", True, 3, "USART1/2/6"),
            Peripheral("SPI", True, 5, "SPI1/2/3/4/5"),
            Peripheral("I2C", True, 3, "I2C1/2/3"),
            Peripheral("ADC", True, 1, "1x 12-bit ADC"),
            Peripheral("TIM", True, 10, "高级定时器 + 基本定时器"),
            Peripheral("DMA", True, 2, "2个DMA控制器"),
            Peripheral("USB", False, 0, "不支持USB"),
            Peripheral("ETH", False, 0, "不支持以太网"),
            Peripheral("CAN", False, 0, "不支持CAN"),
        ],
        description="Entry-level Cortex-M4, Nucleo board friendly",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
    MCUInfo(
        name="STM32F407VG",
        family=MCUFamily.STM32,
        core=CoreType.CORTEX_M4,
        frequency_mhz=168,
        package="LQFP-100",
        flash_kb=1024,
        ram_kb=192,
        peripherals=[
            Peripheral("UART", True, 6, "USART1/2/3/6, UART4/5"),
            Peripheral("SPI", True, 3, "SPI1/2/3"),
            Peripheral("I2C", True, 3, "I2C1/2/3"),
            Peripheral("ADC", True, 3, "3x 12-bit ADC"),
            Peripheral("TIM", True, 17, "高级/通用/基本定时器"),
            Peripheral("DMA", True, 2, "2个DMA控制器, 16 streams"),
            Peripheral("USB", True, 1, "USB OTG FS/HS"),
            Peripheral("ETH", True, 1, "以太网MAC"),
            Peripheral("CAN", True, 2, "CAN1/2"),
        ],
        description="High-performance Cortex-M4 with USB and Ethernet",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
    MCUInfo(
        name="STM32F405RG",
        family=MCUFamily.STM32,
        core=CoreType.CORTEX_M4,
        frequency_mhz=168,
        package="LQFP-64",
        flash_kb=1024,
        ram_kb=192,
        peripherals=[
            Peripheral("UART", True, 6),
            Peripheral("SPI", True, 3),
            Peripheral("I2C", True, 3),
            Peripheral("ADC", True, 3),
            Peripheral("TIM", True, 17),
            Peripheral("DMA", True, 2),
            Peripheral("USB", True, 1),
            Peripheral("ETH", False, 0),
            Peripheral("CAN", True, 2),
        ],
        description="Cortex-M4 without Ethernet, cost-effective",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
    MCUInfo(
        name="STM32F446RE",
        family=MCUFamily.STM32,
        core=CoreType.CORTEX_M4,
        frequency_mhz=180,
        package="LQFP-64",
        flash_kb=512,
        ram_kb=128,
        peripherals=[
            Peripheral("UART", True, 4),
            Peripheral("SPI", True, 4),
            Peripheral("I2C", True, 4),
            Peripheral("ADC", True, 3),
            Peripheral("TIM", True, 17),
            Peripheral("DMA", True, 2),
            Peripheral("USB", True, 1),
            Peripheral("ETH", True, 1),
            Peripheral("CAN", True, 2),
        ],
        description="High-performance with DSP and FPU",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
    MCUInfo(
        name="STM32H743VI",
        family=MCUFamily.STM32,
        core=CoreType.CORTEX_M7,
        frequency_mhz=480,
        package="LQFP-100",
        flash_kb=2048,
        ram_kb=1024,
        peripherals=[
            Peripheral("UART", True, 8),
            Peripheral("SPI", True, 6),
            Peripheral("I2C", True, 4),
            Peripheral("ADC", True, 3),
            Peripheral("TIM", True, 20),
            Peripheral("DMA", True, 2),
            Peripheral("USB", True, 2),
            Peripheral("ETH", True, 1),
            Peripheral("CAN", True, 3),
        ],
        description="High-performance Cortex-M7 with double-precision FPU",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
]

# ============================================
# ESP32 系列
# ============================================

ESP32_SERIES = [
    MCUInfo(
        name="ESP32-WROOM-32",
        family=MCUFamily.ESP32,
        core=CoreType.XTENSA_DUAL,
        frequency_mhz=240,
        package="SMD-38",
        flash_kb=4096,
        ram_kb=520,
        peripherals=[
            Peripheral("UART", True, 3),
            Peripheral("SPI", True, 4),
            Peripheral("I2C", True, 2),
            Peripheral("ADC", True, 2, "2x 12-bit SAR ADC"),
            Peripheral("TIM", True, 4),
            Peripheral("DMA", True, 1),
            Peripheral("WiFi", True, 1, "802.11 b/g/n"),
            Peripheral("BT", True, 1, "Bluetooth v4.2 + BLE"),
            Peripheral("ETH", False, 0),
        ],
        description="Classic ESP32 with WiFi + Bluetooth",
        supports_hal=False,
        supports_zephyr=True,
        supports_arduino=True,
    ),
    MCUInfo(
        name="ESP32-S3-WROOM-1",
        family=MCUFamily.ESP32,
        core=CoreType.XTENSA_DUAL,
        frequency_mhz=240,
        package="SMD-38",
        flash_kb=8192,
        ram_kb=512,
        peripherals=[
            Peripheral("UART", True, 3),
            Peripheral("SPI", True, 4),
            Peripheral("I2C", True, 2),
            Peripheral("ADC", True, 2),
            Peripheral("TIM", True, 4),
            Peripheral("DMA", True, 1),
            Peripheral("WiFi", True, 1, "802.11 b/g/n"),
            Peripheral("BT", True, 1, "BLE 5.0 + Mesh"),
            Peripheral("USB", True, 1, "USB OTG"),
        ],
        description="ESP32-S3 with AI acceleration and USB",
        supports_hal=False,
        supports_zephyr=True,
        supports_arduino=True,
    ),
    MCUInfo(
        name="ESP32-C3-WROOM-02",
        family=MCUFamily.ESP32,
        core=CoreType.RISCV,
        frequency_mhz=160,
        package="SMD-16",
        flash_kb=4096,
        ram_kb=400,
        peripherals=[
            Peripheral("UART", True, 2),
            Peripheral("SPI", True, 3),
            Peripheral("I2C", True, 1),
            Peripheral("ADC", True, 1),
            Peripheral("TIM", True, 4),
            Peripheral("DMA", True, 1),
            Peripheral("WiFi", True, 1),
            Peripheral("BT", True, 1, "BLE 5.0"),
        ],
        description="Cost-effective RISC-V with WiFi + BLE",
        supports_hal=False,
        supports_zephyr=True,
    ),
]

# ============================================
# nRF52 系列
# ============================================

NRF52_SERIES = [
    MCUInfo(
        name="nRF52840",
        family=MCUFamily.NRF52,
        core=CoreType.CORTEX_M4,
        frequency_mhz=64,
        package="QFN-48",
        flash_kb=1024,
        ram_kb=256,
        peripherals=[
            Peripheral("UART", True, 2),
            Peripheral("SPI", True, 4, "SPI/TWI/I2S"),
            Peripheral("I2C", True, 2),
            Peripheral("ADC", True, 1, "8-channel 12-bit"),
            Peripheral("TIM", True, 5),
            Peripheral("DMA", True, 1, "EasyDMA"),
            Peripheral("USB", True, 1, "USB 2.0 Device"),
            Peripheral("BT", True, 1, "BLE 5.0, Mesh, Thread, Zigbee"),
        ],
        description="Advanced BLE SoC with USB and NFC",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
        supports_arduino=True,
    ),
    MCUInfo(
        name="nRF52832",
        family=MCUFamily.NRF52,
        core=CoreType.CORTEX_M4,
        frequency_mhz=64,
        package="QFN-48",
        flash_kb=512,
        ram_kb=64,
        peripherals=[
            Peripheral("UART", True, 1),
            Peripheral("SPI", True, 3),
            Peripheral("I2C", True, 2),
            Peripheral("ADC", True, 1),
            Peripheral("TIM", True, 5),
            Peripheral("DMA", True, 1),
            Peripheral("BT", True, 1, "BLE 5.0"),
        ],
        description="Popular BLE SoC for wearables",
        supports_cmsis=True,
        supports_hal=True,
        supports_zephyr=True,
    ),
]

# ============================================
# RP2040
# ============================================

RP2_SERIES = [
    MCUInfo(
        name="RP2040",
        family=MCUFamily.RP2,
        core=CoreType.CORTEX_M0,
        frequency_mhz=133,
        package="QFN-56",
        flash_kb=0,  # 外接 Flash
        ram_kb=264,
        peripherals=[
            Peripheral("UART", True, 2),
            Peripheral("SPI", True, 2),
            Peripheral("I2C", True, 2),
            Peripheral("ADC", True, 1, "4-channel 12-bit"),
            Peripheral("TIM", True, 1),
            Peripheral("DMA", True, 1, "12 channels"),
            Peripheral("USB", True, 1, "USB 1.1 Device/Host"),
            Peripheral("PIO", True, 2, "Programmable I/O"),
        ],
        description="Raspberry Pi's dual-core Cortex-M0 with PIO",
        supports_cmsis=True,
        supports_zephyr=True,
        supports_arduino=True,
    ),
]

# ============================================
# 完整数据库
# ============================================

ALL_MCUS = STM32_F4_SERIES + ESP32_SERIES + NRF52_SERIES + RP2_SERIES

# 按名称索引
MCU_BY_NAME: Dict[str, MCUInfo] = {mcu.name: mcu for mcu in ALL_MCUS}


def get_mcu(name: str) -> Optional[MCUInfo]:
    """通过名称获取 MCU 信息"""
    return MCU_BY_NAME.get(name)


def search_mcus(
    query: str,
    family: Optional[MCUFamily] = None,
) -> List[MCUInfo]:
    """
    搜索 MCU

    Args:
        query: 搜索关键词
        family: 限定系列

    Returns:
        匹配的 MCU 列表
    """
    query = query.lower()
    results = []

    for mcu in ALL_MCUS:
        if family and mcu.family != family:
            continue

        # 匹配名称、描述、核心、封装
        if (
            query in mcu.name.lower()
            or query in mcu.description.lower()
            or query in mcu.core.value.lower()
            or query in mcu.package.lower()
        ):
            results.append(mcu)

    return results


def get_mcus_by_family(family: MCUFamily) -> List[MCUInfo]:
    """获取指定系列的所有 MCU"""
    return [mcu for mcu in ALL_MCUS if mcu.family == family]


def get_supported_families() -> List[MCUFamily]:
    """获取支持的 MCU 系列列表"""
    return list(set(mcu.family for mcu in ALL_MCUS))
