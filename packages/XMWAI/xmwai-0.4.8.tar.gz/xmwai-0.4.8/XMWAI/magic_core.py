from datetime import date


# U1-07 生日猜猜猜----------------------------------
def birthday():
    while True:
        try:
            # 获取并验证生日计算结果
            code = int(input("\n从上方选出你的生日日期\n将生日的月份乘以4，加上9，再乘以25，最后加上日期后的结果："))
            secret_number = code - 225
            # 解析月份和日期
            month = secret_number // 100
            day = secret_number % 100

            # 基础验证
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("神秘数字解析失败，请确认计算正确！✨")

            # 创建日期对象
            today = date.today()
            try:
                current_year_bday = date(today.year, month, day)
            except ValueError as e:
                raise ValueError(f"🔮 魔法日历显示：{str(e)}，请检查你的生日日期！")

            # 计算时间差
            if current_year_bday < today:
                next_bday = date(today.year + 1, month, day)
                days_passed = (today - current_year_bday).days
                days_left = (next_bday - today).days
                print(f"\n🎂 你的生日是 {month}月{day}日")
                print(f"⏳ 今年生日已经过去了 {days_passed} 天")
                print(f"⏳ 距离下次生日还有 {days_left} 天")
            elif current_year_bday == today:
                print("\n🎉🎉🎉 今天是你的生日！生日快乐！ 🎉🎉🎉")
            else:
                days_left = (current_year_bday - today).days
                print(f"\n🎂 你的生日是 {month}月{day}日")
                print(f"⏳ 距离生日还有 {days_left} 天")

            # 添加节日彩蛋
            if (month, day) == (12, 25):
                print("🎁 圣诞奇迹儿！你的到来就是最棒的圣诞礼物！")
                print("🦌 愿你的善良像驯鹿传遍四方，热情如炉火温暖世界！")
            elif (month, day) == (10, 31):
                print("👻 魔法小精灵！糖果和惊喜永远伴随你！")
                print("🕯️ 愿你的生活充满奇幻冒险，像南瓜灯一样照亮黑夜！")
            elif (month, day) == (1, 1):
                print("✨ 新年小天使！你的诞生就是世界收到的最好新年礼物！")
                print("🎊 愿你的笑容像跨年烟火般灿烂，智慧随岁月与日俱增！")
            elif (month, day) == (5, 1):
                print("👷♀ 勤劳小蜜蜂！你的生日就是全世界的劳动庆典！")
                print("🏆 愿你的努力都能开花结果，像春天播种秋天丰收！")
            elif (month, day) == (10, 1):
                print("🎇 国庆小英雄！你和祖国母亲同庆生辰！")
                print("🚀 愿你的未来如火箭升空，人生像阅兵方阵般气势如虹！")
            elif (month, day) == (6, 1):
                print("🪅 双倍快乐王！全世界的孩子都在为你庆生！")
                print("🎠 愿你的生活永远像游乐场，每天都有新发现！")
            break  # 退出循环

        except ValueError as e:
            print(f"\n⚠️ 魔法出错啦：{e}")
            print("请重新输入正确的神秘数字！")
# -------------------------------------------------
