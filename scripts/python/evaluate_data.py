# this is python code that is used to reverse engineer the differences between the
# raw / processed climate obs data
# code is messy, but leaving here as it is a good starting place for doing some q/a
# operations.

import pandas as pd
import datetime


def extract_site_id(site_name):
    """
    Extract the site id from the site name
    :param site_name: A site name, examples of the format include:
        * 1A01P  Yellowhead Lake
        *
    :return: string
    """
    return site_name.split(' ')[0]


# read in the files
date_cols=['DATE (UTC)']
df = pd.read_csv('old_scripts/sample_data/8-29-2023/TA-8-29.csv',
                 parse_dates=date_cols,
                 encoding="ISO-8859-1")
df = df.rename(columns={'DATE (UTC)': 'date_col'})

start_date = datetime.datetime.strptime('2023-08-28 7:00', '%Y-%m-%d %H:%M')
end_date = datetime.datetime.strptime('2023-08-29 7:00', '%Y-%m-%d %H:%M')
df_date_filter = df.query('date_col >= @start_date and date_col <= @end_date')

df_format = df_date_filter.melt(id_vars=['date_col'],
        var_name='site',
        value_name='temperature')
# reformat the site columns date to only include the site id.
df_format['site'] = df_format['site'].apply(extract_site_id)

# summarize, getting the min and the max temperature
df_min_max_t = df_format.groupby('site')['temperature'].agg([('MINT', 'min'), ('MAXT', 'max')]).reset_index()
# inject in the date column
df_min_max_t.insert(1, 'DATE', end_date)

df_min_max_t



## Reading in the precipitation data

df_pc = pd.read_csv('old_scripts/sample_data/8-29-2023/PC-8-29.csv',
                 parse_dates=date_cols,
                 encoding="ISO-8859-1")
df_pc = df_pc.rename(columns={'DATE (UTC)': 'date_col'})
start_date = datetime.datetime.strptime('2023-08-28 7:00', '%Y-%m-%d %H:%M')
end_date = datetime.datetime.strptime('2023-08-29 7:00', '%Y-%m-%d %H:%M')
df_pc_date_filter = df_pc.query('date_col == @start_date or date_col == @end_date')
df_pc_format = df_pc_date_filter.melt(id_vars=['date_col'],
        var_name='site',
        value_name='precipitation')
# concat the 'site' column to only include site id
df_pc_format['site'] = df_pc_format['site'].apply(extract_site_id)


#df_pc_cum = df_pc_format.groupby('site').agg({'precipitation': 'diff'})

#df_pc_format['precip_diff'] = df_pc_format['precipitation'].diff()
df_pc_format['cumulative_precip'] = df_pc_format.sort_values(['date_col', 'site']).groupby('site')['precipitation'].diff()
df_precip_accum = df_pc_format.groupby(['site']).agg({'cumulative_precip': 'max'}).reset_index()
df_precip_accum


# do the join
result = pd.merge(df_min_max_t, df_precip_accum, how="outer", on=["site"])
result


# next steps:
#  b) attempt to join this dataframe to the other dataframe with the min / max temp.

# df['New']=df.sort_values([']).groupby('ID')['test_result'].diff()

