import threading
from pywinusb import hid


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        instance = cls._instances.get(cls)
        if instance is None:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return instance


class BasePointerDevice(metaclass=SingletonMeta):
    VENDOR_ID = None
    PRODUCT_ID = None
    PRODUCT_DESCRIPTION = None

    def __init__(self, app_ctx, hid_device):
        self._ctx = app_ctx
        self._device = hid_device
        self._stop_event = threading.Event()
        self._monitoring = False
        self._device.set_raw_data_handler(self.handle_input_report)

    def monitor(self):
        if self._monitoring:
            return

        self._ctx.log(f"* Iniciando monitoramento: {self.display_name()}")
        try:
            self._device.open()
            self._monitoring = True
        except Exception as e:
            self._ctx.log(f"* Erro ao abrir dispositivo: {e}")

    def stop(self):
        if self._monitoring:
            self._ctx.log(f"* Encerrando monitoramento: {self.display_name()}")
            try:
                self._device.close()
            except Exception as e:
                self._ctx.log(f"* Erro ao fechar dispositivo: {e}")
            self._monitoring = False

    def display_name(self):
        return (
            self.PRODUCT_DESCRIPTION
            or self._device.product_name
            or self.__class__.__name__
        )

    def handle_input_report(self, data):
        """
        Manipulador de pacotes recebidos do dispositivo.
        Substitua este método na subclasse.
        """
        self._ctx.log(f"> Dados recebidos: {data}")
        self.handle_event(data)

    def handle_event(self, data):
        """Subclasse deve implementar isso para interpretar o relatório bruto."""
        pass

    @classmethod
    def find_all_devices(cls):
        all_devices = hid.HidDeviceFilter(
            vendor_id=cls.VENDOR_ID, product_id=cls.PRODUCT_ID
        ).get_devices()
        return [dev for dev in all_devices if cls.is_known_device(dev)]

    @classmethod
    def is_known_device(cls, device):
        return device.vendor_id == cls.VENDOR_ID and device.product_id == cls.PRODUCT_ID

    def emit_key_press(self, key):
        self._ctx.log(f"> Simulando tecla: {key} (pressionar e soltar)")

    def emit_key_chord(self, keys):
        self._ctx.log(f"> Simulando atalho: {keys}")
