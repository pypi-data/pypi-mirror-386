"""Gradient ribbon series for streamlit-lightweight-charts.

This module provides the GradientRibbonSeries class for creating ribbon charts
that display upper and lower bands with gradient fill areas based on gradient values.
"""

import math
from typing import List, Optional, Union

import pandas as pd

from streamlit_lightweight_charts_pro.charts.series.ribbon import RibbonSeries
from streamlit_lightweight_charts_pro.data.gradient_ribbon import GradientRibbonData
from streamlit_lightweight_charts_pro.type_definitions import ChartType
from streamlit_lightweight_charts_pro.utils import chainable_property


@chainable_property("gradient_start_color", str, validator="color")
@chainable_property("gradient_end_color", str, validator="color")
@chainable_property("normalize_gradients", bool)
class GradientRibbonSeries(RibbonSeries):
    """Gradient ribbon series for lightweight charts.

    This class represents a ribbon series that displays upper and lower bands
    with gradient fill areas based on gradient values. It extends RibbonSeries
    with gradient fill capabilities, allowing for dynamic color transitions
    based on data values.

    The GradientRibbonSeries supports various styling options including separate
    line styling for each band via LineOptions, and gradient color effects based
    on data values.

    Attributes:
        upper_line: LineOptions instance for upper band styling.
        lower_line: LineOptions instance for lower band styling.
        fill_visible: Whether to display the fill area.
        gradient_start_color: Starting color for gradient fills (minimum value).
        gradient_end_color: Ending color for gradient fills (maximum value).
        normalize_gradients: Whether to normalize gradient values to 0-1 range.
        price_lines: List of PriceLineOptions for price lines (set after construction)
        price_format: PriceFormatOptions for price formatting (set after construction)
        markers: List of markers to display on this series (set after construction)
    """

    DATA_CLASS = GradientRibbonData

    def __init__(
        self,
        data: Union[List[GradientRibbonData], pd.DataFrame, pd.Series],
        column_mapping: Optional[dict] = None,
        visible: bool = True,
        price_scale_id: str = "",
        pane_id: Optional[int] = 0,
        gradient_start_color: str = "#4CAF50",
        gradient_end_color: str = "#F44336",
        normalize_gradients: bool = False,
    ):
        """Initialize GradientRibbonSeries.

        Args:
            data: List of data points or DataFrame
            column_mapping: Column mapping for DataFrame conversion
            visible: Whether the series is visible
            price_scale_id: ID of the price scale
            pane_id: The pane index this series belongs to
            gradient_start_color: Starting color for gradient fills
            gradient_end_color: Ending color for gradient fills
            normalize_gradients: Whether to normalize gradient values to 0-1 range
        """
        super().__init__(
            data=data,
            column_mapping=column_mapping,
            visible=visible,
            price_scale_id=price_scale_id,
            pane_id=pane_id,
        )

        # Initialize gradient-specific properties
        self._gradient_start_color = gradient_start_color
        self._gradient_end_color = gradient_end_color
        self._normalize_gradients = normalize_gradients
        self._gradient_bounds: Optional[tuple[float, float]] = None

    @property
    def chart_type(self) -> ChartType:
        """Get the chart type for this series."""
        return ChartType.GRADIENT_RIBBON

    def _calculate_gradient_bounds(self) -> None:
        """Calculate min/max gradient values for normalization with optimized performance."""
        if not self.data:
            self._gradient_bounds = None
            return

        # Ultra-optimized single-pass min/max tracking
        min_grad = float("inf")
        max_grad = float("-inf")
        valid_count = 0

        # Single pass with inline min/max tracking - no list building
        for data_point in self.data:
            # Type check: ensure data point has gradient attribute
            if not hasattr(data_point, "gradient"):
                continue
            gradient = data_point.gradient  # type: ignore[attr-defined]
            if (
                gradient is not None
                and isinstance(gradient, (int, float))
                and not math.isnan(gradient)  # Not NaN
                and gradient != float("inf")
                and gradient != float("-inf")
            ):
                # Update min/max inline - no list operations
                min_grad = min(min_grad, gradient)
                max_grad = max(max_grad, gradient)
                valid_count += 1
                continue

        # Set bounds efficiently - only if we found valid values
        if valid_count > 0:
            self._gradient_bounds = (min_grad, max_grad)
        else:
            self._gradient_bounds = None

    def asdict(self):
        """Override to include normalized gradients and exclude inherited fill property."""
        data_dict = super().asdict()

        # Remove inherited fill property - gradient ribbon uses gradientStartColor/gradientEndColor instead
        data_dict.get("options", {}).pop("fill", None)

        if self._normalize_gradients:
            # Calculate bounds if not already calculated
            if self._gradient_bounds is None:
                self._calculate_gradient_bounds()

            if self._gradient_bounds:
                min_grad, max_grad = self._gradient_bounds
                range_grad = max_grad - min_grad

                if range_grad > 0:  # Avoid division by zero
                    # Ultra-optimized normalization with minimal function calls
                    data_items = data_dict["data"]
                    range_grad_inv = 1.0 / range_grad  # Pre-calculate inverse

                    for item in data_items:  # Remove enumerate for speed
                        gradient = item.get("gradient")
                        if gradient is not None:
                            # Since we already validated in _calculate_gradient_bounds,
                            # we can trust the gradient values here
                            try:
                                # Use pre-calculated inverse for faster division
                                normalized = (gradient - min_grad) * range_grad_inv
                                # Fast clamping using conditional expression
                                item["gradient"] = (
                                    0.0 if normalized < 0.0 else (min(normalized, 1.0))
                                )
                            except (TypeError, ValueError):
                                item.pop("gradient", None)

        return data_dict
