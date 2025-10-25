import itertools
from decimal import Decimal
from typing import Sequence

# Import the Rust implementation
try:
    from . import spot_planner as _rust_module

    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False


def calculate_dynamic_consecutive_selections(
    min_consecutive_periods: int,
    max_consecutive_periods: int,
    min_selections: int,
    total_prices: int,
    max_gap_between_periods: int,
) -> int:
    """
    Calculate dynamic consecutive_selections based on heating requirements.

    This function calculates the actual consecutive selections needed based on:
    - min_consecutive_periods: Minimum allowed consecutive selections
    - max_consecutive_periods: Maximum allowed consecutive selections
    - min_selections: Total selections needed (correlates with historical heating duration)
    - total_prices: Total number of price periods available
    - max_gap_between_periods: Maximum gap between heating periods

    Args:
        min_consecutive_periods: Minimum allowed consecutive selections
        max_consecutive_periods: Maximum allowed consecutive selections
        min_selections: Total selections needed (correlates with historical heating duration)
        total_prices: Total number of price periods available
        max_gap_between_periods: Maximum gap between heating periods

    Returns:
        Calculated consecutive_selections value between min and max
    """
    # Calculate percentage of min_selections relative to total prices
    if total_prices == 0:
        return min_consecutive_periods
    min_selections_percentage = min_selections / total_prices

    # Base calculation based on percentage rules:
    # - < 25% of total prices: use min_consecutive_periods
    # - > 75% of total prices: use max_consecutive_periods
    # - Between 25-75%: linear interpolation
    if min_selections_percentage <= 0.25:
        base_consecutive = min_consecutive_periods
    elif min_selections_percentage >= 0.75:
        base_consecutive = max_consecutive_periods
    else:
        # Linear interpolation between 25% and 75%
        # Map 0.25-0.75 to 0.0-1.0 for interpolation
        interpolation_factor = (min_selections_percentage - 0.25) / (0.75 - 0.25)
        base_consecutive = int(
            min_consecutive_periods
            + interpolation_factor
            * (max_consecutive_periods - min_consecutive_periods)
        )

    # Adjust based on gap between periods
    # Larger gaps mean more consecutive heating needed
    # Scale gap adjustment: larger gaps push toward max_consecutive_periods
    gap_factor = min(max_gap_between_periods / 10.0, 1.0)  # Normalize gap to 0-1
    gap_adjustment = int(
        gap_factor * (max_consecutive_periods - min_consecutive_periods)
    )

    # Final calculation: base + gap adjustment
    dynamic_consecutive = base_consecutive + gap_adjustment

    # Ensure result is within bounds
    return max(
        min_consecutive_periods, min(dynamic_consecutive, max_consecutive_periods)
    )


def _is_valid_combination(
    combination: tuple[tuple[int, Decimal], ...],
    min_consecutive_periods: int,
    max_gap_between_periods: int,
    max_gap_from_start: int,
    full_length: int,
) -> bool:
    if not combination:
        return False

    # Items are already sorted, so indices are in order
    indices = [index for index, _ in combination]

    # Check max_gap_from_start first (fastest check)
    if indices[0] > max_gap_from_start:
        return False

    # Check start gap
    if indices[0] > max_gap_between_periods:
        return False

    # Check gaps between consecutive indices and min_consecutive_periods in single pass
    block_length = 1
    for i in range(1, len(indices)):
        gap = indices[i] - indices[i - 1] - 1
        if gap > max_gap_between_periods:
            return False

        if indices[i] == indices[i - 1] + 1:
            block_length += 1
        else:
            if block_length < min_consecutive_periods:
                return False
            block_length = 1

    # Check last block min_consecutive_periods
    if block_length < min_consecutive_periods:
        return False

    # Check end gap
    if (full_length - 1 - indices[-1]) > max_gap_between_periods:
        return False

    return True


def _get_combination_cost(combination: tuple[tuple[int, Decimal], ...]) -> Decimal:
    return sum(price for _, price in combination) or Decimal("0")


def _group_consecutive_items(
    items: Sequence[tuple[int, Decimal]],
) -> list[list[tuple[int, Decimal]]]:
    """Group cheap items into consecutive runs."""
    if not items:
        return []

    groups = []
    current_group = [items[0]]

    for i in range(1, len(items)):
        if items[i][0] == items[i - 1][0] + 1:
            current_group.append(items[i])
        else:
            groups.append(current_group)
            current_group = [items[i]]
    groups.append(current_group)

    return groups


