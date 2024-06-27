# Libraries
import requests
import json
import math
import time
from datetime import datetime
import pandas as pd
#NSE related functoins
import nsepython as nsepython
#Streamlit
import streamlit as st
import traceback

#Custom Component
from streamlit_autorefresh import st_autorefresh

#Page wide mode
st.set_page_config(layout="wide")
st.header('NIFTY and BANKNIFTY Options Toolkit', divider='rainbow')


# FORMATTING CONSOLE DISPLAY colored  text and background
def strRed(skk):         return "\033[91m {}\033[00m".format(skk)
def strGreen(skk):       return "\033[92m {}\033[00m".format(skk)
def strYellow(skk):      return "\033[93m {}\033[00m".format(skk)
def strLightPurple(skk): return "\033[94m {}\033[00m".format(skk)
def strPurple(skk):      return "\033[95m {}\033[00m".format(skk)
def strCyan(skk):        return "\033[96m {}\033[00m".format(skk)
def strLightGray(skk):   return "\033[97m {}\033[00m".format(skk)
def strBlack(skk):       return "\033[98m {}\033[00m".format(skk)
def strBold(skk):        return "\033[1m {}\033[0m".format(skk)

# Method to get nearest strikes
def round_nearest(x,num=50): return int(math.ceil(float(x)/num)*num)
def nearest_strike_bnf(x): return round_nearest(x,100)
def nearest_strike_nf(x): return round_nearest(x,50)

# NSE Urls for Data fetching 
url_oc      = "https://www.nseindia.com/option-chain"
url_bank_nifty     = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nifty      = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
url_indices = "https://www.nseindia.com/api/allIndices"

# Headers
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'}

sess = requests.Session()
cookies = dict()

# Local methods
def set_cookie():
    request = sess.get(url_oc, headers=headers, timeout=8)
    cookies = dict(request.cookies)

def get_data(url):
    try:

        set_cookie()
        response = sess.get(url, headers=headers, timeout=5, cookies=cookies)
        if(response.status_code==401):
            set_cookie()
            response = sess.get(url_nifty, headers=headers, timeout=5, cookies=cookies)
        if(response.status_code==200):
            return response.text
        return ""
    except Exception as e:
        print(e)

def set_header():
    try:

        global bnf_ul
        global nf_ul
        global bnf_nearest
        global nf_nearest
        response_text = get_data(url_indices)
        data = json.loads(response_text)
        for index in data["data"]:
            if index["index"]=="NIFTY 50":
                nf_ul = index["last"]
                print("nifty")
            if index["index"]=="NIFTY BANK":
                bnf_ul = index["last"]
                print("banknifty")
        bnf_nearest=nearest_strike_bnf(bnf_ul)
        nf_nearest=nearest_strike_nf(nf_ul)
    except Exception as e:
        print(e)




