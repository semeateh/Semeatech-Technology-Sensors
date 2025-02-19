from machine import UART, Pin
import time
import re

from esp32api.SensorResponseParser import SensorResponseParser
from esp32api.SensorDataUtil import SensorDataUtil
from esp32api.FactoryUtil import FactoryUtil
from esp32api.Main import Main



class UARTUtil:
    """串口通信工具类，用于发送和接收数据"""
    def __init__(self, uart_id, tx_pin, rx_pin, baudrate=9600):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))

    def input_hex(self, hex_input):
        """发送十六进制数据"""
        print(f"发送的字节数据: {hex_input}")
        byte_data = self.hex_string_to_byte_array(hex_input)  # 转换为字节数组
        self.uart.write(byte_data)  # 发送数据

    def read_uart_data(self, type_id, series):
        """读取并显示串口数据"""
        if self.uart.any():  # 检查是否有可读数据
            received_data = self.uart.read()  # 读取数据
            hex_string = self.byte_array_to_hex_string(received_data)  # 转换为十六进制字符串
            print(f"接收到的数据的十六进制表示: {hex_string}")  # 打印接收的数据

            # 根据传感器返回的数据类型，调用合适的解析方法
            sensor_data = None
            if series == 4:
                sensor_data = self.substring_data_4(hex_string, type_id)
            elif series == 7:
                sensor_data = self.substring_data_7(hex_string, type_id)

            return sensor_data
        else:
            print("没有接收到数据。")
            return None

    @staticmethod
    def hex_string_to_byte_array(s):
        s = UARTUtil.clean_string(s)
        if s:
            try:
                if len(s) % 2 != 0:
                    s += "0"
                result = bytearray()
                for i in range(0, len(s), 2):
                    hex_pair = s[i:i + 2]
                    result.append(int(hex_pair, 16))
                return result
            except ValueError as e:
                print(f"Error: {e}")
        return bytearray()

    @staticmethod
    def clean_string(s):
        return re.sub(r'[^0-9A-Fa-f]', '', s)

    @staticmethod
    def byte_array_to_hex_string(byte_array):
        return ''.join(f'{b:02X}' for b in byte_array)

    @staticmethod
    def substring_data_4(old_data, type_id):
        """根据指令类型解析4系列数据并格式化为用户友好的信息"""
        type_ = ""
        new_data = ""
        if type_id == 1:
            new_data = old_data[6:8]
            type_ = f"传感器类型: {SensorDataUtil.switch_type_4(SensorDataUtil.hex_to_decimal(new_data))}"
        elif type_id == 2:
            new_data = old_data[8:14]
            type_ = f"气体浓度: {SensorDataUtil.hex_to_decimal(new_data)} ppm"
        elif type_id == 3:
            type_ = "模块校零失败"
            if SensorDataUtil.clean_string(SensorDataUtil.FlagCode.F_SENSOR_MODULE_ZERO3_TRUE) == old_data:
                type_ = "模块校零成功"
        elif type_id == 4:
            type_ = "模块标定失败"
            if SensorDataUtil.clean_string(SensorDataUtil.FlagCode.F_SENSOR_MODULE_CALIBRATION4_TRUE) == old_data:
                type_ = "模块标定成功"
        elif type_id == 5:
            type_ = "地址修改失败"
            if SensorDataUtil.clean_string(SensorDataUtil.FlagCode.F_SENSOR_UPDATE_ADDRESS5_TRUE) == old_data:
                type_ = "地址修改成功"
        elif type_id == 6:
            type_ = "修改模块标气浓度失败"
            if SensorDataUtil.clean_string(SensorDataUtil.FlagCode.F_SENSOR_UPDATE_CONCENTRATION6_TRUE) == old_data:
                type_ = "修改模块标气浓度成功"
        return type_

    @staticmethod
    def substring_data_7(old_data, type_id):
        """根据指令类型解析7系列数据并格式化为用户友好的信息"""
        type_ = ""
        new_data = ""
        if type_id == 1:
            new_data = old_data[6:8]
            type_ = f"传感器类型: {SensorDataUtil.switch_type_7(SensorDataUtil.hex_to_decimal(new_data))}"
        elif type_id == 2:
            new_data = old_data[12:20]
            type_ = f"气体浓度: {SensorDataUtil.hex_to_decimal(new_data)} μg/m³"
        elif type_id == 3:
            new_data = old_data[12:20]
            type_ = f"气体浓度: {SensorDataUtil.hex_to_decimal(new_data)} ppb"
        elif type_id == 4:
            new_data = old_data[12:16]
            type_ = f"监测温度: {SensorDataUtil.hex_to_decimal(new_data) / 100}°C"
        elif type_id == 5:
            new_data = old_data[12:16]
            type_ = f"监测湿度: {SensorDataUtil.hex_to_decimal(new_data) / 100}%RH"
        elif type_id == 6:
            data1 = SensorDataUtil.hex_to_decimal(old_data[12:20])
            data2 = SensorDataUtil.hex_to_decimal(old_data[20:28])
            data3 = SensorDataUtil.hex_to_decimal(old_data[28:32]) / 100
            data4 = SensorDataUtil.hex_to_decimal(old_data[32:36]) / 100
            type_ = f"浓度值: {data1} μg/m³, 浓度值: {data2} ppb, 温度: {data3}°C, 湿度: {data4}%RH"
        elif type_id == 8:
            new_data = old_data[12:16]
            type_ = f"零点标定返回数值: {SensorDataUtil.hex_to_decimal(new_data)}"
        elif type_id == 9:
            flag = "标定成功"
            substring = old_data[6:8]
            if substring == "01":
                flag = "标定中"
            elif substring == "02":
                flag = "标定失败"
            type_ = f"标定结果: {flag}"
        return type_

    @staticmethod
    def switch_type_4(type_id):
        return SensorDataUtil.GAS_TYPE_MAPPING_4.get(type_id)

    @staticmethod
    def switch_type_7(type_id):
        return SensorDataUtil.GAS_TYPE_MAPPING_7.get(type_id)

    @staticmethod
    def hex_to_decimal(hex_str):
        return int(hex_str, 16)

