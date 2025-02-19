from machine import UART, Pin
import time
import re


from esp32api.SensorDataUtil import SensorDataUtil

from esp32api.Main import Main

class SensorResponseParser:
    def __init__(self, sensor_type, baud_rate):
        """
        初始化解析器，指定传感器类型（4系列或7系列）和波特率。
        
        :param sensor_type: 传感器类型（4系列或7系列）
        :param baud_rate: 波特率
        """
        self.sensor_type = sensor_type
        self.baud_rate = baud_rate

    def parse_response(self, hex_data, type_id):
        """
        解析传感器应答的十六进制数据，并根据类型ID返回对应的可读数据。
        
        :param hex_data: 十六进制字符串数据
        :param type_id: 类型ID，决定如何解析数据
        :return: 可读的传感器参数数据
        """ 
        # 先验证和清理十六进制数据
        hex_data = self.clean_and_validate_hex(hex_data)
        
        # 如果数据无效，返回错误信息
        if hex_data is None:
            return "输入的十六进制数据无效"

        # 将十六进制字符串转换为字节数组
        byte_array = SensorDataUtil.hex_string_to_byte_array(hex_data)

        # 选择不同传感器系列的数据解析方法
        if self.sensor_type == 4:
            return self.parse_sensor_data_4(byte_array, type_id)
        elif self.sensor_type == 7:
            return self.parse_sensor_data_7(byte_array, type_id)
        else:
            return "无效的传感器类型"

    def parse_sensor_data_4(self, byte_array, type_id):
        """
        解析4系列传感器的应答数据。
        
        :param byte_array: 字节数组数据
        :param type_id: 类型ID，决定如何解析数据
        :return: 可读的传感器参数数据
        """
        # 将字节数组转回为十六进制字符串
        hex_str = SensorDataUtil.byte_array_to_hex_string(byte_array)
        return SensorDataUtil.substring_data_4(hex_str, type_id)

    def parse_sensor_data_7(self, byte_array, type_id):
        """
        解析7系列传感器的应答数据。
        
        :param byte_array: 字节数组数据
        :param type_id: 类型ID，决定如何解析数据
        :return: 可读的传感器参数数据
        """
        # 将字节数组转回为十六进制字符串
        hex_str = SensorDataUtil.byte_array_to_hex_string(byte_array)
        return SensorDataUtil.substring_data_7(hex_str, type_id)

    def clean_and_validate_hex(self, hex_input):
        """
        清理和验证十六进制输入数据。去除空格、转换为大写并验证合法性。
        
        :param hex_input: 输入的十六进制字符串
        :return: 如果合法则返回格式化后的十六进制字符串，否则返回 None
        """
        # 去除输入中的空格并转换为大写
        hex_input = hex_input.replace(" ", "").upper()
        
        # 检查是否是有效的十六进制字符串
        if not all(c in '0123456789ABCDEF' for c in hex_input):
            print("输入的十六进制数据包含非法字符，请重新输入！")
            return None  # 返回 None，表示输入无效
        
        return hex_input