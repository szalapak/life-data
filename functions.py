import pandas as pd #for tabulated data
import numpy as np #speedy operations on tables

import matplotlib.pyplot as plt #plots
import seaborn as sns #nicer plots
#some fancy plots stuff:
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
from matplotlib.patches import Patch 
import matplotlib.cm as cm

#dealing with dates and time
import datetime
import matplotlib.dates as dates

import re #regular expressions

#loading data from google sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import sys
#from df2gspread import df2gspread as d2g
import scipy.stats as stats


#####define categories and shortcuts used

categories_broad = ['sleep', 'High intensity work', 'Low intensity work', 
              'Human function', 'Procrastination', 'Culture',
             'Socialising', 'Other quality time', 'Travelling', 
              'Idle', 'High intensity exercise', 'Low intensity exercise']

shortcuts_broad_old = ['^S', r'^WI.*', r'^WL.*',
            r'^H.?', r'^P.*', r'^C-.*',
             r'^Ch.*', r'^Q.*', r'^T.*', 
             r'^I.*', r'^ExI.*', r'^ExL.*']

shortcuts_broad = ['.*S', 
                   r'.*WI.*', 
                   r'.*WL.*',
                   r'.*H.?', 
                   r'.*P.*', 
                   r'.*C[ -]+|^C$|.* C$',
                   r'.*Ch.*', 
                   r'.*Q.*', 
                   r'.*T.*', 
                   r'^I .*|^I$|.* I$|.* I .*', 
                   r'.*ExI.*', 
                   r'.*ExL.*']

categories_detail = ['sleep', 
                      'HI uni', 'HI self-improvement', 'HI organisation', 'HI admin', 'HI German',
                      'LI uni', 'LI self-improvement', 'LI organisation', 'LI admin', 'LI German',
                      'Human function', 
                      'Procrastination', 
                      'Culture - books', 'Culture - films', 'Culture - documentaries', 'Culture - TV', 
                     'Socialising', 
                      'Quality - blogs', 'Quality - podcasts', 'Quality - news', 'Quality - games', 'Quality - YT', 'Quality - chill',
                      'Travelling', 
                      'Idle', 
                      'High intensity exercise', 'Low intensity exercise']

shortcuts_detail_old = ['^S', 
                     r'WI-U.*', r'WI-I.*', r'WI-O.*', r'WI-A.*', r'WI-Ger.*',
                     r'WL-U.*', r'WL-I.*', r'WL-O.*', r'WL-A.*', r'WL-Ger.*',
                     r'^H.?', 
                     r'^P.*', 
                     r'C-B.*', r'C-F.*', r'C-D.*', r'C-TV.*',
                     r'^Ch.*', 
                     r'Q-Bl.*', r'Q-P.*', r'Q-N.*', r'Q-Wk.*', r'Q-G.*', r'Q-YT.*',  r'Q-ch.*',
                     r'^T.*', 
                     r'^I.*', 
                     r'^ExI.*', r'^ExL.*']

shortcuts_detail = [r'.*S.*', 
                     r'.*WI-u.*', r'.*WI-i.*', r'.*WI-o.*', r'.*WI-a.*', r'.*WI-ger.*',
                     r'.*WL-u.*', r'.*WL-i.*', r'.*WL-o.*', r'.*WL-a.*', r'.*WL-ger.*',
                     r'.*H.*', 
                     r'.*P.*', 
                     r'.*C-b.*', r'.*C-f.*', r'.*C-d.*', r'.*C-tv.*',
                     r'^Ch.*', 
                     r'.*Q-bl.*', r'.*Q-p.*', r'.*Q-n.*', r'Q-g.*', r'Q-yt.*',  r'Q-ch.*',
                     r'.*T.*', 
                     r'^I .*|^I$|.* I$|.* I .*', 
                     r'.*ExI.*', 
                     r'.*ExL.*']

grades = [0,
          4, 4, 1, 1, 4,
          2, 2, 1, 1, 2,
          0, 
          -4, 
          3, 2, 1, 0,
          0, 
          2, 2, 1, 0, 0, 0,
          0, 
          0, 
          4, 1]

