"""
面向客户二次开发的 SDK 客户端。

设计目标：
1. 保留原有 communication 静态接口不动，避免影响旧项目。
2. 新增实例化客户端，方便客户像使用普通 Python 工具包一样集成。
3. 允许客户直接传入自己已经初始化好的 UART 对象。
"""

try:
    from esp32api._sdk_compat import (
        _UARTWrapper,
        FlagCode,
        substring_data_4,
        substring_data_7,
        build_4_update_span,
        build_7_sensitivity_cal,
        clamp_u16,
        bytes_to_hex,
    )
except ImportError:
    from _sdk_compat import (
        _UARTWrapper,
        FlagCode,
        substring_data_4,
        substring_data_7,
        build_4_update_span,
        build_7_sensitivity_cal,
        clamp_u16,
        bytes_to_hex,
    )


class SensorClient:
    """
    传感器 SDK 客户端。

    支持两种初始化方式：
    1. 传入 uart 对象，复用客户自己的串口初始化逻辑
    2. 传入 port / baudrate / tx / rx，由库内部创建 UART
    """

    def __init__(
        self,
        uart=None,
        port=None,
        baudrate=None,
        tx=None,
        rx=None,
        timeout=300,
        addr_4=0x01,
        id_7=0x10,
    ):
        self._uart = None
        self.addr_4 = int(addr_4)
        self.id_7 = int(id_7)
        self.port = None
        self.baudrate = None
        self.tx = None
        self.rx = None
        self.timeout = None

        self.set_uart(
            uart=uart,
            port=port,
            baudrate=baudrate,
            tx=tx,
            rx=rx,
            timeout=timeout,
        )

    def set_uart(self, uart=None, port=None, baudrate=None, tx=None, rx=None, timeout=None):
        """
        设置或重新设置 UART。

        说明：
        - 如果传入 uart，则直接使用客户已有的 UART 对象
        - 如果未传 uart，则要求至少提供 port，由库内部创建 UART
        """
        if uart is not None:
            resolved_timeout = 300 if timeout is None else timeout

            # 如果传入的对象已经具备 send_hex_and_read 方法，
            # 说明它已经是适配好的串口对象，可以直接复用。
            if hasattr(uart, "send_hex_and_read"):
                self._uart = uart
            else:
                # 如果传入的是原始 UART 对象，则再包一层 _UARTWrapper，
                # 统一成 SDK 内部使用的串口访问接口。
                self._uart = _UARTWrapper(
                    uart=uart,
                    timeout=resolved_timeout,
                )

            # 外部 UART 的实际配置由客户负责。这里仅保存客户显式提供的
            # 描述信息，不推断属性，也不使用这些参数重新配置 UART。
            self.port = port
            self.baudrate = baudrate
            self.tx = tx
            self.rx = rx
            self.timeout = resolved_timeout
            return self

        resolved_port = self.port if port is None else port
        if resolved_port is None:
            raise ValueError("未传入 uart 时，必须至少提供 port 参数")

        resolved_baudrate = self.baudrate if baudrate is None else baudrate
        resolved_tx = self.tx if tx is None else tx
        resolved_rx = self.rx if rx is None else rx
        resolved_timeout = self.timeout if timeout is None else timeout

        if resolved_baudrate is None:
            resolved_baudrate = self._default_baudrate_for_port(resolved_port)
        if resolved_timeout is None:
            resolved_timeout = 300

        self._uart = _UARTWrapper(
            port=resolved_port,
            baudrate=resolved_baudrate,
            tx=resolved_tx,
            rx=resolved_rx,
            timeout=resolved_timeout,
        )

        self.port = resolved_port
        self.baudrate = resolved_baudrate
        self.tx = resolved_tx
        self.rx = resolved_rx
        self.timeout = resolved_timeout
        return self

    def _default_baudrate_for_port(self, port):
        """根据当前硬件约定推导默认波特率。"""
        return 9600 if int(port) == 1 else 115200

    def set_address(self, addr_4=None, id_7=None):
        """更新 4 系列地址或 7 系列设备 ID。"""
        if addr_4 is not None:
            self.addr_4 = int(addr_4)
        if id_7 is not None:
            self.id_7 = int(id_7)
        return self

    def get_config(self):
        """返回当前客户端正在使用的串口与协议配置。"""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "tx": self.tx,
            "rx": self.rx,
            "timeout": self.timeout,
            "addr_4": self.addr_4,
            "id_7": self.id_7,
        }

    def _send_hex_and_read(self, hex_cmd: str, delay_ms: int = 100) -> str:
        """统一封装十六进制指令发送与读取。"""
        return self._uart.send_hex_and_read(hex_cmd, delay_ms=delay_ms)

    def _try_7_then_4(self, hex_cmd_7: str, hex_cmd_4: str, parse_7, parse_4, parse_id: int):
        """
        先尝试 7 系列协议，再回退 4 系列协议。

        这样客户即使不知道模块的具体系列，也可以先调用统一接口。
        """
        rsp7 = self._send_hex_and_read(hex_cmd_7)
        if rsp7:
            return {"series": 7, "raw": rsp7, "parsed": parse_7(rsp7, parse_id)}

        rsp4 = self._send_hex_and_read(hex_cmd_4)
        if rsp4:
            return {"series": 4, "raw": rsp4, "parsed": parse_4(rsp4, parse_id)}

        return {"series": None, "raw": "", "parsed": ""}

    def getInfo(self):
        """读取模块信息并自动识别设备系列。"""
        result = self._try_7_then_4(
            FlagCode.S_SENSOR_TYPE1,
            FlagCode.F_SENSOR_TYPE1,
            substring_data_7,
            substring_data_4,
            1,
        )
        return {
            "ok": bool(result["series"]),
            "series": result["series"],
            "raw": result["raw"],
            "info": result["parsed"],
        }

    def getSpanValue(self):
        """读取量程或标气浓度。"""
        rsp7a = self._send_hex_and_read(FlagCode.S_SENSOR_NUM2)
        rsp7b = self._send_hex_and_read(FlagCode.S_SENSOR_NUM3)
        if rsp7a or rsp7b:
            out = {"series": 7, "raw": {}, "value": {}, "ok": True}
            if rsp7a:
                out["raw"]["μg/m³"] = rsp7a
                out["value"]["μg/m³"] = substring_data_7(rsp7a, 2)
            if rsp7b:
                out["raw"]["ppb"] = rsp7b
                out["value"]["ppb"] = substring_data_7(rsp7b, 3)
            return out

        rsp4 = self._send_hex_and_read(FlagCode.F_SENSOR_NUM2)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "value": substring_data_4(rsp4, 2)}

        return {"ok": False, "series": None, "raw": "", "value": None}

    def getReading(self):
        """读取实时浓度数据。"""
        rsp7 = self._send_hex_and_read(FlagCode.S_SENSOR_PARAMS6)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "parsed": substring_data_7(rsp7, 6)}

        rsp4 = self._send_hex_and_read(FlagCode.F_SENSOR_NUM2)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "parsed": substring_data_4(rsp4, 2)}

        return {"ok": False, "series": None, "raw": "", "parsed": ""}

    def zeroCal(self):
        """执行零点标定。"""
        rsp7 = self._send_hex_and_read(FlagCode.S_SENSOR_ZERO_CALIBRATION8)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "result": substring_data_7(rsp7, 8)}

        rsp4 = self._send_hex_and_read(FlagCode.F_SENSOR_MODULE_ZERO3)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "result": substring_data_4(rsp4, 3)}

        return {"ok": False, "series": None, "raw": "", "result": "无返回"}

    def spanCal(self, spanValue: int, prefer="7-first"):
        """执行跨度标定。"""
        span_ppm = clamp_u16(spanValue)
        id7 = self.id_7 & 0xFF
        addr4 = self.addr_4 & 0xFF

        frame7 = build_7_sensitivity_cal(id7, span_ppm)
        frame4 = build_4_update_span(addr4, span_ppm)

        def send7():
            return self._send_hex_and_read(bytes_to_hex(frame7), delay_ms=150)

        def send4():
            return self._send_hex_and_read(bytes_to_hex(frame4), delay_ms=150)

        rsp7 = ""
        rsp4 = ""
        if prefer == "4-first":
            rsp4 = send4()
            if rsp4 == "" and "EE" not in rsp4:
                rsp7 = send7()
        else:
            rsp7 = send7()
            if rsp7 == "" and "EE" not in rsp7:
                rsp4 = send4()

        out = {
            "ok": False,
            "series": None,
            "request": {"7": bytes_to_hex(frame7), "4": bytes_to_hex(frame4)},
            "response": {},
        }

        if rsp7:
            out["response"]["7"] = rsp7
            out["series"] = 7
            out["ok"] = (" 00 " in f" {rsp7} ") or ("标定成功" in substring_data_7(rsp7, 9))
            out["result"] = substring_data_7(rsp7, 9)

        if rsp4:
            out["response"]["4"] = rsp4
            out["series"] = out["series"] or 4
            if " AA 05 " in f" {rsp4} " and " 10 " in f" {rsp4} "[9:14]:
                out["ok"] = True
            if not out.get("result"):
                out["result"] = substring_data_4(rsp4, 6)

        if not rsp7 and not rsp4:
            out["note"] = "无设备应答，请检查接线、电源和串口参数"

        out["note2"] = f"span={span_ppm} ppm, id7=0x{id7:02X}, addr4=0x{addr4:02X}"
        return out

    def getTemp(self):
        """读取温度，仅 7 系列支持。"""
        rsp7 = self._send_hex_and_read(FlagCode.S_SENSOR_TEMPERATURE4)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "value": substring_data_7(rsp7, 4)}
        return {"ok": False, "series": None, "raw": "", "value": None}

    def getHumi(self):
        """读取湿度，仅 7 系列支持。"""
        rsp7 = self._send_hex_and_read(FlagCode.S_SENSOR_HUMIDITY5)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "value": substring_data_7(rsp7, 5)}
        return {"ok": False, "series": None, "raw": "", "value": None}
