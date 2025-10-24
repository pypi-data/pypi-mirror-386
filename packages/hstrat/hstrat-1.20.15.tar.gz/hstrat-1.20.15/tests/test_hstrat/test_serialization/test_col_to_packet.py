import pytest
import typing_extensions

from hstrat import genome_instrumentation, hstrat


@pytest.mark.parametrize(
    "impl",
    [genome_instrumentation.HereditaryStratigraphicColumn],
    # TODO
    # genome_instrumentation._HereditaryStratigraphicColumn_.impls,
)
@pytest.mark.parametrize(
    "retention_policy",
    [
        hstrat.perfect_resolution_algo.Policy(),
        hstrat.nominal_resolution_algo.Policy(),
        hstrat.fixed_resolution_algo.Policy(fixed_resolution=10),
    ],
)
@pytest.mark.parametrize(
    "ordered_store",
    [
        hstrat.HereditaryStratumOrderedStoreDict,
        hstrat.HereditaryStratumOrderedStoreList,
        hstrat.HereditaryStratumOrderedStoreTree,
        None,
    ],
)
@pytest.mark.parametrize("always_store_rank_in_stratum", [True, False])
@pytest.mark.parametrize(
    "num_deposits",
    [0, 1, 6, 8, 64],
)
@pytest.mark.parametrize(
    "differentia_bit_width",
    [1, 8, 16, 32, 64],
)
def test_col_to_packet(
    impl,
    retention_policy,
    ordered_store,
    always_store_rank_in_stratum,
    num_deposits,
    differentia_bit_width,
    caplog,
):
    column = impl(
        stratum_ordered_store=ordered_store,
        stratum_retention_policy=retention_policy,
        stratum_differentia_bit_width=differentia_bit_width,
        always_store_rank_in_stratum=always_store_rank_in_stratum,
    )
    for __ in range(num_deposits):
        column.DepositStratum()

    packet = hstrat.col_to_packet(column)
    assert packet == hstrat.col_to_packet(column)
    assert packet != hstrat.col_to_packet(
        column, num_strata_deposited_byte_order="little"
    )
    assert packet != hstrat.col_to_packet(
        column, num_strata_deposited_byte_width=42
    )
    assert isinstance(packet, typing_extensions.Buffer)
    assert len(packet) <= (
        (column.GetNumStrataRetained() * differentia_bit_width + 7) // 8
        + 1  # possible num padding bits header byte
        + 4
    )


@pytest.mark.parametrize(
    "impl",
    [genome_instrumentation.HereditaryStratigraphicColumn],
    # TODO
    # genome_instrumentation._HereditaryStratigraphicColumn_.impls,
)
@pytest.mark.parametrize("byte_order", ["big", "little"])
@pytest.mark.parametrize(
    "retention_policy",
    [
        hstrat.perfect_resolution_algo.Policy(),
        hstrat.nominal_resolution_algo.Policy(),
        hstrat.fixed_resolution_algo.Policy(fixed_resolution=10),
    ],
)
@pytest.mark.parametrize(
    "ordered_store",
    [
        hstrat.HereditaryStratumOrderedStoreDict,
        hstrat.HereditaryStratumOrderedStoreList,
        hstrat.HereditaryStratumOrderedStoreTree,
        None,
    ],
)
@pytest.mark.parametrize("always_store_rank_in_stratum", [True, False])
@pytest.mark.parametrize(
    "num_deposits",
    [0, 1, 6, 8, 64],
)
@pytest.mark.parametrize(
    "differentia_bit_width",
    [1, 8, 16, 32, 64],
)
def test_col_to_packet_then_from_packet(
    impl,
    byte_order,
    retention_policy,
    ordered_store,
    always_store_rank_in_stratum,
    num_deposits,
    differentia_bit_width,
    caplog,
):
    column = impl(
        stratum_ordered_store=ordered_store,
        stratum_retention_policy=retention_policy,
        stratum_differentia_bit_width=differentia_bit_width,
        always_store_rank_in_stratum=always_store_rank_in_stratum,
    )
    for __ in range(num_deposits):
        column.DepositStratum()

    assert hstrat.col_to_packet(column) == hstrat.col_to_packet(column)
    packet = hstrat.col_to_packet(
        column, num_strata_deposited_byte_order=byte_order
    )
    reconstituted = hstrat.col_from_packet(
        packet,
        differentia_bit_width=differentia_bit_width,
        differentiae_byte_bit_order="big",
        num_strata_deposited_byte_order=byte_order,
        stratum_retention_policy=retention_policy,
    )
    if column.GetNumStrataRetained() >= 20:
        assert reconstituted != hstrat.col_from_packet(
            packet,
            differentia_bit_width=differentia_bit_width,
            differentiae_byte_bit_order="little",
            num_strata_deposited_byte_order=byte_order,
            stratum_retention_policy=retention_policy,
        )
    assert reconstituted._ShouldOmitStratumDepositionRank()
    if (
        ordered_store == hstrat.HereditaryStratumOrderedStoreList
        and impl == genome_instrumentation.HereditaryStratigraphicColumn
        and not always_store_rank_in_stratum
    ):
        assert reconstituted == column
    else:
        target_records = hstrat.col_to_records(column)
        # always_store_rank_in_stratum setting is lost
        if "stratum_deposition_ranks" in target_records:
            del target_records["stratum_deposition_ranks"]
        assert hstrat.col_to_records(reconstituted) == target_records


