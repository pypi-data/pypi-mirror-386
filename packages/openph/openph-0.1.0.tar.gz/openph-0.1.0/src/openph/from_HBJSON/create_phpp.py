# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

import math

from PHX.model.components import PhxApertureElement, PhxComponentOpaque
from PHX.model.constructions import (
    PhxConstructionOpaque,
    PhxConstructionWindow,
    PhxWindowFrameElement,
)
from PHX.model.enums.hvac import PhxVentDuctType
from PHX.model.geometry import PhxPolygon, PhxPolygonRectangular
from PHX.model.hvac.ducting import PhxDuctElement
from PHX.model.hvac.ventilation import AnyPhxVentilation
from PHX.model.loads.ventilation import PhxLoadVentilation
from PHX.model.phx_site import PhxClimatePeakLoad
from PHX.model.project import PhxVariant
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.spaces import PhxSpace

from openph.model.areas import OpPhAreas
from openph.model.climate import (
    OpPhClimate,
    OpPhClimateCalcPeriod,
    OpPhClimatePeakCoolingLoad,
    OpPhClimatePeakHeatingLoad,
)
from openph.model.components import OpPhConstructionCollection
from openph.model.constructions import (
    OpPhConstructionAperture,
    OpPhConstructionOpaque,
    OpPhGlazing,
    OpPhWindowFrameElement,
)
from openph.model.enums import ComponentExposureExterior, ComponentFaceType
from openph.model.envelope import OpPhApertureSurface, OpPhOpaqueSurface
from openph.model.hvac.hvac import OpPhHVAC
from openph.model.hvac.ventilation_device import (
    OpPhDuct,
    OpPhDuctType,
    OpPhVentilationDeviceDucting,
)
from openph.model.hvac.ventilation_system import (
    OpPhVentilationDevice,
    OpPhVentilationSystem,
)
from openph.model.loads.infiltration import OpPhInfiltration
from openph.model.loads.ventilation import OpPhLoadVentilation
from openph.model.rooms import OpPhRoom, OpPhRooms
from openph.model.schedules.collection import OpPhScheduleCollection
from openph.model.schedules.ventilation import OpPhScheduleVentilation
from openph.phpp import OpPhPHPP

# ----------------------------------------------------------------------------------------------------------------------
# -- Errors


class VentilationDuctError(Exception):
    def __init__(self, _ducts: list[PhxDuctElement], _duct_type: str):
        self.msg = f"\nError: There are {len(_ducts)} {_duct_type} ducts assigned to the Ventilator. Expected 1?"
        super().__init__(self.msg)


# ----------------------------------------------------------------------------------------------------------------------
# -- Climate


def create_ph_energy_peak_heating_load(
    _ph_energy_phpp: OpPhPHPP, _phx_climate_peak_load: PhxClimatePeakLoad
) -> OpPhClimatePeakHeatingLoad:
    """Create a new OpPhClimatePeakHeatingLoad object from a PHX Climate."""
    obj = OpPhClimatePeakHeatingLoad(
        phpp=_ph_energy_phpp,
        period_number=1,
        _radiation_north_kwh_m2=_phx_climate_peak_load.radiation_north or 0.0,
        _radiation_east_kwh_m2=_phx_climate_peak_load.radiation_east or 0.0,
        _radiation_south_kwh_m2=_phx_climate_peak_load.radiation_south or 0.0,
        _radiation_west_kwh_m2=_phx_climate_peak_load.radiation_west or 0.0,
        _radiation_horizontal_kwh_m2=_phx_climate_peak_load.radiation_global or 0.0,
    )
    obj.temperature_air_c = _phx_climate_peak_load.temperature_air or 0.0
    obj.temperature_sky_c = _phx_climate_peak_load.temperature_sky or 0.0
    obj.temperature_dewpoint_c = _phx_climate_peak_load.temperature_dewpoint or 0.0
    obj.temperature_ground_c = _phx_climate_peak_load.temperature_ground or 0.0
    return obj


