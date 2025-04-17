import re
import time
import json
import network
import ntptime
from machine import UART, Pin
from umqtt.simple import MQTTClient


#from esp32api.SensorResponseParser import SensorResponseParser
#from esp32api.FactoryUtil import FactoryUtil
from esp32api.SensorDataUtil import SensorDataUtil  # 导入外部定义的SensorDataUtil类
#from esp32api.UARTUtil import UARTUtil

class Main:
    sensor_flag = 1
    time_string = ''
    BAUDRATE_COPY = 115200

   

    @staticmethod
    def set_time():
        global time_string
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        current_time = time.localtime()
        time_string = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            current_time[0], current_time[1], current_time[2],
            current_time[3], current_time[4], current_time[5])

    
       

       
        global uart
        uart = UART(ID, baudrate=BAUDRATE, tx=Pin(TX), rx=Pin(RX), bits=BIT, parity=PARITY, stop=STOP)

        while True:
            try:
                client.check_msg()
                if client and time.ticks_diff(time.ticks_ms(), last_heartbeat) > KEEPALIVE_TIME * 1000:
                    client.ping()
                    last_heartbeat = time.ticks_ms()
                    print("Heartbeat sent.")

                if uart.any():
                    utime.sleep(0.1)
                    response = uart.read()
                    hex_string = ' '.join(f'{byte:02x}' for byte in response)
                    hex_string = hex_string.upper()
                    rm_space = DataChangeUtil.clean_string(hex_string)
                    print(f"{time_string} Received from STC8H--------> {hex_string}")
                    data = ''
                    if hex_string[:2] == 'AA':
                        data = ReturnDataSubstring.substring_data_4(rm_space, sensor_flag)
                    elif hex_string[:2] == '3A':
                        data = ReturnDataSubstring.substring_data_7(rm_space, sensor_flag)
                    print(f"{time_string} Publish from EMQX--------> {data}")
                    sensor_data = {"data": data}
                    json_data = json.dumps(sensor_data).encode('utf-8')
                    client.publish(REPLY_TOPIC, json_data)

            except Exception as e:
                print("Error occurred:", e)
                if client:
                    try:
                        client.disconnect()
                    except Exception as dis_e:
                        print("Error disconnecting:", dis_e)
                client = None
                reconnect()

    @staticmethod
    def mqtt_subscribe_callback(topic, msg):
        global sensor_flag
        global BAUDRATE_COPY
        string_data = msg.decode('utf-8')
        sensor_flag = int(string_data)
        code = FactoryUtil.by_type_get_return(sensor_flag, BAUDRATE_COPY) 
        formatted_hex = ' '.join(f'{byte:02x}' for byte in code)
        uart.write(code)

        print("发送的指令：", sensor_flag)
        print(f"{time_string} Sent to STC8H--------> {formatted_hex.upper()}")


class SensorDataUtil:
    GAS_TYPE_MAPPING_4 = {
        0: "无", 1: "EX", 6: "C3H8", 12: "CL2", 16: "HBr", 18: "AsH3", 20: "Br2", 25: "SiH4", 
        26: "无", 27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "C6H6", 
        38: "H2O2", 40: "VOC", 2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3", 
        9: "H2S", 10: "SO2", 11: "NH3", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN", 
        19: "HF", 21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2", 
        33: "C2H4", 34: "CH2O", 39: "C2H3CL", 41: "CH3SH", 42: "C4H8"
    }

    GAS_TYPE_MAPPING_7 = {
        0: "无", 1: "无", 6: "无", 16: "无", 18: "无", 20: "无", 25: "无", 26: "无", 
        27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "无", 38: "无", 
        2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3", 9: "H2S", 10: "SO2", 
        11: "NH3", 12: "CL2", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN", 19: "HF", 
        21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2", 33: "C2H4", 
        34: "CH2O", 39: "CH3SH", 40: "C2H3CL"
    }

    class FlagCode:
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

        S_SENSOR_TYPE1 = "3A 10 01 00 00 01 00 00 82 B0"  
        S_SENSOR_NUM2 = "3A 11 01 01 00 00 00 00 82 C0"  
        S_SENSOR_MODULE_ZERO3 = "3A 12 01 01 01 01 01 00 82 D0"  
        S_SENSOR_MODULE_ZERO3_TRUE = "3A 12 01 01 01 00 00 00 82 F0"
        S_SENSOR_MODULE_CALIBRATION4 = "3A 13 01 01 00 00 00 00 82 E0"  
        S_SENSOR_MODULE_CALIBRATION4_TRUE = "3A 13 01 01 01 00 00 00 83 A0"
        S_SENSOR_UPDATE_ADDRESS5 = "3A 14 02 80 A1 01 00 00 83 B0"  
        S_SENSOR_UPDATE_ADDRESS5_TRUE = "3A 14 02 80 00 00 00 00 83 D0" 
        S_SENSOR_UPDATE_CONCENTRATION6 = "3A 15 01 00 00 00 00 00 83 F0"  
        S_SENSOR_UPDATE_CONCENTRATION6_TRUE = "3A 15 01 01 01 01 01 00 84 10"

