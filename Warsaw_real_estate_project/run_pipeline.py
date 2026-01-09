import subprocess
import sys

def run_command(command, step_name):
    #running commands in terminal
    print(f' Starting {step_name}')
    
    try:
        subprocess.check_call(command, shell=True)
        print(f' {step_name} was run succesfully')
    except subprocess.CalledProcessError as e:
        print(f' Error at {step_name} ')
        sys.exit(1)

def main():
    python_cmd = sys.executable


    #----------- Installing necessary libraries  -----------
    run_command(
        f'{python_cmd} -m pip install -r requirements.txt', 
        'Installing necessary libraries'
    )


    #----------- SCRAPER PART -----------
    # run_command(f'{python_cmd} otodom_screaper.py', 'Scraping data')
    print('Scraping was skipped, already downloaded data will be used. If you wish to scrape data, please check run_pipeline.py')


    #----------- CLEANING -----------
    run_command(
        f'{python_cmd} -m jupyter nbconvert --to notebook --execute --inplace Cleaning.ipynb',
        'Cleaning and processing data'
    )


    #----------- DATABASE SETUP -----------
    run_command(
        f'{python_cmd} warsaw_flats_db_setup.py',
        'Database setup'
    )


    #----------- RUNNING STREAMLIT DASHBOARD -----------
    run_command(
        f'{python_cmd} -m streamlit run warsaw_flats_dashboard.py',
        'Streamlit dashboard'
    )


if __name__ == '__main__':
    main()