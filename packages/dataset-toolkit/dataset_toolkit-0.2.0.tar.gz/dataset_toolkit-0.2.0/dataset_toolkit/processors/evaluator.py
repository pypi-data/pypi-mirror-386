# dataset_toolkit/processors/evaluator.py
from typing import Dict, List, Optional, Tuple
from dataset_toolkit.models import Dataset, Annotation, ImageAnnotation


class Evaluator:
    """
    评估器：支持正检集和误检集分离评估
    
    用于比较GT和Pred数据集，计算Precision、Recall、F1、FPPI等指标。
    支持在不同置信度阈值下动态评估，无需重新加载数据。
    """
    
    def __init__(
        self,
        positive_gt: Dataset,
        positive_pred: Dataset,
        negative_gt: Optional[Dataset] = None,
        negative_pred: Optional[Dataset] = None,
        iou_threshold: float = 0.5
    ):
        """
        初始化评估器
        
        Args:
            positive_gt: 正检集GT（必需）- 包含目标物体的测试集
            positive_pred: 正检集预测（必需）- 对正检集的预测结果
            negative_gt: 误检集GT（可选）- 不包含目标的背景图像GT
            negative_pred: 误检集预测（可选）- 对误检集的预测结果
            iou_threshold: IoU阈值，用于判断检测是否匹配GT（默认0.5）
        """
        self.positive_gt = positive_gt
        self.positive_pred = positive_pred
        self.negative_gt = negative_gt
        self.negative_pred = negative_pred
        self.iou_threshold = iou_threshold
        
        # 验证数据集
        self._validate_datasets()
    
    def _validate_datasets(self):
        """验证数据集的有效性"""
        if self.positive_gt is None or self.positive_pred is None:
            raise ValueError("正检集的GT和Pred是必需的")
        
        if len(self.positive_gt.images) == 0:
            raise ValueError("正检集GT为空")
        
        if len(self.positive_pred.images) == 0:
            raise ValueError("正检集Pred为空")
        
        # 检查类别是否一致
        if self.positive_gt.categories != self.positive_pred.categories:
            print("警告: GT和Pred的类别映射不一致")
            print(f"  GT categories: {self.positive_gt.categories}")
            print(f"  Pred categories: {self.positive_pred.categories}")
    
    def calculate_metrics(
        self,
        confidence_threshold: float = 0.5,
        class_id: Optional[int] = None,
        calculate_fppi: bool = True
    ) -> Dict:
        """
        计算综合评估指标
        
        Args:
            confidence_threshold: 置信度阈值（动态传入，不存储在数据集中）
            class_id: 指定类别ID，None表示所有类别
            calculate_fppi: 是否计算FPPI（需要negative_pred）
        
        Returns:
            包含所有指标的字典:
                - tp, fp, fn: True/False Positives/Negatives
                - precision, recall, f1: 精确率、召回率、F1分数
                - fppi: False Positives Per Image（如果计算）
                - confidence_threshold, iou_threshold: 使用的阈值
                - positive_set_size, negative_set_size: 数据集大小
        """
        metrics = {}
        
        # 1. 从正检集计算 Precision, Recall, F1
        positive_metrics = self._calculate_positive_metrics(
            confidence_threshold, class_id
        )
        metrics.update(positive_metrics)
        
        # 2. 从误检集计算 FPPI
        if calculate_fppi and self.negative_pred is not None:
            fppi_metrics = self._calculate_fppi_metrics(
                confidence_threshold, class_id
            )
            metrics.update(fppi_metrics)
        else:
            metrics['fppi'] = None
            metrics['fppi_note'] = "未提供误检集" if self.negative_pred is None else "未计算FPPI"
        
        # 3. 添加配置信息
        metrics['confidence_threshold'] = confidence_threshold
        metrics['iou_threshold'] = self.iou_threshold
        metrics['positive_set_size'] = len(self.positive_gt.images)
        metrics['negative_set_size'] = (
            len(self.negative_pred.images) 
            if self.negative_pred else 0
        )
        
        return metrics
    
    def _calculate_positive_metrics(
        self,
        confidence_threshold: float,
        class_id: Optional[int] = None
    ) -> Dict:
        """
        从正检集计算 Precision, Recall, F1
        
        Args:
            confidence_threshold: 置信度阈值
            class_id: 指定类别ID
        
        Returns:
            包含TP, FP, FN, Precision, Recall, F1的字典
        """
        # 1. 过滤预测结果
        filtered_preds = self._filter_predictions(
            self.positive_pred, 
            confidence_threshold,
            class_id
        )
        
        # 2. 匹配GT和Pred
        tp = 0  # True Positives
        fp = 0  # False Positives
        fn = 0  # False Negatives
        
        matched_gt = set()  # 记录已匹配的GT，格式: (image_id, gt_index)
        
        # 遍历每张图像
        for img_gt in self.positive_gt.images:
            # 获取该图像的GT标注
            gt_anns = [
                ann for ann in img_gt.annotations
                if class_id is None or ann.category_id == class_id
            ]
            
            # 获取该图像的预测结果
            img_preds = filtered_preds.get(img_gt.image_id, [])
            
            # 匹配预测和GT
            for pred in img_preds:
                best_iou = 0
                best_gt_idx = -1
                
                for i, gt_ann in enumerate(gt_anns):
                    if (img_gt.image_id, i) not in matched_gt:
                        iou = self._calculate_iou(pred.bbox, gt_ann.bbox)
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = i
                
                if best_iou >= self.iou_threshold:
                    tp += 1
                    matched_gt.add((img_gt.image_id, best_gt_idx))
                else:
                    fp += 1
            
            # 统计未匹配的GT（False Negatives）
            fn += len([
                i for i in range(len(gt_anns))
                if (img_gt.image_id, i) not in matched_gt
            ])
        
        # 3. 计算指标
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall) 
              if (precision + recall) > 0 else 0.0)
        
        return {
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'positive_set_note': f"基于{len(self.positive_gt.images)}张正检图像"
        }
    
    def _calculate_fppi_metrics(
        self,
        confidence_threshold: float,
        class_id: Optional[int] = None
    ) -> Dict:
        """
        从误检集计算 FPPI (False Positives Per Image)
        
        Args:
            confidence_threshold: 置信度阈值
            class_id: 指定类别ID
        
        Returns:
            包含FPPI相关指标的字典
        """
        # 1. 过滤预测结果
        filtered_preds = self._filter_predictions(
            self.negative_pred,
            confidence_threshold,
            class_id
        )
        
        # 2. 统计误检数
        total_fp = 0
        fp_per_image = []
        
        for img_pred in self.negative_pred.images:
            img_preds = filtered_preds.get(img_pred.image_id, [])
            
            # 在误检集中，所有检测都是False Positive
            # 但如果提供了negative_gt，可以更精确地判断
            if self.negative_gt is not None:
                # 找到对应的GT图像
                gt_img = next(
                    (img for img in self.negative_gt.images 
                     if img.image_id == img_pred.image_id),
                    None
                )
                
                if gt_img is not None:
                    # 获取GT标注
                    gt_anns = [
                        ann for ann in gt_img.annotations
                        if class_id is None or ann.category_id == class_id
                    ]
                    
                    # 匹配预测和GT，未匹配的是FP
                    matched = set()
                    fp_count = 0
                    for pred in img_preds:
                        is_matched = False
                        for i, gt_ann in enumerate(gt_anns):
                            if i not in matched:
                                iou = self._calculate_iou(pred.bbox, gt_ann.bbox)
                                if iou >= self.iou_threshold:
                                    matched.add(i)
                                    is_matched = True
                                    break
                        if not is_matched:
                            fp_count += 1
                    
                    total_fp += fp_count
                    fp_per_image.append(fp_count)
                else:
                    # 没有对应的GT，所有检测都是FP
                    fp_count = len(img_preds)
                    total_fp += fp_count
                    fp_per_image.append(fp_count)
            else:
                # 没有提供negative_gt，假设所有检测都是FP
                fp_count = len(img_preds)
                total_fp += fp_count
                fp_per_image.append(fp_count)
        
        # 3. 计算FPPI
        num_images = len(self.negative_pred.images)
        fppi = total_fp / num_images if num_images > 0 else 0.0
        
        return {
            'fppi': fppi,
            'total_false_positives': total_fp,
            'negative_set_size': num_images,
            'fppi_note': f"基于{num_images}张误检图像",
            'max_fp_per_image': max(fp_per_image) if fp_per_image else 0,
            'min_fp_per_image': min(fp_per_image) if fp_per_image else 0,
            'avg_fp_per_image': total_fp / num_images if num_images > 0 else 0.0
        }
    
    def _filter_predictions(
        self,
        pred_dataset: Dataset,
        confidence_threshold: float,
        class_id: Optional[int] = None
    ) -> Dict[str, List[Annotation]]:
        """
        根据置信度阈值和类别过滤预测结果
        
        Args:
            pred_dataset: 预测数据集
            confidence_threshold: 置信度阈值
            class_id: 指定类别ID
        
        Returns:
            {image_id: [annotations]} 字典
        """
        filtered = {}
        for img in pred_dataset.images:
            img_preds = [
                ann for ann in img.annotations
                if ann.confidence >= confidence_threshold
                and (class_id is None or ann.category_id == class_id)
            ]
            if img_preds:
                filtered[img.image_id] = img_preds
        return filtered
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        计算两个边界框的IoU (Intersection over Union)
        
        Args:
            bbox1, bbox2: [x_min, y_min, width, height] 格式的边界框
        
        Returns:
            IoU值 (0.0 到 1.0)
        """
        # bbox格式: [x_min, y_min, width, height]
        x1_min, y1_min, w1, h1 = bbox1
        x2_min, y2_min, w2, h2 = bbox2
        
        x1_max = x1_min + w1
        y1_max = y1_min + h1
        x2_max = x2_min + w2
        y2_max = y2_min + h2
        
        # 计算交集
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # 计算并集
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def calculate_pr_curve(
        self,
        thresholds: Optional[List[float]] = None,
        class_id: Optional[int] = None
    ) -> List[Dict]:
        """
        计算PR曲线（不同置信度阈值下的Precision-Recall）
        
        Args:
            thresholds: 要测试的置信度阈值列表，None则使用默认值
            class_id: 指定类别ID
        
        Returns:
            每个阈值对应的指标列表
        """
        if thresholds is None:
            thresholds = [i/10 for i in range(1, 10)]  # 0.1 到 0.9
        
        pr_points = []
        for threshold in thresholds:
            # 对同一份数据，使用不同阈值计算指标
            metrics = self.calculate_metrics(
                confidence_threshold=threshold,
                class_id=class_id,
                calculate_fppi=False  # PR曲线不需要FPPI
            )
            pr_points.append({
                'threshold': threshold,
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1': metrics['f1'],
                'tp': metrics['tp'],
                'fp': metrics['fp'],
                'fn': metrics['fn']
            })
        
        return pr_points
    
    def find_optimal_threshold(
        self,
        metric: str = 'f1',
        class_id: Optional[int] = None,
        thresholds: Optional[List[float]] = None
    ) -> Dict:
        """
        找到使指定指标最优的置信度阈值
        
        Args:
            metric: 优化目标指标 ('precision', 'recall', 'f1')
            class_id: 指定类别ID
            thresholds: 要测试的阈值列表
        
        Returns:
            最优阈值及对应的所有指标
        """
        if metric not in ['precision', 'recall', 'f1']:
            raise ValueError(f"不支持的指标: {metric}")
        
        pr_curve = self.calculate_pr_curve(thresholds, class_id)
        
        # 找到指定指标最大的点
        best_point = max(pr_curve, key=lambda x: x[metric])
        
        return {
            'optimal_threshold': best_point['threshold'],
            'optimized_metric': metric,
            'metrics': best_point
        }
    
    def find_threshold_with_constraint(
        self,
        target_metric: str,
        constraint_metric: str,
        constraint_value: float,
        class_id: Optional[int] = None,
        thresholds: Optional[List[float]] = None
    ) -> Optional[Dict]:
        """
        在约束条件下找到最优阈值
        
        例如：在FPPI < 0.01的约束下，找到Recall最高的阈值
        
        Args:
            target_metric: 要优化的目标指标 ('precision', 'recall', 'f1')
            constraint_metric: 约束指标 ('fppi', 'precision', 'recall')
            constraint_value: 约束值（如 fppi < 0.01）
            class_id: 指定类别ID
            thresholds: 要测试的阈值列表
        
        Returns:
            最优阈值及对应的指标，如果无满足约束的阈值则返回None
        """
        if thresholds is None:
            thresholds = [i/100 for i in range(1, 100)]  # 0.01 到 0.99
        
        best_threshold = None
        best_value = 0
        best_metrics = None
        
        for threshold in thresholds:
            metrics = self.calculate_metrics(
                confidence_threshold=threshold,
                class_id=class_id,
                calculate_fppi=(constraint_metric == 'fppi')
            )
            
            # 检查约束条件
            constraint_satisfied = False
            if constraint_metric == 'fppi':
                if metrics['fppi'] is not None and metrics['fppi'] <= constraint_value:
                    constraint_satisfied = True
            elif constraint_metric in metrics:
                if metrics[constraint_metric] >= constraint_value:
                    constraint_satisfied = True
            
            # 如果满足约束，检查是否是最优的
            if constraint_satisfied:
                if metrics[target_metric] > best_value:
                    best_value = metrics[target_metric]
                    best_threshold = threshold
                    best_metrics = metrics
        
        if best_threshold is None:
            return None
        
        return {
            'optimal_threshold': best_threshold,
            'target_metric': target_metric,
            'target_value': best_value,
            'constraint': f"{constraint_metric} <= {constraint_value}",
            'metrics': best_metrics
        }
    
    def generate_report(
        self,
        confidence_threshold: float = 0.5,
        class_id: Optional[int] = None
    ) -> str:
        """
        生成评估报告
        
        Args:
            confidence_threshold: 置信度阈值
            class_id: 指定类别ID
        
        Returns:
            格式化的评估报告字符串
        """
        metrics = self.calculate_metrics(confidence_threshold, class_id)
        
        class_name = "所有类别"
        if class_id is not None and class_id in self.positive_gt.categories:
            class_name = f"类别 {class_id} ({self.positive_gt.categories[class_id]})"
        
        report = f"""
{'='*60}
评估报告 - {class_name}
{'='*60}

配置信息:
  置信度阈值: {metrics['confidence_threshold']}
  IoU阈值: {metrics['iou_threshold']}
  正检集大小: {metrics['positive_set_size']} 张图像
  误检集大小: {metrics['negative_set_size']} 张图像

正检集指标 (Precision & Recall):
  True Positives (TP):  {metrics['tp']}
  False Positives (FP): {metrics['fp']}
  False Negatives (FN): {metrics['fn']}
  
  Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)
  Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)
  F1-Score:  {metrics['f1']:.4f}
"""
        
        if metrics['fppi'] is not None:
            report += f"""
误检集指标 (FPPI):
  FPPI (False Positives Per Image): {metrics['fppi']:.6f}
  总误检数: {metrics.get('total_false_positives', 'N/A')}
  平均每图误检数: {metrics.get('avg_fp_per_image', 'N/A'):.2f}
  单图最大误检数: {metrics.get('max_fp_per_image', 'N/A')}
  单图最小误检数: {metrics.get('min_fp_per_image', 'N/A')}
"""
        else:
            report += f"""
误检集指标 (FPPI):
  {metrics['fppi_note']}
"""
        
        report += f"\n{'='*60}\n"
        
        return report

