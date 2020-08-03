import pandas_datareader as pdr
import pandas as pd
import random

from bokeh.plotting import figure
from bokeh.io import show,reset_output,output_file
from bokeh.models import Column,Row,ColumnDataSource,LinearAxis, Range1d, Band,Div
from bokeh.palettes import Spectral11
from bokeh.models import HoverTool

import urllib.request as urlRQ
from bs4 import BeautifulSoup as bs
from datetime import datetime

###############################################################################
#####################HELP FUNCTIONS############################################
###############################################################################

#a function that scrapes the dividend history from yahoo
def get_dividend(name,start):
    dividendList = []
    dividendDateList = []
    
    #calculate the time differences in seconds between 1-Jan-2010 and today
    #startTimeSeconds=1262300400 #1 Jan 2010 
    refDate=datetime.strptime(start, '%m/%d/%Y')
    startTimeSeconds=(refDate-datetime(1970,1,1)).total_seconds()
    endTimeSeconds=(datetime.today()-datetime(1970,1,1)).total_seconds()

    url="https://finance.yahoo.com/quote/"+name+"/history?period1="+str(int(startTimeSeconds))+"&period2="+str(int(endTimeSeconds))+"&interval=div%7Csplit&filter=div&frequency=1d"
    rows = bs(urlRQ.urlopen(url).read(),'lxml').findAll('table')[0].tbody.findAll('tr')

    for each_row in rows:
        divs = each_row.findAll('td')
        if divs[1].span.text  == 'Dividend': #use only the row from the table with dividend info
            dividendDateList.append(divs[0].span.text)
            dividendList.append(float(divs[1].strong.text.replace(',','')))
            
    dividendDateList=[datetime.strptime(i, '%b %d, %Y') for i in dividendDateList]#convert string list to datetime list

    return {'date':dividendDateList,'dividend':dividendList}


def createBoxPlot(Filter,yAxisFilter,source,title='Boxplot',width=1400):
    df=pd.DataFrame(source.data)
    # generate the category list
    catsColumn=list(source.data[Filter])
    cats =sorted(set(catsColumn))
    
    #get the x-axis for the dots and create jitter effect
    x_axis_value=[0.5]#bokeh plots categories on x-axis like this: 0.5,1.5,2.5,..
    for x in range (1,len(cats)):
        x_axis_value.append(x_axis_value[-1]+1)#make a list of the different category x-axis values
    x_axis=[]
    for x in catsColumn:
        index=cats.index(x)
        x_axis.append(x_axis_value[index]+random.uniform(-0.3,0.3))#make a jitter around the x-axis value of the catergory for each datapoint
    source.add(x_axis,'categorical_x_axis_value')#add a column to the datasource with the Jitter values 
    
    # find the quartiles and IQR for each category
    groups = df.groupby(Filter)
    q1 = groups.quantile(q=0.25)
    q2 = groups.quantile(q=0.5)
    q3 = groups.quantile(q=0.75)
    iqr = q3 - q1
    upper = q3 + 1.5*iqr
    lower = q1 - 1.5*iqr
    
    TOOLS="pan,wheel_zoom,lasso_select,reset,save"
    p = figure(tools=TOOLS, title=title, x_range=cats,width=width)
    
    # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
    qmin = groups.quantile(q=0.00)
    qmax = groups.quantile(q=1.00)
    upperStem = [min([x,y]) for (x,y) in zip(list(qmax.loc[:,yAxisFilter]),upper[yAxisFilter])]
    lowerStem = [max([x,y]) for (x,y) in zip(list(qmin.loc[:,yAxisFilter]),lower[yAxisFilter])]
    
    # stems
    p.segment(cats, upperStem, cats, q3[yAxisFilter], line_color="black")
    p.segment(cats, lowerStem, cats, q1[yAxisFilter], line_color="black")
    
    #create the boxes boxes
    def createColorList(number=11):#create a color list for each category
        colorList=[]   
        for x in range(0,number):
            colorList.append(Spectral11[x%11])
            
        return colorList
    colorList=createColorList(number=len(cats))
    
    p.vbar(x=cats, width=0.7, bottom=q2[yAxisFilter], top=q3[yAxisFilter], line_color="black",color=colorList)
    p.vbar(cats, 0.7, q1[yAxisFilter], q2[yAxisFilter], line_color="black",color=colorList)
    
    #add data points
    #p.circle(source=source,x=Filter, y=yAxisFilter,size=5,color='black',alpha=0.3)
    p.circle(source=source,x='categorical_x_axis_value', y=yAxisFilter,size=5,line_color='black',fill_alpha=0)#with Jitter and via source
    
    # whiskers (almost-0 height rects simpler than segments)
    whiskerHeight=(max(qmax[yAxisFilter])-min(qmin[yAxisFilter]))/1000
    p.rect(x=cats, y=lowerStem, width=0.2, height=whiskerHeight, line_color="black",fill_color="black")
    p.rect(x=cats, y=upperStem, width=0.2, height=whiskerHeight, line_color="black",fill_color="black")
    
    return p

