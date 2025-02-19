from machine import UART, Pin
import time

# UART1 配置：用于收发和打印数据
uart1 = UART(1, baudrate=115200, tx=Pin(12), rx=Pin(13))

# UART2 配置：用于与传感器通信
uart2 = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))

# 串口通信功能
def uart_communication():
    ch = b""

    while True:
        # 检查 UART1 是否有可读数据
        if uart1.any():
            # 从 UART1 读取数据并通过 UART2 转发给传感器
            ch = uart1.read()
            uart2.write(ch)
            print("UART1 发送的数据转发给 UART2:", ch)
            time.sleep(2)

            # 检查 UART2 是否有传感器回复的数据
            if uart2.any():
                # 读取来自传感器的回复数据
                sensor_reply = uart2.read(uart2.any())
                print("UART2 从传感器接收到的数据:", sensor_reply)

                # UART2 将传感器数据回复给 UART1
                uart1.write(sensor_reply)
                print("UART2 回复 UART1 的数据:", sensor_reply)

            # 检查 UART1 是否收到 UART2 的回复
            if uart1.any():
                reply = uart1.read(uart1.any())
                print("UART1 接收到 UART2 的回复:", reply)

        time.sleep(1)  # 防止过快循环

# 启动通信
uart_communication()