def create_ph_energy_peak_cooling_load(
    _ph_energy_phpp: OpPhPHPP, _phx_climate_peak_load: PhxClimatePeakLoad
) -> OpPhClimatePeakCoolingLoad:
    """Create a new OpPhClimatePeakCoolingLoad object from a PHX Climate."""
    obj = OpPhClimatePeakCoolingLoad(
        phpp=_ph_energy_phpp,
        period_number=1,
        _radiation_north_kwh_m2=_phx_climate_peak_load.radiation_north or 0.0,
        _radiation_east_kwh_m2=_phx_climate_peak_load.radiation_east or 0.0,
        _radiation_south_kwh_m2=_phx_climate_peak_load.radiation_south or 0.0,
        _radiation_west_kwh_m2=_phx_climate_peak_load.radiation_west or 0.0,
        _radiation_horizontal_kwh_m2=_phx_climate_peak_load.radiation_global or 0.0,
    )
    obj.temperature_air_c = _phx_climate_peak_load.temperature_air or 0.0
    obj.temperature_sky_c = _phx_climate_peak_load.temperature_sky or 0.0
    obj.temperature_dewpoint_c = _phx_climate_peak_load.temperature_dewpoint or 0.0
    obj.temperature_ground_c = _phx_climate_peak_load.temperature_ground or 0.0
    return obj


def create_ph_energy_climate(
    _ph_energy_phpp: OpPhPHPP, _phx_variant: PhxVariant
) -> OpPhClimate:
    """Create a OpPhClimate object from a PhxVariant."""

    ph_energy_climate = OpPhClimate(_ph_energy_phpp)

    # -------------------------------------------------------------------------
    # -- Initialize all the calc-steps
    for i, period in enumerate(_phx_variant.site.climate.monthly_hours, start=1):
        period_name, period_length_hours = period
        ph_energy_climate.periods.append(
            OpPhClimateCalcPeriod(
                phpp=_ph_energy_phpp,
                period_number=i,
                display_name=period_name,
                _period_length_hours=period_length_hours,
            )
        )

    # ------------------------------------------------------------------------
    # -- Set the calc-step data
    for i, period in enumerate(ph_energy_climate.periods):
        # -- Set Climate Radiation
        period.radiation_north_kwh_m2 = _phx_variant.site.climate.radiation_north[i]
        period.radiation_east_kwh_m2 = _phx_variant.site.climate.radiation_east[i]
        period.radiation_south_kwh_m2 = _phx_variant.site.climate.radiation_south[i]
        period.radiation_west_kwh_m2 = _phx_variant.site.climate.radiation_west[i]
        period.radiation_horizontal_kwh_m2 = _phx_variant.site.climate.radiation_global[
            i
        ]

        # -- Set Climate Temperatures
        period.temperature_air_c = _phx_variant.site.climate.temperature_air[i]
        period.temperature_sky_c = _phx_variant.site.climate.temperature_sky[i]
        period.temperature_dewpoint_c = _phx_variant.site.climate.temperature_dewpoint[
            i
        ]

    # -------------------------------------------------------------------------
    # --Calculate and set the period radiation factors for the Monthly Periods
    for period in ph_energy_climate.periods:
        period.calculate_radiation_factors()

    # -------------------------------------------------------------------------
    # -- Set Peak Load Data for Heating and Cooling
    ph_energy_climate.peak_heating_1 = create_ph_energy_peak_heating_load(
        _ph_energy_phpp, _phx_variant.site.climate.peak_heating_1
    )
    ph_energy_climate.peak_heating_2 = create_ph_energy_peak_heating_load(
        _ph_energy_phpp, _phx_variant.site.climate.peak_heating_2
    )
    ph_energy_climate.peak_cooling_1 = create_ph_energy_peak_cooling_load(
        _ph_energy_phpp, _phx_variant.site.climate.peak_cooling_1
    )
    ph_energy_climate.peak_cooling_2 = create_ph_energy_peak_cooling_load(
        _ph_energy_phpp, _phx_variant.site.climate.peak_cooling_2
    )

    # -------------------------------------------------------------------------
    # --Calculate and set the period radiation factors for the Peak-Load Periods
    ph_energy_climate.peak_heating_1.calculate_radiation_factors()
    ph_energy_climate.peak_heating_2.calculate_radiation_factors()
    ph_energy_climate.peak_cooling_1.calculate_radiation_factors()
    ph_energy_climate.peak_cooling_2.calculate_radiation_factors()

    return ph_energy_climate