def _check_consecutive_runs(
    indices: list[int], min_consecutive_periods: int
) -> bool:
    """Check if all consecutive runs in indices meet the minimum length requirement.

    Args:
        indices: Sorted list of indices
        min_consecutive_periods: Minimum required length for each consecutive run

    Returns:
        True if all runs meet the requirement, False otherwise
    """
    if not indices:
        return False

    if len(indices) == 1:
        return min_consecutive_periods <= 1

    # Count consecutive runs
    run_length = 1
    for i in range(1, len(indices)):
        if indices[i] == indices[i - 1] + 1:
            run_length += 1
        else:
            # End of a run - check if it meets minimum
            if run_length < min_consecutive_periods:
                return False
            run_length = 1

    # Check the last run
    if run_length < min_consecutive_periods:
        return False

    return True


def _get_cheapest_periods_python(
    prices: Sequence[Decimal],
    low_price_threshold: Decimal,
    min_selections: int,
    min_consecutive_periods: int,
    max_gap_between_periods: int,
    max_gap_from_start: int,
    aggressive: bool = True,
) -> list[int]:
    price_items: tuple[tuple[int, Decimal], ...] = tuple(enumerate(prices))
    cheap_items: tuple[tuple[int, Decimal], ...] = tuple(
        (index, price) for index, price in price_items if price <= low_price_threshold
    )
    # Calculate actual consecutive selections based on cheap percentage
    if len(price_items) == 0:
        return []
    cheap_percentage = len(cheap_items) / len(price_items)
    if cheap_percentage > 0.8:
        actual_consecutive_selections = min_consecutive_periods
    else:
        actual_consecutive_selections = calculate_dynamic_consecutive_selections(
            min_consecutive_periods,
            8,
            min_selections,
            len(price_items),
            max_gap_between_periods,
        )

    # Special case: if min_selections equals total items, return all of them
    if min_selections == len(price_items):
        return list(range(len(price_items)))

    # Special case: if all items are below threshold, return all of them
    if len(cheap_items) == len(price_items):
        return list(range(len(price_items)))

    # Choose algorithm based on aggressive parameter
    if aggressive:
        # Aggressive mode: minimize average cost (current behavior)
        return _get_cheapest_periods_aggressive_python(
            price_items,
            cheap_items,
            min_selections,
            actual_consecutive_selections,
            max_gap_between_periods,
            max_gap_from_start,
        )
    else:
        # Conservative mode: maximize number of cheap items
        return _get_cheapest_periods_conservative_python(
            price_items,
            cheap_items,
            min_selections,
            actual_consecutive_selections,
            max_gap_between_periods,
            max_gap_from_start,
        )


def _get_cheapest_periods_aggressive_python(
    price_items: tuple[tuple[int, Decimal], ...],
    cheap_items: tuple[tuple[int, Decimal], ...],
    min_selections: int,
    actual_consecutive_selections: int,
    max_gap_between_periods: int,
    max_gap_from_start: int,
) -> list[int]:
    # Generate all combinations and find the best one after merging with cheap items
    best_result = []
    best_cost = _get_combination_cost(price_items)
    found = False

    # Try combinations starting from min_selections
    for current_count in range(min_selections, len(price_items) + 1):
        for price_item_combination in itertools.combinations(
            price_items, current_count
        ):
            if not _is_valid_combination(
                price_item_combination,
                actual_consecutive_selections,
                max_gap_between_periods,
                max_gap_from_start,
                len(price_items),
            ):
                continue

            # Start with this combination
            result_indices = [i for i, _ in price_item_combination]
            existing_indices = set(result_indices)

            # Try every combination of cheap items that are not already included
            available_cheap_items = [
                item for item in cheap_items if item[0] not in existing_indices
            ]

            # Group cheap items into consecutive runs for efficiency
            cheap_groups = _group_consecutive_items(available_cheap_items)

            # Try every combination of consecutive groups (2^n instead of 2^20)
            best_merged_result = result_indices.copy()
            best_merged_cost = _get_combination_cost(
                [(i, price_items[i][1]) for i in result_indices]
            )

            for group_mask in range(1, 2 ** len(cheap_groups)):  # Skip empty selection
                merged_indices = result_indices.copy()

                # Add items from selected groups
                for group_idx, group in enumerate(cheap_groups):
                    if group_mask & (1 << group_idx):
                        for index, _ in group:
                            merged_indices.append(index)

                merged_indices.sort()

                # Check if merged result maintains valid consecutive runs
                if _check_consecutive_runs(
                    merged_indices, actual_consecutive_selections
                ):
                    # Calculate average cost of this merged result
                    merged_cost = sum(price_items[i][1] for i in merged_indices)
                    merged_avg_cost = merged_cost / len(merged_indices)

                    # Calculate average cost of current best
                    best_avg_cost = best_merged_cost / len(best_merged_result)

                    # Keep the result with lowest average cost
                    if merged_avg_cost < best_avg_cost:
                        best_merged_result = merged_indices
                        best_merged_cost = merged_cost

            # Use the best merged result
            total_cost = best_merged_cost
            avg_cost = total_cost / len(best_merged_result)

            # Compare average costs, not total costs
            best_avg_cost = (
                best_cost / len(best_result) if best_result else float("inf")
            )

            if avg_cost < best_avg_cost:
                best_result = best_merged_result
                best_cost = total_cost
                found = True

        # If we found a valid combination at this size, don't try larger sizes
        if found:
            break

    if not found:
        raise ValueError(
            f"No valid combination found that satisfies the constraints for {len(price_items)} items"
        )

    return best_result


