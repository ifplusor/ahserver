# encoding=utf-8

__all__ = ["noexcept"]


class noexcept:
    def __init__(self, except_return, raise_exception=()):
        self.except_return = except_return
        self.raise_exception = raise_exception

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self.raise_exception as e:
                raise e
            except Exception:
                # print("encounter exception, type{}, message:{}".format(type(e), e))
                return self.except_return

        return wrapper
