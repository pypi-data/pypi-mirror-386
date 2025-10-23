from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Final,
    Tuple,
)

from faster_eth_utils import (
    big_endian_to_int,
)

from faster_eth_abi.exceptions import (
    InsufficientDataBytes,
    InvalidPointer,
    NonEmptyPaddingBytes,
)
from faster_eth_abi.io import (
    BytesIO,
    ContextFramesBytesIO,
)

if TYPE_CHECKING:
    from .decoding import (
        BaseArrayDecoder,
        DynamicArrayDecoder,
        FixedByteSizeDecoder,
        HeadTailDecoder,
        SignedIntegerDecoder,
        SizedArrayDecoder,
        TupleDecoder,
    )


# Helpers
def decode_uint_256(stream: ContextFramesBytesIO) -> int:
    """
    This function is a faster version of decode_uint_256 in decoding.py.

    It recreates the logic from the UnsignedIntegerDecoder, but we can
    skip a lot because we know the value of many vars.
    """
    # read data from stream
    if len(data := stream.read(32)) == 32:
        return big_endian_to_int(data)  # type: ignore [no-any-return]
    raise InsufficientDataBytes(f"Tried to read 32 bytes, only got {len(data)} bytes.")


def get_value_byte_size(decoder: "FixedByteSizeDecoder") -> int:
    return decoder.value_bit_size // 8


# HeadTailDecoder
def decode_head_tail(self: "HeadTailDecoder", stream: ContextFramesBytesIO) -> Any:
    # Decode the offset and move the stream cursor forward 32 bytes
    start_pos = decode_uint_256(stream)
    # Jump ahead to the start of the value
    stream.push_frame(start_pos)

    # assertion check for mypy
    tail_decoder = self.tail_decoder
    if tail_decoder is None:
        raise AssertionError("`tail_decoder` is None")
    # Decode the value
    value = tail_decoder(stream)
    # Return the cursor
    stream.pop_frame()

    return value


# TupleDecoder
def decode_tuple(self: "TupleDecoder", stream: ContextFramesBytesIO) -> Tuple[Any, ...]:
    # NOTE: the original implementation would do this but it's
    # kinda wasteful, so we rebuilt the logic within this function
    # validate_pointers_tuple(self, stream)

    current_location = stream.tell()
    if self._no_head_tail:
        # TODO: if all(isinstance(d, TupleDecoder) for d in self._decoders)
        #           return tuple(decode_tuple(stream) for _ in range(len(self.decoders))
        #       and other types with compiled decode funcs
        return tuple(decoder(stream) for decoder in self.decoders)

    end_of_offsets = current_location + 32 * self.len_of_head
    total_stream_length = len(stream.getbuffer())
    items = []
    for decoder, is_head_tail in zip(self.decoders, self._is_head_tail):
        if is_head_tail:
            # the next 32 bytes are a pointer that we should validate
            # checkpoint the stream location so we can reset it after validation
            step_location = stream.tell()

            offset = decode_uint_256(stream)
            indicated_idx = current_location + offset
            if indicated_idx < end_of_offsets or indicated_idx >= total_stream_length:
                # the pointer is indicating its data is located either within the
                # offsets section of the stream or beyond the end of the stream,
                # both of which are invalid
                raise InvalidPointer(
                    "Invalid pointer in tuple at location "
                    f"{stream.tell() - 32} in payload"
                )

            # reset the stream so we can decode
            stream.seek(step_location)

        items.append(decoder(stream))

    # return the stream to its original location for actual decoding
    stream.seek(current_location)

    return tuple(items)


def validate_pointers_tuple(
    self: "TupleDecoder",
    stream: ContextFramesBytesIO,
) -> None:
    """
    Verify that all pointers point to a valid location in the stream.
    """
    current_location = stream.tell()
    if self._no_head_tail:
        for decoder in self.decoders:
            decoder(stream)
    else:
        end_of_offsets = current_location + 32 * self.len_of_head
        total_stream_length = len(stream.getbuffer())
        for decoder, is_head_tail in zip(self.decoders, self._is_head_tail):
            if not is_head_tail:
                # the next 32 bytes are not a pointer, so progress the stream per the decoder
                decoder(stream)
            else:
                # the next 32 bytes are a pointer
                offset = decode_uint_256(stream)
                indicated_idx = current_location + offset
                if (
                    indicated_idx < end_of_offsets
                    or indicated_idx >= total_stream_length
                ):
                    # the pointer is indicating its data is located either within the
                    # offsets section of the stream or beyond the end of the stream,
                    # both of which are invalid
                    raise InvalidPointer(
                        "Invalid pointer in tuple at location "
                        f"{stream.tell() - 32} in payload"
                    )
    # return the stream to its original location for actual decoding
    stream.seek(current_location)


