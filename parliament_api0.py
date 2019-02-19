# coding: utf-8
import os
path = os.getcwd()
os.chdir(path)
import argparse
import datetime
from dateutil.relativedelta import relativedelta
import calendar
from requesturl import RequestURL
import copy
from time import sleep
from collections import OrderedDict
import re


START_DATE, END_DATE, HOUSES, NEXT_POSITION, MEETING, SPEAKER = \
'START_DATE', 'END_DATE', 'HOUSES', 'NEXT_POSITION', 'MEETING', 'SPEAKER'

#MAXレコーヅ数は仕様上の最大値にする。
MAXIMUM_RECORDS = 'MAXIMUM_RECORDS'
OUTPUT_DIR = './output/%s/%s/'
OUTPUT_FILE = '%s_%s.txt'
RYO_IN = '両院'
SYU_IN = '衆議院'
SAN_IN = '参議院'
HOUSES_TAPPLE = (RYO_IN, SYU_IN, SAN_IN)

NUMBER_OF_RECORDS, NUMBER_OF_RETURN, SPEECH_RECORD, NEXT_RECORD_POSITION = \
'numberOfRecords', 'numberOfReturn', 'speechRecord', 'nextRecordPosition'

SESSION, NAME_OF_HOUSE, NAME_OF_MEETING, ISSUE, \
DATE, SPEECH_ORDER, SPEAKER, SPEECH = \
'session', 'nameOfHouse', 'nameOfMeeting', 'issue', \
'date', 'speechOrder', 'speaker', 'speech'
SPEECH_TAG_TAPPLE = (SESSION, NAME_OF_HOUSE, NAME_OF_MEETING, ISSUE, \
                     DATE, SPEECH_ORDER, SPEAKER, SPEECH
                    )
SPEECH_DELETE_PATTERN = r'^○.+　'

WRITE_CONTENTS_SPEAKER = '発言者:'
WRITE_CONTENTS_MEETING = '会議名:'
WRITE_CONTENTS_ORDER = '発言順'
WRITE_CONTENTS_SPEECH = '発言:'

def makedir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


class SearchHandle:
    def __init__(self, start_date='', end_date='', houses='', meeting='',speaker='', next_position='1'):
        search_dict = {START_DATE:start_date, \
                       END_DATE:end_date, \
                       HOUSES:houses, \
                       NEXT_POSITION:next_position, \
                       MEETING:meeting, \
                       SPEAKER:speaker \
                       }
        self.search_dict = {key:value for key, value in search_dict.items() if value}


    @staticmethod
    def set_datelist(start_date, end_date):
        result_list = []
        start_datetime = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        end_datetime = datetime.datetime.strptime(end_date, '%Y/%m/%d')
        diff = (end_datetime.year - start_datetime.year) * 12 + (end_datetime.month - start_datetime.month)
        for _ in range(0, diff+1):
            _, lastday = calendar.monthrange(start_datetime.year, start_datetime.month)
            month_lastday = datetime.date(start_datetime.year, start_datetime.month, lastday)
            end_month_flag = (start_datetime.year == end_datetime.year) and \
                             (start_datetime.month == end_datetime.month)
            result_start = \
             datetime.datetime(start_datetime.year, start_datetime.month, start_datetime.day).strftime('%Y-%m-%d')
            result_end = \
             datetime.datetime(end_datetime.year, start_datetime.month, end_datetime.day).strftime('%Y-%m-%d') \
             if end_month_flag else \
             datetime.datetime(start_datetime.year, start_datetime.month, lastday).strftime('%Y-%m-%d')
            start_datetime += relativedelta(months=1)
            start_datetime = datetime.datetime(start_datetime.year, start_datetime.month, 1)

            result_list.append([result_start, result_end])

        return result_list


    def return_seacrh_dict(self):
        return_dicts = []
        start_date_flg = START_DATE in self.search_dict
        end_date_flg = END_DATE in self.search_dict
        if start_date_flg or end_date_flg:
            self.search_dict.setdefault(START_DATE, '1900-01-01')
            self.search_dict.setdefault(END_DATE, datetime.date.today().strftime('%Y-%m-%d'))

        date_lists = self.set_datelist(self.search_dict[START_DATE], self.search_dict[END_DATE])
        for date_list in date_lists:
            return_dict = {}
            return_dict = {key:value for key, value in self.search_dict.items() if not key in (START_DATE, END_DATE)}
            return_dict[START_DATE], return_dict[END_DATE] = date_list[0], date_list[1]
            if not HOUSES in return_dict:
                for value in  HOUSES_TAPPLE:
                    return_dict[HOUSES] = value
                    return_dicts.append(copy.copy(return_dict))

            else:
                return_dicts.append(copy.copy(return_dict))

        return return_dicts



