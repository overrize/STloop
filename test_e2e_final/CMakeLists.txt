cmake_minimum_required(VERSION 3.15)
project(stm32_app C CXX ASM)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

# 目标芯片配置（由 chip_config.cmake 注入，或使用默认）
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/chip_config.cmake")
  include(chip_config.cmake)
else()
  set(MCU_DEVICE STM32F411xE)
  set(STARTUP_PATTERN f411)
  set(LINKER_PATTERN F411)
endif()
set(MCU_FAMILY STM32F4xx)

# STM32Cube 路径检测策略：
# 1. 优先使用用户指定的 CUBE_ROOT 或项目内嵌的 cube
# 2. 其次尝试查找系统范围的 STM32Cube（STM32CubeMX 安装位置）
# 3. 最后使用内置的精简 CMSIS（不需要外部 Cube）
set(CUBE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/cube/STM32CubeF4" CACHE PATH "STM32Cube root")

# 检测可用的 Cube/CMSIS 来源
set(USE_EMBEDDED_CMSIS FALSE)

if(EXISTS "${CUBE_ROOT}/Drivers/CMSIS/Device/ST/STM32F4xx/Include/stm32f4xx.h")
  message(STATUS "Using STM32CubeF4 from: ${CUBE_ROOT}")
  set(CMSIS_DEVICE_DIR "${CUBE_ROOT}/Drivers/CMSIS/Device/ST/STM32F4xx")
  set(CMSIS_CORE_DIR "${CUBE_ROOT}/Drivers/CMSIS/Include")
  set(HAL_DRIVER_DIR "${CUBE_ROOT}/Drivers/STM32F4xx_HAL_Driver")
else()
  # 尝试系统范围的 Cube（STM32CubeMX 安装位置）
  if(WIN32)
    file(GLOB SYS_CUBE "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeF4" 
                       "C:/STM32Cube/STM32CubeF4"
                       "$ENV{USERPROFILE}/STM32Cube/STM32CubeF4")
  else()
    file(GLOB SYS_CUBE "/opt/STM32CubeF4" 
                       "$ENV{HOME}/STM32Cube/STM32CubeF4")
  endif()
  
  if(SYS_CUBE)
    list(GET SYS_CUBE 0 SYS_CUBE_PATH)
    if(EXISTS "${SYS_CUBE_PATH}/Drivers/CMSIS/Device/ST/STM32F4xx/Include/stm32f4xx.h")
      message(STATUS "Using system STM32CubeF4 from: ${SYS_CUBE_PATH}")
      set(CUBE_ROOT "${SYS_CUBE_PATH}")
      set(CMSIS_DEVICE_DIR "${CUBE_ROOT}/Drivers/CMSIS/Device/ST/STM32F4xx")
      set(CMSIS_CORE_DIR "${CUBE_ROOT}/Drivers/CMSIS/Include")
      set(HAL_DRIVER_DIR "${CUBE_ROOT}/Drivers/STM32F4xx_HAL_Driver")
    endif()
  endif()
endif()

# 如果没有找到完整的 Cube，使用内置的精简 CMSIS
if(NOT CMSIS_DEVICE_DIR)
  set(EMBEDDED_CMSIS "${CMAKE_CURRENT_SOURCE_DIR}/cmsis_minimal")
  if(EXISTS "${EMBEDDED_CMSIS}/Device/STM32F4xx/Include/stm32f411xe.h")
    message(STATUS "Using embedded minimal CMSIS (no external Cube required)")
    set(USE_EMBEDDED_CMSIS TRUE)
    set(CMSIS_DEVICE_DIR "${EMBEDDED_CMSIS}/Device/STM32F4xx")
    set(CMSIS_CORE_DIR "${EMBEDDED_CMSIS}/Core")
    # 检查是否有内置的 LL 驱动
    if(EXISTS "${EMBEDDED_CMSIS}/Drivers/STM32F4xx_HAL_Driver/Inc/stm32f4xx_ll_gpio.h")
      set(HAL_DRIVER_DIR "${EMBEDDED_CMSIS}/Drivers/STM32F4xx_HAL_Driver")
      message(STATUS "Using embedded LL drivers")
    else()
      message(WARNING "Using minimal CMSIS without HAL/LL library. Some features may be limited.")
    endif()
  else()
    message(FATAL_ERROR "STM32CubeF4 not found and embedded CMSIS not available. "
                        "Please install STM32CubeMX or run 'stloop cube-download'")
  endif()
endif()

# 工具链：按 cube 支持，仅用 arm-none-eabi (GNU)。startup 用 gcc/，linker 用 .ld
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)

