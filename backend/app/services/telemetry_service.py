"""Telemetry service with satellite metadata tracking."""

from typing import Optional

from app.models import Telemetry, StateVector, Satellite


# Default satellite parameters for instantiation
DEFAULT_FUEL_MASS_KG = 50.0
DEFAULT_DRY_MASS_KG = 200.0


class TelemetryService:
    """Manages telemetry and satellite metadata."""

    def __init__(self) -> None:
        self.satellites: dict[str, Telemetry] = {}
        self.debris: dict[str, Telemetry] = {}
        self.satellite_metadata: dict[str, Satellite] = {}
        # Store nominal/reference orbits for recovery burns
        self.nominal_orbits: dict[str, StateVector] = {}
        # Track satellites that are "unprotected" (critical conjunction, no LOS)
        self.unprotected_satellites: dict[str, dict] = {}

    def add_telemetry(self, telemetry: Telemetry) -> None:
        """Store telemetry keyed by object_id.

        IDs starting with "D" are treated as debris; everything else
        is treated as a satellite.
        """
        if telemetry.object_id.startswith("D"):
            self.debris[telemetry.object_id] = telemetry
        else:
            self.satellites[telemetry.object_id] = telemetry

            # Initialize satellite metadata if not exists
            if telemetry.object_id not in self.satellite_metadata:
                self.satellite_metadata[telemetry.object_id] = Satellite(
                    id=telemetry.object_id,
                    name=telemetry.object_id,
                    state=telemetry.state,
                    fuel_mass=DEFAULT_FUEL_MASS_KG,
                    dry_mass=DEFAULT_DRY_MASS_KG,
                )

            # Store initial state as nominal orbit if not already stored
            if telemetry.object_id not in self.nominal_orbits:
                self.nominal_orbits[telemetry.object_id] = telemetry.state

    def add_telemetry_with_metadata(
        self,
        telemetry: Telemetry,
        fuel_mass: float = DEFAULT_FUEL_MASS_KG,
        dry_mass: float = DEFAULT_DRY_MASS_KG,
    ) -> None:
        """Add telemetry with explicit satellite metadata."""
        self.add_telemetry(telemetry)

        if not telemetry.object_id.startswith("D"):
            self.satellite_metadata[telemetry.object_id] = Satellite(
                id=telemetry.object_id,
                name=telemetry.object_id,
                state=telemetry.state,
                fuel_mass=fuel_mass,
                dry_mass=dry_mass,
            )

    def update_satellite_state(
        self, object_id: str, new_state: StateVector, timestamp: float
    ) -> None:
        """Replace the state vector and timestamp for an existing satellite."""
        if object_id not in self.satellites:
            raise KeyError(f"Satellite '{object_id}' not found in telemetry store.")
        existing = self.satellites[object_id]
        self.satellites[object_id] = Telemetry(
            object_id=existing.object_id,
            timestamp=timestamp,
            state=new_state,
            tle_line1=existing.tle_line1,
            tle_line2=existing.tle_line2,
            tle_epoch=existing.tle_epoch,
        )

        # Also update metadata state
        if object_id in self.satellite_metadata:
            meta = self.satellite_metadata[object_id]
            self.satellite_metadata[object_id] = Satellite(
                id=meta.id,
                name=meta.name,
                state=new_state,
                fuel_mass=meta.fuel_mass,
                dry_mass=meta.dry_mass,
                initial_fuel_mass=meta.initial_fuel_mass,
                exhaust_velocity_ms=meta.exhaust_velocity_ms,
                min_fuel_reserve_kg=meta.min_fuel_reserve_kg,
                max_delta_v_per_burn_ms=meta.max_delta_v_per_burn_ms,
                is_maneuverable=meta.is_maneuverable,
                is_healthy=meta.is_healthy,
            )

    def update_satellite_state_with_tle(
        self,
        object_id: str,
        new_state: StateVector,
        timestamp: float,
        tle_epoch: float,
    ) -> None:
        """Replace the state vector, timestamp, and TLE epoch for a satellite."""
        if object_id not in self.satellites:
            raise KeyError(f"Satellite '{object_id}' not found in telemetry store.")
        existing = self.satellites[object_id]
        self.satellites[object_id] = Telemetry(
            object_id=existing.object_id,
            timestamp=timestamp,
            state=new_state,
            tle_line1=existing.tle_line1,
            tle_line2=existing.tle_line2,
            tle_epoch=tle_epoch,
        )

        # Also update metadata state
        if object_id in self.satellite_metadata:
            meta = self.satellite_metadata[object_id]
            self.satellite_metadata[object_id] = Satellite(
                id=meta.id,
                name=meta.name,
                state=new_state,
                fuel_mass=meta.fuel_mass,
                dry_mass=meta.dry_mass,
                initial_fuel_mass=meta.initial_fuel_mass,
                exhaust_velocity_ms=meta.exhaust_velocity_ms,
                min_fuel_reserve_kg=meta.min_fuel_reserve_kg,
                max_delta_v_per_burn_ms=meta.max_delta_v_per_burn_ms,
                is_maneuverable=meta.is_maneuverable,
                is_healthy=meta.is_healthy,
            )

    def update_debris_state(
        self, object_id: str, new_state: StateVector, timestamp: float
    ) -> None:
        """Replace the state vector and timestamp for an existing debris object."""
        if object_id not in self.debris:
            raise KeyError(f"Debris '{object_id}' not found in telemetry store.")
        existing = self.debris[object_id]
        self.debris[object_id] = Telemetry(
            object_id=existing.object_id,
            timestamp=timestamp,
            state=new_state,
            tle_line1=existing.tle_line1,
            tle_line2=existing.tle_line2,
            tle_epoch=existing.tle_epoch,
        )

    def update_debris_state_with_tle(
        self,
        object_id: str,
        new_state: StateVector,
        timestamp: float,
        tle_epoch: float,
    ) -> None:
        """Replace the state vector, timestamp, and TLE epoch for debris."""
        if object_id not in self.debris:
            raise KeyError(f"Debris '{object_id}' not found in telemetry store.")
        existing = self.debris[object_id]
        self.debris[object_id] = Telemetry(
            object_id=existing.object_id,
            timestamp=timestamp,
            state=new_state,
            tle_line1=existing.tle_line1,
            tle_line2=existing.tle_line2,
            tle_epoch=tle_epoch,
        )

    def update_satellite_fuel(self, object_id: str, new_fuel_mass_kg: float) -> None:
        """Update fuel mass for a satellite."""
        if object_id not in self.satellite_metadata:
            raise KeyError(f"Satellite metadata '{object_id}' not found.")

        meta = self.satellite_metadata[object_id]
        self.satellite_metadata[object_id] = Satellite(
            id=meta.id,
            name=meta.name,
            state=meta.state,
            fuel_mass=max(0.0, new_fuel_mass_kg),
            dry_mass=meta.dry_mass,
            initial_fuel_mass=meta.initial_fuel_mass,
            exhaust_velocity_ms=meta.exhaust_velocity_ms,
            min_fuel_reserve_kg=meta.min_fuel_reserve_kg,
            max_delta_v_per_burn_ms=meta.max_delta_v_per_burn_ms,
            is_maneuverable=meta.is_maneuverable,
            is_healthy=meta.is_healthy,
        )

    # Nominal orbit tracking for recovery

    def get_nominal_orbit(self, object_id: str) -> Optional[StateVector]:
        """Get the nominal/reference orbit for a satellite."""
        return self.nominal_orbits.get(object_id)

    def set_nominal_orbit(self, object_id: str, state: StateVector) -> None:
        """Set the nominal/reference orbit for a satellite."""
        self.nominal_orbits[object_id] = state

    def update_nominal_orbit(self, object_id: str) -> None:
        """Update nominal orbit to current state (after successful recovery)."""
        if object_id in self.satellites:
            self.nominal_orbits[object_id] = self.satellites[object_id].state

    # Unprotected satellite tracking

    def mark_unprotected(
        self, satellite_id: str, conjunction_id: str, time_to_tca: float, reason: str
    ) -> None:
        """Mark a satellite as unprotected due to LOS failure during critical conjunction."""
        self.unprotected_satellites[satellite_id] = {
            "conjunction_id": conjunction_id,
            "time_to_tca": time_to_tca,
            "reason": reason,
            "marked_at": None,  # Will be filled with sim_time
        }

    def clear_unprotected(self, satellite_id: str) -> None:
        """Clear unprotected status for a satellite."""
        if satellite_id in self.unprotected_satellites:
            del self.unprotected_satellites[satellite_id]

    def get_unprotected_satellites(self) -> dict[str, dict]:
        """Get all unprotected satellites."""
        return self.unprotected_satellites.copy()

    def is_unprotected(self, satellite_id: str) -> bool:
        """Check if a satellite is marked as unprotected."""
        return satellite_id in self.unprotected_satellites

    def get_satellite_metadata(self, object_id: str) -> Optional[Satellite]:
        """Get satellite metadata including fuel info."""
        return self.satellite_metadata.get(object_id)

    def get_all_satellite_metadata(self) -> dict[str, Satellite]:
        """Get all satellite metadata."""
        return self.satellite_metadata.copy()

    def set_satellite_metadata(self, satellite: Satellite) -> None:
        """Set or update satellite metadata."""
        self.satellite_metadata[satellite.id] = satellite

    def get_all_objects(self) -> dict[str, Telemetry]:
        """Return all tracked objects (satellites + debris) combined."""
        return {**self.satellites, **self.debris}

    def get_all_satellites(self) -> dict[str, Telemetry]:
        return self.satellites.copy()

    def get_all_debris(self) -> dict[str, Telemetry]:
        return self.debris.copy()

    def get_satellite(self, object_id: str) -> Optional[Telemetry]:
        """Get a specific satellite's telemetry."""
        return self.satellites.get(object_id)

    def get_debris(self, object_id: str) -> Optional[Telemetry]:
        """Get a specific debris object's telemetry."""
        return self.debris.get(object_id)

    def get_low_fuel_satellites(self, threshold_fraction: float = 0.2) -> list[str]:
        """Get IDs of satellites with low fuel (below threshold fraction of initial)."""
        low_fuel = []
        for sat_id, meta in self.satellite_metadata.items():
            if meta.fuel_fraction_remaining < threshold_fraction:
                low_fuel.append(sat_id)
        return low_fuel

    def get_constellation_stats(self) -> dict:
        """Get statistics about the constellation."""
        total_fuel = sum(m.fuel_mass for m in self.satellite_metadata.values())
        total_initial_fuel = sum(
            m.initial_fuel_mass or m.fuel_mass for m in self.satellite_metadata.values()
        )

        maneuverable = sum(
            1 for m in self.satellite_metadata.values() if m.is_maneuverable
        )
        healthy = sum(1 for m in self.satellite_metadata.values() if m.is_healthy)

        return {
            "total_satellites": len(self.satellites),
            "total_debris": len(self.debris),
            "total_fuel_kg": total_fuel,
            "total_initial_fuel_kg": total_initial_fuel,
            "constellation_fuel_fraction": total_fuel / total_initial_fuel
            if total_initial_fuel > 0
            else 0,
            "maneuverable_satellites": maneuverable,
            "healthy_satellites": healthy,
            "low_fuel_satellites": len(self.get_low_fuel_satellites()),
            "unprotected_satellites": len(self.unprotected_satellites),
        }


telemetry_service = TelemetryService()
