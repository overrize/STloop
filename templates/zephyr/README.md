# Zephyr RTOS Template

This is a Zephyr RTOS project template for STLoop.

## Features

- Modern RTOS with built-in HAL
- Hardware abstraction via Device Tree
- Multi-threading support
- Rich ecosystem of drivers
- Cross-platform (STM32, nRF, ESP32, etc.)

## Prerequisites

1. Install Zephyr SDK:
   ```bash
   # Ubuntu/Debian
   wget https://github.com/zephyrproject-rtos/sdk/releases/download/v0.16.5/zephyr-sdk-0.16.5_linux-x86_64.tar.xz
   tar xvf zephyr-sdk-0.16.5_linux-x86_64.tar.xz
   ./zephyr-sdk-0.16.5/setup.sh

   # Windows (使用 chocolatey)
   choco install zephyr-sdk
   ```

2. Install west tool:
   ```bash
   pip install west
   ```

3. Get Zephyr source:
   ```bash
   cd ~
   west init zephyrproject
   cd zephyrproject
   west update
   ```

## Building

### Method 1: Using west (recommended)

```bash
cd <project_directory>
west build -p auto -b nucleo_f411re .
```

### Method 2: Using provided script

```bash
cd <project_directory>
./build.sh
```

### Method 3: Using build_zephyr.py

```bash
python build_zephyr.py <project_directory> nucleo_f411re
```

## Supported Boards

- `nucleo_f411re` - STM32F411RE Nucleo (default)
- `nucleo_f401re` - STM32F401RE Nucleo
- `nucleo_f446re` - STM32F446RE Nucleo
- `stm32f4_disco` - STM32F4 Discovery

## Project Structure

```
.
├── CMakeLists.txt          # Zephyr CMake configuration
├── prj.conf               # Project configuration
├── build.sh               # Unix build script
├── build_zephyr.py        # Python build script
├── src/
│   └── main.c            # Application code
└── README.md
```

## Advantages over STM32Cube

1. **Modern Architecture**: Clean, consistent APIs
2. **Device Tree**: Hardware configuration in declarative format
3. **Multi-platform**: Same code works on different MCU families
4. **Active Community**: Large ecosystem and support
5. **Security**: Built-in security features
6. **Connectivity**: Native support for Bluetooth, WiFi, etc.

## Customization

Edit `prj.conf` to enable features:

```
# Enable Bluetooth
CONFIG_BT=y

# Enable sensors
CONFIG_SENSOR=y

# Enable logging
CONFIG_LOG=y
```

## Flashing

```bash
west flash
```

## Debugging

```bash
west debug
```
