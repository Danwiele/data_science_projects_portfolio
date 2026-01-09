import pandas as pd
import sqlite3
import os
import re
import numpy as np

db_path = 'warsaw_flats.db'
file_pattern = r'^flats_20\d{2}-\d{2}\.csv$'


#----------- DATATYPE MAPPING -----------
dtype_map = {
    'id': 'Int64', 
    'price': 'float64',
    'rent': 'float64',
    'area': 'float64',
    'price_per_sq_m': 'float64',
    'no_rooms': 'Int64',
    'building_type': 'category',
    'no_floor': 'Int64',
    'building_floors_num': 'Int64',
    'windows_type': 'category',
    'construction_status': 'category',
    'building_ownership': 'category',
    'lat': 'float64',
    'long': 'float64',
    'district': 'category',
    'built_year' :'Int64',
    'url': 'string',
    'rent_per_sq_m': 'float64',
    'lift': 'Int8',
    'balcony': 'Int8',
    'garage': 'Int8',
    'basement': 'Int8',
    'separate_kitchen': 'Int8',
    'usable_room': 'Int8',
    'air_conditioning': 'Int8',
    'terrace': 'Int8',
    'garden': 'Int8',
    'two_storey': 'Int8',
    'is_primary': 'Int8',
    'date_scraped': 'string' 
}


#----------- CREATING SQL TABLE -----------
def create_table_if_not_exists(conn):
    flats_table = """
    CREATE TABLE IF NOT EXISTS flats (
        id INTEGER PRIMARY KEY,
        price REAL,
        rent REAL,
        area REAL,
        price_per_sq_m REAL,
        no_rooms INTEGER,
        building_type TEXT,
        no_floor INTEGER,
        building_floors_num INTEGER,
        windows_type TEXT,
        construction_status TEXT,
        building_ownership TEXT,
        lat REAL,
        long REAL,
        district TEXT,
        built_year INTEGER,
        url TEXT,
        rent_per_sq_m REAL,
        lift INTEGER,
        balcony INTEGER,
        garage INTEGER,
        basement INTEGER,
        separate_kitchen INTEGER,
        usable_room INTEGER,
        air_conditioning INTEGER,
        terrace INTEGER,
        garden INTEGER,
        two_storey INTEGER,
        is_primary INTEGER,
        date_scraped DATE
    );
    """
    cursor = conn.cursor()
    cursor.execute(flats_table)
    conn.commit()


#----------- CHECKING FOR ALL FILES IN THE DIRECTORY -----------
all_files = os.listdir('.')
csv_files = [f for f in all_files if re.match(file_pattern, f)]
csv_files.sort()

#connecting to the db
conn = sqlite3.connect(db_path)


#-----------  IF TABLE DOESN'T EXIST WE CREATE ONE -----------
create_table_if_not_exists(conn)


#getting the already existing ids
try:
    existing_ids = pd.read_sql('SELECT id FROM flats', conn)
    existing_ids_set = set(existing_ids['id'].tolist())
    print(f'There are {len(existing_ids_set)} offers in db.')
except Exception as e:
    existing_ids_set = set()
    print(f'Starting with empty set or error: {e}')
    
    
#-----------  LOADING FILE -----------
for filename in csv_files:
    print(f'Loading file {filename}')

    try:
        df = pd.read_csv(
            filename, 
            sep=';', 
            quotechar='"', 
            dtype=dtype_map
        )
    except Exception as e:
        print(f'Error reading {filename}: {e}')
        continue

    if 'id' not in df.columns:
        print(f'No id column in {filename}')
        continue

    #filtering duplicates
    df_new = df[~df['id'].isin(existing_ids_set)].copy()
    
    if not df_new.empty:
        #-----------  INSERTING DATA -----------
        
        #changing nan to None so  SQLite won't raise an error
        df_new = df_new.replace({np.nan: None})
        
        #dynamic insert
        columns = list(df_new.columns)
        placeholders = ', '.join(['?'] * len(columns))
        columns_str = ', '.join(columns)
        sql_insert = f"INSERT INTO flats ({columns_str}) VALUES ({placeholders})"
        
        #converting data to list so it can be loaded
        data_to_insert = df_new.values.tolist()
        
        cursor = conn.cursor()
        try:
            cursor.executemany(sql_insert, data_to_insert)
            conn.commit()
            
            #updating ids
            new_ids = df_new['id'].tolist()
            existing_ids_set.update(new_ids)
            
            print(f'Added {len(df_new)} unique offers.')
            
        except sqlite3.Error as e:
            print(f'Error inserting data from {filename}: {e}')
            
    else:
        print('No new offers added')

conn.close()
print('DB creation/upload finished.')