"""
Training module for MedVision.
"""

import os
import torch
import json
import shutil
from typing import Dict, Any
from pathlib import Path
import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.utilities import rank_zero_only
from medvision.models import get_model
from medvision.datasets import get_datamodule
from medvision.utils.onnx_utils import convert_models_to_onnx


import os
import json
import torch
from pytorch_lightning.utilities import rank_zero_only


@rank_zero_only
def convert_to_onnx_if_needed(checkpoint_callback, model, datamodule, config):
    convert_flag = config["training"].get(
        "convert_to_onnx", config["training"].get("export_onnx", False)
    )
    if not convert_flag:
        return [], None

    print("\n" + "=" * 50)
    print("Converting models to ONNX format...")
    print("=" * 50)

    try:
        converted_models, onnx_dir = convert_models_to_onnx(
            checkpoint_callback, model.__class__, config["model"], datamodule
        )
        print(f"\n✓ ONNX conversion completed!")
        print(f"✓ Saved to: {onnx_dir}")
        print(f"✓ {len(converted_models)} models converted.")
    except Exception as e:
        print(f"❌ ONNX conversion failed: {e}")
        converted_models, onnx_dir = [], None

    print("=" * 50 + "\n")
    return converted_models, onnx_dir


@rank_zero_only
def save_training_results(train_val_results, checkpoint_callback, test_results, converted_models, onnx_dir, config):
    train_results = train_val_results
    train_val_metrics = {
        k: float(v)
        for k, v in train_results.items()
        if isinstance(v, torch.Tensor)
        and (k.startswith("val/") or k.startswith("train/"))
    }
    test_metrics = {k: float(v) for k, v in test_results[0].items()} if test_results else {}

    final_metrics = {
        "train_val_metrics": train_val_metrics,
        "test_metrics": test_metrics,
        "best_model_path": checkpoint_callback.best_model_path,
        "best_model_score": float(checkpoint_callback.best_model_score)
        if checkpoint_callback.best_model_score is not None
        else None,
        "monitor": config["training"].get("monitor", "val_loss"),
    }

    if converted_models:
        final_metrics["onnx_conversion"] = {
            "converted_count": len(converted_models),
            "onnx_directory": onnx_dir,
            "models": converted_models,
        }

    result_path = os.path.join(config["training"]["output_dir"], "results.json")
    with open(result_path, "w") as f:
        json.dump(final_metrics, f, indent=4)
    print(f"Final metrics saved to: {result_path}")

@rank_zero_only
def merge_into_results(dataset_stats_path, results_path):
    with open(dataset_stats_path, "r") as f:
        data1 = json.load(f)
    with open(results_path, "r") as f:
        data2 = json.load(f)

    if isinstance(data1, dict) and isinstance(data2, dict):
        merged = {**data1, **data2}  # results.json 的字段覆盖 dataset_stats.json
    elif isinstance(data1, list) and isinstance(data2, list):
        merged = data1 + data2
    else:
        raise ValueError("JSON types do not match or are unsupported")

    with open(results_path, "w") as f:
        json.dump(merged, f, indent=2)

    return results_path


def train_model(config: Dict[str, Any]) -> None:
    """
    Train a model based on the provided configuration.
    
    Args:
        config: Configuration dictionary
    """
    print("Starting training...")
    
    # Set random seed for reproducibility
    pl.seed_everything(config.get("seed", 42))
    
    # Create the model
    model = get_model(config["model"])
    
    # Create data module
    datamodule = get_datamodule(config["data"])
    
    # Configure callbacks
    callbacks = []

    checkpoint_callback = ModelCheckpoint(
        dirpath=os.path.join(config["training"]["output_dir"], "checkpoints"),
        filename=f"{config['training'].get('experiment_name')}",
        monitor=config["training"].get("monitor", "val_loss"),
        mode=config["training"].get("monitor_mode", "min"),
        save_top_k=config["training"].get("save_top_k", 1),
        save_last=False,
    )

    callbacks.append(checkpoint_callback)
    
    # EarlyStopping callback
    if config["training"].get("early_stopping", False):
        early_stop_callback = EarlyStopping(
            monitor=config["training"].get("monitor", "val_loss"),
            mode=config["training"].get("monitor_mode", "min"),
            patience=config["training"].get("patience", 10),
            verbose=True,
        )
        callbacks.append(early_stop_callback)
        
    # Configure logger
    logger = TensorBoardLogger(
        save_dir=config["training"]["output_dir"],
        name="logs",
        version=config["training"].get("version", None),
    )
    
    # Create trainer
    trainer = pl.Trainer(
        max_epochs=config["training"].get("max_epochs", 100),
        devices=config["training"].get("devices", 'auto'),
        accelerator=config["training"].get("accelerator", "gpu"),
        strategy=config["training"].get("strategy", 'ddp'),
        precision=config["training"].get("precision", 32),
        callbacks=callbacks,
        logger=logger,
        log_every_n_steps=config["training"].get("log_every_n_steps", 10),
        deterministic=config["training"].get("deterministic", False),
        gradient_clip_val=config["training"].get("gradient_clip_val", 0.0),
        check_val_every_n_epoch=config["training"].get("check_val_every_n_epoch", 1)
        
    )

    trainer.fit(model, datamodule=datamodule)
    train_results = trainer.logged_metrics

    converted_models, onnx_dir = (convert_to_onnx_if_needed(
        checkpoint_callback, model, datamodule, config
    ) or ([], None))

    test_results = trainer.test(model, datamodule=datamodule)

    if config["training"].get("save_metrics", True):
        save_training_results(
            train_results, checkpoint_callback, test_results, converted_models, onnx_dir, config
        )

    # move dataset summary logging to outputs dir and merge with results.json
    merged_file = merge_into_results(os.path.join(config['data']['data_dir'], "dataset_stats.json"), os.path.join(config["training"]["output_dir"], "results.json"))
    print(f"Merged JSON saved to {merged_file}")
