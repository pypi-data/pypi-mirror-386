import typing

import typing_extensions

from ..genome_instrumentation import HereditaryStratigraphicColumn
from ._col_from_packet import col_from_packet
from ._impl import DEFAULT_PACKET_NUM_STRATA_DEPOSITED_BYTE_WIDTH


def col_from_packet_buffer(
    packet_buffer: typing_extensions.Buffer,
    differentia_bit_width: int,
    stratum_retention_policy: typing.Callable,
    differentiae_byte_bit_order: typing.Literal["big", "little"] = "big",
    num_strata_deposited_byte_order: typing.Literal["big", "little"] = "big",
    num_strata_deposited_byte_width: int = (
        DEFAULT_PACKET_NUM_STRATA_DEPOSITED_BYTE_WIDTH
    ),
) -> HereditaryStratigraphicColumn:
    """Deserialize a `HereditaryStratigraphicColumn` from a buffer containing
    the differentia packet at the front, then stored differentia values.

    Use when buffer size exceeds packet size.

    See Also
    --------
    col_from_packet: use when buffer size equals packet size.
    """

    num_strata_deposited = int.from_bytes(
        packet_buffer[:num_strata_deposited_byte_width],
        byteorder=num_strata_deposited_byte_order,
        signed=False,
    )
    num_strata_retained = stratum_retention_policy.CalcNumStrataRetainedExact(
        num_strata_deposited,
    )
    packet_num_bits = (
        num_strata_deposited_byte_width * 8
        + num_strata_retained * differentia_bit_width
    )
    packet_num_bytes = (packet_num_bits + 7) // 8  # +7 rounds up
    assert packet_num_bytes <= len(packet_buffer)
    return col_from_packet(
        packet=packet_buffer[:packet_num_bytes],
        differentia_bit_width=differentia_bit_width,
        stratum_retention_policy=stratum_retention_policy,
        differentiae_byte_bit_order=differentiae_byte_bit_order,
        num_strata_deposited_byte_order=num_strata_deposited_byte_order,
        num_strata_deposited_byte_width=num_strata_deposited_byte_width,
    )
