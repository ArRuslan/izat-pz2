from openpyxl import load_workbook
from openpyxl.cell import Cell
from openpyxl.styles import PatternFill

green = "8000FF00"
blue = "800000FF"
yellow = "80FFFF00"

fill_green = PatternFill(start_color=green, end_color=green, fill_type="solid")
fill_blue = PatternFill(start_color=blue, end_color=blue, fill_type="solid")
fill_yellow = PatternFill(start_color=yellow, end_color=yellow, fill_type="solid")


def _process_cell(cell: Cell) -> None:
    if not isinstance(cell.value, (int, str)):
        return

    if isinstance(cell.value, int):
        cell.fill = fill_green
        return

    if cell.value.isdigit():
        cell.fill = fill_green
        return

    chars = False
    digits = False
    for char in cell.value:
        if char.isdigit():
            digits = True
        else:
            chars = True

    if chars and digits:
        cell.fill = fill_yellow
    elif chars:
        cell.fill = fill_blue
    elif digits:
        cell.fill = fill_green


def main():
    wb = load_workbook("pz1.xlsx")
    ws = wb.active

    for row in ws:
        for col in row:
            _process_cell(col)

    wb.save("pz1-processed.xlsx")


if __name__ == "__main__":
    main()
