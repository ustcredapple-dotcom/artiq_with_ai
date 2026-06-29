from artiq.experiment import *


class TTLBlink(EnvExperiment):
    """TTL 闪烁示例。

    使用前请确认 device_db.py 中存在名为 ttl0 的设备。
    如果你的 TTL 设备名不同，请把 build() 中的 ttl0 改成实际名称。
    """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")
        self.setattr_argument("count", NumberValue(10, min=1, max=100, step=1, ndecimals=0))
        self.setattr_argument("pulse_ms", NumberValue(100, min=1, max=5000, unit="ms", step=1, ndecimals=0))

    @kernel
    def run(self):
        self.core.reset()
        delay(10 * ms)
        for _ in range(self.count):
            self.ttl0.on()
            delay(self.pulse_ms * ms)
            self.ttl0.off()
            delay(self.pulse_ms * ms)
