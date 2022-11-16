import string 
import json
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import calendar
import re

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

# def get_week(tokens, timezone='Asia/Ho_Chi_Minh'):
#     tz = pytz.timezone(timezone)
#     now = datetime.datetime.now(tz=tz).date()
#     day_month_years = []
#     for i in range(0, len(tokens)):
#         tok_key = list(tokens[i].keys())[0]
#         tok_value = list(tokens[i].values())[0]
#         if "month" in tok_key:
#             month_num = int(tok_key.split("month")[1])
#             year = now.year
#             for k in range(i+1, len(tokens)):
#                 year_tok_key = list(tokens[k].keys())[0]
#                 year_tok_value = list(tokens[k].values())[0]
#                 if "year" in year_tok_key:
#                     if year_tok_key == "year":
#                         year = int(year_tok_value.split()[-1])
#                         break
#                     if year_tok_key == "nextyear":
#                         if year_tok_value.split()[0].isnumeric():
#                             num_year = int(
#                                 year_tok_value.split()[0])
#                             year = (
#                                 now + relativedelta(years=num_year)).year
#                         else:
#                             year = now.year + 1
#                         break
#                     if year_tok_key == "lastyear":
#                         if year_tok_value.split()[0].isnumeric():
#                             num_year = - \
#                                 int(year_tok_value.split()[0])
#                             year = (
#                                 now + relativedelta(years=num_year)).year
#                         else:
#                             year = now.year - 1
#                         break
#                     break
#             first_date = datetime.date(int(year), month_num, day = 1)
#             lastday = calendar.monthrange(year, month_num)[1]
#             last_date = datetime.date(int(year), month_num, day = lastday)
#             day_month_years.append(first_date.strftime("%d-%m-%Y"))
#             day_month_years.append(last_date.strftime("%d-%m-%Y"))
#     return day_month_years

def tokens_classification(tokens):
    for token in tokens:
        tok_key = list(token.keys())[0]
        if tok_key in ["daysago", "beforeyesterday"]:
            return "get_date"
        elif "weekday" in tok_key or tok_key in ["lastweek"]:
            return "get_weekday"
        elif "day" in tok_key or tok_key == "endmonth":
            return "get_day_month_year"
        elif "month" in tok_key:
            return "get_month_year"
        else:
            return None
    pass

def summary_date(mesage):
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

message = "có tin gì mới trong hôm qua không"
tokens=  (tokenize(message))
print(summary_date(message))
# print(get_month_year(tokens))