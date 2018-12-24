import base64
import contextlib
import os
import re
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from AutoElectsysUtil import (config_file_name, course_rounds, file_read_json, file_read_lines, file_write_json,
                              file_write_lines, first_categories, is_positive_int, pswd_file_name, remove_utf8_bom)

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

default_pswd_choice = 0
default_captcha = 0
default_relogin_interval = 60
default_teacher_row = 1
default_round = 2
default_first_category = 3
default_sleep = 2000


class AutoElectsysConfig:
    def __init__(self):
        self.init_window()
        self.init_color()
        self.init_coords()
        self.init_widgets()
        self.init_tips()
        self.load()
        self.show_status()

    def init_window(self):
        self.window = tk.Tk()
        self.window.title('AutoElectsys 配置设置')
        self.window.geometry('552x400')
        self.window.resizable(False, False)
        self.window.protocol('WM_DELETE_WINDOW', self.ask_quit)

    def init_color(self):
        self.login_color = 'White'
        self.course_color = 'White'
        self.misc_color = 'White'
        self.info_color = 'RoyalBlue'
        self.success_color = 'LimeGreen'
        self.error_color = 'Crimson'
        self.style = ttk.Style()
        self.style.configure('Login.TRadiobutton', background=self.login_color)
        self.style.configure('Login.TLabel', background=self.login_color)
        self.style.configure('Login.TCheckbutton', background=self.login_color)
        self.style.configure('Course.TLabel', background=self.course_color)
        self.style.configure('Course.TCheckbutton', background=self.course_color)
        self.style.configure('Misc.TRadiobutton', background=self.misc_color)
        self.style.configure('Misc.TLabel', background=self.misc_color)
        self.style.configure('Info_Login.TLabel', foreground=self.info_color, background=self.login_color)
        self.style.configure('Info_Course.TLabel', foreground=self.info_color, background=self.course_color)
        self.style.configure('Info_Misc.TLabel', foreground=self.info_color, background=self.misc_color)
        self.style.configure('Success.TLabel', foreground=self.success_color)
        self.style.configure('Error.TLabel', foreground=self.error_color)

    def init_coords(self):
        self.tab_x = 15
        self.tab_y = 30
        self.tab_w = 520
        self.tab_h = 280

        self.x1 = 15
        self.yd = 33
        self.y1 = 15
        self.y2 = self.y1 + self.yd
        self.y3 = self.y1 + self.yd * 2
        self.y4 = self.y1 + self.yd * 3
        self.y5 = self.y1 + self.yd * 4
        self.y6 = self.y1 + self.yd * 5
        self.y7 = self.y1 + self.yd * 6

        self.w1 = 14
        self.w2 = 8
        self.w3 = 7
        self.w4 = 22

        self.login_x2 = self.x1 + 18
        self.login_x3 = self.x1 + 82
        self.login_x4 = self.x1 + 150

        self.course_x2 = self.x1 + 70

        self.misc_x2 = self.x1 + 70
        self.misc_x3 = self.x1 + 140

        self.bottom_x1 = 180
        self.bottom_x2 = 280
        self.bottom_y = 350

        self.tip_x = 275

        self.status_x = 276
        self.status_y = 7

    def init_widgets(self):
        self.tab = ttk.Notebook(self.window, width=self.tab_w, height=self.tab_h)
        self.tab.place(x=self.tab_x, y=self.tab_y)

        self.login_frame = tk.Frame(self.tab, background=self.login_color)
        self.tab.add(self.login_frame, text='登录设置')

        self.pswd_choice_v = tk.IntVar()
        self.pswd_chrome_radio = ttk.Radiobutton(self.login_frame, text='使用 Chrome 保存的用户名和密码',
                                                 variable=self.pswd_choice_v, value=1, command=self.on_pswd,
                                                 style='Login.TRadiobutton')
        self.pswd_chrome_radio.place(x=self.x1, y=self.y1)

        self.pswd_custom_radio = ttk.Radiobutton(self.login_frame, text='使用自定义的用户名和密码',
                                                 variable=self.pswd_choice_v, value=0, command=self.on_pswd,
                                                 style='Login.TRadiobutton')
        self.pswd_custom_radio.place(x=self.x1, y=self.y2)

        self.clear_pswd_button = ttk.Button(self.login_frame, text='清除账号信息', command=self.on_clear)
        self.clear_pswd_button.place(x=self.tip_x, y=self.y4)

        self.user_label = ttk.Label(self.login_frame, text='用户名：', style='Login.TLabel')
        self.user_label.place(x=self.login_x2, y=self.y3)

        self.user_v = tk.StringVar()
        self.user_entry = ttk.Entry(self.login_frame, textvariable=self.user_v, width=self.w1)
        self.user_entry.place(x=self.login_x3, y=self.y3)

        self.pass_label = ttk.Label(self.login_frame, text='密码：', style='Login.TLabel')
        self.pass_label.place(x=self.login_x2, y=self.y4)

        self.pass_v = tk.StringVar()
        self.pass_entry = ttk.Entry(self.login_frame, textvariable=self.pass_v, width=self.w1, show='*')
        self.pass_entry.place(x=self.login_x3, y=self.y4)

        self.captcha_v = tk.IntVar()
        self.captcha_check = ttk.Checkbutton(self.login_frame, text='自动识别验证码', variable=self.captcha_v,
                                             command=self.on_captcha, style='Login.TCheckbutton')
        self.captcha_check.place(x=self.x1, y=self.y5)

        self.relogin_v = tk.IntVar()
        self.relogin_check = ttk.Checkbutton(self.login_frame, text='自动重新登录', variable=self.relogin_v,
                                             command=self.on_relogin, style='Login.TCheckbutton')
        self.relogin_check.place(x=self.x1, y=self.y6)

        self.per_label = ttk.Label(self.login_frame, text='时间间隔：', style='Login.TLabel')
        self.per_label.place(x=self.login_x2, y=self.y7)

        self.relogin_interval_v = tk.StringVar()
        self.relogin_interval = ttk.Entry(self.login_frame, textvariable=self.relogin_interval_v, width=self.w2)
        self.relogin_interval.place(x=self.login_x3, y=self.y7)

        self.min_label = ttk.Label(self.login_frame, text='分钟', style='Login.TLabel')
        self.min_label.place(x=self.login_x4, y=self.y7)

        self.course_frame = tk.Frame(self.tab, background=self.course_color)
        self.tab.add(self.course_frame, text='课程设置')

        self.course_id_label = ttk.Label(self.course_frame, text='课程代码：', style='Course.TLabel')
        self.course_id_label.place(x=self.x1, y=self.y1)

        self.course_id_v = tk.StringVar()
        self.course_id_entry = ttk.Entry(self.course_frame, textvariable=self.course_id_v, width=self.w1)
        self.course_id_entry.place(x=self.course_x2, y=self.y1)

        self.teacher_row_label = ttk.Label(self.course_frame, text='教师行数：', style='Course.TLabel')
        self.teacher_row_label.place(x=self.x1, y=self.y2)

        self.teacher_row_v = tk.StringVar()
        self.teacher_row_entry = ttk.Entry(self.course_frame, textvariable=self.teacher_row_v, width=self.w1)
        self.teacher_row_entry.place(x=self.course_x2, y=self.y2)

        self.round_label = ttk.Label(self.course_frame, text='选课轮次：', style='Course.TLabel')
        self.round_label.place(x=self.x1, y=self.y3)

        self.round_v = tk.StringVar()
        self.round_combo = ttk.Combobox(self.course_frame, values=course_rounds, textvariable=self.round_v,
                                        state='readonly', width=self.w1)
        self.round_combo.bind('<<ComboboxSelected>>', self.on_round)
        self.round_combo.place(x=self.course_x2, y=self.y3)

        self.autolocate_v = tk.IntVar()
        self.autolocate_check = ttk.Checkbutton(self.course_frame, text='自动定位选课页面',
                                                variable=self.autolocate_v, command=self.on_locate,
                                                style='Course.TCheckbutton')
        self.autolocate_check.place(x=self.x1, y=self.y4)

        self.first_cat_label = ttk.Label(self.course_frame, text='一级分类：', style='Course.TLabel')
        self.first_cat_label.place(x=self.x1, y=self.y5)

        self.first_cat_v = tk.StringVar()
        self.first_cat_combo = ttk.Combobox(self.course_frame, values=first_categories,
                                            textvariable=self.first_cat_v, state='readonly', width=self.w1)
        self.first_cat_combo.bind('<<ComboboxSelected>>', self.on_first_cat)
        self.first_cat_combo.place(x=self.course_x2, y=self.y5)

        self.second_cat_label = ttk.Label(self.course_frame, text='二级分类：', style='Course.TLabel')
        self.second_cat_label.place(x=self.x1, y=self.y6)

        self.second_cat_v = tk.StringVar()
        self.second_cat_entry = ttk.Entry(self.course_frame, textvariable=self.second_cat_v, width=self.w4)
        self.second_cat_entry.place(x=self.course_x2, y=self.y6)

        self.misc_frame = tk.Frame(self.tab, background=self.misc_color)
        self.tab.add(self.misc_frame, text='其他设置')

        self.sleep_label = ttk.Label(self.misc_frame, text='刷新间隔：', style='Misc.TLabel')
        self.sleep_label.place(x=self.x1, y=self.y1)

        self.sleep_v = tk.StringVar()
        self.sleep_entry = ttk.Entry(self.misc_frame, textvariable=self.sleep_v, width=self.w2)
        self.sleep_entry.place(x=self.misc_x2, y=self.y1)

        self.ms_label = ttk.Label(self.misc_frame, text='毫秒', style='Misc.TLabel')
        self.ms_label.place(x=self.misc_x3, y=self.y1)

        self.ok_button = ttk.Button(self.window, text='确定', command=self.store)
        self.ok_button.place(x=self.bottom_x1, y=self.bottom_y)
        self.window.bind('<Control-s>', self.store)

        self.cancel_button = ttk.Button(self.window, text='取消', command=self.ask_quit)
        self.cancel_button.place(x=self.bottom_x2, y=self.bottom_y)
        self.window.bind('<Escape>', self.ask_quit)

    def init_tips(self):
        self.pswd_tip_label = ttk.Label(self.login_frame, style='Info_Login.TLabel')

        self.captcha_tip_label = ttk.Label(self.login_frame, text='自动识别 jAccount 登录页面的验证码。',
                                           style='Info_Login.TLabel')
        self.captcha_tip_label.place(x=self.tip_x, y=self.y5)

        self.relogin_tip_label = ttk.Label(self.login_frame, text='每隔一段时间自动重新登录，\n'
                                                                  '刷新 Cookie 以防止页面过期。\n'
                                                                  '需开启自动定位选课页面功能。',
                                           style='Info_Login.TLabel')
        self.relogin_tip_label.place(x=self.tip_x, y=self.y6)

        self.course_id_tip_label = ttk.Label(self.course_frame, text='欲选课程的课程代码，可在网页上查知。',
                                             style='Info_Course.TLabel')
        self.course_id_tip_label.place(x=self.tip_x, y=self.y1)

        self.teacher_row_tip_label = ttk.Label(self.course_frame, text='欲选教师或时间段在内层页面中第几行。',
                                               style='Info_Course.TLabel')
        self.teacher_row_tip_label.place(x=self.tip_x, y=self.y2)

        self.round_tip_label = ttk.Label(self.course_frame, text='“其他”项用于二专选课等。\n'
                                                                 '此模式下不支持自动定位选课页面。',
                                         style='Info_Course.TLabel')
        self.round_tip_label.place(x=self.tip_x, y=self.y3)

        self.autolocate_tip_label = ttk.Label(self.course_frame, text='按照课程的类型，自动进入所在的页面。',
                                              style='Info_Course.TLabel')
        self.autolocate_tip_label.place(x=self.tip_x, y=self.y4)

        self.second_cat_tip_label = ttk.Label(self.course_frame, style='Info_Course.TLabel')
        self.second_cat_tip_label.place(x=self.tip_x, y=self.y6)

        self.sleep_time_tip_label = ttk.Label(self.misc_frame, text='设置自动刷新选课页面的频率。\n'
                                                                    '若提示“请勿频繁刷新本页面”，\n'
                                                                    '请将此值调大。',
                                              style='Info_Misc.TLabel')
        self.sleep_time_tip_label.place(x=self.tip_x, y=self.y1)

    def on_pswd(self):
        if self.pswd_choice_v.get():
            new_state = 'disabled'
            new_text = '将加载您的 Chrome 用户文件，\n您的插件以及保存的密码会被\nChrome 载入。'
            new_y = self.y1
        else:
            new_state = 'normal'
            new_text = '将以新用户身份打开 Chrome，\n不会载入您的插件和保存的密码。\n请在左侧填写 jAccount 账号信息。'
            new_y = self.y2

        self.user_label.config(state=new_state)
        self.user_entry.config(state=new_state)
        self.pass_label.config(state=new_state)
        self.pass_entry.config(state=new_state)
        self.pswd_tip_label.config(text=new_text)
        self.pswd_tip_label.place(x=self.tip_x, y=new_y)

    def on_clear(self):
        self.user_v.set('')
        self.pass_v.set('')

    def on_captcha(self):
        if self.captcha_v.get():
            self.captcha_tip_label.config(state='normal')

            if self.autolocate_v.get():
                self.relogin_check.config(state='normal')
        else:
            self.captcha_tip_label.config(state='disabled')
            self.relogin_check.config(state='disabled')
            self.relogin_v.set(0)
            self.relogin_tip_label.config(state='disabled')
            self.on_relogin()

    def on_relogin(self):
        if self.relogin_v.get():
            new_state = 'normal'

            if self.relogin_interval_v.get().strip() == '':
                self.relogin_interval_v.set(str(default_relogin_interval))
        else:
            new_state = 'disabled'

        self.relogin_tip_label.config(state=new_state)
        self.per_label.config(state=new_state)
        self.relogin_interval.config(state=new_state)
        self.min_label.config(state=new_state)

    def on_locate(self):
        if self.autolocate_v.get():
            self.autolocate_tip_label.config(state='normal')
            self.first_cat_label.config(state='normal')
            self.first_cat_combo.config(state='normal')
            self.first_cat_combo.config(state='readonly')
            self.on_first_cat()

            if self.captcha_v.get():
                self.relogin_check.config(state='normal')
        else:
            self.autolocate_tip_label.config(state='disabled')
            self.first_cat_label.config(state='disabled')
            self.first_cat_combo.config(state='disabled')
            self.second_cat_label.config(state='disabled')
            self.second_cat_entry.config(state='disabled')
            self.second_cat_tip_label.config(state='disabled')
            self.relogin_check.config(state='disabled')
            self.relogin_v.set(0)
            self.relogin_tip_label.config(state='disabled')
            self.on_relogin()

    def on_round(self, event=None):
        if self.round_v.get() == course_rounds[0]:
            self.autolocate_v.set(0)
            self.autolocate_check.config(state='disabled')
            self.autolocate_tip_label.config(state='disabled')
            self.round_tip_label.place(x=self.tip_x, y=self.y3)
            self.on_locate()
        else:
            self.autolocate_check.config(state='normal')
            self.round_tip_label.place_forget()

    def on_first_cat(self, event=None):
        s = self.first_cat_v.get()

        if s in (first_categories[0], first_categories[4]):
            new_state = 'disabled'
            new_text = ''
        else:
            new_state = 'normal'

            if s == first_categories[1]:
                new_text = '填写课程所属的模块名称，\n如“个性化教育”等。\n请填写网页上显示的全称，不要简写。'
            elif s == first_categories[2]:
                new_text = '填写课程所属的模块名称，\n如“人文学科”“社会科学”等。\n请填写网页上显示的全称，不要简写。'
            else:
                new_text = '填写开课院系名称。\n请填写网页上显示的全称，不要简写。\n注：默认选择本年级，跨年级选课\n请勿使用自动定位功能。'

        self.second_cat_label.config(state=new_state)
        self.second_cat_entry.config(state=new_state)
        self.second_cat_tip_label.config(state=new_state, text=new_text)

    def load(self):
        self.config_file_exists = os.path.isfile(config_file_name)

        try:
            remove_utf8_bom(config_file_name)
        except Exception:
            messagebox.showerror('错误', '无法写入配置文件！')
            self.quit()

        self.config_file_valid = True

        try:
            config = file_read_json(config_file_name)
        except Exception:
            self.config_file_valid = False

        try:
            cf_pswd_choice = config['Login']['password_saved']
            assert isinstance(cf_pswd_choice, bool)
            self.pswd_choice_v.set(cf_pswd_choice)
        except Exception:
            self.config_file_valid = False
            self.pswd_choice_v.set(default_pswd_choice)

        try:
            cf_captcha = config['Login']['auto_captcha']
            assert isinstance(cf_captcha, bool)
            self.captcha_v.set(cf_captcha)
        except Exception:
            self.config_file_valid = False
            self.captcha_v.set(default_captcha)

        try:
            cf_relogin_interval = config['Login']['relogin_interval']
            assert isinstance(cf_relogin_interval, int) and cf_relogin_interval >= 0

            if cf_relogin_interval == 0:
                self.relogin_interval_v.set('')
                self.relogin_v.set(0)
            else:
                self.relogin_interval_v.set(str(cf_relogin_interval))
                self.relogin_v.set(1)
        except Exception:
            self.config_file_valid = False
            self.relogin_interval_v.set('')
            self.relogin_v.set(0)
            self.relogin_tip_label.config(state='disabled')

        try:
            cf_course_id = config['CourseInfo']['course_id']
            assert isinstance(cf_course_id, str)
            assert re.fullmatch('[A-Za-z0-9]*', cf_course_id)
            self.course_id_v.set(cf_course_id)
        except Exception:
            self.config_file_valid = False
            self.course_id_v.set('')

        try:
            cf_teacher_row = config['CourseInfo']['teacher_row']
            assert isinstance(cf_teacher_row, int) and cf_teacher_row > 0
            self.teacher_row_v.set(str(cf_teacher_row))
        except Exception:
            self.config_file_valid = False
            self.teacher_row_v.set(str(default_teacher_row))

        try:
            cf_round = config['CourseLocate']['round']
            assert isinstance(cf_round, int) and cf_round in range(0, 7)
            self.round_v.set(course_rounds[cf_round])
        except Exception:
            self.config_file_valid = False
            self.round_v.set(course_rounds[default_round])

        try:
            cf_auto_locate = config['CourseLocate']['auto_locate']
            assert isinstance(cf_auto_locate, bool)
            self.autolocate_v.set(cf_auto_locate)
        except Exception:
            self.config_file_valid = False
            self.autolocate_v.set(0)
            self.autolocate_tip_label.config(state='disabled')

        try:
            cf_first_category = config['CourseLocate']['first_category']
            assert isinstance(cf_first_category, int) and cf_first_category in (1, 2, 3, 4, 5)
            self.first_cat_v.set(first_categories[cf_first_category - 1])

            if cf_first_category in (2, 3, 4):
                try:
                    cf_second_category = config['CourseLocate']['second_category']
                    assert isinstance(cf_second_category, str)
                    self.second_cat_v.set(cf_second_category)
                except Exception:
                    self.config_file_valid = False
                    self.second_cat_v.set('')
        except Exception:
            self.config_file_valid = False
            self.first_cat_v.set(first_categories[default_first_category - 1])

        try:
            cf_sleep = config['Miscellaneous']['sleep_time']
            assert isinstance(cf_sleep, int) and cf_sleep > 0
            self.sleep_v.set(str(cf_sleep))
        except Exception:
            self.config_file_valid = False
            self.sleep_v.set(str(default_sleep))

        try:
            username, password = file_read_lines(pswd_file_name)
            password = base64.b85decode(password).decode()
        except Exception:
            username = ''
            password = ''

        self.user_v.set(username)
        self.pass_v.set(password)

        self.on_pswd()
        self.on_relogin()
        self.on_captcha()
        self.on_first_cat()
        self.on_locate()
        self.on_round()

    def show_status(self):
        if self.config_file_exists:
            if self.config_file_valid:
                self.status_label = ttk.Label(self.window, text='成功读取配置文件', style='Success.TLabel')
            else:
                self.status_label = ttk.Label(self.window, text='配置文件格式错误或值无效，将自动修正',
                                              style='Error.TLabel')
        else:
            self.status_label = ttk.Label(self.window, text='配置文件不存在，将创建新的配置文件',
                                          style='Error.TLabel')

        self.status_label.place(x=self.status_x, y=self.status_y, anchor=tk.N)

    def store(self, event=None):
        config = {
            'Login': {},
            'CourseInfo': {},
            'CourseLocate': {},
            'Miscellaneous': {}
        }

        config['Login']['password_saved'] = bool(self.pswd_choice_v.get())
        config['Login']['auto_captcha'] = bool(self.captcha_v.get())

        if self.relogin_v.get():
            cf_relogin_interval = self.relogin_interval_v.get().strip()

            if cf_relogin_interval == '':
                messagebox.showwarning('错误', '请设置自动重新登录的间隔时间！')
                return

            if not is_positive_int(cf_relogin_interval):
                messagebox.showwarning('错误', '自动重新登录间隔时间应为正整数！')
                return
        else:
            cf_relogin_interval = '0'

        config['Login']['relogin_interval'] = int(cf_relogin_interval)

        cf_course_id = self.course_id_v.get().strip()

        if not re.fullmatch('[A-Za-z0-9]*', cf_course_id):
            messagebox.showwarning('错误', '课程代码只能包含字母和数字！')
            return

        config['CourseInfo']['course_id'] = cf_course_id

        cf_teacher_row = self.teacher_row_v.get().strip()

        if cf_teacher_row == '':
            messagebox.showwarning('错误', '请填写教师行数！')
            return

        if not is_positive_int(cf_teacher_row):
            messagebox.showwarning('错误', '教师行数应为正整数！')
            return

        config['CourseInfo']['teacher_row'] = int(cf_teacher_row)

        config['CourseLocate']['round'] = course_rounds.index(self.round_v.get())

        config['CourseLocate']['auto_locate'] = bool(self.autolocate_v.get())

        config['CourseLocate']['first_category'] = first_categories.index(self.first_cat_v.get()) + 1

        config['CourseLocate']['second_category'] = self.second_cat_v.get().strip()

        cf_sleep = self.sleep_v.get().strip()

        if cf_sleep == '':
            messagebox.showwarning('错误', '请设置选课页面刷新间隔！')
            return

        if not is_positive_int(cf_sleep):
            messagebox.showwarning('错误', '选课页面刷新间隔应为正整数！')
            return

        config['Miscellaneous']['sleep_time'] = int(cf_sleep)

        if not messagebox.askokcancel('保存', '确定要保存当前配置吗？'):
            return

        try:
            file_write_json(config_file_name, config, indent=4, ensure_ascii=False)
        except Exception:
            messagebox.showerror('错误', '无法写入配置文件！')
            self.quit()

        username = self.user_v.get()
        password = self.pass_v.get()

        if username == '' and password == '':
            with contextlib.suppress(Exception):
                os.remove(pswd_file_name)
        else:
            try:
                password = base64.b85encode(password.encode()).decode()
                file_write_lines(pswd_file_name, (username, password))
            except Exception:
                messagebox.showerror('错误', '无法写入账号信息文件！')
                self.quit()

        self.quit()

    def __call__(self):
        self.window.mainloop()

    def quit(self):
        self.window.quit()

    def ask_quit(self, event=None):
        if messagebox.askokcancel('退出', '确定要退出吗？'):
            self.quit()


def main():
    aec = AutoElectsysConfig()
    aec()


if __name__ == '__main__':
    main()
