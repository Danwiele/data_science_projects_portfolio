import streamlit as st
import polars as pl
from polars import col
import plotly.express as px
import os
import sqlite3
import pandas as pd
import re


#----------- PAGE SETUP ----------- 
st.set_page_config(
    page_title='Warsaw Real Estate Market', 
    layout='wide', 
    initial_sidebar_state='auto'
    )


#----------- LOADING DATA  ----------- 
def load_data():
    
    file_pattern = r'^flats_20\d{2}-\d{2}\.csv$'
    directory = '.' 
    
    #all files with the given pattern
    if not os.path.exists(directory):
        st.error(f'Directory {directory} not found')
        st.stop()
        
    all_files = os.listdir(directory)
    matching_files = [f for f in all_files if re.match(file_pattern, f)]
    matching_files.sort()
    
    if not matching_files:
        st.error(f'No files found matching pattern: {file_pattern}')
        st.stop()
        
    dataframes = []
    
    #reading files
    for filename in matching_files:
        try:
            df_temp = pl.read_csv(filename, separator=';', quote_char='"')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            
            dataframes.append(df_temp)
            
        except Exception as e:
            st.warning(f'Error loading file {filename}: {e}. Skipping this file.')
            
    if not dataframes:
        st.error('Failed to load any data files')
        st.stop()
        
    #combining files into dataframe
    try:
        df = pl.concat(dataframes, how="vertical")
        
        if 'id' in df.columns:
            df = df.unique(subset='id', keep='last', maintain_order=True)
            
    except Exception as e:
        st.error(f'Error concatenating files (check if column names/types match): {e}')
        st.stop()
        
    try:
        # column mapping
        expected_cols = [
            'lift', 'balcony', 'garage', 'basement', 'separate_kitchen', 
            'usable_room', 'air_conditioning', 'terrace', 'garden', 'two_storey',
            'building_ownership', 'construction_status', 'windows_type', 
            'no_floor', 'building_floors_num', 'is_primary', 'price_per_sq_m', 'built_year'
        ]
        
        for col in expected_cols:
            if col not in df.columns and col in expected_cols[:10]: 
                df = df.with_columns(pl.lit(0).alias(col))
        
        return df
        
    except Exception as e:
        st.error(f'Error processing data columns: {e}')
        st.stop()

flats = load_data()


#----------- UNIQUE VALUES IN A COLUMN ----------- 

#getting unique values in each column
def get_unique_list(df, col):
    if col in df.columns:
        return df[col].drop_nulls().unique().sort().to_list()
    return []


#----------- RESET NUMERIC KEYS FUNCTION -----------
def reset_numeric_filter(col_name, default_min, default_max):
    st.session_state[f'input_min_{col_name}'] = default_min
    st.session_state[f'input_max_{col_name}'] = default_max


#----------- CREATING FUNCTION FOR FILTERING OF NUMERIC VALUES -----------

def numeric_filter(df, col_name, label, step=1):
    
    #setting min and max values
    min_num_val = int(df.select(col(col_name).min()).item())
    max_num_val = int(df.select(col(col_name).max()).item())

    #check if a given column has data
    if min_num_val is None or max_num_val is None:
        st.warning(f'No data{label}')
        return None, None
   
    #setting up cols for min and max filter
    col1, col2 = st.columns(2) 

    with col1:
        chosen_min = st.number_input(
            f'Min {label}', 
            min_value=min_num_val, 
            max_value=max_num_val, 
            value=min_num_val,   
            step=step,
            key=f'input_min_{col_name}' 
        )
    
    with col2:
        chosen_max = st.number_input(
            f'Max {label}', 
            min_value=min_num_val, 
            max_value=max_num_val, 
            value=max_num_val,  
            step=step,
            key=f'input_max_{col_name}'
        )
    
    #applying reset button logic
    is_changed = (chosen_min != min_num_val) or (chosen_max != max_num_val)
    
    if is_changed:
        st.button(
            f'↺ Reset {label}', 
            key=f'btn_reset_{col_name}',
            on_click=reset_numeric_filter, 
            args=(col_name, min_num_val, max_num_val)
        )
    
    #check
    if chosen_min > chosen_max:
        st.error(f'Minimum value cant be higher than Maximum for {label}')
        st.stop()

    #returning the values
    return chosen_min, chosen_max


#----------- CREATING FUNCTION FOR MULTISELECT DROPDOWN -----------

def multiselect(df, multi_col, name_to_display, default_vals=[]):
    unique_vals = get_unique_list(
        df, 
        multi_col)
    
    selected_vals = st.multiselect(
        name_to_display, 
        unique_vals, 
        default=default_vals
        )
    
    return selected_vals


