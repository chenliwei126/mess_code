#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 14:56:40 2019

@author: chenliwei
"""
#from nltk.stem.wordnet import WordNetLemmatizer
import re,jieba,xlrd
from tqdm import tqdm
from gensim import corpora
from gensim import models
import matplotlib.pylab as plt
import zhon.hanzi as hanzi

#设置英文的删除词汇,并添加新中文删除词汇
#stop = set(stopwords.words('english'))#注意是words不是word，这一步是删除各种冠词、指示代词、介词！！！注意仅限于英文

#设置中文的删除词汇
#stop=[stop.add(word.strip()) for word in open()
#stop2 = dt.LoadStopwords("stopwords.txt")
f = open(r"/Users/chenliwei/Desktop/主题模型/中文停用词.txt",'r',encoding = 'UTF-8')
stopwords_n = f.readlines()
f.close()  
#设置中文的停用词
stopwords = [sw.strip().replace('\n','') for sw in stopwords_n]
stopwords.append('…')
stopwords.append('...')

#定义存储空间
# real_text_raw=[]
user_name=set()

def seg_text(doc):
    pat_uid = re.compile(u"@[a-zA-Z0-9一-龥-_]{2,30}")
    doc = pat_uid.sub('', doc) 
  #  doc=re.sub('@.*?:','',doc) #没有必要再处理一次了
    doc=re.sub("【.*?】",'',doc)
    doc = re.sub('#.*?#','',doc)
    # remove user name before tokenizing
   # doc = re.compile("(http:)[a-zA-Z0-9\.\\\\]{0,}").sub('', doc) #删除短链接，但是这里没有必要
    ## remove short urls
    tokens = jieba.cut(doc)
    tokens = [el for el in tokens if len(el) > 1] 
    ## remove single character
    tokens = [el for el in tokens if el not in hanzi.punctuation] #删除标点
    ## remove Chinese punctuation
    pat_num = re.compile("[0-9a-zA-Z]{1,}")
    tokens=[el for el in tokens if pat_num.sub('', el) != ''] #删除空格
    cutResult=[el for el in tokens if el not in stopwords] #删除停顿词语
   #cutResult=[el for el in tokens if el not in user_name] #删除用户名，但是因为上面已经处理了，所以觉得没必要
    return cutResult
    

def get_index_and_name_list(community_num,user_name):#获取对应社群的用户index和name，从而得到微博保存文件名
    new=[]
    readbook=xlrd.open_workbook('/Users/chenliwei/Desktop/新的数据处理代码/userinfo.xlsx')
    sheet=readbook.sheet_by_name('Sheet1')
    nrows=sheet.nrows
    for nrow in range(0,nrows):
        index=sheet.cell(nrow,0).value
        name=sheet.cell(nrow,1).value
        com=sheet.cell(nrow,2).value
        if com == community_num:  #node2还是node3
            new_str=str(index)+str(name)
            print(new_str)
            new.append(new_str)
#            new_f=open('/Users/chenliwei/Desktop/total/%s计数.csv'%index)#添加用户名set ，以删除用户名
#            for line in new_f:
 #               line=line.strip().split(',')
#                line=jieba.cut(line[0])
#                for i in line:
#                user_name.add(line[0])
#            new_f.close()
#    f.close()
    return new
   
def get_all_text(index_and_name_list,cut_documents,user_name):#获取所有的微博内容
    for index_and_name in index_and_name_list:
        print('\n'+index_and_name)
        new=[]
        readbook=xlrd.open_workbook(r"/Users/chenliwei/Desktop/total/%s.xlsx"%index_and_name)       
#        readbook=xlrd.open_workbook(r"/Users/chenliwei/Desktop/total/0302魚躍于淵Y4.xlsx")
#        sheet = readbook.sheet_by_index(1)       #index out of range
        sheet = readbook.sheet_by_name('Sheet1')#名字的方式获取
        nrows = sheet.nrows
        for row in tqdm(range(0,nrows)):
            if '2018' in str(sheet.cell(row,1).value):
                tweet = sheet.cell(row,2).value#获取i行3列的表格值，包含别人的评论转发
                retweet = sheet.cell(row,4).value #第i行第五列，即转发内容
                line=str(tweet)+str(retweet)
                if type(line) is float or type(line) is int:
                    pass
                else:  
    #                if '女' in line or '男' in line:   #注意筛选条件
                    linelist=seg_text(line) 
                new.extend(linelist)
        cut_documents.append(new)


def save_documents(cut_documents,community_num):
    f=open('/Users/chenliwei/Desktop/新的数据处理代码/LDA/%s_community.txt'%community_num,'w',encoding='utf-8')#存储内容
    for doc in cut_documents:
        doc=' '.join(doc)  
        f.write(doc+'\n')
    f.close()

def shape_best_model(weibo,dictionary,best_topic,community_num):
    lda = models.LdaModel(corpus=weibo, num_topics=best_topic, id2word=dictionary, 
                               chunksize=100, passes= 2)
#    Idamodel=Lda(corpus=weibo,num_topics=5,id2word=dictionary,passes=2,chunksize=100)
    print(lda.print_topics())
    f=open('/Users/chenliwei/Desktop/新的数据处理代码/话题模型结果/%s_%s.txt'%(int(community_num),best_topic),'w',encoding='utf-8')
    for item in lda.print_topics():
        f.write(str(item)+'\n')
    f.close()
    return lda

def get_umass(corpus, num_topics, dictionary):#计算话题一致性指标
    mod = models.LdaModel(corpus=corpus, num_topics=num_topics, id2word=dictionary)
    cm = models.CoherenceModel(model=mod, corpus=corpus, dictionary=dictionary, coherence="u_mass")
    umass = cm.get_coherence()
    return umass


def umass_plot(k,umass,community_num):#将一致性指标画图
    plt.plot(k, umass, "k-o")
    plt.xlabel("number of topics")
    plt.ylabel("umass")
    plt.savefig('/Users/chenliwei/Desktop/新的数据处理代码/社群图表/%s.png'%community_num)
    plt.show()
    
def main():
    community_num=float(input('请输入社群编号：'))  #注意更改社区编码
    index_and_name_list=get_index_and_name_list(community_num,user_name)
    print(index_and_name_list)
    cut_documents=[]
    get_all_text(index_and_name_list,cut_documents,user_name)
    
    save_documents(cut_documents,community_num)
    dictionary = corpora.Dictionary()
    dictionary.add_documents(cut_documents)
    weibo=[dictionary.doc2bow(doc) for doc in cut_documents]
    construction=input('是否需要计算话题一致性（是/否）：')
    if construction == '是':
        k = [1, 2, 3, 4, 5,6,7,8,9,10]
        umass = [get_umass(weibo, _, dictionary) for _ in k]
        umass_plot(k,umass,community_num)
        best_topic=input('best_topic_number is :')
        shape_best_model(weibo,dictionary,best_topic,community_num)
    x = input('是否需要再拟合一个话题（是/否）:')
    if x == '是':
        best_topic=input('best_topic_number is :')
        shape_best_model(weibo,dictionary,best_topic,community_num)
    x = input('是否需要再拟合一个话题（是/否）:')
    if x == '是':
        best_topic=input('best_topic_number is :')
        shape_best_model(weibo,dictionary,best_topic,community_num)
        
    del cut_documents
    del dictionary
    del weibo
    
main()