set(CMAKE_EXE_LINKER_FLAGS "--specs=nosys.specs -Wl,--gc-sections -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard" CACHE INTERNAL "")

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
  ${MCU_DEVICE}
  HSE_VALUE=8000000
)

# 包含路径
set(INCLUDES
  ${CMSIS_DEVICE_DIR}/Include
  ${CMSIS_CORE_DIR}
)

# 如果有 HAL/LL 库，添加其头文件路径
if(HAL_DRIVER_DIR AND EXISTS "${HAL_DRIVER_DIR}/Inc")
  list(APPEND INCLUDES ${HAL_DRIVER_DIR}/Inc)
endif()

# 项目头文件
list(APPEND INCLUDES ${CMAKE_CURRENT_SOURCE_DIR}/inc)

# 源文件（system/startup 从 CMSIS 引用，兼容不同 Cube/CMSIS 版本路径）
set(CMSIS_DEVICE ${CMSIS_DEVICE_DIR})
file(GLOB SYSTEM_C_CANDIDATES "${CMSIS_DEVICE}/Source/Templates/system_stm32f4xx.c" "${CMSIS_DEVICE}/Source/system_stm32f4xx.c")
if(SYSTEM_C_CANDIDATES)
  list(GET SYSTEM_C_CANDIDATES 0 SYSTEM_C_SRC)
else()
  file(GLOB_RECURSE SYSTEM_C_CANDIDATES "${CMSIS_DEVICE}/**/system_stm32f4xx.c")
  if(SYSTEM_C_CANDIDATES)
    list(GET SYSTEM_C_CANDIDATES 0 SYSTEM_C_SRC)
  else()
    file(GLOB_RECURSE SYSTEM_C_CANDIDATES "${CUBE_ROOT}/Drivers/**/system_stm32f4xx.c")
    if(SYSTEM_C_CANDIDATES)
      list(GET SYSTEM_C_CANDIDATES 0 SYSTEM_C_SRC)
    else()
      # GitHub STM32CubeF4 repo stores these in Projects/
      file(GLOB_RECURSE SYSTEM_C_CANDIDATES "${CUBE_ROOT}/Projects/**/system_stm32f4xx.c")
      if(SYSTEM_C_CANDIDATES)
        list(GET SYSTEM_C_CANDIDATES 0 SYSTEM_C_SRC)
      else()
        message(FATAL_ERROR "system_stm32f4xx.c not found under ${CUBE_ROOT}/Drivers or ${CUBE_ROOT}/Projects")
      endif()
    endif()
  endif()
endif()
# startup：优先工程目录，再查 cube。必须用 gcc/ 下的 GNU 汇编（arm/ 为 Keil 不兼容）
file(GLOB PROJECT_STARTUP_S_LIST "${CMAKE_CURRENT_SOURCE_DIR}/startup_stm32*.s")
if(PROJECT_STARTUP_S_LIST)
  set(STARTUP_S_LIST "${PROJECT_STARTUP_S_LIST}")
  message(STATUS "Using startup from project dir: ${PROJECT_STARTUP_S_LIST}")
else()
  file(GLOB_RECURSE _ALL_STARTUP "${CMSIS_DEVICE}/**/startup_stm32*.s")
  if(NOT _ALL_STARTUP)
    file(GLOB_RECURSE _ALL_STARTUP "${CUBE_ROOT}/Drivers/**/startup_stm32*.s")
  endif()
  if(NOT _ALL_STARTUP)
    # GitHub STM32CubeF4 repo stores these in Projects/
    file(GLOB_RECURSE _ALL_STARTUP "${CUBE_ROOT}/Projects/**/startup_stm32*.s")
  endif()
  # 优先 gcc 目录
  set(STARTUP_S_LIST "")
  foreach(f ${_ALL_STARTUP})
    if(f MATCHES "[\\\\/]gcc[\\\\/]")
      list(APPEND STARTUP_S_LIST "${f}")
    endif()
  endforeach()
  if(NOT STARTUP_S_LIST)
    foreach(f ${_ALL_STARTUP})
      if(NOT f MATCHES "[\\\\/]arm[\\\\/]")
        list(APPEND STARTUP_S_LIST "${f}")
      endif()
    endforeach()
  endif()
  if(NOT STARTUP_S_LIST AND _ALL_STARTUP)
    list(GET _ALL_STARTUP 0 _first_startup)
    if(_first_startup MATCHES "[\\\\/]arm[\\\\/]")
      message(FATAL_ERROR
        "startup 仅来自 arm/（ARM/Keil 汇编），与 arm-none-eabi-gcc 不兼容。"
        "请使用含 gcc/ 的 STM32CubeF4（如 GitHub release）。")
    endif()
  endif()
  if(NOT STARTUP_S_LIST)
    set(STARTUP_S_LIST "${_ALL_STARTUP}")
  endif()
