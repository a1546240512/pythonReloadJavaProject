# -*- coding: UTF-8 -*-
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import requests
import time
import os
import logging
import datetime
import json
import threading


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

# 将文件读取并转换成json格式数据返回
def changeReadFileToJson(path):
    with open(path,encoding="UTF-8") as file_object:
        contends = file_object.read()
    return json.loads(contends)
#读取配置文件
shortMessageConfig = changeReadFileToJson("./config/shortMessage")
projectMessageConfig = changeReadFileToJson("./config/projectMessage")


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

if __name__ == '__main__':
    logging.info("------------------------------")
    projectMessages = projectMessageConfig.get("requestUrlsAndJarPath")
    for projectMessage in projectMessages:
        logging.info(projectMessage.split("$")[0]+"  开启脚本")
        myThread(projectMessage,shortMessageConfig).start()
        time.sleep(2)





