from materia.core.utils import to_float


def average_impacts(impacts_list, decimals=6):
    """Calculate average impacts from a list of impact dictionaries."""
    sums, counts = {}, {}

    for impacts in impacts_list:
        for item in impacts:
            name = item.get("name")
            values = item.get("values", {})
            if name not in sums:
                sums[name], counts[name] = {}, {}

            for stage, value in values.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    sums[name][stage] = sums[name].get(stage, 0.0) + to_float(value)
                    counts[name][stage] = counts[name].get(stage, 0) + 1

    return [
        {
            "name": name,
            "values": {
                stage: (
                    round(sums[name][stage] / counts[name][stage], decimals)
                    if counts[name][stage] > 0
                    else None
                )
                for stage in sums[name]
            },
        }
        for name in sums
    ]


def weighted_averages(
    market_shares: dict[str, float], results_by_country: dict[str, list[dict]]
) -> dict[str, dict[str, float]]:
    """Return market-share weighted averages per indicator and module."""
    return {
        ind: {
            mod: sum(
                market_shares[c]
                * next(
                    (
                        item["values"].get(mod, 0.0)
                        for item in results_by_country[c]
                        if item["name"] == ind
                    ),
                    0.0,
                )
                for c in market_shares
                if c in results_by_country
                and any(item["name"] == ind for item in results_by_country[c])
            )
            / sum(
                market_shares[c]
                for c in market_shares
                if c in results_by_country
                and any(item["name"] == ind for item in results_by_country[c])
            )
            for mod in {
                m
                for c in market_shares
                if c in results_by_country
                for item in results_by_country[c]
                if item["name"] == ind
                for m in item["values"]
            }
        }
        for ind in {
            item["name"] for items in results_by_country.values() for item in items
        }
    }


def average_material_properties(epds: list, decimals: int = 6) -> dict:
    """Compute average of numeric Material properties from EPDs."""
    sums, counts = {}, {}

    for epd in epds:
        mat = getattr(epd, "material", None)
        for key, value in mat.to_dict().items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                sums[key] = sums.get(key, 0.0) + value
                counts[key] = counts.get(key, 0) + 1

    return {
        key: round(sums[key] / counts[key], decimals) if counts[key] > 0 else None
        for key in sums
    }