#get the index of the next value in a list equal to the value at startIndex
def findNextIndexOf(startIndex,timeList):
    while True:
        for time in timeList[startIndex+1:]:
            if timeList[startIndex]==time:
                index=timeList[startIndex+1:].index(time)
                #print(str(timeList[startIndex])+' is found at index '+str(index+startIndex+1))
                return index+startIndex+1
                break
        break
    return False

#find the previous index in timeList with value equal to the startIndex. StartIndex needs to be larger than 0 
def findPreviousIndexOf(startIndex,timeList):
    if startIndex<len(timeList):
        for i in range(startIndex-1,-1,-1):
            if timeList[i]==timeList[startIndex]:
                break
            else:
                i=False
    else:
        i=False
    return(i)

#calculate the relative difference compared to the week average for a chonological list of values and a list of weeksdays with monday=0,tuesday=1,...
def getTimeVariability(timeList,values,intervalSize):
    averageList=[1]*(intervalSize-1)#skip the first
    
    for i in range(intervalSize,len(values)-intervalSize+2):
        beforeStartIndex=findPreviousIndexOf(i,timeList)
        afterEndIndex=findNextIndexOf(i,timeList)
        
        intervalListBefore=values[beforeStartIndex:i-1]
        intervalListAfter=values[i:afterEndIndex-1]
        
        intervalListBefore=values[i-intervalSize:i-1]
        
        avg=(sum(intervalListBefore)+sum(intervalListAfter))/(len(intervalListAfter)+len(intervalListBefore))
        #print('the value at index '+str(i-1)+' is '+str(values[i-1]))
        averageList.append(values[i-1]/avg)
        
    for i in range(len(values)-intervalSize+1,len(values)):#skipt the last
        averageList.append(1)
        
    return averageList

values=[3,4,5,6,7,8,9,10,9,8]
timeList=[3,4,0,1,2,3,4,0,1,2]
intervalSize=5
#print(getTimeVariability(timeList,values,intervalSize))

#calculate the relative difference compared to the week average for a chonological list of values and a list of weeksdays with monday=0,tuesday=1,...
def getAverage(valuesList,sizeNumber):
    averageList=[valuesList[0]] 
    for i in range(1,len(valuesList)):
        sizeList=valuesList[max(0,i-sizeNumber):min(len(valuesList),i)]
        averageList.append(sum(sizeList)/max(len(sizeList),1))
        
    return averageList

#apply a certain buy/sell strategy on historical data
# meDirect transactie tarieven per beurs https://www.medirect.be/nl-be/tarieven-en-kosten/transactietarieven 
def stategy(timeList,valueDayList,longDaysAverage=200,mediumDaysAverage=50,shortDaysAverage=20,trafficTax=0.0035,tafficCost=0.001):
    profitPercent=100
    buyValue=1

    short=getAverage(valueDayList,shortDaysAverage)
    medium=getAverage(valueDayList,mediumDaysAverage)
    long=getAverage(valueDayList,longDaysAverage)

    transactionTimeList=[timeList[0]]
    valueList=[valueDayList[0]]
    eventList=['blue']
    
    for x in range(1,len(long)):
        if long[x]<medium[x] and long[x-1]>medium[x-1] and eventList[-1]!='green':#BUY
            buyValue=round(valueDayList[x],2)
            eventList.append('green')
            valueList.append(valueDayList[x])
            transactionTimeList.append(timeList[x])
        if short[x]<long[x] and short[x-1]>long[x-1] and eventList[-1]=='green':#SELL
            profitPercent=profitPercent*valueDayList[x]/buyValue*(1-trafficTax)*(1-tafficCost)
            eventList.append('red')
            valueList.append(valueDayList[x])
            transactionTimeList.append(timeList[x])
            
    strategyDF=pd.DataFrame({'time':transactionTimeList,'event':eventList,'value':valueList})
       
    return profitPercent,strategyDF