# ----------------------------------------------------------------------------------------------------------------------
# -- Envelope


def create_ph_energy_opaque_surface(
    _phx_compo: PhxComponentOpaque,
    _phx_polygon: PhxPolygon,
    _construction: OpPhConstructionOpaque,
) -> OpPhOpaqueSurface:
    """Create a OpPhSurface_Opaque object from a PhxComponentOpaque and PhxPolygon."""

    ph_energy_surface = OpPhOpaqueSurface(
        construction=_construction,
        id_num=_phx_polygon.id_num,
        display_name=_phx_polygon.display_name,
        area_m2=_phx_polygon.area,
        angle_from_horizontal=_phx_polygon.angle_from_horizontal,
        cardinal_orientation_angle=_phx_polygon.cardinal_orientation_angle,
        face_type=ComponentFaceType(_phx_compo.face_type.value),
        exposure_exterior=ComponentExposureExterior(_phx_compo.exposure_exterior.value),
    )

    return ph_energy_surface


def create_ph_energy_aperture_surface(
    _phx_ap_element: PhxApertureElement,
    _host_surface: OpPhOpaqueSurface,
    _construction: OpPhConstructionAperture,
) -> OpPhApertureSurface | None:
    """Create a OpPhSurface_Aperture object from a PhxApertureElement."""

    if not _phx_ap_element.polygon:
        return None

    # -- Set all the Open-PH-Aperture data from the PHX-Aperture
    ph_e_ap = OpPhApertureSurface(
        host=_host_surface,
        construction=_construction,
        face_type=ComponentFaceType(_phx_ap_element.host.face_type.value),
        exposure_exterior=ComponentExposureExterior(
            _phx_ap_element.host.exposure_exterior.value
        ),
        id_num=_phx_ap_element.polygon.id_num,
        display_name=_phx_ap_element.polygon.display_name,
    )
    ph_e_ap.heat_gain.winter.shading_factor = _phx_ap_element.winter_shading_factor
    ph_e_ap.heat_gain.summer.shading_factor = _phx_ap_element.summer_shading_factor

    if isinstance(_phx_ap_element.polygon, PhxPolygonRectangular):
        ph_e_ap.height_m = _phx_ap_element.polygon.height
        ph_e_ap.width_m = _phx_ap_element.polygon.width
    else:
        ph_e_ap.height_m = math.sqrt(_phx_ap_element.polygon.area)
        ph_e_ap.width_m = math.sqrt(_phx_ap_element.polygon.area)

    return ph_e_ap