class CreateRequest(RequestURL):
    #検索条件を受け取る
    START_RECORD_TAG, MAXIMUM_RECORDS_TAG, NAME_OF_HOUSE_TAG, \
    NAME_OF_MEETING_TAG, SPEAKER_TAG, FROM_TAG, UNTIL_TAG  = \
    'startRecord', 'maximumRecords', 'nameOfHouse', \
    'nameOfMeeting', 'speaker', 'from', 'until'\

    SEARCH_TAG_DICT = {START_DATE:FROM_TAG, \
                       END_DATE:UNTIL_TAG, \
                       HOUSES:NAME_OF_HOUSE_TAG, \
                       NEXT_POSITION:START_RECORD_TAG, \
                       MEETING:NAME_OF_MEETING_TAG, \
                       SPEAKER:SPEAKER_TAG, \
                       MAXIMUM_RECORDS:MAXIMUM_RECORDS_TAG \
                       }

    SPEECH_URL = 'http://kokkai.ndl.go.jp/api/1.0/speech?'
    MEETING_URL = 'http://kokkai.ndl.go.jp/api/1.0/meeting?'
    SPEECH_RECORD_NUM = '100'
    MEETING_RECORD_MUN = '5'

    def __init__(self, search_dict, speech_flag=True):
        super(CreateRequest, self).__init__()
        self.search_dict = search_dict
        self.speech_flag = speech_flag


    def geturl(self):
        search_url = ''
        for key, value in self.SEARCH_TAG_DICT.items():
            if (key in self.search_dict) or (key == MAXIMUM_RECORDS):
                search_url = search_url + '&' if search_url != '' else ''
                add_url = value + '='
                if key in self.search_dict:
                    add_url += self.search_dict[key]
                else:
                    add_url = add_url + self.SPEECH_RECORD_NUM if self.speech_flag else add_url + self.MEETING_RECORD_MUN

                search_url += add_url

        search_url = RequestURL.encode_url(search_url)
        search_url = self.SPEECH_URL + search_url if self.speech_flag else self.MEETING_URL + search_url

        return search_url


def reshape_speech_dict(child):
    key = child.nodeName
    try:
        value = child.childNodes[0].data
        if key in (SESSION, DATE, SPEECH_ORDER):
            if key == DATE:
                value = value.replace('-', '')
                value = int(value)
            elif key == SPEECH:
                value = re.sub(SPEECH_DELETE_PATTERN, ' ', value)
    except IndexError:
        key, value = None, None

    return key, value


def create_speech_nodes(speech_nodes):
    speech_dicts = []
    for speech_node in speech_nodes:
        speech_dict = OrderedDict()
        for child in speech_node.childNodes:
            if not child.nodeName in SPEECH_TAG_TAPPLE:
                continue

            key, value = reshape_speech_dict(child)
            if not key:
                continue

            speech_dict[key] = value

        speech_dicts.append(copy.copy(speech_dict))

    return speech_dicts


def output_files(speech_dicts):
    speech_dicts.sort(key=lambda x:(int(x.get(SESSION)), \
                                    int(x.get(DATE)), \
                                    x.get(NAME_OF_HOUSE), \
                                    x.get(NAME_OF_MEETING), \
                                    int(x.get(SPEECH_ORDER)) \
                                    ) \
                     )
    for speech_dict in speech_dicts:
        '''
        OrderedDict([('session', '196'), ('nameOfHouse', '参議院'), ('nameOfMeeting', '予算委員会'), ('issue', '2号'), ('date', 20180131), ('speechOrder', '1'), ('speaker', '金子原二郎'), ('speech', '○委員長（金子原二郎君）\u3000ただいまから予算委員会を開会いたします。\n\u3000政府参考人の出席要求に関する件についてお諮りいたします。\n\u3000平成二十九年度補正予算二案審査のため、必要に応じ政府参考人の出席を求めることとし、その手続につきましては、これを委員長に御一任願いたいと存じますが、御異議ございませんか。\n\u3000\u3000\u3000〔「異議なし」と呼ぶ者あり〕\n')])
        '''
        order = speech_dict[SPEECH_ORDER]
        if order == '0' or ( not order):
            continue

        output_dir = OUTPUT_DIR %(speech_dict.get(NAME_OF_HOUSE), speech_dict.get(SESSION))
        meeting = speech_dict.get(NAME_OF_MEETING)
        speaker = speech_dict.get(SPEAKER)
        speech = speech_dict.get(SPEECH)
        order = speech_dict.get(SPEECH_ORDER)
        if not(meeting and speaker and speech):
            continue

        makedir(output_dir)
        output_file_dir = output_dir + (OUTPUT_FILE % (speech_dict.get(DATE), speech_dict.get(NAME_OF_MEETING)))
        with open(output_file_dir, 'a') as f:
            f.write(WRITE_CONTENTS_MEETING + meeting)
            f.write('\n')
            f.write(WRITE_CONTENTS_ORDER + order)
            f.write('\n')
            f.write(WRITE_CONTENTS_SPEAKER + speaker)
            f.write('\n')
            f.write(WRITE_CONTENTS_SPEECH + re.sub(SPEECH_DELETE_PATTERN, '', speech))
            f.write('\n')



def getChildNodesFirstData(nodelist):
    result = nodelist[0].childNodes[0].data if nodelist else ''
    return result

if __name__ == '__main__':
    #parser = argparse.ArgumentParser()
    #parser.add_argument('--session', help='optional')
    sh = SearchHandle(start_date='2018/01/01', end_date='2018/12/31')
    sh_dicts =sh.return_seacrh_dict()
    for sh_dict in sh_dicts:
        next_recos = 'dummy'
        speech_nodes = []
        while next_recos != '':
            cr = CreateRequest(sh_dict, speech_flag=True)
            url = cr.geturl()
            request = cr.get_request(url)
            print(url)
            spe_recos = cr.getElementsByTagName(SPEECH_RECORD)
            num_recos = cr.getElementsByTagName(NUMBER_OF_RECORDS)
            num_retu = cr.getElementsByTagName(NUMBER_OF_RETURN)
            next_recos = cr.getElementsByTagName(NEXT_RECORD_POSITION)
            if not spe_recos:
                break

            num_recos, num_retu, next_recos = getChildNodesFirstData(num_recos), \
                                              getChildNodesFirstData(num_retu), \
                                              getChildNodesFirstData(next_recos)

            speech_nodes.extend(copy.copy(spe_recos))
            sh_dict[NEXT_POSITION] = next_recos

        if len(speech_nodes) > 0:
            speech_dicts = create_speech_nodes(speech_nodes)
            output_files(speech_dicts)
