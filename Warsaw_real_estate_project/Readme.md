# Warsaw Real Estate Analytics

## Project Overview
This project aims to create a  **ETL (Extract, Transform, Load)** pipeline to analyze the real estate market in Warsaw. The goal is to check price differences between districts, identify trends, and present these insights in a user-friendly way using **Streamlit**.

The project consists of three main components:
* **Extract:** web scraping data from `otodom.pl`.
* **Transform:** cleaning and exploratory data analysis.
* **Load:** loading data into SQlite databse.
* **Visualize:** interactive dashboard in Streamlit.

---

## Data Source & Original Dataset
The analysis is based on data scraped from the Polish real estate listing site, `otodom.pl`.

> **Note:** The initial version of the dashboardis based on the the dataset named `otodom_scraped_2026-01.csv`. This file contains the original data scraped by me.
---

## How to Run the Project

### Option 1: Automated Pipeline (Recommended)
This is the designed way to execute the workflow.

1. Open the terminal in VS Code or command line (replace `path/to/` with your actual folder path):
   ```bash
   cd path/to/Warsaw_real_estate_project
   ```

2. Run the main pipeline script:
   ```bash
   python run_pipeline.py
   ```

#### Important Note regarding Web Scraping:
By default, the actual scraping process in `run_pipeline.py` is excluded (commented out) to allow for a quicker demonstration of the dashboard using existing data.

**To run the fresh scraper:**
1. Ensure you have the correct **chromedriver** (you can find a way how to check it in this [video](https://www.youtube.com/watch?v=vWO5C66gLFU)) installed and paths configured in `otodom_scraper.py`, you can change them in **lines 20 and 26** of the file.
2. Uncomment **line 29** in `run_pipeline.py`.
3. **Warning:** The scraping process may take 2-3 hours depending on the volume of data.

---

### Option 2: Manual Execution
If the automated pipeline does not work, then you can run the steps individually in the following order.

**Prerequisite:** Open terminal or command line and go to the folder (same as in the Option 1):
```bash
cd path/to/Warsaw_real_estate_project
```

#### 1. Scrape Data (skip for quicker result)
Fill in the directory and driver paths, then run:

```bash
python otodom_scraper.py
```

#### 2. Clean & Analyze
Run the Jupyter Notebook: `Cleaning_and_EDA.ipynb`

#### 3. Setup Database
Prepare the database for the dashboard:

```bash
python warsaw_flats_db_setup.py
```

#### 4. Launch Dashboard
Run the Streamlit dashboard:

```bash
streamlit run warsaw_flats_dashboard.py
```