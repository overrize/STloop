cmake_minimum_required(VERSION 3.15)
project(stm32_app C CXX ASM)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

# 目标芯片配置
set(MCU_FAMILY STM32F4xx)
set(MCU_DEVICE STM32F411xE)

# STM32Cube 路径（默认项目内嵌 cube，可自包含复制/二次开发）
set(CUBE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/cube/STM32CubeF4" CACHE PATH "STM32Cube root")
if(NOT EXISTS "${CUBE_ROOT}/Drivers")
  message(FATAL_ERROR "STM32Cube not found at ${CUBE_ROOT}. Run scripts/download_cube.py first.")
endif()

# 工具链
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)

set(CMAKE_EXE_LINKER_FLAGS "--specs=nosys.specs -Wl,--gc-sections" CACHE INTERNAL "")

# 编译选项
add_compile_options(
  -mcpu=cortex-m4
  -mthumb
  -mfpu=fpv4-sp-d16
  -mfloat-abi=hard
  -ffunction-sections
  -fdata-sections
  -Wall
)
add_compile_definitions(
  USE_FULL_LL_DRIVER
  STM32F411xE
  HSE_VALUE=8000000
)

# 包含路径
set(INCLUDES
  ${CUBE_ROOT}/Drivers/CMSIS/Device/ST/STM32F4xx/Include
  ${CUBE_ROOT}/Drivers/CMSIS/Include
  ${CUBE_ROOT}/Drivers/STM32F4xx_HAL_Driver/Inc
  ${CMAKE_CURRENT_SOURCE_DIR}/inc
)

# 源文件（system/startup 从 cube 引用，兼容不同 Cube 版本路径）
set(CMSIS_DEVICE ${CUBE_ROOT}/Drivers/CMSIS/Device/ST/STM32F4xx)
set(SYSTEM_C_SRC ${CMSIS_DEVICE}/Source/Templates/system_stm32f4xx.c)
if(NOT EXISTS "${SYSTEM_C_SRC}")
  set(SYSTEM_C_SRC ${CMSIS_DEVICE}/Source/system_stm32f4xx.c)
endif()
set(STARTUP_GCC ${CMSIS_DEVICE}/Source/Templates/gcc)
if(NOT EXISTS "${STARTUP_GCC}")
  set(STARTUP_GCC ${CMSIS_DEVICE}/Source/gcc)
endif()
set(SOURCES
  src/main.c
  ${SYSTEM_C_SRC}
  ${STARTUP_GCC}/startup_stm32f411xe.s
)

# LL 驱动（仅 GPIO 示例，可按需添加）
file(GLOB LL_SOURCES ${CUBE_ROOT}/Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_ll_*.c)
# 过滤掉不需要的
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_usb.*")
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_fsmc.*")
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_sdmmc.*")

add_executable(${PROJECT_NAME}.elf ${SOURCES} ${LL_SOURCES})
target_include_directories(${PROJECT_NAME}.elf PRIVATE ${INCLUDES})
set(LINKER_SCRIPT ${STARTUP_GCC}/linker/STM32F411RETx_FLASH.ld)
target_link_options(${PROJECT_NAME}.elf PRIVATE
  -T${LINKER_SCRIPT}
  -Wl,-Map=${PROJECT_NAME}.map
)

# 生成 bin/hex
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND arm-none-eabi-objcopy -O binary $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.bin
  COMMAND arm-none-eabi-objcopy -O ihex $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.hex
  COMMENT "Generating bin and hex"
)