def create_ph_energy_areas(
    _ph_energy_phpp: OpPhPHPP, _phx_variant: PhxVariant
) -> OpPhAreas:
    """Create a OpPhAreas object from a PhxVariant."""

    if len(_ph_energy_phpp.opaque_constructions) == 0:
        raise ValueError(
            "Make sure that you populate the Opaque Constructions Collection with all the constructions "
            "before trying to create the OpPhAreas object. Use 'create_opaque_construction_collection()'."
        )

    if len(_ph_energy_phpp.aperture_constructions) == 0:
        raise ValueError(
            "Make sure that you populate the Aperture Constructions Collection with all the constructions "
            "before trying to create the OpPhAreas object. Use 'create_aperture_construction_collection()'."
        )

    ph_energy_areas = OpPhAreas(_ph_energy_phpp)
    for phx_compo in _phx_variant.building.opaque_components:
        opaque_construction = (
            _ph_energy_phpp.opaque_constructions.get_construction_by_identifier(
                phx_compo.assembly.identifier
            )
        )

        for phx_polygon in phx_compo.polygons:
            # -----------------------------------------------------------------
            # -- build the opaque surface
            ph_energy_surface = create_ph_energy_opaque_surface(
                phx_compo, phx_polygon, opaque_construction
            )
            ph_energy_areas._opaque_surface_list.append(ph_energy_surface)

            # -----------------------------------------------------------------
            # -- build the child apertures, if any
            for child_polygon_id in phx_polygon.child_polygon_ids:
                phx_aperture_element = phx_compo.get_aperture_element_by_polygon_id_num(
                    child_polygon_id
                )
                window_construction = _ph_energy_phpp.aperture_constructions.get_construction_by_identifier(
                    phx_aperture_element.host.window_type.identifier
                )

                ph_energy_aperture = create_ph_energy_aperture_surface(
                    phx_compo.get_aperture_element_by_polygon_id_num(child_polygon_id),
                    ph_energy_surface,
                    window_construction,
                )
                ph_energy_surface.add_aperture(ph_energy_aperture)

    return ph_energy_areas


def create_opaque_construction(
    _construction: PhxConstructionOpaque,
) -> OpPhConstructionOpaque:
    """Create a new OpPhConstructionOpaque object from a PhxConstructionOpaque."""
    return OpPhConstructionOpaque(
        identifier=_construction.identifier,
        id_num=_construction.id_num,
        display_name=_construction.display_name,
        u_value=_construction.u_value,
    )


def create_opaque_construction_collection(
    _phx_variant: PhxVariant,
) -> OpPhConstructionCollection[OpPhConstructionOpaque]:
    """Create a new ConstructionCollection[OpPhConstructionOpaque] object from a PhxVariant."""
    opaque_construction_collection = OpPhConstructionCollection[
        OpPhConstructionOpaque
    ]()
    for phx_compo in _phx_variant.building.opaque_components:
        opaque_construction_collection.add_new_construction(
            create_opaque_construction(phx_compo.assembly)
        )
    return opaque_construction_collection


def create_frame_element(
    _phx_frame_element: PhxWindowFrameElement,
) -> OpPhWindowFrameElement:
    """Create a new OpPhWindowFrameElement object from a PhxWindowFrameElement."""
    return OpPhWindowFrameElement(
        width=_phx_frame_element.width,
        u_value=_phx_frame_element.u_value,
        psi_glazing=_phx_frame_element.psi_glazing,
        psi_install=_phx_frame_element.psi_install,
    )


def create_aperture_construction(
    _construction: PhxConstructionWindow,
) -> OpPhConstructionAperture:
    """Create a new OpPhConstructionAperture object from a PhxConstructionWindow."""
    return OpPhConstructionAperture(
        identifier=_construction.identifier,
        id_num=_construction.id_num,
        display_name=_construction.display_name,
        glazing_type_display_name=_construction.glazing_type_display_name,
        frame_type_display_name=_construction.frame_type_display_name,
        glazing=OpPhGlazing(
            identifier=_construction.identifier,
            id_num=_construction.id_num,
            u_value=_construction.u_value_glass,
            g_value=_construction.glass_g_value,
        ),
        frame_top=create_frame_element(_construction.frame_top),
        frame_bottom=create_frame_element(_construction.frame_bottom),
        frame_left=create_frame_element(_construction.frame_left),
        frame_right=create_frame_element(_construction.frame_right),
    )


def create_aperture_construction_collection(
    _phx_variant: PhxVariant,
) -> OpPhConstructionCollection[OpPhConstructionAperture]:
    """Create a new ConstructionCollection[OpPhConstructionAperture] object from a PhxVariant."""
    aperture_construction_collection = OpPhConstructionCollection[
        OpPhConstructionAperture
    ]()
    for phx_compo in _phx_variant.building.aperture_components:
        aperture_construction_collection.add_new_construction(
            create_aperture_construction(phx_compo.window_type)
        )
    return aperture_construction_collection


