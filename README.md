# Semeatech Technology Sensors

这是一个基于 MicroPython 的 UART 气体传感器接入项目，用于在 ESP32 / ESP8266 上读取 Sematech 4 系列、7 系列传感器数据，并支持校零、跨度标定、温湿度读取等功能。

当前对外版本为 **V3**。V3 的重点是把项目整理成三种清晰的使用方式：

- 客户模式：设备上电后自动进入中文交互流程
- 工程模式：研发人员通过菜单脚本调试传感器
- SDK 模式：客户开发者在自己的 MicroPython 项目中导入 `esp32api`

详细 SDK 接口说明见 [SDK_GUIDE.md](./SDK_GUIDE.md)。

## 项目能力

- 通过 UART 与传感器通信
- 自动识别 4 系列 / 7 系列传感器
- 读取模块信息、实时浓度、标气浓度
- 执行零点标定、跨度标定
- 读取 7 系列温度、湿度数据
- 支持客户自己创建 `UART(...)` 并注入 SDK
- 保留旧版 `communication.xxx()` 调用方式

## 默认硬件约定

当前项目默认约定如下：

| 串口 | 传感器系列 | 默认波特率 |
|------|------------|------------|
| `UART(1)` | 4 系列 | `9600` |
| `UART(2)` | 7 系列 | `115200` |

如果客户硬件设计不同，可以在 SDK 中显式传入自己的 `UART(...)` 或 `port / baudrate / tx / rx` 参数。

## 仓库结构

```text
.
├─ main.py                     # 客户模式自动启动入口
├─ customer_mode_v2.py         # 客户模式 V2
├─ CUSTOMER_MODE_V2.md         # 客户模式说明
├─ SDK_GUIDE.md                # SDK 接口集成文档
├─ examples/                   # SDK 示例
│  ├─ sdk_with_uart_object.py
│  ├─ sdk_with_params.py
│  └─ legacy_compat.py
├─ esp32api/
│  ├─ communication.py         # 协议层与旧接口兼容层
│  ├─ client.py                # V3 SDK 客户端 SensorClient
│  ├─ test.py                  # 工程模式测试入口
│  ├─ Main.py                  # 旧版主流程 / 扩展示例
│  └─ __init__.py              # 包导出入口
├─ boot.py
└─ lib/
   └─ ntptime.mpy
```

## 三种使用方式

### 客户模式

适合交付给现场用户直接操作。

上传文件：

```text
main.py
customer_mode_v2.py
esp32api/
```

运行方式：

- ESP32 / ESP8266 上电后会自动执行根目录 `main.py`
- `main.py` 会进入 `customer_mode_v2.py`
- 程序会自动检测设备、保存配置并进入状态首页

客户模式提供：

- 状态首页
- 连续检测
- 设备详情
- 校零向导
- 标定向导
- 连接设置

### 工程模式

适合研发、生产测试和协议联调。

上传文件：

```text
esp32api/communication.py
esp32api/client.py
esp32api/test.py
esp32api/__init__.py
```

运行：

```python
import esp32api.test
esp32api.test.main()
```

或在 Thonny 中直接运行 `esp32api/test.py`。

工程模式会让你手动输入 UART 参数，然后通过菜单执行：

- `getInfo()`
- `getReading()`
- `getSpanValue()`
- `zeroCal()`
- `spanCal(ppm)`
- `getTemp()`
- `getHumi()`

### SDK 模式

适合客户把本项目集成进自己的 MicroPython 工程。

上传文件：

```text
esp32api/communication.py
esp32api/client.py
esp32api/__init__.py
```

推荐写法：客户自己创建 UART 后传入 SDK。

```python
from machine import UART, Pin
from esp32api import SensorClient

uart = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))
client = SensorClient(uart=uart)

print(client.getInfo())
print(client.getReading())
```

简单写法：直接把串口参数交给 SDK。

```python
from esp32api import SensorClient

client = SensorClient(port=2, tx=17, rx=16)

print(client.getInfo())
print(client.getReading())
```

如果只传 `port`，SDK 会按默认硬件约定自动补齐波特率：

- `port=1` 默认 `9600`
- `port=2` 默认 `115200`

完整接口说明见 [SDK_GUIDE.md](./SDK_GUIDE.md)。

## 接线说明

典型 UART 接线如下：

| 传感器引脚 | ESP32 GPIO |
|------------|------------|
| `VCC` | `3.3V` 或传感器要求的电源 |
| `GND` | `GND` |
| `TX` | `GPIO16`，接开发板 RX |
| `RX` | `GPIO17`，接开发板 TX |

注意：

- `TX` 和 `RX` 要交叉连接
- 开发板与传感器必须共地
- 如果传感器是 5V TTL 电平，需要按硬件要求做电平转换
- 如果传感器是 RS485，不可直接接 ESP32 UART，需要 RS485 转 TTL 模块

## 主要接口

| 接口 | 说明 |
|------|------|
| `getInfo()` | 读取模块信息并识别气体类型 |
| `getReading()` | 读取实时浓度数据 |
| `getSpanValue()` | 读取标气浓度 / 量程信息 |
| `zeroCal()` | 零点标定 |
| `spanCal(ppm)` | 跨度标定 |
| `getTemp()` | 读取温度，仅 7 系列 |
| `getHumi()` | 读取湿度，仅 7 系列 |

详细参数、返回值和示例见 [SDK_GUIDE.md](./SDK_GUIDE.md)。

## 旧接口兼容

旧项目仍可继续使用：

```python
from esp32api.communication import communication

communication.init_uart(port=2, tx=17, rx=16)

print(communication.getInfo())
print(communication.getReading())
```

新项目建议优先使用：

```python
from esp32api import SensorClient
```

## 常见问题

### 接上传感器没有返回

建议依次检查：

1. 传感器是否上电
2. `TX` 和 `RX` 是否接反
3. 开发板与传感器是否共地
4. 波特率是否匹配
5. 是否选对 UART 口
6. 传感器是否确实是 UART 协议

### 如何判断 4 系列还是 7 系列

调用：

```python
print(client.getInfo())
```

默认硬件约定是：

- 4 系列使用 `UART(1) + 9600`
- 7 系列使用 `UART(2) + 115200`

### 校零和标定可以随便执行吗

不建议。`zeroCal()` 和 `spanCal(ppm)` 会改变传感器校准状态：

- `zeroCal()` 应在洁净空气环境下执行
- `spanCal(ppm)` 应在标准气体环境下执行
- 现场不满足条件时不要执行标定类操作

## 开发状态

当前代码层面已完成：

- SDK 入口 `SensorClient`
- 客户模式和工程模式底层统一到 `SensorClient`
- 默认串口 / 系列 / 波特率规则统一
- 示例和文档统一到 V3 口径

正式对外交付前，仍建议做一次真实硬件联调：

- 4 系列：`UART(1) + 9600`
- 7 系列：`UART(2) + 115200`

## License

本项目使用 MIT License，详见 [LICENSE](./LICENSE)。