def _get_cheapest_periods_conservative_python(
    price_items: tuple[tuple[int, Decimal], ...],
    cheap_items: tuple[tuple[int, Decimal], ...],
    min_selections: int,
    actual_consecutive_selections: int,
    max_gap_between_periods: int,
    max_gap_from_start: int,
) -> list[int]:
    """Conservative algorithm: maximize number of cheap items while respecting constraints."""
    # First, try to use as many cheap items as possible
    best_result = []
    found = False

    # Try combinations starting from min_selections, prioritizing cheap items
    for current_count in range(min_selections, len(price_items) + 1):
        # First try combinations that include as many cheap items as possible
        cheap_indices = [i for i, _ in cheap_items]

        # Try all combinations of cheap items first (from most to least)
        for cheap_count in range(len(cheap_indices), 0, -1):
            if cheap_count < min_selections:
                continue

            for cheap_combination in itertools.combinations(cheap_indices, cheap_count):
                # Convert to price_item format for validation
                cheap_price_items = [(i, price_items[i][1]) for i in cheap_combination]

                if not _is_valid_combination(
                    cheap_price_items,
                    actual_consecutive_selections,
                    max_gap_between_periods,
                    max_gap_from_start,
                    len(price_items),
                ):
                    continue

                # If we need more items, try to add non-cheap items
                if cheap_count < current_count:
                    remaining_needed = current_count - cheap_count
                    non_cheap_indices = [
                        i for i in range(len(price_items)) if i not in cheap_indices
                    ]

                    for non_cheap_combination in itertools.combinations(
                        non_cheap_indices, min(remaining_needed, len(non_cheap_indices))
                    ):
                        combined_indices = list(cheap_combination) + list(
                            non_cheap_combination
                        )
                        combined_indices.sort()

                        # Convert to price_item format for validation
                        combined_price_items = [
                            (i, price_items[i][1]) for i in combined_indices
                        ]

                        if _is_valid_combination(
                            combined_price_items,
                            actual_consecutive_selections,
                            max_gap_between_periods,
                            max_gap_from_start,
                            len(price_items),
                        ):
                            best_result = combined_indices
                            found = True
                            break
                else:
                    # We have enough cheap items
                    best_result = list(cheap_combination)
                    found = True
                    break

                if found:
                    break

            if found:
                break

        if found:
            break

    if not found:
        raise ValueError(
            f"No valid combination found that satisfies the constraints for {len(price_items)} items"
        )

    return best_result


