import typing

from ...._detail import PolicyCouplerBase
from ..._PolicySpec import PolicySpec
from ..._impl import num_to_condemn


class GenDropRanks:
    """Functor to implement the recency-proportional resolution stratum
    retention policy, for use with HereditaryStratigraphicColumn.

    This functor enacts the recency-proportional resolution policy by
    specifying the set of strata ranks that should be purged from a hereditary
    stratigraphic column when the nth stratum is deposited.
    """

    def __init__(
        self: "GenDropRanks",
        policy_spec: typing.Optional[PolicySpec],
    ) -> None:
        pass

    def __eq__(self: "GenDropRanks", other: typing.Any) -> bool:
        return isinstance(other, self.__class__)

    def __call__(
        self: "GenDropRanks",
        policy: PolicyCouplerBase,
        num_stratum_depositions_completed: int,
        retained_ranks: typing.Optional[typing.Iterable[int]],
    ) -> typing.Iterator[int]:
        """Decide which strata within the stratagraphic column should be purged.

        Every time a new stratum is deposited, this method is called to
        determine which strata should be purged. All strata at ranks yielded
        from this functor are immediately purged from the column, meaning that
        for a stratum to persist it must not be yielded by this functor each
        and every time a new stratum is deposited.

        Parameters
        ----------
        policy: Policy
            Policy this functor enacts.
        num_stratum_depositions_completed : int
            The number of strata that have already been deposited, not
            including the latest stratum being deposited which prompted the
            current purge operation.
        retained_ranks : iterator over int
            An iterator over ranks of strata currently retained within the
            hereditary stratigraphic column. Not used in this functor.

        Returns
        -------
        iterator over int
            The ranks of strata that should be purged from the hereditary
            stratigraphic column at this deposition step.

        See Also
        --------
        recency_proportional_resolution_algo:
            For details on the rationale, implementation, and guarantees of the
            recency-proportional resolution stratum retention policy.
        """
        spec = policy.GetSpec()
        resolution = spec.GetRecencyProportionalResolution()
        num_to_condemn_ = num_to_condemn(
            resolution,
            num_stratum_depositions_completed,
        )

        for i in range(num_to_condemn_):
            factor = 2 * resolution + 1
            num_ranks_back = factor * (2**i)
            yield num_stratum_depositions_completed - num_ranks_back
