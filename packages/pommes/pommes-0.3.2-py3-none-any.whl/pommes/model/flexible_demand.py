"""Module to write in model flexible demand related constraints."""

import numpy as np
import xarray as xr
from linopy import Constraint, Model
from xarray import Dataset


def add_flexibility(
    model: Model,
    model_parameters: Dataset,
    annualised_totex_def: Constraint,
    operation_year_normalization: float,
    operation_adequacy_constraint: Constraint,
) -> Model:
    """
    Add flexible demand components to the Linopy model.

    Including variables, costs, and constraints.

    Args:
        model (linopy.Model):
            The Linopy model to which conversion-related elements will be
            added.
        model_parameters (xarray.Dataset):
            Dataset containing energy system parameters, including conversion
            technology details, availability, ramping rates, and production
            limits.
        annualised_totex_def (linopy.Constraint):
            Constraint defining the annualised total expenditure (totex),
            which will be updated with conversion-specific costs.
        operation_year_normalization (float):
            Normalization factor for operational year durations.
        operation_adequacy_constraint (linopy.Constraint):
            Constraint defining operational adequacy, ensuring supply meets
            demand. This will be updated with conversion-related contributions.

    Returns:
        linopy.Model:
            The updated Linopy model with added conversion-related variables,
            costs, and constraints.

    Example:
        This function introduces the following key elements to the model:

        Variables:
        - ``operation_flexibility_demand``: Represents the demand
        resulting from flexibility activation
        - ``operation_flexibility_displaced_demand``: Represents the displaced demand resulting from flexibility
        activation
        - ``operation_flexibility_costs``: Represents the operational costs associated with the activation
            of flexibilities for each area, resource, and operational year.


        Constraints:
        - Operational demand limits based on user defined maximal and minimal values.
        - Ramp-up and ramp-down constraints for smooth power output changes.
        - Total energy demand is conserved over a period defined by the user.

    Note:
        This function introduces the following elements into the model:

        **Variables**

        - *Operation*
            - ``operation_flexibility_demand``
                Represents the demand resulting from flexibility activation


        - *Costs (intermediate variables)*:
            - ``operation_flexibility_costs``
                Represents the operational costs associated with the activation
                of flexibilities for each area, resource, and operational year.

        **Constraints**

            - *Operation*
                - ``operation_flexibility_demand_max``
                    Limits flexible demand scheduling to the defined maximal value
                - ``operation_flexibility_demand_min``
                    Limits flexible demand scheduling to the defined minimal value
                - ``operation_flexibility_demand_conservation``
                    Enforces the conservation of energy demand over a period of time.
                - ``operation_flexibility_demand_ramp_up_constraint``
                    Constrains the ramp-up rate of flexible demand.
                - ``operation_flexibility_demand_ramp_up_constraint``
                    Constrains the ramp-down rate of flexible demand.


                - *Intermediate variables definition*
                    - ``operation_conversion_power_capacity_def``
                        Defines the operational power capacity based on the
                        planned investments over the years.
                    - ``operation_conversion_net_generation_def``
                        Relates net generation to the power output and conversion
                        factor, ensuring consistent accounting.
                        :eq:`equation conversion net generation <conv-net-gen-def>`


            - *Costs*
                - ``operation_conversion_costs_def``
                    Defines operational costs as a function of variable costs
                    and flexible demand activation


        These additions ensure that the flexible demand is activated within
        feasible and efficient limits, respecting availability,
        ramping capabilities, and power capacity limits.
        The model is thereby enhanced to accurately simulate
        flexible demand behavior and costs.
    """


    m = model
    p = model_parameters

    flexibility_demand = p.flexibility_demand
    for dim in ["area","resource","year_op","hour"]:
        if dim not in flexibility_demand.dims:
            flexibility_demand = flexibility_demand.expand_dims(dim={dim: p[dim]})

    conservation_hrs = p.flexibility_conservation_hrs
    for dim in ["area","year_op","resource"]:
        if dim not in conservation_hrs.dims:
            conservation_hrs = conservation_hrs.expand_dims(dim={dim: p[dim]})


    # ------------
    # Variables
    # ------------

    operation_flexibility_demand = m.add_variables(
        name="operation_flexibility_demand",
        lower=0,
        coords=[p.area, p.resource, p.hour, p.year_op],
    )

    # --------------
    # Constraints
    # --------------
    #
    # Adequacy constraint

    operation_adequacy_constraint.lhs += -operation_flexibility_demand

    # Max and min demand constraints

    m.add_constraints(operation_flexibility_demand - p.flexibility_max_demand <= 0,
                      name="operation_flexibility_demand_max")

    m.add_constraints(operation_flexibility_demand - p.flexibility_min_demand >= 0,
                      name="operation_flexibility_demand_min")

    # Conservation constraint
    m.add_constraints(operation_flexibility_demand.sum("hour") - flexibility_demand.sum("hour") == 0,
                      name="operation_flexibility_demand_conservation"
    )



    for res in p.resource.values:
        for area in p.area.values:
            for year in p.year_op.values:
                cons_hr = conservation_hrs.sel(year_op=year, resource=res, area=area).values
                if cons_hr > 0:
                    hours = p.hour.values
                    hour_min = hours.min()
                    hour_max = hours.max()

                    # Calculate group labels relative to the minimum hour
                    hour_groups = (hours - hour_min) // cons_hr

                    # Filter to only include complete groups
                    max_complete_hour = (
                        hour_min + ((hour_max - hour_min) // cons_hr) * cons_hr
                    )
                    valid_mask = hours < max_complete_hour

                    # Create a DataArray with group labels
                    hour_group_da = xr.DataArray(
                        hour_groups, coords={"hour": hours}, dims=["hour"]
                    )

                    # Create constraint using groupby
                    flex_demand_sel = operation_flexibility_demand.sel(
                        resource=res, area=area, year_op=year
                    )
                    target_demand_sel = flexibility_demand.sel(
                        resource=res, area=area, year_op=year
                    )

                    # Apply mask and group by hour groups
                    constraint_lhs = flex_demand_sel.where(
                        valid_mask, drop=False
                    ).groupby(hour_group_da).sum(
                        "hour"
                    ) - target_demand_sel.where(
                        valid_mask, drop=False
                    ).groupby(hour_group_da).sum("hour")

                    m.add_constraints(
                        constraint_lhs == 0,
                        name=f"operation_flexibility_demand_conservation_{res}_{area}_{year}",
                    )

    # Ramp constraints
    m.add_constraints(
        (operation_flexibility_demand
        - operation_flexibility_demand.shift(hour=1)) / p.time_step_duration
        - p.flexibility_ramp_up * flexibility_demand
        <= 0,
        name="operation_flexibility_demand_ramp_up_constraint",
        mask=np.isfinite(p.flexibility_ramp_up) * (p.hour != p.hour[0]),
    )

    m.add_constraints(
        (operation_flexibility_demand.shift(hour=1)
        - operation_flexibility_demand) / p.time_step_duration
        -p.flexibility_ramp_down * flexibility_demand
        <= 0,
        name="operation_flexibility_demand_ramp_down_constraint",
        mask=np.isfinite(p.flexibility_ramp_down) * (p.hour != p.hour[0]),
    )

    # Costs - Flexible Demand

    operation_flexibility_displaced_demand = m.add_variables(
        name="operation_flexibility_displaced_demand",
        lower=0,
        coords=[p.area, p.resource, p.hour, p.year_op],
    )

    m.add_constraints(
        operation_flexibility_displaced_demand
        >= - operation_flexibility_demand + flexibility_demand,
        name="operation_flexibility_displaced_demand_def",
    )

    operation_flexibility_costs = m.add_variables(
        name="operation_flexibility_costs",
        coords=[p.area, p.resource, p.year_op],
    )

    m.add_constraints(
        operation_flexibility_costs
        == p.flexibility_variable_cost
        * operation_year_normalization
        * p.time_step_duration
        * operation_flexibility_displaced_demand.sum("hour"),
        name="operation_flexibility_costs_def",
        mask=p.flexibility_variable_cost.notnull(),
    )

    # ------------------
    # Objective function
    # ------------------

    annualised_totex_def.lhs += operation_flexibility_costs.sum(
        "resource"
    )


    return m