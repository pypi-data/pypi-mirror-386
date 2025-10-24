# Spreadsheet Column Splitter
Takes in a file with column data (csv or Excel), groups and filters the data based on a given **splitter** column, and splits the data in the input file into separate output files based on groupings via the splitter column. 

For example, if you have sales data for fruit, and one of the columns is 'fruit name' and the options are "apple, orange, peach", then Spreadsheet Column Splitter will output three files, one with the apple data, one with the orange data, and one with the peach data. 

If there are multiple worksheets, you can optionally provide a `sheets_list` to indicate which worksheets contain data that you would like to include in the split files. Spreadsheet Column Splitter will split the data in each worksheet into a corresponding worksheet in each output file. If you do not provide `sheets_list`, it will try to read every worksheet found and look for the `splitter_column`.

## Installation
```
pip install spreadsheet-column-splitter
```

## How to use:

```
from spreadsheet_column_splitter import splitter

splitter(
    input_file=STRING,
    output_folder=STRING,
    splitter_column=STRING,
    naming_suffix=STRING,
    sheets_list=LIST(optional),
    template_name=STRING(optional)
)
```
The first 4 parameters are required. `sheets_list` and `template_name` are optional. 

## Parameters:
- `input_file`: the column data file that holds the data that will be split. Takes csv and excel formats. 
- `output_folder`: subfolder director name that will be created in the current working directory to hold the output files.
- `splitter_column`: the column that will be used to group and split the data into filtered separate files. 
- `naming_suffix`: a suffix that will be added to the output files. 
- `sheets_list`: (optional) If you are using as an input_file an Excel with multiple sheets, but you do not wish to split all of them, add a sheets list that holds the names of the sheets that you wish to split from the Workbook.
- `template_name`: (optional) If you want the data to be added to a formated Excel template file, include that filename/path here.

## Excel files with multiple sheets
By default, Spreadsheet Column Splitter will look for table data and the splitter column in every sheet within a workbook. The splitter column must be named identical in each worksheet. 

If you have worksheets that you do not want to be looked at for data to be split, use `sheets_list` to provide the names of the worksheets that you wish to split, omitting names of worksheets that you wish to skip.

## Using an Excel template for output
An output template file should contain a header row in row 1 and be blank below that. You can format however you'd like.

Be careful: Cells that look empty in Excel are not always recognized as such by `openpyxl`. Thus when using a template, your data may be added to a row way at the bottom, past many rows that look empty but are not recognized as such. 

To remedy this, delete all rows in an Excel file template below your header row. Then they will usually be recognized as empty. 