###############################################################################
#####################BODY OF THE CODE############################################
###############################################################################

def createView(symbol,start=None,getStrategyYield=False,longDaysAverage=200,mediumDaysAverage=50,shortDaysAverage=20):
    
    data=pdr.get_data_yahoo(symbol,start=start)
    hover = HoverTool(names=['dividend'],tooltips=[("dividend", "$y")])
    tools=['pan','box_zoom','wheel_zoom',hover,'reset']
    
    stock_value=figure(height=400,width=1200,x_axis_type='datetime',title = symbol+" value (source=Yahoo finance)",tools=tools)

    #plot the value vs time
    timeList=data.index.values#get the x-axis values: datetime
    #stock_value.circle(timeList,data['Close'],color='blue')
    stock_value.line(timeList,data['Close'],color='black')

    #plot the dividend events
    dividendDict=get_dividend(symbol,start)#scrape the dividend data from the yahoo website
    if dividendDict['dividend']!=[]:
        dividendSource = ColumnDataSource(data=dividendDict)
        stock_value.extra_y_ranges = {"2dyrange": Range1d(start=0, end=max(dividendDict['dividend'])*1.05)}# Setting the second y axis range name and range
        stock_value.add_layout(LinearAxis(y_range_name="2dyrange"), 'right')# Adding the second axis to the plot.
        stock_value.circle(x='date',y='dividend',fill_color="white",color='black',size=8,alpha=0.5,y_range_name="2dyrange",name='dividend',source=dividendSource)
    else:
        print(symbol+' has given no dividend since 2010!')

    #add SimpleMeanAverage and KEEP/SELL signals
    ### SMA50 overtakes SMA200 (golden cross) --> more gains ahead: KEEP
    ### SMA200 overtakes SMA20 (death cross) --> more losses ahead: SELL
    if getStrategyYield==True:
        SMA20=getAverage(data['Open'],shortDaysAverage)
        SMA50=getAverage(data['Open'],mediumDaysAverage)
        SMA200=getAverage(data['Open'],longDaysAverage)
        
        stock_value.line(timeList,SMA20,color='red',legend_label=str(shortDaysAverage)+" days average")#20 days average
        stock_value.line(timeList,SMA50,color='green',legend_label=str(mediumDaysAverage)+" days average")#50 days average
        stock_value.line(timeList,SMA200,color='blue',legend_label=str(longDaysAverage)+" days average")#200 days average
        
# =============================================================================
#         deathSource = ColumnDataSource({'base':timeList,'SMA20':SMA20,'SMA200':[j if j>i else i for i,j in zip(SMA20,SMA200)]})
#         deathBand = Band(base='base', lower='SMA20', upper='SMA200',level='underlay', fill_alpha=0.5, line_width=1, fill_color='red',source=deathSource)
#         stock_value.add_layout(deathBand)
#         goldSource = ColumnDataSource({'base':timeList,'SMA50':SMA50,'SMA200':[j if i>j else i for i,j in zip(SMA50,SMA200)]})
#         goldBand = Band(base='base', lower='SMA200', upper='SMA50',level='underlay', fill_alpha=0.5, line_width=1, fill_color='green',source=goldSource)
#         stock_value.add_layout(goldBand)    
# =============================================================================
        
        stock_value.legend.location = "bottom_left"
        stock_value.legend.click_policy="hide"

        #add BUY and SELL strategy
        divtext=""
# =============================================================================
#         for x in range(1,len(SMA200)):
#             if SMA200[x]<SMA50[x] and SMA200[x-1]>SMA50[x-1]:
#                 divtext+=str(timeList[x])[:10]+" KEEP OR BUY EXTRA: more gains ahead! "+" value: "+str(round(data['Close'][x],2))+"<br>"
#             if SMA20[x]<SMA200[x] and SMA20[x-1]>SMA200[x-1]:
#                 divtext+=str(timeList[x])[:10]+" SELL: more losses ahead! "+" value: "+str(round(data['Close'][x],2))+"<br>"
# =============================================================================
    
        profitPercent,strategyDF=stategy(timeList,data['Close'],longDaysAverage=longDaysAverage,mediumDaysAverage=mediumDaysAverage,shortDaysAverage=shortDaysAverage,trafficTax=0.0035,tafficCost=0.001)
        divtext+="over this period, this profit strategy would have given a yield of "+str(int(profitPercent-100))+"% for "+symbol
        div=Div(text=divtext,width=1200, height=300)
        
        #add a colored dot to illustrate a buy or sell event
        strategySource = ColumnDataSource(data=strategyDF)
        stock_value.circle(x='time',y='value',color='event',size=10,alpha=1,name='strategy',source=strategySource)
        

