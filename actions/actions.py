# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import random
from pymongo import MongoClient
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from bs4 import BeautifulSoup
import requests
import string 
import json
import datetime 
import pytz
from dateutil.relativedelta import relativedelta
import calendar
import re
import datetime

# get database
def get_database():
 
   # Provide the mongodb atlas url to connect python to mongodb using pymongo
   CONNECTION_STRING = "mongodb+srv://kudo313:kudo_321@cluster1.mza5o.mongodb.net/?retryWrites=true&w=majority"
 
   # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
   client = MongoClient(CONNECTION_STRING)
 
   # Create the database for our example (we will use the same database throughout the tutorial
   return client['rasa']
  
dbname = get_database()
ask_infor = [None]

# datetime parser

# REGEX
REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"
REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])"
REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])([-\/:|](2[0-1][0-9][0-9]))"

def regex_date(msg, timezone="Asia/Ho_Chi_Minh"):
    ''' use regex to capture date string format '''

    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz)

    date_str = []
    regex = REGEX_DATE
    regex_day_month = REGEX_DAY_MONTH
    regex_month_year = REGEX_MONTH_YEAR
    pattern = re.compile("(%s|%s|%s)" % (
        regex, regex_month_year, regex_day_month), re.UNICODE)

    matches = pattern.finditer(msg)
    for match in matches:
        _dt = match.group(0)
        _dt = _dt.replace("/", "-").replace("|", "-").replace(":", "-")
        for i in range(len(_dt.split("-"))):
            if len(_dt.split("-")[i]) == 1:
                _dt = _dt.replace(_dt.split("-")[i], "0"+_dt.split("-")[i])
        if len(_dt.split("-")) == 2:
            pos1 = _dt.split("-")[0]
            pos2 = _dt.split("-")[1]
            if 0 < int(pos1) < 32 and 0 < int(pos2) < 13:
                _dt = pos1+"-"+pos2+"-"+str(now.year)
        date_str.append(_dt)
    return date_str


def preprocess_msg(msg):
    ''' return a list of character of messenger without punctuation'''
    msg = msg.lower()
    # rm punctuation
    special_punc = string.punctuation
    for punc in "-+/:|":
        special_punc = special_punc.replace(punc, '')
    msg = ''.join(c for c in msg if c not in special_punc)
    return msg.split()

def remove_token(words, token):
    delete_words = token.split(" ")
    for i in delete_words:
        words.remove(i)
    return words

with open("synonyms.json", "r") as file:
    data = json.load(file)

number_str = {"hai": "2", "ba": "3", "tư": "4"}
def tokenize(msg):
    ''' extract date in messenger by matching in synonyms.json '''

    words = preprocess_msg(msg)
    tokens = []
    n_grams = (8, 7, 6, 5, 4, 3, 2, 1)
    i = 0
    while i < len(words):
        has_gram = False
        token = None
        for n_gram in n_grams:
            token = ' '.join(words[i:i + n_gram])
            if token in data:
                w = words[i-1] if i > 0 else ''
                W = words[i+n_gram] if i < len(words) - n_gram else ''
                #i += n_gram
                has_gram = True
                break
        if has_gram is False:
            token = words[i]
            i += 1
        if token in data:
            if data[token] in ["daysago", "nextday", "lastweek", "nextweek", "lastmonth", "nextmonth", "lastyear", "nextyear"]:
                if w in number_str.keys():
                    tokens.append({data[token]: number_str[w] + " " + token})
                    words.remove(w)
                elif w.isnumeric():
                    tokens.append({data[token]: w + " " + token})
                    words.remove(w)
                else:
                    tokens.append({data[token]: token})
                words = remove_token(words=words, token=token)
                continue
            if data[token] in ["week", "year"]:
                if W in number_str.keys():
                    tokens.append({data[token]: token + " " + number_str[W]})
                    words.remove(W)
                elif W.isnumeric():
                    tokens.append({data[token]: token + " " + W})
                    words.remove(W)
                else:
                    tokens.append({data[token]: token})
                words = remove_token(words=words, token=token)
                continue
            tokens.append({data[token]: token})
            words = remove_token(words=words, token=token)
    return tokens