# BaseArrayDecoder
def validate_pointers_array(
    self: "BaseArrayDecoder", stream: ContextFramesBytesIO, array_size: int
) -> None:
    """
    Verify that all pointers point to a valid location in the stream.
    """
    current_location = stream.tell()
    end_of_offsets = current_location + 32 * array_size
    total_stream_length = len(stream.getbuffer())
    for _ in range(array_size):
        offset = decode_uint_256(stream)
        indicated_idx = current_location + offset
        if indicated_idx < end_of_offsets or indicated_idx >= total_stream_length:
            # the pointer is indicating its data is located either within the
            # offsets section of the stream or beyond the end of the stream,
            # both of which are invalid
            raise InvalidPointer(
                "Invalid pointer in array at location "
                f"{stream.tell() - 32} in payload"
            )
    stream.seek(current_location)


# SizedArrayDecoder
def decode_sized_array(
    self: "SizedArrayDecoder", stream: ContextFramesBytesIO
) -> Tuple[Any, ...]:
    item_decoder = self.item_decoder
    if item_decoder is None:
        raise AssertionError("`item_decoder` is None")

    array_size = self.array_size
    self.validate_pointers(stream, array_size)
    return tuple(item_decoder(stream) for _ in range(array_size))


# DynamicArrayDecoder
def decode_dynamic_array(
    self: "DynamicArrayDecoder", stream: ContextFramesBytesIO
) -> Tuple[Any, ...]:
    array_size = decode_uint_256(stream)
    stream.push_frame(32)
    if self.item_decoder is None:
        raise AssertionError("`item_decoder` is None")

    self.validate_pointers(stream, array_size)
    item_decoder = self.item_decoder
    try:
        return tuple(item_decoder(stream) for _ in range(array_size))
    finally:
        stream.pop_frame()


# FixedByteSizeDecoder
def read_fixed_byte_size_data_from_stream(
    self: "FixedByteSizeDecoder",
    # NOTE: use BytesIO here so mypyc doesn't type-check
    # `stream` once we compile ContextFramesBytesIO.
    stream: BytesIO,
) -> bytes:
    data_byte_size = self.data_byte_size
    if len(data := stream.read(data_byte_size)) == data_byte_size:
        return data
    raise InsufficientDataBytes(
        f"Tried to read {data_byte_size} bytes, only got {len(data)} bytes."
    )


def split_data_and_padding_fixed_byte_size(
    self: "FixedByteSizeDecoder",
    raw_data: bytes,
) -> Tuple[bytes, bytes]:
    value_byte_size = get_value_byte_size(self)
    padding_size = self.data_byte_size - value_byte_size

    if self.is_big_endian:
        if padding_size == 0:
            return raw_data, b""
        padding_bytes = raw_data[:padding_size]
        data = raw_data[padding_size:]
    else:
        data = raw_data[:value_byte_size]
        padding_bytes = raw_data[value_byte_size:]

    return data, padding_bytes


def validate_padding_bytes_fixed_byte_size(
    self: "FixedByteSizeDecoder",
    value: Any,
    padding_bytes: bytes,
) -> None:
    if padding_bytes != get_expected_padding_bytes(self, b"\x00"):
        raise NonEmptyPaddingBytes(f"Padding bytes were not empty: {padding_bytes!r}")


_expected_padding_bytes_cache: Final[
    Dict["FixedByteSizeDecoder", Dict[bytes, bytes]]
] = {}


def get_expected_padding_bytes(self: "FixedByteSizeDecoder", chunk: bytes) -> bytes:
    instance_cache = _expected_padding_bytes_cache.setdefault(self, {})
    expected_padding_bytes = instance_cache.get(chunk)
    if expected_padding_bytes is None:
        value_byte_size = get_value_byte_size(self)
        padding_size = self.data_byte_size - value_byte_size
        expected_padding_bytes = chunk * padding_size
        instance_cache[chunk] = expected_padding_bytes
    return expected_padding_bytes


def validate_padding_bytes_signed_integer(
    self: "SignedIntegerDecoder",
    value: int,
    padding_bytes: bytes,
) -> None:
    if value >= 0:
        expected_padding_bytes = get_expected_padding_bytes(self, b"\x00")
    else:
        expected_padding_bytes = get_expected_padding_bytes(self, b"\xff")

    if padding_bytes != expected_padding_bytes:
        raise NonEmptyPaddingBytes(f"Padding bytes were not empty: {padding_bytes!r}")


# BooleanDecoder
def decoder_fn_boolean(data: bytes) -> bool:
    if data == b"\x00":
        return False
    elif data == b"\x01":
        return True
    raise NonEmptyPaddingBytes(f"Boolean must be either 0x0 or 0x1.  Got: {data!r}")