#----------- CREATING FILTER PANE -----------
with st.sidebar:
    st.title('Filters',)
    
    #market type filter
    st.subheader('Market Type')
    market_origin_opt = st.radio(
        'Source:',
        ['All', 'Primary Market', 'Secondary Market'],
        index=0
    )
    
   #district filter
    with st.expander('Location', expanded=False):
        selected_districts = multiselect(flats, 'district', 'District', get_unique_list(flats, 'district'))
        
    #price filter
    with st.expander('Price', expanded=False):
        min_price, max_price = numeric_filter(flats, 'price', 'Price (PLN)', step=5000)

    #price per sqm filter
    with st.expander('Price per m²', expanded=False):
        min_price_per_sqm, max_price_per_sqm = numeric_filter(flats, 'price_per_sq_m', 'Price (PLN)', step=200)
    
    #area filter
    with st.expander('Area', expanded=False):
        min_area, max_area = numeric_filter(flats, 'area', 'Area (m²)')

    #floor filter
    with st.expander('Floor', expanded=False):
        min_floor, max_floor = numeric_filter(flats, 'no_floor', 'Floor number')
        
    #floor filter
    with st.expander('Build year', expanded=False):
        min_year, max_year = numeric_filter(flats, 'built_year', 'Year')

    #building details
    with st.expander('Building Details', expanded=False):
        
        sel_ownership = multiselect(flats, 'building_ownership', 'Ownership', [] )
        
        sel_status = multiselect(flats, 'construction_status', 'Construction Status', [] )

    #extras
    with st.expander('Apartment features', expanded=False):
        extras = {
            'lift': 'Lift', 
            'balcony': 'Balcony', 
            'garage': 'Garage', 
            'air_conditioning': 'A/C', 
            'garden': 'Garden', 
            'terrace': 'Terrace',
            'basement': 'Basement'
        }
        selected_extras = []
        for col_name, label in extras.items():
            if st.checkbox(label, key=f'chk_{col_name}'):
                selected_extras.append(col_name)


#----------- FILTERING LOGIC -----------
if not selected_districts: selected_districts = get_unique_list(flats, 'district')

#mask
mask = (
    (col('district').is_in(selected_districts)) &
    (col('price').is_between(min_price, max_price)) &
    (col('area').is_between(min_area, max_area)) &
    (col('price_per_sq_m').is_between(min_price_per_sqm, max_price_per_sqm))&
    (
        (col('built_year').is_between(min_year, max_year)) | 
        (col('built_year').is_null()) #handling null years
    )
)
#apply primary/secondary filter
if market_origin_opt == 'Primary Market':
    mask = mask & (col('is_primary') == 1)
elif market_origin_opt == 'Secondary Market':
    mask = mask & (col('is_primary') == 0)

df_filtered = flats.filter(mask)

#filtering extras
for extra in selected_extras:
    if extra in df_filtered.columns:
        df_filtered = df_filtered.filter(col(extra) == 1)

#apply categories
if sel_ownership:
    df_filtered = df_filtered.filter(col('building_ownership').is_in(sel_ownership))
if sel_status:
    df_filtered = df_filtered.filter(col('construction_status').is_in(sel_status))

#apply floors
df_filtered = df_filtered.filter(
    ((col('no_floor') >= min_floor) & (col('no_floor') <= max_floor)) |
    (col('no_floor').is_null())  #including null values
)

#pandas for plotly 
df_pd = df_filtered.to_pandas()


#----------- DASHBOARD -----------
st.title('Warsaw Real Estate Overview')


#----------- KPIS -----------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
median = df_pd['price'].median() if not df_pd.empty else 0
median_sqm = df_pd['price_per_sq_m'].median() if not df_pd.empty else 0
median_area = df_pd['area'].median() if not df_pd.empty else 0



kpi1.metric('Total Offers', f'{len(df_pd):,}'.replace(',', ' '))
kpi2.metric('Median Price', f'{median:,.0f}'.replace(',', ' ') + ' PLN')
kpi3.metric('Median Price/m²', f'{median_sqm:,.0f}'.replace(',', ' ') + ' PLN')
kpi4.metric('Median Area in m²', f'{median_area:,.0f}'.replace(',', ' '))

st.divider()

#----------- CHARTS -----------
c_map, c_distplot = st.columns([2, 2])

