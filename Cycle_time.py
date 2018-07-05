#!/usr/bin/python
# -*- coding:utf-8 -*-
import codecs
import re
import requests
import json
import urllib
import datetime
import time
from urllib.parse import urlparse
from urllib.parse import urljoin
import numpy as np
import csv
import sys
import os
import configparser

#app_key = 'a35ed2ec958bf34c51b872d58f388860'
#token = 'a2ce7bae3b1c355a2ad5b69c1d2f7baa19f69b09cc77a090e5afb40db94ca5f4'
#Auth_v1_info = 'key=' + app_key + '&token=' + token

URL_head = 'https://api.trello.com'

Board_id = '5a9366442baffb4f2fa3ef6b'
Label_id = '5af3bbd4ada3ab078c4fd295'


API_story_list = '/1/boards/{board_id}/cards?'
API_board_list = '/1/boards/{board_id}/lists?'
API_cards_acts = '/1/cards/{card_id}/actions?'
API_cards_add = '/1/cards/{card_id}/actions?filter=createCard&'
API_board_labels = '/1/boards/{board_id}/labels?'
API_me_boards = '/1/members/me/boards?'

UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

url = ''

Table_head = ['Card_id', 'Card_name']

Card_time = ['Card_id', 'Card_name']


def get_config():
    conf = configparser.ConfigParser()
    conf.read('Cycle_time.conf')
    app_key = conf.get('Auth', 'APP_KEY')
    token = conf.get('Auth', 'TOKEN')
    global Auth_v1_info
    Auth_v1_info = 'key=' + app_key + '&token=' + token
    return(Auth_v1_info)


def get_myboards():
    API_INFO = API_me_boards
    url = URL_head + API_INFO + Auth_v1_info
    respose = requests.get(url)
    body = json.loads(respose.text)
    for i in range(0, len(body)):
        print("%d . %s id is '%s' " %
              (i + 1, body[i]['name'], body[i]['id']))
    return(0)


def get_table_head():
    API_INFO = API_board_list.replace('{board_id}', '5a9366442baffb4f2fa3ef6b')
    url = URL_head + API_INFO + Auth_v1_info
    respose = requests.get(url)
    body = json.loads(respose.text)
    for i in range(0, len(body)):
        Table_head.append(body[i]['name'])
        Card_time.append(0)
    Table_head.append('Exception')
    Card_time.append(0)


def get_board_labels():
    API_INFO = API_board_labels.replace(
        '{board_id}', Board_id)
    url = URL_head + API_INFO + Auth_v1_info
    respose = requests.get(url)
    body = json.loads(respose.text)

    for i in range(0, len(body)):
        print("%d . '%s' id is '%s' " %
              (i + 1, body[i]['name'], body[i]['id']))
    return(0)


def get_card_list():
    API_INFO = API_story_list.replace('{board_id}', Board_id)
    url = URL_head + API_INFO + Auth_v1_info
    Cycle_list = np.array(Table_head)
    respose = requests.get(url)
    body = json.loads(respose.text)
    m = 0
    for i in range(0, len(body)):
        if Label_id in body[i]['idLabels']:
            card_info = Card_time[:]
            card_info[0] = body[i]['id']
            card_info[1] = body[i]['name']
            respose_b = get_cards_acts(body[i]['id'], card_info)
            if (respose_b != 100):
                Cycle_list = np.row_stack((Cycle_list, respose_b))

    csv_file = open('/Users/pengwang/Documents/Trello/data/MVP2.csv',
                    'w', encoding='utf_8_sig')
    writer = csv.writer(csv_file)
    for i in range(0, len(Cycle_list)):
        writer.writerow(Cycle_list[i])


def get_cards_acts(card_id, card_info):
    API_INFO = API_cards_acts.replace('{card_id}', card_id)
    url = URL_head + API_INFO + Auth_v1_info
    respose_b = requests.get(url)
    act_detail = json.loads(respose_b.text)
#    print(act_detail)
    card_move_detail = ['', '', '', '']
    card_move_detail = get_card_create_date(card_id)
    card_move_list = np.array(card_move_detail)
    flag = 0
    for j in range(0, len(act_detail)):
        if ('listAfter' in act_detail[j]['data'].keys() and 'listBefore' in act_detail[j]['data'].keys()):
            flag = 1
            move_date = datetime.datetime.strptime(
                act_detail[j]['date'], UTC_FORMAT)
            card_move_detail = (card_id, act_detail[j]['data']['listAfter']['name'],
                                act_detail[j]['data']['listBefore']['name'], move_date)
            card_move_list = np.row_stack((card_move_list, card_move_detail))

    if flag == 0:
        return(100)

    index = np.lexsort([card_move_list[:, 3]])
    card_move_list_order = card_move_list[index]
    for i in range(1, len(card_move_list_order)):
        duration = (card_move_list_order[i][
                    3] - card_move_list_order[i - 1][3]).days
        if card_move_list_order[i][2] in Table_head:
            position = Table_head.index(card_move_list_order[i][2])
            card_info[position] = card_info[position] + duration
    return(card_info)


def get_card_create_date(card_id):
    API_INFO = API_cards_add.replace('{card_id}', card_id)
    url = URL_head + API_INFO + Auth_v1_info
    respose_b = requests.get(url)
    card_create_detail = ['', '', '', '']
    create_body = json.loads(respose_b.text)
    move_date = datetime.datetime.strptime(create_body[0]['date'], UTC_FORMAT)
    card_create_detail = (card_id, create_body[0]['data']['list'][
                          'name'], 'Create card', move_date)
    return(card_create_detail)


if __name__ == '__main__':

    get_config()

    if len(sys.argv) == 1:
        print('Please input argv')
        os._exit(0)
    if sys.argv[1] == 'boards':
        get_myboards()

    if sys.argv[1] == 'labels':
        get_board_labels()

    if sys.argv[1] == 'start':
        print('Cycle time is start')
        get_table_head()
        get_card_list()