#Get the oi data as dictionary
def get_io(num,step,nearest,url):
    try:

        strike = nearest - (step*num)
        start_strike = nearest - (step*num)
        response_text = get_data(url)
        data = json.loads(response_text)
        data_list = []
        currExpiryDate = data["records"]["expiryDates"][0]
        for item in data['records']['data']:
            if item["expiryDate"] == currExpiryDate:
                if item["strikePrice"] == strike and item["strikePrice"] < start_strike+(step*num*2):
                    print(f"strikePrice: {item['strikePrice']} , step:{step} , nearest: {nearest} , nearest-step: {nearest-step} , nearest+step : {nearest+step} ")
                    if item["strikePrice"] == (nearest-step) or item["strikePrice"] == nearest or  item["strikePrice"] == (nearest+step):
                        print(strGreen(data["records"]["expiryDates"][0] + " "  + " CE " + "[ " + strBold("OI:"+str(item["CE"]["openInterest"])) +strBold("LTP:"+str(item["CE"]["lastPrice"]))+ strBold("CHNG:"+str(round(item["CE"]["change"],2)))+ " ] ") + strPurple(item["strikePrice"])+ strRed(" PE " + "[ " + strBold("OI:"+str(item["PE"]["openInterest"]).rjust(10," ")) +strBold("LTP:"+str(item["PE"]["lastPrice"]))+ strBold("CHNG:"+str(round(item["PE"]["change"],2)))+ " ]"))
                        #st.write(data["records"]["expiryDates"][0]  +" "+symbol+" STRK - "+str(item["strikePrice"])+"  - " + " CE " + "[ " + str("LTP:"+str(item["CE"]["lastPrice"]))+ str("  CHNG:"+str(round(item["CE"]["change"],2)))+ " ] " + " PE " + "[ " + str("LTP:"+str(item["PE"]["lastPrice"]))+ str(("  CHNG:"+str(round(item["PE"]["change"],2))))+ " ]")
                        data_list.append({'expiry':str(data["records"]["expiryDates"][0]),'strike':item["strikePrice"],'ce_ltp':item["CE"]["lastPrice"],'ce_change':round(item["CE"]["change"],2),'pe_ltp':item["PE"]["lastPrice"],'pe_change':round(item["PE"]["change"],2)})
                        #return {'expiry':str(data["records"]["expiryDates"][0]),'strike':nearest,'ce_ltp':item["CE"]["lastPrice"],'ce_change':round(item["CE"]["change"],2),'pe_ltp':item["PE"]["lastPrice"],'pe_change':round(item["PE"]["change"],2)}
                    strike = strike + step
        print(str(data_list))
        return data_list
    except Exception as e:
        print(e)

#OI Plot function
def oi_plot(num,step,nearest,url):
    #print(f" oi_plot() called with {num},{step},{nearest},{url} ")
    try:

        strike = nearest - (step*num)
        start_strike = nearest - (step*num)
        response_text = get_data(url)
        data = json.loads(response_text)
        currExpiryDate = data["records"]["expiryDates"][0]
        max_oi = 0
        max_oi_strike = 0
        ce_oi_list = []
        pe_oi_list = []
        oi_strike_list = []
        #st.divider()
        for item in data['records']['data']:
            #st.write(f"ITEM {item}")
            if item["expiryDate"] == currExpiryDate:
                if "PE" in item:
                    pe_oi_list.append(item["PE"]["openInterest"])
                else:
                    pe_oi_list.append(0)

                if "CE" in item:
                    ce_oi_list.append(item["CE"]["openInterest"])
                else:
                    ce_oi_list.append(0)

                oi_strike_list.append(item["strikePrice"])

                if item["strikePrice"] == strike and item["strikePrice"] < start_strike+(step*num*2):
                    if "CE" in item:
                        if item["CE"]["openInterest"] > max_oi:
                            max_oi = item["CE"]["openInterest"]
                            max_oi_strike = item["strikePrice"]
               

                strike = strike + step
                       
               
        #print(f"URL {url} , ce_oi_list {len(ce_oi_list)} pe_oi_list {len(pe_oi_list)}")
        chart_data = pd.DataFrame(
        {
            "CE_OI": ce_oi_list,
            "PE_OI": pe_oi_list,
            "Strike": oi_strike_list,
       
        })
        #print(f" {url}, {chart_data.head()}")
        #st.bar_chart(chart_data,x="Strike", y=["CE_OI","PE_OI"], color=["#0000FF","#FF0000"])
                    
        #return max_oi_strike
        return chart_data
    except Exception as e:
        st.error(f"Error while processing {url}  and the error is {e} and trace is {traceback.format_exc()}")


# Finding highest Open Interest of People's in CE based on CE data         
def highest_oi_CE(num,step,nearest,url):
    try:

        strike = nearest - (step*num)
        start_strike = nearest - (step*num)
        response_text = get_data(url)
        data = json.loads(response_text)
        currExpiryDate = data["records"]["expiryDates"][0]
        max_oi = 0
        max_oi_strike = 0
        for item in data['records']['data']:
            if item["expiryDate"] == currExpiryDate:
                if item["strikePrice"] == strike and item["strikePrice"] < start_strike+(step*num*2):
                    if item["CE"]["openInterest"] > max_oi:
                        max_oi = item["CE"]["openInterest"]
                        max_oi_strike = item["strikePrice"]
                    strike = strike + step
        return max_oi_strike
    except Exception as e:
        print(e)

