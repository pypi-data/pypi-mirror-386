def normalize_page_args(kwargs):
    page_sort = kwargs.get("page_sort")
    if isinstance(page_sort, tuple):
        kwargs["page_sort"] = list(page_sort)
    return kwargs
