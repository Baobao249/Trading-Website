from flask import Flask, render_template, redirect, url_for, request, session
from requests_oauthlib import OAuth2Session 
from requests.auth import HTTPBasicAuth 
import requests
import json
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import ta
from ta.trend import MACD
from datetime import datetime
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached' 
app.config['SECRET_KEY'] = 'e6ce8d168bf77e2f1ceb2cb8ae14b1a2' 
 # client id and client secret details are from the FIDOR portal.
client_id = "39721985718515ee"   
client_secret = 'e6ce8d168bf77e2f1ceb2cb8ae14b1a2' 
 
authorization_base_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/authorize' 
token_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/token' 
redirect_uri = 'http://localhost:5000/callback'

@app.route('/index', methods=["GET"]) 
def default(): 
 
    try: 
        #Step 1: User Application Authorization 
        #sending authorization client ID and client Secret to Fidor for authorization 
        fidor = OAuth2Session(client_id,redirect_uri=redirect_uri)
        authorization_url, state = fidor.authorization_url(authorization_base_url)
        # State is used to prevent CSRF, keep this for later.    
        print("state is ="+state) 
        session['oauth_state'] = state 
        print("authorization URL is =" +authorization_url) 
        return redirect(authorization_url) 
    except KeyError: 
        print("Key error in default-to return back to index") 
        return redirect(url_for('default')) 

@app.route("/callback", methods=["GET"]) 
def callback(): 
    try: 
        #Step 2: Retrieving an access token. 
        #The user has been redirected back from the provider to your registered  
        #callback URL. With this redirection comes an authorization code included 
        #in the redirect URL. We will use that to obtain an access token. 
        fidor = OAuth2Session(state=session['oauth_state']) 
        authorizationCode = request.args.get('code') 
        body = 'grant_type="authorization_code&code='+authorizationCode+ \
        '&redirect_uri='+redirect_uri+'&client_id='+client_id 
        auth = HTTPBasicAuth(client_id, client_secret) 
        token = fidor.fetch_token(token_url,auth=auth,code=authorizationCode,body=body,method='POST') 
        #At this point you can fetch protected resources but lets save 
        #the token and show how this is done from a persisted token 
        session['oauth_token'] = token 
        return redirect(url_for('.home'))
 
    except KeyError:     
        print("Key error in callback-to return back to index") 
        return redirect(url_for('default'))

@app.route('/failedTransaction', methods=['GET'])
def failedTransaction(): 
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 
        
        return render_template('transaction_failed.html', fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100)) 
    
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))


@app.route('/home', methods=['GET'])
def home(): 
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 
        
        return render_template('home.html', fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100)) 
    
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

@app.route('/stock', methods=['GET'])
def stock():
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 

        return render_template('stock.html', fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100))
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

