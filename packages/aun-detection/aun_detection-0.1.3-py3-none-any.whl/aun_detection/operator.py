def aun_filter(a, b, t=0.85, s_min=4):
    """
    Basic symbolic mimicry detector.
    Returns None if inputs are structurally too similar,
    otherwise returns a normalized difference score.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError("Inputs must be strings")

    # Basic similarity: count shared characters / average length
    overlap = len(set(a) & set(b))
    avg_len = (len(a) + len(b)) / 2
    similarity = overlap / avg_len

    # Collapse if similarity passes threshold
    if similarity >= t:
        return None
    else:
        return round(1 - similarity, 3)
