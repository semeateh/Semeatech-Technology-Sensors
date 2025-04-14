# 项目使用说明

## 项目简介

本项目包括一个 `Main` 类和多个传感器数据处理模块，主要功能包括：
- 读取传感器数据，进行解析和处理
- 处理设备的校零和标定
- 与支持 UART 通信的传感器进行数据交互

本项目主要适用于环境监测、气体检测等应用场景。

## 功能概述

### 1. `Main` 类主要实现的功能：
- **UART 数据处理**: 通过串口（UART）接收和发送数据，解析不同类型的传感器数据
- **传感器数据解析**: 结合 `ReturnDataSubstring` 类，将传感器数据解析成易于理解的格式
- **校零与标定**: 支持传感器的校零和标定操作

### 2. `ReturnDataSubstring` 类
- **气体类型映射**: 支持从 `GAS_TYPE_MAPPING_4` 和 `GAS_TYPE_MAPPING_7` 中获取对应的气体名称
- **数据提取与处理**: 通过 `substring_data_4` 和 `substring_data_7` 方法解析传感器返回的数据
- **校零与标定信息**: 处理模块的校零、标定状态

### 3. `FlagCode` 类
- **定义与传感器通信的指令码**，用于不同型号的传感器，包括读取数据、校零、标定等指令。

### 4. `DataChangeUtil` 类
- **数据转换工具**，支持十六进制字符串和字节数组的转换，十六进制到十进制转换等。

### 5. `FactoryUtil` 类
- **根据传感器类型 ID 选择合适的指令进行通信**，支持不同波特率的传感器。

## 安装要求

- **Python 3.x**
- **MicroPython 库**（适用于嵌入式设备）
- **支持 UART 通信的传感器**
- 依赖：`ReturnDataSubstring`, `DataChangeUtil`, `FlagCode` 类

## 使用方法

### 1. 解析传感器数据
```python
response = uart.read()  # 从传感器读取数据
hex_string = ' '.join(f'{byte:02x}' for byte in response)  # 转换为十六进制字符串
rm_space = DataChangeUtil.clean_string(hex_string)  # 清除空格

# 根据数据开头判断解析方式
if hex_string[:2] == 'AA':
    data = ReturnDataSubstring.substring_data_4(rm_space, sensor_flag)
elif hex_string[:2] == '3A':
    data = ReturnDataSubstring.substring_data_7(rm_space, sensor_flag)

print(f"Parsed Data: {data}")
```

### 2. 发送数据
```python
# 将处理后的数据发送到设备或其他系统
sensor_data = {"data": data}
json_data = json.dumps(sensor_data).encode('utf-8')
# 使用适当的通信方式发送数据
```

### 3. 处理 UART 发送与接收
```python
# 根据指令码向传感器发送命令
sensor_flag = FlagCode.F_SENSOR_TYPE1  # 获取传感器类型
code = FactoryUtil.by_type_get_return(sensor_flag, BAUDRATE)
uart.write(code)  # 向传感器发送命令

# 读取传感器返回的数据
response = uart.read()
```

### 4. 处理错误
```python
try:
    # 数据处理代码...
except Exception as e:
    print(f"Error: {e}")
    # 处理错误或重试机制
```

## 主要类说明

### `FlagCode` 类
```python
sensor_info_cmd = FlagCode.F_SENSOR_TYPE1  # 获取传感器信息
```
- `F_SENSOR_TYPE1`: 读取传感器类型
- `F_SENSOR_NUM2`: 读取浓度数据
- `F_SENSOR_MODULE_ZERO3`: 校零
- `F_SENSOR_MODULE_CALIBRATION4`: 标定

### `ReturnDataSubstring` 类
```python
gas_type = ReturnDataSubstring.switch_type_4(2)  # 获取气体类型
print(gas_type)  # 输出: "监测气体:CO"
```

### `DataChangeUtil` 类
```python
hex_str = "AA 0F 01 C5 80 EE"
byte_array = DataChangeUtil.hex_string_to_byte_array(hex_str)
print(byte_array)  # 输出: bytearray([170, 15, 1, 197, 128, 238])
```

### `FactoryUtil` 类
```python
type_id = 1
baud_rate = 115200
command = FactoryUtil.by_type_get_return(type_id, baud_rate)
print(command)  # 输出对应的字节数组
```

## 常见问题

1. **如何选择正确的 `type_id`？**
   - `1`：获取气体类型
   - `2`：获取浓度数据
   - `3-4`：查询校零和标定状态

2. **如何确保传感器数据正确解析？**
   - 确保从传感器读取的数据格式正确，`AA` 开头使用 `substring_data_4`，`3A` 开头使用 `substring_data_7`。

3. **如何处理 UART 通信问题？**
   - 确保 UART 配置正确（波特率、数据位、校验位等）。
   - 传感器和设备连接是否正常。

4. **如何处理传感器错误或异常？**
   - 根据错误信息调整通信协议或检查设备状态。

## 许可证

本项目使用 MIT 许可证，详情请见 `LICENSE` 文件。

---

这样改写后，主要集中在传感器数据处理、指令码解析和校零标定等功能。如果有其他需要调整的地方，随时告诉我！

## 许可证

本项目使用 MIT 许可证，详情请见 `LICENSE` 文件。