@app.route('/result', methods=['GET', 'POST'])
def result():
    error = None
    try:
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 

        
        if request.method == "POST":
            ticker_code = request.form['stockSymbol']
            timeLine = request.form['timeLine']  
            # Retreives the CNY/SGD exchange rate
            url4 = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=CNY&to_currency=SGD&apikey=W6Z1AKFZL4R1GZY4C"
            payload4 = {}
            headers4 = {}
            response4 = requests.request("GET", url4, headers=headers4, data=payload4)
            stockdata4 = json.loads(response4.text)
            exchangeRate = stockdata4["Realtime Currency Exchange Rate"]
            cnysgdRate = float(exchangeRate["5. Exchange Rate"])


        # Retrieved Data based on timeLine chosen
        if timeLine == "Daily":
            #daily api
            url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol="+ticker_code+"&outputsize=full&apikey=W6Z1AKFZL4R1GZY4C"
            #weekly api 
        elif timeLine == "Weekly":
            url = "https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol="+ticker_code+"&outputsize=full&apikey=W6Z1AKFZL4R1GZY4C"
            #monthly api 
        else :
            url = "https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol="+ticker_code+"&outputsize=full&apikey=W6Z1AKFZL4R1GZY4C"

        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
       
       #convert from JSON string to python dictionary
        stockData = json.loads(response.text)
       
        #To retrieve the latest date from Realtime Currency Exchange Rate
        latestDate = list(stockData["Time Series (Daily)" if timeLine == "Daily" else "Weekly Time Series" if timeLine == "Weekly" else "Monthly Time Series"].keys())[0]  # modified line
        latestStockPrices = stockData["Time Series (Daily)" if timeLine == "Daily" else "Weekly Time Series" if timeLine == "Weekly" else "Monthly Time Series"][latestDate]  # modified line
        openingPrice = latestStockPrices ["1. open"]
        highPrice = latestStockPrices ["2. high"]
        lowPrice = latestStockPrices ["3. low"]
        closingPrice = latestStockPrices ["4. close"]

        sgdOpeningPrice = float(openingPrice) * cnysgdRate
        sgdOpeningPrice = round(sgdOpeningPrice, 3)

        sgdHighPrice = float(highPrice) * cnysgdRate
        sgdHighPrice = round(sgdHighPrice, 3)

        sgdLowPrice = float(lowPrice) * cnysgdRate
        sgdLowPrice = round(sgdLowPrice, 3)

        sgdClosingPrice = float(closingPrice) * cnysgdRate
        sgdClosingPrice = round(sgdClosingPrice, 3)




        response = requests.get(url).json()

        # Graph Building, Get data of the fund from stockdata
        stockData = response["Time Series (Daily)" if timeLine == "Daily" else "Weekly Time Series" if timeLine == "Weekly" else "Monthly Time Series"]
        
        # Coverting stock data into panda dataframe
        df = pd.DataFrame(stockData)
        df = df.T
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)

        #Computation of the macd line
        macd = MACD(df['4. close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd.macd()
        df['signal'] = macd.macd_signal()

        # Creating two subplots, one for Candlestick and another for Line Graph
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing= 0.1)

        # Adding Candlestick chart to the first plot
        fig.add_trace(go.Candlestick(x=df.index, open=df["1. open"], high=df["2. high"], low=df["3. low"], close=df["4. close"], increasing=dict(line=dict(color='green')), decreasing=dict(line=dict(color='red'))), row=1, col=1)

        # Adding Line Graph chart to the second plot
        fig.add_trace(go.Scatter(x=df.index, y=df['4. close'], name='Linegraph', line=dict(color='blue')), row=2, col=1)

        # Adding MACD and MA20 indicators to the first plot
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD Candlestick'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['signal'], name='Signal Candlestick'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['4. close'].rolling(window=20).mean(), name='MA20 Candlestick'), row=1, col=1)

        # Adding MACD and MA20 indicators to the second plot
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD Line Graph'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['signal'], name='Signal Line Graph'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['4. close'].rolling(window=20).mean(), name='MA20 Line Graph'), row=2, col=1)

        fig.update_layout(height=500, width=1200, title_text="Stock Analysis for {}".format(ticker_code), xaxis_rangeslider_visible=False, plot_bgcolor='white')

        # plot_html will be how we will be able to show the chart.
        plot_html = fig.to_html(full_html=False)

        # Retrieve Market opening and closing time, made use of demo api key as i don't need to use my api key retrieve this info
        url2 = "https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=demo"
        payload2 ={}
        headers2 = {}

        response2 = requests.request("GET", url2, headers=headers2, data=payload2)
        stockData2 = json.loads(response2.text)
        openingTime = stockData2["markets"][9]
        timeOpen = openingTime["local_open"]
        timeClose = openingTime["local_close"]
        status = openingTime["current_status"]
        notes = openingTime["notes"]

        # Retrieve Current Price, as well as changes in price and changes in percentage

        url3 = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol="+ticker_code+"&apikey=W6Z1AKFZL4R1GZY4C"
        payload3 = {}
        headers3 = {}

        response3 = requests.request("GET", url3, headers=headers3, data=payload3)
        stockData3 = json.loads(response3.text)
        priceQuotes = stockData3["Global Quote"]
        price = priceQuotes["05. price"]
        change = priceQuotes["09. change"]
        percentChange = priceQuotes["10. change percent"]
        sgdPrice = cnysgdRate * float(price)
        sgdPrice = round(sgdPrice, 3)

        session['price'] = sgdPrice
        session['ticker'] = ticker_code

        url5 = "https://yahoo-finance15.p.rapidapi.com/api/yahoo/mo/module/"+ticker_code+"?module=financial-data"

        payload5 = "\r\n"
        headers5 = {
        'X-RapidAPI-Key': 'a79f1ac0e3msh3c1df9677d16871p1fd94ajsnde2b6462d50c',
        'X-RapidAPI-Host': 'yahoo-finance15.p.rapidapi.com'
        }

        response5 = requests.request("GET", url5, headers=headers5, data=payload5)
        stockdata5 = json.loads(response5.text)
        if isinstance(stockdata5["financialData"], list):
            print("financialData is a list")
        elif isinstance(stockdata5["financialData"], dict):
            print("financialData is a dictionary")
        else:
            print("financialData is not a list or a dictionary")
        financialQuotes = stockdata5["financialData"]
        print(financialQuotes)
        if len(financialQuotes) > 0:
            pms = financialQuotes["profitMargins"]['fmt']
            rg = financialQuotes["revenueGrowth"]['fmt']
            roa = financialQuotes["returnOnAssets"]['fmt']
            roe = financialQuotes["returnOnEquity"]['fmt']   
        else: 
            pms = "No data"
            rg = "No data"
            roa = "No data"
            roe = "No data" 
        
        country = 'China'
        url6 = 'https://api.api-ninjas.com/v1/inflation?country={}'.format(country)
        response6 = requests.get(url6, headers={'X-Api-Key': 'F8F+vCFae83FUldhN+UxRA==hg1tDAsqTr6mEz6i'})
        stockdata6 = json.loads(response6.text)
        cpi = stockdata6[0]["yearly_rate_pct"]
            
    # handle the case where the list is empty
        #quickRatio = stockdata5["financialData"]["quickRatio"][0]
        #currentRatio = stockdata5["financialData"]["currentRatio"][0]
        
         #QuickRatio = quickRatio, CurrentRatio = currentRatio, 


        return render_template('stock.html', CPI = cpi, PMS = pms, wRG = rg ,Roa = roa, Roe = roe, wTickerCode = ticker_code, wTimeLine = timeLine,
         wOpeningPrice = sgdOpeningPrice, wHighPrice = sgdHighPrice, wLowPrice = sgdLowPrice, wClosingPrice = sgdClosingPrice, wTimeOpen = timeOpen, wTimeClose = timeClose, wStatus = status, wNotes = notes , plot_html=plot_html, Price = price, Change=change, PercentChange = percentChange,sgdPrice = sgdPrice, fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100) )
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

