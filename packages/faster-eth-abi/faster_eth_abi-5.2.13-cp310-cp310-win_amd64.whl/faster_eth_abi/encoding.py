import abc
import codecs
import decimal
from typing import (
    Any,
    Callable,
    ClassVar,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
)

from faster_eth_utils import (
    is_address,
    is_boolean,
    is_bytes,
    is_integer,
    is_list_like,
    is_number,
    is_text,
    to_canonical_address,
)
from typing_extensions import (
    Self,
)

from faster_eth_abi._encoding import (
    encode_elements,
    encode_elements_dynamic,
    encode_fixed,
    encode_signed,
    encode_tuple,
    int_to_big_endian,
)
from faster_eth_abi.base import (
    BaseCoder,
)
from faster_eth_abi.exceptions import (
    EncodingTypeError,
    IllegalValue,
    ValueOutOfBounds,
)
from faster_eth_abi.from_type_str import (
    parse_tuple_type_str,
    parse_type_str,
)
from faster_eth_abi.utils.numeric import (
    TEN,
    abi_decimal_context,
    ceil32,
    compute_signed_fixed_bounds,
    compute_signed_integer_bounds,
    compute_unsigned_fixed_bounds,
    compute_unsigned_integer_bounds,
)
from faster_eth_abi.utils.padding import (
    zpad_right,
)
from faster_eth_abi.utils.string import (
    abbr,
)


class BaseEncoder(BaseCoder, metaclass=abc.ABCMeta):
    """
    Base class for all encoder classes.  Subclass this if you want to define a
    custom encoder class.  Subclasses must also implement
    :any:`BaseCoder.from_type_str`.
    """

    @abc.abstractmethod
    def encode(self, value: Any) -> bytes:  # pragma: no cover
        """
        Encodes the given value as a sequence of bytes.  Should raise
        :any:`exceptions.EncodingError` if ``value`` cannot be encoded.
        """

    @abc.abstractmethod
    def validate_value(self, value: Any) -> None:  # pragma: no cover
        """
        Checks whether or not the given value can be encoded by this encoder.
        If the given value cannot be encoded, must raise
        :any:`exceptions.EncodingError`.
        """

    @classmethod
    def invalidate_value(
        cls,
        value: Any,
        exc: Type[Exception] = EncodingTypeError,
        msg: Optional[str] = None,
    ) -> NoReturn:
        """
        Throws a standard exception for when a value is not encodable by an
        encoder.
        """
        raise exc(
            f"Value `{abbr(value)}` of type {type(value)} cannot be encoded by "
            f"{cls.__name__}{'' if msg is None else (': ' + msg)}"
        )

    def __call__(self, value: Any) -> bytes:
        return self.encode(value)


class TupleEncoder(BaseEncoder):
    encoders: Tuple[BaseEncoder, ...] = ()

    def __init__(self, encoders: Tuple[BaseEncoder, ...], **kwargs: Any) -> None:
        super().__init__(encoders=encoders, **kwargs)

        self.is_dynamic = any(getattr(e, "is_dynamic", False) for e in self.encoders)

    def validate(self) -> None:
        super().validate()

        if self.encoders is None:
            raise ValueError("`encoders` may not be none")

    def validate_value(self, value: Sequence[Any]) -> None:
        if not is_list_like(value):
            self.invalidate_value(
                value,
                msg="must be list-like object such as array or tuple",
            )

        encoders = self.encoders
        if len(value) != len(encoders):
            self.invalidate_value(
                value,
                exc=ValueOutOfBounds,
                msg=f"value has {len(value)} items when {len(encoders)} "
                "were expected",
            )

        for item, encoder in zip(value, encoders):
            try:
                encoder.validate_value(item)
            except AttributeError:
                encoder(item)

    def encode(self, values: Sequence[Any]) -> bytes:
        self.validate_value(values)
        return encode_tuple(values, self.encoders)

    __call__: Callable[[Self, Sequence[Any]], bytes] = encode

    @parse_tuple_type_str
    def from_type_str(cls, abi_type, registry):
        encoders = tuple(
            registry.get_encoder(c.to_type_str()) for c in abi_type.components
        )

        return cls(encoders=encoders)


