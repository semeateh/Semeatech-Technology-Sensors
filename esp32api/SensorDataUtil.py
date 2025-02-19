import re

class SensorDataUtil:
    # 4系列气体类型映射
    GAS_TYPE_MAPPING_4 = {
        0: "无", 1: "EX", 6: "C3H8", 12: "CL2", 16: "HBr", 18: "AsH3", 20: "Br2", 25: "SiH4", 
        26: "无", 27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "C6H6", 
        38: "H2O2", 40: "VOC", 2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3", 
        9: "H2S", 10: "SO2", 11: "NH3", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN", 
        19: "HF", 21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2", 
        33: "C2H4", 34: "CH2O", 39: "C2H3CL", 41: "CH3SH", 42: "C4H8"
    }

    # 7系列气体类型映射
    GAS_TYPE_MAPPING_7 = {
        0: "无", 1: "无", 6: "无", 16: "无", 18: "无", 20: "无", 25: "无", 26: "无", 
        27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "无", 38: "无", 
        2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3", 9: "H2S", 10: "SO2", 
        11: "NH3", 12: "CL2", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN", 19: "HF", 
        21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2", 33: "C2H4", 
        34: "CH2O", 39: "CH3SH", 40: "C2H3CL"
    }

    class FlagCode:
        # 4系列指令
        F_SENSOR_TYPE1 = "AA 0F 01 C5 80 EE"  
        F_SENSOR_NUM2 = "AA 01 01 C1 E0 EE"  
        F_SENSOR_MODULE_ZERO3 = "AA 02 01 C1 10 EE"  
        F_SENSOR_MODULE_ZERO3_TRUE = "AA 02 01 10 D0 5C EE"
        F_SENSOR_MODULE_CALIBRATION4 = "AA 03 01 C0 80 EE"  
        F_SENSOR_MODULE_CALIBRATION4_TRUE = "AA 03 01 10 81 9C EE"
        F_SENSOR_UPDATE_ADDRESS5 = "AA 04 02 82 B1 EE"  
        F_SENSOR_UPDATE_ADDRESS5_TRUE = "AA 04 02 10 30 AD EE"
        F_SENSOR_UPDATE_CONCENTRATION6 = "AA 05 01 01 F4 51 3F EE"  
        F_SENSOR_UPDATE_CONCENTRATION6_TRUE = "AA 05 01 10 01 F4 E8 2E EE"

        # 7系列指令
        S_SENSOR_TYPE1 = "3A 10 01 00 00 01 00 00 82 B0"  
        S_SENSOR_NUM2 = "3A 10 03 00 00 02 00 00 73 52"  
        S_SENSOR_NUM3 = "3A 10 03 00 02 02 00 00 72 EA"  
        S_SENSOR_TEMPERATURE4 = "3A 10 03 00 04 01 00 00 82 62"  
        S_SENSOR_HUMIDITY5 = "3A 10 03 00 05 01 00 00 83 9E"  
        S_SENSOR_PARAMS6 = "3A 10 03 00 00 06 00 00 32 93"  
        S_SENSOR_CHECK7 = "3A 10 08 00 0A F9"  
        S_SENSOR_ZERO_CALIBRATION8 = "3A 10 07 00 00 01 00 00 82 D6"  
        S_SENSOR_SENSITIVITY_CALIBRATION9 = "3A 10 09 00 00 01 00 0A 03 FF"  

    @staticmethod
    def substring_data_4(old_data, type_id):
        type_ = ""
        new_data = ""
        if type_id == 1:
            new_data = old_data[6:8]
            type_ = SensorDataUtil.switch_type_4(SensorDataUtil.hex_to_decimal(new_data))
        elif type_id == 2:
            new_data = old_data[8:14]
            type_ = str(SensorDataUtil.hex_to_decimal(new_data)) + " ppm"
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
        type_ = ""
        new_data = ""
        if type_id == 1:
            new_data = old_data[6:8]
            type_ = SensorDataUtil.switch_type_7(SensorDataUtil.hex_to_decimal(new_data))
        elif type_id == 2:
            new_data = old_data[12:20]
            type_ = str(SensorDataUtil.hex_to_decimal(new_data)) + "μg/m³"
        elif type_id == 3:
            new_data = old_data[12:20]
            type_ = str(SensorDataUtil.hex_to_decimal(new_data)) + "ppb"
        elif type_id == 4:
            new_data = old_data[12:16]
            type_ = "监测温度为:" + str(SensorDataUtil.hex_to_decimal(new_data) / 100) + "°C"
        elif type_id == 5:
            new_data = old_data[12:16]
            type_ = "监测湿度为:" + str(SensorDataUtil.hex_to_decimal(new_data) / 100) + "%RH"
        elif type_id == 6:
            data1 = SensorDataUtil.hex_to_decimal(old_data[12:20])
            data2 = SensorDataUtil.hex_to_decimal(old_data[20:28])
            data3 = SensorDataUtil.hex_to_decimal(old_data[28:32]) / 100
            data4 = SensorDataUtil.hex_to_decimal(old_data[32:36]) / 100
            type_ = f"浓度值: {data1} μg/m³, 浓度值: {data2}ppb, 温度值: {data3}°C, 湿度值: {data4}%RH"
        elif type_id == 8:
            new_data = old_data[12:16]
            type_ = "零点标定返回数值:" + str(SensorDataUtil.hex_to_decimal(new_data))
        elif type_id == 9:
            flag = "标定成功"
            substring = old_data[6:8]
            if substring == "01":
                flag = "标定中"
            elif substring == "02":
                flag = "标定失败"
            type_ = "标定结果:" + flag
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



    @staticmethod
    def clean_string(flag_str):
        return flag_str.replace(" ", "").upper()

    @staticmethod
    def extract_numbers_from_string(input_string):
        # 使用 findall 提取所有数字
        return re.findall(r'\d+', input_string)
    
    @staticmethod
    def byte_array_to_hex_string(byte_array):
        # 使用 hex 方法将整数转换为十六进制字符串
        return ''.join(f"{byte:02X}" if isinstance(byte, int) else '00' for byte in byte_array)

    @staticmethod
    def hex_string_to_byte_array(hex_str):
        return bytes.fromhex(hex_str)


