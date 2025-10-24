# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Fresh-Air Ventilation Schedule."""

from dataclasses import dataclass, field


@dataclass
class VentOperatingPeriod:
    schedule: "OpPhScheduleVentilation"
    period_operating_hours: float = 0.0  # hours/period
    period_operation_speed: float = 0.0  # % of peak design airflow

    @property
    def period_operating_percentage(self) -> float:
        return self.period_operating_hours / self.schedule.operating_hours

    @property
    def weighted_reduction_factor(self) -> float:
        return self.period_operating_percentage * self.period_operation_speed


@dataclass
class VentPeriods:
    schedule: "OpPhScheduleVentilation"

    high: VentOperatingPeriod = field(init=False)
    standard: VentOperatingPeriod = field(init=False)
    basic: VentOperatingPeriod = field(init=False)
    minimum: VentOperatingPeriod = field(init=False)

    def __post_init__(self):
        self.high = VentOperatingPeriod(schedule=self.schedule)
        self.standard = VentOperatingPeriod(schedule=self.schedule)
        self.basic = VentOperatingPeriod(schedule=self.schedule)
        self.minimum = VentOperatingPeriod(schedule=self.schedule)


@dataclass
class OpPhScheduleVentilation:
    """A Open-PH Schedule for the Ventilation."""

    id_num: int = 0
    name: str = "__unnamed_vent_schedule__"
    identifier: str = "_identifier_"
    operating_hours: float = 24.0
    operating_days: float = 7.0
    operating_weeks: float = 52.0
    holiday_days: float = 0.0

    operating_periods: VentPeriods = field(init=False)

    def __post_init__(self):
        self.operating_periods = VentPeriods(schedule=self)

    @property
    def off_hours_reduction_factor(self) -> float:
        """A reduction factor (0.0-1.0) accounting for the time the system is 'off'.

        PHPP V10 | Addl Vent | AQ56:AQ86

        =IF(AND(AU56,AV56),N56*O56/(24*7)*IF(ISNUMBER(($G$21-P56)/$G$21),($G$21-P56)/$G$21,1)*(Q56*R56+S56*T56+U56*V56),"")

        """
        hourly_reduction_factor = (self.operating_hours * self.operating_days) / (
            24 * 7
        )
        try:
            __heating_period_length__ = (
                0  # TODO: get heating period length from model / phpp....
            )
            holiday_reduction_factor = (
                __heating_period_length__
                - self.holiday_days / __heating_period_length__
            )
        except ZeroDivisionError:
            holiday_reduction_factor = 1.0

        return hourly_reduction_factor * holiday_reduction_factor

    @property
    def annual_average_reduction_factor(self) -> float:
        """A single annual average weighted reduction-factor incorporating all of the operating periods.

        PHPP V10 | Addl Vent | W56:W86

        =IF(AND(ISNUMBER(J56),ISNUMBER($AQ56),$D56>0),J56*$AQ56*$D56,"")

        Returns:

        """
        return (
            self.operating_periods.high.weighted_reduction_factor
            + self.operating_periods.standard.weighted_reduction_factor
            + self.operating_periods.basic.weighted_reduction_factor
            + self.operating_periods.minimum.weighted_reduction_factor
        ) * self.off_hours_reduction_factor
