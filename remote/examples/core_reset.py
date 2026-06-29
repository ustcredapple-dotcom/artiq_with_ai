from artiq.experiment import *


class CoreReset(EnvExperiment):
    """最小远程测试实验：只复位 core device，不操作外设。"""

    def build(self):
        self.setattr_device("core")

    @kernel
    def run(self):
        self.core.reset()