# ----------------------------------------------------------------------------------------------------------------------
# -- Ventilation - Devices


def get_phx_duct_from_list(
    _phx_ducts: list[PhxDuctElement], _duct_type: PhxVentDuctType
) -> PhxDuctElement:
    """Find the PHX-Duct of the specified type (Supply | Exhaust) for the designated Ventilator."""

    phx_ducting = [d for d in _phx_ducts if d.duct_type == _duct_type]
    if len(phx_ducting) != 1:
        raise VentilationDuctError(phx_ducting, _duct_type.name)
    return phx_ducting[0]


def create_ph_en_duct(
    _device: OpPhVentilationDevice, _phx_duct: PhxDuctElement
) -> OpPhDuct:
    """Create a new OpPhDuct from a source PhxDuctElement."""

    return OpPhDuct(
        device=_device,
        length_m=_phx_duct.length_m,
        diameter_mm=_phx_duct.diameter_mm,
        height_mm=_phx_duct.height_mm,
        width_mm=_phx_duct.width_mm,
        insulation_thickness_mm=_phx_duct.insulation_thickness_mm,
        insulation_conductivity_w_mk=_phx_duct.insulation_conductivity_wmk,
        insulation_reflective=_phx_duct.is_reflective,
        duct_type=OpPhDuctType(_phx_duct.duct_type.value),
    )


def create_ph_energy_ventilator_ducting(
    _device: OpPhVentilationDevice,
    _phx_supply_duct: PhxDuctElement,
    _phx_exhaust_duct: PhxDuctElement,
) -> OpPhVentilationDeviceDucting:
    """Create a new OpPhVentilationDeviceDucting from source Supply and Exhaust PhxDuctElements."""

    ducting = OpPhVentilationDeviceDucting(_device)
    ducting.supply_ducting = create_ph_en_duct(_device, _phx_supply_duct)
    ducting.exhaust_ducting = create_ph_en_duct(_device, _phx_exhaust_duct)
    return ducting


def create_ph_energy_ventilator(
    _ph_energy_phpp: OpPhPHPP,
    _phx_ventilator: AnyPhxVentilation,
    _phx_supply_duct: PhxDuctElement,
    _phx_exhaust_duct: PhxDuctElement,
) -> OpPhVentilationDevice:
    """Create a new OpPhVentilationDevice (HRV/ERV) from a source PHX-Ventilation Device."""

    device = OpPhVentilationDevice(
        phpp=_ph_energy_phpp,
        id_num=_phx_ventilator.id_num,
        display_name=_phx_ventilator.display_name,
        quantity=_phx_ventilator.quantity,
        sensible_heat_recovery_effic=_phx_ventilator.params.sensible_heat_recovery,
        latent_heat_recovery_effic=_phx_ventilator.params.latent_heat_recovery,
        electric_efficiency_wh_m3=_phx_ventilator.params.electric_efficiency,
        frost_protection_reqd=_phx_ventilator.params.frost_protection_reqd,
        temperature_c_below_defrost_used=_phx_ventilator.params.temperature_below_defrost_used,
    )
    device.ducting = create_ph_energy_ventilator_ducting(
        device, _phx_supply_duct, _phx_exhaust_duct
    )
    return device


def create_ph_energy_ventilation_system(
    _ph_energy_phpp: OpPhPHPP,
    _phx_variant: PhxVariant,
) -> OpPhVentilationSystem:
    """Create a new OpPhMechanicalSystemCollection object from a PhxMechanicalSystemCollection."""

    ph_energy_vent_system = OpPhVentilationSystem(phpp=_ph_energy_phpp)

    # -- Get the Mechanical Vent Devices
    for phx_mech_collection in _phx_variant.mech_collections:
        for phx_ventilator in phx_mech_collection.ventilation_devices:
            phx_ducts = [
                d
                for d in phx_mech_collection.vent_ducting
                if phx_ventilator.id_num in d.assigned_vent_unit_ids
            ]
            ph_energy_ventilator = create_ph_energy_ventilator(
                _ph_energy_phpp=_ph_energy_phpp,
                _phx_ventilator=phx_ventilator,
                _phx_supply_duct=get_phx_duct_from_list(
                    phx_ducts, PhxVentDuctType.SUPPLY
                ),
                _phx_exhaust_duct=get_phx_duct_from_list(
                    phx_ducts, PhxVentDuctType.EXHAUST
                ),
            )

            ph_energy_vent_system.device_collection.add_new_mech_device(
                str(ph_energy_ventilator.id_num), ph_energy_ventilator
            )
    return ph_energy_vent_system


