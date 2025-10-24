from pydantic_core import InitErrorDetails
from pydantic import model_serializer, model_validator, ValidationError


def register_validator(_cls):
    def decorator(func):
        _cls.add_validator(func)
        return func
    return decorator


def register_serializer(_cls):
    def decorator(func):
        _cls.add_serializer(func)
        return func
    return decorator


class GcSerializer:
    _serializers = {}
    _validators = {}

    @classmethod
    def add_serializer(cls, serializer_func):
        cls._serializers[cls.__qualname__] = serializer_func

    @classmethod
    def add_validator(cls, validator_func):
        cls._validators[cls.__qualname__] = validator_func

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        model = handler(self)
        serialize_func = self._serializers.get(self.__class__.__qualname__)
        if serialize_func:
            return serialize_func(model)
        return model

    @model_validator(mode='wrap')
    @classmethod
    def validate_model(cls, model, handler, info):
        try:
            validator = cls._validators.get(cls.__qualname__)
            if validator:
                return validator(model, handler, info)
            return handler(model)
        except Exception as exc:
            raise ValidationError.from_exception_data(
                title=cls.__qualname__,
                line_errors=[InitErrorDetails(type="value_error",
                                              input=f'model: {model}',
                                              ctx=dict(error=f'model: {model}, err: {str(exc)}'))])
