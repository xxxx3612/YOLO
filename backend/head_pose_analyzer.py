"""
头部姿态分析模块
通过YOLO关键点分析人体的抬头、低头动作
"""
from typing import Dict, List, Optional, Tuple


class HeadPoseAnalyzer:
    """头部姿态分析器"""
    
    # COCO格式关键点索引
    KEYPOINT_INDICES = {
        'nose': 0,
        'left_eye': 1,
        'right_eye': 2,
        'left_ear': 3,
        'right_ear': 4,
        'left_shoulder': 5,
        'right_shoulder': 6,
        'left_elbow': 7,
        'right_elbow': 8,
        'left_wrist': 9,
        'right_wrist': 10,
        'left_hip': 11,
        'right_hip': 12,
        'left_knee': 13,
        'right_knee': 14,
        'left_ankle': 15,
        'right_ankle': 16
    }
    
    def __init__(self, head_up_threshold: float = -10.0, head_down_threshold: float = 15.0):
        """
        初始化头部姿态分析器
        
        Args:
            head_up_threshold: 抬头角度阈值（度），负值表示向上
            head_down_threshold: 低头角度阈值（度），正值表示向下
        """
        self.head_up_threshold = head_up_threshold
        self.head_down_threshold = head_down_threshold
    
    def _get_keypoint(self, keypoints: List[Dict], index: int) -> Optional[Tuple[float, float, float]]:
        """
        获取指定索引的关键点
        
        Args:
            keypoints: 关键点列表
            index: 关键点索引
            
        Returns:
            (x, y, confidence) 或 None
        """
        if index < len(keypoints):
            kp = keypoints[index]
            if kp['confidence'] > 0.3:  # 置信度阈值
                return (kp['x'], kp['y'], kp['confidence'])
        return None
    
    def calculate_head_angle(self, keypoints: List[Dict]) -> Optional[float]:

        # 获取关键点
        nose = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['nose'])
        left_eye = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['left_eye'])
        right_eye = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['right_eye'])
        left_ear = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['left_ear'])
        right_ear = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['right_ear'])
        left_shoulder = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['left_shoulder'])
        right_shoulder = self._get_keypoint(keypoints, self.KEYPOINT_INDICES['right_shoulder'])
        
        # 至少需要鼻子和一个肩膀
        if not nose or (not left_shoulder and not right_shoulder):
            return None
        
        # 计算眼睛中心点
        eye_center = None
        if left_eye and right_eye:
            eye_center = ((left_eye[0] + right_eye[0]) / 2, 
                         (left_eye[1] + right_eye[1]) / 2)
        elif left_eye:
            eye_center = (left_eye[0], left_eye[1])
        elif right_eye:
            eye_center = (right_eye[0], right_eye[1])
        
        # 计算肩膀中心点
        if left_shoulder and right_shoulder:
            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) / 2,
                             (left_shoulder[1] + right_shoulder[1]) / 2)
        elif left_shoulder:
            shoulder_center = (left_shoulder[0], left_shoulder[1])
        else:
            shoulder_center = (right_shoulder[0], right_shoulder[1])
        
        # 方法1: 使用鼻子和眼睛的垂直距离判断
        if eye_center:
            # 计算鼻子相对于眼睛的垂直偏移
            nose_eye_offset = nose[1] - eye_center[1]
            
            # 计算头部长度（眼睛到肩膀的距离）
            head_length = abs(shoulder_center[1] - eye_center[1])
            
            if head_length > 0:
                # 归一化偏移，转换为角度
                # 正常情况下鼻子在眼睛下方约10-20像素
                normalized_offset = (nose_eye_offset / head_length) * 100
                
                # 转换为角度估计
                # 鼻子越靠下（相对眼睛）= 低头
                # 鼻子越靠上（相对眼睛）= 抬头
                angle = normalized_offset * 0.8  # 缩放因子
                return angle
        
        # 方法2: 使用鼻子和肩膀的角度（备用方案）
        nose_shoulder_offset = nose[1] - shoulder_center[1]
        
        # 计算参考距离（肩膀宽度）
        if left_shoulder and right_shoulder:
            shoulder_width = abs(left_shoulder[0] - right_shoulder[0])
        else:
            shoulder_width = 100  # 默认值
        
        if shoulder_width > 0:
            # 归一化并转换为角度
            angle = (nose_shoulder_offset / shoulder_width) * 50
            return angle
        
        return None
    
    def analyze_pose(self, keypoints: List[Dict]) -> Dict:

        angle = self.calculate_head_angle(keypoints)
        
        result = {
            'head_angle': round(angle, 2) if angle is not None else None,
            'pose': 'unknown',
            'description': '无法识别'
        }
        
        if angle is not None:
            if angle < self.head_up_threshold:
                result['pose'] = 'head_up'
                result['description'] = '抬头'
            elif angle > self.head_down_threshold:
                result['pose'] = 'head_down'
                result['description'] = '低头'
            else:
                result['pose'] = 'normal'
                result['description'] = '正常'
        
        return result
    
    def analyze_detections(self, detections: List[Dict]) -> List[Dict]:

        results = []
        
        for detection in detections:
            keypoints = detection.get('keypoints', [])
            pose_analysis = self.analyze_pose(keypoints)
            
            # 添加姿态分析结果
            detection_with_pose = detection.copy()
            detection_with_pose['head_pose'] = pose_analysis
            
            results.append(detection_with_pose)
        
        return results
    
    def get_statistics(self, detections_with_pose: List[Dict]) -> Dict:

        total = len(detections_with_pose)
        head_up = sum(1 for d in detections_with_pose 
                     if d.get('head_pose', {}).get('pose') == 'head_up')
        head_down = sum(1 for d in detections_with_pose 
                       if d.get('head_pose', {}).get('pose') == 'head_down')
        normal = sum(1 for d in detections_with_pose 
                    if d.get('head_pose', {}).get('pose') == 'normal')
        unknown = sum(1 for d in detections_with_pose 
                     if d.get('head_pose', {}).get('pose') == 'unknown')
        
        return {
            'total_persons': total,
            'head_up_count': head_up,
            'head_down_count': head_down,
            'normal_count': normal,
            'unknown_count': unknown,
            'head_up_percentage': round(head_up / total * 100, 1) if total > 0 else 0,
            'head_down_percentage': round(head_down / total * 100, 1) if total > 0 else 0
        }


def analyze_head_pose(detections: List[Dict], 
                     head_up_threshold: float = -10.0,
                     head_down_threshold: float = 15.0) -> Tuple[List[Dict], Dict]:

    analyzer = HeadPoseAnalyzer(head_up_threshold, head_down_threshold)
    detections_with_pose = analyzer.analyze_detections(detections)
    statistics = analyzer.get_statistics(detections_with_pose)
    
    return detections_with_pose, statistics