@pytest.mark.parametrize(
    "impl",
    [genome_instrumentation.HereditaryStratigraphicColumn],
    # TODO
    # genome_instrumentation._HereditaryStratigraphicColumn_.impls,
)
@pytest.mark.parametrize(
    "retention_policy",
    [
        hstrat.perfect_resolution_algo.Policy(),
        hstrat.nominal_resolution_algo.Policy(),
        hstrat.fixed_resolution_algo.Policy(fixed_resolution=10),
    ],
)
@pytest.mark.parametrize(
    "ordered_store",
    [
        hstrat.HereditaryStratumOrderedStoreDict,
        hstrat.HereditaryStratumOrderedStoreList,
        hstrat.HereditaryStratumOrderedStoreTree,
        None,
    ],
)
@pytest.mark.parametrize("always_store_rank_in_stratum", [True, False])
@pytest.mark.parametrize(
    "num_deposits",
    [0, 1, 6, 8, 64],
)
@pytest.mark.parametrize(
    "differentia_bit_width",
    [1, 8, 16, 32, 64],
)
@pytest.mark.parametrize(
    "buffer_excess_bytes",
    [0, 1, 100],
)
@pytest.mark.parametrize("byte_order", ["big", "little"])
def test_col_to_packet_then_from_packet_buffer(
    impl,
    retention_policy,
    ordered_store,
    always_store_rank_in_stratum,
    num_deposits,
    differentia_bit_width,
    buffer_excess_bytes,
    byte_order,
    caplog,
):
    column = impl(
        stratum_ordered_store=ordered_store,
        stratum_retention_policy=retention_policy,
        stratum_differentia_bit_width=differentia_bit_width,
        always_store_rank_in_stratum=always_store_rank_in_stratum,
    )
    for __ in range(num_deposits):
        column.DepositStratum()

    assert hstrat.col_to_packet(column) == hstrat.col_to_packet(column)
    packet = hstrat.col_to_packet(
        column, num_strata_deposited_byte_order=byte_order
    )
    packet_buffer = bytearray(len(packet) + buffer_excess_bytes)
    packet_buffer[: len(packet)] = packet
    reconstituted = hstrat.col_from_packet_buffer(
        packet_buffer,
        differentiae_byte_bit_order="big",
        differentia_bit_width=differentia_bit_width,
        num_strata_deposited_byte_order=byte_order,
        stratum_retention_policy=retention_policy,
    )
    if column.GetNumStrataRetained() >= 20:
        assert reconstituted != hstrat.col_from_packet_buffer(
            packet_buffer,
            differentia_bit_width=differentia_bit_width,
            differentiae_byte_bit_order="little",
            num_strata_deposited_byte_order=byte_order,
            stratum_retention_policy=retention_policy,
        )
    assert reconstituted._ShouldOmitStratumDepositionRank()
    if (
        ordered_store == hstrat.HereditaryStratumOrderedStoreList
        and impl == genome_instrumentation.HereditaryStratigraphicColumn
        and not always_store_rank_in_stratum
    ):
        assert reconstituted == column
    else:
        target_records = hstrat.col_to_records(column)
        # always_store_rank_in_stratum setting is lost
        if "stratum_deposition_ranks" in target_records:
            del target_records["stratum_deposition_ranks"]
        assert hstrat.col_to_records(reconstituted) == target_records
