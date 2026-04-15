def get_strings(language="pt_BR"):
    """Load the locale strings dict for the given language."""
    if language == "en":
        from orion.locales import en
        return en.STRINGS
    from orion.locales import pt_BR
    return pt_BR.STRINGS
