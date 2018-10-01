# -*- coding: utf-8 -*-
"""
@author: Franz Georg Fuchs
Bachelorarbeit
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math


"Hier werden die benötigten Daten geladen"
def set_profile_data_path():
    profile_path = 'C:\\Users\\Franz Georg\\Documents\\Uni\\Bachelorarbeit\\Daten\\LoadProfiles2010_sorted_kWhper15min_one_sheet2.csv';
    return profile_path;

def set_gen_path():
    gen_path = 'C:\\Users\\Franz Georg\\Documents\\Uni\\Bachelorarbeit\\Daten\\PV_Generation_15min_Vienna.csv';
    return gen_path;

def extract_data_from_csv(filepath,index_column):
    data = pd.DataFrame();
    return data.from_csv(filepath,index_column).as_matrix();

def extract_profile():
    profile_path = set_profile_data_path();
    return extract_data_from_csv(profile_path,0)[:,:];

def extract_gen():
    profile_path = set_gen_path();
    return 5*extract_data_from_csv(profile_path,0);        "Hart codierter Faktor 5 für die Erzeugung, entsprechend der angenommenen Größe der Anlage"

"Summiert die übergebenen Profile auf"
def aggregate_profiles(profiles):
     agg = profiles[0];
     for i in range(1,len(profiles)):
        agg += profiles[i];
     return agg;

"trennt die erzeugte Energie auf in Verbrauch und Überschuss"        
def allocate_gen(profiles):
    usage = aggregate_profiles(profiles);
    production = extract_gen();
    used = [];
    excess = [];   
    for i in range(0,len(usage)):
        prod = production[i];       
        if prod[0] <= usage[i]:
            used.append(prod[0]);
            excess.append(0.0);
        else:
            used.append(usage[i]);
            excess.append(prod[0]-usage[i]);
    return used, excess, production; 

"Verteilt den Strom entsprechend des jeweiligen Bieterpreises"
def allocate_usage(profiles,payment_willingness):
    used, excess, production = allocate_gen(profiles);   
    out = [];
    willingness = list(payment_willingness);
    for i in range(0,len(willingness)):
       index = np.argmax(willingness);
       out.append(used-np.clip(used-profiles[index],0,math.inf));
       used = used - out[i];
       willingness[index] = 0.0;       
    return out;

"Nachkorrektur falls zwei Parteien den exakt gleichen Preis bieten"
def handle_equal_price(distribution, payment_willingness):
    res = [];    
    willingness = np.sort(payment_willingness)[::-1];
    for i in range(0, len(willingness)):      
        if (i == 0):
            use = distribution[i];            
            counter = 1;
        else:
            if (willingness[i] == willingness[i-1]):
                use += distribution[i];
                counter +=1;
            else:                
                for j in range (0, counter): 
                    res.append(use/counter);
                use = distribution[i];
                counter = 1;                
    for k in range (0, counter):
        res.append(use/counter);
    return res;    

"Ermittlung des jeweiligen marginalen Preises je Zeiteinheit. Der komische Zahlenwert soll eine korrekte Behandlung von Null gewährleisten"
def find_marginal_price(payment_willingness, profiles):
    willingness = np.sort(payment_willingness); 
    price = np.full_like(profiles[0],willingness[0]);   
    for i in range (0, len(profiles)):        
        for j in range (0, len(profiles[i])):
            if (abs(profiles[i][j]) < 0.0001): 
                if i < len(profiles)-1:
                    price[j] = willingness[i+1];
    return price;

"Ermittelt die jeweiligen Zahlungsvektoren"
def get_payment(profiles, price):
    payment = [];
    for i in range (0, len(profiles)):
        payment.append(profiles[i]*price);       
    return payment;

"Errechnet den gesamten Verbrauch"
def get_total_allocation(profiles):
    allocation = 0.0
    for i in range(0,len(profiles)):
        allocation+= profiles[i].sum();
    return allocation;

"Errechnet den allokierten Verbrauch je Haushalt"
def get_profiles_alloc_sums(allocation):
    totals = [];
    for i in range(0,len(allocation)):
        totals.append(allocation[i].sum());
    return totals;  
"Bisher nicht im Einsatz. Würde für das diskriminierende Preismodell benötigt"
def get_total_payout_disc(totals, payment_willingness,net_price, profiles):
    willingness = np.sort(payment_willingness);
    payout = totals*willingness;
    return payout.sum()+net_price*(extract_gen().sum()-get_total_allocation(profiles));       

"Summiert die Erlöse eines Jahres"
def get_total_payout(payment,net_price,profiles):
    payout = 0.0;
    for i in range(0,len(payment)):
        payout+=payment[i].sum();    
    excess = extract_gen().sum()-get_total_allocation(profiles);
    payout += excess*net_price; 
    return payout;

"Diskontiert den Erlöscashflow"
def discount_cashflow(payment, annuity_factor):
    return payment/annuity_factor;

"Hier werden noch einige Annahmen gesetzt"   
net_price = 0.03;
investment_cost = 24254;
fix_cost = 200;
interest_rate = 0.025; 
years = 20;

"Einige Vorbereitungen"
annuity_factor = ((1+interest_rate)**years)*interest_rate/((1+interest_rate)**years - 1);
profiles = extract_profile().transpose();
total_willingness = extract_data_from_csv('C:\\Users\\Franz Georg\\Documents\\Uni\\Bachelorarbeit\\Daten\\PaymentWillingness.csv',0);    
prod = extract_gen().sum();
result = [];

print(annuity_factor);
#print(prod);
    
"Eigentliche MC-Simulation"

for i in range(0,10000):  
    payment_willingness = total_willingness[np.random.randint(10000, size=10)];
    chosen_profiles = profiles[np.random.randint(73,size=10)]; 
    test = allocate_usage(chosen_profiles,payment_willingness);
    corr = handle_equal_price(test, payment_willingness);
    price = find_marginal_price(payment_willingness, corr);
    payment = get_payment(corr, price);
    payout = get_total_payout(payment,net_price,corr);
    allocation = get_total_allocation(corr);
    total = get_profiles_alloc_sums(corr);
    value = discount_cashflow(payout-fix_cost, annuity_factor)-investment_cost;
    result.append(value);

"Formatieren und Herausschreiben der Ergebnisse"
#result = pd.DataFrame(result);    
#result.to_csv(path_or_buf='C:\\Users\\Franz Georg\\Documents\\Uni\\Bachelorarbeit\\Daten\\Results.csv');
