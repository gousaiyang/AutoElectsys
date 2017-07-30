# -*- coding: utf-8 -*-

import time
import datetime
import os
import ConfigParser
import base64
import re

import platform
current_system = platform.system()
is_windows = current_system == 'Windows'
is_mac = current_system == 'Darwin'
is_64 = '64' in platform.machine()

config_file_name = 'AutoElectsys.ini'
pswd_file_name = 'jaccount.pswd'
log_file_name = 'AutoElectsys.log'

try:
    log = open(log_file_name, 'a')
except:
    print u'错误：无法打开或创建日志文件！\n'
    print u'请按Enter键退出...',
    raw_input()
    raise SystemExit

def write_log(message):
    log.write(time.strftime('%Y-%m-%d %H:%M:%S '))
    log.write(message)
    log.write('\n')

def print_and_log(s):
    print s
    write_log(s.encode('UTF-8'))

try:
    from selenium import webdriver
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import NoSuchElementException
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    webdriver_wait_time = 10
    if is_windows:
        webdriver_dir = './dependency/chromedriver_win32.exe'
    elif is_mac:
        webdriver_dir = './dependency/chromedriver_mac64'
    elif is_64:
        webdriver_dir = './dependency/chromedriver_linux64'
    else:
        webdriver_dir = './dependency/chromedriver_linux32'
except ImportError:
    print u'错误：您的 Python 未安装 selenium 库，请安装 selenium 库后继续使用本程序！\n'
    print u'请按Enter键退出...',
    raw_input()
    raise SystemExit

def WaitForElement(driver, by, s):
    return WebDriverWait(driver, timeout = webdriver_wait_time).until(EC.presence_of_element_located((by, s)))

def get_user_data_dir():
    if is_windows:
        s = os.getenv('LOCALAPPDATA') + '\\Google\\Chrome\\User Data'
    elif is_mac:
        s = os.getenv('HOME') + '/Library/Application Support/Google/Chrome'
    else:
        s = os.getenv('HOME') + '/.config/google-chrome'
    if os.path.isdir(s):
        return s
    else:
        return ''

jHelper_dir = './dependency/SJTU-jAccount-Login-Helper_v0.3.1.crx'
jHelper_id = 'ihchdleonhejkpdkmahiejaabcpkkicj'

def jHelper_installed(base_dir):
    ext_dir = base_dir.replace('\\', '/') + '/Default/Extensions/' + jHelper_id
    return os.path.isdir(ext_dir)

def remove_white_space(s):
    return s.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')

def to_utf8(s):
    if is_windows:
        return s.decode('GB2312').encode('UTF-8')
    else:
        return s

def fix_utf8(filename):
    try:
        f = open(filename, 'r')
        s = f.read(3)
        if s != '\xef\xbb\xbf':
            f.close()
            return
        s = f.read()
        f.close()
        f = open(filename, 'w')
        f.write(s)
        f.close()
    except:
        pass

try:
    import Tkinter
    import tkMessageBox
    tkinter_available = True
except ImportError:
    tkinter_available = False
    print u'注意：您的 Python 未安装 Tkinter 库，选课提交后将无法出现弹窗提示。\n'

def alert_msg(title, content):
    if tkinter_available:
        root = Tkinter.Tk()
        root.withdraw()
        tkMessageBox.showinfo(title, content)
        root.destroy()

