# -- coding: utf-8 --
# @Author : ZhiliangLong
# @File : sportGet.py
# @Time : 2025/3/22 20:19
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import requests

debug = True

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

GET_TIME_LIST_URL = "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/getTimeList.do"
GET_ROOM_LIST_URL = "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do"
INSERT_URL = "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/insertVenueBookingInfo.do"

# 默认开抢规则：预约日前一天 12:30
DEFAULT_OPEN_DAYS_BEFORE = 1
DEFAULT_OPEN_TIME = "12:30"


def build_config(you_name, you_id, yylx, type_of_sport, appointment_day,
                 appointment_time_start, cookie, campus):
    """根据配置生成请求参数与请求头，cookie 保存在内存中，运行时自动刷新。"""
    params_get_room_list = {
        "XQDM": int(campus),
        "YYRQ": appointment_day,
        "YYLX": yylx,
        "XMDM": type_of_sport,
        "KSSJ": "",
        "JSSJ": "",
    }
    params_get_time_list = {
        "XQ": 1,
        "YYRQ": appointment_day,
        "YYLX": yylx,
        "XMDM": type_of_sport,
    }
    params_insert = {
        "DHID": "",
        "YYRGH": you_id,
        "CYRS": "",
        "YYRXM": you_name,
        "CGDM": "",
        "CDWID": "",
        "XMDM": type_of_sport,
        "XQWID": "",
        "KYYSJD": "",
        "YYRQ": appointment_day,
        "YYLX": yylx,
        "YYKS": "",
        "YYJS": "",
        "PC_OR_PHONE": "pc",
    }
    return SimpleNamespace(
        you_name=you_name,
        you_id=you_id,
        yylx=yylx,
        type_of_sport=type_of_sport,
        appointment_day=appointment_day,
        appointment_time_start=appointment_time_start,
        campus=campus,
        params_get_room_list=params_get_room_list,
        params_get_time_list=params_get_time_list,
        params_insert=params_insert,
        headers={"Cookie": cookie},
    )


