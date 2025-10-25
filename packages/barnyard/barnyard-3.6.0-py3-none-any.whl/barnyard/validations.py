def validate_next_params(barn, add, expiry, calls, display):
    # Validate types and values for integers
    if not isinstance(calls, int):
        raise TypeError(f"❌ 'calls' must be an integer, got {type(calls).__name__}")
    if calls <= 0:
        raise ValueError(f"❌ 'calls' must be a positive integer, got {calls}")

    # Optional: validate display flag
    if display is not None and not isinstance(display, bool):
        raise TypeError(f"❌ 'display' must be a boolean or None, got {type(display).__name__}")

    # Optional: validate barn and add
    if not isinstance(barn, str):
        raise TypeError(f"❌ 'barn' must be a string, got {type(barn).__name__}")

    if not callable(add):
        raise TypeError(f"❌ 'add' must be a callable (function), got {type(add).__name__}")


def validate_find_params(barn, keys, values, display):
    if not isinstance(barn, str):
        raise ValueError("Parameter 'barn' must be a non-empty string.")

    if keys is not None and values is not None:
        raise ValueError("Parameters 'keys' and 'values' cannot be provided at the same time.")
    
    if keys is None and values is None:
        raise ValueError("Either 'keys' or 'values' must be provided.")

    if not isinstance(display, bool):
        raise ValueError("Parameter 'display' must be a boolean.")

    #---

    if keys is not None:
        if isinstance(keys, str):
            try:
                keys = int(keys)
            except ValueError:
                raise ValueError("keys must be convertible to an integer")
        elif not isinstance(keys, int):
            raise TypeError("keys must be an integer or a string representing an integer")