with c_map:
    
    #setting up colors, otherwise the scale wouldn't show difference well enough 
    min_color = df_pd['price_per_sq_m'].quantile(0.01)
    max_color = df_pd['price_per_sq_m'].quantile(0.95)
    
    
    
    st.subheader('Offer Map')
    if not df_pd.empty:
        fig_map = px.scatter_mapbox(
            df_pd, 
            lat='lat', 
            lon='long', 
            color='price_per_sq_m', 
            size='area',
            color_continuous_scale='RdYlGn_r', 
            range_color=[min_color, max_color],
            zoom=9.5, 
            height=500,
            custom_data=['district', 'price', 'area', 'price_per_sq_m', 'built_year'],
            labels={'price_per_sq_m': 'Price/m²'}
        )
        fig_map.update_traces(hovertemplate=(
            "<b>District</b>: %{customdata[0]}<br>"
            "<b>Price</b>: %{customdata[1]:,.0f} PLN<br>"
            "<b>Area</b>: %{customdata[2]} m²<br>"
            "<b>Price/m²</b>: %{customdata[3]:,.0f} PLN<br>"
            "<b>Year of build</b>: %{customdata[4]}"
            "<extra></extra>"
        ))
        fig_map.update_layout(mapbox_style='carto-darkmatter', margin={'r':0,'t':0,'l':0,'b':0})
        st.plotly_chart(fig_map, width='stretch')


with c_distplot:
    #dictionary for picklist
    dist_options = {
        'price': 'Price', 
        'area': 'Area', 
        'price_per_sq_m': 'Price/m²', 
        'built_year': 'Year of build', 
        'no_rooms': 'Number of rooms', 
        'no_floor': 'Floor'
    }
    
    #creating selectbox
    selected_col_name = st.selectbox(
        'Choose a parameter to display', 
        list(dist_options.keys()), 
        format_func=lambda x: dist_options[x]
    )

    #getting labels
    lbl = dist_options[selected_col_name]


    st.subheader(f'Distribution of {lbl}')
    if not df_pd.empty:
        fig_dist = px.histogram(
            df_pd, 
            x=selected_col_name, 
            nbins=50, 
            marginal='box', 
            color_discrete_sequence=['#1E6583']
        )
        
       #formatting hover
        fig_dist.update_traces(hovertemplate="<b>" + lbl + "</b>: %{x}<br><b>Number of occurrences</b>: %{y}<extra></extra>")


        fig_dist.update_layout(
            xaxis_title=lbl, 
            yaxis_title='Number of offers',
            showlegend=False,
            margin={'r':0,'t':40,'l':0,'b':0}
        )
        
        st.plotly_chart(fig_dist, width='stretch')

#correl plot and scatter plot
c_top_districts, c_corel  = st.columns([1, 1])

with c_corel:
    st.subheader('Price correlation matrix')

    #dictionary for good looking axis
    corr_labels = {
        'price': 'Price', 
        'area': 'Area', 
        'built_year': 'Year of build', 
        'no_rooms': 'Rooms', 
        'no_floor': 'Floor',
        'is_primary': 'Primary market',
        'lift': 'Lift', 
        'balcony': 'Balcony', 
        'garage': 'Garage', 
        'air_conditioning': 'A/C', 
        'garden': 'Garden', 
        'terrace': 'Terrace',
        'basement': 'Basement'

    }

    #checking if passed columns are in df
    available_cols = [c for c in corr_labels.keys() if c in df_pd.columns]

    if available_cols:
        #evaluating correlation 
        corr_matrix = df_pd[available_cols].corr().round(2)

        #setting up labels
        corr_lbl = [corr_labels[col] for col in corr_matrix.columns]

        #create plot
        fig_corr = px.imshow(
            corr_matrix,
            x=corr_lbl, 
            y=corr_lbl, 
            text_auto=True,
            aspect="auto",
            color_continuous_scale='PiYG',
            zmin=-1, zmax=1,
            origin='lower',
        )
        fig_corr.update_layout(margin={'r':0,'t':40,'l':0,'b':0})
        st.plotly_chart(fig_corr, width='stretch')
    
    #if there's to little data raise a warning
    else:
        st.warning('Not enough data to calculate correlation')

with c_top_districts:
    st.subheader('Districts by median Price/m²')

    #getting median for districts
    district_stats = df_pd.groupby('district')['price_per_sq_m'].median().reset_index()
    district_stats = district_stats.sort_values('price_per_sq_m', ascending=True)

    #create plot
    fig_ranking = px.bar(
        district_stats,
        x='price_per_sq_m',
        y='district',
        orientation='h',
        color='price_per_sq_m',
        color_continuous_scale='Viridis',
        labels={'price_per_sq_m': 'Price/m²'},
        text_auto='.0f'
    )
    fig_ranking.update_traces(textfont_size=16, textangle=0, textposition='outside', cliponaxis=False)
    fig_ranking.update_traces(hovertemplate="<b>%{y}</b><br>Median Price: %{x:,.0f} PLN/m²<extra></extra>")
    fig_ranking.update_layout(xaxis_title='Price/m²', yaxis_title="")
    st.plotly_chart(fig_ranking, width='stretch')



