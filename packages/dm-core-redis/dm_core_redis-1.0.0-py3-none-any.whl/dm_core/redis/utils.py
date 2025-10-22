def singleton(cls):
    instances = {}

    def instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    # Having a reference so the unit test can work and make use of patching
    # Example: @patch('where_ever_singleton_included.singleton.__wrapped__.MetaClient.service_info) assuming MetaClient is
    # wrapped with singleton
    instance.__wrapped__ = cls
    return instance


def singleton_with_param(cls):
    instances = {}

    def instance(param, *args, **kwargs):
        key = f"{cls.__name__}:{param}"
        if key not in instances:
            instances[key] = cls(param)
        return instances[key]

    return instance