# ----------------------------------------------------------------------------------------------------------------------
# -- Program


def create_ventilation_schedule(
    _phx_schedule: PhxScheduleVentilation,
) -> OpPhScheduleVentilation:
    """Create a new Ph-Energy Ventilation Schedule from a PHX Ventilation Schedule"""

    # -- Create the basic object with attributes from PHX
    new_schedule = OpPhScheduleVentilation(
        id_num=_phx_schedule.id_num,
        name=_phx_schedule.name,
        identifier=str(_phx_schedule.identifier),
        operating_hours=_phx_schedule.operating_hours,
        operating_days=_phx_schedule.operating_days,
        operating_weeks=_phx_schedule.operating_weeks,
        holiday_days=_phx_schedule.holiday_days,
    )

    # -- Transfer the Operating-Period values from PHX
    new_schedule.operating_periods.high.period_operating_hours = (
        _phx_schedule.operating_periods.high.period_operating_hours
    )
    new_schedule.operating_periods.high.period_operation_speed = (
        _phx_schedule.operating_periods.high.period_operation_speed
    )
    new_schedule.operating_periods.basic.period_operating_hours = (
        _phx_schedule.operating_periods.standard.period_operating_hours
    )
    new_schedule.operating_periods.standard.period_operation_speed = (
        _phx_schedule.operating_periods.standard.period_operation_speed
    )
    new_schedule.operating_periods.basic.period_operating_hours = (
        _phx_schedule.operating_periods.basic.period_operating_hours
    )
    new_schedule.operating_periods.basic.period_operation_speed = (
        _phx_schedule.operating_periods.basic.period_operation_speed
    )
    new_schedule.operating_periods.minimum.period_operating_hours = (
        _phx_schedule.operating_periods.minimum.period_operating_hours
    )
    new_schedule.operating_periods.minimum.period_operation_speed = (
        _phx_schedule.operating_periods.minimum.period_operation_speed
    )

    return new_schedule


def create_ventilation_load(
    _phx_ventilation_load: PhxLoadVentilation,
) -> OpPhLoadVentilation:
    """Return a new OpPhLoadVentilation object with values set from the PhxLoadVentilation."""
    return OpPhLoadVentilation(
        supply_airflow_m3_h=_phx_ventilation_load.flow_supply,
        exhaust_airflow_m3_h=_phx_ventilation_load.flow_extract,
        transfer_airflow_m3_h=_phx_ventilation_load.flow_transfer,
    )


# ----------------------------------------------------------------------------------------------------------------------
# -- Rooms


def create_ph_energy_room(
    _phx_space: PhxSpace,
    _schedule_collection: OpPhScheduleCollection[OpPhScheduleVentilation],
    _ph_en_hvac: OpPhHVAC,
) -> OpPhRoom:
    """Create a new OpPhRoom object from a PhxSpace."""
    new_room = OpPhRoom()
    new_room.quantity = _phx_space.quantity
    new_room.display_name = _phx_space.display_name
    new_room.floor_area_m2 = _phx_space.floor_area
    try:
        new_room.weighting_factor = (
            _phx_space.weighted_floor_area / _phx_space.floor_area
        )
    except ZeroDivisionError:
        new_room.weighting_factor = 0.0
    new_room.net_volume_m3 = _phx_space.net_volume

    # -- Assign Ventilator Device
    new_room.vent_unit = (
        _ph_en_hvac.ventilation_system.device_collection.get_device_by_key(
            str(_phx_space.vent_unit_id_num)
        )
    )

    # -- Build the Room's Ventilation Program
    new_room.ventilation.display_name = _phx_space.ventilation.display_name
    new_room.ventilation.schedule = _schedule_collection.get_schedule_by_key(
        str(_phx_space.ventilation.schedule.identifier)
    )
    new_room.ventilation.load = create_ventilation_load(_phx_space.ventilation.load)

    # TODO: Build Occupancy Program

    # TODO: Build Lighting Program

    return new_room