def get_cheapest_periods(
    prices: Sequence[Decimal],
    low_price_threshold: Decimal,
    min_selections: int,
    min_consecutive_periods: int,
    max_consecutive_periods: int,
    max_gap_between_periods: int = 0,
    max_gap_from_start: int = 0,
    aggressive: bool = True,
) -> list[int]:
    """
    Find optimal periods in a price sequence based on cost and timing constraints.

    This algorithm selects periods (indices) from a price sequence to minimize cost
    while satisfying various timing constraints. The algorithm prioritizes periods
    with prices at or below the threshold, but still respects all constraints.

    Args:
        prices: Sequence of prices for each period. Each element represents the
               price for one time period (e.g., hourly, 15-minute intervals).
        low_price_threshold: Price threshold below/equal to which periods are
                           preferentially selected. Periods with price <= threshold
                           will be included if they can form valid consecutive runs
                           meeting the consecutive_selections constraint.
        min_selections: Desired minimum number of periods to select. If no valid
                       combination is found, this will be incremented by 1 until
                       a valid solution is found.
        min_consecutive_periods: HARD CONSTRAINT - minimum consecutive periods always
                                required for effective operation. This is enforced as a
                                minimum for every consecutive block.
        max_consecutive_periods: Maximum consecutive periods that may be needed (e.g.,
                                after long idle time or adverse conditions). NOT a hard
                                limit - actual consecutive periods can exceed this value.
                                Used only for dynamic calculation of required consecutive periods.
        max_gap_between_periods: Maximum number of periods allowed between selected
                               periods. Controls the maximum downtime between operating
                               periods. Set to 0 to require consecutive selections only.
        max_gap_from_start: Maximum number of periods from the beginning before the
                          first selection must occur. Controls how long we can wait
                          before starting operations.

    Returns:
        List of indices representing the selected periods, sorted by index.
        The indices correspond to positions in the input prices sequence.

    Raises:
        ValueError: If the input parameters are invalid or no valid combination
                   can be found that satisfies all constraints.

    Examples:
        >>> prices = [Decimal('0.05'), Decimal('0.08'), Decimal('0.12'), Decimal('0.06')]
        >>> get_cheapest_periods(prices, Decimal('0.10'), 2, 1, 3, 1, 1)
        [0, 1, 3]  # Selects periods 0, 1, 3 (all <= 0.10 and form valid runs)

        >>> # Dynamic calculation based on min_selections percentage and gaps
        >>> get_cheapest_periods(prices, Decimal('0.10'), 6, 2, 5, 3, 2)
        [0, 1, 3]  # consecutive_selections calculated dynamically between 2-5

    Note:
        The algorithm uses adaptive retry logic:
        1. Calculate dynamic consecutive requirements based on min/max bounds
        2. Find cheapest main combination that meets constraints
        3. Try adding cheap items to that combination
        4. If no valid solution found, increment min_selections and retry

        The actual consecutive_selections value is calculated dynamically:
        - If min_selections < 25% of total prices: use min_consecutive_periods
        - If min_selections > 75% of total prices: use max_consecutive_periods
        - Between 25-75%: linear interpolation between min and max
        - Larger gaps push the result closer to max_consecutive_periods
    """
    # Calculate dynamic consecutive_selections based on min/max bounds
    actual_consecutive_selections = calculate_dynamic_consecutive_selections(
        min_consecutive_periods=min_consecutive_periods,
        max_consecutive_periods=max_consecutive_periods,
        min_selections=min_selections,
        total_prices=len(prices),
        max_gap_between_periods=max_gap_between_periods,
    )

    # Validate input parameters before calling either implementation
    if not prices:
        raise ValueError("prices cannot be empty")

    if len(prices) > 28:
        raise ValueError("prices cannot contain more than 28 items")

    if min_selections <= 0:
        raise ValueError("min_selections must be greater than 0")

    if min_selections > len(prices):
        raise ValueError("min_selections cannot be greater than total number of items")

    if min_consecutive_periods <= 0:
        raise ValueError("min_consecutive_periods must be greater than 0")

    if max_consecutive_periods <= 0:
        raise ValueError("max_consecutive_periods must be greater than 0")

    if min_consecutive_periods > min_selections:
        raise ValueError(
            "min_consecutive_periods cannot be greater than min_selections"
        )

    if min_consecutive_periods > max_consecutive_periods:
        raise ValueError(
            "min_consecutive_periods cannot be greater than max_consecutive_periods"
        )

    # Note: actual_consecutive_selections can be greater than min_selections
    # because consecutive_selections is per-block minimum, while min_selections is total minimum

    if max_gap_between_periods < 0:
        raise ValueError("max_gap_between_periods must be greater than or equal to 0")

    if max_gap_from_start < 0:
        raise ValueError("max_gap_from_start must be greater than or equal to 0")

    if max_gap_from_start > max_gap_between_periods:
        raise ValueError(
            "max_gap_from_start must be less than or equal to max_gap_between_periods"
        )

    if _RUST_AVAILABLE:
        # Use Rust implementation - convert Decimal objects to strings
        prices_str = [str(price) for price in prices]
        low_price_threshold_str = str(low_price_threshold)
        return _rust_module.get_cheapest_periods(
            prices_str,
            low_price_threshold_str,
            min_selections,
            min_consecutive_periods,
            max_consecutive_periods,
            max_gap_between_periods,
            max_gap_from_start,
            aggressive,
        )
    else:
        # Fallback to Python implementation
        return _get_cheapest_periods_python(
            prices,
            low_price_threshold,
            min_selections,
            actual_consecutive_selections,
            max_gap_between_periods,
            max_gap_from_start,
            aggressive,
        )
