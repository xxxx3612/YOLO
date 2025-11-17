import os
from ..config import config


def validate_image_file(file):
    """验证上传的图像文件
    Args:
        file: Flask文件对象
    Returns:
        list: 错误信息列表，空列表表示验证通过
    """
    errors = []

    # 检查文件名是否为空
    if not file.filename:
        errors.append("文件名不能为空")

    # 检查文件扩展名是否允许
    if not allowed_file(file.filename):
        errors.append(f"不支持的文件类型。允许的类型: {', '.join(config.ALLOWED_EXTENSIONS)}")

    # 检查文件大小
    file.seek(0, os.SEEK_END)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小
    file.seek(0)  # 重置文件指针到开头

    if file_size > config.MAX_FILE_SIZE:
        errors.append(f"文件大小超过限制 ({config.MAX_FILE_SIZE // (1024 * 1024)}MB)")

    return errors


def validate_detection_params(confidence, iou):
    """验证检测参数的有效性
    Args:
        confidence: 置信度阈值
        iou: 交并比阈值
    Returns:
        list: 错误信息列表
    """
    errors = []

    if confidence is not None:
        try:
            conf = float(confidence)
            if not 0 <= conf <= 1:
                errors.append("置信度阈值必须在0到1之间")
        except ValueError:
            errors.append("置信度阈值必须是数字")

    if iou is not None:
        try:
            iou_val = float(iou)
            if not 0 <= iou_val <= 1:
                errors.append("IoU阈值必须在0到1之间")
        except ValueError:
            errors.append("IoU阈值必须是数字")

    return errors