class FixedSizeEncoder(BaseEncoder):
    value_bit_size = None
    data_byte_size = None
    encode_fn = None
    type_check_fn = None
    is_big_endian = None

    def validate(self) -> None:
        super().validate()

        value_bit_size = self.value_bit_size
        if value_bit_size is None:
            raise ValueError("`value_bit_size` may not be none")
        data_byte_size = self.data_byte_size
        if data_byte_size is None:
            raise ValueError("`data_byte_size` may not be none")
        if self.encode_fn is None:
            raise ValueError("`encode_fn` may not be none")
        if self.is_big_endian is None:
            raise ValueError("`is_big_endian` may not be none")

        if value_bit_size % 8 != 0:
            raise ValueError(
                f"Invalid value bit size: {value_bit_size}. Must be a multiple of 8"
            )

        if value_bit_size > data_byte_size * 8:
            raise ValueError("Value byte size exceeds data size")

    def validate_value(self, value):
        raise NotImplementedError("Must be implemented by subclasses")

    def encode(self, value: Any) -> bytes:
        self.validate_value(value)
        encode_fn = self.encode_fn
        if encode_fn is None:
            raise AssertionError("`encode_fn` is None")
        return encode_fixed(value, encode_fn, self.is_big_endian, self.data_byte_size)

    __call__ = encode


class Fixed32ByteSizeEncoder(FixedSizeEncoder):
    data_byte_size = 32


class BooleanEncoder(Fixed32ByteSizeEncoder):
    value_bit_size = 8
    is_big_endian = True

    @classmethod
    def validate_value(cls, value: Any) -> None:
        if not is_boolean(value):
            cls.invalidate_value(value)

    @classmethod
    def encode_fn(cls, value: bool) -> bytes:
        if value is True:
            return b"\x01"
        elif value is False:
            return b"\x00"
        else:
            raise ValueError("Invariant")

    @parse_type_str("bool")
    def from_type_str(cls, abi_type, registry):
        return cls()


class PackedBooleanEncoder(BooleanEncoder):
    data_byte_size = 1


class NumberEncoder(Fixed32ByteSizeEncoder):
    is_big_endian = True
    bounds_fn = None
    illegal_value_fn = None
    type_check_fn = None

    def validate(self) -> None:
        super().validate()

        if self.bounds_fn is None:
            raise ValueError("`bounds_fn` cannot be null")
        if self.type_check_fn is None:
            raise ValueError("`type_check_fn` cannot be null")

    def validate_value(self, value):
        type_check_fn = self.type_check_fn
        if type_check_fn is None:
            raise AssertionError("`type_check_fn` is None")
        if not type_check_fn(value):
            self.invalidate_value(value)

        illegal_value_fn = self.illegal_value_fn
        illegal_value = illegal_value_fn is not None and illegal_value_fn(value)
        if illegal_value:
            self.invalidate_value(value, exc=IllegalValue)

        lower_bound, upper_bound = self.bounds_fn(self.value_bit_size)
        if value < lower_bound or value > upper_bound:
            self.invalidate_value(
                value,
                exc=ValueOutOfBounds,
                msg=f"Cannot be encoded in {self.value_bit_size} bits. Must be bounded "
                f"between [{lower_bound}, {upper_bound}].",
            )


class UnsignedIntegerEncoder(NumberEncoder):
    encode_fn = staticmethod(int_to_big_endian)
    bounds_fn = staticmethod(compute_unsigned_integer_bounds)
    type_check_fn = staticmethod(is_integer)

    @parse_type_str("uint")
    def from_type_str(cls, abi_type, registry):
        return cls(value_bit_size=abi_type.sub)


encode_uint_256 = UnsignedIntegerEncoder(value_bit_size=256, data_byte_size=32)


class PackedUnsignedIntegerEncoder(UnsignedIntegerEncoder):
    @parse_type_str("uint")
    def from_type_str(cls, abi_type, registry):
        return cls(
            value_bit_size=abi_type.sub,
            data_byte_size=abi_type.sub // 8,
        )


class SignedIntegerEncoder(NumberEncoder):
    bounds_fn = staticmethod(compute_signed_integer_bounds)
    type_check_fn = staticmethod(is_integer)

    def encode_fn(self, value: int) -> bytes:
        return int_to_big_endian(value % (2**self.value_bit_size))

    def encode(self, value: int) -> bytes:
        self.validate_value(value)
        return encode_signed(value, self.encode_fn, self.data_byte_size)

    __call__ = encode

    @parse_type_str("int")
    def from_type_str(cls, abi_type, registry):
        return cls(value_bit_size=abi_type.sub)


class PackedSignedIntegerEncoder(SignedIntegerEncoder):
    @parse_type_str("int")
    def from_type_str(cls, abi_type, registry):
        return cls(
            value_bit_size=abi_type.sub,
            data_byte_size=abi_type.sub // 8,
        )


