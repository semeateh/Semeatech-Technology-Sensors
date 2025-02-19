# esp32api/FactoryUtil.py
from machine import UART, Pin
import time
import re

from esp32api.SensorResponseParser import SensorResponseParser
from esp32api.SensorDataUtil import SensorDataUtil

from esp32api.Main import Main


class FactoryUtil:
    @staticmethod
    def get_sensor_response_by_flag(flag_code):
        """
        根据用户输入的 FlagCode 类指令返回传感器的可读数据。
        
        :param flag_code: FlagCode 类中的指令
        :return: 可读的传感器参数数据
        """
        # 映射FlagCode到传感器类型（4系列或7系列）和波特率
        sensor_type = None
        baud_rate = None
        type_id = None

        # 判断是否属于4系列指令
        if flag_code in SensorDataUtil.FlagCode.__dict__.values():
            if flag_code.startswith("AA"):
                sensor_type = 4  # 4系列
                baud_rate = 9600  # 默认波特率9600
            elif flag_code.startswith("3A"):
                sensor_type = 7  # 7系列
                baud_rate = 115200  # 默认波特率115200
            else:
                return "无效的FlagCode指令"

        # 获取相应的消息并解析
        message = FactoryUtil.by_type_get_return(flag_code, baud_rate)
        
        # 创建解析器实例
        parser = SensorResponseParser(sensor_type, baud_rate)
        
        # 通过传感器类型、波特率、和指令类型解析传感器数据
        # type_id需要根据具体指令来调整，这里暂时假设为1
        return parser.parse_response(SensorDataUtil.byte_array_to_hex_string(message), 1)

    @staticmethod
    def by_type_get_return(flag_code, baud_rate):
        """
        根据 FlagCode 和波特率获取相应的命令。
        
        :param flag_code: 指令
        :param baud_rate: 波特率
        :return: 对应的传感器命令
        """
        # 通过波特率和 flag_code 获取对应的命令
        command_mapping = {
            9600: {
                SensorDataUtil.FlagCode.F_SENSOR_TYPE1: SensorDataUtil.FlagCode.F_SENSOR_TYPE1,
                SensorDataUtil.FlagCode.F_SENSOR_NUM2: SensorDataUtil.FlagCode.F_SENSOR_NUM2,
                SensorDataUtil.FlagCode.F_SENSOR_MODULE_ZERO3: SensorDataUtil.FlagCode.F_SENSOR_MODULE_ZERO3,
                SensorDataUtil.FlagCode.F_SENSOR_MODULE_CALIBRATION4: SensorDataUtil.FlagCode.F_SENSOR_MODULE_CALIBRATION4,
                SensorDataUtil.FlagCode.F_SENSOR_UPDATE_ADDRESS5: SensorDataUtil.FlagCode.F_SENSOR_UPDATE_ADDRESS5,
                SensorDataUtil.FlagCode.F_SENSOR_UPDATE_CONCENTRATION6: SensorDataUtil.FlagCode.F_SENSOR_UPDATE_CONCENTRATION6,
            },
            115200: {
                SensorDataUtil.FlagCode.S_SENSOR_TYPE1: SensorDataUtil.FlagCode.S_SENSOR_TYPE1,
                SensorDataUtil.FlagCode.S_SENSOR_NUM2: SensorDataUtil.FlagCode.S_SENSOR_NUM2,
                SensorDataUtil.FlagCode.S_SENSOR_NUM3: SensorDataUtil.FlagCode.S_SENSOR_NUM3,
                SensorDataUtil.FlagCode.S_SENSOR_TEMPERATURE4: SensorDataUtil.FlagCode.S_SENSOR_TEMPERATURE4,
                SensorDataUtil.FlagCode.S_SENSOR_HUMIDITY5: SensorDataUtil.FlagCode.S_SENSOR_HUMIDITY5,
                SensorDataUtil.FlagCode.S_SENSOR_PARAMS6: SensorDataUtil.FlagCode.S_SENSOR_PARAMS6,
                SensorDataUtil.FlagCode.S_SENSOR_CHECK7: SensorDataUtil.FlagCode.S_SENSOR_CHECK7,
                SensorDataUtil.FlagCode.S_SENSOR_ZERO_CALIBRATION8: SensorDataUtil.FlagCode.S_SENSOR_ZERO_CALIBRATION8,
                SensorDataUtil.FlagCode.S_SENSOR_SENSITIVITY_CALIBRATION9: SensorDataUtil.FlagCode.S_SENSOR_SENSITIVITY_CALIBRATION9,
            }
        }

        # 获取对应的命令，如果没有则返回 None
        return command_mapping.get(baud_rate, {}).get(flag_code, None)