def load_cookie(cookie=""):
    """优先使用传入的 cookie；为空时读取项目根目录的 cookie.txt。"""
    cookie = (cookie or "").strip()
    if cookie:
        return cookie
    try:
        with open(os.path.join(BASE_DIR, "cookie.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except (IOError, OSError):
        return ""


def _load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _wait_for_cookie_update(cfg, notify, should_cancel, cancel_result, last_cookie):
    """cookie 失效后轮询 cookie.txt，检测到用户更新且有效则继续。返回 False 表示用户取消。"""
    notify('Cookies 已失效，请把当天的完整 Cookie 更新到项目根目录 cookie.txt（程序会自动检测并继续）')
    last = last_cookie
    pending = None
    retry_after = 0.0
    while True:
        if should_cancel():
            return False
        time.sleep(3)
        cookie = load_cookie()
        if not cookie:
            continue
        if cookie != last:
            last = cookie
            pending = cookie
            cfg.headers['Cookie'] = cookie
        if pending is None or time.time() < retry_after:
            continue
        flag, msg = request_url(cfg, GET_TIME_LIST_URL, cfg.params_get_time_list, cfg.headers)
        if flag:
            notify('已检测到 Cookie 更新且有效，继续执行...')
            return True
        if 'Cookies' in msg:
            pending = None
        else:
            retry_after = time.time() + 15


def _ensure_cookie_valid(cfg, notify, should_cancel, cancel_result):
    """校验 cookie 是否有效；失效时提示并等待用户更新。返回 False 表示用户取消。"""
    flag, msg = request_url(cfg, GET_TIME_LIST_URL, cfg.params_get_time_list, cfg.headers)
    if flag:
        return True
    if 'Cookies' in msg:
        return _wait_for_cookie_update(cfg, notify, should_cancel, cancel_result, cfg.headers['Cookie'])
    return True


def _merge_cookie(cfg, set_cookie_headers):
    """把响应中的 Set-Cookie 合并进内存中的 Cookie，用于运行时刷新 _WEU 会话。"""
    cookie = cfg.headers.get("Cookie", "")
    for header in set_cookie_headers:
        m = re.match(r"\s*([^=;]+)=([^;]*)", header)
        if not m:
            continue
        name, value = m.group(1).strip(), m.group(2).strip()
        pattern = re.compile(r"(^|;\s*)" + re.escape(name) + r"=[^;]*")
        if pattern.search(cookie):
            cookie = pattern.sub(lambda m: m.group(1) + name + "=" + value, cookie)
        else:
            cookie = (cookie + "; " if cookie else "") + name + "=" + value
    cfg.headers["Cookie"] = cookie


def request_url(cfg, url, params, headers):
    """POST 请求。成功解析出 JSON 返回 (True, json)，否则返回 (False, 原因)。"""
    try:
        response = requests.post(url, data=params, headers=headers, timeout=10)
    except requests.RequestException as e:
        return False, f"网络请求失败: {e}"
    set_cookie_headers = response.raw.headers.getlist("Set-Cookie")
    if set_cookie_headers:
        _merge_cookie(cfg, set_cookie_headers)
    if "authserver" in response.url:
        return False, "Cookies 已失效，请把浏览器复制的 Cookie 更新到项目根目录 cookie.txt"
    try:
        return True, json.loads(response.content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, "预约尚未开放，请稍候"


def main(cfg, emit=None, cancel_callback=None, cnt=1, target_room=None):
    """执行一轮预约尝试，返回 (是否成功, 信息)。"""
    def should_cancel():
        return cancel_callback and cancel_callback()

    if should_cancel():
        return False, '用户取消'

    # 先校验 cookie（同时刷新会话），再按运动类型取时间段列表
    flag, times_list = request_url(cfg, GET_TIME_LIST_URL, cfg.params_get_time_list, cfg.headers)
    if not flag:
        return False, 'Cookies 失效或接口未开放，请把浏览器复制的 Cookie 更新到项目根目录 cookie.txt'
    if emit:
        emit('appointment_update', {'message': 'cookies 校验成功'})
    elif debug:
        print('cookies 校验成功')

    if cfg.type_of_sport == "001":
        # 羽毛球时间表固定，直接用本地缓存，减少一次请求
        times_list = _load_json(os.path.join(STATIC_DIR, "time_list.json"))

    if debug:
        print('times_list', times_list)
        print('=' * 30)
    if should_cancel():
        return False, '用户取消'

    available_times = []
    for item in times_list:
        if should_cancel():
            return False, '用户取消'
        if not item['disabled']:
            code_start, code_end = item['CODE'].split('-')
            available_times.append({
                'code_start': code_start.strip(),
                'code_end': code_end.strip()
            })

    if debug:
        print('available_times', available_times)
        print('=' * 30)
    if should_cancel():
        return False, '用户取消'

    if not available_times:
        return False, '网慢了，已经无！要不就是还没开！'

    rooms_list = _load_json(os.path.join(STATIC_DIR, "room_list.json"))
    global_cdwid = -1
    if target_room:
        global_cdwid = rooms_list[cfg.campus][target_room]

    def move_dict_to_front(items, target):
        """将指定字典移动到列表首位，用于优先预约指定场地。"""
        if target in items:
            items.remove(target)
            items.insert(0, target)
            return True
        return False

    for item in available_times:
        if should_cancel():
            return False, '用户取消'
        if item['code_start'] < cfg.appointment_time_start:
            continue
        cfg.params_get_room_list['KSSJ'] = item['code_start']
        cfg.params_get_room_list['JSSJ'] = item['code_end']
        if should_cancel():
            return False, '用户取消'
        flag_room_info, room_info = request_url(cfg, GET_ROOM_LIST_URL, cfg.params_get_room_list, cfg.headers)
        if not flag_room_info:
            return False, room_info
        if debug:
            print('room_info', room_info)
            print('=' * 30)
        available_room = []
        for item_room in room_info['datas']['getOpeningRoom']['rows']:
            if should_cancel():
                return False, '用户取消'
            if item_room['disabled']:
                continue
            yyrq = '-'.join([item['code_start'], item['code_end']])
            yyks = ' '.join([cfg.appointment_day, item['code_start']])
            yyjs = ' '.join([cfg.appointment_day, item['code_end']])
            available_item = {
                'CGDM': item_room['CGBM'],
                'CDWID': item_room['WID'],
                'XQWID': item_room['XQDM'],
                'CDMC': item_room['CDMC'],
                'KYYSJD': yyrq,
                'YYKS': yyks,
                'YYJS': yyjs,
            }
            available_room.append(available_item)
        if debug:
            print('available_room', available_room)
            print('=' * 30)
        if should_cancel():
            return False, '用户取消'

        pre_param = []
        target_param = None
        for available_item in available_room:
            if should_cancel():
                return False, '用户取消'
            params_insert_ = cfg.params_insert.copy()
            params_insert_['CGDM'] = available_item['CGDM']
            params_insert_['CDWID'] = available_item['CDWID']
            params_insert_['KYYSJD'] = available_item['KYYSJD']
            params_insert_['YYKS'] = available_item['YYKS']
            params_insert_['YYJS'] = available_item['YYJS']
            params_insert_['CDMC'] = available_item['CDMC']
            params_insert_['XQWID'] = available_item['XQWID']
            pre_param.append(params_insert_)
            if available_item['CDWID'] == global_cdwid:
                target_param = params_insert_

        if not pre_param:
            continue
        random.shuffle(pre_param)
        if target_param is not None:
            move_dict_to_front(pre_param, target_param)

        for param_item in pre_param:
            if should_cancel():
                return False, '用户取消'
            flag, _ = request_url(cfg, INSERT_URL, param_item, cfg.headers)
            if flag:
                if cnt == 1:
                    message = f"日期:{param_item['YYKS']}\n场馆:{param_item['CDMC']}预约成功!!!\n"
                    if emit:
                        emit('appointment_update', {'message': message})
                    elif debug:
                        print(message)
                    return True, 'success'
                cnt -= 1
                global_cdwid = param_item['CDWID']
                message = f"日期:{param_item['YYKS']}\n场馆:{param_item['CDMC']}预约成功!!!\n开始下一场预约..."
                if emit:
                    emit('appointment_update', {'message': message})
                elif debug:
                    print(message)
                break
            else:
                global_cdwid = -1
                message = f"日期:{param_item['YYKS']}\n场馆:{param_item['CDMC']}预约失败!!!\n开始下一场预约..."
                if emit:
                    emit('appointment_update', {'message': message})
                elif debug:
                    print(message)
    return False, '可能是你选择的时间段没了'


def strat_appointment(day, start_time, stu_name, stu_id, cookie, sport_type="001", yylx=1.0,
                      emit=None,
                      max_attempts=30, retry_delay=0.5, cancel_callback=None, cnt=1, campus="1", target_room=None):
    """预约入口。

    :param day: 预约日期，格式 YYYY-MM-DD
    :param start_time: 预约开始时间，格式 HH:MM
    :param stu_name: 姓名
    :param stu_id: 学号
    :param cookie: 浏览器复制来的完整 Cookie 字符串（或留空，自动读取 cookie.txt）
    """
    def notify(msg: str):
        if emit:
            emit('appointment_update', {'message': msg})
        else:
            print(msg)

    def should_cancel():
        return cancel_callback and cancel_callback()

    def cancel_result():
        notify('用户取消，任务已停止')
        return False, '用户取消'

    if not stu_id:
        notify('请先配置个人信息')
        return False, 'missing user information'
    if not cookie or not str(cookie).strip():
        notify('未配置 Cookie：请把浏览器复制的 Cookie 粘贴到项目根目录 cookie.txt')
        return False, 'missing cookie'

    cfg = build_config(
        you_name=stu_name,
        you_id=stu_id,
        yylx=yylx,
        type_of_sport=sport_type,
        appointment_day=day,
        appointment_time_start=start_time,
        cookie=str(cookie).strip(),
        campus=campus,
    )

    try:
        appointment_date = datetime.strptime(day, '%Y-%m-%d').date()
    except ValueError:
        notify(f'预约日期格式错误: {day}')
        return False, 'invalid appointment day'
    if appointment_date < datetime.now().date():
        notify('预约日期已经过去，程序停止')
        return False, 'appointment day already passed'

    # 固定开抢时间：预约日前一天 12:30
    target_time = datetime.combine(
        appointment_date - timedelta(days=DEFAULT_OPEN_DAYS_BEFORE),
        datetime.strptime(DEFAULT_OPEN_TIME, '%H:%M').time(),
    )

    # 启动时先校验 cookie，失效则提示并等待用户在 cookie.txt 中更新
    if should_cancel():
        return cancel_result()
    if not _ensure_cookie_valid(cfg, notify, should_cancel, cancel_result):
        return cancel_result()

    def countdown(remaining):
        total_seconds = int(remaining.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        notify(f'距离预约开放时间还剩: {hours:02d}:{minutes:02d}:{seconds:02d}')

    if target_time:
        # 越接近开抢时间，倒计时刷新越频繁；最后阶段不再发请求，避免影响预约性能
        while True:
            if should_cancel():
                return cancel_result()
            remaining = target_time - datetime.now()
            if remaining.total_seconds() <= 0:
                break
            total = remaining.total_seconds()
            if total >= 3600:
                interval, refresh = 900, True
            elif total >= 600:
                interval, refresh = 600, True
            elif total >= 60:
                interval, refresh = 60, False
            elif total >= 10:
                interval, refresh = 5, False
            else:
                interval, refresh = 1, False
            countdown(remaining)
            time.sleep(interval)
            if refresh:
                # 长时间等待时定期校验并刷新 cookie 会话；失效会立即提示并等待更新
                if not _ensure_cookie_valid(cfg, notify, should_cancel, cancel_result):
                    return cancel_result()

    attempts = 0
    last_error = ''
    while attempts < max_attempts:
        if should_cancel():
            return cancel_result()
        attempts += 1
        success, msg_main = main(cfg, emit=emit, cancel_callback=should_cancel, cnt=cnt, target_room=target_room)
        if success:
            notify('预约成功，速速付款!')
            return True, 'success'
        last_error = msg_main or 'unknown error'
        notify('预约失败，原因是 ' + last_error)
        if attempts < max_attempts:
            if should_cancel():
                return cancel_result()
            time.sleep(retry_delay)

    if should_cancel():
        return cancel_result()
    if not last_error:
        last_error = '预约失败'
    return False, last_error + f' (尝试 {attempts} 次)'