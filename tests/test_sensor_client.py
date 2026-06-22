import pytest

import esp32api.client as client_module
from esp32api.client import SensorClient


class FakeUART:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self):
        if self.responses:
            return self.responses.pop(0)
        return None


class ScriptedTransport:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.commands = []

    def send_hex_and_read(self, hex_cmd, delay_ms=100):
        self.commands.append((hex_cmd, delay_ms))
        if self.responses:
            return self.responses.pop(0)
        return ""


class RecordingWrapper:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.commands = []
        RecordingWrapper.instances.append(self)

    def send_hex_and_read(self, hex_cmd, delay_ms=100):
        self.commands.append((hex_cmd, delay_ms))
        return ""


@pytest.fixture
def recording_wrapper(monkeypatch):
    RecordingWrapper.instances = []
    monkeypatch.setattr(client_module, "_UARTWrapper", RecordingWrapper)
    return RecordingWrapper


def test_external_uart_does_not_require_port():
    uart = FakeUART()

    client = SensorClient(uart=uart)

    assert client.get_config() == {
        "port": None,
        "baudrate": None,
        "tx": None,
        "rx": None,
        "timeout": 300,
        "addr_4": 1,
        "id_7": 16,
    }


def test_external_uart_description_is_reported_without_reconfiguring_uart(recording_wrapper):
    uart = FakeUART()

    client = SensorClient(
        uart=uart,
        port=2,
        baudrate=115200,
        tx=17,
        rx=16,
        timeout=450,
    )

    assert recording_wrapper.instances[0].kwargs == {
        "uart": uart,
        "timeout": 450,
    }
    assert client.get_config() == {
        "port": 2,
        "baudrate": 115200,
        "tx": 17,
        "rx": 16,
        "timeout": 450,
        "addr_4": 1,
        "id_7": 16,
    }


@pytest.mark.parametrize(
    ("port", "expected_baudrate"),
    [(1, 9600), (2, 115200)],
)
def test_sdk_created_uart_uses_existing_default_baudrate_rule(
    recording_wrapper, port, expected_baudrate
):
    client = SensorClient(port=port, tx=17, rx=16)

    assert recording_wrapper.instances[0].kwargs == {
        "port": port,
        "baudrate": expected_baudrate,
        "tx": 17,
        "rx": 16,
        "timeout": 300,
    }
    assert client.get_config()["baudrate"] == expected_baudrate


def test_sdk_created_uart_requires_port():
    with pytest.raises(ValueError, match="必须至少提供 port"):
        SensorClient()


def test_clients_keep_external_uart_instances_isolated():
    first_uart = FakeUART()
    second_uart = FakeUART()
    first = SensorClient(uart=first_uart)
    second = SensorClient(uart=second_uart)

    first.getInfo()
    second.getReading()

    assert first_uart.writes == [
        bytes.fromhex("3A 10 01 00 00 01 00 00 82 B0"),
        bytes.fromhex("AA 0F 01 C5 80 EE"),
    ]
    assert second_uart.writes == [
        bytes.fromhex("3A 10 03 00 00 06 00 00 32 93"),
        bytes.fromhex("AA 01 01 C1 E0 EE"),
    ]


def test_set_uart_switches_to_new_external_uart():
    first_uart = FakeUART()
    second_uart = FakeUART()
    client = SensorClient(uart=first_uart)

    client.set_uart(uart=second_uart)
    client.getTemp()

    assert first_uart.writes == []
    assert second_uart.writes == [
        bytes.fromhex("3A 10 03 00 04 01 00 00 82 62")
    ]
    assert client.get_config()["port"] is None
    assert client.get_config()["baudrate"] is None


def test_public_methods_keep_existing_commands_and_return_shapes():
    transport = ScriptedTransport(
        [
            "3A 10 01 02 8D 68",
            "3A 10 03 00 00 06 00 00 00 08 00 00 00 07 09 3F 15 9E 77 6B",
            "3A 10 03 00 00 02 00 00 00 06 24 CF",
            "3A 10 03 00 02 02 00 00 00 06 25 2D",
            "3A 10 07 00 00 01 00 E4 82 9D",
            "3A 10 09 00 00 32 3F",
            "3A 10 03 00 04 01 09 49 45 C4",
            "3A 10 03 00 05 01 14 E3 CD 17",
        ]
    )
    client = SensorClient(uart=transport)

    info = client.getInfo()
    reading = client.getReading()
    span = client.getSpanValue()
    zero = client.zeroCal()
    calibration = client.spanCal(250)
    temperature = client.getTemp()
    humidity = client.getHumi()

    assert info == {
        "ok": True,
        "series": 7,
        "raw": "3A 10 01 02 8D 68",
        "info": "CO (code=2)",
    }
    assert reading["ok"] is True
    assert reading["series"] == 7
    assert set(reading) == {"ok", "series", "raw", "parsed"}
    assert span["ok"] is True
    assert span["series"] == 7
    assert set(span) == {"ok", "series", "raw", "value"}
    assert zero["ok"] is True
    assert set(zero) == {"ok", "series", "raw", "result"}
    assert calibration["series"] == 7
    assert set(calibration) == {
        "ok",
        "series",
        "request",
        "response",
        "result",
        "note2",
    }
    assert temperature["ok"] is True
    assert set(temperature) == {"ok", "series", "raw", "value"}
    assert humidity["ok"] is True
    assert set(humidity) == {"ok", "series", "raw", "value"}

    assert transport.commands == [
        ("3A 10 01 00 00 01 00 00 82 B0", 100),
        ("3A 10 03 00 00 06 00 00 32 93", 100),
        ("3A 10 03 00 00 02 00 00 73 52", 100),
        ("3A 10 03 00 02 02 00 00 72 EA", 100),
        ("3A 10 07 00 00 01 00 00 82 D6", 100),
        ("3A 10 09 00 00 01 00 FA 03 BB", 150),
        ("3A 10 03 00 04 01 00 00 82 62", 100),
        ("3A 10 03 00 05 01 00 00 83 9E", 100),
    ]
