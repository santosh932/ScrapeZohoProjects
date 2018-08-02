# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import getpass
import time
import json
import csv
import itertools

driver = None
baseurl = "" #zoho projects login page URL`
username = "" #username
password =  "" #password

xpaths = { 'usernameTxtBox' : '//*[@id="lid"]',
           'passwordTxtBox' : '//*[@id="pwd"]',
           'submitButton' :   '//*[@id="signin_submit"]'
           }

def scroll_to_bottom():
    # Scroll down till the end of the page
    SCROLL_PAUSE_TIME = 1
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    # print('scrolling to bottom. Current height : {0}'.format(last_height))
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        # print('new height : {0}'.format(new_height))
        if new_height == last_height:
            break
        last_height = new_height

def get_tasks_for_project(project_id):
    project_url = "https://projects.zoho.com/portal/magmagroup#plainview/{0}/customview/0".format(project_id)
    driver.get(project_url)
    time.sleep(2)
    scroll_to_bottom()

    tasks_div = driver.find_elements_by_css_selector('.bugown3.pt10.pb12.titleminmax.bdrbtm5')
    tasks =[]
    for task_div in tasks_div:
        task_detail = {}
        task_detail['link'] = task_div.find_element_by_tag_name('a').get_attribute('href')
        task_detail['title'] = task_div.find_element_by_tag_name('a').get_attribute('title').encode("utf-‌​8")
        task_detail['id'] = task_div.find_element_by_css_selector('.pr3.col666.pointer').get_attribute('innerHTML')
        task_detail['uid'] = task_div.find_element_by_tag_name('a').get_attribute('id').split('_')[-1]
        task_detail['owners'] = driver.find_element_by_id("towner_{0}".format(task_detail['uid'])).get_attribute('innerHTML').encode("utf-‌​8")
        task_detail['status'] = driver.find_element_by_id("CUSTOM_STATUSID_{0}".format(task_detail['uid'])).find_element_by_tag_name('span').find_element_by_tag_name('span').get_attribute('innerHTML').encode("utf-‌​8")
        task_detail['creation_date'] = '' #TBD
        task_detail['severity'] = '' #TBD Priority
        # print(task_detail)
        tasks.append(task_detail)
    return tasks

def get_issues_for_project(project_id):
    # https://projects.zoho.com/portal/magmagroup#bugsview/1205116000000120005/0
    project_url = "https://projects.zoho.com/portal/magmagroup#bugsview/{0}/0".format(project_id)

    driver.get(project_url)
    time.sleep(2)
    scroll_to_bottom()
    print('loaded Issues page')
    issues_divs = driver.find_elements_by_css_selector('.tdout')
    issues =[]
    for issue_div in issues_divs:
        issue_detail = {}
        issue_id = issue_div.get_attribute('id').split('_')[-1]
        issue_title_id = 'bugtitle_{0}_{1}'.format(issue_id,project_id)
        bug_sub = 'bugsub_{0}'.format(issue_id)

        issue_detail['uid'] = issue_id
        issue_detail['link'] = issue_div.find_element_by_id(issue_title_id).get_attribute('href')
        issue_detail['id'] = issue_div.find_element_by_id(issue_title_id).get_attribute('innerHTML')
        issue_detail['title'] = issue_div.find_element_by_id(bug_sub).get_attribute('innerHTML').encode("utf-‌​8")
        issue_detail['creation_date'] = issue_div.find_element_by_id('zbugcreatedon')
        try:
            issue_detail['status'] = issue_div.find_element_by_id('status_span_{}'.format(issue_id)).get_attribute('title')
        except:
            issue_detail['status'] = 'Failed to extract'
        issue_detail['severity'] = issue_div.find_element_by_id('severity_span_{}'.format(issue_id)).get_attribute('innerHTML')
        issue_detail['owners'] = '' #TBD
        issues.append(issue_detail)
    return issues

def get_projects():
  global driver
  driver = webdriver.Chrome()
  executor_url = driver.command_executor._url
  session_id = driver.session_id
  driver.get(baseurl)
  time.sleep(2)
  driver.find_element_by_xpath(xpaths['usernameTxtBox']).send_keys(username)
  driver.find_element_by_xpath(xpaths['passwordTxtBox']).send_keys(password)
  driver.find_element_by_xpath(xpaths['submitButton']).click()
  print "Login Sucessfull"

  time.sleep(10) #page loads slowly

  elems = driver.find_elements_by_css_selector('.projNmetxt.w98per.pl5.fl.pointer.h20.lh20.bugoflowh')
  print("count of projects : {0}".format(len(elems)))
  projs = {}
  for elem in elems:
      proj = {}
      proj['uid'] = elem.get_attribute("href").split("/")[-1]
      proj['name'] = elem.get_attribute('innerHTML').split("</span>")[-1].encode("utf-‌​8")
      proj_id =  elem.find_element_by_tag_name("span").get_attribute('innerHTML')
      projs[proj_id] = proj
      # break;
  #print(projs)

  print("count of unique projects : {0}".format(len(projs)))

  for proj_id, proj in projs.items():
      print('Fethcing tasks for project {0} : {1}'.format(proj['uid'],proj['name']))
      tasks = get_tasks_for_project(proj['uid']) #tryingt with one project, should be done for all in a loop
      print('found {0} tasks'.format(len(tasks)))
      proj['tasks'] = tasks
      print('Fetching issues for project {0} : {1}'.format(proj['uid'],proj['name']))
      # issues = get_issues_for_project(proj['uid'])
      issues = get_issues_for_project(proj['uid'])
      print('found {0} issues'.format(len(issues)))
      proj['issues'] = issues
      # break;

  # print(projs)

  # with open('zoho_projects_data.json', 'w') as fp:
  #      json.dump(projs, fp,indent=2)

  keys = ['project_id','project_name','ticket_type'] + projs[projs.keys()[0]]['tasks'][0].keys()
  with open('zoho_tickets.csv', 'w') as fp:
      dict_writer =csv.DictWriter(fp,keys,quoting=csv.QUOTE_ALL)
      dict_writer.writeheader()
      for proj_id, proj in projs.items():
          proj_detail = {"project_id":proj_id, "project_name":proj['name'], "ticket_type" : 'TASK'}
          dict_writer.writerows([dict(itertools.chain(proj_detail.items(),a.items())) for a in proj['tasks']])
          proj_detail = {"project_id":proj_id, "project_name":proj['name'], "ticket_type" : 'ISSUE'}
          dict_writer.writerows([dict(itertools.chain(proj_detail.items(),a.items())) for a in proj['issues']])

get_projects()