class AutoElectsys:
    def __init__(self):
        print u'SJTU AutoElectsys\n'
        print u'初始化中...'
        write_log('启动程序。')
        self.init_config()
        self.init_webdriver()
        print '\n'         

    def init_config(self):
        try:
            self.logged_in = False

            if is_windows:
                fix_utf8(config_file_name)

            cf = ConfigParser.ConfigParser()
            cf.read(config_file_name)

            self.password_saved = bool(cf.getint('Login', 'password_saved'))
            self.user_data = self.password_saved
            if self.user_data:
                self.user_data_dir = get_user_data_dir()
                if self.user_data_dir == '':
                    self.error_exit(u'错误：找不到 Chrome 用户文件夹，请确认 Chrome 是否正常安装。')
            self.autocaptcha_on = bool(cf.getint('Login', 'auto_captcha'))
            self.relogin_interval = cf.getint('Login', 'relogin_interval')
            self.auto_relogin = self.relogin_interval > 0

            self.course_id = cf.get('CourseInfo', 'course_id')
            self.teacher_row = cf.getint('CourseInfo', 'teacher_row')

            self.round = cf.getint('CourseLocate', 'round')
            self.auto_locate = bool(cf.getint('CourseLocate', 'auto_locate'))
            if (not self.autocaptcha_on or not self.auto_locate) and self.auto_relogin:
                self.error_exit(u'无效配置项：自动重新登录需要自动识别验证码，并开启选课页面自动定位功能。')
            if self.auto_locate:
                if self.round == 0:
                    self.error_exit(u'无效配置项：自动定位选课页面不支持“其他”选课轮次。')
                self.first_category = cf.getint('CourseLocate', 'first_category')
                if self.first_category in [2, 3, 4]:
                    self.second_category = cf.get('CourseLocate', 'second_category')

            self.sleep_time = cf.getint('Miscellaneous', 'sleep_time')
            self.browse_only = self.course_id == ''

            self.electsys_pp_on = False

        except ConfigParser.NoSectionError:
            self.error_exit(u'错误：配置文件出现错误，请使用配置器检查并修复！')

        except ConfigParser.DuplicateSectionError:
            self.error_exit(u'错误：配置文件出现错误，请使用配置器检查并修复！')

        except ConfigParser.NoOptionError:
            self.error_exit(u'错误：配置文件出现错误，请使用配置器检查并修复！')

        except ConfigParser.ParsingError:
            self.error_exit(u'错误：配置文件出现错误，请使用配置器检查并修复！')

        except ConfigParser.MissingSectionHeaderError:
            self.error_exit(u'错误：配置文件出现错误，请使用配置器检查并修复！')

    def init_webdriver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['ignore-certificate-errors'])
        if self.user_data:
            options.add_argument('user-data-dir=' + to_utf8(self.user_data_dir))
            if self.autocaptcha_on and not jHelper_installed(self.user_data_dir):
                options.add_extension(jHelper_dir)
        else:
            if self.autocaptcha_on:
                options.add_extension(jHelper_dir)
        self.driver = webdriver.Chrome(webdriver_dir, chrome_options = options)
        self.driver.maximize_window()

    def get_user_and_pass(self):
        try:
            faccount = open(pswd_file_name, 'r')
            username = faccount.readline()
            password = faccount.readline()
            username = username.replace('\n', '')
            password = base64.decodestring(password.replace('\n', ''))
            return username, password
        except:
            self.error_exit(u'错误：读取账号信息文件失败！')

    def auto_input_captcha(self):
        try:
            title = WaitForElement(self.driver, By.XPATH, '//title')
            result = re.findall(r'<img src="([^"]*)"', self.driver.page_source)
            captcha_src = ''
            for item in result:
                if 'captcha' in item:
                    captcha_src = item
            if captcha_src == '':
                self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')
            captchapic = WaitForElement(self.driver, By.XPATH, '//img[@src="%s"]' % (captcha_src))
            captchapic.click()
            time.sleep(0.5)
            captchabox = WaitForElement(self.driver, By.ID, 'captcha')
            captchabox.send_keys('\n')
            return True

        except NoSuchElementException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

        except TimeoutException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

    def login(self):
        try:
            if not self.password_saved:
                username, password = self.get_user_and_pass()
            flag = True
            self.driver.get('http://electsys.sjtu.edu.cn/edu/login.aspx')
            while flag:
                if not self.password_saved:
                    userbox = WaitForElement(self.driver, By.ID, 'user')
                    userbox.clear()
                    userbox.send_keys(username)
                    passbox = WaitForElement(self.driver, By.ID, 'pass')
                    passbox.clear()
                    passbox.send_keys(password)
                if self.autocaptcha_on:
                    flag = not self.auto_input_captcha()
                    if flag:
                        self.driver.get('http://electsys.sjtu.edu.cn/edu/login.aspx')
                        continue
                    title = WaitForElement(self.driver, By.XPATH, '//title')
                else:
                    print u'请输入验证码并成功登录后再按 Enter 键继续...',
                    raw_input()
                    print
                flag = u'请正确填写验证码' in self.driver.page_source
            if self.driver.title == u'上海交通大学教学信息服务网－学生服务平台':
                print_and_log(u'成功登录教学信息服务网。')
                print
                self.logged_in = True
                if self.auto_relogin:
                    self.t1 = datetime.datetime.now()
                self.electsys_pp_on = 'Optimized by electsys++' in self.driver.page_source
                now_handle = self.driver.current_window_handle
                all_handles = self.driver.window_handles
                for handle in all_handles:
                    if handle != now_handle:
                        self.driver.switch_to_window(handle)
                        self.driver.close()
                self.driver.switch_to_window(now_handle)
            else:
                print u'错误：登录教学信息服务网失败！\n'
                print u'这可能是以下2种原因导致的：'
                print u'(1)您输入的用户名或密码不正确。'
                print u'(2)网络不畅通。'
                write_log('错误：登录教学信息服务网失败！')
                self.error_exit()

        except NoSuchElementException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

        except TimeoutException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

    def readme(self):
        if self.round == 0:
            return
        try:
            try:
                if self.round < 1 or self.round > 6:
                    raise ValueError
                if self.round == 1:
                    print_and_log(u'读取到的选课轮次设置：海选。')
                elif self.round == 2:
                    print_and_log(u'读取到的选课轮次设置：抢选。')
                elif self.round == 3:
                    print_and_log(u'读取到的选课轮次设置：第三轮选课。')
                elif self.round == 4:
                    print_and_log(u'读取到的选课轮次设置：暑假小学期海选。')
                elif self.round == 5:
                    print_and_log(u'读取到的选课轮次设置：暑假小学期抢选。')
                else:
                    print_and_log(u'读取到的选课轮次设置：暑假小学期第三轮选课。')
            except:
                print_and_log(u'读取到无效的选课轮次设置，已自动设置为抢选。')
                self.round = 2
            if self.round == 1:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=1')
            elif self.round == 2:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=2')
            elif self.round == 3:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=3')
            elif self.round == 4:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/warning.aspx?xklc=1&lb=3')
            elif self.round == 5:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/warning.aspx?xklc=2&lb=3')
            else:
                self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/warning.aspx?xklc=3&lb=3')
            if self.round > 3:
                return
            read_check = WaitForElement(self.driver, By.XPATH, '//input[@type="checkbox"]')
            if not read_check.is_selected():
                read_check.click()
            continue_button = self.driver.find_element_by_xpath(u'//input[@value="继续"]')
            continue_button.click()

        except NoSuchElementException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

        except TimeoutException:
            self.error_exit(u'错误：无法获取页面元素，请检查您的网络是否畅通。')

    def locate_course_page(self):
        print u'读取到欲选课程：%s\t教师行数：%d' % (self.course_id, self.teacher_row)
        write_log('读取到欲选课程：%s，教师行数：%d' % (self.course_id, self.teacher_row))
        if self.round > 3:
            print_and_log(u'当前为小学期，无需定位。')
            return
        if self.auto_locate:
            try:
                write_log('自动定位选课页面。')
                if self.electsys_pp_on:
                    smalltable_container = WaitForElement(self.driver, By.XPATH, '//div[@id="smalltable_container"]')
                    if smalltable_container.get_attribute('style') != 'display: none;':
                        smalltable_title = self.driver.find_element_by_xpath('//div[@class="smalltable_title"]')
                        smalltable_title.click()
                        time.sleep(1)
                if self.first_category == 1:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyRequiredCourse.aspx')
                    print_and_log(u'已自动定位到：必修课。')
                elif self.first_category == 2:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyLimitedCourse.aspx')
                    submit_button = WaitForElement(self.driver, By.XPATH, u'//input[@value="选课提交"]')
                    tight_page_source = remove_white_space(self.driver.page_source)
                    result = re.findall(r'<tr[^<>]*><td[^<>]*><inputid="([^<>]*)"type="radio"[^<>]*/></td><td[^<>]*>([^<>]*)</td>', tight_page_source)
                    second_button_id = ''
                    for item in result:
                        if item[1].encode('UTF-8') == self.second_category:
                            second_button_id = item[0]
                            break
                    if second_button_id == '':
                        self.error_exit(u'错误：无效的二级分类！')
                    second_button = self.driver.find_element_by_xpath('//input[@id="%s"]' % (second_button_id))
                    second_button.click()
                    print_and_log(u'已自动定位到：限选课 ' + self.second_category.decode('UTF-8'))
                elif self.first_category == 3:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyCommonCourse.aspx')
                    submit_button = WaitForElement(self.driver, By.XPATH, u'//input[@value="选课提交"]')
                    tight_page_source = remove_white_space(self.driver.page_source)
                    result = re.findall(r'<tr[^<>]*><td[^<>]*><inputid="([^<>]*)"type="radio"[^<>]*/></td><td[^<>]*>([^<>]*)</td>', tight_page_source)
                    second_button_id = ''
                    for item in result:
                        if item[1].encode('UTF-8') == self.second_category:
                            second_button_id = item[0]
                            break
                    if second_button_id == '':
                        self.error_exit(u'错误：无效的二级分类！')
                    second_button = self.driver.find_element_by_xpath('//input[@id="%s"]' % (second_button_id))
                    second_button.click()
                    print_and_log(u'已自动定位到：通识课 ' + self.second_category.decode('UTF-8'))
                elif self.first_category == 4:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/outSpeltyEP.aspx')
                    drop_list = WaitForElement(self.driver, By.XPATH, '//select[@id="OutSpeltyEP1_dpYx"]')
                    Select(drop_list).select_by_visible_text(self.second_category)
                    second_button = WaitForElement(self.driver, By.XPATH, u'//input[@value="查 询"]')
                    second_button.click()
                    print_and_log(u'已自动定位到：任选课 ' + self.second_category.decode('UTF-8'))
                elif self.first_category == 5:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/freshmanLesson.aspx')
                    print_and_log(u'已自动定位到：新生研讨课')
                else:
                    self.error_exit(u'错误：无效的一级分类！')

            except NoSuchElementException:
                print u'错误：无法获取页面元素！\n'
                print u'这可能是以下2种原因导致的：'
                print u'(1)您输入的定位信息不正确。'
                print u'(2)网络不畅通。'
                write_log('错误：自动定位阶段无法获取页面元素。')
                self.error_exit()

            except TimeoutException:
                print u'错误：无法获取页面元素！\n'
                print u'这可能是以下2种原因导致的：'
                print u'(1)您输入的定位信息不正确。'
                print u'(2)网络不畅通。'
                write_log('错误：自动定位阶段无法获取页面元素。')
                self.error_exit()
        else:
            write_log('手动定位选课页面。')
            print u'\n请手动定位到欲选课程所在的页面，然后按 Enter 键继续...',
            raw_input()

    def check_status(self):
        try:
            max_enrollment = int(self.driver.find_element_by_xpath('//tbody/tr[%d]/td[6]' % (self.teacher_row + 1)).text)
            current_enrollment = int(self.driver.find_element_by_xpath('//tbody/tr[%d]/td[9]' % (self.teacher_row + 1)).text)
            return current_enrollment >= max_enrollment
        except:
            print_and_log(u'错误：自动选课阶段无法获取计划人数与确定人数，可能是您输入的教师行数不存在！')
            self.error_exit()

    def auto_elect_course(self):
        try:
            print u'\n开始自动刷新...'
            write_log('开始自动刷新。')
            log.flush()
            while True:
                if self.auto_relogin:
                    self.t2 = datetime.datetime.now()
                    if (self.t2 - self.t1).seconds > self.relogin_interval * 60:
                        print
                        print_and_log(u'即将自动重新登录。')
                        return False
                try:
                    course_radio = WaitForElement(self.driver, By.XPATH, '//input[@value="%s"]' % (self.course_id))
                    course_radio.click()
                except:
                    print u'错误：无法获取页面元素！\n'
                    print u'这可能是以下3种原因导致的：'
                    print u'(1)定位的页面不正确。'
                    print u'(2)您输入的课程代码不存在。'
                    print u'(3)网络不畅通。'
                    write_log('错误：自动选课阶段无法获取页面元素。')
                    self.error_exit()
                if not self.electsys_pp_on:
                    arrangement = self.driver.find_element_by_xpath(u'//input[@value="课程安排"]')
                    arrangement.click()
                try:
                    button = WaitForElement(self.driver, By.XPATH, u'//input[@value="选定此教师"]')
                except:
                    self.driver.back()
                    continue

                status = self.check_status()

                if not status:
                    result = re.findall(r'value="(\d+)"', self.driver.page_source)
                    teacher_id = result[self.teacher_row - 1]
                    teacher_radio = self.driver.find_element_by_xpath('//input[@value=%s]' % (teacher_id))
                    teacher_radio.click()
                    time.sleep(1.5)
                    select_button = self.driver.find_element_by_xpath(u'//input[@value="选定此教师"]')
                    select_button.click()
                    try:
                        submit_button = WaitForElement(self.driver, By.XPATH, u'//input[@value="选课提交"]')
                        print
                        print_and_log(u'已选定课程%s的教师。' % (self.course_id))
                        break
                    except:
                        self.driver.back()
                self.driver.back()
                time.sleep(self.sleep_time / 1000.0)
            submit_button = self.driver.find_element_by_xpath(u'//input[@value="选课提交"]')
            submit_button.click()
            print
            print_and_log(u'已提交选课%s！' % (self.course_id))
            alert_msg(u'提示', u'已提交选课%s！' % (self.course_id))
            return True

        except NoSuchElementException:
            print u'错误：无法获取页面元素！\n'
            print u'这可能是以下2种原因导致的：'
            print u'(1)定位的页面不正确。'
            print u'(2)网络不畅通。'
            write_log('错误：自动选课阶段无法获取页面元素。')
            self.error_exit()

        except TimeoutException:
            print u'错误：无法获取页面元素！\n'
            print u'这可能是以下2种原因导致的：'
            print u'(1)定位的页面不正确。'
            print u'(2)网络不畅通。'
            write_log('错误：自动选课阶段无法获取页面元素。')
            self.error_exit()

    def logout(self):
        self.driver.get('http://electsys.sjtu.edu.cn/edu/logOut.aspx')
        title = WaitForElement(self.driver, By.XPATH, '//title')
        self.logged_in = False
        print u'已登出。\n'
        try:
            write_log('已登出。')
        except:
            pass

    def error_exit(self, msg = ''):
        try:
            if msg != '':
                print_and_log(msg)
            write_log('程序遇到错误而退出。')
            log.write('\n---------------------------------------------------------\n')
            log.close()
            if self.logged_in:
                print u'\n请按 Enter 键注销本次登录并退出...',
            else:
                print u'\n请按 Enter 键退出...',
            raw_input()
        except:
            pass
        if self.logged_in:
            self.logout()
            time.sleep(1)
            self.driver.quit()
        raise SystemExit

    def success_exit(self):
        try:
            write_log('程序正常退出。')
            log.write('\n---------------------------------------------------------\n')
            log.close()
            if self.logged_in:
                print u'\n请按 Enter 键注销本次登录并退出...',
            else:
                print u'\n请按 Enter 键退出...',
            raw_input()
        except:
            pass
        if self.logged_in:
            self.logout()
            time.sleep(1)
            self.driver.quit()

def main():
    ae = AutoElectsys()
    if ae.browse_only:
        ae.login()
        ae.readme()
        print u'提示：未填写课程代码，已进入仅浏览模式。'
    else:
        while True:
            ae.login()
            ae.readme()
            ae.locate_course_page()
            if ae.auto_elect_course():
                break
            ae.logout()
            time.sleep(1)
    ae.success_exit()

if __name__ == '__main__':
    main()