def get_date(tokens, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    dates = []

    for token in tokens:
        tok_key = list(token.keys())[0]
        tok_value = list(token.values())[0]
        date = now
        if tok_key == "beforeyesterday":
            date = now + datetime.timedelta(days=-2)
        if tok_key == "aftertomorrow":
            date = now + datetime.timedelta(days=2)
        if tok_key == "daysago":
            if tok_value.split()[0].isnumeric():
                num_days = -int(tok_value.split()[0])
                date = now + datetime.timedelta(days=num_days)
            else:
                date = now + datetime.timedelta(days=(-1))
        if tok_key == "nextday":
            if tok_value.split()[0].isnumeric():
                num_days = int(tok_value.split()[0])
                date = now + datetime.timedelta(days=num_days)
            else:
                date = now + datetime.timedelta(days=(1))
        dates.append(date.strftime("%d-%m-%Y"))
    return dates

def get_weekday_week(tokens, week_now, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    weekday_now = now.weekday() + 2
    weekday_weeks = []
    week_day = 0
    for i in range(0, len(tokens)):
        tok_key = list(tokens[i].keys())[0]
        tok_value = list(tokens[i].values())[0]
        num_week = 0
        if "weekday" in tok_key:
            week_day = int(tok_key.split("weekday")[1])
            for j in range(i+1, len(tokens)):
                week_tok_key = list(tokens[j].keys())[0]
                week_tok_value = list(tokens[j].values())[0]
                if week_tok_key == "week":
                    week = int(week_tok_value.split()[-1])
                    num_week = week - week_now
                    break
                if week_tok_key == "nextweek":
                    if week_tok_value.split()[0].isnumeric():
                        num_week = int(week_tok_value.split()[0])
                    else:
                        num_week = 1
                    break
                if week_tok_key == "lastweek":
                    if week_tok_value.split()[0].isnumeric():
                        num_week = -int(week_tok_value.split()[0])
                    else:
                        num_week = -1
                    break
                if week_tok_key == "thisweek":
                    num_week = 0
                    break
            date = now + \
                datetime.timedelta(weeks=num_week) + \
                datetime.timedelta(days=week_day-weekday_now)
            weekday_weeks.append(date.strftime("%d-%m-%Y"))

        else:
            if tok_key == "week":
                week = int(tok_value.split()[-1])
                num_week = week - week_now
            if tok_key == "nextweek":
                if tok_value.split()[0].isnumeric():
                    num_week = int(tok_value.split()[0])
                else:
                    num_week = 1
            if tok_key == "lastweek":
                if tok_value.split()[0].isnumeric():
                    num_week = -int(tok_value.split()[0])
                else:
                    num_week = -1
            if tok_key == "thisweek":
                num_week = 0
            if week_day == 0:
                week = [(now + datetime.timedelta(weeks=num_week) + datetime.timedelta(days=2-weekday_now)).strftime("%d-%m-%Y"),
                        (now + datetime.timedelta(weeks=num_week) + datetime.timedelta(days=8-weekday_now)).strftime("%d-%m-%Y")]
                weekday_weeks.append(week)
            else:
                date = now + \
                    datetime.timedelta(weeks=num_week) + \
                    datetime.timedelta(days=week_day-weekday_now)
                weekday_weeks.append(date.strftime("%d-%m-%Y"))

    return weekday_weeks

def get_day_month_year(tokens, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    day_month_years = []
    for i in range(0, len(tokens)):
        day_tok_key = list(tokens[i].keys())[0]
        day_tok_value = list(tokens[i].values())[0]
        if "day" in day_tok_key or day_tok_key == "endmonth":
            day = int(day_tok_key.split("day")[1])
            if day_tok_key == "endmonth":
                day = calendar.monthrange(now.year, now.month)[1]
            month = now.month
            year = now.year
            for j in range(i+1, len(tokens)):
                month_tok_key = list(tokens[j].keys())[0]
                month_tok_value = list(tokens[j].values())[0]
                if "month" in month_tok_key and month_tok_key != "endmonth":
                    if month_tok_key.startswith("month"):
                        month = int(month_tok_key.split("month")[1])
                        for k in range(j+1, len(tokens)):
                            year_tok_key = list(tokens[k].keys())[0]
                            year_tok_value = list(tokens[k].values())[0]
                            if "year" in year_tok_key:
                                if year_tok_key == "year":
                                    year = int(year_tok_value.split()[-1])
                                    break
                                if year_tok_key == "nextyear":
                                    if year_tok_value.split()[0].isnumeric():
                                        num_year = int(
                                            year_tok_value.split()[0])
                                        year = (
                                            now + relativedelta(years=num_year)).year
                                    else:
                                        year = now.year + 1
                                    break
                                if year_tok_key == "lastyear":
                                    if year_tok_value.split()[0].isnumeric():
                                        num_year = - \
                                            int(year_tok_value.split()[0])
                                        year = (
                                            now + relativedelta(years=num_year)).year
                                    else:
                                        year = now.year - 1
                                    break
                        break
                    if month_tok_key == "nextmonth":
                        if month_tok_value.split()[0].isnumeric():
                            num_month = int(month_tok_value.split()[0])
                            month = (
                                now + relativedelta(months=num_month)).month
                            year = (now + relativedelta(months=num_month)).year
                        else:
                            month = now.month + 1
                        break
                    if month_tok_key == "lastmonth":
                        if month_tok_value.split()[0].isnumeric():
                            num_month = -int(month_tok_value.split()[0])
                            month = (
                                now + relativedelta(months=num_month)).month
                            year = (now + relativedelta(months=num_month)).year
                        else:
                            month = now.month - 1
                        break
            date = datetime.date(int(year), int(month), int(day))
            day_month_years.append(date.strftime("%d-%m-%Y"))
    return day_month_years

def get_month_year(tokens, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    day_month_years = []
    for i in range(0, len(tokens)):
        tok_key = list(tokens[i].keys())[0]
        tok_value = list(tokens[i].values())[0]
        if "month" in tok_key:
            month_num = int(tok_key.split("month")[1])
            year = now.year
            for k in range(i+1, len(tokens)):
                year_tok_key = list(tokens[k].keys())[0]
                year_tok_value = list(tokens[k].values())[0]
                if "year" in year_tok_key:
                    if year_tok_key == "year":
                        year = int(year_tok_value.split()[-1])
                        break
                    if year_tok_key == "nextyear":
                        if year_tok_value.split()[0].isnumeric():
                            num_year = int(
                                year_tok_value.split()[0])
                            year = (
                                now + relativedelta(years=num_year)).year
                        else:
                            year = now.year + 1
                        break
                    if year_tok_key == "lastyear":
                        if year_tok_value.split()[0].isnumeric():
                            num_year = - \
                                int(year_tok_value.split()[0])
                            year = (
                                now + relativedelta(years=num_year)).year
                        else:
                            year = now.year - 1
                        break
                    break
            first_date = datetime.date(int(year), month_num, day = 1)
            lastday = calendar.monthrange(year, month_num)[1]
            last_date = datetime.date(int(year), month_num, day = lastday)
            day_month_years.append(first_date.strftime("%d-%m-%Y"))
            day_month_years.append(last_date.strftime("%d-%m-%Y"))
    return day_month_years

def tokens_classification(tokens):
    for token in tokens:
        tok_key = list(token.keys())[0]
        if tok_key in ["daysago", "beforeyesterday"]:
            return "get_date"
        elif "weekday" in tok_key or tok_key in ["lastweek", "thisweek"]:
            return "get_weekday"
        elif "day" in tok_key or tok_key == "endmonth":
            return "get_day_month_year"
        elif "month" in tok_key:
            return "get_month_year"
        else:
            return None
    pass

def summary_date(message):
    dates =  regex_date(message)
    tokens = tokenize(message)
    tokens_class = tokens_classification(tokens)
    if tokens_class == "get_date":
        dates = get_date(tokens)
    elif tokens_class == "get_weekday":
        dates = get_weekday_week(tokens, week_now= 36)
    elif tokens_class == "get_day_month_year":
        dates = get_day_month_year(tokens)
    elif tokens_class == "get_month_year":
        dates = get_month_year(tokens)
    return unique(dates)

def unique(list1):
    # initialize a null list
    unique_list = []
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    # print list
    return unique_list

class ActionRecommend(Action):

    def name(self) -> Text:
        return "action_recommend"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        
        collection_name = dbname["test_do_an"]
        items = collection_name.find()
        list_food = []
        for item in items:
        # This does not give a very readable output
            list_food.append(item['mon_an'])
        
        food = []   
        for i in range(2):
            food_number = random.randrange(len(list_food))
            food.append(list_food[food_number])

        dispatcher.utter_message(
            text="Em nghĩ hôm nay anh chị có thể thử món '{}' hoặc bên cạnh đó cũng có thể là món '{}' ạ".format(food[0], food[1]))

        return []

class GetName(Action):
    def name(self) -> Text:
        return "get_name"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ask_infor[0] = next(tracker.get_latest_entity_values("position"), None)
        if ask_infor[0]  != None:
            ask_infor[0]  = "position"
        else:
            ask_infor[0]  = next(tracker.get_latest_entity_values("department"), None)
            if ask_infor[0]  != None:
                ask_infor[0]  = "department"
        dispatcher.utter_message(
            text = "Anh chị có thể cho em xin tên của mình được không ạ")                
        print(ask_infor[0])

        return []

class GetInfor(Action):
    def name(self) -> Text:
        return "get_infor"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name =  next(tracker.get_latest_entity_values("name_person"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        print(ask_infor[0] )
        if name != None:
            for item in items:
                ten_nv = item['ten_nv'].lower()
                name = name.lower()
                if name in ten_nv:
                    if ask_infor[0]  == "department":
                        dispatcher.utter_message(
                        text = "Trung tâm của anh chị bên " + item['trung_tam'])
                    elif ask_infor[0] == "position":
                        dispatcher.utter_message(
                            text = "Vị trí của anh/chị là " + item['chuc_vu'])
                    else:
                        dispatcher.utter_message(
                        text = "Xin lỗi em không thể tìm thấy thông tin của anh/chị")
                    break
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em không phân biệt được tên anh chị")
        return []

class AnsIndiInfor(Action):
    def name(self) -> Text:
        return "ans_indi_infor"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name = next(tracker.get_latest_entity_values("name_person"), None)
        ques = next(tracker.get_latest_entity_values("indi_ques"), None)
        pronous = next(tracker.get_latest_entity_values("pronouns"), "bạn")
        if pronous == "bạn":
            bot_pronous = "mình"
        else:
            bot_pronous = "em"
        collection_name = dbname["company"]
        items = collection_name.find()
        print(ques)
        print(name)
        print(pronous)
        if name != None:
            for item in items:
                ten_nv = item['ten_nv'].lower()
                name = name.lower()
                
                if name in ten_nv:
                    if ques != None:
                        ques = ques.lower()
                        if ques == "trung tâm":
                            dispatcher.utter_message(
                            text = "Trung tâm của {} bên ".format(pronous) + item['trung_tam'])
                        elif ques == "vị trí":
                            dispatcher.utter_message(
                                text = "Vị trí của {} là ".format(pronous) + item['chuc_vu'])
                        elif ques == "thông tin":
                            dispatcher.utter_message(
                                text = "Vị trí của {} là ".format(pronous) + item['chuc_vu'] + " bên trung tâm " + item['trung_tam'])
                        else:
                            dispatcher.utter_message(
                            text = "Xin lỗi {0} không thể tìm thấy thông tin của {1}".format(bot_pronous, pronous))
                        break
                    else:
                        dispatcher.utter_message(
                            text = "Xin lỗi, nhưng {0} chưa hiểu câu hỏi của {1}".format(bot_pronous, pronous))
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng {0} không phân biệt được tên {1}".format(bot_pronous, pronous))
        return []

class AnsListEmploy(Action):
    def name(self) -> Text:
        return "ans_list_employ"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name_department = next(tracker.get_latest_entity_values("name_department"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        list_employ = ""
        print(name_department)
        print(name_position)
        if name_department != None and name_position != None:
            for item in items:
                department = item['trung_tam'].lower()
                name_department = name_department.lower()
                position = item['chuc_vu'].lower()
                name_position = name_position.lower()
                if name_position != "thành viên":
                    if name_department in department and name_position in position:
                        list_employ += item['ten_nv'] + "\n"
                else:
                    if name_department in department :
                        list_employ += item['ten_nv'] + "\n"
            if list_employ == "":
                dispatcher.utter_message(
                    text = "Hiện tại không có nhân viên nào ở vị trí này")
            else:
                list_employ = "Danh sách " + name_position + " bên " + name_department + " hiện tại: \n" + list_employ
                dispatcher.utter_message(
                    text = list_employ)
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em chưa hiểu câu hỏi của anh chị")
        return []    

class AnsNumEmploy(Action):
    def name(self) -> Text:
        return "ans_number_employ"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name_department = next(tracker.get_latest_entity_values("name_department"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        number = 0
        print(name_department)
        print(name_position)
        if name_department != None and name_position != None:
            for item in items:
                department = item['trung_tam'].lower()
                name_department = name_department.lower()
                position = item['chuc_vu'].lower()
                name_position = name_position.lower()
                if name_position != "thành viên":
                    if name_department in department and name_position in position:
                        number +=1 
                else:
                    if name_department in department :
                        number += 1
            if number == 0:
                dispatcher.utter_message(
                    text = "Hiện tại không có nhân viên nào ở vị trí này")
            else:
                list_employ = "Có tổng "+ str(number) + " " + name_position + " bên " + name_department + " hiện tại \n"
                dispatcher.utter_message(
                    text = list_employ)
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em chưa hiểu câu hỏi của anh chị")
        return []

class AnsForJob(Action):
    def name(self) -> Text:
        return "ans_for_job"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        url = 'https://careers.rikai.technology/tuyen-dung'
        # page = urllib.request.urlopen(url, context=context)
        page = requests.get(url, verify=False)
        soup = BeautifulSoup(page.text, 'html.parser')
        all_jobs = {}
        all_jobs_text = ""
        for n in range(len(soup.find_all(class_='page5sl-text',))):
            jobs = soup.find_all(class_='page5sl-text',)[n]
            name_job = jobs.find_all('a', href=True)[0].decode_contents()
            link_jd = jobs.find_all('a', href=True)[0]['href']
            num = jobs.find_all(class_="xanh")[0].decode_contents()
            all_jobs[name_job] = {'num':num, 'link_jd':link_jd}
            all_jobs_text += name_job + ":" + "\n" + num + "\n" + "Link JD: " + link_jd + "\n"
        name_job = next(tracker.get_latest_entity_values("name_job"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        print(name_job)
        print(name_position)
        if name_job != None or name_position != None:
            if name_job == None:
                name_job = name_position
            name_job = name_job.lower()
            found = False
            for name_job_data in all_jobs.keys():
                name_job_data_lower = name_job_data.lower()
            
                if fuzz.partial_ratio(name_job_data_lower, name_job) > 80:
                    text = ("Hiện công ty đang tuyển vị trí: " + name_job_data + "\n" + all_jobs[name_job_data]['num']
                            + "\n" + "Link JD: " + all_jobs[name_job_data]['link_jd'])
                    
                    dispatcher.utter_message(
                        text = text)
                    found = True
                    break
        
            if found == False:
                dispatcher.utter_message(
                        text = "Hiện bên mình không còn tuyển vị trí này nữa")

        else:
            dispatcher.utter_message(
                text = "Hiện bên mình đang tuyển các vị trí sau:\n " + all_jobs_text)
        return []    

class AnsForNews(Action):
    def name(self) -> Text:
        return "ans_for_news"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        url = 'https://careers.rikai.technology/tin-tuc'
        # page = urllib.request.urlopen(url, context=context)
        page = requests.get(url, verify=False)
        soup = BeautifulSoup(page.text, 'html.parser')
        all_news = {}

        list_news = soup.find_all(class_='blog-hot__item_text')
        all_news = {}
        for n in range(len(list_news)):
            news = list_news[n]
            date = news.find(class_='time-view',).decode_contents()
            date = datetime.datetime.strptime(date, '%d/%m/%Y')
            title = news.find('a', href=True)['title']
            link = news.find('a', href=True)['href']
            all_news[title] = [date, link]
        
        msg = tracker.latest_message['text']
        date_time = summary_date(msg)
        while len(date_time) == 1:
            date_time = date_time[0]
        text_ans_news = "Các tin tức hiện đang có: \n"
        has_news = False
        print(date_time)
        if len(date_time) == 0:
            count = 0
            for news_key in all_news.keys():
                text_ans_news += news_key + ": " + all_news[news_key][1] + "\n"
                has_news = True
                count += 1
                if count > 5:
                    break
        else:
            if isinstance(date_time, list):
                if not isinstance(date_time[0], list):
                    first_date = datetime.datetime.strptime(date_time[0], '%d-%m-%Y')
                    last_date = datetime.datetime.strptime(date_time[1], '%d-%m-%Y')
                    for news_key in all_news.keys():
                        if all_news[news_key][0] > first_date and all_news[news_key][0] < last_date:
                            text_ans_news += news_key + ": " + all_news[news_key][1] + "\n"
                            has_news = True
            else:
                date = datetime.datetime.strptime(date_time, '%d-%m-%Y')
                for news_key in all_news.keys():
                    if all_news[news_key][0] == date:
                        text_ans_news += news_key + ": " + all_news[news_key][1] + "\n"
                        has_news = True
        print(text_ans_news)
        if has_news:
            dispatcher.utter_message(
                text = text_ans_news)
        else:
            dispatcher.utter_message(
                text = "Không có tin tức nào trong thời gian này")

        return []

class Ans_for_department(Action):
    def name(self) -> Text:
        return "ans_for_department"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        collection_name = dbname["company"]
        items = collection_name.find()
        list_department = []
        for item in items:
            department = item['trung_tam'].lower()
            if department not in list_department:
                list_department.append(item['trung_tam'])
        list_department = unique(list_department)
        if len(list_department) > 0:
            text = "Công ty hiện có tổng cộng {} trung tâm: \n".format(len(list_department))
            for department in list_department:
                text += department + "\n"
        else:
            text = "Công ty không có trung tâm nào"
        dispatcher.utter_message(
                text = text)

        return []

class Ans_for_address(Action):
    def name(self) -> Text:
        return "ans_for_address"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(
            text = "Công ty tọa lạc tại 219 phố  Trung Kính, quận Cầu Giấy, thành phố Hà Nội")

        return []

class Ans_for_pr_company(Action):
    def name(self) -> Text:
        return "ans_for_pr_company"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(
            text = "Công ty bên mình là Rikai Mind\n Link Facebook: https://www.facebook.com/RikaiMind")

        return []
