import base64
import datetime
import logging
import os
import pathlib
import re
import sys
import time
import traceback

import colorlabels as cl
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from AutoElectsysUtil import (alert_msg, config_file_name, course_rounds, dependency_dir, file_read_json,
                              file_read_lines, general_validation, is_64bit, is_mac, is_windows, log_file_name,
                              pswd_file_name, remove_utf8_bom, remove_whitespace)

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

try:
    logger = logging.getLogger('AutoElectsys')
    file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
except Exception:
    traceback.print_exc()
    cl.error('错误：无法打开或创建日志文件！')
    cl.input('请按 Enter 键退出...')
    sys.exit(1)


def print_and_log_info(msg):
    cl.info(msg)
    logger.info(msg)


def print_and_log_warning(msg):
    cl.warning(msg)
    logger.warning(msg)


if is_windows:
    webdriver_path = os.path.join(dependency_dir, 'chromedriver_win32.exe')
elif is_mac:
    webdriver_path = os.path.join(dependency_dir, 'chromedriver_mac64')
elif is_64bit:
    webdriver_path = os.path.join(dependency_dir, 'chromedriver_linux64')
else:
    webdriver_path = os.path.join(dependency_dir, 'chromedriver_linux32')


def get_user_data_dir():
    if is_windows:
        s = os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data')
    elif is_mac:
        s = os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:
        s = os.path.expanduser('~/.config/google-chrome')

    return s if os.path.isdir(s) else None


jHelper_path = os.path.join(dependency_dir, 'SJTU-jAccount-Login-Helper_v0.3.1.crx')
jHelper_id = 'ihchdleonhejkpdkmahiejaabcpkkicj'


def jHelper_installed(base_dir):
    return (pathlib.Path(base_dir) / 'Default/Extensions' / jHelper_id).is_dir()


