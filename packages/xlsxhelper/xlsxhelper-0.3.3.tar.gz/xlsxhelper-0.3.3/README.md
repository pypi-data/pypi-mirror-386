# xlsxhelper

Excel file manipulation toolset. 

## Notice

The library is based on library openpyxl, so only xlsx (new excel format) files are supported.

## Help Functions

- get_workbook
- get_worksheet
- get_merged_range_string
- parse_cols
- parse_rows
- get_cells
- set_cells_data
- load_data_from_workbook
- get_merged_ranges
- copy_cells
- merge_ranges

## Test Passed With Pythons

- 2.7
- 3.4
- 3.5
- 3.6
- 3.7
- 3.8
- 3.9
- 3.10
- 3.11

## Releases

### v0.3.3 2025/10/22

- Doc update.

### v0.3.2 2023/09/10

- Fix unit test problem.

### v0.3.1 2022/01/10

- Fix license file missing problem.
- Add set_cells_data function.

### v0.3.0 2020/07/19

- Add workbook and worksheet create support.

### v0.2.1 2019/08/31

- Fix load_data_from_workbook get raw function statement problem.
- Fix worksheet.merged_cell_ranges deprecating problem, use worksheet.merged_cells.ranges instead.
