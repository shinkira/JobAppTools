# 🧠 Neuroscience Job Ads Scraper

This Python script scrapes and filters neuroscience-related academic job postings from three major career platforms:

- **NeuroJobs (SfN)**
- **Nature Careers**
- **Science Careers**

It is designed to help researchers track tenure-track and assistant professor positions more efficiently. The filtered jobs are saved in a well-formatted Excel file with hyperlinks and date formatting.

---

## 🔍 Features

- Scrapes multiple pages of listings from each source
- Filters job ads using neuroscience- and position-related keywords
- Extracts structured job metadata, including employer, location, description, and application URL
- Parses and formats posting dates for consistent output
- Saves results to an Excel file with:
  - Sorted and ordered columns
  - Hyperlinks to each job ad
  - Date formatting for easy tracking
- Automatically chooses save directory based on the computer name

---

## 📦 Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`
- `pandas`
- `openpyxl`
- `xlsxwriter`

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python jobads_checker.py
```

### Debug mode (limit to 3 pages per site):

```bash
python jobads_checker.py --debug
```

An Excel file named `job_ads_YYMMDD_HHMMSS.xlsx` will be saved to a preset folder, depending on the computer you're running it on (defined in `computer_dirs`).

---

## 🧠 Keyword Filtering

Jobs are selected based on the presence of:

- **Position-related terms:** e.g., `tenure-track`, `assistant professor`, `open rank`, etc.
- **Neuroscience-related terms:** e.g., `neuro`, `brain`, `cognit`, `psych`, etc.

For **SfN**, only position-related keywords are required.  
For **Nature** and **Science Careers**, both position and neuroscience keywords must be present.

---

## 🗂 Output Columns (subset)

- **Source**: SfN / Nature / Science
- **Date Posted**
- **University**
- **Title**
- **Location**
- **Deadline**
- **Description**
- **Link** (clickable hyperlink)

---

## 🖥 Custom Save Directory

You can define custom output directories per device in the `computer_dirs` dictionary. The script will detect the current machine's hostname and route the Excel file accordingly.

---

## 📝 Notes

- This script is currently configured for three specific sites using their public HTML structure.
- It may require updates if those websites change their layout.
- For sites that load jobs dynamically with JavaScript, Selenium may be required (currently not implemented here).

---

## 📜 License

MIT License

---

## 🙏 Acknowledgments

Created by [Shin Kira](https://github.com/shinkira) to streamline the academic job search process for neuroscience researchers. Contributions welcome!
