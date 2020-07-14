import pandas as pd
import numpy as np
import datetime
from math import pi

from bokeh.plotting import figure,show
from bokeh.models import Column,ColumnDataSource,Row
from bokeh.palettes import Category20
from bokeh.transform import cumsum

def nearest(date,timeSeries,findSeries):
    """
    This function will return the datetime in items which is the closest to the date pivot.
    """
    nearDate= min(timeSeries, key=lambda x: abs(x - date))
    index=list(timeSeries).index(nearDate)
    
    return list(findSeries)[index]

df=pd.read_csv(r'C:\Users\joris\.spyder-py3\good code\scraping\scraping.csv',parse_dates=[0])
df['time_interval']=[np.nan]+[(df['date'][i]-df['date'][i-1]).days for i in range(1,len(df))]

#############CANADA GOOSE######################################################
df['CanadaGoose_newFollowers_Weibo']=[np.nan]+[df['CanadaGoose_followers_Weibo'][i]-df['CanadaGoose_followers_Weibo'][i-1] for i in range(1,len(df))]
df['CanadaGoose_newFollowers_Instagram']=[np.nan]+[df['CanadaGoose_followers_Instagram'][i]-df['CanadaGoose_followers_Instagram'][i-1] for i in range(1,len(df))]
df['CanadaGoose_newFollowers_Pinterest']=[np.nan]+[df['CanadaGoose_followers_Pinterest'][i]-df['CanadaGoose_followers_Pinterest'][i-1] for i in range(1,len(df))]

df['CanadaGoose_newFollowersADay_Weibo']=df['CanadaGoose_newFollowers_Weibo']/df['time_interval']
df['CanadaGoose_newFollowersADay_Instagram']=df['CanadaGoose_newFollowers_Instagram']/df['time_interval']
df['CanadaGoose_newFollowersADay_Pinterest']=df['CanadaGoose_newFollowers_Pinterest']/df['time_interval']
df['CanadaGoose_newFollowersADay_Instagram'][df['CanadaGoose_newFollowersADay_Instagram'].first_valid_index()]=np.nan#replace the first measurement with nan
df['CanadaGoose_newFollowersADay_Pinterest'][df['CanadaGoose_newFollowersADay_Pinterest'].first_valid_index()]=np.nan#replace the first measurement with nan

gooseDF=pd.DataFrame()
gooseDF['date'] = [df['date'][0] + datetime.timedelta(days=x) for x in range(int((list(df['date'])[-1]-df['date'][0]).days))]
gooseDF['Weibo']=gooseDF['date'].apply(nearest,timeSeries=df['date'],findSeries=df['CanadaGoose_newFollowersADay_Weibo'])
gooseDF['Instagram']=gooseDF['date'].apply(nearest,timeSeries=df['date'],findSeries=df['CanadaGoose_newFollowersADay_Instagram'])
gooseDF['Pinterest']=gooseDF['date'].apply(nearest,timeSeries=df['date'],findSeries=df['CanadaGoose_newFollowersADay_Pinterest'])

gooseSource=ColumnDataSource(gooseDF)

canadaGoosePlot=figure(title='Cananda Goose',width=800,height=400,x_axis_type='datetime')
canadaGoosePlot.vbar(x='date',top='Weibo',width=datetime.timedelta(1),color='red',legend_label='New Weibo followers',source=gooseSource,alpha=0.5)
canadaGoosePlot.vbar(x='date',top='Instagram',width=datetime.timedelta(1),color='blue',legend_label='New Instagram followers',source=gooseSource,alpha=0.5)
canadaGoosePlot.vbar(x='date',top='Pinterest',width=datetime.timedelta(1),color='green',legend_label='New Pinterest followers',source=gooseSource,alpha=0.5)

#############SMARTPHOTO##############INSTAGRAM##########################
keyListInstagram=[]
nameListInstagram=[]
pieDictInstagram={}
for i in df.columns.values:
    if i.startswith('SmartPhoto') and 'Instagram' in i:
        keyListInstagram.append(i)
        name=i[i.rfind('_')+1:]
        nameListInstagram.append(name)
        pieDictInstagram[name]=list(df[i])[-1]
        if np.isnan(pieDictInstagram[name]):#replace with previous number in case of NaN
            pieDictInstagram[name]=list(df[i])[-2]
            
        #print(i[i.rfind('_')+1:],list(df[i])[-1])    

data = pd.Series(pieDictInstagram).reset_index(name='value').rename(columns={'index':'country'})
data['angle'] = data['value']/data['value'].sum() * 2*pi
data['color'] = Category20[len(pieDictInstagram)]

pieInstagram = figure(plot_height=350, title="Smartphoto Instagram followers", toolbar_location=None,
           tools="hover", tooltips="@country: @value", x_range=(-0.5, 1.0))

pieInstagram.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field='country', source=data)

pieInstagram.axis.axis_label=None
pieInstagram.axis.visible=False
pieInstagram.grid.grid_line_color = None