# =============================================================================
#         colorSource = ColumnDataSource({'base':timeList,'SMA20':SMA20,'SMA200':[j if j>i else i for i,j in zip(SMA20,SMA200)]})
#         colorBand = Band(base='base', lower='SMA20', upper='SMA200',level='underlay', fill_alpha=0.5, line_width=1, fill_color='red',source=colorSource)
#         stock_value.add_layout(colorBand)
# =============================================================================
        
# =============================================================================
#         for x in range(50,350,25):
#             for y in range(30,100,10):
#                 for z in range(5,50,5):
#                     profitPercent=stategy(data['Close'],longDaysAverage=x,mediumDaysAverage=y,shortDaysAverage=z,trafficTax=0.0035,tafficCost=0.001)
#                     print("over this period, the "+str(x)+"-"+str(y)+"-"+str(z)+" strategy would have given a yield of "+str(int(profitPercent-100))+"% for "+symbol)
#                     with open('profitStrategy.csv','a') as file:
#                         file.write(str(x)+","+str(y)+","+str(z)+","+symbol+","+str(int(profitPercent-100))+"%\n")
# =============================================================================
    else:
        profitPercent=None
        div=Div(text="",width=1200, height=1)
    
    
    #plot the trading volume versus time
    stock_volume=figure(height=300,width=1200,x_axis_type='datetime',x_range=stock_value.x_range,title = symbol+" trading volume (source=Yahoo finance)",tools=tools)
    stock_volume.vbar(x=timeList, top=data['Volume'], bottom=0, width=50000000, fill_color="#b3de69")
    
    #calcute fluctuation depending on day of the week                 
    dates = pd.DatetimeIndex(timeList) #convert to datetime format
    weekdays = dates.weekday.values[:-365]#get the weekdays (0=monday, 1=tuesday,...)
    values=list(data['Open'])[:-365]#get the values in a list
    relToWeekAvg=getTimeVariability(timeList=list(weekdays),values=values,intervalSize=5)
    weekdaysStrings=[]
    for i in weekdays:
        if i==0:
            weekdaysStrings.append('1_Monday')
        elif i==1:
            weekdaysStrings.append('2_Tuesday')
        elif i==2:
            weekdaysStrings.append('3_Wednesday')
        elif i==3:
            weekdaysStrings.append('4_Thursday')
        elif i==4:
            weekdaysStrings.append('5_Friday')
        elif i==5:
            weekdaysStrings.append('6_Saturday')
        elif i==6:
            weekdaysStrings.append('7_Sunday')     
    sourceDays=ColumnDataSource({'ratio to week average':relToWeekAvg,'day of the week':weekdaysStrings})
    weekdayBoxPlot=createBoxPlot(Filter='day of the week',yAxisFilter='ratio to week average',source=sourceDays,title='Variability depending on the day of the week',width=500)
    
    #calcute fluctuation depending on month of the year                 
    months = dates.month.values#get the weekdays (0=monday, 1=tuesday,...)
    values=list(data['Open'])#get the values in a list
    relToYearAvg=getTimeVariability(timeList=list(months),values=values,intervalSize=12)
    monthStrings=[]
    for i in months:
        if i==1:
            monthStrings.append('01_Jan')
        elif i==2:
            monthStrings.append('02_Feb')
        elif i==3:
            monthStrings.append('03_Mar')
        elif i==4:
            monthStrings.append('04_Apr')
        elif i==5:
            monthStrings.append('05_May')
        elif i==6:
            monthStrings.append('06_Jun')
        elif i==7:
            monthStrings.append('07_Jul')
        elif i==8:
            monthStrings.append('08_Aug')
        elif i==9:
            monthStrings.append('09_Sep')
        elif i==10:
            monthStrings.append('10_Oct')
        elif i==11:
            monthStrings.append('11_Nov')
        elif i==12:
            monthStrings.append('12_Dec')
    
    sourceMonth=ColumnDataSource({'ratio to year average':relToYearAvg,'month':monthStrings})
    monthBoxPlot=createBoxPlot(Filter='month',yAxisFilter='ratio to year average',source=sourceMonth,title='Variability depending on the month of the year',width=1200)
    
    #calcute fluctuation depending on day of the month                 
    days = dates.day.values#get the weekdays (0=monday, 1=tuesday,...)
    values=list(data['Open'])#get the values in a list
    relToMonthAvg=getTimeVariability(timeList=list(days),values=values,intervalSize=27)#getWeekAverage(days,values,start=1)
    daysStrings=[str(i) if i>9 else '0'+str(i) for i in days]
    
    sourceMonth=ColumnDataSource({'ratio to month average':relToMonthAvg,'day':daysStrings})
    dayBoxPlot=createBoxPlot(Filter='day',yAxisFilter='ratio to month average',source=sourceMonth,title='Variability depending on the day of the month',width=1200)
    
    layout=Row(Column(stock_value,stock_volume,div,monthBoxPlot,dayBoxPlot),weekdayBoxPlot)
    
    reset_output()
    output_file(symbol+".html")
    return layout,profitPercent
    