class BaseFixedEncoder(NumberEncoder):
    frac_places = None

    @staticmethod
    def type_check_fn(value):
        return is_number(value) and not isinstance(value, float)

    @staticmethod
    def illegal_value_fn(value):
        if isinstance(value, decimal.Decimal):
            return value.is_nan() or value.is_infinite()

        return False

    def validate_value(self, value):
        super().validate_value(value)

        with decimal.localcontext(abi_decimal_context):
            residue = value % (TEN**-self.frac_places)

        if residue > 0:
            self.invalidate_value(
                value,
                exc=IllegalValue,
                msg=f"residue {residue!r} outside allowed fractional precision of "
                f"{self.frac_places}",
            )

    def validate(self) -> None:
        super().validate()

        frac_places = self.frac_places
        if frac_places is None:
            raise ValueError("must specify `frac_places`")

        if frac_places <= 0 or frac_places > 80:
            raise ValueError("`frac_places` must be in range (0, 80]")


class UnsignedFixedEncoder(BaseFixedEncoder):
    def bounds_fn(self, value_bit_size):
        return compute_unsigned_fixed_bounds(self.value_bit_size, self.frac_places)

    def encode_fn(self, value):
        with decimal.localcontext(abi_decimal_context):
            scaled_value = value * TEN**self.frac_places
            integer_value = int(scaled_value)

        return int_to_big_endian(integer_value)

    @parse_type_str("ufixed")
    def from_type_str(cls, abi_type, registry):
        value_bit_size, frac_places = abi_type.sub

        return cls(
            value_bit_size=value_bit_size,
            frac_places=frac_places,
        )


class PackedUnsignedFixedEncoder(UnsignedFixedEncoder):
    @parse_type_str("ufixed")
    def from_type_str(cls, abi_type, registry):
        value_bit_size, frac_places = abi_type.sub

        return cls(
            value_bit_size=value_bit_size,
            data_byte_size=value_bit_size // 8,
            frac_places=frac_places,
        )


class SignedFixedEncoder(BaseFixedEncoder):
    def bounds_fn(self, value_bit_size):
        return compute_signed_fixed_bounds(self.value_bit_size, self.frac_places)

    def encode_fn(self, value):
        with decimal.localcontext(abi_decimal_context):
            scaled_value = value * TEN**self.frac_places
            integer_value = int(scaled_value)

        unsigned_integer_value = integer_value % (2**self.value_bit_size)

        return int_to_big_endian(unsigned_integer_value)

    def encode(self, value):
        self.validate_value(value)
        return encode_signed(value, self.encode_fn, self.data_byte_size)

    __call__ = encode

    @parse_type_str("fixed")
    def from_type_str(cls, abi_type, registry):
        value_bit_size, frac_places = abi_type.sub

        return cls(
            value_bit_size=value_bit_size,
            frac_places=frac_places,
        )


class PackedSignedFixedEncoder(SignedFixedEncoder):
    @parse_type_str("fixed")
    def from_type_str(cls, abi_type, registry):
        value_bit_size, frac_places = abi_type.sub

        return cls(
            value_bit_size=value_bit_size,
            data_byte_size=value_bit_size // 8,
            frac_places=frac_places,
        )


class AddressEncoder(Fixed32ByteSizeEncoder):
    value_bit_size = 20 * 8
    encode_fn = staticmethod(to_canonical_address)
    is_big_endian = True

    @classmethod
    def validate_value(cls, value: Any) -> None:
        if not is_address(value):
            cls.invalidate_value(value)

    def validate(self) -> None:
        super().validate()

        if self.value_bit_size != 20 * 8:
            raise ValueError("Addresses must be 160 bits in length")

    @parse_type_str("address")
    def from_type_str(cls, abi_type, registry):
        return cls()


class PackedAddressEncoder(AddressEncoder):
    data_byte_size = 20


class BytesEncoder(Fixed32ByteSizeEncoder):
    is_big_endian = False

    def validate_value(self, value: Any) -> None:
        if not is_bytes(value):
            self.invalidate_value(value)

        byte_size = self.value_bit_size // 8
        if len(value) > byte_size:
            self.invalidate_value(
                value,
                exc=ValueOutOfBounds,
                msg=f"exceeds total byte size for bytes{byte_size} encoding",
            )

    @staticmethod
    def encode_fn(value):
        return value

    @parse_type_str("bytes")
    def from_type_str(cls, abi_type, registry):
        return cls(value_bit_size=abi_type.sub * 8)


class PackedBytesEncoder(BytesEncoder):
    @parse_type_str("bytes")
    def from_type_str(cls, abi_type, registry):
        return cls(
            value_bit_size=abi_type.sub * 8,
            data_byte_size=abi_type.sub,
        )


