# pythonReloadJavaProject
python重启java项目
场景：公司有一个java项目不太稳定，经常会挂，是一个已上线的项目，暂时还没找到挂掉的原因。现在想我写一个脚本，当java项目挂掉的时候可以自动重启它，并短信通知。另外，有可能是要部署项目，这时不用重启，报警。重启的项目可能是多个。短信的模板可以配置。   
所以，我要实现的功能有：   
>1.自动重启   
>2.发送短信   
>3个配置文件 
> >3.1配置是否在部署项目，不用通知。
>>3.2多个重启项目的配置信息。
>>3.3短信模板的配置。  

怎么判断java项目是不是挂了？可以用python的requests模块去访问它的接口，看是否超时，规定超过多少次超时就认为它挂掉了。所以python程序的流程图是这样的   
![](https://upload-images.jianshu.io/upload_images/19597329-a444d5c73a658b4a.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

用到的环境   
>1.系统:Linux version 3.10.0-862.14.4.el7.x86_64 (mockbuild@kbuilder.bsys.centos.org) (gcc version 4.8.5 20150623 (Red Hat 4.8.5-28) 
>2.python3.6(3.7要升级一些东西，建议用3.6版本的)，centos安装python3.6的方法。   
[https://www.jianshu.com/p/e88e0e2d5a69](https://www.jianshu.com/p/e88e0e2d5a69)   
>3.安装完python后，需要安装一些包。   
pip install requests -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://links.jianshu.com/go?to=https%3A%2F%2Fpypi.tuna.tsinghua.edu.cn%2Fsimple)   
pip install aliyun-python-sdk-core-v3 (发短信会用到)   
注意pip安装是啥版本的,要3的   
 
项目的结构如下   
![](https://upload-images.jianshu.io/upload_images/19597329-a48d5bcd5b1ca8f8.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**开始写代码**
配置文件projectMessage：
中间用\$分割，可配置多个项目   
java项目访问地址端口\$重启java项目的命令\$项目名称（发短信要用到的） 
   


	{
	    "requestUrlsAndJarPath": ["http://127.0.0.1:8123$/usr/bin/sh /opt/jar/read/startService.sh$项目名称1","http://127.0.0.1:8666$/usr/bin/sh /opt/jar/adSystem/startService.sh$项目名称1"]
	}


配置文件shortMessage,这里用的是阿里云短信平台：


	{
	    "SignName":"网络公司",
	    "PhoneNumbers":["164651895255$小新"],
	    "TemplateCode":"SMS_561955852",
	    "ACCESSKEYID":"LTAIpLOA7dOIniun",
	    "ACCESSSECRET":"stO4jIiUyPgNwWXEDUdxHr6j98ebKC",
	    "TemplateParam":{"returnDomain": ""}
	}
	 

配置文件runConfig：   
1启用重启和发短信，其他不启用。

	{
	    "run": ["http://127.0.0.1:8123$1","http://127.0.0.1:8666$1"]
	}

要引入的模块

	from aliyunsdkcore.client import AcsClient
	from aliyunsdkcore.request import CommonRequest
	import requests
	import time
	import os
	import logging
	import datetime
	import json
	import threading


初始化并创建日志文件


	# filename：设置日志输出文件，以天为单位输出到不同的日志文件，以免单个日志文件日志信息过多，
	# 日志文件如果不存在则会自动创建，但前面的路径如log文件夹必须存在，否则会报错
	log_file = '/opt/python_file/py_web_%s.log' % datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
	# log_file = '/opt/python_file/py_web.log'
	# level：设置日志输出的最低级别，即低于此级别的日志都不会输出
	# 在平时开发测试的时候可以设置成logging.debug以便定位问题，但正式上线后建议设置为logging.WARNING，既可以降低系统I/O的负荷，也可以避免输出过多的无用日志信息
	log_level = logging.INFO
	# format：设置日志的字符串输出格式
	log_format = '%(asctime)s[%(levelname)s]: %(message)s'
	logging.basicConfig(filename=log_file, level=logging.INFO, format=log_format)
	logger = logging.getLogger()

   
要用到的一些工具函数

	# 将配置文件读取并转换成json格式数据返回
	def changeReadFileToJson(path):
	    with open(path,encoding="UTF-8") as file_object:
	        contends = file_object.read()
	    return json.loads(contends)

	# --------发送短信--------
	def send_sms(shortMessageConfig,projectName):
	    logging.info("进入发送短信")
	    PhoneNumbers = shortMessageConfig.get("PhoneNumbers")
	    SignName = shortMessageConfig.get("SignName")
	    TemplateParams = shortMessageConfig.get("TemplateParam")
	    logging.info("TemplateParams1"+str(TemplateParams))
	    for templateParam in TemplateParams:
	        TemplateParams[templateParam] = TemplateParams[templateParam] = projectName
	    logging.info("TemplateParams2"+str(TemplateParams))
	    TemplateCode = shortMessageConfig.get("TemplateCode")
	    ACCESSKEYID = shortMessageConfig.get("ACCESSKEYID")
	    ACCESSSECRET = shortMessageConfig.get("ACCESSSECRET")
	    for PhoneNumber in PhoneNumbers:
	        # client = AcsClient('<accessKeyId>', '<accessSecret>', 'default')
	        client = AcsClient(ACCESSKEYID, ACCESSSECRET, 'default')
	        request = CommonRequest()
	        request.set_accept_format('json')
	        request.set_domain('dysmsapi.aliyuncs.com')
	        request.set_method('POST')
	        request.set_protocol_type('https')  # https | http
	        request.set_version('2017-05-25')
	        # 以上部分是公用的不变
	        request.set_action_name('SendSms')
	        # set_action_name 这个是选择你调用的接口的名称，如：SendSms，SendBatchSms等
	        request.add_query_param('RegionId', "default")
	        # 这个参数也是固定的
	        try:
	            request.add_query_param('PhoneNumbers', str(PhoneNumber).split("$")[0])  # 发给谁
	        except Exception as e:
	            pass
	        request.add_query_param('SignName', SignName)  # 签名
	        request.add_query_param('TemplateCode', TemplateCode)  # 模板编号
	        request.add_query_param('TemplateParam', f"{TemplateParams}")  # 发送验证码内容
	        response = client.do_action_with_exception(request)
	        logging.info(str(response, encoding='utf-8'))
	        return str(response, encoding='utf-8')


全局变量   

	#读取配置文件
	#短信配置信息
	shortMessageConfig = changeReadFileToJson("./config/shortMessage")
	#项目配置信息
	projectMessageConfig = changeReadFileToJson("./config/projectMessage")


主要逻辑

	def doListen(projectMessage,shortMessageConfig):
	    requestUrl = projectMessage.split("$")[0]
	    jarUrl = projectMessage.split("$")[1]
	    projectName = projectMessage.split("$")[2]
	    logging.info("projectName:"+projectName)
	
	    # 起始时间戳
	    time1 = time.time()
	    #是否已经发送短信的标志
	    send = 0
	    while True:
	        i = 0
	        while i<=3:
	            try:
	                time.sleep(5)
	                r = requests.get(requestUrl, timeout=(3, 5))
	                if r.status_code == 200:
	                    time2 = time.time()
	                    #每20分钟打印成功的日志
	                    if time2 - time1 >= 1200 or send == 1:
	                        logging.info(requestUrl +"  服务器正常")
	                        logging.info(requestUrl +"  访问结果"+str(r.status_code))
	                        time1 = time2
	                    i = 4
	                    send = 0
	                    continue
	                else:
	                    if send == 0:
	                        logging.info(requestUrl +"  访问结果："+str(r.status_code)+"-当前次数" + str(i) + "次")
	                    else:
	                        time2 = time.time();
	                        if time2 - time1 >= 1200:
	                            logging.info(requestUrl +"  服务器未启动")
	                            logging.info(requestUrl +"  访问结果：" + str(r.status_code))
	                            time1 = time2
	                    i = i + 1
	                if i >= 4 and send == 0:
	                    runConfig = changeReadFileToJson("./config/runConfig")
	                    runs = runConfig.get("run")
	                    nowRun = 1
	                    for run in runs:
	                        adress = run.split("$")[0]
	                        if adress == requestUrl:
	                            nowRun = run.split("$")[1]
	                    if nowRun == 1:
	                        logger.info(requestUrl + "  检测到服务挂了，重启服务！！！")
	                        os.system(jarUrl)
	                        logger.info(requestUrl + "  短信通知！！！")
	                        send_sms(shortMessageConfig,projectName)
	                    else:
	                        logger.info(requestUrl + "  正在部署，不用重启")
	                        time.sleep(5)
	                        i = 0
	                        break
	
	                    send = 1
	                    i = 0
	                    break
	            except Exception as e:
	                i = i + 1
	                if send == 0:
	                    logging.info(requestUrl +"  访问结果：超时" + str(i)+"次")
	                else:
	                    time2 = time.time();
	                    if time2 - time1 >= 1200:
	                        logging.info(requestUrl +"  服务器未启动，访问超时！！！")
	                        time1 = time2
	                if i >= 4 and send == 0:
	                    runConfig = changeReadFileToJson("./config/runConfig")
	                    runs = runConfig.get("run")
	                    nowRun = 1
	                    for run in runs:
	                        adress = run.split("$")[0]
	                        if adress == requestUrl:
	                            nowRun = run.split("$")[1]
	                    if nowRun == "1":
	                        logger.info(requestUrl + "  检测到服务挂了，重启服务！！！")
	                        os.system(jarUrl)
	                        logger.info(requestUrl + "  短信通知！！！")
	                        send_sms(shortMessageConfig,projectName)
	                    else:
	                        logger.info(requestUrl + "  正在部署，不用重启")
	                        time.sleep(5)
	                        i = 0
	                        break
	                    i = 0
	                    send = 1
	                    break


因为可能要监听多个java项目，所以要用到多线程。  

	# 线程处理
	class myThread(threading.Thread):
	    def __init__(self,projectMessage,shortMessageConfig):
	        threading.Thread.__init__(self)
	        self.projectMessage = projectMessage
	        self.shortMessageConfig = shortMessageConfig
	
	
	    def run(self):
	        try:
	            doListen(self.projectMessage,self.shortMessageConfig)
	        except Exception as e:
	            print(e)


主函数  

	#入口
	if __name__ == '__main__':
	    logging.info("------------------------------")
	    projectMessages = projectMessageConfig.get("requestUrlsAndJarPath")
	    for projectMessage in projectMessages:
	        logging.info(projectMessage.split("$")[0]+"  开启脚本")
	        myThread(projectMessage,shortMessageConfig).start()
	        time.sleep(2)


接下来就部署到java项目运行的机器上。   
我是用MobaXterm连接的   
在/opt下新建目录python_file  
把写好的代码和配置文件夹放到python_file目录下   
![](https://upload-images.jianshu.io/upload_images/19597329-427b01656c85fabf.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

>cd /opt/python_file
后台进程运行python程序
>nohup python3  send.py >/dev/null 2>&1 &
查看python进程  
>ps -ef | grep python

![](https://upload-images.jianshu.io/upload_images/19597329-7c6250630b485622.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

要终止进程
>kill -9 3543

查看java进程   
>ps -ef | grep java 

![](https://upload-images.jianshu.io/upload_images/19597329-230900162b599bcc.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

查看日志   
>tail -f 200 py_web_2020-03-31.log

![](https://upload-images.jianshu.io/upload_images/19597329-706f0df26fc6984b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

要测试的话，可以kill掉一个java项目试试（不要在正式服kill,手动滑稽）
>kill -9 3587 

打开日志  
![](https://upload-images.jianshu.io/upload_images/19597329-28b45f5a569bb11d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

在看看java项目有没有重启  
>ps -ef | grep java 

  ![](https://upload-images.jianshu.io/upload_images/19597329-1d4ae75461c7e23f.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
正常重启了   









