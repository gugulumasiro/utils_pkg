# -- coding: utf-8 --
from CStack_utils import *
from config import (YOU_NAME, YOU_ID, YYLX, typeOfSport, appointment_day,
                    appointment_time_start, cnt, campus, target_room)

you_name = YOU_NAME  # 姓名
you_id = YOU_ID  # 学号
# Cookie 从项目根目录 cookie.txt 读取（浏览器复制后手动粘贴进去）
cookie = sportGet.load_cookie()

sportGet.strat_appointment(appointment_day,
                           appointment_time_start,
                           you_name,
                           you_id,
                           cookie,
                           sport_type=typeOfSport,
                           yylx=YYLX,
                           cnt=cnt,
                           campus=campus,
                           target_room=target_room)