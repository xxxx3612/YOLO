from flask import request
from flask_restx import Resource, fields, Namespace
import os
from ..config import config
from ..models.yolo_detector import detector
from ..utils.image_processor import process_uploaded_file, allowed_file
from ..utils.validators import validate_image_file, validate_detection_params

# 创建API命名空间
api = Namespace('detection', description='YOLO目标检测操作')

# API数据模型
detection_model = api.model('DetectionParams', {
    'confidence': fields.Float(description='置信度阈值', default=0.25),
    'iou': fields.Float(description='IoU阈值', default=0.45),
    'save_image': fields.Boolean(description='是否保存结果图像', default=True)
})


@api.route('/health')
class HealthCheck(Resource):
    def get(self):
        """服务健康检查"""
        return {
            'status': 'healthy',
            'service': config.APP_NAME,
            'version': config.APP_VERSION,
            'model_loaded': detector.model is not None
        }


@api.route('/detect')
class DetectImage(Resource):
    @api.expect(detection_model)
    def post(self):
        """单张图像目标检测"""
        try:
            # 检查文件上传
            if 'image' not in request.files:
                return {'success': False, 'error': '未提供图像文件'}, 400

            file = request.files['image']

            # 验证文件
            if file.filename == '':
                return {'success': False, 'error': '未选择文件'}, 400

            if not allowed_file(file.filename):
                return {
                    'success': False,
                    'error': f'不支持的文件类型。允许的类型: {", ".join(config.ALLOWED_EXTENSIONS)}'
                }, 400

            # 处理上传的文件
            try:
                image_path = process_uploaded_file(file)
            except Exception as e:
                return {'success': False, 'error': f'文件处理失败: {str(e)}'}, 400

            # 获取检测参数
            confidence = request.form.get('confidence', type=float)
            iou = request.form.get('iou', type=float)
            save_image = request.form.get('save_image', 'true').lower() == 'true'

            # 验证参数
            param_errors = validate_detection_params(confidence, iou)
            if param_errors:
                # 清理上传的文件
                try:
                    os.remove(image_path)
                except:
                    pass
                return {'success': False, 'errors': param_errors}, 400

            # 执行检测
            result = detector.detect_image(image_path, save_result=save_image)

            # 清理上传的临时文件
            try:
                os.remove(image_path)
            except:
                pass

            # 返回结果
            if result['success']:
                return {
                    'success': True,
                    'filename': file.filename,
                    'detections': result['detections'],
                    'detection_count': len(result['detections']),
                    'result_image': result['result_image'],
                    'image_size': result['image_size']
                }
            else:
                return {'success': False, 'error': result['error']}, 500

        except Exception as e:
            return {'success': False, 'error': f'检测失败: {str(e)}'}, 500


@api.route('/detect/batch')
class BatchDetect(Resource):
    def post(self):
        """批量图像检测"""
        try:
            if 'images' not in request.files:
                return {'success': False, 'error': '未提供图像文件'}, 400

            files = request.files.getlist('images')
            if len(files) == 0:
                return {'success': False, 'error': '未选择任何图像文件'}, 400

            # 处理所有文件
            image_paths = []
            valid_files = []

            for file in files:
                if file.filename and allowed_file(file.filename):
                    try:
                        image_path = process_uploaded_file(file)
                        image_paths.append(image_path)
                        valid_files.append(file)
                    except Exception as e:
                        print(f"文件 {file.filename} 处理失败: {e}")
                        continue

            if not image_paths:
                return {'success': False, 'error': '没有有效的图像文件'}, 400

            # 执行批量检测
            results = []
            for i, image_path in enumerate(image_paths):
                result = detector.detect_image(image_path, save_result=True)
                result['filename'] = valid_files[i].filename
                results.append(result)

                # 清理临时文件
                try:
                    os.remove(image_path)
                except:
                    pass

            return {
                'success': True,
                'total_images': len(results),
                'results': results
            }

        except Exception as e:
            return {'success': False, 'error': f'批量检测失败: {str(e)}'}, 500


@api.route('/classes')
class GetClasses(Resource):
    def get(self):
        """获取模型支持的类别列表"""
        try:
            class_names = detector.get_class_names()
            return {
                'success': True,
                'classes': class_names,
                'total_classes': len(class_names)
            }
        except Exception as e:
            return {'success': False, 'error': f'获取类别失败: {str(e)}'}, 500