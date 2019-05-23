#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 19:34:25 2019

@author: chenliwei
"""

'''
    将user_agent的list存储在本地txt,并将cookies的dictionary也存储在本地。读取user_agent和cookies。
    将weibo用户的姓名、编码、containerid和end_page等属性存储在本地txt，不同属性空格隔开，不同用户换行隔开
    读取上述相应材料，利用requeat.post进行内容抓取。
    对于抓去失败页面存储在本地txt，在最后再进行一次抓取。

'''

import requests,re,time,random,numpy,ast,gc
from urllib.parse import urlencode
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#name=['发表时间','发表内容','转发来源','转发内容','转发数','评论数','点赞数']
base_url="https://m.weibo.cn/api/container/getIndex?"
link_list=[]
#sergaent
  
def get_weibo_cookies(driver):
    cookie_list=[]
    url='https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F'
    user_dic={

            }
    for key in user_dic:
        username=key
        password=user_dic[key]
        print(key,user_dic[key])
        
        driver.get(url)
        driver.implicitly_wait(10)
        driver.find_element_by_xpath('//*[@id="loginName"]').clear()
        driver.find_element_by_xpath('//*[@id="loginName"]').send_keys(username)
        driver.find_element_by_xpath('//*[@id="loginPassword"]').clear()
        driver.find_element_by_xpath('//*[@id="loginPassword"]').send_keys(password)
        driver.find_element_by_xpath('//*[@id="loginPassword"]').send_keys(Keys.ENTER)
        time.sleep(20)
        driver.get('https://m.weibo.cn/status/4364192750865299')
        cookies=driver.get_cookies()
        ret={}
        for cookie in cookies:
            cookie_name=cookie['name']
            cookie_value=cookie['value']
            ret[cookie_name]=cookie_value
    #        ret=ret + cookie_name + "=" + cookie_value +";"
        print(ret)
        if len(ret)>5:
            cookie_list.append(ret)
        else:
            continue
        time.sleep(3)
    file=open('/Users/chenliwei/Desktop/mac2/文件/cookies_list.txt','w')
    for item in cookie_list:       
        file.write(str(item)+'\n')
    file.close()
    return cookie_list

def get_user_agent():
    user_agent_list=[]
    user_agent_file=open('/Users/chenliwei/Desktop/mac2/文件/user_agent.txt','r',encoding='utf-8')
    for line in user_agent_file:
        line=line.replace('\n','')
        user_agent_list.append(line)
    user_agent_file.close()
    return user_agent_list
        
def get_cookies_list():
    cookie_list=[]
    password=input('是否要重新获取cookies:')
    if password == '是': 
        driver=webdriver.Chrome()
        cookie_list=get_weibo_cookies(driver)
        driver.quit()
    else:
        cookies_file=open('/Users/chenliwei/Desktop/mac2/文件/cookies_list.txt','r',encoding='utf-8')
        for line in cookies_file:
            line=line.replace('\n','')
            dic_line=ast.literal_eval(line)
            cookie_list.append(dic_line)
        cookies_file.close()
    return cookie_list

def get_page(page,header,containerid,cookies):#构造url，注意主页containerid与微博是不同的
    prames={
           "containerid":containerid,#手动获取相应博主内容的api接口容器id
           "page_type":"03",
           "page":page
    }
    url=base_url + urlencode(prames)#url
    try:#网络状态差，多次请求
        response = requests.post(url, headers=header,timeout=10)#请求获取网页
        if response.status_code == 200:
            return response.json()
        else:
            for node in range(1,3):
                print('请求超时了，第%s次重复请求' % node)
                time.sleep(40)
                response = requests.post(url, headers=header,cookies=cookies,timeout=15)
                if response.status_code == 200:
                    return response.json()        
    except:
        for x in range(1, 2):
            print('请求超时，第%s次重复请求' % x)
            time.sleep(100)
            response = requests.post(url, headers=header,cookies=cookies,timeout=15)
            if response.status_code == 200:
                return response.json()
    return -1  # 当所有请求都失败，返回  -1  ，此时有极大的可能是网络问题或IP被封。

def prase_date(res_json,header,cookies,interrupted_list,file2,t_list):#解析数据
#    time.sleep(random.uniform(1,2))   #休息时间1
    for item in res_json['data']['cards']:
        if 'mblog' in item:
            new=[]
            ti=item['mblog']['created_at']
            attitude=item['mblog']['attitudes_count']
            comment=item['mblog']['comments_count']
            repost=item['mblog']['reposts_count']
            original_text=item['mblog']['text']
            
            if '>全文</a>'in original_text:            #如果评论需要展开全文
                link=re.findall(r'\/status\/([0-9]+)',original_text)
                txt_url='http://m.weibo.cn/statuses/extend?id='+link[0]
                txt_response=requests.post(txt_url,headers=header,cookies=cookies)#构造展开全文url
                if txt_response.status_code == 200: #检查是否触发微博反扒冷却机制
                    txt_res_json=txt_response.json()
                    if 'msg' in txt_res_json:   #检查是否cookies登陆成功
                        print(header,cookies)
                        print('抓取失败，全文网址是：',txt_url)
                        interrupted_list.append(txt_url)
                        interrupted_list.append(txt_url)
                    else:
                        original_text=txt_res_json['data']['longTextContent']

                else:
                    print('全文网络连接失败，位置：',txt_url)
                    print(header,cookies)
                    interrupted_list.append(txt_url)
                    original_text=txt_url
                    time.sleep(180) #等待微博反扒冷却机制

            #判定是否有转发，防止keyerror错误        
            if 'retweeted_status' in item['mblog']and item['mblog']['retweeted_status']['user'] != None:
                retweeted_name=item['mblog']['retweeted_status']['user']['screen_name']
                file2.write(retweeted_name+'\n')
                original_retweeted_txt=item['mblog']['retweeted_status']['text']
                #如果需要展开全文，点击后提取文本
                if '>全文</a>'in original_retweeted_txt:
                    link=re.findall(r'\/status\/([0-9]+)',original_retweeted_txt)
                    retweeted_url='http://m.weibo.cn/statuses/extend?id='+link[0]
                    retweeted_response=requests.post(retweeted_url,headers=header,cookies=cookies)#构造转发url
                    if retweeted_response.status_code == 200: #检查是否绕过微博反扒冷却机制
                        retweeted_res_json=retweeted_response.json()
                        #检查是否需要登陆后查看
                        if 'msg' in retweeted_res_json:
                            print('转发网址是：',retweeted_url)
                            print(header,cookies)
                            interrupted_list.append(retweeted_url)
                            original_retweeted_txt=retweeted_url
                        else:
                            original_retweeted_txt=retweeted_res_json['data']['longTextContent']
                    else:
                        print('转发网络连接失败，网址：',retweeted_url)
                        print(header,cookies)
                        interrupted_list.append(retweeted_url)
                        original_retweeted_txt=retweeted_url
                        time.sleep(180) #等待微博反扒冷却机制
            else:
                retweeted_name=''
                original_retweeted_txt=''
    
            #存储进入数据库
            ab_txt='a'+original_text+'//<b' #对评论内容进行处理，提取出评论艾特关系和评论内的转发关系
            ab_text=ab_txt.split('//<',3) 
            direct_name=re.findall("<a href='/n/(.*?)'>",ab_text[0]) #评论艾特关系
            direct_text=ab_text[0].replace('a','',1)
            direct_retweeted_name=re.findall("a href='/n/(.*?)'>",ab_text[1],flags=0) #评论转发关系
            
            new.append(ti)
            new.append(direct_text)
            new.append(original_text)
            new.append(retweeted_name)
            new.append(original_retweeted_txt)
            new.append(repost)
            new.append(comment)
            new.append(attitude)

            if new not in t_list:
                t_list.append(new)
            
            for name in direct_name:
                file2.write(name+'\n')
            if len(direct_retweeted_name) !=0:   
                file2.write(direct_retweeted_name[0]+'\n')
            print(ti)
        else:
            print('页面不存在')
#    time.sleep(random.uniform(3,4))

def get_interrupted_txt(interrupted_list,t_list):#通过chromedriver登录方法获取获取失败的内容

    header={
    'host':'m.weibo.cn',
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1',
    'Accept':'image/webp,image/apng,image/*,*/*;q=0.8'
    }  
    url='https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F'
    driver=webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(5)
    driver.find_element_by_xpath('//*[@id="loginName"]').clear()
    driver.find_element_by_xpath('//*[@id="loginName"]').send_keys('13122343606')
    driver.find_element_by_xpath('//*[@id="loginPassword"]').clear()
    driver.find_element_by_xpath('//*[@id="loginPassword"]').send_keys('clw147258369')
    driver.find_element_by_xpath('//*[@id="loginPassword"]').send_keys(Keys.ENTER)
    time.sleep(5)
    driver.get('http://m.weibo.cn/statuses/extend?id=4114867936344029')
    cookies=driver.get_cookies()
    ret={}
    for cookie in cookies:
        cookie_name=cookie['name']
        cookie_value=cookie['value']
        ret[cookie_name]=cookie_value
    interrupted_txt={}
    try:   
        for interrupted_url in interrupted_list:
            print(interrupted_url)
            try:
                response=requests.post(interrupted_url,headers=header,cookies=ret)
                if response.status_code == 200:
                    txt_res_json=response.json()
                    if 'msg' in txt_res_json:   #检查是否需要登陆后查看
                        print('登陆失败，全文网址是：',interrupted_url,'\n用户隐私设置，无权查看')
                        txt=''
                    else:
                        txt=txt_res_json['data']['longTextContent']
                else:
                    print('页面获取失败，网址是',interrupted_url)
                    txt=input('请输入页面内容')

                print(txt)
            except:
                txt=''
            interrupted_txt[interrupted_url]=txt
            print(txt)
        for key in interrupted_txt:
            for item in t_list:
                for y in item:
                    if key == y:
                        print(y)
                        item[item.index(y)]=interrupted_txt[key]
                    else:
                        continue

    except:
        print('断点网址获取失败')
        pass
            
def connection_count(name):#网络关系统计 
    segments=[]
    for line in open('/Users/chenliwei/Desktop/mac2/数据/%s.txt'%name,'r',encoding='utf-8'):  
        line=line.replace('\n','')
        if line != name and len(line)> 0:  #计数要不要加入自己？
            segments.append(line)
    segmentDF = pd.DataFrame({'segment':segments})
    df = segmentDF.groupby("segment")["segment"].agg({"计数":numpy.size}).sort_values(by="计数",ascending=0)
    print(df.head(30))
    df.to_csv('/Users/chenliwei/Desktop/mac2/数据/%s计数.csv'%name,header=None)

def save_excel(name,t_list):#数据存储
    excel_data=pd.DataFrame(data=t_list)
    excel_data.to_excel('/Users/chenliwei/Desktop/mac2/数据/%s.xlsx'%name,encoding="utf_8_sig",sheet_name='Sheet1',header=None)
    print('Congratulations!\n终于爬完了\n累死我了！！！\n请查看！！！')
    

def main():

    user_agent_list=get_user_agent()
    cookies_list=get_cookies_list()
    print(user_agent_list,cookies_list)
    basic_weibouser_file=open('/Users/chenliwei/Desktop/mac2/文件/basic_weibouser_file2.txt','r',encoding='utf-8')
    for line in basic_weibouser_file:
        print(line)
        basic_list=line.split()
        i=0
        t_list=[]
        interrupted_list=[]
        name=basic_list[0]
        containerid=basic_list[2]
        end_page=1+int(basic_list[3])
        start_page=1
        for page in range(start_page,end_page):
            time.sleep(0.2)
            file2=open('/Users/chenliwei/Desktop/mac2/数据/%s.txt'%name,'a+',encoding='utf-8') 
            random_number=random.randint(0,len(cookies_list)-1)
            user_agent=user_agent_list[random_number]
            cookies=cookies_list[random_number]
            header = {
                    'host':'m.weibo.cn',
                    'User-Agent':user_agent,
                    'X-Requested-With': 'XMLHttpRequest'
                    }
            print('页面',page)
            i=i+1
            try:            
                res_json=get_page(page,header,containerid,cookies)
                prase_date(res_json,header,cookies,interrupted_list,file2,t_list)
                file2.close()
            except:
                print('抓取失败')
                f=open('/Users/chenliwei/Desktop/mac2/数据/%s断面.txt'%name,'a+',encoding='utf-8')
                f.write(str(page)+'\n')
                f.close()
            if i % 1000 ==0:
                time.sleep(100)
                print('爬到%s/%s页'%(page,end_page))   
            file2.close()
        try:#获取获取页面失败的页面内容
            page_file=open('/Users/chenliwei/Desktop/mac2/数据/%s断面.txt'%name,'r',encoding='utf-8')
            for line in page_file:
                random_number=random.randint(0,len(cookies_list)-1)
                user_agent=user_agent_list[random_number]
                cookies=cookies_list[random_number]
                header = {
                        'host':'m.weibo.cn',
                        'User-Agent':user_agent,
                        'X-Requested-With': 'XMLHttpRequest'
                        }
                try: 
                    page=line
                    print('正在抓取断点页面:'+str(page))
                    res_json=get_page(page,header,containerid,cookies)
                    prase_date(res_json,header,cookies,interrupted_list,file2,t_list)
                    file2.close()
                    print('获取成功')
                except:
                    print('获取失败')
                    continue
            page_file.close()
        except:
            pass
        print(name)
        if len(interrupted_list) > 0:
            get_interrupted_txt(interrupted_list,t_list)
        else:
            print('没有断点页面，跳过')

        save_excel(name,t_list)
        connection_count(name)
        gc.collect()
        print('请查看！！！')
        time.sleep(20)


    
if __name__ == '__main__':
	main()  

