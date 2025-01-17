def parse_json_boolean(value):
    """
    Converts a string to a boolean value.
    Used when parsing from the frontend.
    """
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    return None