###############################################################################
###################DATABASE####################################################
###############################################################################

stocksList=['PG','VEUR.AS','C40.PA','APAM.AS','PROX.BR','SOLB.BR','ABI.BR','MELE.BR','MSFT','COFB.BR','ELI.BR','SEV.PA','BAS.F','AAPL','FP.PA',
            'ACKB.BR','BEKB.BR','BPOST.BR','COLR.BR','GLPG.AS','ONTEX.BR','SOF.BR','TNET.BR','UCB.BR','UMI.BR','NYR.BR','ENGI.PA','VALE','NOVN.SW',
            'LYB','WEB.BR','EVS.BR','ATEB.BR','TESB.BR','INGA.AS','AD.AS','ABN.AS','REP.MC','CE','EMN','STERV.HE','GSH','WB','BABA','ADL.DE',
            'GAZ.DE','WTI','TFG.AS','RDSA.AS','MT.AS','AMG.AS','SLIGR.AS','RIO.L','VGP.BR','AMUN.PA','FL','POLY.L','CAM.L','TECK','CAM.L','TECK','KAZ.L',
            'VEDL','BOL.ST','S32.L','BNB.BR','DEL','TRQ','JLG.L','CXL.AX','HEI.DE','1101.TW','CRH.L','BZU.MI','LC','MU']
