# Sematech Sensors SDK 集成指南

## 1. 文档定位

本文档是 V3 版本下的 SDK 开发文档，面向需要将 Sematech 传感器接入自己 MicroPython 项目的开发者。

如果你想了解整个仓库的三种使用方式，请先看：

- [`README_NEW.md`]

如果你已经确定要把本项目当作工具包集成进自己的工程，请继续阅读本文档。

## 2. V3 的 SDK 思路

V3 不是推翻旧接口，而是在原有 `communication` 静态接口的基础上，新增了更适合二次开发的 `SensorClient`。

这样带来的结果是：

- 老项目可以继续使用 `communication.xxx()`
- 新项目可以使用 `SensorClient`
- 客户可以自己决定使用哪个 UART
- 客户可以把自己初始化好的 UART 对象直接传入 SDK

## 3. 推荐接入方式

### 方式 A：客户自己创建 UART 对象

这是最推荐的方式，适合客户已经有自己的主程序和串口初始化逻辑。

```python
from machine import UART, Pin
from esp32api import SensorClient

uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))
client = SensorClient(uart=uart)

print(client.getInfo())
print(client.getReading())
```

### 方式 B：把串口参数直接交给 SDK

适合快速接入和简单脚本。

```python
from esp32api import SensorClient

client = SensorClient(port=2, baudrate=9600, tx=17, rx=16)

print(client.getInfo())
print(client.getReading())
```

## 4. 初始化参数说明

`SensorClient(...)` 支持以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `uart` | 外部已创建好的 UART 对象 | `UART(2, baudrate=9600, ...)` |
| `port` | 串口号 | `1` / `2` |
| `baudrate` | 波特率 | `9600` / `115200` |
| `tx` | TX 引脚 | `17` 或 `Pin(17)` |
| `rx` | RX 引脚 | `16` 或 `Pin(16)` |
| `timeout` | 串口超时时间，单位毫秒 | `300` |
| `addr_4` | 4 系列默认地址 | `0x01` |
| `id_7` | 7 系列默认设备 ID | `0x10` |

说明：

- 如果传入 `uart`，SDK 会直接复用这个对象
- 如果没有传入 `uart`，则由 SDK 内部根据 `port / baudrate / tx / rx` 创建 UART

## 5. 主要接口

`SensorClient` 当前主要提供以下接口：

- `getInfo()`
- `getReading()`
- `getSpanValue()`
- `zeroCal()`
- `spanCal(ppm)`
- `getTemp()`
- `getHumi()`
- `set_uart(...)`
- `set_address(...)`
- `get_config()`

## 6. 返回值格式

核心接口统一返回 `dict`，常见字段包括：

- `ok`
- `series`
- `raw`
- `info`
- `parsed`
- `value`
- `result`
- `note`
- `note2`

建议客户代码先判断 `ok` 字段，再处理业务逻辑。

示例：

```python
result = client.getReading()
if result.get("ok"):
    print("读取成功：", result)
else:
    print("读取失败：", result)
```

## 7. 接线建议

典型接线如下：

| 传感器引脚 | ESP32 GPIO |
|------------|------------|
| VCC | 3.3V |
| GND | GND |
| TX | GPIO16（接开发板 RX） |
| RX | GPIO17（接开发板 TX） |

注意：

- `TX` 和 `RX` 要交叉连接
- 开发板与传感器必须共地
- 如果传感器不是 3.3V 电平，请按硬件说明处理

## 8. 兼容旧接口

为了兼容旧项目，原来的 `communication` 写法仍然保留：

```python
from esp32api.communication import communication

communication.init_uart(port=2, baudrate=9600, tx=17, rx=16)
print(communication.getInfo())
print(communication.getReading())
```

但是对于新项目，推荐优先使用：

```python
from esp32api import SensorClient
```

## 9. 推荐的客户集成方式

如果客户已经有自己的主程序，推荐按下面的思路集成：

1. 在客户自己的工程里初始化 UART
2. 把 UART 对象传给 `SensorClient`
3. 直接调用 `getInfo()`、`getReading()` 等接口

这样做的好处是：

- 客户可以完全控制自己项目里使用哪个 UART
- 不需要修改我们底层协议实现
- 更容易和客户自己的任务调度、配置系统和主程序整合

## 10. 当前相关文件

和 SDK 集成直接相关的文件有：

- [`esp32api/communication.py`]
- [`esp32api/client.py`]
- [`esp32api/__init__.py`]
- [`examples/sdk_with_uart_object.py`]
- [`examples/sdk_with_params.py`]
- [`examples/legacy_compat.py`]

## 11. 常见问题

### 1. 客户自己的工程里可以用 UART1、UART2 或其他串口吗

可以。只要目标开发板和固件支持，客户就可以在自己的工程里这样写：

```python
uart = UART(1, baudrate=9600, tx=..., rx=...)
```

或者：

```python
uart = UART(2, baudrate=9600, tx=..., rx=...)
```

然后把这个 UART 传给 `SensorClient`。

### 2. 如果不知道模块是 4 系列还是 7 系列怎么办

可以直接调用：

```python
print(client.getInfo())
```

项目会优先尝试识别 7 系列，再尝试 4 系列。

### 3. 接上传感器没有返回怎么办

建议按顺序检查：

1. 传感器是否上电
2. `TX` / `RX` 是否接反
3. 波特率是否匹配
4. 当前是否选对 UART
5. 传感器是否确实使用 UART 协议

## 12. 与工程模式和客户模式的关系

当前 [`esp32api/test.py`] 的菜单交互保持原样，但底层已经切换到 `SensorClient`。

当前 [`customer_mode_v2.py`] 的客户交互流程也保持原样，但底层同样已经切换到 `SensorClient`。

这意味着：

- 内部联调仍然方便
- 客户模式和工程模式共用了同一套 SDK 底层
- 同时也能覆盖 SDK 这条新路径

## 13. 总结

V3 的核心目标不是替换掉旧接口，而是：

- 让旧项目继续稳定运行
- 让新项目更容易集成
- 让客户能自己控制 UART 初始化方式

如果你需要项目全局说明，请看：

- [`README_NEW.md`]
