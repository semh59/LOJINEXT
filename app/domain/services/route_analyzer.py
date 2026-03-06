from typing import List, Dict, Any
from dataclasses import dataclass
import logging
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    start_index: int
    end_index: int
    value: int
    start_dist: float = 0.0
    end_dist: float = 0.0


class RouteAnalyzer:
    """
    Analyzes OpenRouteService route data to provide detailed statistics
    by crossing different data dimensions (e.g., Steepness x Road Class).
    """

    def analyze_segments(
        self,
        geometry_points: List[List[float]],
        extras: Dict[str, Any],
        reference_distance_m: float = None,
    ) -> Dict[str, Any]:
        """
        Intersect disparate segment ranges from ORS extra_info.

        Args:
            geometry_points: List of [lon, lat, elev]
            extras: ORS extras dictionary
            reference_distance_m: Total route distance in meters from summary (for scaling)

        Returns:
            Granular stats (motorway, trunk, etc.) AND aggregated stats (highway, other).
        """
        if not geometry_points:
            return {}

        # 1. Calculate cumulative distances for each point in geometry
        cum_distances = self._calculate_cumulative_distances(geometry_points)

        # 2. Extract segments
        steepness_segments = self._parse_extra_segments(
            extras, "steepness", cum_distances
        )
        waycategory_segments = self._parse_extra_segments(
            extras, "waycategory", cum_distances
        )
        waytype_segments = self._parse_extra_segments(extras, "waytype", cum_distances)

        # If fallback is needed, we must have at least steepness and one of the others
        if not steepness_segments or (
            not waycategory_segments and not waytype_segments
        ):
            logger.warning("Missing critical data for analysis")
            return {
                "highway": {"flat": 0.0, "up": 0.0, "down": 0.0},
                "other": {"flat": 0.0, "up": 0.0, "down": 0.0},
            }

        # 3. Initialize stats buckets
        categories = [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "unclassified",
            "other",
        ]
        stats = {cat: {"flat": 0.0, "up": 0.0, "down": 0.0} for cat in categories}

        # ORS WayCategory Mapping
        category_map = {
            1: "motorway",
            2: "trunk",
            3: "primary",
            4: "secondary",
            5: "tertiary",
            6: "unclassified",
            7: "residential",
        }

        # 3-way Intersection using nested sweeps or consolidated segments
        # To keep it simple and efficient, we use a single sweep across the combined boundaries
        all_dists = sorted(
            list(
                set(
                    [
                        s.start_dist
                        for s in steepness_segments
                        + waycategory_segments
                        + waytype_segments
                    ]
                    + [
                        s.end_dist
                        for s in steepness_segments
                        + waycategory_segments
                        + waytype_segments
                    ]
                )
            )
        )

        for k in range(len(all_dists) - 1):
            start = all_dists[k]
            end = all_dists[k + 1]
            length_m = end - start
            if length_m <= 0:
                continue

            mid = (start + end) / 2.0

            # Find matching segments for this slice
            st_val = next(
                (
                    s.value
                    for s in steepness_segments
                    if s.start_dist <= mid < s.end_dist
                ),
                0,
            )
            wc_val = next(
                (
                    s.value
                    for s in waycategory_segments
                    if s.start_dist <= mid < s.end_dist
                ),
                0,
            )
            wt_val = next(
                (s.value for s in waytype_segments if s.start_dist <= mid < s.end_dist),
                0,
            )

            # Determine Category
            cat_key = category_map.get(wc_val, "other")

            # Fallback: If category is unknown but waytype is 1 (State Road), treat as Primary
            if cat_key == "other" and wt_val == 1:
                cat_key = "primary"

            # Determine Steepness
            steep_type = "flat"
            if st_val > 0:
                steep_type = "up"
            elif st_val < 0:
                steep_type = "down"

            stats[cat_key][steep_type] += length_m

        # 3. Normalization (Scaling)
        if reference_distance_m and reference_distance_m > 0:
            total_geometry_m = sum(sum(steeps.values()) for steeps in stats.values())
            if total_geometry_m > 0:
                scale_factor = reference_distance_m / total_geometry_m
                for cat in stats:
                    for steep in stats[cat]:
                        stats[cat][steep] *= scale_factor

        # 4. Aggregations & Rounding
        # In Turkey, 'primary' roads (D-roads) are also effectively high-speed truck routes
        highway_categories = ["motorway", "trunk", "primary"]
        aggregates = {
            "highway": {"flat": 0.0, "up": 0.0, "down": 0.0},
            "other": {"flat": 0.0, "up": 0.0, "down": 0.0},
        }

        # Calculate raw aggregated meters first from stats
        for cat, components in stats.items():
            target_bucket = "highway" if cat in highway_categories else "other"
            for steep, val in components.items():
                if steep in ["flat", "up", "down"] and val > 0:
                    aggregates[target_bucket][steep] += val

        # Round granular stats (KM) - Keep original stats granular
        for cat in stats:
            for steep in ["flat", "up", "down"]:
                stats[cat][steep] = round(stats[cat][steep] / 1000.0, 3)

        # Round aggregates with Residual Distribution
        for bucket in ["highway", "other"]:
            raw_sums = aggregates[bucket]
            total_m = sum(raw_sums.values())
            total_km = round(total_m / 1000.0, 1)

            # 1. Round each part to 1 decimal
            rounded_parts = {
                steep: round(val / 1000.0, 1) for steep, val in raw_sums.items()
            }

            # 2. Check for discrepancy
            diff = round(total_km - sum(rounded_parts.values()), 1)

            if diff != 0:
                # Add/Subtract the difference (0.1) from the largest part
                largest_steep = max(raw_sums, key=raw_sums.get)
                rounded_parts[largest_steep] = round(
                    rounded_parts[largest_steep] + diff, 1
                )

            stats[bucket] = rounded_parts

        # 5. Top-Level Residual Distribution
        # Ensure sum(highway, other) == total_km if reference_distance_m was provided
        if reference_distance_m and reference_distance_m > 0:
            total_target_km = round(reference_distance_m / 1000.0, 1)

            # Use raw meter sums for top-level bucket sizing to find 'largest'
            bucket_m = {b: sum(aggregates[b].values()) for b in ["highway", "other"]}
            bucket_km_sums = {
                b: round(sum(stats[b].values()), 1) for b in ["highway", "other"]
            }

            top_diff = round(total_target_km - sum(bucket_km_sums.values()), 1)

            if top_diff != 0:
                # Add/Subtract top_diff from 'flat' part of the largest bucket
                largest_bucket = max(bucket_m, key=bucket_m.get)
                stats[largest_bucket]["flat"] = round(
                    stats[largest_bucket]["flat"] + top_diff, 1
                )

        # 6. User Requested 3-Tier Ratios (Otoyol, Devlet, Sehir)
        # Combine meters before rounding for accuracy
        hwy_m = sum(aggregates["highway"].values())  # total highway+trunk+primary
        other_m = sum(aggregates["other"].values())
        otoyol_m = (
            sum(stats.get("motorway", {"flat": 0}).values()) * 1000
        )  # Convert back to meters for precision
        devlet_m = (
            sum(stats.get("trunk", {"flat": 0}).values())
            + sum(stats.get("primary", {"flat": 0}).values())
        ) * 1000

        total_m = hwy_m + other_m
        if total_m > 0:
            stats["ratios"] = {
                "otoyol": round(otoyol_m / total_m, 2),
                "devlet_yolu": round(devlet_m / total_m, 2),
                "sehir_ici": round(1.0 - (otoyol_m + devlet_m) / total_m, 2),
            }
        else:
            stats["ratios"] = {"otoyol": 0.0, "devlet_yolu": 0.0, "sehir_ici": 1.0}

        # 7. Generate Granular Nodes for Physics Engine (Phase 11 P2P)
        # We iterate through the original geometry points and enrich each segment
        granular_nodes = []
        speed_map = {
            "motorway": 85.0 / 3.6,
            "trunk": 65.0 / 3.6,
            "primary": 65.0 / 3.6,
            "secondary": 45.0 / 3.6,
            "tertiary": 35.0 / 3.6,
            "residential": 35.0 / 3.6,
            "unclassified": 35.0 / 3.6,
            "other": 35.0 / 3.6,
        }

        for i in range(1, len(geometry_points)):
            prev_p = geometry_points[i - 1]
            curr_p = geometry_points[i]

            dist = self._haversine(prev_p[0], prev_p[1], curr_p[0], curr_p[1])
            if dist <= 0:
                continue

            # Delta height (elevation is 3rd index if exists)
            elev_diff = 0.0
            if len(prev_p) >= 3 and len(curr_p) >= 3:
                elev_diff = curr_p[2] - prev_p[2]

            # Find road category for midpoint of this segment
            seg_mid = (cum_distances[i - 1] + cum_distances[i]) / 2.0

            wc_val = next(
                (
                    s.value
                    for s in waycategory_segments
                    if s.start_dist <= seg_mid < s.end_dist
                ),
                0,
            )
            cat_key = category_map.get(wc_val, "other")

            # If cat unknown, check waytype
            if cat_key == "other":
                wt_val = next(
                    (
                        s.value
                        for s in waytype_segments
                        if s.start_dist <= seg_mid < s.end_dist
                    ),
                    0,
                )
                if wt_val == 1:
                    cat_key = "primary"

            speed_ms = speed_map.get(cat_key, 35.0 / 3.6)

            granular_nodes.append((float(dist), float(speed_ms), float(elev_diff)))

        stats["granular_nodes"] = granular_nodes
        return stats

    def _calculate_cumulative_distances(self, points: List[List[float]]) -> List[float]:
        """Calculates cumulative distance in meters for each point in the route geometry."""
        cum_dist = [0.0]
        for i in range(1, len(points)):
            prev = points[i - 1]
            curr = points[i]
            # points are [lon, lat, elev] or [lon, lat]
            dist = self._haversine(prev[0], prev[1], curr[0], curr[1])
            cum_dist.append(cum_dist[-1] + dist)

        return cum_dist

    def _haversine(self, lon1, lat1, lon2, lat2):
        R = 6371000  # Radius of Earth in meters
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        a = (
            sin(dLat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
        )
        c = 2 * asin(sqrt(a))
        return R * c

    def _parse_extra_segments(
        self, extras: Dict, key: str, cum_dists: List[float]
    ) -> List[Segment]:
        if key not in extras or "values" not in extras[key]:
            return []

        raw_segments = extras[key]["values"]
        parsed = []

        for item in raw_segments:
            # item is [start_idx, end_idx, value]
            start_idx = item[0]
            end_idx = item[1]
            val = item[2]

            # Safety check
            if start_idx >= len(cum_dists) or end_idx >= len(cum_dists):
                continue

            parsed.append(
                Segment(
                    start_index=start_idx,
                    end_index=end_idx,
                    value=val,
                    start_dist=cum_dists[start_idx],
                    end_dist=cum_dists[end_idx],
                )
            )

        return parsed


# Singleton
route_analyzer = RouteAnalyzer()
