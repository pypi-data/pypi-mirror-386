# TODO: possibly document


class KeyValue:  # noqa: D101
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value


class EnvVariable(KeyValue):  # noqa: D101
    pass


class Label(KeyValue):  # noqa: D101
    pass


class ExposedPort:  # noqa: D101
    def __init__(self, container_port: int, host_port: int | None = None):
        self.container_port = container_port
        self.host_port = host_port


class Volume:  # noqa: D101
    def __init__(self, container_path: str, host_path: str | None = None):
        self.container_path = container_path
        self.host_path = host_path


class Healthcheck:  # noqa: D101
    def __init__(
        self,
        test: list[str],
        interval: str | None = None,
        timeout: str | None = None,
        retries: int | None = None,
        start_period: str | None = None,
    ):
        self.test = test
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.start_period = start_period
