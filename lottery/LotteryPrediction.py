import datetime
import logging
import random
import smtplib
from collections import Counter
from email.header import Header
from email.mime.text import MIMEText

import requests
from jsonpath import jsonpath


class LotteryPrediction:
    """根据历史中奖号码推荐本期号码"""

    def __init__(self):
        """初始化属性"""
        self.page_no = 1
        self.page_size = 1000
        self.first_front_nums = []  # 排序后前区1号码集合
        self.second_front_nums = []  # 排序后前区2号码集合
        self.third_front_nums = []  # 排序后前区3号码集合
        self.fourth_front_nums = []  # 排序后前区4号码集合
        self.fifth_front_nums = []  # 排序后前区5号码集合
        self.first_back_nums = []  # 排序后后区1号码集合
        self.second_back_nums = []  # 排序后后区2号码集合
        self.unsort_first_front_nums = []  # 原始前区1号码集合
        self.unsort_second_front_nums = []  # 原始前区2号码集合
        self.unsort_third_front_nums = []  # 原始前区3号码集合
        self.unsort_fourth_front_nums = []  # 原始前区4号码集合
        self.unsort_fifth_front_nums = []  # 原始前区5号码集合
        self.unsort_first_back_nums = []  # 原始后区1号码集合
        self.unsort_second_back_nums = []  # 原始后区2号码集合
        self.history_lottery_draw_results_front_nums = []  # 前区号码组合列表
        self.history_lottery_draw_results_back_nums = []  # 后区号码组合列表
        self.history_lottery_unsort_draw_results_front_nums = []  # 原始前区号码组合列表
        self.history_lottery_unsort_draw_results_back_nums = []  # 原始后区号码组合列表
        logging.basicConfig(level=logging.DEBUG)  # 日志级别
        self.send_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.smtp_host = "smtp.qq.com"
        self.smtp_email = "243062737@qq.com"
        self.smtp_passwd = "nfpbmhqnsslibhjg"

    def send_prediction_result(self, lottery_draw_num, prediction_result):
        """通过邮箱发送预测结果"""
        message = MIMEText(prediction_result, "plain", "utf-8")  # 预测结果
        message["From"] = Header(f'"=?utf-8?B?6LSi56We6am+5YiwCg=?=" {self.smtp_email}')  # 发件人
        message["Subject"] = Header(f"第{lottery_draw_num}期超级大乐透幸运号码", "utf-8")  # 邮件标题
        smtp_server = smtplib.SMTP_SSL(self.smtp_host, 465)  # 发送服务器的端口号
        try:
            smtp_server.login(self.smtp_email, self.smtp_passwd)
            smtp_server.sendmail(self.smtp_email, self.smtp_email, message.as_string())
        except smtplib.SMTPException as e:
            logging.info(f"邮件发送失败{e}")
        finally:
            smtp_server.quit()

    def get_history_lottery_draw_info(self):
        """获取历史中奖信息"""
        url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        headers = {
            'Connection': 'close',
        }
        params = {
            "gameNo": 85,
            "provinceId": 0,
            "isVerify": 1,
            "termLimits": 0,
            "pageSize": self.page_size,
            "pageNo": self.page_no,
        }
        # 获取历史中奖号码信息，将结果转化为json对象
        history_lottery_draw_info = requests.get(url=url, headers=headers, params=params).json()

        # 断言请求是否成功
        error_code = int(jsonpath(history_lottery_draw_info, "$.errorCode")[0])
        if error_code == 0:
            # 获取历史中奖期数&号码和最新一期期数
            last_lottery_draw_num = jsonpath(history_lottery_draw_info, "$.value.lastPoolDraw..lotteryDrawNum")[0]
            history_lottery_draw_nums = jsonpath(
                history_lottery_draw_info, '$.value.list[?(@.lotteryDrawNum > "19018")].lotteryDrawNum')  # 期数
            history_lottery_draw_results = jsonpath(
                history_lottery_draw_info, '$.value.list[?(@.lotteryDrawNum > "19018")].lotteryDrawResult')  # 排序
            history_lottery_unsort_draw_results = jsonpath(
                history_lottery_draw_info, '$.value.list[?(@.lotteryDrawNum > "19018")].lotteryUnsortDrawresult')  # 原始

            # 获取排序后前区及后区组合数字
            for history_lottery_draw_result in history_lottery_draw_results:
                self.history_lottery_draw_results_front_nums.append(str(history_lottery_draw_result)[0:-6])
                self.history_lottery_draw_results_back_nums.append(str(history_lottery_draw_result)[-5:])

            # 获取原始前区及后区组合数字
            for history_lottery_unsort_draw_result in history_lottery_unsort_draw_results:
                self.history_lottery_draw_results_front_nums.append(str(history_lottery_unsort_draw_result)[0:-6])
                self.history_lottery_draw_results_back_nums.append(str(history_lottery_unsort_draw_result)[-5:])

            return {
                'last_lottery_draw_num': last_lottery_draw_num,
                'history_lottery_draw_nums': history_lottery_draw_nums,
                'history_lottery_draw_results': history_lottery_draw_results,
                'history_lottery_unsort_draw_results': history_lottery_unsort_draw_results,
            }
        else:
            logging.info(f"获取历史中奖号码失败，请检查~\n"
                         f"错误信息：{history_lottery_draw_info}")

    def analyze_history_info_prediction_result(self):
        """分析历史数据并预测中奖结果"""

        # 获取历史中奖信息（排序后&原始）及最新期数
        history_lottery_draw_info = self.get_history_lottery_draw_info()
        history_lottery_draw_results = history_lottery_draw_info["history_lottery_draw_results"]  # 排序后
        history_lottery_unsort_draw_results = history_lottery_draw_info["history_lottery_unsort_draw_results"]  # 原始
        lottery_draw_num = int(history_lottery_draw_info["last_lottery_draw_num"]) + 1

        # 循环排序后中奖号码并将每位数字转化为列表
        for history_lottery_draw_result in history_lottery_draw_results:
            self.first_front_nums.append(str(history_lottery_draw_result).split(" ")[0])
            self.second_front_nums.append(str(history_lottery_draw_result).split(" ")[1])
            self.third_front_nums.append(str(history_lottery_draw_result).split(" ")[2])
            self.fourth_front_nums.append(str(history_lottery_draw_result).split(" ")[3])
            self.fifth_front_nums.append(str(history_lottery_draw_result).split(" ")[4])
            self.first_back_nums.append(str(history_lottery_draw_result).split(" ")[5])
            self.second_back_nums.append(str(history_lottery_draw_result).split(" ")[6])

        # 循环原始中奖号码并将每位数字转化为列表
        for history_lottery_unsort_draw_result in history_lottery_unsort_draw_results:
            self.unsort_first_front_nums.append(str(history_lottery_unsort_draw_result).split(" ")[0])
            self.unsort_second_front_nums.append(str(history_lottery_unsort_draw_result).split(" ")[1])
            self.unsort_third_front_nums.append(str(history_lottery_unsort_draw_result).split(" ")[2])
            self.unsort_fourth_front_nums.append(str(history_lottery_unsort_draw_result).split(" ")[3])
            self.unsort_fifth_front_nums.append(str(history_lottery_unsort_draw_result).split(" ")[4])
            self.unsort_first_back_nums.append(str(history_lottery_unsort_draw_result).split(" ")[5])
            self.unsort_second_back_nums.append(str(history_lottery_unsort_draw_result).split(" ")[6])

        # 将排序后号码转化为字典 key为号码 value为出现次数
        first_front_nums_info = Counter(self.first_front_nums)
        logging.debug(f"前区1号码详情：{first_front_nums_info}")
        second_front_nums_info = Counter(self.second_front_nums)
        logging.debug(f"前区2号码详情：{second_front_nums_info}")
        third_front_nums_info = Counter(self.third_front_nums)
        logging.debug(f"前区3号码详情：{third_front_nums_info}")
        fourth_front_nums_info = Counter(self.fourth_front_nums)
        logging.debug(f"前区4号码详情：{fourth_front_nums_info}")
        fifth_front_nums_info = Counter(self.fifth_front_nums)
        logging.debug(f"前区5号码详情：{fifth_front_nums_info}")
        first_back_nums_info = Counter(self.first_back_nums)
        logging.debug(f"后区1号码详情：{first_back_nums_info}")
        second_back_nums_info = Counter(self.second_back_nums)
        logging.debug(f"后区2号码详情：{second_back_nums_info}")

        # 将原始号码转化为字典 key为号码 value为出现次数
        unsort_first_front_nums_info = Counter(self.unsort_first_front_nums)
        logging.debug(f"前区1号码详情：{unsort_first_front_nums_info}")
        unsort_second_front_nums_info = Counter(self.unsort_second_front_nums)
        logging.debug(f"前区2号码详情：{unsort_second_front_nums_info}")
        unsort_third_front_nums_info = Counter(self.unsort_third_front_nums)
        logging.debug(f"前区3号码详情：{unsort_third_front_nums_info}")
        unsort_fourth_front_nums_info = Counter(self.unsort_fourth_front_nums)
        logging.debug(f"前区4号码详情：{unsort_fourth_front_nums_info}")
        unsort_fifth_front_nums_info = Counter(self.unsort_fifth_front_nums)
        logging.debug(f"前区5号码详情：{unsort_fifth_front_nums_info}")
        unsort_first_back_nums_info = Counter(self.unsort_first_back_nums)
        logging.debug(f"后区1号码详情：{unsort_first_back_nums_info}")
        unsort_second_back_nums_info = Counter(self.unsort_second_back_nums)
        logging.debug(f"后区2号码详情：{unsort_second_back_nums_info}")

        # 统计中奖号码出现次数并转化为字典key:draw_result为中奖号码，value:draw_result_nums为中奖次数，并输出中奖次数最多的号码
        draw_result_num_info = Counter(history_lottery_draw_results).most_common(1)[0]
        prediction_result1 = draw_result_num_info[0]
        logging.info(
            f"根据历史中奖号码中中奖次数最多的号码推荐（中奖次数：{draw_result_num_info[1]}次），本期中奖号码1为：{prediction_result1}.")

        # 根据玄学推荐2
        first_front_num = list(first_front_nums_info.keys())[0]
        second_front_num = list(second_front_nums_info.keys())[0]
        third_front_num = list(third_front_nums_info.keys())[0]
        fourth_front_num = list(fourth_front_nums_info.keys())[0]
        fifth_front_num = list(fifth_front_nums_info.keys())[0]
        first_back_num = list(first_back_nums_info.keys())[0]
        second_back_num = list(second_back_nums_info.keys())[0]
        prediction_result2 = f"{first_front_num} {second_front_num} {third_front_num} {fourth_front_num} {fifth_front_num}" \
                             f"  {first_back_num} {second_back_num}"
        logging.info(f"根据玄学出现次数最高的号码推荐，本期中奖号码2为：{prediction_result2}.")

        # 根据玄学推荐3
        first_front_num = list(first_front_nums_info.keys())[-1]
        second_front_num = list(second_front_nums_info.keys())[-1]
        third_front_num = list(third_front_nums_info.keys())[-1]
        fourth_front_num = list(fourth_front_nums_info.keys())[-1]
        fifth_front_num = list(fifth_front_nums_info.keys())[-1]
        first_back_num = list(first_back_nums_info.keys())[-1]
        second_back_num = list(second_back_nums_info.keys())[-1]
        prediction_result3 = f"{first_front_num} {second_front_num} {third_front_num} {fourth_front_num} {fifth_front_num}" \
                             f"  {first_back_num} {second_back_num}"
        logging.info(f"根据玄学出现次数最低的号码推荐，本期中奖号码3为：{prediction_result3}.")

        # 根据历史中奖号码中每一位出现次数最高的号码推荐
        first_front_num = first_front_nums_info.most_common()[0][0]
        second_front_num = second_front_nums_info.most_common()[0][0]
        third_front_num = third_front_nums_info.most_common()[0][0]
        fourth_front_num = fourth_front_nums_info.most_common()[0][0]
        fifth_front_num = fifth_front_nums_info.most_common()[0][0]
        first_back_num = first_back_nums_info.most_common()[0][0]
        second_back_num = second_back_nums_info.most_common()[0][0]
        prediction_result4 = f"{first_front_num} {second_front_num} {third_front_num} {fourth_front_num} {fifth_front_num}" \
                             f"  {first_back_num} {second_back_num}"
        logging.info(f"根据历史中奖号码中每一位出现次数最高的号码推荐，本期中奖号码4为：{prediction_result4}.")

        # 根据历史中奖号码中每一位出现次数最低的号码推荐
        first_front_num = first_front_nums_info.most_common()[-1][0]
        second_front_num = second_front_nums_info.most_common()[-1][0]
        third_front_num = third_front_nums_info.most_common()[-1][0]
        fourth_front_num = fourth_front_nums_info.most_common()[-1][0]
        fifth_front_num = fifth_front_nums_info.most_common()[-1][0]
        first_back_num = first_back_nums_info.most_common()[-1][0]
        second_back_num = second_back_nums_info.most_common()[-1][0]
        prediction_result5 = f"{first_front_num} {second_front_num} {third_front_num} {fourth_front_num} {fifth_front_num}" \
                             f"  {first_back_num} {second_back_num}"
        logging.info(f"根据历史中奖号码中每一位出现次数最低的号码推荐，本期中奖号码5为：{prediction_result5}.")

        # 分别统计前后区中奖号码出现次数并转化为字典key:draw_result为中奖号码，value:draw_result_nums为中奖次数，并随机输出中奖次数最多的5个号码
        logging.debug(f"前区组合详情：{Counter(self.history_lottery_draw_results_front_nums).most_common(15)}")
        draw_result_front_num_info = random.sample(
            Counter(self.history_lottery_draw_results_front_nums).most_common(15), k=5)  # 前区
        draw_result_back_num_info = Counter(self.history_lottery_draw_results_back_nums).most_common(5)  # 后区
        logging.debug(f"后区组合详情：{Counter(self.history_lottery_draw_results_back_nums).most_common(5)}")
        prediction_result6 = draw_result_front_num_info[0][0] + " " + draw_result_back_num_info[0][0]
        prediction_result7 = draw_result_front_num_info[1][0] + " " + draw_result_back_num_info[1][0]
        prediction_result8 = draw_result_front_num_info[2][0] + " " + draw_result_back_num_info[2][0]
        prediction_result9 = draw_result_front_num_info[3][0] + " " + draw_result_back_num_info[3][0]
        prediction_result10 = draw_result_front_num_info[4][0] + " " + draw_result_back_num_info[4][0]
        logging.info(
            f"根据前后区历史中奖号码中中奖次数最多的号码推荐，\n"
            f"本期中奖号码6为：{prediction_result6}.\n"
            f"本期中奖号码7为：{prediction_result7}.\n"
            f"本期中奖号码8为：{prediction_result8}.\n"
            f"本期中奖号码9为：{prediction_result9}.\n"
            f"本期中奖号码10为：{prediction_result10}."
        )

        # 通过邮箱发送预测通知
        prediction_result = f"根据历史中奖号码中中奖次数最多的号码推荐: \n{prediction_result1}\n" \
                            f"根据玄学出现次数最高的号码推荐: \n{prediction_result2}\n" \
                            f"根据玄学出现次数最低的号码推荐: \n{prediction_result3}\n" \
                            f"根据历史中奖号码中每一位出现次数最高的号码推荐： \n{prediction_result4}\n" \
                            f"根据历史中奖号码中每一位出现次数最低的号码推荐： \n{prediction_result5}\n" \
                            f"根据前后区历史中奖号码中中奖次数最多的号码推荐1： \n{prediction_result6}\n" \
                            f"根据前后区历史中奖号码中中奖次数最多的号码推荐2：\n{prediction_result7}\n" \
                            f"根据前后区历史中奖号码中中奖次数最多的号码推荐3：\n{prediction_result8}\n" \
                            f"根据前后区历史中奖号码中中奖次数最多的号码推荐4：\n{prediction_result9}\n" \
                            f"根据前后区历史中奖号码中中奖次数最多的号码推荐5：\n{prediction_result10}\n"
        self.send_prediction_result(lottery_draw_num, prediction_result)


if __name__ == '__main__':
    LotteryPrediction().analyze_history_info_prediction_result()