@app.route("/buy", methods=['GET'])
def buy():
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 
        symbol = session['ticker'] 
        price = session['price']
 
        return render_template('buy.html', fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100), Symbol = symbol, Price = price) 
         
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

@app.route("/process", methods=["POST"]) 
def process(): 
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 
    
        if request.method == "POST":    
            token = session['oauth_token'] 
            customersAccount = session['fidor_customer'] 
            customerDetails = customersAccount['data'][0] 
            fidorID = customerDetails['id']
            custEmail = "studentB09@email.com"
            #fidorID = customerDetails['id'] 
            #custEmail = request.form['customerEmailAdd'] 
            transferAmt = int(float(request.form['transferAmt'])*100)
            if transferAmt > 50000:
                return redirect(url_for('failedTransaction'))
            else:
                transferRemarks = request.form['transferRemarks']     
                transactionID = request.form['transactionID']

                url = "https://api.tp.sandbox.fidorfzco.com/internal_transfers"

                payload = "{\n\t\"account_id\": \""+fidorID+"\",\n\t\"receiver\": \""+ \
                        custEmail+"\", \n\t\"external_uid\": \""+transactionID+"\",\n\t\"amount\": "+ \
                        str(transferAmt)+",\n\t\"subject\": \""+transferRemarks+"\"\n}\n"

                headers = {
                    'Accept': "application/vnd.fidor.de; version=1.text/json",
                    'Authorization': "Bearer "+token["access_token"],
                    'Content-Type': "application/json"

                }
                response = requests.request("POST", url, data=payload, headers=headers) 
            
                print("process="+response.text)

                transactionDetails = json.loads(response.text) 
                return render_template('transfer_result.html',fTransactionID=transactionDetails["id"], 
                        custEmail=transactionDetails["receiver"],fRemarks=transactionDetails["subject"], 
                        famount=(float(transactionDetails["amount"])/100), 
                        fRecipientName=transactionDetails["recipient_name"],fID=customerInformation["id"], 
                            fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                            fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100))
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))


