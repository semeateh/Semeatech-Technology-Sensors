from machine import UART, Pin
import time
import re


class UARTUtil:

    def __init__(self, uart_id, tx_pin, rx_pin, baudrate=9600):
        # 初始化UART
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))

    def input_hex(self):
        print("发送的字节数据")
        hex_input = input("请输入十六进制数据（例如 3A 10 01）: ")  # 输入十六进制数据
        hex_values = hex_input.split()  # 按空格分割输入
        byte_data = self.hex_string_to_byte_array(hex_input)  # 转换为字节数组
        print("发送的字节数据:", byte_data)  # 打印发送的字节数据
        self.uart.write(byte_data)  # 发送数据

    def read_uart_data(self):
        if self.uart.any():  # 检查是否有可读数据
            received_data = self.uart.read()  # 读取数据
            hex_string = self.byte_array_to_hex_string(received_data)  # 转换为十六进制字符串
            print(f"接收到的数据的十六进制表示: {hex_string}")  # 打印接收的数据
        else:
            print("没有接收到数据。")

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
        return ' '.join(f'{b:02X}' for b in byte_array)

# 主函数
if __name__ == "__main__":
    uart_util = UARTUtil(uart_id=2, tx_pin=17, rx_pin=16)  # 根据实际连接调整引脚
    while True:
        uart_util.input_hex()  # 输入并发送十六进制数据
        time.sleep(1)   # 等待一秒以确保数据发送完成
        uart_util.read_uart_data()  # 读取并打印接收到的数据