class ByteStringEncoder(BaseEncoder):
    is_dynamic = True

    @classmethod
    def validate_value(cls, value: Any) -> None:
        if not is_bytes(value):
            cls.invalidate_value(value)

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        cls.validate_value(value)
        value_length = len(value)

        encoded_size = encode_uint_256(value_length)
        padded_value = zpad_right(value, ceil32(value_length))

        return encoded_size + padded_value

    __call__: ClassVar[Callable[[Type[Self], bytes], bytes]] = encode

    @parse_type_str("bytes")
    def from_type_str(cls, abi_type, registry):
        return cls()  # type: ignore [misc]


class PackedByteStringEncoder(ByteStringEncoder):
    is_dynamic = False

    @classmethod
    def encode(cls, value):
        cls.validate_value(value)
        return value

    __call__ = encode


class TextStringEncoder(BaseEncoder):
    is_dynamic = True

    @classmethod
    def validate_value(cls, value: Any) -> None:
        if not is_text(value):
            cls.invalidate_value(value)

    @classmethod
    def encode(cls, value: str) -> bytes:
        cls.validate_value(value)

        value_as_bytes = codecs.encode(value, "utf8")
        value_length = len(value_as_bytes)

        encoded_size = encode_uint_256(value_length)
        padded_value = zpad_right(value_as_bytes, ceil32(value_length))

        return encoded_size + padded_value

    __call__: ClassVar[Callable[[Type[Self], str], bytes]] = encode

    @parse_type_str("string")
    def from_type_str(cls, abi_type, registry):
        return cls()  # type: ignore [misc]


class PackedTextStringEncoder(TextStringEncoder):
    is_dynamic = False

    @classmethod
    def encode(cls, value: str) -> bytes:
        cls.validate_value(value)
        return codecs.encode(value, "utf8")

    __call__ = encode


class BaseArrayEncoder(BaseEncoder):
    item_encoder: BaseEncoder = None

    def validate(self) -> None:
        super().validate()

        if self.item_encoder is None:
            raise ValueError("`item_encoder` may not be none")

    def validate_value(self, value: Any) -> None:
        if not is_list_like(value):
            self.invalidate_value(
                value,
                msg="must be list-like such as array or tuple",
            )

        item_encoder = self.item_encoder
        for item in value:
            item_encoder.validate_value(item)

    def encode_elements(self, value: Sequence[Any]) -> bytes:
        self.validate_value(value)
        return encode_elements(self.item_encoder, value)

    @parse_type_str(with_arrlist=True)
    def from_type_str(cls, abi_type, registry):
        item_encoder = registry.get_encoder(abi_type.item_type.to_type_str())

        array_spec = abi_type.arrlist[-1]
        if len(array_spec) == 1:
            # If array dimension is fixed
            return SizedArrayEncoder(
                array_size=array_spec[0],
                item_encoder=item_encoder,
            )
        else:
            # If array dimension is dynamic
            return DynamicArrayEncoder(item_encoder=item_encoder)


class PackedArrayEncoder(BaseArrayEncoder):
    array_size = None

    def validate_value(self, value: Any) -> None:
        super().validate_value(value)

        array_size = self.array_size
        if array_size is not None and len(value) != array_size:
            self.invalidate_value(
                value,
                exc=ValueOutOfBounds,
                msg=f"value has {len(value)} items when {array_size} were expected",
            )

    def encode(self, value: Sequence[Any]) -> bytes:
        return encode_elements(self.item_encoder, value)

    __call__ = encode

    @parse_type_str(with_arrlist=True)
    def from_type_str(cls, abi_type, registry):
        item_encoder = registry.get_encoder(abi_type.item_type.to_type_str())

        array_spec = abi_type.arrlist[-1]
        if len(array_spec) == 1:
            return cls(
                array_size=array_spec[0],
                item_encoder=item_encoder,
            )
        else:
            return cls(item_encoder=item_encoder)


class SizedArrayEncoder(BaseArrayEncoder):
    array_size = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_dynamic = self.item_encoder.is_dynamic

    def validate(self) -> None:
        super().validate()

        if self.array_size is None:
            raise ValueError("`array_size` may not be none")

    def validate_value(self, value: Any) -> None:
        super().validate_value(value)

        if len(value) != self.array_size:
            self.invalidate_value(
                value,
                exc=ValueOutOfBounds,
                msg=f"value has {len(value)} items when {self.array_size} were "
                "expected",
            )

    def encode(self, value: Sequence[Any]) -> bytes:
        return encode_elements(self.item_encoder, value)

    __call__ = encode


class DynamicArrayEncoder(BaseArrayEncoder):
    is_dynamic = True

    def encode(self, value: Sequence[Any]) -> bytes:
        return encode_elements_dynamic(self.item_encoder, value)
