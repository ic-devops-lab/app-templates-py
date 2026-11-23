def get_metric_value(
    exposition: str,
    name: str,
    labels: dict[str, str],
) -> float | None:
    """Find a Prometheus sample by name and labels."""
    from prometheus_client.parser import text_string_to_metric_families

    for family in text_string_to_metric_families(exposition):
        for sample in family.samples:
            if sample.name == name and sample.labels == labels:
                return float(sample.value)

    return None