# Here, we define how the sensor data and MQTT interaction flow.
class DataChangeUtil:
    @staticmethod
    def clean_string(input_string):
        """
        清除输入字符串中的空格和其他不必要的字符
        """
        return input_string.replace(" ", "").replace("\n", "").replace("\r", "")

class ReturnDataSubstring:
    @staticmethod
    def substring_data_4(hex_string, sensor_flag):
        """
        处理4字节长度的数据，根据不同的传感器类型获取不同的气体类型
        """
        if len(hex_string) < 8:
            print("数据长度不正确，无法处理")
            return ''
        
        # 假设气体类型数据位于字节5和字6
        gas_type_code = int(hex_string[4:6], 16)
        gas_type = SensorDataUtil.GAS_TYPE_MAPPING_4.get(gas_type_code, "未知气体")
        
        # 获取传感器的其他信息，可以扩展
        concentration = int(hex_string[6:8], 16)  # 假设浓度信息在字节7和字节8
        data = {
            "gas_type": gas_type,
            "concentration": concentration
        }
        return json.dumps(data)

    @staticmethod
    def substring_data_7(hex_string, sensor_flag):
        """
        处理7字节长度的数据，根据不同的传感器类型获取不同的气体类型
        """
        if len(hex_string) < 14:
            print("数据长度不正确，无法处理")
            return ''
        
        # 假设气体类型数据位于字节5和字6
        gas_type_code = int(hex_string[4:6], 16)
        gas_type = SensorDataUtil.GAS_TYPE_MAPPING_7.get(gas_type_code, "未知气体")
        
        # 获取传感器的其他信息，可以扩展
        concentration = int(hex_string[6:8], 16)  # 假设浓度信息在字节7和字节8
        data = {
            "gas_type": gas_type,
            "concentration": concentration
        }
        return json.dumps(data)

class FactoryUtil:
    @staticmethod
    def by_type_get_return(sensor_flag, baud_rate):
        """
        根据传感器标识返回相应的指令数据
        """
        if sensor_flag == 1:
            # 返回传感器类型1的指令
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_TYPE1)
        elif sensor_flag == 2:
            # 返回传感器类型2的指令
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_NUM2)
        elif sensor_flag == 3:
            # 返回传感器模块初始化指令
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_MODULE_ZERO3)
        elif sensor_flag == 4:
            # 进行传感器校准
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_MODULE_CALIBRATION4)
        elif sensor_flag == 5:
            # 更新传感器地址
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_UPDATE_ADDRESS5)
        elif sensor_flag == 6:
            # 更新传感器浓度
            return bytes.fromhex(SensorDataUtil.FlagCode.F_SENSOR_UPDATE_CONCENTRATION6)
        else:
            print(f"未定义的传感器标识 {sensor_flag}")
            return b''

    @staticmethod
    def get_reply_for_sensor(sensor_flag):
        """
        根据传感器类型返回对应的应答指令（假设从设备的应答指令）
        """
        if sensor_flag == 1:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_TYPE1)
        elif sensor_flag == 2:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_NUM2)
        elif sensor_flag == 3:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_MODULE_ZERO3)
        elif sensor_flag == 4:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_MODULE_CALIBRATION4)
        elif sensor_flag == 5:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_UPDATE_ADDRESS5)
        elif sensor_flag == 6:
            return bytes.fromhex(SensorDataUtil.FlagCode.S_SENSOR_UPDATE_CONCENTRATION6)
        else:
            print(f"未定义的传感器标识 {sensor_flag}")
            return b'123456789'

    @staticmethod
    def get_sensor_response_by_flag(sensor_flag):
        """
        根据传感器标识返回相应的应答指令
        """
        return FactoryUtil.get_reply_for_sensor(sensor_flag)





        