st.divider()


# --- TOP DEALS SECTION SQL ---
st.header('Top Deals')

#connecting to the db
conn = sqlite3.connect('warsaw_flats.db')

#setting up columns
c_ctrl1, c_ctrl2 = st.columns([1, 2])
with c_ctrl1:
    top_n = st.selectbox('Number of results:', [5, 10, 25, 50], index=1)
with c_ctrl2:
    sort_col_map = {
        'Total Price (PLN)': 'price',
        'Price per m² (PLN/m²)': 'price_per_sq_m',
        'Area (m²)': 'area'
    }
    sort_selection = st.selectbox('Sort by column:', list(sort_col_map.keys()))
    sort_col_tech = sort_col_map[sort_selection]


#creating conditions for filtering the data via SQL
conditions = []

#districts
if selected_districts:
    safe_districts = "', '".join(selected_districts)
    conditions.append(f"district IN ('{safe_districts}')")

#market type
if market_origin_opt == 'Primary Market':
    conditions.append("is_primary = 1")
elif market_origin_opt == 'Secondary Market':
    conditions.append("is_primary = 0")

#price
if 'min_price' in locals():
    conditions.append(f"price BETWEEN {min_price} AND {max_price}")
#area
if 'min_area' in locals():
    conditions.append(f"area BETWEEN {min_area} AND {max_area}")
#price per sqm
if 'min_price_per_sqm' in locals():
    conditions.append(f"price_per_sq_m BETWEEN {min_price_per_sqm} AND {max_price_per_sqm}")
#year
if 'min_year' in locals():
    conditions.append(f"(built_year BETWEEN {min_year} AND {max_year} OR built_year IS NULL)")
#floor
if 'min_floor' in locals():
    conditions.append(f"(no_floor BETWEEN {min_floor} AND {max_floor} OR no_floor IS NULL)")
#ownership
if sel_ownership:
    formatted_own = "', '".join(sel_ownership)
    conditions.append(f"building_ownership IN ('{formatted_own}')")
if sel_status:
    formatted_status = "', '".join(sel_status)
    conditions.append(f"construction_status IN ('{formatted_status}')")

#extras
for extra in selected_extras:
    conditions.append(f"{extra} = 1")

#combining conditions into where clause
where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""


#setting up columns to display
col_config = {
    'district': 'District',
    'price': st.column_config.NumberColumn('Total Price', format='%d PLN'),
    'price_per_sq_m': st.column_config.NumberColumn('Price/m²', format='%d PLN'),
    'no_rooms': st.column_config.NumberColumn('Rooms', format='%.0f'),
    'no_floor': st.column_config.NumberColumn('Floor', format='%.0f'),
    'area': st.column_config.NumberColumn('Area', format='%.2f m²'),
    'url': st.column_config.LinkColumn('Offer Link'),
}
cols_sql = "district, price, price_per_sq_m, area, no_rooms, no_floor, url"

#table layout
col_low, col_high = st.columns(2)

with col_low:
    st.subheader(f' Lowest {sort_selection}')
    
    
    query_low = f"""
        SELECT {cols_sql}
        FROM flats
        {where_clause}
        ORDER BY {sort_col_tech} ASC
        LIMIT {top_n}
    """
    
    try:
        df_low = pd.read_sql(query_low, conn)
        if not df_low.empty:
            st.dataframe(
                df_low,
                hide_index=True,
                column_config=col_config,
                width='stretch'
            )
        else:
            st.info('No results for selected filters')
    except Exception as e:
        st.error(f'SQL error {e}')

with col_high:
    st.subheader(f' Highest {sort_selection}')
    

    query_high = f"""
        SELECT {cols_sql}
        FROM flats
        {where_clause}
        ORDER BY {sort_col_tech} DESC
        LIMIT {top_n}
    """
    
    try:
        df_high = pd.read_sql(query_high, conn)
        if not df_high.empty:
            st.dataframe(
                df_high,
                hide_index=True,
                column_config=col_config,
                width='stretch'
            )
        else:
            st.info('No results for selected filters')
    except Exception as e:
        st.error(f'SQL error {e}')

#closing connection
conn.close()

#all data table
st.subheader('Collected data')
st.dataframe(
    df_pd,
    width='stretch',
    column_config={'url': st.column_config.LinkColumn('Link')},
    hide_index=True
)