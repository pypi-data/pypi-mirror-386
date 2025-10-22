
# Iron Bars

**Iron Bars** is a lightweight Python utility providing a set of small but powerful functions to simplify common programming tasks. It is designed to be **fast, easy to use, and improve efficiency** in your Python projects. With Iron Bars, you can quickly handle CSV files, load data from Google Sheets or GitHub, save multiple DataFrames effortlessly, and automate repetitive data-handling tasks—all without writing boilerplate code.

This utility is perfect for:  
- **Data analysts & data scientists** who work with multiple CSVs and sheets.  
- **Developers** who need quick, reliable utilities to fetch, transform, and save data.  
- **Students or hobbyists** learning Python and working on small projects that require data loading and storage.  

> Iron Bars saves time, reduces errors, and simplifies your workflow by providing a clear, Pythonic interface for common tasks.

---

## Latest Shipment -> [V0.3.5 (Added byteBars for lazy DataFrame storage) 04-10-2025](https://pypi.org/project/ironBars/0.3.5/)
<a href="https://pypi.org/project/ironBars/">
  <img src="https://upload.wikimedia.org/wikipedia/commons/6/64/PyPI_logo.svg" width="100" alt="PyPI">
</a>

**Changes:**
- Added **byteBars**: disk-backed, compressed, lazy-loading DataFrame storage with row-, block-, and column-wise access. **<mark>[v0.3.5]</mark>**
- Added function: **fill_nans**. **<mark>[v0.2.6]</mark>**
- Fixed importing issue. **<mark>[v0.2.5]</mark>**

**Pending:**
- Implementing new feature which is extending a dataset with suitable values. **Extending a small dataset to large** 
- Implementing dependency issues on different machines.
---

## Requirements

- Any operating system with Python installed.  
- Python version >= 3.10.

---

## Installation

You can easily install **Iron Bars** via `pip`:

```bash
pip install ironbars
```

You can easily use **Iron Bars** by using:
```bash
import ironBars # for importing whole Module
import ironBars.ironSheets # for importing ironSheets
```

---

## IronSheets Module

**IronSheets** is a module within Iron Bars that simplifies working with CSV files, especially for loading data directly from Google Sheets or GitHub CSV files. You can fetch single or multiple sheets, load them into pandas DataFrames, and save them with automatic or custom naming—all in a few lines of code.  

For complete usage instructions, visit the [Iron Bars Wiki Documentation](https://sevruscorporations.github.io/ironBars/).

---

### Functions

#### `gsheet_load(url: str | list, as_df: bool = False, max_workers: int | None = None)`

Fetch CSVs from Google Sheets, GitHub, or direct URLs. Returns either CSV URLs or pandas DataFrames.

**Parameters:**

- `url` (`str` | `list[str]`): Google Sheet URL(s) or GitHub CSV link(s).  
- `as_df` (`bool`): If `True`, loads data as pandas DataFrame(s). Default is `False`.  
- `max_workers` (`int` | `None`): Maximum threads for parallel downloading. Defaults to `None`.

**Returns:**  
`str` | `list[str]` | `pd.DataFrame` | `list[pd.DataFrame]`

**Examples:**

```python
import ironSheets

# Single Google Sheet -> pandas DataFrame
df = ironSheets.gsheet_load(url, as_df=True)
print(df.head())

# Multiple URLs -> list of DataFrames
data_frames = ironSheets.gsheet_load([url1, url2], as_df=True)
```

---

#### `gsheet_save(data_frames, auto_name=True, name_series="Sheet", save_dir=".", filename=None)`

Save one or more pandas DataFrames as CSV files with flexible naming options.

**Parameters:**

- `data_frames` (`pd.DataFrame | list[pd.DataFrame]`)  
- `auto_name` (`bool`): Default `True`. Auto-names multiple DataFrames.  
- `name_series` (`str | list[str]`): Base name or list of filenames.  
- `save_dir` (`str`): Directory to save files. Default is current directory.  
- `filename` (`str | None`): Required for a single DataFrame.  

**Examples:**

```python
# Save single DataFrame
ironSheets.gsheet_save(df, filename="my_sheet.csv")

# Save multiple DataFrames with automatic naming
ironSheets.gsheet_save(dfs, auto_name=True, name_series="Sheet")

# Save multiple DataFrames with custom names
ironSheets.gsheet_save(dfs, auto_name=False, name_series=["First", "Second"])
```

---

### Why Iron Bars Helps You

- **Speed & Efficiency:** Load multiple sheets in parallel using threads.  
- **Automatic Conversion:** Google Sheet URLs and GitHub blob URLs are automatically converted to CSV links.  
- **Error Prevention:** Clear error messages, automatic directory creation, and safe saving prevent accidental overwrites.  
- **Flexible Saving:** Auto-name multiple DataFrames or provide custom filenames.  
- **User-Friendly:** Minimal setup, clean API, and works across platforms.  

For **detailed examples, advanced usage, and troubleshooting**, check out the full documentation on the **[Iron Bars Wiki](https://sevruscorporations.github.io/ironBars/)**.

---

**Author:** Sevrus (b25bs1304@iitj.ac.in)  
**GitHub:** [sevruscorporations](https://github.com/sevruscorporations)
