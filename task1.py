from openpyxl import load_workbook
from openpyxl.styles import PatternFill

fill_green = PatternFill(
    start_color="8000FF00",
    end_color="8000FF00",
    fill_type="solid",
)
fill_blue = PatternFill(
    start_color="800000FF",
    end_color="800000FF",
    fill_type="solid",
)
fill_yellow = PatternFill(
    start_color="80FFFF00",
    end_color="80FFFF00",
    fill_type="solid",
)


def main():
    wb = load_workbook("pz1.xlsx")
    ws = wb.active

    for row in ws:
        for col in row:
            if col.value is None:
                continue
            if isinstance(col.value, int):
                col.fill = fill_green
            elif isinstance(col.value, str):
                if col.value.isdigit():
                    col.fill = fill_green
                else:
                    chars = False
                    digits = False
                    for char in col.value:
                        if char.isdigit():
                            digits = True
                        else:
                            chars = True

                    if chars and digits:
                        col.fill = fill_yellow
                    elif chars:
                        col.fill = fill_blue
                    elif digits:
                        col.fill = fill_green

    wb.save("pz1-processed.xlsx")


if __name__ == "__main__":
    main()
