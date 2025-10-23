from PIL import Image, ImageDraw, ImageFont
import io
import os
import random
import base64


class CaptchaService:
    """
    验证码模块服务层
    """

    @classmethod
    def create_captcha_image_service(cls):
        # 创建空白图像
        image = Image.new('RGB', (400, 300), color='#EAEAEA')

        # 创建绘图对象
        draw = ImageDraw.Draw(image)

        # 设置字体 - 尝试加载系统字体,失败则使用默认字体
        try:
            # 获取项目根目录(backlin包的上一级目录)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            custom_font_path = os.path.join(project_root, 'data', 'font', 'Arial.ttf')

            # 尝试常见的系统字体路径
            font_paths = [
                custom_font_path,  # 自定义字体路径
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Linux
                '/System/Library/Fonts/Helvetica.ttc',  # macOS
                'C:\\Windows\\Fonts\\Arial.ttf',  # Windows
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size=100)
                    break
            if font is None:
                # 如果所有路径都不存在,使用默认字体
                font = ImageFont.load_default()
        except Exception:
            # 如果加载失败,使用默认字体
            font = ImageFont.load_default()

        # 生成两个0-9之间的随机整数
        num1 = random.randint(0, 9)
        num2 = random.randint(0, 9)
        # 从运算符列表中随机选择一个
        operational_character_list = ['+', '-', '*']
        operational_character = random.choice(operational_character_list)
        # 根据选择的运算符进行计算
        if operational_character == '+':
            result = num1 + num2
        elif operational_character == '-':
            result = num1 - num2
        else:
            result = num1 * num2
        # 绘制文本
        text = f"{num1} {operational_character} {num2} = ?"
        draw.text((10, 120), text, fill='blue', font=font)

        # 将图像数据保存到内存中
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')

        # 将图像数据转换为base64字符串
        base64_string = f'data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}'

        return [base64_string, result]
