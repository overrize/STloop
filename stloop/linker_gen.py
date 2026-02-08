"""STM32F4 链接脚本生成器 — cube 无 .ld 时自动生成"""
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("stloop")

# linker_pat -> (flash_kb, ram_kb, ccm_kb), 0 表示无该区域
LINKER_MEMORY: dict[str, tuple[int, int, int]] = {
    "F401": (512, 64, 0),
    "F405": (1024, 128, 64),
    "F407": (1024, 128, 64),
    "F410": (128, 32, 0),
    "F411": (512, 128, 0),
    "F412": (1024, 256, 0),
    "F413": (1536, 320, 0),
    "F427": (2048, 192, 64),
    "F429": (2048, 192, 64),
    "F437": (2048, 192, 64),
    "F439": (2048, 192, 64),
    "F446": (512, 128, 0),
    "F469": (2048, 192, 64),
    "F479": (2048, 192, 64),
}

# 模板：含 {{FLASH_LEN}}, {{RAM_LEN}}, {{CCMRAM_LEN}}, {{ESTACK}}, {{HAS_CCMRAM}}
_LD_TEMPLATE = '''/*
 * Auto-generated linker script for STM32F4 (STLoop)
 * flash={{FLASH_K}}K, ram={{RAM_K}}K{{CCM_SUFFIX}}
 */
ENTRY(Reset_Handler)
_estack = {{ESTACK}};
_Min_Heap_Size = 0x200;
_Min_Stack_Size = 0x400;

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = {{FLASH_LEN}}
  RAM (xrw)   : ORIGIN = 0x20000000, LENGTH = {{RAM_LEN}}
{{CCMRAM_LINE}}
}

SECTIONS
{
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))
    . = ALIGN(4);
  } >FLASH

  .text :
  {
    . = ALIGN(4);
    *(.text) *(.text*)
    *(.glue_7) *(.glue_7t) *(.eh_frame)
    KEEP (*(.init)) KEEP (*(.fini))
    . = ALIGN(4);
    _etext = .;
  } >FLASH

  .rodata : { . = ALIGN(4); *(.rodata) *(.rodata*); . = ALIGN(4); } >FLASH
  .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } >FLASH
  .ARM : {
    __exidx_start = .;
    *(.ARM.exidx*)
    __exidx_end = .;
  } >FLASH

  .preinit_array : {
    PROVIDE_HIDDEN (__preinit_array_start = .);
    KEEP (*(.preinit_array*))
    PROVIDE_HIDDEN (__preinit_array_end = .);
  } >FLASH
  .init_array : {
    PROVIDE_HIDDEN (__init_array_start = .);
    KEEP (*(SORT(.init_array.*)))
    KEEP (*(.init_array*))
    PROVIDE_HIDDEN (__init_array_end = .);
  } >FLASH
  .fini_array : {
    PROVIDE_HIDDEN (__fini_array_start = .);
    KEEP (*(SORT(.fini_array.*)))
    KEEP (*(.fini_array*))
    PROVIDE_HIDDEN (__fini_array_end = .);
  } >FLASH

  _sidata = LOADADDR(.data);

  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data) *(.data*)
    . = ALIGN(4);
    _edata = .;
  } >RAM AT> FLASH
{{CCMRAM_SECTION}}

  . = ALIGN(4);
  .bss :
  {
    _sbss = .;
    __bss_start__ = _sbss;
    *(.bss) *(.bss*) *(COMMON)
    . = ALIGN(4);
    _ebss = .;
    __bss_end__ = _ebss;
  } >RAM

  ._user_heap_stack :
  {
    . = ALIGN(8);
    PROVIDE ( end = . );
    PROVIDE ( _end = . );
    . = . + _Min_Heap_Size;
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } >RAM

  /DISCARD/ : { libc.a ( * ) libm.a ( * ) libgcc.a ( * ) }
  .ARM.attributes 0 : { *(.ARM.attributes) }
}
'''


def generate_linker_script(
    project_dir: Path,
    linker_pat: str,
) -> Optional[Path]:
    """
    生成链接脚本到工程目录。
    返回生成的文件路径，不支持时返回 None。
    """
    project_dir = Path(project_dir)
    key = linker_pat.upper() if len(linker_pat) <= 4 else linker_pat[:4].upper()
    mem = LINKER_MEMORY.get(key)
    if not mem:
        # 尝试前缀匹配
        for k, v in LINKER_MEMORY.items():
            if k in linker_pat.upper():
                mem = v
                key = k
                break
    if not mem:
        log.warning("linker_gen: 无 %s 内存配置，跳过生成", linker_pat)
        return None

    flash_k, ram_k, ccm_k = mem
    flash_len = f"{flash_k}K"
    ram_len = f"{ram_k}K"
    estack = 0x20000000 + (ram_k * 1024)
    estack_hex = f"0x{estack:08X}"

    if ccm_k > 0:
        ccm_line = f"  CCMRAM (rw) : ORIGIN = 0x10000000, LENGTH = {ccm_k}K"
        ccm_suffix = f", ccm={ccm_k}K"
        ccm_section = '''
  _siccmram = LOADADDR(.ccmram);
  .ccmram :
  {{
    . = ALIGN(4);
    _sccmram = .;
    *(.ccmram) *(.ccmram*)
    . = ALIGN(4);
    _eccmram = .;
  }} >CCMRAM AT> FLASH
'''
    else:
        ccm_line = ""
        ccm_suffix = ""
        ccm_section = ""

    content = _LD_TEMPLATE.replace("{{FLASH_K}}", str(flash_k))
    content = content.replace("{{RAM_K}}", str(ram_k))
    content = content.replace("{{CCM_SUFFIX}}", ccm_suffix)
    content = content.replace("{{FLASH_LEN}}", flash_len)
    content = content.replace("{{RAM_LEN}}", ram_len)
    content = content.replace("{{ESTACK}}", estack_hex)
    content = content.replace("{{CCMRAM_LINE}}", ccm_line)
    content = content.replace("{{CCMRAM_SECTION}}", ccm_section)

    out_name = f"STM32{key}xx_FLASH.ld"
    out_path = project_dir / out_name
    out_path.write_text(content, encoding="utf-8")
    log.info("linker_gen: 已生成 %s (flash=%s ram=%s)", out_path, flash_len, ram_len)
    return out_path
