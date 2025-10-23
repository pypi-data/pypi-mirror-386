"""Module for carbon related constraints."""

import numpy as np
import xarray as xr
from linopy import Constraint, Model
from xarray import Dataset


def add_carbon(
    model: Model,
    model_parameters: Dataset,
    annualised_totex_def: Constraint,
    operation_year_normalization: float,
) -> Model:
    """
    Add carbon-related components to the Linopy model.

    Including variables, constraints, and costs related to carbon emissions
    and taxation.

    Args:
        model (linopy.Model):
            The Linopy model to which carbon-related elements will be added.
        model_parameters (xarray.Dataset):
            Dataset containing energy system parameters, including carbon
            emission factors and cost details.
        annualised_totex_def (linopy.Constraint):
            Constraint defining annualised total expenditures (totex), which
            will be updated with carbon-specific costs.
        operation_year_normalization (float):
            Normalization factor for operational year durations.

    Returns:
        linopy.Model:
            The updated Linopy model with added carbon-related variables,
            costs, and constraints.

    Note:
        This function introduces the following elements into the model:

        **Variables**

        - *Operation*
            - ``operation_carbon_emissions``
                Represents carbon emissions at the operational level for each
                area, hour, and operational year.
            - ``operation_total_carbon_emissions``
                Represents total carbon emissions over time for each area,
                hour, and operational year.
            - ``operation_carbon_costs``
                Represents the cost associated with carbon emissions for each
                area and operational year.

        **Constraints**

        - *Operation*
            - ``operation_carbon_goal_constraint``
                Limits the total carbon emissions to a predefined carbon goal.
            - ``operation_carbon_emissions_def``
                Defines carbon emissions based on power production and emission
                factors.
            - ``operation_total_carbon_emissions_def``
                Ensures total carbon emissions correctly aggregate emissions
                over time.

        - *Costs*
            - ``operation_carbon_costs_def``
                Defines carbon costs as a function of carbon tax and emissions.

        These additions ensure that carbon constraints and costs are
        appropriately modeled, allowing for emissions regulation within the
        energy system. The model is enhanced to accurately capture carbon
        emissions behavior and its economic impact.
    """
    m = model
    p = model_parameters
    v = m.variables

    # ------------
    # Variables
    # ------------

    # Operation - Carbon

    operation_carbon_emissions = m.add_variables(
        name="operation_carbon_emissions", coords=[p.area, p.hour, p.year_op]
    )

    operation_total_carbon_emissions = m.add_variables(
        name="operation_total_carbon_emissions",
        coords=[p.area, p.hour, p.year_op],
    )

    # Costs - Carbon

    operation_carbon_costs = m.add_variables(
        name="operation_carbon_costs", lower=0, coords=[p.area, p.year_op]
    )

    # ------------------
    # Objective function
    # ------------------

    annualised_totex_def.lhs += operation_carbon_costs

    # --------------
    # Constraints
    # --------------

    # Operation - Carbon

    m.add_constraints(
        # Warning, timestep_duration is used here and for the total emission
        # as there is a "duplication"
        # of the variables operation_total_carbon_emissions and
        # operation_carbon_emissions
        +operation_year_normalization
        * operation_total_carbon_emissions.sum(["area", "hour"])
        <= p.carbon_goal,
        mask=np.isfinite(p.carbon_goal),
        name="operation_carbon_goal_constraint",
    )

    # Operation - Carbon intermediate variables

    operation_carbon_emissions_def = m.add_constraints(
        -operation_carbon_emissions
        + (v.operation_conversion_power * p.conversion_emission_factor).sum(
            ["conversion_tech"]
        )
        * p.time_step_duration
        == 0,
        name="operation_carbon_emissions_def",
    )

    operation_total_carbon_emissions_def = m.add_constraints(
        -operation_total_carbon_emissions
        + (v.operation_conversion_power * p.conversion_emission_factor).sum(
            ["conversion_tech"]
        )
        * p.time_step_duration
        == 0,
        name="operation_total_carbon_emissions_def",
    )

    if "net_import" in p.keys() and p.net_import:
        operation_carbon_emissions_def.lhs += (
            v.operation_net_import_import * p.net_import_emission_factor
        ).sum(["resource"]) * p.time_step_duration
        operation_total_carbon_emissions_def.lhs += (
            v.operation_net_import_import * p.net_import_total_emission_factor
        ).sum(["resource"]) * p.time_step_duration

    # Costs - Carbon

    m.add_constraints(
        -operation_carbon_costs
        # Warning, timestep_duration is used here and for the total costs as
        # there is a "duplication"
        # of the variables operation_total_carbon_emissions and
        # operation_carbon_emissions
        + operation_year_normalization
        * operation_carbon_emissions.sum("hour")
        * xr.where(
            cond=np.isfinite(p.carbon_tax),
            x=p.carbon_tax,
            y=0,
        )
        == 0,
        name="operation_carbon_costs_def",
    )

    return m