def test_sensor_data():
    """测试传感器数据解析功能"""
    print("欢迎使用传感器数据解析工具！")
    print("请输入指令号来读取传感器数据：")

    # 显示可用的指令列表
    print("\n可用的指令如下：")
    print("4系列指令：")
    print("1: 读取传感器类型")
    print("2: 读取气体浓度")
    print("3: 零点标定")
    print("4: 模块标定")
    print("5: 地址修改")
    print("6: 修改模块标气浓度")

    print("\n7系列指令：")
    print("1: 读取传感器类型")
    print("2: 读取气体浓度(μg/m³)")
    print("3: 读取气体浓度(ppb)")
    print("4: 读取监测温度")
    print("5: 读取监测湿度")
    print("6: 读取多项传感器参数")
    print("7: 校验错误应")
    print("8: 零点标定返回数值")
    print("9: 标定结果")

    try:
        type_id = int(input("\n请输入指令类型（1 - 9）: "))
    except ValueError:
        print("无效输入，请输入一个有效的指令号！")
        return

    # 获取波特率类型
    baud_rate = input("\n请输入波特率（9600 或 115200）: ").strip()
    try:
        baud_rate = int(baud_rate)
        if baud_rate not in [9600, 115200]:
            print("无效的波特率，请选择 9600 或 115200！")
            return
    except ValueError:
        print("无效的波特率输入，请输入一个有效的波特率！")
        return

    # 选择 UART 配置
    uart_util = UARTUtil(uart_id=2, tx_pin=17, rx_pin=16, baudrate=baud_rate)

    # 选择系列指令
    if baud_rate == 9600:
        series = 4
        flag_code = get_flag_code_4_series(type_id)
    elif baud_rate == 115200:
        series = 7
        flag_code = get_flag_code_7_series(type_id)
    else:
        print("不支持的波特率！")
        return

    if not flag_code:
        print("无效的指令类型！")
        return

    print(f"\n发送指令: {flag_code}")
    uart_util.input_hex(flag_code)  # 发送指令（转化为16进制）
    time.sleep(1)  # 等待一秒以确保数据发送完成
    sensor_data = uart_util.read_uart_data(type_id, series)  # 读取并解析接收到的数据

    if sensor_data is not None:
        print(f"解析后的传感器数据: {sensor_data}")
    else:
        print("未能解析传感器数据")

# 获取4系列指令
def get_flag_code_4_series(type_id):
    flag_code_map_4 = {
        1: "AA 0F 01 C5 80 EE",
        2: "AA 01 01 C1 E0 EE",
        3: "AA 02 01 C1 10 EE",
        4: "AA 03 01 C0 80 EE",
        5: "AA 04 02 82 B1 EE",
        6: "AA 05 01 01 F4 51 3F EE",
    }
    return flag_code_map_4.get(type_id)

# 获取7系列指令
def get_flag_code_7_series(type_id):
    flag_code_map_7 = {
        1: "3A 10 01 00 00 01 00 00 82 B0",
        2: "3A 10 03 00 00 02 00 00 73 52",
        3: "3A 10 03 00 02 02 00 00 72 EA",
        4: "3A 10 03 00 04 01 00 00 82 62",
        5: "3A 10 03 00 05 01 00 00 83 9E",
        6: "3A 10 03 00 00 06 00 00 32 93",
        7: "3A 10 08 00 0A F9",
        8: "3A 10 07 00 00 01 00 00 82 D6",
        9: "3A 10 09 00 00 01 00 0A 03 FF",
    }
    return flag_code_map_7.get(type_id)

# 运行测试脚本
if __name__ == "__main__":
    test_sensor_data()



