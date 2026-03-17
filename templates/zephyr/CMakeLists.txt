cmake_minimum_required(VERSION 3.20.0)

# Zephyr 项目配置
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(stloop_zephyr_app)

target_sources(app PRIVATE src/main.c)