endif()
if(NOT STARTUP_S_LIST)
  message(FATAL_ERROR "No startup_*.s found in project dir or under ${CUBE_ROOT}/Drivers")
endif()
# 按 STARTUP_PATTERN 匹配（如 f405、f411）
set(STARTUP_S_FILE "")
foreach(f ${STARTUP_S_LIST})
  get_filename_component(basename "${f}" NAME)
  if(basename MATCHES "startup_stm32${STARTUP_PATTERN}")
    set(STARTUP_S_FILE "${f}")
    break()
  endif()
endforeach()
if(NOT STARTUP_S_FILE)
  list(GET STARTUP_S_LIST 0 STARTUP_S_FILE)
  message(STATUS "No match for startup_stm32${STARTUP_PATTERN}*, using ${STARTUP_S_FILE}")
endif()
get_filename_component(STARTUP_GCC "${STARTUP_S_FILE}" DIRECTORY)
set(SOURCES
  src/main.c
  ${SYSTEM_C_SRC}
  ${STARTUP_S_FILE}
)

# LL 驱动（如果可用）
if(HAL_DRIVER_DIR AND EXISTS "${HAL_DRIVER_DIR}/Src")
  file(GLOB LL_SOURCES ${HAL_DRIVER_DIR}/Src/stm32f4xx_ll_*.c)
  # 过滤掉不需要的
  list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_usb.*")
  list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_fsmc.*")
  list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_fmc.*")
  list(FILTER LL_SOURCES EXCLUDE REGEX ".*ll_sdmmc.*")
  message(STATUS "Using LL drivers from: ${HAL_DRIVER_DIR}")
else()
  set(LL_SOURCES "")
  message(STATUS "No LL drivers available, using minimal build")
endif()

add_executable(${PROJECT_NAME}.elf ${SOURCES} ${LL_SOURCES})
target_include_directories(${PROJECT_NAME}.elf PRIVATE ${INCLUDES})
# linker 脚本：优先工程目录（与 src 同级），再查 cube
file(GLOB PROJECT_LD_LIST "${CMAKE_CURRENT_SOURCE_DIR}/*.ld")
if(PROJECT_LD_LIST)
  set(LD_LIST "${PROJECT_LD_LIST}")
  message(STATUS "Using linker script from project dir: ${PROJECT_LD_LIST}")
else()
  file(GLOB_RECURSE LD_LIST "${CMSIS_DEVICE}/**/*.ld")
  if(NOT LD_LIST)
    file(GLOB_RECURSE LD_LIST "${CUBE_ROOT}/Drivers/**/*.ld")
  endif()
  if(NOT LD_LIST)
    file(GLOB_RECURSE LD_LIST "${CUBE_ROOT}/Projects/**/*.ld")
  endif()
endif()
if(NOT LD_LIST)
  message(FATAL_ERROR "No linker script .ld in project dir or under ${CUBE_ROOT} (checked CMSIS, Drivers, Projects)")
endif()
set(LINKER_SCRIPT "")
foreach(f ${LD_LIST})
  get_filename_component(basename "${f}" NAME)
  if(basename MATCHES ".*${LINKER_PATTERN}.*FLASH.*")
    set(LINKER_SCRIPT "${f}")
    break()
  endif()
endforeach()
if(NOT LINKER_SCRIPT)
  list(GET LD_LIST 0 LINKER_SCRIPT)
  message(STATUS "No match for *${LINKER_PATTERN}*FLASH*, using ${LINKER_SCRIPT}")
endif()
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
