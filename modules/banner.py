#!


def banner(
    text: str, border: str = "=", ncol: int = 40, bottom_text: str = "(Ctrl+C to exit)"
):
    if len(text) > ncol:
        ncol = len(text)
        ncol_c = ""
        ncol_b = ""
    else:
        ncol_c = " " * int((ncol - len(text)) / 2)
        ncol_b = border * int((ncol - len(bottom_text)) / 2)

    print(border * ncol)
    print(ncol_c + text + ncol_c)
    print(ncol_b + bottom_text + ncol_b)
    print()