@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount


        endpoint = 'https://api.tp.sandbox.fidorfzco.com/transactions'
        response = requests.get(endpoint, headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()['data']
            # Create a list to hold the transactions
            transactions = []
            # Iterate over each transaction in the data
            for transaction in data:
                amount_formatted = "{:.2f}".format(abs(transaction["amount"]) / 100)
                date = datetime.strptime(transaction['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                # Format the date as a string
                date_formatted = date.strftime('%B %d, %Y')
                # Check if the recipient is "studentb09@email.com"
                if transaction['transaction_type_details']['recipient'] == 'studentb09@email.com':
                    # Extract the relevant information from the transaction
                    transaction_info = {
                        'subject': transaction['transaction_type_details']['remote_subject'],
                        'amount': amount_formatted,
                        'date': date_formatted
                    }
                    # Add the transaction information to the transactions list
                    transactions.append(transaction_info)
                    print(transaction)
            # Render the transactions page and pass in the transactions list
            return render_template('transaction.html', transactions=transactions, fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100),)
 
             
    except KeyError: 
         print("Key error in services-to return back to index")
    return render_template('home.html', error_message="An error occurred while processing your request.")


articles = []

@app.route('/news', methods=['GET'])
def news():
    try: 
        token = session['oauth_token'] 
        url = "https://api.tp.sandbox.fidorfzco.com/accounts" 
 
        payload = "" 
        headers = { 
            'Accept': "application/vnd.fidor.de;version=1;text/json", 
            'Authorization': "Bearer "+token["access_token"] 
        } 
        response = requests.request("GET", url, data=payload, headers=headers) 
        print("services=" + response.text) 
        customerAccount = json.loads(response.text) 
        customerDetails = customerAccount['data'][0] 
        customerInformation = customerDetails['customers'][0] 
        session['fidor_customer'] = customerAccount 
        
        
        # Define the API endpoint URL
        endpoint = "https://newsapi.org/v2/everything"

        # Define your API key
        api_key = "19d0c7e0ce30433da0260591ca85e234"

        # Define the parameters for the API request
        params = {
            "q": "china equity", # search query to retrieve forex news
            "pageSize": 20, # number of results to retrieve
            "apiKey": api_key
        }

        # Make the API request
        response = requests.get(endpoint, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            news = response.json()

            # Store the articles in a list
            articles.clear()
            for article in news["articles"]:
                # Parse the date string
                articles.append({
                    "title": article["title"],
                    "description": article["description"],
                    "url": article["url"],
                    "content": article["content"],
                    "id": hash(article["url"]),
                    "publishedAt": article["publishedAt"],
                    "urlToImage": article["urlToImage"]

                })
        else:
            # If the request failed, print an error message
            print("Error:", response.text)

        return render_template('news.html', articles = articles, fID=customerInformation["id"], 
                    fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                    fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100))
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

if __name__ == '__main__':
    app.run(debug=True)















    