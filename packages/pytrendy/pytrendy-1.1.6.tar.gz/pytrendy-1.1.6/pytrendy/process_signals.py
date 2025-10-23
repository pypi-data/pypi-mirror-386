"""**Signal Smoothing and Region Classification**"""

import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from .post_processing.segments_refine import GROUPING_DISTANCE

def process_signals(df:pd.DataFrame, value_col: str):
    """
    Applies signal processing techniques to classify regions of a time series.

    This function uses Savitzky-Golay smoothing and rolling statistics to identify:

    - Flat regions (low standard deviation)
    - Noisy regions (low signal-to-noise ratio)
    - Uptrends and downtrends (based on smoothed derivatives)

    Flags are added to the DataFrame to indicate each region type:

    - `flat_flag`: 1 for flat regions
    - `noise_flag`: 1 for noisy regions
    - `trend_flag`: 
    
        - 1 for uptrend
        - -1 for downtrend
        - -2 for flat
        - -3 for noise

    Args:
        df (pd.DataFrame): 
            Input time series data with a datetime index and signal column.
        value_col (str): 
            Name of the column containing the signal to process.

    Returns:
        `pd.DataFrame`: Modified DataFrame with additional columns.
           
            - `'smoothed'`, `'smoothed_std'`, `'snr'`, `'smoothed_deriv'`
            - `'flat_flag'`, `'noise_flag'`, `'trend_flag'`
    """
    WINDOW_SMOOTH = 15
    WINDOW_FLAT = int(WINDOW_SMOOTH*0.5)
    WINDOW_NOISE = int(WINDOW_SMOOTH*0.5)

    THRESHOLD_NOISE = 2.5 # Sensitivity to detecting noise (recommended 0-10)
    THRESHOLD_SMOOTH = 0.25 # Sensitivity to detecting trends (recommended 0-0.5)

    # 1. Noise detection via SNR. 
    # 1.1 Compute the SNR
    df['signal'] = df[value_col].rolling(window=WINDOW_NOISE, center=True, min_periods=1).mean()
    df['noise'] = df[value_col] - df['signal']
    df['snr'] = 10 * np.log10(df['signal']**2 / df['noise']**2)

    # 1.2 Define noise flag when SNR & not all zero
    df['noise_flag'] = 0
    df.loc[(df['snr'] <= THRESHOLD_NOISE), 'noise_flag'] = 1
    
    # 1.3 Double check & refresh noise flag. Distinguish noise from abrupt change.
    df['noise_flag_diff'] = df['noise_flag'].diff()
    noise_starts = df.loc[df['noise_flag_diff'] == 1].index
    noise_ends = df.loc[df['noise_flag_diff'] == -1].index
    
    # 1.3.1 Construct noise segments list based on flag_diff
    noise_segments = []
    for noise_start in noise_starts: # Loops from first start onwards
        after_ends = [end for end in noise_ends if end > noise_start]
        if len(after_ends) > 0:
            noise_end = after_ends[0]
        else:
            noise_end = min(noise_start + pd.Timedelta(days=1), df.index[-1])
        noise_segments.append(dict(start=noise_start, end=noise_end))

    if len(noise_ends) > 0: # Adds noise end with no start if at beginning
        noise_end = noise_ends[0]
        early_starts = [start for start in noise_starts if start < noise_end]
        if len(early_starts) == 0:
            noise_start = max(noise_end - pd.Timedelta(days=1), df.index[0])
            noise_segments.insert(0, dict(start=noise_start, end=noise_end))

    # 1.3.2 Group noise segments if within a close enough distance of each other
    if len(noise_segments) <= 1: 
        noise_segments_grouped = noise_segments
    else: # only try group logic if > 1 segments to group
        noise_segments_grouped = []
        prev_seg = noise_segments[0].copy()
        for i, seg in enumerate(noise_segments[1:]):
            width = (seg['start'] - prev_seg['end']).days
            if width <= GROUPING_DISTANCE:
                new_seg = {'start': prev_seg['start'], 'end': seg['end']}
                noise_segments_grouped.append(new_seg)
            else:
                noise_segments_grouped.append(prev_seg) # append prev if no grouping
                if (i == len(noise_segments) - 2): # append curr if on last with no grouping
                    noise_segments_grouped.append(seg)
            prev_seg = seg.copy()

    # 1.3.3 Update noise flag to larger groupings, so segments continuous to then refine
    if noise_segments_grouped != noise_segments:
        df.loc[:, 'noise_flag'] = 0
        for seg in noise_segments_grouped:
            df.loc[seg['start']:seg['end'], 'noise_flag'] = 1
        
    # 1.3.4 Refine the noise segments early
    for segment in noise_segments_grouped:

        width = (pd.to_datetime(segment['end']) - pd.to_datetime(segment['start'])).days
        start = pd.to_datetime(segment['start']) - pd.Timedelta(days=1)
        end = pd.to_datetime(segment['end']) + pd.Timedelta(days=1)

        # Cap to bounds of df in case at beginning or end.
        start = max(start, df.index.min())
        end = min(end, df.index.max())
        width_padded = end - start

        # Cater for edge coise of noise, but its actually an abrupt trend.
        diff = abs(df.loc[end, value_col] - df.loc[start, value_col])
        small_value = df.loc[df[value_col] > 0, value_col].quantile(0.40)
        abrupt_ends = diff > small_value

        # check if possibly abrupt, provided that window is narrow enough
        if (width <= 4) and abrupt_ends:
            df.loc[start:end, 'noise_flag'] = 0 # filter it out when abrupt trend
        # # if too narrow a noise window, stretch it out for visibility.
        elif (width <= 2):
            df.loc[start:end, 'noise_flag'] = 1 # stretch it out

        # Conversely, if a spike-type noise, shave to be precise around peak
        ts_max = df.loc[start:end, value_col].abs().idxmax()

        # Define center as 40% - 60% of window.
        center_start = (start + 0.4 * width_padded).floor('D') 
        center_end   = (start + 0.6 * width_padded).floor('D')
        is_central = ts_max >= center_start and ts_max <= center_end

        # Identify spike-type noise by peak in center, then shave for precision
        if is_central or not abrupt_ends:
            df_left = df.loc[:ts_max].copy()
            df_left['diff'] = df_left[value_col].diff(periods=-1)
            lowers = df_left.loc[df_left['diff'] >= 0]
            if len(lowers) > 0: 
                noise_start = lowers.index[-1]
                df.loc[start:noise_start, 'noise_flag'] = 0

            df_right = df.loc[ts_max:].copy()
            df_right['diff'] = df_right[value_col].diff()
            highers = df_right.loc[df_right['diff'] >= 0]
            if len(highers) > 0:
                noise_end = highers.index[0]
                df.loc[noise_end:end, 'noise_flag'] = 0

    # 2. Create a temporary signal with no noise
    # Following flat & trend detection logic assumes no noise in the signals it depends on
    df['value_cleaned'] = df[value_col]
    df.loc[df['noise_flag'] == 1, 'value_cleaned'] = None
    df['value_cleaned'] = df['value_cleaned'].ffill().bfill()

    # 3. Flat detection using rolling std of savgol filter.
    # with leading and trailing to cater for periods centered windows doesnt cover
    df['smoothed'] = savgol_filter(df['value_cleaned'], window_length=WINDOW_SMOOTH, polyorder=1)
    df['smoothed_std'] = df['smoothed'].rolling(WINDOW_FLAT, center=True).std()
    df['smoothed_std_leading'] = df['smoothed'].iloc[::-1].rolling(window=WINDOW_FLAT).std().iloc[::-1]
    df['smoothed_std_trailing'] = df['smoothed'].rolling(WINDOW_FLAT).std()
    df['smoothed_std'] = df['smoothed_std'].fillna(df['smoothed_std_leading']).fillna(df['smoothed_std_trailing'])

    df['flat_flag'] = 0
    rolling_std = df['value_cleaned'].rolling(WINDOW_FLAT, center=True).std()
    min_nonzero_std = rolling_std[rolling_std > 0].min()
    df.loc[(df['smoothed_std'] <= min_nonzero_std) & (df['noise_flag'] == 0), 'flat_flag'] = 1 

    # 4. Detect up/down trend. Uses first derivates of savgol filter (like diff). 
    # Savgol filter (rolling avg improvement). Caters for seasonality with tightness to day.
    # Results in signal that's uptrend > 0, else down. As long as its not on a flat or noise.
    df['trend_flag'] = 0
    df.loc[df['flat_flag'] == 1, 'trend_flag'] = -2
    df.loc[df['noise_flag'] == 1, 'trend_flag'] = -3
    df['smoothed_deriv'] = savgol_filter(df['value_cleaned'], window_length=WINDOW_SMOOTH, polyorder=1, deriv=1)
    df.loc[(df['smoothed_deriv'] >= THRESHOLD_SMOOTH) & (df['flat_flag'] == 0) & (df['noise_flag'] == 0), 'trend_flag'] = 1
    df.loc[(df['smoothed_deriv'] < -THRESHOLD_SMOOTH) & (df['flat_flag'] == 0) & (df['noise_flag'] == 0), 'trend_flag'] = -1

    # import matplotlib.pyplot as plt

    # ax = df[[value_col, 'snr']].plot(figsize=(20,3), secondary_y='snr')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'noise_flag']].plot(figsize=(20,3), secondary_y='noise_flag')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'smoothed']].plot(figsize=(20,3), secondary_y='smoothed')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'smoothed_std']].plot(figsize=(20,3), secondary_y='smoothed_std')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'flat_flag']].plot(figsize=(20,3), secondary_y='flat_flag')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'smoothed_deriv']].plot(figsize=(20,3), secondary_y='smoothed_deriv')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    # ax = df[[value_col, 'trend_flag']].plot(figsize=(20,3), secondary_y='trend_flag')
    # ax.right_ax.axhline(y=0, color='gray', linestyle='--', linewidth=2)
    # plt.show()

    return df