class AutoElectsys:
    def __init__(self):
        cl.section('SJTU AutoElectsys')
        cl.progress('初始化中...')
        logger.info('启动程序。')
        self.init_config()
        self.init_webdriver()

    def init_config(self):
        self.driver = None
        self.logged_in = False
        self.electsys_pp_on = False

        try:
            remove_utf8_bom(config_file_name)
        except Exception:
            self.error_exit('错误：无法写入配置文件！')

        try:
            config = file_read_json(config_file_name)

            self.password_saved = config['Login']['password_saved']
            general_validation(isinstance(self.password_saved, bool))

            self.user_data = self.password_saved

            if self.user_data:
                self.user_data_dir = get_user_data_dir()

                if not self.user_data_dir:
                    self.error_exit('错误：找不到 Chrome 用户文件夹，请确认 Chrome 是否正常安装。', with_exc_info=False)

            self.autocaptcha_on = config['Login']['auto_captcha']
            general_validation(isinstance(self.autocaptcha_on, bool))

            self.relogin_interval = config['Login']['relogin_interval']
            general_validation(isinstance(self.relogin_interval, int) and self.relogin_interval >= 0)

            self.auto_relogin = self.relogin_interval > 0

            self.course_id = config['CourseInfo']['course_id']
            general_validation(isinstance(self.course_id, str) and re.fullmatch('[A-Za-z0-9]*', self.course_id))

            self.teacher_row = config['CourseInfo']['teacher_row']
            general_validation(isinstance(self.teacher_row, int) and self.teacher_row > 0)

            self.round = config['CourseLocate']['round']
            general_validation(isinstance(self.round, int) and self.round in range(0, 7))

            self.auto_locate = config['CourseLocate']['auto_locate']
            general_validation(isinstance(self.auto_locate, bool))

            if (not self.autocaptcha_on or not self.auto_locate) and self.auto_relogin:
                self.error_exit('无效配置项：自动重新登录需要自动识别验证码，并开启选课页面自动定位功能。', with_exc_info=False)

            if self.auto_locate:
                if self.round == 0:
                    self.error_exit('无效配置项：自动定位选课页面不支持“其他”选课轮次。', with_exc_info=False)

                self.first_category = config['CourseLocate']['first_category']
                general_validation(isinstance(self.first_category, int) and self.first_category in (1, 2, 3, 4, 5))

                if self.first_category in (2, 3, 4):
                    self.second_category = config['CourseLocate']['second_category']
                    general_validation(isinstance(self.second_category, str))

            self.sleep_time = config['Miscellaneous']['sleep_time']
            general_validation(isinstance(self.sleep_time, int) and self.sleep_time > 0)
            self.sleep_time /= 1000

            self.browse_only = self.course_id == ''
        except Exception:
            self.error_exit('错误：配置文件出现错误，请使用配置器检查并修复！')

    def init_webdriver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--log-level=3')
        options.add_argument('--disable-logging')
        options.add_argument('--silent')
        options.add_experimental_option('excludeSwitches', ['ignore-certificate-errors'])

        if self.user_data:
            options.add_argument('user-data-dir=' + self.user_data_dir)

            if self.autocaptcha_on and not jHelper_installed(self.user_data_dir):
                options.add_extension(jHelper_path)
        else:
            if self.autocaptcha_on:
                options.add_extension(jHelper_path)

        self.driver = webdriver.Chrome(webdriver_path, options=options, service_log_path=os.devnull)

        if not is_mac:  # maximize_window is buggy on macOS
            self.driver.maximize_window()

        self.wait = WebDriverWait(self.driver, 24 * 3600)  # Infinite wait.

    def get_user_and_pass(self):
        try:
            username, password = file_read_lines(pswd_file_name)
            password = base64.b85decode(password).decode()
            return username, password
        except Exception:
            self.error_exit('错误：读取账号信息文件失败！')

    def wait_for_page_load(self):
        self.wait.until(lambda driver: driver.execute_script('return document.readyState == "complete"'))

    def auto_input_captcha(self):
        try:
            for item in re.findall(r'<img src="(.*?)"', self.driver.page_source):
                if 'captcha' in item:
                    captcha_src = item
                    break
            else:
                raise NoSuchElementException

            self.driver.find_element_by_css_selector('img[src="%s"]' % captcha_src).click()
            time.sleep(0.5)
            self.driver.find_element_by_id('captcha').send_keys('\n')
            self.wait_for_page_load()
        except NoSuchElementException:
            self.error_exit('错误：自动输入验证码过程中无法获取页面元素。')

    def login(self):
        if not self.password_saved:
            username, password = self.get_user_and_pass()

        try:
            flag = True
            self.driver.get('http://electsys.sjtu.edu.cn/edu/login.aspx')

            while flag:
                if '对不起，您的Jaccount帐号没有对应交大正式学生学号或教师工号，不能登陆！' in self.driver.page_source:
                    logger.debug('登录过程中页面错误，即将重试。')
                    time.sleep(3)
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/login.aspx')
                    continue

                if not self.password_saved:
                    userbox = self.driver.find_element_by_id('user')
                    userbox.clear()
                    userbox.send_keys(username)
                    passbox = self.driver.find_element_by_id('pass')
                    passbox.clear()
                    passbox.send_keys(password)

                if self.autocaptcha_on:
                    self.auto_input_captcha()
                else:
                    cl.info('请在网页中输入验证码并登录，成功登录后程序会自动继续。')
                    self.wait.until(EC.url_contains('electsys.sjtu.edu.cn'))
                    self.wait_for_page_load()

                flag = '请正确填写验证码' in self.driver.page_source

            if self.driver.title == '上海交通大学教学信息服务网－学生服务平台':
                cl.success('成功登录教学信息服务网。')
                logger.info('成功登录教学信息服务网。')
                self.logged_in = True

                if self.auto_relogin:
                    self.t1 = datetime.datetime.now()

                self.electsys_pp_on = 'Optimized by electsys++' in self.driver.page_source
                this_handle = self.driver.current_window_handle

                # Close other windows.
                for handle in self.driver.window_handles:
                    if handle != this_handle:
                        self.driver.switch_to.window(handle)
                        self.driver.close()

                self.driver.switch_to.window(this_handle)
            else:
                self.error_exit('错误：登录教学信息服务网失败！您输入的用户名或密码可能不正确。', with_exc_info=False)
        except NoSuchElementException:
            self.error_exit('错误：登录过程中无法获取页面元素。')

    def readme(self):
        if self.round == 0:
            return

        try:
            print_and_log_info('读取到的选课轮次设置：%s。' % course_rounds[self.round])

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

            read_check = self.driver.find_element_by_css_selector('input[type="checkbox"]')

            if not read_check.is_selected():
                read_check.click()

            self.driver.find_element_by_css_selector('input[value="继续"]').click()
            self.wait_for_page_load()
        except NoSuchElementException:
            self.error_exit('错误：阅读选课提示时无法获取页面元素。')

    def locate_course_page(self):
        print_and_log_info('读取到欲选课程：%s，教师行数：%d' % (self.course_id, self.teacher_row))

        if self.round > 3:
            print_and_log_info('当前为小学期，无需定位。')
            return

        if self.auto_locate:
            try:
                logger.info('自动定位选课页面。')

                if self.electsys_pp_on:
                    smalltable_container = self.driver.find_element_by_css_selector('div[id="smalltable_container"]')

                    if smalltable_container.get_attribute('style') != 'display: none;':
                        self.driver.find_element_by_css_selector('div[class="smalltable_title"]').click()
                        time.sleep(1)

                if self.first_category == 1:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyRequiredCourse.aspx')
                    print_and_log_info('已自动定位到：必修课。')
                elif self.first_category == 2:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyLimitedCourse.aspx')
                    tight_page_source = remove_whitespace(self.driver.page_source)

                    for item in re.findall(r'<tr.*?><td.*?><inputid="(.*?)"type="radio".*?/></td><td.*?>(.*?)</td>', tight_page_source):
                        if item[1] == self.second_category:
                            second_button_id = item[0]
                            break
                    else:
                        self.error_exit('错误：无效的二级分类！', with_exc_info=False)

                    self.driver.find_element_by_css_selector('input[id="%s"]' % second_button_id).click()
                    self.wait_for_page_load()
                    print_and_log_info('已自动定位到：限选课 %s' % self.second_category)
                elif self.first_category == 3:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/speltyCommonCourse.aspx')
                    tight_page_source = remove_whitespace(self.driver.page_source)

                    for item in re.findall(r'<tr.*?><td.*?><inputid="(.*?)"type="radio".*?/></td><td.*?>(.*?)</td>', tight_page_source):
                        if item[1] == self.second_category:
                            second_button_id = item[0]
                            break
                    else:
                        self.error_exit('错误：无效的二级分类！', with_exc_info=False)

                    self.driver.find_element_by_css_selector('input[id="%s"]' % second_button_id).click()
                    self.wait_for_page_load()
                    print_and_log_info('已自动定位到：通识课 %s' % self.second_category)
                elif self.first_category == 4:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/outSpeltyEP.aspx')
                    drop_list = self.driver.find_element_by_css_selector('select[id="OutSpeltyEP1_dpYx"]')
                    Select(drop_list).select_by_visible_text(self.second_category)
                    self.driver.find_element_by_css_selector('input[value="查 询"]').click()
                    self.wait_for_page_load()
                    print_and_log_info('已自动定位到：任选课 %s' % self.second_category)
                else:
                    self.driver.get('http://electsys.sjtu.edu.cn/edu/student/elect/freshmanLesson.aspx')
                    print_and_log_info('已自动定位到：新生研讨课')
            except NoSuchElementException:
                self.error_exit('错误：自动定位阶段无法获取页面元素！您输入的定位信息可能不正确。')
        else:
            logger.info('手动定位选课页面。')
            cl.input('请手动定位到欲选课程所在的页面，然后按 Enter 键继续...')

    def check_status(self):
        try:
            max_enrollment = int(self.driver.find_element_by_xpath('//tbody/tr[%d]/td[6]' % (self.teacher_row + 1)).text)
            current_enrollment = int(self.driver.find_element_by_xpath('//tbody/tr[%d]/td[9]' % (self.teacher_row + 1)).text)
            return current_enrollment >= max_enrollment
        except Exception:
            self.error_exit('错误：自动选课阶段无法获取计划人数与确定人数，可能是您输入的教师行数不存在！')

    def auto_elect_course(self):
        try:
            cl.progress('开始自动刷新...')
            logger.info('开始自动刷新。')

            while True:
                if self.auto_relogin:
                    self.t2 = datetime.datetime.now()

                    if (self.t2 - self.t1).seconds > self.relogin_interval * 60:
                        print_and_log_info('即将自动重新登录。')
                        return False

                # Should not click, will be buggy when Electsys++ is on
                self.driver.execute_script("document.querySelector('input[value=\"%s\"]').checked = true" % self.course_id)
                self.driver.find_element_by_css_selector('input[value="课程安排"]').click()
                self.wait_for_page_load()

                try:
                    self.driver.find_element_by_css_selector('input[value="选定此教师"]')
                except NoSuchElementException:
                    logger.debug('查看课程安排时页面错误，即将重试。')
                else:
                    status = self.check_status()

                    if not status:
                        result = re.findall(r'value="(\d+)"', self.driver.page_source)
                        teacher_id = result[self.teacher_row - 1]
                        self.driver.find_element_by_css_selector('input[value="%s"]' % teacher_id).click()
                        time.sleep(2)
                        self.driver.find_element_by_css_selector('input[value="选定此教师"]').click()
                        self.wait_for_page_load()

                        try:
                            self.driver.find_element_by_css_selector('input[value="选课提交"]')
                        except NoSuchElementException:
                            logger.debug('选定教师时页面错误，即将重试。')
                            self.driver.back()
                        else:
                            print_and_log_info('已选定课程 %s 的教师。' % self.course_id)
                            break

                self.driver.back()
                time.sleep(self.sleep_time)

            time.sleep(2)
            self.driver.find_element_by_css_selector('input[value="选课提交"]').click()
            self.wait_for_page_load()
            submit_msg = '已提交选课 %s！' % self.course_id
            cl.success(submit_msg)
            logger.info(submit_msg)
            alert_msg('AutoElectsys 提示', submit_msg)
            return True
        except NoSuchElementException:
            self.error_exit('错误：自动选课阶段无法获取页面元素！定位的页面可能不正确，或您输入的课程代码不存在。')

    def logout(self, log=True):
        self.driver.get('http://electsys.sjtu.edu.cn/edu/logOut.aspx')
        self.logged_in = False

        if log:
            print_and_log_info('已登出。')

    def error_exit(self, msg, with_exc_info=True):
        if with_exc_info:
            logger.exception(msg)
            traceback.print_exc()
        else:
            logger.error(msg)

        cl.error(msg)

        logger.critical('程序遇到错误而退出。')

        if self.logged_in:
            cl.input('请按 Enter 键注销本次登录并退出...')
            self.logout(log=False)
            time.sleep(1)
        else:
            cl.input('请按 Enter 键退出...')

        if self.driver:
            self.driver.quit()

        sys.exit(1)

    def success_exit(self):
        logger.info('程序正常退出。')

        if self.logged_in:
            cl.input('请按 Enter 键注销本次登录并退出...')
            self.logout(log=False)
            time.sleep(1)
        else:
            cl.input('请按 Enter 键退出...')

        self.driver.quit()


def main():
    ae = AutoElectsys()

    if ae.browse_only:
        ae.login()
        ae.readme()
        cl.info('提示：未填写课程代码，已进入仅浏览模式。')
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
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_and_log_warning('用户中断程序。')
        cl.input('请按 Enter 键退出...')
    except Exception:
        traceback.print_exc()
        cl.error('发生未预期的错误')
        logger.exception('未预期的错误')
        cl.input('请按 Enter 键退出...')
