import base64
import tkinter as tk
import urllib
import requests
import json
from PIL import Image
from PIL import ImageGrab
from io import BytesIO
import time
import os
import ctypes
import cv2
import numpy as np

'''-----------体验课1-----------'''
import urllib.parse
import platform
from io import BytesIO


def make(screen):
    save_pic(screen)
    while not os.path.exists("pic.png"):
        pass

    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    API_KEY = "YleMT041wl8zkXhk1Y4AdEuk"
    SECRET_KEY = "xQousjKEqphGwVMKHJlUSGDXp7PiUVpk"
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials",
              "client_id": API_KEY, "client_secret": SECRET_KEY}

    # 获取访问令牌并构建API请求URL
    access_token = str(requests.post(
        url, params=params).json().get("access_token"))
    create_url = f"https://aip.baidubce.com/rpc/2.0/ernievilg/v1/txt2imgv2?access_token={access_token}"
    query_url = f"https://aip.baidubce.com/rpc/2.0/ernievilg/v1/getImgv2?access_token={access_token}"

    # 读取图像并转换为Base64编码
    with open("pic.png", "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')

    # 构建创建任务的请求参数
    create_payload = json.dumps({
        "prompt": "参考当前图，希望画面卡通一些，画面可以丰富一些，内容积极向上，参考宫崎骏画风",
        "width": 1024,
        "height": 1024,
        "image": base64_string,
        "change_degree": 1
    }, ensure_ascii=False)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # 发送创建任务请求
    response = requests.post(create_url, headers=headers,
                             data=create_payload.encode("utf-8"))
    response.raise_for_status()
    task_id = response.json()["data"]["task_id"]

    # 轮询检查任务状态
    query_payload = json.dumps({"task_id": task_id}, ensure_ascii=False)
    task_status = "RUNNING"
    print("AI图片生成中.......")
    while task_status == "RUNNING":
        time.sleep(30)
        response = requests.post(
            query_url, headers=headers, data=query_payload.encode("utf-8"))
        response.raise_for_status()
        task_status = response.json()["data"]["task_status"]

    # 处理任务结果
    if task_status == "SUCCESS":
        picture = requests.get(response.json()[
            "data"]["sub_task_result_list"][0]["final_image_list"][0]["img_url"])
        image_data = BytesIO(picture.content)
        image = Image.open(image_data)
        image.save('image.gif')
        open_image("image.gif")
    else:
        print(f"任务失败，状态: {task_status}")


def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded 
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def detect_scale():
    """
    跨平台缩放比例检测
    - Windows: 检测实际 DPI
    - macOS/Linux: 默认返回 1.0
    """
    if platform.system() == "Windows":
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            if hasattr(user32, 'GetDpiForSystem'):
                dpi = user32.GetDpiForSystem()
                return dpi / 96.0
            screen_width = user32.GetSystemMetrics(0)
            return screen_width / 1920.0
        except Exception:
            return 1.0
    else:
        return 1.0


def save_pic(screen, output_file="pic.png"):
    """
    精准截取turtle绘图区域，不包含窗口边框和标题栏
    跨平台支持 (Windows/macOS/Linux)
    """
    canvas = screen.getcanvas()
    screen.update()

    try:
        # 获取画布位置和大小
        x = canvas.winfo_rootx()
        y = canvas.winfo_rooty()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        # 检测屏幕缩放比例
        scale_factor = detect_scale()

        # Windows 上要扣除边框和标题栏
        border_width = int(
            8 * scale_factor) if platform.system() == "Windows" else 0
        title_height = int(
            30 * scale_factor) if platform.system() == "Windows" else 0

        # 计算实际绘图区域
        img = ImageGrab.grab(
            bbox=(
                x + border_width,
                y + title_height,
                x + width - border_width,
                y + height - border_width
            )
        )

        img.save(output_file)
    except Exception as e:
        print(f"截图时出错: {e}")
        print("提示: 可以尝试手动截图或使用其他方法")


def open_image(file_path):
    """
    跨平台打开图片
    - Windows: os.startfile
    - macOS: open
    - Linux: xdg-open
    """
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            os.system(f"open {file_path}")
        else:  # Linux / 其他
            os.system(f"xdg-open {file_path}")
    except Exception as e:
        print(f"打开图片失败: {e}")


'''-----------体验课2-----------'''


def get_file_content_as_base64_2(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded 
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def cartoon(name):
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    API_KEY = "LjdoA5Ar7MGrwynZfTFcB7K3"
    SECRET_KEY = "3htSVp4IhW8LIyetP5Yo8NdWvF0yNH0W"
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials",
              "client_id": API_KEY, "client_secret": SECRET_KEY}
    s = str(requests.post(url, params=params).json().get("access_token"))

    url = "https://aip.baidubce.com/rest/2.0/image-process/v1/selfie_anime?access_token=" + s
    base64_string = get_file_content_as_base64_2("pic.jpg", True)
    payload = "image={}".format(base64_string)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    response = requests.request(
        "POST", url, headers=headers, data=payload.encode("utf-8"))
    base64_data = response.json()["image"]
    image_data = base64.b64decode(base64_data)
    with open("img.png", 'wb') as f:
        f.write(image_data)

    photo = cv2.imread('img.png')
    original = cv2.imread('pic.jpg')
    height, width = photo.shape[:2]

    # 扫描效果参数
    scan_bar_height = 60  # 扫描光带高度
    glow_width = 15       # 光晕宽度
    glow_intensity = 0.3  # 光晕强度
    scan_speed = 5        # 扫描速度（毫秒）

    # 创建一个与图像大小相同的透明层用于绘制扫描效果
    overlay = np.zeros_like(original, dtype=np.uint8)

    for i in range(-scan_bar_height, height + scan_bar_height):
        # 创建一个空白图像
        display = original.copy()
        # 只显示扫描到的部分
        if i > 0:
            display[:min(i, height), :] = photo[:min(i, height), :]

        # 清除上一帧的扫描效果
        overlay.fill(0)

        # 计算扫描光带位置
        scan_start = max(0, i - scan_bar_height // 2)
        scan_end = min(height, i + scan_bar_height // 2)

        if scan_start < scan_end:
            # 创建渐变扫描光带
            for y in range(scan_start, scan_end):
                # 计算渐变因子（0-1-0）
                distance_from_center = abs(y - i)
                gradient_factor = 1.0 - \
                    (distance_from_center / (scan_bar_height / 2))

                # 绿色扫描线主体
                green_intensity = int(255 * gradient_factor)
                overlay[y, :, 1] = green_intensity

                # 添加轻微的蓝色调，使扫描线更真实
                overlay[y, :, 2] = int(60 * gradient_factor)

            # 添加光晕效果
            for y in range(max(0, scan_start - glow_width), min(height, scan_end + glow_width)):
                if y < scan_start or y >= scan_end:
                    # 计算光晕强度
                    distance_from_edge = min(
                        abs(y - scan_start), abs(y - scan_end))
                    glow_factor = max(
                        0, 1.0 - (distance_from_edge / glow_width)) * glow_intensity

                    # 添加绿色光晕
                    overlay[y, :, 1] = np.clip(
                        overlay[y, :, 1] + (255 * glow_factor), 0, 255)

            # 将半透明扫描效果叠加到图像上
            alpha = 0.5  # 透明度
            cv2.addWeighted(overlay, alpha, display, 1 - alpha, 0, display)

        # 显示稳定的扫描效果
        cv2.imshow(name, display)
        cv2.waitKey(scan_speed)  # 控制扫描速度
