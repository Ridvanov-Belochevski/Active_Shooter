# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 21:00:13 2022

@author: wb563112
"""

#Import the required libraries
import os
import pandas as pd
import re
import numpy as np
from collections import defaultdict

#Import the data and get rid of empty rows
os.chdir("C:/Users/WB563112/Downloads")
raw_df = pd.read_excel("Active_shooter_raw_extract_from_pdf.xlsx", index_col=[0])
raw_df = raw_df[raw_df.Events.notna()]

#Determine which row in the data is an event header row by extracting the words in a bracket
raw_df['loc_type']=raw_df['Events'].str.extract(r"(\(\w+[\s\w+]*\))")
possible_options = ["(Commerce)", "(Education)", "(Government)", "(Open Space)",
                    "(Residences)", "(Health Care)", "(House of Worship)"]
#if the bracketed terms are in possible_options, that is an event header.
for idx,row in raw_df.iterrows():
    if row["loc_type"] in possible_options:
        raw_df.loc[idx,"new_event"] = True
        raw_df.loc[idx,"location"] = row["Events"] if raw_df.loc[idx,"new_event"]==True else ""
        
print(raw_df.loc_type.value_counts())
print(raw_df.new_event.sum())
print(raw_df.location.nunique())

#Transform dataframe into a two column df containing event location and event details
events_dict = defaultdict(str)
true_count = 0
false_count = 0

#For each row in the df
for idx,row in raw_df.iterrows():
    #if the observation is a new event
    if row["new_event"]==True:
        event_location = row["location"]
        event_details = row["Events"]
        #if the event column does not end with a ")", it means we have untidy data in that cell
        if event_details!=")":
            #so, split the event details on the line break character
            event_details_split = event_details.split("_x000D_")
            #join all the split characters except the first
            event_extract = ' '.join(event_details_split[1:])
            #assign the event extract to the event location
            events_dict[event_details_split[0]] = event_extract
        true_count+=1
    #if observation is not a new event, append it details to the new event preceeding it
    else:
        events_dict[event_location] += str(row["Events"]) + " "
        false_count+=1
print(true_count); print(false_count)
del(true_count); del(false_count)

#Transform the data to dataframe
data = pd.DataFrame.from_dict(dict(events_dict), orient="index", columns=["details"])
    
#Define the functions needed to extract the data from the event details
def depunctuate(text):
    #First, clean within text by removing all punctuations
    text_no_punc = re.findall(r"[^!,;^'()?-]", text)
    text_clean = ''.join(text_no_punc)
    text_clean_lower = text_clean.lower()
    return text_clean_lower  

def fully_depunctuate(text):
    text_no_punc = re.findall(r"[^!,;:.^'()?-]", text)
    text_clean = ''.join(text_no_punc)
    text_clean_lower = text_clean.lower()
    return text_clean_lower 

def extract_date(text):
    date = re.search(r'\s(\w+)\s(\d+),\s(\d{4})', text).group() if re.search(r'\s(\w+)\s(\d+),\s(\d{4})', text) else ""
    date = date.strip(' ')
    return date

def extract_time(text):
    time = re.search(r'(\d+):(\d{2})(\s\w\.\w)', text).group() if re.search(r'(\d+):(\d{2})(\s\w\.\w)', text) else ""
    return time

def extract_age(text):
    age=re.search(r',\s\d{2},', text).group() if re.search(r',\s\d{2},', text) else ""
    age = age.strip(',').strip(' ')
    return age
    
def casualties(text):
    #Input must be depunctuated
    try:
        sentences = text.split('.')
        target_list = list(filter(lambda x: (("killed" in x) & ("wounded" in x)), sentences))
        if len(target_list) == 0:
            num_killed=num_injd=np.nan
        else:
            target_sentence = target_list[0]
            sent_no_punc = fully_depunctuate(target_sentence)
            sent_no_punc = sent_no_punc.lower()      
            word_split = sent_no_punc.split(' ')
            word_split = [x.strip(' ') for x in word_split]
            k_idx = word_split.index("killed")
            w_idx = word_split.index("wounded")
            num_killed = word_split[k_idx-3] if word_split[k_idx-3]!="no" else ' '.join(word_split[k_idx-3:k_idx-1])
            num_injd = word_split[w_idx-2] if word_split[w_idx-3]!="no" else ' '.join(word_split[w_idx-3:w_idx-1])
        return (num_killed, num_injd)
    except:
        return ("an error occured", "an error occured")

#states = pd.read_clipboard()  
#states = states.assign(name_2 = lambda x: x['Name'].str.strip(' ').str.lower())   
states = ['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 'delaware', 'florida', 
          'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 
          'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 
          'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohio', 'oklahoma', 
          'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 
          'vermont', 'virginia', 'washington', 'west virginia', 'wisconsin', 'wyoming', 'd.c.']
def extract_state(text):
    #Input must be depunctuated
    for x in states:
        if x in text:
            start_idx = text.index(x)
            end_idx = start_idx + len(x)
            result = text[start_idx:end_idx]
            return result
        
def extract_hgun(text):
    #Input must be fully depunctuated
    split_text = text.split(' ')
    if "handgun" in split_text or "hand gun" in split_text:
        return "one"
    elif "handguns" in split_text:
        hgun_idx = split_text.index("handguns")
        return split_text[hgun_idx-1]
    elif "hand guns" in split_text:
        hgun_idx = split_text.index("hand guns")
        return split_text[hgun_idx-1]
    
def extract_sgun(text):
    #Input must be fully depunctuated
    split_text = text.split(' ')
    if "shotgun" in split_text or "shot gun" in split_text:
        return "one"
    elif "shotguns" in split_text:
        sgun_idx = split_text.index("shotguns")
        return split_text[sgun_idx-1]
    elif "shot guns" in split_text:
        sgun_idx = split_text.index("shot guns")
        return split_text[sgun_idx-1]

def extract_rifle(text):
    #Input must be fully depunctuated
    split_text = text.split(' ')
    if "rifle" in split_text:
        return "one"
    elif "rifles" in split_text:
        r_idx = split_text.index("rifles")
        return split_text[r_idx-1]
    
def extract_loctype(text):
    possible_options = ["(Commerce)", "(Education)", "(Government)", "(Open Space)",
                        "(Residences)", "(Health Care)", "(House of Worship)"]
    for x in possible_options:
        if x in text:
            return x.strip(')').strip('(')
        continue

def resolution(text):
    sentences = text.split('.')
    for sentence in sentences:
        if ("restrained" in text) or ("wrestled" in text):
            return "restrained/killed by civilian(s) before police arrived"
            continue
        elif ("suicide" in text):
            return "comitted suicide"
            continue
        elif ("shot" in text) & ("self" in text):
            return "comitted suicide"
            continue
        elif ("surrendered" in text) or ("apprehended" in text) or ("custody" in text) or ("arrested" in text):
            return "arrested by police"
            continue
        elif ("killed" in text) & ("gunfire" in text) & ("police" in text):
            return "shot by police"
            continue
        elif ("killed" in text) & ("by" in text) & ("police" in text):
            return "shot by police"
            continue
        elif ("killed" in text) & ("by" in text) & ("officer" in text):
            return "shot by police"
            continue
        elif ("wounded" in text) & ("gunfire" in text) & ("police" in text):
            return "shot by police"
            continue
        elif ("at large" in text):
            return "remained at large"
            continue

        
#Apply the function to the dataframe    
for idx,row in data.iterrows():
    text = row['details']
    depunc_text = depunctuate(text)
    no_punc_text = fully_depunctuate(text)
    num_killed, num_injd = casualties(depunc_text)
    data.loc[idx,'time_of_day'] = extract_time(text)
    data.loc[idx,'date'] = extract_date(text)
    data.loc[idx,'shooter_age'] = extract_age(text)
    data.loc[idx, 'num_killed'] = num_killed
    data.loc[idx, 'num_injd'] = num_injd
    data.loc[idx, 'state'] = extract_state(depunc_text)
    data.loc[idx, 'handgun'] = extract_hgun(no_punc_text)
    data.loc[idx, 'shotgun'] = extract_sgun(no_punc_text)
    data.loc[idx, 'rifle'] = extract_rifle(no_punc_text)
    data.loc[idx, 'loctype'] = extract_loctype(idx)
    data.loc[idx, 'shooter_sex'] = "female" if "female" in no_punc_text else np.nan
    data.loc[idx, 'multi_shooter'] = True if "shooters" in no_punc_text else False
    data.loc[idx, 'resolution'] = resolution(depunc_text)
    if "no one was killed or wounded" in depunc_text:
        data.loc[idx, 'num_injd'] = "no one"

#Manual corrections
data.loc['Taft Union High School (Education)', 'resolution'] = "restrained/killed by civilian(s) before police arrived"
data.loc['Tom Bradley International Terminal at Los Angeles International Airport (Government)', 'shooter_age'] = 41
data.loc['Burger King and Huddle House (Commerce)', 'shooter_sex'] = "unidentified shooter"
data.loc['Club LT Tranz (Commerce)', 'shooter_sex'] = "unidentified shooter"
data.loc['Washington, D.C. Department of Public Works (Government)', 'shooter_sex'] = "unidentified shooter"
data.loc['Washington, D.C. Department of Public Works (Government)', 'state'] = "d.c."
data.loc['Sparks Middle School (Education)', 'num_injd'] = "two"
data.loc['Coffee and Geneva Counties, Alabama (Open Space)', 'num_injd'] = "one"
data.loc['Am-Pac Tire Pros (Commerce)', 'num_injd'] = "two"
data.loc['Am-Pac Tire Pros (Commerce)', 'num_killed'] = "one"
data.loc['St. Vincent’s Hospital (Health Care)', 'num_injd'] = "three"
data.loc['St. Vincent’s Hospital (Health Care)', 'num_killed'] = "no one"
data.loc['Pinewood Village Apartments (Residences)', 'num_injd'] = "no one"
data.loc['Pinewood Village Apartments (Residences)', 'num_killed'] = "four"
data.loc['Millard South High School (Education)', 'num_injd'] = "one"
data.loc['Millard South High School (Education)', 'num_killed'] = "one"
data.loc['Gold Leaf Nursery (Commerce)', 'num_injd'] = "no one"
data.loc['Gold Leaf Nursery (Commerce)', 'num_killed'] = "three"
data.loc['Campbell County Comprehensive High School (Education)', 'num_injd'] = "two"
data.loc['Campbell County Comprehensive High School (Education)', 'num_killed'] = "one"
data.loc['Essex Elementary School and Two Residences (Education)', 'num_injd'] = "two"
data.loc['Essex Elementary School and Two Residences (Education)', 'num_killed'] = "two"
data.loc['Essex Elementary School and Two Residences (Education)', 'resolution'] = "arrested by police"
data.loc['Family Dental Care (Commerce)', 'num_killed'] = "one"
data.loc['Legacy Metrolab (Commerce)', 'num_killed'] = "one"
data.loc['International House of Pancakes (Commerce)', 'num_killed'] = "four"
data.loc['International House of Pancakes (Commerce)', 'num_injd'] = "seven"
data.loc['Laidlaw Transit Services Maintenance Yard (Commerce)', 'num_killed'] = "one"
data.loc['Lockheed Martin Subassembly Plant (Commerce)', 'num_killed'] = "six"
data.loc['Forza Coffee Shop (Commerce)', 'num_killed'] = "four"
data.loc['Sandy Hook Elementary School and Residence (Education)', 'num_killed'] = "27"
data.loc['Sandy Hook Elementary School and Residence (Education)', 'num_injd'] = "two"
data.loc['Los Angeles International Airport (Government)', 'num_killed'] = "one"
data.loc['Los Angeles International Airport (Government)', 'num_injd'] = "three"
data.loc['Player’s Bar and Grill (Commerce)', 'resolution'] = "restrained/killed by civilian(s) before police arrived"
data.loc['Red Lion Junior High School (Education)', 'num_killed'] = "one"
data.loc['Red Lion Junior High School (Education)', 'num_injd'] = "no one"
data.loc['Liberty Transportation (Commerce)', 'num_killed'] = "two"
data.loc['Liberty Transportation (Commerce)', 'num_injd'] = "no one"
data.loc['Azana Day Salon (Commerce)', 'num_killed'] = "three"
data.loc['Tom Bradley International Terminal at Los Angeles International Airport (Government)', 'resolution'] = "restrained/killed by civilian(s) before police arrived"
data.loc['Memorial Middle School (Education)', 'resolution'] = "restrained/killed by civilian(s) before police arrived"
data.loc['Memorial Middle School (Education)', 'num_injd'] = "no one"
data.loc['Inskip Elementary School (Education)', 'num_injd'] = "two"
data.loc['Las Dominicanas M&M Hair Salon (Commerce)', 'num_injd'] = "one"
data.loc['Copley Township Neighborhood, Ohio (Residences)', 'num_injd'] = "one"
data.loc['Rocori High School (Education)', 'resolution'] = "restrained/killed by civilian(s) before police arrived"
data.loc['Lloyd D. George U.S. Courthouse and Federal Building (Government)', 'num_injd'] = "one"
data.loc['The Pentagon (Government)', 'num_injd'] = "two"
data.loc['Middletown City Court (Government)', 'num_injd'] = "one"
data.loc['Frankstown Township, Pennsylvania (Open Space)', 'num_injd'] = "three"
data.loc['Albuquerque, New Mexico (Open Space)', 'num_injd'] = "four"
data.loc['Columbia High School (Education)', 'num_injd'] = "one"
data.loc['Best Buy in Hudson Valley Mall (Commerce)', 'num_injd'] = "two"
data.loc['Tacoma Mall (Commerce)', 'num_injd'] = "six"
data.loc['Deer Creek Middle School (Education)', 'num_injd'] = "two"
data.loc['Blue Sky Carnival (Open Space)', 'num_injd'] = "one"
data.loc['AT&T Cellular (Commerce)', 'num_injd'] = "one"
data.loc['Crawford County Courthouse (Government)', 'num_injd'] = "one"
data.loc['Copper Top Bar (Commerce)', 'num_injd'] = "eighteen"
data.loc['Perry Hall High School (Education)', 'num_injd'] = "one"
data.loc['Taft Union High School (Education)', 'num_injd'] = "two"
data.loc['Red Lake High School and Residence (Education)', 'num_injd'] = "six"
data.loc['Tacoma Mall (Commerce)', 'num_injd'] = "six"
data.loc['United States Holocaust Memorial Museum (Government)', 'state'] = "d.c."
data.loc['Washington Navy Yard Building 197 (Government)', 'state'] = "d.c."
data.loc['Red Lion Junior High School (Education)', 'state'] = "pennsylvania"
data.loc['Living Church of God (House of Worship)', 'state'] = "wisconsin"
data.loc['Tacoma Mall (Commerce)', 'state'] = "washington"
data.loc['Forza Coffee Shop (Commerce)', 'state'] = "washington"
data.loc['Los Angeles International Airport (Government)', 'state'] = "california"
data.loc['Multiple Locations in Owosso, Michigan (Open Space)', 'handgun'] = "three"
data.loc['Shelby Center, University of Alabama (Education)', 'handgun'] = "one"
data.loc['Accent Signage Systems (Commerce)', 'handgun'] = "one"
data.loc['House Party in South Jamaica, New York (Residences)', 'handgun'] = "one"
data.loc['Edgewater Technology, Inc. (Commerce)','shotgun'] = "one"
data.loc['Amko Trading Store (Commerce)','shotgun'] = None
data.loc['Sparks Middle School (Education)', 'num_killed'] = "one"
data.loc['Virginia Polytechnic Institute and State University (Education)', 'num_killed'] = 32
data.loc['Kelly Elementary School (Education)', 'num_injd'] = "two"
data.loc['Youth with a Mission Training Center/New Life Church (House of Worship)', 'num_injd'] = "five"
data.loc['Youth with a Mission Training Center/New Life Church (House of Worship)', 'num_killed'] = "four"

from word2number import w2n

for idx,row in data.iterrows():
    #data.loc[idx,'handgun_n']=w2n.word_to_num(row.handgun) if row.handgun!=None else 0
    #data.loc[idx,'shotgun_n']=w2n.word_to_num(row.shotgun) if row.shotgun!=None else 0
    #data.loc[idx,'rifle_n']=w2n.word_to_num(row.rifle) if row.rifle!=None else 0
    try: 
        data.loc[idx,'deaths_n']=0 if row.num_killed=="no one" else w2n.word_to_num(row.num_killed)
    except:
        data.loc[idx,'deaths_n']=row.num_killed
    try: 
        data.loc[idx,'wounded_n']=0 if row.num_injd=="no one" else w2n.word_to_num(row.num_injd)
    except:
        data.loc[idx,'wounded_n']=row.num_injd
        
print(data.wounded_n.sum())
print(data.deaths_n.sum())

data.to_excel("shooter_data_cleaned.xlsx", index=True, index_label="Event_header")
#Auxiliary commands
#data.to_clipboard() 