class FactoryUtil: 
    @staticmethod
    def by_type_get_return(typeId, baudRate):
        message = ""
        if baudRate == 9600:
            if typeId == 1:
                message = SensorDataUtil.FlagCode.F_SENSOR_TYPE1
            elif typeId == 2:
                message = SensorDataUtil.FlagCode.F_SENSOR_NUM2
            elif typeId == 3:
                message = SensorDataUtil.FlagCode.F_SENSOR_MODULE_ZERO3
            elif typeId == 4:
                message = SensorDataUtil.FlagCode.F_SENSOR_MODULE_CALIBRATION4
            elif typeId == 5:
                message = SensorDataUtil.FlagCode.F_SENSOR_UPDATE_ADDRESS5
            elif typeId == 6:
                message = SensorDataUtil.FlagCode.F_SENSOR_UPDATE_CONCENTRATION6
            else:
                message = "功能还在开发中......"
        elif baudRate == 115200:
            if typeId == 1:
                message = SensorDataUtil.FlagCode.S_SENSOR_TYPE1
            elif typeId == 2:
                message = SensorDataUtil.FlagCode.S_SENSOR_NUM2
            elif typeId == 3:
                message = SensorDataUtil.FlagCode.S_SENSOR_NUM3
            elif typeId == 4:
                message = SensorDataUtil.FlagCode.S_SENSOR_TEMPERATURE4
            elif typeId == 5:
                message = SensorDataUtil.FlagCode.S_SENSOR_HUMIDITY5
            elif typeId == 6:
                message = SensorDataUtil.FlagCode.S_SENSOR_PARAMS6
            elif typeId == 7:
                message = SensorDataUtil.FlagCode.S_SENSOR_CHECK7
            elif typeId == 8:
                message = SensorDataUtil.FlagCode.S_SENSOR_ZERO_CALIBRATION8
            elif typeId == 9:
                message = SensorDataUtil.FlagCode.S_SENSOR_SENSITIVITY_CALIBRATION9
            else:
                message = "功能还在开发中......"
        return SensorDataUtil.hex_string_to_byte_array(message)





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




