import logging
import time
from pathlib import Path

from app.core.orbit_propagator import orbit_propagator
from app.models import Telemetry, StateVector
from app.services.telemetry_service import telemetry_service
from app.utils.tle_parser import parse_tle

logger = logging.getLogger(__name__)


class OrbitService:
    """High-level service for orbit initialisation and bulk propagation."""

    def initialize_from_tle_file(self, file_path: str) -> int:
        """Read a TLE file and seed TelemetryService with initial state vectors.

        The file is expected to contain 3-line TLE sets (name + line 1 + line 2).
        Blank lines and comment lines (starting with '#') are ignored.
        Returns the number of objects loaded.
        """
        lines = [
            line.rstrip()
            for line in Path(file_path).read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        loaded = 0
        i = 0
        while i < len(lines) - 2:
            # Check if this is a 3-line TLE (name, line1, line2)
            if lines[i + 1].startswith("1") and lines[i + 2].startswith("2"):
                name = lines[i].strip()
                line1 = lines[i + 1]
                line2 = lines[i + 2]
                i += 3
            # Or 2-line TLE (line1, line2)
            elif lines[i].startswith("1") and lines[i + 1].startswith("2"):
                name = None
                line1 = lines[i]
                line2 = lines[i + 1]
                i += 2
            else:
                # Skip unrecognized line
                i += 1
                continue

            try:
                state: StateVector = parse_tle(line1, line2)
                # Use the NORAD catalogue number from line 1 as the object ID
                norad_id = line1[2:7].strip()
                object_id = f"SAT-{norad_id}"
                # Store TLE data for SGP4 propagation
                telemetry = Telemetry(
                    object_id=object_id,
                    timestamp=time.time(),
                    state=state,
                    tle_line1=line1,
                    tle_line2=line2,
                    tle_epoch=0.0,  # Start at TLE epoch
                )
                telemetry_service.add_telemetry(telemetry)
                loaded += 1
            except Exception:
                # Skip malformed entries rather than crashing
                continue

        return loaded

    def initialize_debris_from_tle_file(self, file_paths: str | list[str]) -> int:
        """Read one or more TLE files and seed TelemetryService with debris state vectors.

        Args:
            file_paths: A single file path (string) or a list of file paths to load.

        Each file is expected to contain 3-line TLE sets (name + line 1 + line 2).
        Blank lines and comment lines (starting with '#') are ignored.
        Debris IDs are prefixed with "D-" to distinguish from satellites.
        Returns the total number of debris objects loaded across all files.
        """
        # Normalize to list for uniform processing
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        total_loaded = 0

        for file_path in file_paths:
            logger.info(f"Loading debris from: {Path(file_path).name}")

            try:
                lines = [
                    line.rstrip()
                    for line in Path(file_path).read_text().splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
            except FileNotFoundError:
                logger.warning(f"File not found: {file_path}")
                continue

            file_loaded = 0
            i = 0
            while i < len(lines) - 2:
                # Check if this is a 3-line TLE (name, line1, line2)
                if lines[i + 1].startswith("1") and lines[i + 2].startswith("2"):
                    name = lines[i].strip()
                    line1 = lines[i + 1]
                    line2 = lines[i + 2]
                    i += 3
                # Or 2-line TLE (line1, line2)
                elif lines[i].startswith("1") and lines[i + 1].startswith("2"):
                    name = None
                    line1 = lines[i]
                    line2 = lines[i + 1]
                    i += 2
                else:
                    # Skip unrecognized line
                    i += 1
                    continue

                try:
                    state: StateVector = parse_tle(line1, line2)
                    # Use the NORAD catalogue number from line 1 as the object ID
                    # Prefix with "D-" to mark as debris
                    norad_id = line1[2:7].strip()
                    object_id = f"D-{norad_id}"
                    # Store TLE data for SGP4 propagation
                    telemetry = Telemetry(
                        object_id=object_id,
                        timestamp=time.time(),
                        state=state,
                        tle_line1=line1,
                        tle_line2=line2,
                        tle_epoch=0.0,  # Start at TLE epoch
                    )
                    telemetry_service.add_telemetry(telemetry)
                    file_loaded += 1
                except Exception:
                    # Skip malformed entries rather than crashing
                    continue

            logger.info(f"✓ Loaded {file_loaded} debris objects from {Path(file_path).name}")
            total_loaded += file_loaded

        return total_loaded

    def propagate_all(self, dt_seconds: float) -> int:
        """Propagate every object (satellites + debris) in TelemetryService forward by *dt_seconds*.

        Uses SGP4 when TLE data is available for accurate propagation with perturbations.
        Falls back to J2 RK4 for objects without TLE data.

        Returns the total number of objects updated.
        """
        satellites = telemetry_service.get_all_satellites()
        debris = telemetry_service.get_all_debris()
        now = time.time()

        updated_count = 0

        # Propagate all satellites
        for object_id, telemetry in satellites.items():
            new_state, new_epoch = orbit_propagator.propagate_telemetry(telemetry, dt_seconds)
            telemetry_service.update_satellite_state_with_tle(
                object_id=object_id,
                new_state=new_state,
                timestamp=now,
                tle_epoch=new_epoch,
            )
            updated_count += 1

        # Propagate all debris
        for object_id, telemetry in debris.items():
            new_state, new_epoch = orbit_propagator.propagate_telemetry(telemetry, dt_seconds)
            telemetry_service.update_debris_state_with_tle(
                object_id=object_id,
                new_state=new_state,
                timestamp=now,
                tle_epoch=new_epoch,
            )
            updated_count += 1

        return updated_count


orbit_service = OrbitService()
