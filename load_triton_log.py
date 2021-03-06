# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 14:32:40 2019

@author: otten
"""
#TODO stitch logs (For reader)
import ctypes
import numpy as np
import re
import pandas as pd
import logging
from datetime import datetime
from pytz import timezone

logger = logging.getLogger('tritonMonitor.load_triton_log')
logger.setLevel(logging.DEBUG)

LOCAL_TIMEZONE_DIFF = datetime.now()-datetime.utcnow()

def parse_cstr(cstr: bytes) -> str:
    return ctypes.create_string_buffer(cstr).value.decode()


def split_at_idx(buf, idx):
    return buf[:idx], buf[idx:]

def parse_triton_log(bin_data) -> pd.DataFrame:
    header_size = 1024
    comments_size = 5120
    name_block_size = 5120
    name_len = 32
    unknown_block_size = 1024
    
    header = parse_cstr(bin_data[:header_size])
    rest = bin_data[header_size:]
    
    comments = parse_cstr(rest[:comments_size])
    rest = rest[comments_size:]
    
    name_block = rest[:name_block_size]
    rest = rest[name_block_size:]


    names = []
    for idx in range(0, name_block_size, name_len):
        name = parse_cstr(name_block[idx:idx+name_len])
        if name:
            names.append(name)
        else:
            break

    unknown_block, rest = split_at_idx(rest, unknown_block_size)

    data = np.frombuffer(rest, dtype=float)
    data = data.reshape((-1, len(names)))
    df = pd.DataFrame(columns=names, data=data)
    return df

def cat_columns(columns):
    drop_columns=[]
    time_columns=[]
    # temperature_sensors=[]
    for column in columns:
        # print(column)
        if re.match('^chan\[\d+\]',column):
            # print('Match: Empty channel')
            drop_columns.append(column)
            
        elif re.match('.+t\(s\)$',column):
            # print('Match: Temperature Sensor time channel')
            # group_name = re.split(' t\(s\)',column)[0]
            # temperature_sensors.append(group_name)
            time_columns.append(column)
    return drop_columns, time_columns
                    
def cleanup_log(df, drop_columns, time_columns):
    dt = pd.to_datetime(df['Time(secs)'], unit='s')+LOCAL_TIMEZONE_DIFF
    df.insert(0, 'Time', dt)
    
    for column in time_columns:
        df[column] = pd.to_datetime(df[column], unit='s')+LOCAL_TIMEZONE_DIFF
        val_columns = [re.split('t\(s\)$',column)[0] + 'T(K)', re.split('t\(s\)$',column)[0] + 'R(Ohm)']
        df.loc[df[column]<='1971-01-01 00:00:00',val_columns]=None
        df.loc[df[column]<='1971-01-01 00:00:00',column]=df.loc[0,'Time']
        
    df = df.drop(columns=drop_columns)
    df = df.drop(columns=['LineSize(bytes)', 'LineNumber', 'Time(secs)'])
    return df

        
class TritonLogReader:
    def __init__(self, fullpath):
        self.logger = logging.getLogger('tritonMonitor.load_triton_log.TritonLogReader')
        self.logger.setLevel(logging.DEBUG)
        self.fullpath = fullpath
        self.logger.debug(f'Opening Log File {self.fullpath}')
        self.LOCAL_TIMEZONE_DIFF = LOCAL_TIMEZONE_DIFF
        with open(self.fullpath, 'rb') as file:           
            self.df = parse_triton_log(file.read())
            self.current_fpos = file.tell()
            self.last_refresh = datetime.now() 
        self.names = self.df.columns     
        self.drop_columns, self.time_columns = cat_columns(self.df.columns)

        self.logger.debug('Cleaning up Log file')
        self.df = cleanup_log(self.df, self.drop_columns, self.time_columns)
    
 
    
    def refresh(self):
        self.logger.debug(f'Refresh: Opening Log File {self.fullpath}')
        with open(self.fullpath, 'rb') as file:   
            file.seek(self.current_fpos)             
            bin_data = file.read()
            self.current_fpos = file.tell()
            self.last_refresh = datetime.now() 
        data = np.frombuffer(bin_data, dtype=float)
        data = data.reshape((-1, len(self.names)))
        
        #TODO if no ew lines skip append
        self.logger.debug(f'Found {data.shape[0]} new lines')
        if len(data):
            self.logger.debug(f'Creating Dataframe')
            updated_df = pd.DataFrame(columns=self.names, data=data)
            self.logger.debug('Refresh: Cleaning up Log file')
            updated_df = cleanup_log(updated_df, self.drop_columns, self.time_columns)
            self.df = self.df.append(updated_df)          
            return updated_df.shape[0]
        else:
            return 0

            