infoList=['PG: Procter and Gamble',
          'Vanguard Europe ETF tracker',
          'Amundi France CAC40 ETF tracker',
          'APAM.AS Aperam (roestvrij staal Belgie, Frankrijk, Brazilie)',      
          'PROX.BR: Proximus',
          'SOLB.BR: Solvay',
          'ABI.BR: AB Inbev',
          'MELE.BR: Melexis: semiconductor for cars, Belgium',
          'MSFT: Microsoft',
          'COFB.BR: Confinimmo (verhuur (zorg)vastgoed belgie)',
          'ELI.BR: Elia (energie (oa veel nulceair), waterzuivering, Belgie, Frankrijk, Nederland, UK, Brazil, Thailand, North and west Africa, Kuwait)',
          'Suez (energie en gas)',
          'BAS.F: BASF',
          'AAPL: Apple',
          'TOTAL S.A.: French oil company not dependent from any state.',
          'Ackermans en van Haren (oa DEME, Bank van Breda)','Bekaert: staaldraad','bpost','Colruyt','galapagos (pharma en R&D)','Ontex',
          'sofina (portefeuille maatschappij - verhofstad)','telenet','UCB (biopharma)','Umicore (autokatalysatoren, smelten edelmetalen)',
          'Nyrstar (zinksmelten) - schuldherschikking',
          'Engie: energie (voorheen oa Suez en Electrabel)',
          'Vale, Brazilie mijnen, grootste ijzererts en nikkel erts. Braziliaanse spoorwegen. Afhankelijk van vraag uit China. Schadeclaims voor dambreuken in Brazilie',
          'NOVN.SW Novartis. Zwisterse big pharma.',
          'LYB: LyondellBasell. Nederlands-Amerikaans. Chemicals, Plastics US and EU (and some in China and Brazil). Leader in PE and PET',
          'WEB.BR Warehouse Estates Belgium. Kantoren, Winkelcentra, in Wallonie.','Orsted: Deens bedrijf dat windmolenparken maakt.',
          'EVS Broadcasting Equipment: materiaal om life uit te zenden op verplaatsing, bv sportwedstrijden. Luik.',
          'ATEB.BR, Atenor: Vastgoed in stadcentra, Belgie, Parijs, Luxemburg, Dusseldorf, Warchau, Budapest. Vrij grote debt.',
          'TESB.BR Tessenderloo Chemie. Gewasbescherming, meststoffen, gelatine.',
          'INGA.AS: ING Bank','KBC.BR: Bank',
          'BNP.PA: Franse bank.',
          'AD.AS: Delhaize en Albert Heijn',
          'ABN.AS: Nederlandse bank',
          'REP.MC: Repsol SA. Spaanse Olie en Gas maatschappij. Productie en raffinage. Productie vooral in Latin America. O.a. ook Venezuela en Libie.',
          'CE: Celanese Corporation (Dallas). Chemie met acetyl: verf, autos, voeding (oa ketons sport supplements)',
          'EMN: Eastman Chemical Company. Coatings, Adhesives and plastics. US.',
          'STERV.HE: Stora Enso. Fins papier bedrijf met bossen in Finland en Zweden. Maakt kartonnen verpappking en ruw hout, houtpulp.',
          'GSH: Guangshen Railway Company Limited. Treinlein tussen Shenzen (Hong Kong) en Guanhzou',
          'WB:Weibo. Chinese microblog (e.g. Twitter). Spin-off of SINA 40%, 30% owned by Alibaba',
          'BABA: Alibaba. Chinese online retail met ambitie voor alles (cloud computing,..), e.g. de Chinese Amazon',
          'ADL.DE: Adler real estate. Duitse Real Estate. Vrij grote debt.',
          'GAZ.DE: Gazprom. 41% Russian Government. Supplies gaseous gas to Europe, Turkey and China via long distance pipelines. Geopolitic conflict with Ukraine started the NorthSteam2 pipline across to Baltic Sea.',
          'WTI: US Company that drills gas from Mexican Gulf',
          'TFG.AS: Tretragon financial investment group. Real Estate, bank loans , bonds, stocks, participations.',
          'AAPL: Apple',
          'RDSA.AS: Royal Dutch Shell, vooral gas nu',
          'MT.AS: Arcelor Mittal. Vooral Europees staal. Is afhankelijk voor de ijzer erts prijs.',
          'AMG.AS: Advanced Metallurgical Group. Maakt oa rotorbladen voor vliegtuigen. Grootste omzet in US en Duitsland. Heeft ingezet op Lithium voor batterijen met oa een mijn in Brazilie.',
          'SLIGR.AS: Nederlandse voedingketen',
          'RIO.L: Rio Tinto: ijzer erts mijnen. Engels-Astralisch. aluminium, iron ore, copper, uranium, and diamonds. Austalie, Papua, Indonesia, Canada, US',
          'VGP.BR:  Logistiek en office vastgoed in Duitsland, CEE Europe en Iberia'
          'AMUN.PA: Franse financiele instelling die trackers en fondsen beheert, voor private investors maar ook voor grotere banken.',
          'FL: Foot Locker. Amerikaanse sportschoenen retailer met vooral (70%) Nike. Winkels in US, Canada, Europa, Australie.',
          'POLY.L: Polymetal international. Engels-Russisch bedrijf met zilver en goudmijnen in Rusland, Armenie en Kazakhstan.',
          'CAM.L: Central Asia Metals PLC. Zink en Loodmijn in Noord Macedonie en Kopermijn in Kazakhtstan.',
          'TECK: Teck Resources. Canadian mining on coal (mostly), copper, zinc (minors lead, silver, gold,..). Divisions in Canada, Mexico, US, Chile and Peru. Investing on oil sands energy winning in ALberta (bitumen, high C-oil, hard to process and environmental concerns.)',
          'KAZ.L: KAZ Minerals PLC. mining and processing copper and other metals primarily in Kazakhstan and Kyrgyzstan',
          'VEDL: Vedanta Limited. Indian mining company in zinc-lead-silver (40%), oil and gas (30%), aluminium (10%), Power (8%) and iron ore(7%). Also a copper plant that is not operational since May2018 because of environmental/political issues. 50% owned by Anil Agarwal family. Zinc mine in RSA too.'
          'BOL.ST: Boliden. Zweedse mijn en smelter met mijnen/smelters in Scandinavie en Ierland. Mijnen: Zinc (29%); Koper (36%), Nickel (5%), Lood (5%), Goud (12%), Zilver (8%). ',
          'FCX: Freeport-NcMoran Inc. Amerikaanse mijn (koper, goud, molybdenium). 2e grootse koper producent ter wereld. 33% mijnen in US (Arizona, New Mex), 33% Chili/Peru en 33% Indonesia (grootste kopermijn ter wereld. Hier moeten ze de volgende jaren wel naar undeground mining gaan ipv open pit. Daarom lagere opbrengst gedurende enkele jaren, en grotere kosten.',
          'S32.L: South32. Australisch/Brits mijnbedrijf. 40% Aluminium, 15% coal, 31% Mangaan, 7% Nickel, 7% Ag/Pb/Zn. Mijnen in Australie, RSA, Peru, Colombia, Mozambique. Looking to sell RSA Coal.',
          'NDA.DE: Grootste kopeproducent Europe, door recyclage. Alle metalen via recyclage, oa computer boards.',
          'BNB.BR: Nationale bank belgie. Belgische staat is voor 50% eigenaar, de andere helf is op de beurs.',
          'NWH-UN.TO: Canadees zorgvastgoed. Grote debt. This company payed a debt interest of 140 million in 2018. By 2023 about 90% of this current debt would be mature. So that is 126 million extra profit on top of the 47 million in 2018 (supposed they stop taking loans now). That would bring the P/E to one quarter of today: - 13.',
          'DEL: Delta Airlines, US.',
          'TRQ: Turqoise Hill. Copper mining porject in Mongolia. Might become one of the largest copper mines in the world. Also for 59% in Ivanhoe Australia?, Kyzyl Gold? in Kazachstan, Gold exploration in China, Phillipines, Indonesia, 14% in Entree Gold  with gold mines in Arizona and Mongolia. 51% owned by Rio Tinto. Vast delays on Oyu Tolgoi.',
          'JLG.L: British developer and operator of privately financed, public sector infrastructure projects such as roads, railways, hospitals and schools',
          'CXL.AX: Austalian R&D company with renawable/environmental technologies in the pipeline like crop protection, waste water treatment, solar energy storage(CaO), cement without CaO (MgO) for CO2 absorbing roads. CO2 scheiding process bij kalk productie. Everything is based on MgO (they own a mine too).',
          'HEI.DE: HeidelbergCement. 40% van de omzet in Europa, de rest diversified over heel de wereld. Leider in West Africa (Nigeria). Investeerde ook in Indonesie. Geloven dat zij leaden ivm CO2 neutraal beton.',
          '1101.TW: Taiwan Cement Corp.',
          'CRH.L: diversified building materials businesses which manufacture and supply of a wide range of products for the construction industry. Largest Irish company. Also own part of LafargeHolcim. Sell twice as much in US than in Europe. Also in China/India.',
          'BZU.MI: italiaanse cement.',
          'LC: Lending Club. Online platform for peer to peer lending. No profit yet.',
          'MU: Micron Technology. American producer of computer memory and computer data storage including dynamic random-access memory, flash memory, and USB flash drives. First to make cell phone 1Terabyte card.']

stocksDict={'code':stocksList,'info':infoList,'yearly Dividend':[]}

#weekly check for opportunity to sell/buy
stocksOfInterest=['J37.SI','INTC','GFS.L','IMMO.BR','ABI.BR']

sumGain=0
for symbol in stocksOfInterest:
    layout,profitPercent=createView(symbol, start='1/1/2014',getStrategyYield=True,longDaysAverage=200,mediumDaysAverage=75,shortDaysAverage=10)
    #sumGain+=profitPercent
    show(layout)

# =============================================================================
# with open('profitStrategy.csv','a') as file:
#     file.write('longTermDays,mediumTermDays,ShortTermDays,symbol \n')
# =============================================================================
    
#print(sumGain)
#insider trading belgie: https://www.fsma.be/nl/transaction-search
    

    
