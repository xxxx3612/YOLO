import os
from datetime import datetime
from werkzeug.utils import secure_filename as wz_secure_filename
from PIL import Image, ExifTags
import io
from ..config import config


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def process_uploaded_file(file):
    """处理上传的文件"""
    try:
        if file and allowed_file(file.filename):
            # 读取文件数据
            file_data = file.read()

            # 检查文件大小
            if len(file_data) > config.MAX_FILE_SIZE:
                raise ValueError("文件大小超过限制")

            # 使用PIL处理图像
            image = Image.open(io.BytesIO(file_data))

            # 处理EXIF方向
            image = fix_image_orientation(image)

            # 转换为RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # 生成安全文件名
            filename = secure_filename(file.filename)
            filepath = os.path.join(config.UPLOAD_FOLDER, filename)

            # 保存图像
            image.save(filepath, 'JPEG', quality=95)

            return filepath

        else:
            raise ValueError("不支持的文件类型")

    except Exception as e:
        raise ValueError(f"文件处理错误: {str(e)}")


def fix_image_orientation(image):
    """修复图像的EXIF方向"""
    try:
        exif = image._getexif()
        if exif is not None:
            for tag, value in ExifTags.TAGS.items():
                if value == 'Orientation':
                    orientation_tag = tag
                    break

            orientation = exif.get(orientation_tag, 1)

            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)

    except Exception:
        pass

    return image


def secure_filename(filename):
    """安全地处理文件名"""
    secure_name = wz_secure_filename(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    name, ext = os.path.splitext(secure_name)
    return f"{name}_{timestamp}{ext}"