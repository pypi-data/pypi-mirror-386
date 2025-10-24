# Follow the same sanitization methods in jitpcb/src/jitpcb/importer2/sanitize.stanza

from ._types.landpattern import (
    PinByType,
    PinByTypeCode,
    PinByNameCode,
    PinByBundleCode,
    PinByIndexCode,
    PinByRequireCode,
)


def sanitize_defpad(s: str) -> str:
    """
    Convert a string like 'my_pad_name' to 'MyPadName':
    - Removes underscores.
    - Capitalizes each part including the first, that is CamelCase.
    """
    parts = sanitize_id(s).split("_")
    return "".join(word.capitalize() for word in parts if word)


def python_id_char(
    ch: str,
) -> bool:  # "pin_pad_char" in jitpcb/src/jitpcb/importer2/sanitize.stanza
    # A valid Python identifier character, excluding '~' and '*'
    return ch.isalnum() or ch == "_"


def any_valid_chars(identifier: str) -> bool:
    return any(python_id_char(ch) for ch in identifier)


def replace_by_underscore(ch: str) -> bool:
    return ch in {".", "-", " "}


def illegal_id_prefix(
    ch: str,
) -> bool:  # Don't allow '_' as prefix, even it is valid in python
    return not ch.isalpha()


# same as sanitize_prefix in jitpcb/src/jitpcb/importer2/sanitize.stanza
def sanitize_prefix(name: str, prefix: str, n_prefix: bool = False) -> str:
    if n_prefix:
        return "n" + name
    elif not name or illegal_id_prefix(name[0]):
        return prefix + name
    else:
        return name


# same as sanitize_id in jitpcb/src/jitpcb/importer2/sanitize.stanza
def sanitize_id_core(id_: str, replace=None, prepend: str = "U") -> str:
    chars = []
    for ch in id_:
        if python_id_char(ch):
            chars.append(ch)
        elif replace is True:
            chars.append("_")
        elif replace_by_underscore(ch):
            chars.append("_")
        elif isinstance(replace, str) and len(replace) == 1:
            chars.append(replace)
        # else skip the character entirely
    return sanitize_prefix("".join(chars), prepend, False)


# same as sanitize-id in jitpcb/src/jitpcb/importer2/sanitize.stanza
def sanitize_id(id: str) -> str:
    return sanitize_id_core(id, True, "U")


# same as sanitize-id-with-replacement in jitpcb/src/jitpcb/importer2/sanitize.stanza
def sanitize_id_with_replacement(id: str) -> str:
    return sanitize_id_core(id, True, "P")


def python_component_name(mpn: str, name: str) -> str:
    comp_name = name if not any_valid_chars(mpn) else mpn
    return sanitize_id_core(comp_name, True, "Comp_")


def python_landpattern_name(name: str) -> str:
    return "Landpattern_" if not name else sanitize_id("Landpattern" + name)


def python_symbol_name(name: str) -> str:
    return "Symbol_" if not name else sanitize_id("Symbol" + name)


def python_manufacturer_folder(name: str) -> str:
    return sanitize_id_with_replacement(name)


# ======== sanitize_pin ========


def sanitize_pin(pin: PinByTypeCode) -> PinByTypeCode:
    """
    Return a sanitized version of the PinByTypeCode with the same structure but safe identifiers.

    Examples:
        "IN+" → "INp"
        "A.B" → "A__B"
        PinByIndex → keep structure, sanitize `name`
    """

    def sanitize(s: str) -> str:
        if not s:
            return "p"
        chars = []
        for i, ch in enumerate(s):  # exclude the last char
            if i == len(s) - 1:  # the last char
                if s[-1] == "-":
                    chars.append("n")
                elif s[-1] == "+":
                    chars.append("p")
                elif python_id_char(ch):
                    chars.append(ch)
                elif replace_by_underscore(ch):
                    chars.append("_")
                # remove all else
            else:
                if python_id_char(ch):  # valid char for python identifier
                    chars.append(ch)
                elif replace_by_underscore(ch):
                    chars.append("_")
                # remove all else
        result = "".join(chars)
        # Add prefix "p" so the name is valid in python
        if illegal_id_prefix(result[0]):
            result = "p" + result
        return result

    if pin.type == PinByType.pin_by_name:
        return PinByTypeCode(
            type=PinByType.pin_by_name,
            value=PinByNameCode(pin_name=sanitize(pin.value.pin_name)),
        )

    elif pin.type == PinByType.pin_by_bundle:
        return PinByTypeCode(
            type=PinByType.pin_by_bundle,
            value=PinByBundleCode(
                bundle_name=sanitize(pin.value.bundle_name),
                pin_name=sanitize(pin.value.pin_name),
            ),
        )

    elif pin.type == PinByType.pin_by_index:
        return PinByTypeCode(
            type=PinByType.pin_by_index,
            value=PinByIndexCode(name=sanitize(pin.value.name), index=pin.value.index),
        )

    elif pin.type == PinByType.pin_by_require:
        return PinByTypeCode(
            type=PinByType.pin_by_require,
            value=PinByRequireCode(bundle_name=sanitize(pin.value.bundle_name)),
        )

    raise ValueError(f"Unsupported pin type: {pin.type}")