def load_data():
    #loading data from google sheets
    scope = ['https://spreadsheets.google.com/feeds']

    # Give the path to the Service Account Credential json file 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('key/data-analysis-jupyter-5431f3097178.json',
                                                                   scope
                                                                  )
    # Authorise your Notebook
    gc = gspread.authorize(credentials)

    # The sprad sheet ID, which can be taken from the link to the sheet
    spreadsheet_key = '1nU4LKQSrn194_J79vpps0wbS6N-pS_TWl7J20hyn9Sg'
    
    
    book = gc.open_by_key(spreadsheet_key)
    worksheet = book.worksheet("data")
    table = worksheet.get_all_values()
    data = pd.DataFrame(table[1:], columns=table[0])
    
    data['date'] = pd.to_datetime(data['date'], format = '%d/%m/%y')
    data['date'] = data['date'].dt.date

    data['day'] = pd.DatetimeIndex(data['date']).day
    data['month'] = pd.DatetimeIndex(data['date']).month
    data['weekday'] = pd.DatetimeIndex(data['date']).weekday

    for name in ['morning', 'afternoon', 'evening']:
        data[name] = pd.to_numeric(data[name])

    data = data.set_index(data['date'])
    
    #fix mood, add column with an average
    data['av_mood'] = data[['morning', 'afternoon', 'evening']].mean(axis = 1)

    data.av_mood.iloc[:17] = [6.0, 3.0, 3.0, 6.0, 5.0, 4.0, 5.0, 
                        3.0, 5.0, 6.0, 6.0, 4.0, 5.0, 5.0, 
                        5.0, 5.0, 4.0]
    
    return(data)

def make_activities_df(data):
    cols = list(data.columns)

    start = cols.index("0:00")
    end = cols.index("23:45")

    act_ind = cols[start:end+1]

    activities = data[act_ind]

    activities = activities.set_index(data['date'])
    activities.columns = pd.to_datetime(activities.columns, format = '%H:%M').time

    return(activities)

def make_summary(data, activities, categories, shortcuts):
    summary = pd.DataFrame(index = data['date'], columns = categories)

    for cat, short in zip(categories, shortcuts):
        summary[cat] =  activities.apply(lambda row : row.str.count(short).sum()*0.25, axis = 1)
    
    return(summary)

def grading(data, activities, summary_detail, grades = grades):
    #multiply the detailed summary by grade for each category to get dataframe of grades
    ocenki = summary_detail.multiply(grades)

    #sleep separate as is complicated
    for i in range(len(data['date'])):
        not_in_bed = activities.iloc[i,4:20].str.count(r'^((?!S).)*$').sum()*-1*0.25 #-1 for not sleeping after 1 am
        #penatly doesn't work if time is spent with friends or on traveling
        frens = activities.iloc[i,4:20].str.count(r'^Ch.*').sum()*1*0.25 
        travel = activities.iloc[i,4:20].str.count(r'^T.*').sum()*1*0.25

        still_in_bed = activities.iloc[i,33:-5].str.count('^S').sum()*-2*0.25 #-2 per hour for not being awake after 8:30

        ocenki['sleep'].iloc[i] = not_in_bed + frens + travel + still_in_bed
        
        return(ocenki)
    
def plot_grades(ocenki, nd = 7, incl_today = False):
    if incl_today == False:
        nd += 1
        ocenki_week = ocenki.iloc[-nd:-1]
        
    else:
        ocenki_week = ocenki.iloc[-nd:]

    nonzero_ocenki = ocenki_week.loc[:, (ocenki != 0).any(axis=0)]

    fig = plt.figure(figsize = (14,nd))
    ax1 = fig.add_subplot(111)

    im = sns.heatmap(nonzero_ocenki, ax = ax1,
                    annot = True, 
                    cmap = 'PiYG', center = 0,
                    linewidth = 0.05, 
                    vmin=ocenki.min().min(), vmax=ocenki.max().max(), 
                    cbar_kws = dict(use_gridspec=False,location="right", 
                                    shrink = 0.8, anchor = (0.0, 0.7)))
    

    ax = plt.gca()
    plt.gca().xaxis.tick_top()
    plt.xticks(rotation=90)
    ax.tick_params(length = 0)

    plt.yticks(np.arange(nd)+0.5, rotation=0, va="center")

    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)
    

    plt.show()
    
    




