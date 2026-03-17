cmake_minimum_required(VERSION 3.20.0)

# 模拟 Zephyr 项目 - 使用 cmsis_minimal 作为底层 HAL
# 当真正的 Zephyr 不可用时，此配置使用本地 cmsis_minimal 构建

project(stloop_zephyr_compat)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

# 编译器设置
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)

# 阻止 CMake 添加平台特定的链接标志
set(CMAKE_C_LINK_EXECUTABLE "<CMAKE_C_COMPILER> <FLAGS> <CMAKE_C_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>")
set(CMAKE_CXX_LINK_EXECUTABLE "<CMAKE_CXX_COMPILER> <FLAGS> <CMAKE_CXX_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>")

# 清除默认的 Windows 库
set(CMAKE_C_STANDARD_LIBRARIES "")
set(CMAKE_CXX_STANDARD_LIBRARIES "")

# 目标芯片
set(MCU_DEVICE STM32F411xE)
set(MCU_FAMILY STM32F4xx)

# 添加编译选项
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
  ${MCU_DEVICE}
  HSE_VALUE=8000000
)

# CMSIS 路径 - 使用本地 cmsis_minimal
set(CMSIS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../generated/cmsis_minimal)

# 包含路径
include_directories(
  ${CMSIS_ROOT}/Device/STM32F4xx/Include
  ${CMSIS_ROOT}/Core
  ${CMSIS_ROOT}/Drivers/STM32F4xx_HAL_Driver/Inc
  ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# 源文件
set(SOURCES
  src/main.c
  ${CMSIS_ROOT}/Device/STM32F4xx/Source/Templates/system_stm32f4xx.c
  ${CMSIS_ROOT}/Device/STM32F4xx/Source/Templates/gcc/startup_stm32f411xe.s
)

# LL 驱动（排除依赖 HAL 的）
file(GLOB LL_SOURCES ${CMSIS_ROOT}/Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_ll_*.c)
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_usb.*")
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_fsmc.*")
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_fmc.*")
list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_sdmmc.*")

# 创建可执行文件
add_executable(${PROJECT_NAME}.elf ${SOURCES} ${LL_SOURCES})

# 链接器选项
target_link_options(${PROJECT_NAME}.elf PRIVATE
  -mcpu=cortex-m4
  -mthumb
  -mfpu=fpv4-sp-d16
  -mfloat-abi=hard
  -T${CMAKE_CURRENT_SOURCE_DIR}/STM32F411RETX_FLASH.ld
  -Wl,--gc-sections
  -Wl,-Map=${PROJECT_NAME}.map
  --specs=nosys.specs
)

# 生成 bin/hex
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND arm-none-eabi-objcopy -O binary $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.bin
  COMMAND arm-none-eabi-objcopy -O ihex $<TARGET_FILE:${PROJECT_NAME}.elf> ${PROJECT_NAME}.hex
  COMMENT "Generating binary and hex files"
)
