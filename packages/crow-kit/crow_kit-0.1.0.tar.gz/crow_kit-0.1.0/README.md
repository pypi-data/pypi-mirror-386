# CroW-Kit (Crowdsourced Wrapper Generation Framework)

CroW-Kit is a lightweight Python toolkit supporting the **CroW (Crowdsourced Wrapper Generation Framework)**. It enables users to interactively design, store, and execute web data wrappers for both tabular and non-tabular websites.

This package provides independent wrapper generation, extraction, and maintenance functionality — ideal for researchers, developers, and data engineers working with web data.

## Installation

Install directly from PyPI:

    pip install crow-kit
    

## Important: Dependencies & Requirements

This package uses `selenium` and `webdriver-manager` to control a live browser.

-   **Browser:** You must have **Google Chrome** or **Brave Browser** installed on your system.
    
-   **Permissions:** The package needs write permissions in its working directory to create a `wrappers_5ece4797eaf5e/` folder for storing the JSON wrapper files.
    
-   **External Files:** The interactive wrapper generation depends on several JavaScript and CSS files (`st.action-panel.js`, `jquery-3.7.1.min.js`, etc.). These are included with the package, but you must ensure your environment doesn't block them from being loaded.
    

## Usage Overview

The workflow is a simple two-step process:

1.  **Generate a Wrapper:** Run an interactive function (`setTableWrapper` or `setGeneralWrapper`). A browser window will open, allowing you to click on the data you want to scrape. Your selections are saved as a JSON file.
    
2.  **Extract Data:** Use the saved wrapper file (`getWrapperData`) to automatically fetch the data from the site, including handling pagination.
    

## Core Functions

### 1\. setTableWrapper(url, wrapper\_name='no\_name')

Interactively creates a table-based wrapper using Selenium. This is best for data inside a `<table_wrapper>` HTML tag.

**Parameters:**

-   `url` (str): The URL of the web page containing the table.
    
-   `wrapper_name` (str, optional): Prefix for the saved wrapper filename.
    

**Returns:**

-   Tuple: `(success, wrapper_filename, error_code, error_type, error_message)`
    

**Example:**

    from crow_kit import setTableWrapper
    
    success, wrapper_file, err_code, err_type, err_msg = setTableWrapper(
        "[https://example.com/table_page](https://example.com/table_page)",
        wrapper_name="sample_table"
    )
    
    if success:
        print("Wrapper created:", wrapper_file)
    else:
        print("Error:", err_type, err_msg)
    

**What Happens Interactively:**

1.  A new Chrome window opens to the specified `url`.
    
2.  An action panel will appear. You will be prompted to click on the table you want to scrape.
    
3.  After selecting the table, you will be prompted to click on the "Next Page" button (if one exists).
    
4.  Once you confirm, the browser will close, and a JSON wrapper file will be saved.
    

### 2\. setGeneralWrapper(url, wrapper\_name='no\_name', repeat='no')

Create a wrapper for general or non-tabular content. This is best for repeating items like articles, product cards, or search results.

**Parameters:**

-   `url` (str): Target webpage.
    
-   `wrapper_name` (str): Name for the wrapper file.
    
-   `repeat` (str): `'yes'` if the content repeats across multiple pages (e.g., product listings with pagination). Use `'no'` if you are only scraping data from a single page.
    

**Returns:**

-   Tuple: `(success, wrapper_filename, error_code, error_type, error_message)`
    

**Example:**

    from crow_kit import setGeneralWrapper
    
    success, wrapper_file, _, _, _ = setGeneralWrapper(
        "[https://example.com/articles](https://example.com/articles)",
        wrapper_name="article_wrapper",
        repeat='yes'
    )
    

**What Happens Interactively:**

1.  A Chrome window opens.
    
2.  Click on the first data point (e.g., an article title). A popup will ask you to give this data a name (e.g., "title").
    
3.  Click on the next data point (e.g., the author). Give it a name (e.g., "author").
    
4.  Continue this for all the data fields you want to extract from one of the repeating items.
    
5.  When you are done adding fields, you will be prompted to click on the "Next Page" button (if one exists).
    
6.  Confirm your selections. The browser closes, and the wrapper is saved.
    

### 3\. getWrapperData(wrapper\_name, maximum\_data\_count=100, url='')

Execute a previously created wrapper to extract structured data. This function runs headlessly (no browser window).

**Parameters:**

-   `wrapper_name` (str): Name of the saved wrapper JSON file (e.g., `article_wrapper_...json`).
    
-   `maximum_data_count` (int, optional): The maximum number of records to extract. This acts as a safeguard against infinite loops.
    
-   `url` (str, optional): Override the original URL saved in the wrapper. This is useful for running the same wrapper on a different but structurally identical page.
    

**Returns:**

-   Tuple: `(success, extracted_data)` Where `extracted_data` is a list of lists containing the extracted values (including a header row).
    

**Example:**

    from crow_kit import getWrapperData
    
    # 'wrapper_file' is the filename returned from setGeneralWrapper
    success, data = getWrapperData(wrapper_file, maximum_data_count=50)
    
    if success:
        for row in data:
            print(row)
    

### 4\. listWrappers()

Lists all locally saved wrapper files in the `wrappers_5ece4797eaf5e/` directory.

**Returns:**

-   Tuple: `(success, wrapper_file_list)` Where `wrapper_file_list` is a list of filenames.
    

**Example:**

    from crow_kit import listWrappers
    
    success, files = listWrappers()
    if success:
        print("Available wrappers:", files)
    

## Wrapper Storage

All generated wrappers are stored in a local directory:

`wrappers_5ece4797eaf5e/`

Each wrapper file is a JSON that includes:

-   Wrapper type (table or general)
    
-   Target URL
    
-   XPath selectors for the data fields
    
-   XPath for the "next page" button (if any)
    
-   Repetition pattern (`repeat`)
    

## Example Workflow

Here is a complete example from start to finish.

    from crow_kit import setGeneralWrapper, getWrapperData, listWrappers
    
    # --- Step 1: Create a general wrapper ---
    # A browser will open. Follow the interactive steps.
    print("Creating wrapper...")
    success_create, wrapper_file, _, _, _ = setGeneralWrapper(
        "[https://example.com/articles](https://example.com/articles)",
        wrapper_name="article_wrapper",
        repeat='yes'
    )
    
    if not success_create:
        print("Failed to create wrapper.")
        exit()
    
    print(f"Wrapper '{wrapper_file}' created.")
    
    # --- Step 2: List available wrappers ---
    success_list, files = listWrappers()
    if success_list:
        print("Available wrappers:", files)
    
    # --- Step 3: Extract data using the new wrapper ---
    print("Extracting data...")
    success_extract, extracted_data = getWrapperData(
        wrapper_file,
        maximum_data_count=100
    )
    
    if success_extract:
        print(f"Successfully extracted {len(extracted_data)} rows.")
        for row in extracted_data:
            print(row)
    else:
        print("Failed to extract data:", extracted_data)
    

## Example Output

The data returned by `getWrapperData` is a list of lists. The first inner list is always the header row you defined during wrapper creation.

**Tabular wrapper output:**

    [
        ["Name", "Age", "City"],
        ["Alice", "30", "New York"],
        ["Bob", "28", "Chicago"]
    ]
    

**General wrapper output:**

    [
        ["Title", "Date", "Author"],
        ["AI and Web Wrappers", "2025-10-20", "K. Naha"],
        ["The Future of Data", "2025-10-19", "J. Doe"]
    ]
    

## License

This project is licensed under the MIT License