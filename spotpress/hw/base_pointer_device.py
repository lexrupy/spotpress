from spotpress.utils import SingletonMeta


class BasePointerDevice(metaclass=SingletonMeta):
    def monitor(self):
        pass

    def stop(self):
        pass
