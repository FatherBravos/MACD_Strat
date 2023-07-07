import os
import gzip
import pandas as pd
import numpy as np
import shutil
# path to the Darwinex Data repo
dir_path = "C:\\Users\\49176\\Desktop\\Darwinex Data\\AUDJPY"

slice=30
# output directory
output_dir = "C:\\Users\\49176\\Desktop\\Darwinex Data"

# data dictionary to hold dataframes
data = {'BID': [], 'ASK': []}
directory="C:\\Users\\49176\\Desktop\\Darwinex Data\\temp_files"

if not os.path.exists(directory):
    os.makedirs(directory)
else:
    shutil.rmtree(directory)
    os.makedirs(directory)
# resolutions for OHLC

resolutions = ['1min', '1H', '1D']

def cooncat(dfs):
    d={'1min':None, '1H':None, '1D':None}
    concatenated_df = pd.concat(dfs)

    for resolution in resolutions:
        # Resample the concatenated data to given resolution
        df_resampled = concatenated_df.resample(resolution).agg(
            {'price': ['first', 'max', 'min', 'last'], 'volume': 'sum'})

        # flatten column names
        df_resampled.columns = ['open', 'high', 'low', 'close', 'volume']

        # Keep original timestamp
        df_resampled['timestamp'] = df_resampled.index.values.astype(np.int64) // 10 ** 6

        # remove rows where no data available
        final_df = df_resampled[df_resampled['volume'] != 0]

        # Save with original timestamp
        final_df.reset_index(drop=True, inplace=True)
        final_df = final_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        d[resolution]=final_df
    return d


# iterate through files in directory
for order_type in ['ASK','BID']:
    # check if file is .log.gz
    for i, filename in enumerate(os.listdir(dir_path)):
        if filename.endswith('.log.gz') and order_type in filename :

            # print status message
            #print(f'Processing {order_type} data from {filename}...')

            # open file
            with gzip.open(os.path.join(dir_path, filename), 'rt') as f:
                # read file into pandas dataframe
                df = pd.read_csv(f, header=None, names=['timestamp', 'price', 'volume'])

                # convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

                # set datetime as index
                df.set_index('datetime', inplace=True)

                # append to data dictionary
                data[order_type].append(df)
                if len(data[order_type])%slice==0  :
                    dic=cooncat(data[order_type])
                    for reso,dataf in dic.items():
                        dataf.to_csv(f'{directory}\\{order_type}_{reso}_{i}.csv',index=False)
                        data[order_type]=[]
    try:
        dic = cooncat(data[order_type])
        for reso, dataf in dic.items():
            dataf.to_csv(f'{directory}\\{order_type}_{reso}_{i}.csv')
            data[order_type] = []
    except Exception:
        pass

# concatenate
for order in ['ASK','BID']:
    for reso in resolutions:
        dfs=[pd.read_csv(os.path.join(directory,fnm)) for fnm in os.listdir(directory) if f'{order}_{reso}' in fnm]
        c_dfs=pd.concat(dfs)
        c_dfs=c_dfs.drop('Unnamed: 0',axis=1)
        c_dfs = c_dfs.groupby(['timestamp'], as_index=False).agg(
            {'open': 'first','high': 'max', 'low': 'min','close': 'last','volume': 'sum'})
        c_dfs.sort_values(by='timestamp',inplace=True)
        c_dfs.reset_index(drop=True, inplace=True)
        c_dfs.to_csv(os.path.join(output_dir, f'AUDJPY_{order}_{reso}.csv'), index=False)


#shutil.rmtree(directory)