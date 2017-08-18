"""命令行火车票查看器

Usage:
    tickets [-gdtkz] <from> <to> <date>

Options:
    -h,--help   显示帮助菜单
    -g          高铁
    -d          动车
    -t          特快
    -k          快速
    -z          直达

Example:
    tickets 北京 上海 2016-10-10
    tickets -dg 成都 南京 2016-10-10
"""

from docopt import docopt
from station_code import station_code
from code_station import code_station
from prettytable import PrettyTable
from colorama import init, Fore

import requests
import re

init()


class TrainCollection:

    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 硬座 无座'.split()

    def __init__(self, available_trains, options, code_station):
        """查询到的火车班次集合

        :param available_trains: 一个列表, 包含可获得的火车班次, 每个班次是一个字母都是一个字典

        :param options: 查询的选项, 如高铁, 动车, etc...
        """

        self.available_trains = available_trains
        self.options = options
        self.station = code_station

    def _get_duration(self, raw_train_duration):
        duration = raw_train_duration.replace(':', '小时') + '分'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration

    @property
    def trains(self):
        for raw_train in self.available_trains:
            train_no = raw_train[3]
            initial = train_no[0].lower()
            if not self.options or initial in self.options:
                train = [
                    train_no,
                    '\n'.join([Fore.GREEN + self.station[raw_train[4]] + Fore.RESET,Fore.RED + self.station[raw_train[5]] + Fore.RESET]),
                    '\n'.join([Fore.GREEN + raw_train[8] + Fore.RESET,Fore.RED + raw_train[9] + Fore.RESET]),
                    self._get_duration(raw_train[10]),
                    raw_train[31] if raw_train[31] != '' else '--',
                    raw_train[30] if raw_train[30] != '' else '--',
                    raw_train[24] if raw_train[24] != '' else '--',
                    raw_train[28] if raw_train[28] != '' else '--',
                    raw_train[29] if raw_train[29] != '' else '--',
                    raw_train[26] if raw_train[26] != '' else '--' # [24]rw [34]dw [27]wz [28]yw [29]yz [30]ez [31]yz [32]tz

                ]
                yield train
    
    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        for train in self.trains:
            pt.add_row(train)
        print(pt)

def parse_data(results):
    parsed_data = []
    for datas in results:
        data = re.split(r'\|', datas)
        parsed_data.append(data)
    return parsed_data
   

def cli():
    """command-line interface"""

    arguments = docopt(__doc__)
    from_station = station_code.get(arguments['<from>'])
    to_station = station_code.get(arguments['<to>'])
    date = arguments['<date>']
    # create url
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(date, from_station, to_station)
    options = ''.join([key for key, value in arguments.items() if value is True])
    # 添加verify=False参数不验证证书
    r = requests.get(url, verify=False)
    results = r.json()['data']['result']
    maps = r.json()
    TrainCollection(parse_data(results), options, code_station).pretty_print()


if __name__ == '__main__':
    cli()
