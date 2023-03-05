from requests_oauthlib import OAuth2Session 
from flask import Flask, request, redirect, session, url_for, render_template 
from requests.auth import HTTPBasicAuth 
import requests 
import json 
 
app = Flask(__name__) 
app.config['SESSION_TYPE'] = 'memcached' 
app.config['SECRET_KEY'] = 'f2da45982e70501308ea4ec5e803fc4a' 
 # client id and client secret details are from the FIDOR portal.
client_id = "922799614d9f1d1f"   
client_secret = 'f2da45982e70501308ea4ec5e803fc4a' 
 
authorization_base_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/authorize' 
token_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/token' 
redirect_uri = 'http://localhost:5000/callback' 
 
 
@app.route('/', methods=["GET"]) 
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
 
@app.route("/services", methods=["GET"]) 
def services(): 
    #Fetching a protected resource using an Oauth 2 token. 
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
 
        return render_template('services.html', fID=customerInformation["id"], 
                fFirstName=customerInformation["first_name"],fLastName=customerInformation["last_name"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100)) 
         
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))

@app.route("/bank_transfer", methods=["GET"]) 
def transfer(): 
   
    try: 
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]
 
        return render_template('internal_transfer.html', fFIDORID=customerDetails["id"], 
                fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100)) 
         
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('.index'))

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
            custEmail = request.form['customerEmailAdd'] 
            transferAmt = int(float(request.form['transferAmount'])*100) 
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
                fRecipientName=transactionDetails["recipient_name"])
    except KeyError: 
        print("Key error in services-to return back to index") 
        return redirect(url_for('default'))
