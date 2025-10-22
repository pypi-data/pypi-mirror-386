"""
评估系统使用示例

演示如何使用dataset_toolkit进行模型评估：
1. 加载GT数据集（正检集和误检集）
2. 加载预测结果
3. 计算评估指标（Precision, Recall, F1, FPPI）
4. 测试不同置信度阈值
5. 找到最优阈值
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_toolkit import (
    load_yolo_from_local,
    load_predictions_from_streamlined,
    Evaluator
)


def main():
    print("="*60)
    print("评估系统使用示例")
    print("="*60)
    
    # ============================================================
    # 1. 配置路径（请根据实际情况修改）
    # ============================================================
    
    # 正检集路径
    positive_gt_path = "/opt/dlami/nvme/workspace_wenxiang/parcel/test_val/labels"
    positive_pred_path = "/opt/dlami/nvme/workspace_wenxiang/ai_train/onnx_infer/detections/results/streamlined_test"
    positive_image_path = "/opt/dlami/nvme/workspace_wenxiang/parcel/test_val/images"
    
    # 误检集路径（可选）
    negative_pred_path = None  # 如果有误检集，设置路径
    negative_image_path = None
    
    # 类别映射
    categories = {0: 'parcel'}
    
    # ============================================================
    # 2. 加载数据集
    # ============================================================
    
    print("\n步骤1: 加载数据集...")
    print("-" * 60)
    
    # 加载正检集GT
    print("\n加载正检集GT...")
    gt_positive = load_yolo_from_local(
        positive_gt_path,
        categories=categories
    )
    gt_positive.dataset_type = "gt"
    gt_positive.metadata = {
        "test_purpose": "positive",
        "description": "包含目标物体的测试集"
    }
    print(f"✓ 正检集GT: {len(gt_positive.images)} 张图像")
    
    # 加载正检集预测
    print("\n加载正检集预测结果...")
    pred_positive = load_predictions_from_streamlined(
        positive_pred_path,
        categories=categories,
        image_dir=positive_image_path
    )
    pred_positive.dataset_type = "pred"
    pred_positive.metadata = {
        "test_purpose": "positive",
        "model_name": "yolov8_parcel"
    }
    print(f"✓ 正检集Pred: {len(pred_positive.images)} 张图像")
    
    # 加载误检集预测（如果有）
    pred_negative = None
    if negative_pred_path:
        print("\n加载误检集预测结果...")
        pred_negative = load_predictions_from_streamlined(
            negative_pred_path,
            categories=categories,
            image_dir=negative_image_path
        )
        pred_negative.dataset_type = "pred"
        pred_negative.metadata = {
            "test_purpose": "negative",
            "model_name": "yolov8_parcel"
        }
        print(f"✓ 误检集Pred: {len(pred_negative.images)} 张图像")
    else:
        print("\n未提供误检集，将只计算Precision/Recall/F1")
    
    # ============================================================
    # 3. 创建评估器
    # ============================================================
    
    print("\n步骤2: 创建评估器...")
    print("-" * 60)
    
    evaluator = Evaluator(
        positive_gt=gt_positive,
        positive_pred=pred_positive,
        negative_pred=pred_negative,
        iou_threshold=0.5
    )
    print("✓ 评估器创建成功")
    
    # ============================================================
    # 4. 计算单个阈值的指标
    # ============================================================
    
    print("\n步骤3: 计算评估指标（置信度阈值=0.5）...")
    print("-" * 60)
    
    metrics = evaluator.calculate_metrics(
        confidence_threshold=0.5,
        class_id=0  # 只评估parcel类别
    )
    
    print(f"\n正检集指标:")
    print(f"  TP: {metrics['tp']}, FP: {metrics['fp']}, FN: {metrics['fn']}")
    print(f"  Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"  Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"  F1-Score:  {metrics['f1']:.4f}")
    
    if metrics['fppi'] is not None:
        print(f"\n误检集指标:")
        print(f"  FPPI: {metrics['fppi']:.6f}")
        print(f"  总误检数: {metrics['total_false_positives']}")
    
    # ============================================================
    # 5. 测试多个阈值
    # ============================================================
    
    print("\n步骤4: 测试多个置信度阈值...")
    print("-" * 60)
    
    test_thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    
    print(f"\n{'阈值':<10} {'Precision':<12} {'Recall':<12} {'F1':<12} {'FPPI':<12}")
    print("-" * 60)
    
    for threshold in test_thresholds:
        m = evaluator.calculate_metrics(
            confidence_threshold=threshold,
            class_id=0
        )
        fppi_str = f"{m['fppi']:.6f}" if m['fppi'] is not None else "N/A"
        print(f"{threshold:<10.2f} {m['precision']:<12.4f} {m['recall']:<12.4f} "
              f"{m['f1']:<12.4f} {fppi_str:<12}")
    
    # ============================================================
    # 6. 找到最优阈值
    # ============================================================
    
    print("\n步骤5: 寻找最优阈值...")
    print("-" * 60)
    
    # 找到F1最高的阈值
    optimal = evaluator.find_optimal_threshold(
        metric='f1',
        class_id=0
    )
    
    print(f"\n最优阈值（F1最大）:")
    print(f"  阈值: {optimal['optimal_threshold']}")
    print(f"  Precision: {optimal['metrics']['precision']:.4f}")
    print(f"  Recall:    {optimal['metrics']['recall']:.4f}")
    print(f"  F1-Score:  {optimal['metrics']['f1']:.4f}")
    
    # 如果有误检集，找到FPPI约束下的最优阈值
    if pred_negative:
        constrained = evaluator.find_threshold_with_constraint(
            target_metric='recall',
            constraint_metric='fppi',
            constraint_value=0.01,  # FPPI < 0.01
            class_id=0
        )
        
        if constrained:
            print(f"\n最优阈值（FPPI < 0.01约束下，Recall最大）:")
            print(f"  阈值: {constrained['optimal_threshold']}")
            print(f"  Recall: {constrained['target_value']:.4f}")
            print(f"  FPPI:   {constrained['metrics']['fppi']:.6f}")
        else:
            print(f"\n警告: 无法找到满足 FPPI < 0.01 约束的阈值")
    
    # ============================================================
    # 7. 生成完整报告
    # ============================================================
    
    print("\n步骤6: 生成完整评估报告...")
    print("-" * 60)
    
    report = evaluator.generate_report(
        confidence_threshold=0.5,
        class_id=0
    )
    print(report)
    
    # ============================================================
    # 8. 计算PR曲线数据（可用于绘图）
    # ============================================================
    
    print("\n步骤7: 计算PR曲线数据...")
    print("-" * 60)
    
    pr_curve = evaluator.calculate_pr_curve(
        thresholds=[i/10 for i in range(1, 10)],
        class_id=0
    )
    
    print(f"\nPR曲线数据点: {len(pr_curve)} 个")
    print(f"{'阈值':<10} {'Precision':<12} {'Recall':<12}")
    print("-" * 40)
    for point in pr_curve[:5]:  # 只显示前5个
        print(f"{point['threshold']:<10.2f} {point['precision']:<12.4f} {point['recall']:<12.4f}")
    print("...")
    
    print("\n" + "="*60)
    print("评估完成！")
    print("="*60)
    
    # 可以将PR曲线数据保存或绘图
    # import matplotlib.pyplot as plt
    # precisions = [p['precision'] for p in pr_curve]
    # recalls = [p['recall'] for p in pr_curve]
    # plt.plot(recalls, precisions)
    # plt.xlabel('Recall')
    # plt.ylabel('Precision')
    # plt.title('PR Curve')
    # plt.savefig('pr_curve.png')


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("\n请修改脚本中的路径配置，指向实际的数据集位置。")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

