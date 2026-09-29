"""Interactive prompt for the user's search query."""


def input_search_query():
    """Prompt for a free-text search query, e.g. "ayam in Jakarta Selatan"."""
    print('What are you looking for? Use the format "<keyword(s)> in <area or district>":')
    print("Example: ayam in Jakarta Selatan")
    return input()