def create_ph_energy_rooms(
    _ph_energy_phpp: OpPhPHPP, _phx_variant: PhxVariant
) -> OpPhRooms:
    """Create a OpPhRooms object from a PhxVariant's 'Zones'."""
    ph_energy_rooms = OpPhRooms(_ph_energy_phpp)
    for phx_zone in _phx_variant.building.zones:
        for phx_space in phx_zone.spaces:
            ph_energy_rooms.add_room(
                create_ph_energy_room(
                    phx_space,
                    _ph_energy_phpp.schedules,
                    _ph_energy_phpp.hvac,
                )
            )

    return ph_energy_rooms


def create_schedules(_phx_variant: PhxVariant) -> list[OpPhScheduleVentilation]:
    """Return a list of each unique Schedule object found on the PHX model's Spaces."""
    schedules = {}
    for phx_zone in _phx_variant.building.zones:
        for phx_space in phx_zone.spaces:
            # TODO: Create new OpPh Objects from the PHX Schedules...
            schedules[str(phx_space.ventilation.schedule.identifier)] = (
                create_ventilation_schedule(phx_space.ventilation.schedule)
            )
            # TODO: handle Occupancy and Lighting Schedules
            # schedules[str(phx_space.occupancy.schedule.identifier)] = \
            #     create_new_schedule(phx_space.occupancy.schedule)
            # schedules[str(phx_space.lighting.schedule.identifier)] = \
            #     create_new_schedule(phx_space.lighting.schedule)
    return list(schedules.values())


def create_ph_energy_infiltration(
    _ph_energy_phpp: OpPhPHPP, _phx_variant: PhxVariant
) -> OpPhInfiltration:
    """Return a new OpPhInfiltration object with props based on a PHX Variant"""

    return OpPhInfiltration(
        phpp=_ph_energy_phpp,
        wind_coefficient_e=_phx_variant.phius_cert.ph_building_data.wind_coefficient_e,
        wind_coefficient_f=_phx_variant.phius_cert.ph_building_data.wind_coefficient_f,
        airtightness_n50=_phx_variant.phius_cert.ph_building_data.airtightness_n50,
    )


# ----------------------------------------------------------------------------------------------------------------------
# -- Entry Point


def from_phx_variant(_phx_variant: PhxVariant) -> OpPhPHPP:
    """Create a new OpPhergyPHPP object from a PhxVariant."""

    ph_energy_phpp = OpPhPHPP()

    # -- Setup the PHPP Data
    for program in create_schedules(_phx_variant):
        ph_energy_phpp.schedules.add_new_schedule(program)
    ph_energy_phpp.opaque_constructions = create_opaque_construction_collection(
        _phx_variant
    )
    ph_energy_phpp.aperture_constructions = create_aperture_construction_collection(
        _phx_variant
    )
    ph_energy_phpp.hvac.ventilation_system = create_ph_energy_ventilation_system(
        ph_energy_phpp, _phx_variant
    )
    ph_energy_phpp.climate = create_ph_energy_climate(ph_energy_phpp, _phx_variant)
    ph_energy_phpp.infiltration = create_ph_energy_infiltration(
        ph_energy_phpp, _phx_variant
    )
    ph_energy_phpp.areas = create_ph_energy_areas(ph_energy_phpp, _phx_variant)
    ph_energy_phpp.rooms = create_ph_energy_rooms(ph_energy_phpp, _phx_variant)

    return ph_energy_phpp