def newFollowers(df,keyList=['SmartPhoto_followers_Instagram_Belgium'],nameList=['Belgium']):
    smartDF=pd.DataFrame()
    smartDF['date'] = [df['date'][0] + datetime.timedelta(days=x) for x in range(int((list(df['date'])[-1]-df['date'][0]).days))]
    for key,name in zip(keyList,nameList):
        df[key+'new']=[np.nan]+[df[key][i]-df[key][i-1] for i in range(1,len(df))]
        df[key+'newDaily']=df[key+'new']/df['time_interval']
        df[key+'newDaily'][df[key+'newDaily'].first_valid_index()]=np.nan#replace the first measurement with nan

        smartDF[name]=smartDF['date'].apply(nearest,timeSeries=df['date'],findSeries=df[key+'newDaily'])

    smartDF['all']=smartDF.sum(axis=1)

    return smartDF

smartDF=newFollowers(df,keyList=keyListInstagram,nameList=nameListInstagram)
smartSource=ColumnDataSource(smartDF)
smartphotoPlotInstagram=figure(title='Smartphoto Instagram: new followers',width=800,height=400,x_axis_type='datetime',x_range=(list(smartDF['date'])[smartDF[nameListInstagram[0]].first_valid_index()],list(smartDF['date'])[-1]))

smartphotoPlotInstagram.vbar(x='date',top='all',width=datetime.timedelta(1),color='black',legend_label='total',source=smartSource,alpha=0.5)
for name,color in zip(nameListInstagram,Category20[len(nameListInstagram)]):
    smartphotoPlotInstagram.line(x='date',y=name,color=color,legend_label=name,source=smartSource,line_width=2)

#plot the total Instagram followers
for index, row in df.iterrows():
    df['smartphotoTotalInstagramFollowers']=0
    for name in nameListInstagram:
        df['smartphotoTotalInstagramFollowers']=df['smartphotoTotalInstagramFollowers']+df['SmartPhoto_followers_Instagram_'+name]
smartphotoTotalInstagramPlot=figure(title='Smartphoto Instagram: total followers',width=800,height=400,x_axis_type='datetime')
smartphotoTotalInstagramPlot.line(df['date'],df['smartphotoTotalInstagramFollowers'])

smartphotoInstagramRow=Row(pieInstagram,smartphotoPlotInstagram,smartphotoTotalInstagramPlot)

#############SMARTPHOTO##############PINTEREST##########################
df=pd.read_csv(r'E:\financieel\beleggingen\scraping.csv',parse_dates=[0])
print(df.columns)
print(len(df))
df['time_interval']=[np.nan]+[(df['date'][i]-df['date'][i-1]).days for i in range(1,len(df))]

keyListPinterest=[]
nameListPinterest=[]
pieDictPinterest={}
for i in df.columns.values:
    if i.startswith('SmartPhoto') and 'Pinterest' in i:
        keyListPinterest.append(i)
        name=i[i.rfind('_')+1:]
        nameListPinterest.append(name)
        pieDictPinterest[name]=list(df[i])[-1]
        #print(i[i.rfind('_')+1:],list(df[i])[-1])    
print(pieDictPinterest)

data = pd.Series(pieDictPinterest).reset_index(name='value').rename(columns={'index':'country'})
data['angle'] = data['value']/data['value'].sum() * 2*pi
data['color'] = Category20[len(nameListPinterest)]

piePinterest=figure(plot_height=350, title="Smartphoto Pinterest followers", toolbar_location=None,
           tools="hover", tooltips="@country: @value", x_range=(-0.5, 1.0))

piePinterest.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field='country', source=data)

piePinterest.axis.axis_label=None
piePinterest.axis.visible=False
piePinterest.grid.grid_line_color = None


smartDF=newFollowers(df,keyList=keyListPinterest,nameList=nameListPinterest)
smartSource=ColumnDataSource(smartDF)
print(list(smartDF['date'])[smartDF[nameListPinterest[0]].first_valid_index()])
print(list(smartDF['date'])[-1])
smartphotoPlotPinterest=figure(title='Smartphoto Pinterest: new followers',width=800,height=400,x_axis_type='datetime',x_range=(list(smartDF['date'])[smartDF[nameListPinterest[0]].first_valid_index()],list(smartDF['date'])[-1]))

smartphotoPlotPinterest.vbar(x='date',top='all',width=datetime.timedelta(1),color='black',legend_label='total',source=smartSource,alpha=0.5)
for name,color in zip(nameListPinterest,Category20[len(nameListPinterest)]):
    smartphotoPlotPinterest.line(x='date',y=name,color=color,legend_label=name,source=smartSource,line_width=2)

#plot the total Instagram followers
for index, row in df.iterrows():
    df['smartphotoTotalPinterestFollowers']=0
    for name in nameListPinterest:
        df['smartphotoTotalPinterestFollowers']=df['smartphotoTotalPinterestFollowers']+df['SmartPhoto_followers_Pinterest_'+name]
smartphotoTotalPinterestPlot=figure(title='Smartphoto Pinterest: total followers',width=800,height=400,x_axis_type='datetime')
smartphotoTotalPinterestPlot.line(df['date'],df['smartphotoTotalPinterestFollowers'])

smartphotoPinterestRow=Row(piePinterest,smartphotoPlotPinterest,smartphotoTotalPinterestPlot)

######################SUMMARY#################################################
layout=Column(canadaGoosePlot,smartphotoInstagramRow,smartphotoPinterestRow)
show(layout)