# Finding highest Open Interest of People's in PE based on PE data 
def highest_oi_PE(num,step,nearest,url):
    try:

        strike = nearest - (step*num)
        start_strike = nearest - (step*num)
        response_text = get_data(url)
        data = json.loads(response_text)
        currExpiryDate = data["records"]["expiryDates"][0]
        max_oi = 0
        max_oi_strike = 0
        for item in data['records']['data']:
            if item["expiryDate"] == currExpiryDate:
                if item["strikePrice"] == strike and item["strikePrice"] < start_strike+(step*num*2):
                    if item["PE"]["openInterest"] > max_oi:
                        max_oi = item["PE"]["openInterest"]
                        max_oi_strike = item["strikePrice"]
                    strike = strike + step
        return max_oi_strike
    except Exception as e:
        print(e)


if __name__ == "__main__":
    
    # creating a single-element container.
    #main()
    # Run the autorefresh about every 60000 milliseconds (60 seconds) 
    count = st_autorefresh(interval=30000, limit=10000, key="mycounter")
    #st.caption(f"Last Page Refresh datetime: {datetime.now()} and Count:{count}")
    #while True:
    niftycol = st.columns(1)
    bnkniftycol = st.columns(1)
    nifty_bank_quote = nsepython.nse_get_index_quote("nifty bank")
    nifty_quote = nsepython.nse_get_index_quote("nifty 50")
    set_header()
    bnf_nearest=nearest_strike_bnf(bnf_ul)
    nf_nearest=nearest_strike_nf(nf_ul)
    nifty_oi_data = get_io(2,50,nf_nearest,url_nifty)
    bank_nifty_oi_data = get_io(2,100,bnf_nearest,url_bank_nifty)
    # Finding Highest OI in Call Option In Nifty
    nf_highestoi_CE = highest_oi_CE(10,50,nf_nearest,url_nifty)
    
    #oi_plot(10,50,nf_nearest,url_nifty)

    # Finding Highet OI in Put Option In Nifty
    nf_highestoi_PE = highest_oi_PE(10,50,nf_nearest,url_nifty)
    

    # Finding Highest OI in Call Option In Bank Nifty
    bnf_highestoi_CE = highest_oi_CE(20,100,bnf_nearest,url_bank_nifty)
    
    #oi_plot(10,100,bnf_nearest,url_bank_nifty)

    # Finding Highest OI in Put Option In Bank Nifty
    bnf_highestoi_PE = highest_oi_PE(20,100,bnf_nearest,url_bank_nifty)
    #oicol1,oicol2 = st.columns(2)
    nifty_chart_data = oi_plot(5,50,nf_nearest,url_nifty)
    #st.write(f"NIFTY CHART Data {nifty_chart_data}")
    bank_nifty_chart_data = oi_plot(10,100,bnf_nearest,url_bank_nifty)
    #print(bank_nifty_chart_data.head(3))
    #st.write(bank_nifty_chart_data)
    st.metric("NIFTY Index",nifty_quote['last'],nifty_quote['percChange'])
    st.write(f"NIFTY Exp-{nifty_oi_data[0]['expiry']} :blue[LTP {str(nf_ul)}], :gray[CE[ ATM:{str(nf_nearest)},ITM:{str(nf_nearest-50)},OTM:{str(nf_nearest+50)}]], :gray[PE[ ATM:{str(nf_nearest)}, ITM:{str(nf_nearest+50)}, OTM:{str(nf_nearest-50)}]], :green[OI_SUP {str(nf_highestoi_PE)}] :red[OI_RES {str(nf_highestoi_CE)}]")
    
    col1,col2,col3,col4,col5,col6 = st.columns(6)
    placeholder = st.empty()
    with placeholder.container():
                    col1.metric(label="NIFTY"+str(nifty_oi_data[0]['strike'])+" CE", value=str(nifty_oi_data[0]['ce_ltp']), delta=str(nifty_oi_data[0]['ce_change']))
                    col2.metric(label="NIFTY"+str(nifty_oi_data[0]['strike'])+" PE", value=str(nifty_oi_data[0]['pe_ltp']), delta=str(nifty_oi_data[0]['pe_change']))
                    col3.metric(label="NIFTY"+str(nifty_oi_data[1]['strike'])+" CE", value=str(nifty_oi_data[1]['ce_ltp']), delta=str(nifty_oi_data[1]['ce_change']))
                    col4.metric(label="NIFTY"+str(nifty_oi_data[1]['strike'])+" PE", value=str(nifty_oi_data[1]['pe_ltp']), delta=str(nifty_oi_data[1]['pe_change']))
                    col5.metric(label="NIFTY"+str(nifty_oi_data[2]['strike'])+" CE", value=str(nifty_oi_data[2]['ce_ltp']), delta=str(nifty_oi_data[2]['ce_change']))
                    col6.metric(label="NIFTY"+str(nifty_oi_data[2]['strike'])+" PE", value=str(nifty_oi_data[2]['pe_ltp']), delta=str(nifty_oi_data[2]['pe_change']))
                    #st.text("NIFTY "+nifty_oi_data[0]['expiry']+ " LTP :"+str(nf_ul) +" NIFTY Supp PE_OI:"+str(nf_highestoi_PE)+ " Res CE_OI:"+str(nf_highestoi_CE))
                    st.caption(datetime.now())
                    st.divider()
    with st.expander("Click to see Nifty OI"):
        st.bar_chart(nifty_chart_data,x="Strike", y=["CE_OI","PE_OI"], color=["#0000FF","#FF0000"])
    
    #BANK NIFTY related display
    st.metric("BANKNIFTY Index",nifty_bank_quote['last'],nifty_bank_quote['percChange'])
    st.write(f"BANKNIFTY Exp-{bank_nifty_oi_data[0]['expiry']} :blue[LTP {str(bnf_ul)}] , :gray[ CE[ATM: {str(bnf_nearest)},ITM:{str(bnf_nearest-100)},OTM:{str(bnf_nearest+100)}]], :gray[PE[ ATM:{str(bnf_nearest)}, ITM:{str(bnf_nearest+100)}, OTM:{str(bnf_nearest-100)}]], :green[OI_SUP {str(bnf_highestoi_PE)}],  :red[OI_RES {str(bnf_highestoi_CE)}]")
    bnf_col1,bnf_col2,bnf_col3,bnf_col4,bnf_col5,bnf_col6 = st.columns(6)
    placeholder = st.empty()
    with placeholder.container():
        bnf_col1.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[0]['strike'])+" CE", value=str(bank_nifty_oi_data[0]['ce_ltp']), delta=str(bank_nifty_oi_data[0]['ce_change']))
        bnf_col2.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[0]['strike'])+" PE", value=str(bank_nifty_oi_data[0]['pe_ltp']), delta=str(bank_nifty_oi_data[0]['pe_change']))
        bnf_col3.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[1]['strike'])+" CE", value=str(bank_nifty_oi_data[1]['ce_ltp']), delta=str(bank_nifty_oi_data[1]['ce_change']))
        bnf_col4.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[1]['strike'])+" PE", value=str(bank_nifty_oi_data[1]['pe_ltp']), delta=str(bank_nifty_oi_data[1]['pe_change']))
        bnf_col5.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[2]['strike'])+" CE", value=str(bank_nifty_oi_data[2]['ce_ltp']), delta=str(bank_nifty_oi_data[2]['ce_change']))
        bnf_col6.metric(label="BANKNIFTY"+str(bank_nifty_oi_data[2]['strike'])+" PE", value=str(bank_nifty_oi_data[2]['pe_ltp']), delta=str(bank_nifty_oi_data[2]['pe_change']))
        #st.caption("BANKNIFTY "+bank_nifty_oi_data[0]['expiry']+ " LTP :"+str(bnf_ul) + " BANKNIFTY Supp PE_OI:"+str(bnf_highestoi_PE)+" Res CE_OI:"+str(bnf_highestoi_CE))
        st.caption(datetime.now())
        st.divider()
    with st.expander("Click to see BankNifty OI"):
        st.bar_chart(bank_nifty_chart_data,x="Strike", y=["CE_OI","PE_OI"], color=["#0000FF","#FF0000"])

    