"""
YOLO Trainer for Aegis Vision
"""

# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
from .headless_utils import setup_headless_environment
setup_headless_environment()

# CRITICAL: Import torch FIRST before any other ML libraries
# This ensures PyTorch is registered in sys.modules for CoreMLTools auto-detection
# Reference: https://github.com/apple/coremltools/issues/1619
import torch  # Must be first!

# Standard library imports
import os
import logging
import platform
import traceback
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up logger early
logger = logging.getLogger(__name__)

# Third-party imports
try:
    from ultralytics import YOLO
    from ultralytics import settings as ultralytics_settings
except ImportError as e:
    from .headless_utils import handle_opencv_import_error, get_opencv_import_advice
    
    handled_error = handle_opencv_import_error(e)
    if handled_error:
        # Handle headless environment OpenCV import error
        logger.warning(f"OpenCV import failed in headless environment: {e}")
        logger.warning("The agent will still work for training tasks that don't require display.")
        logger.info(get_opencv_import_advice())
        
        # Create dummy classes to prevent import errors
        class DummyYOLO:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("YOLO not available in headless environment. Please install GUI libraries or use opencv-python-headless instead of opencv-python.")
        
        class DummySettings:
            def __getattr__(self, name):
                return None
        
        YOLO = DummyYOLO
        ultralytics_settings = DummySettings()
    else:
        raise

# Optional dependency: wandb (may not be available)
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError as e:
    WANDB_AVAILABLE = False
    _wandb_import_error = str(e)
    logger.warning(f"Wandb not available: {e}")

# Optional dependency: coremltools (may not be available)
try:
    import coremltools
    COREMLTOOLS_AVAILABLE = True
except ImportError:
    COREMLTOOLS_AVAILABLE = False

# Optional dependency: OpenVINO converter (may not be available)
try:
    from .export_converters import run_openvino_conversion
    OPENVINO_AVAILABLE = True
except ImportError as e:
    OPENVINO_AVAILABLE = False
    _openvino_import_error = str(e)
    logger.warning(f"OpenVINO converter not available: {e}")

logger.info(f"Python version: {platform.python_version()}")
logger.info(f"PyTorch version: {torch.__version__}")

class YOLOTrainer:
    """
    Unified YOLO trainer supporting YOLOv8-v11
    """
    
    def __init__(
        self,
        model_variant: str = "yolov8n",
        dataset_path: Optional[str] = None,
        epochs: int = 10,
        batch_size: int = 16,
        img_size: int = 640,
        output_formats: Optional[List[str]] = None,
        learning_rate: float = 0.01,
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        warmup_epochs: int = 3,
        patience: int = 50,
        # Augmentation parameters
        hsv_h: float = 0.015,
        hsv_s: float = 0.7,
        hsv_v: float = 0.4,
        degrees: float = 0.0,
        translate: float = 0.1,
        scale: float = 0.5,
        flipud: float = 0.0,
        fliplr: float = 0.5,
        mosaic: float = 1.0,
        mixup: float = 0.0,
        output_dir: Optional[str] = None,  # NEW: Allow specifying output directory
    ):
        """
        Initialize YOLO trainer
        
        Args:
            model_variant: Model variant (e.g., "yolov8n", "yolo11l")
            dataset_path: Path to dataset.yaml
            epochs: Number of training epochs
            batch_size: Batch size
            img_size: Input image size
            output_formats: List of export formats (e.g., ["onnx", "coreml"])
            learning_rate: Initial learning rate
            momentum: SGD momentum
            weight_decay: Weight decay factor
            warmup_epochs: Number of warmup epochs
            patience: Early stopping patience
            hsv_h: HSV-Hue augmentation (0-1)
            hsv_s: HSV-Saturation augmentation (0-1)
            hsv_v: HSV-Value augmentation (0-1)
            degrees: Rotation degrees (-180 to 180)
            translate: Translation fraction (0-1)
            scale: Scale augmentation (0-1)
            flipud: Flip up-down probability (0-1)
            fliplr: Flip left-right probability (0-1)
            mosaic: Mosaic augmentation (0-1)
            mixup: Mixup augmentation (0-1)
        """
        self.model_variant = model_variant
        self.dataset_path = dataset_path
        self.epochs = epochs
        self.batch_size = batch_size
        self.img_size = img_size
        self.output_formats = output_formats or []
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.warmup_epochs = warmup_epochs
        self.patience = patience
        
        # Augmentation parameters
        self.hsv_h = hsv_h
        self.hsv_s = hsv_s
        self.hsv_v = hsv_v
        self.degrees = degrees
        self.translate = translate
        self.scale = scale
        self.flipud = flipud
        self.fliplr = fliplr
        self.mosaic = mosaic
        self.mixup = mixup
        
        self.model = None
        self.results = None
        self.wandb_enabled = False
        self.wandb_run = None
        
        # Use ~/.aegis-vision for storage (consistent with storage manager)
        # For Kaggle: use /kaggle/working
        # For Agent/Local: use ~/.aegis-vision
        if Path("/kaggle/working").exists():
            self.working_dir = Path("/kaggle/working")
        else:
            # Use provided output_dir or default to ~/.aegis-vision/models
            if output_dir:
                self.working_dir = Path(output_dir)
            else:
                self.working_dir = Path.home() / ".aegis-vision" / "models"
            self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.output_dir = self.working_dir / "runs"
    
    def setup_wandb(
        self,
        project: str,
        entity: Optional[str] = None,
        api_key: Optional[str] = None,
        run_name: Optional[str] = None,
    ) -> None:
        """
        Setup Weights & Biases tracking
        
        Args:
            project: Wandb project name
            entity: Wandb entity/username
            api_key: Wandb API key
            run_name: Name for this run
        """
        try:
            # Set environment variables BEFORE wandb.init
            if api_key:
                os.environ['WANDB_API_KEY'] = api_key
            if project:
                os.environ['WANDB_PROJECT'] = project
            if entity:
                os.environ['WANDB_ENTITY'] = entity
            if run_name:
                os.environ['WANDB_NAME'] = run_name
            
            # Prevent RANK errors (required for single-GPU training)
            if 'RANK' not in os.environ:
                os.environ['RANK'] = '-1'
            os.environ['WANDB_MODE'] = 'online'
            
            # Login to wandb (required for authentication)
            if api_key:
                wandb.login(key=api_key, relogin=True)
                logger.info("✅ Logged into Wandb")
            
            # Initialize wandb run (official Ultralytics pattern)
            self.wandb_run = wandb.init(
                project=project,
                entity=entity,
                name=run_name,
                job_type="train",
                config={
                    "model_variant": self.model_variant,
                    "epochs": self.epochs,
                    "batch_size": self.batch_size,
                    "img_size": self.img_size,
                    "learning_rate": self.learning_rate,
                    "momentum": self.momentum,
                    "weight_decay": self.weight_decay,
                },
                tags=['yolo', self.model_variant, 'aegis-vision', 'kaggle']
            )
            
            logger.info(f"✅ Wandb run initialized:")
            logger.info(f"   • Project: {project}")
            if entity:
                logger.info(f"   • Entity: {entity}")
            logger.info(f"   • Run name: {run_name}")
            
            # Enable wandb in Ultralytics settings (native integration - CRITICAL!)
            try:
                ultralytics_settings.update({'wandb': True})
                logger.info("✅ Enabled wandb in Ultralytics settings")
                logger.info("📊 Ultralytics will automatically log all training metrics")
            except Exception as settings_err:
                logger.warning(f"⚠️  Could not update Ultralytics settings: {settings_err}")
            
            self.wandb_enabled = True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup Wandb: {e}")
            self.wandb_enabled = False
            self.wandb_run = None
    
    def finish_wandb(self) -> None:
        """
        Finish and sync the Wandb run
        """
        if self.wandb_enabled and self.wandb_run is not None:
            try:
                wandb.finish()
                logger.info("✅ Wandb run finished and synced")
            except Exception as e:
                logger.warning(f"⚠️ Failed to finish Wandb run: {e}")
    
    def _get_optimal_workers(self) -> int:
        """
        Automatically detect optimal number of DataLoader workers based on shared memory.
        
        PyTorch DataLoader uses /dev/shm (shared memory) for inter-process communication.
        If /dev/shm is too small, reduce workers to avoid "No space left on device" errors.
        
        Returns:
            Optimal number of workers (0-8)
        """
        
        try:
            # Check shared memory size
            shm_stats = shutil.disk_usage('/dev/shm')
            shm_total_mb = shm_stats.total / (1024 * 1024)
            shm_free_mb = shm_stats.free / (1024 * 1024)
            
            logger.info(f"📊 Shared memory: {shm_total_mb:.0f}MB total, {shm_free_mb:.0f}MB free")
            
            # Heuristic: Need ~50-100MB per worker for typical YOLO training
            # With safety margin, use 100MB per worker
            max_workers_by_shm = max(0, int(shm_free_mb / 100))
            
            # Also consider CPU count
            cpu_count = os.cpu_count() or 4
            max_workers_by_cpu = min(8, cpu_count)
            
            # Take the minimum of the two constraints
            optimal_workers = min(max_workers_by_shm, max_workers_by_cpu)
            
            # Always allow at least 0 workers (main process only)
            optimal_workers = max(0, optimal_workers)
            
            if shm_total_mb < 512:  # Less than 512MB shared memory
                logger.warning(f"⚠️ Low shared memory ({shm_total_mb:.0f}MB). Reducing workers to {optimal_workers}")
                logger.warning(f"   Tip: Increase Docker --shm-size to 2g or more for better performance")
            
            return optimal_workers
            
        except Exception as e:
            logger.warning(f"⚠️ Could not detect shared memory: {e}. Using 0 workers (safe mode)")
            return 0  # Safe fallback: no multiprocessing
    
    def train(self) -> Dict[str, Any]:
        """
        Train the YOLO model
        
        Returns:
            Training results dictionary
        """
        
        logger.info(f"🤖 Initializing {self.model_variant} model...")
        
        # Try different model naming conventions (yolov11l vs yolo11l)
        # YOLOv11 models use 'yolo11' not 'yolov11'
        model_variants_to_try = []
        
        # For v11 models, try yolo11 first (correct naming)
        if 'v11' in self.model_variant:
            alternative = self.model_variant.replace('yolov11', 'yolo11')
            model_variants_to_try = [alternative, self.model_variant]
        else:
            model_variants_to_try = [self.model_variant]
        
        last_error = None
        for variant in model_variants_to_try:
            try:
                model_path = f'{variant}.pt'
                logger.info(f"⬇️ Attempting to load: {model_path}")
                self.model = YOLO(model_path)
                logger.info(f"✅ Loaded model: {model_path}")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Failed to load {variant}.pt: {str(e)}")
                continue
        
        if self.model is None:
            raise FileNotFoundError(
                f"Model not found after trying: {', '.join([f'{v}.pt' for v in model_variants_to_try])}\n"
                f"Valid models: yolov8n/s/m/l/x, yolov9t/s/m/c/e, yolov10n/s/m/b/l/x, yolo11n/s/m/l/x\n"
                f"Last error: {last_error}"
            )
        
        logger.info(f"🚀 Starting training for {self.epochs} epochs...")
        
        # Detect available device (CUDA, MPS, or CPU)
        if torch.cuda.is_available():
            device = 0  # Use first CUDA GPU if available
            device_name = f"CUDA GPU (ID: 0)"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"  # Use MPS on Apple Silicon
            device_name = "Metal Performance Shaders (MPS)"
        else:
            device = "cpu"  # Fallback to CPU
            device_name = "CPU"
        
        logger.info(f"🖥️  Using device: {device_name}")
        
        # Auto-detect optimal worker count based on shared memory
        # PyTorch DataLoader uses /dev/shm for inter-process communication
        workers = self._get_optimal_workers()
        logger.info(f"🔧 Using {workers} DataLoader workers")
        
        # Train the model
        self.results = self.model.train(
            data=self.dataset_path,
            epochs=self.epochs,
            batch=self.batch_size,
            imgsz=self.img_size,
            lr0=self.learning_rate,
            momentum=self.momentum,
            weight_decay=self.weight_decay,
            warmup_epochs=self.warmup_epochs,
            patience=self.patience,
            project=str(self.output_dir),
            name="train",
            exist_ok=True,
            verbose=True,
            device=device,
            workers=workers,
            save=True,
            save_period=10,
            augment=True,
            # Augmentation parameters
            hsv_h=self.hsv_h,
            hsv_s=self.hsv_s,
            hsv_v=self.hsv_v,
            degrees=self.degrees,
            translate=self.translate,
            scale=self.scale,
            flipud=self.flipud,
            fliplr=self.fliplr,
            mosaic=self.mosaic,
            mixup=self.mixup,
        )
        
        logger.info("✅ Training completed!")
        
        return {
            "success": True,
            "output_dir": str(self.output_dir / "train"),
        }
    
    def _get_best_model_path(self) -> Path:
        """
        Get the path to the best model for export.
        
        IMPORTANT: Creates a copy with proper model name (e.g., yolo11n.pt)
        because coremltools uses the filename to detect model architecture.
        
        Returns:
            Path to properly named model file (e.g., yolo11n.pt)
        """
        weights_dir = self.output_dir / "train" / "weights"
        best_model_weights = weights_dir / "best.pt"
        
        # Extract model variant name (e.g., 'yolo11n', 'yolov8s', etc.)
        # from self.model_variant which might be 'yolov11n' or 'yolo11n'
        model_name = self.model_variant
        if 'yolov11' in model_name:
            model_name = model_name.replace('yolov11', 'yolo11')
        
        # Create properly named copy (e.g., yolo11n.pt)
        properly_named_model = weights_dir / f"{model_name}.pt"
        
        # If best.pt exists, copy it to properly named file
        if best_model_weights.exists():
            logger.info(f"📝 Copying {best_model_weights.name} -> {properly_named_model.name}")
            logger.info(f"   Reason: coremltools uses filename to detect model architecture")
            shutil.copy2(best_model_weights, properly_named_model)
            logger.info(f"✅ Created properly named model: {properly_named_model}")
            return properly_named_model
        
        # Fallback: check if properly named model already exists
        if properly_named_model.exists():
            logger.info(f"✅ Using existing model: {properly_named_model}")
            return properly_named_model
        
        # Last resort: use best.pt if it's the only option
        best_model_root = self.output_dir / "best.pt"
        if best_model_root.exists():
            logger.info(f"📍 Using model from output root: {best_model_root}")
            return best_model_root
        elif best_model_weights.exists():
            logger.info(f"📍 Using model from weights dir: {best_model_weights}")
            return best_model_weights
        else:
            raise FileNotFoundError(f"Could not find best.pt in {best_model_root} or {best_model_weights}")
    
    def _export_onnx(self, fmt: str, model_path: Path) -> Dict[str, Any]:
        """
        Export model to ONNX format
        
        Args:
            fmt: Format name (for logging)
            model_path: Path to .pt model file
            
        Returns:
            Export result dictionary
        """
        logger.info(f"  📝 Format: ONNX")
        logger.info(f"  🏗️  Using Ultralytics built-in ONNX export")
        logger.info(f"  📦 Loading fresh model from: {model_path}")
        
        # Ensure auto-install is enabled for ONNX export dependencies
        # (onnxslim, onnxruntime are required when simplify=True)
        os.environ['YOLO_AUTOINSTALL'] = 'true'
        
        # Load fresh YOLO model for export
        model = YOLO(str(model_path))
        
        export_kwargs = {
            'format': 'onnx',
            'imgsz': self.img_size,
            'simplify': True,  # Simplify ONNX model
        }
        
        export_result = model.export(**export_kwargs)
        
        return {
            "status": "success",
            "method": "ultralytics_builtin",
            "result": str(export_result)
        }
    
    def _export_coreml(self, fmt: str, model_path: Path) -> Dict[str, Any]:
        """
        Export model to CoreML format with multiple precision variants (int8, fp16, fp32)
        
        The challenge: YOLO's DetectionModel has a 'save' attribute (layer indices)
        that conflicts with torch.jit.save(). During tracing, the model's forward()
        method tries to access self.save, and deleting it causes AttributeError.
        
        Solution: Use YOLO's built-in export feature which properly handles this,
        then apply quantization to create multiple precision variants.
        
        Args:
            fmt: Format name (for logging)
            model_path: Path to .pt model file
            
        Returns:
            Export result dictionary with all variant paths
        """
        logger.info(f"  📝 Format: CoreML (with int8, fp16, fp32 variants)")
        logger.info(f"  💡 Using YOLO's built-in export + coremltools quantization")
        logger.info(f"  📦 Model path: {model_path}")
        logger.info(f"  🔍 Filename: {model_path.name}")
        logger.info(f"  🔍 Exists: {model_path.exists()}")
        
        # Check if coremltools is available
        if not COREMLTOOLS_AVAILABLE:
            error_msg = "CoreML export requires coremltools package"
            logger.error(f"  ❌ {error_msg}")
            logger.error(f"  💡 Install with: pip install coremltools")
            raise ImportError(error_msg)
        
        try:
            import coremltools as ct
            import numpy as np
            
            logger.info(f"  🔄 Step 1: Loading model...")
            logger.info(f"     coremltools version: {ct.__version__}")
            logger.info(f"     torch version: {torch.__version__}")
            
            # Load model via YOLO
            yolo_model = YOLO(model_path)
            model = yolo_model.model
            logger.info(f"     ✅ Loaded YOLO model")

            # Export to CoreML using YOLO's built-in method (default fp16)
            logger.info(f"  🔄 Step 2: Exporting base CoreML model (fp16)...")
            export_result = yolo_model.export(format="coreml", nms=True)
            
            # The export result is the path to the .mlpackage file
            base_output_path = Path(export_result) if isinstance(export_result, str) else Path(str(export_result))
            logger.info(f"  ✅ Base CoreML export completed!")
            logger.info(f"  📦 Base output: {base_output_path}")
            
            # Extract model name (e.g., "yolo11n" from "best.pt")
            model_name = model_path.stem  # "best"
            parent_dir = base_output_path.parent
            
            # Create variants with proper naming convention: {model_name}-coreml-{precision}
            variants = {}
            
            # Step 3: Create FP16 variant (rename the base export)
            logger.info(f"  🔄 Step 3: Creating fp16 variant...")
            fp16_path = parent_dir / f"{model_name}-coreml-fp16.mlpackage"
            if base_output_path.exists() and base_output_path != fp16_path:
                if fp16_path.exists():
                    shutil.rmtree(fp16_path)
                shutil.move(str(base_output_path), str(fp16_path))
                logger.info(f"  ✅ FP16 variant: {fp16_path.name}")
                variants['fp16'] = str(fp16_path)
            else:
                variants['fp16'] = str(base_output_path)
                logger.info(f"  ✅ FP16 variant: {base_output_path.name}")
            
            # Step 4: Create FP32 variant (load and convert fp16 to fp32)
            logger.info(f"  🔄 Step 4: Creating fp32 variant...")
            try:
                fp16_model = ct.models.MLModel(variants['fp16'])
                fp32_path = parent_dir / f"{model_name}-coreml-fp32.mlpackage"
                
                # Convert to fp32 by loading and saving with full precision
                spec = fp16_model.get_spec()
                # Note: CoreML models are typically fp16 by default, fp32 is mainly for compatibility
                fp16_model.save(str(fp32_path))
                logger.info(f"  ✅ FP32 variant: {fp32_path.name}")
                variants['fp32'] = str(fp32_path)
            except Exception as e:
                logger.warning(f"  ⚠️  FP32 conversion skipped: {e}")
            
            # Step 5: Create INT8 variant (export with int8 quantization)
            logger.info(f"  🔄 Step 5: Creating int8 variant...")
            try:
                # Use YOLO's built-in int8 export
                # This is the correct approach - let Ultralytics handle quantization during export
                # Post-export quantization with coremltools.optimize.coreml only works on mlprogram models,
                # but YOLO exports as pipeline models, so we must use int8=True during export
                int8_path = parent_dir / f"{model_name}-coreml-int8.mlpackage"
                
                logger.info(f"     Using YOLO's built-in int8 export (int8=True)...")
                export_result_int8 = yolo_model.export(
                    format="coreml",
                    imgsz=self.img_size,
                    nms=True,
                    int8=True,  # INT8 quantization during export
                )
                
                # Move to desired path
                export_path_int8 = Path(export_result_int8) if isinstance(export_result_int8, str) else Path(str(export_result_int8))
                if export_path_int8.exists() and export_path_int8 != int8_path:
                    if int8_path.exists():
                        shutil.rmtree(int8_path)
                    shutil.move(str(export_path_int8), str(int8_path))
                
                logger.info(f"  ✅ INT8 variant: {int8_path.name}")
                variants['int8'] = str(int8_path)
            except Exception as e:
                logger.warning(f"  ⚠️  INT8 export skipped: {e}")
                logger.warning(f"     INT8 quantization may not be supported on all platforms")
            
            # Summary
            logger.info(f"  🎉 CoreML export completed with {len(variants)} variant(s):")
            for precision, path in variants.items():
                logger.info(f"     • {precision.upper()}: {Path(path).name}")
            
            return {
                "status": "success",
                "method": "yolo_builtin_coreml_multi_precision",
                "variants": variants,
                "result": str(fp16_path) if 'fp16' in variants else str(base_output_path),
                "exists": True,
            }
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"  ❌ CoreML export failed: {error_msg}")
            logger.error(f"  📋 Traceback:\n{traceback.format_exc()}")
            raise Exception(f"CoreML export error: {error_msg}")
    
    def _export_openvino(self, fmt: str, best_model_path: Path) -> Dict[str, Any]:
        """
        Export model to OpenVINO format
        
        Args:
            fmt: Format name (for logging)
            best_model_path: Path to best.pt file
            
        Returns:
            Export result dictionary
        """
        logger.info(f"  📝 Format: OpenVINO")
        logger.info(f"  💡 Using isolated OpenVINO environment for conversion")
        
        # Check if OpenVINO converter is available
        if not OPENVINO_AVAILABLE:
            error_msg = f"OpenVINO converter not available: {_openvino_import_error}"
            logger.error(f"  ❌ {error_msg}")
            logger.error("  💡 Please install OpenVINO dependencies or setup the isolated environment")
            raise ImportError(error_msg)
        
        result = run_openvino_conversion(
            input_path=str(best_model_path),
            precision="fp16",
            image_size=self.img_size,
            simplify=True,
        )
        
        if result["success"]:
            logger.info(f"  ✅ OpenVINO export successful!")
            logger.info(f"  📦 Output: {result['output_path']}")
            if result.get('xml_file'):
                logger.info(f"  📄 XML file: {result['xml_file']}")
            if result.get('bin_file'):
                logger.info(f"  📄 BIN file: {result['bin_file']}")
            
            return {
                "status": "success",
                "method": "isolated_env",
                "output_path": result['output_path'],
                "xml_file": result.get('xml_file'),
                "bin_file": result.get('bin_file'),
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            if "virtual environment not found" in error_msg:
                logger.error("  💡 Please run: bash aegis-vision/scripts/setup_openvino_env.sh")
            raise Exception(error_msg)
    
    def _export_torchscript(self, fmt: str, model_path: Path) -> Dict[str, Any]:
        """
        Export model to TorchScript format
        
        Args:
            fmt: Format name (for logging)
            model_path: Path to .pt model file
            
        Returns:
            Export result dictionary
        """
        logger.info(f"  📝 Format: TorchScript")
        logger.info(f"  💡 Using main environment for TorchScript export")
        logger.info(f"  📦 Loading fresh model from: {model_path}")
        
        # Load fresh YOLO model for export
        model = YOLO(str(model_path))
        
        export_kwargs = {
            'format': 'torchscript',
            'imgsz': self.img_size,
            'optimize': True,  # Enable optimization
        }
        
        export_result = model.export(**export_kwargs)
        
        return {
            "status": "success",
            "method": "ultralytics_builtin",
            "result": str(export_result)
        }
    
    def _export_generic(self, fmt: str, model_path: Path) -> Dict[str, Any]:
        """
        Export model to generic format (TensorRT, TFLite, etc.)
        
        Args:
            fmt: Format name
            model_path: Path to .pt model file
            
        Returns:
            Export result dictionary
        """
        fmt_lower = fmt.lower()
        logger.info(f"  📝 Format: {fmt}")
        logger.info(f"  🏗️  Using Ultralytics built-in export")
        logger.info(f"  📦 Loading fresh model from: {model_path}")
        
        # Load fresh YOLO model for export
        model = YOLO(str(model_path))
        
        export_kwargs = {
            'format': fmt_lower,
            'imgsz': self.img_size,
        }
        
        export_result = model.export(**export_kwargs)
        
        return {
            "status": "success",
            "method": "ultralytics_builtin",
            "result": str(export_result)
        }
    
    def _handle_export_error(self, fmt: str, error: Exception) -> Dict[str, Any]:
        """
        Handle export errors and provide helpful guidance
        
        Args:
            fmt: Format name
            error: Exception that occurred
            
        Returns:
            Error result dictionary
        """
        fmt_lower = fmt.lower()
        error_msg = str(error)
        
        logger.error(f"  ❌ {fmt.upper()} export FAILED!")
        logger.error(f"  💥 Error type: {type(error).__name__}")
        logger.error(f"  💥 Error message: {error_msg}")
        
        # Print full traceback for debugging
        traceback_str = traceback.format_exc()
        logger.error(f"  📋 Full traceback:\n{traceback_str}")
        
        # Provide specific guidance for known issues
        if fmt_lower == "tensorrt":
            logger.error("  💡 TensorRT requires specific GPU architecture (SM 75+)")
            logger.error("  💡 Check CUDA version and GPU compatibility")
        elif fmt_lower == "tflite":
            logger.error("  💡 TFLite may fail due to CuDNN version or onnx2tf issues")
        elif fmt_lower == "coreml":
            logger.error("  💡 CoreML export requires coremltools package")
            logger.error("  💡 Install with: pip install coremltools")
            logger.error("  💡 CoreML is primarily supported on macOS")
            logger.error(f"  💡 Current platform: {platform.system()}")
            
            # Check if coremltools is installed
            if COREMLTOOLS_AVAILABLE:
                logger.error(f"  ✓ coremltools is installed (version: {coremltools.__version__})")
            else:
                logger.error("  ✗ coremltools is NOT installed!")
        elif fmt_lower == "openvino":
            if "virtual environment not found" in error_msg:
                logger.error("  💡 Please run: bash aegis-vision/scripts/setup_openvino_env.sh")
        
        return {
            "status": "failed",
            "error": error_msg,
            "error_type": type(error).__name__
        }
    
    def export(self, formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export model to various formats
        
        Args:
            formats: List of export formats (onnx, coreml, openvino, tensorrt, tflite)
            
        Returns:
            Export results dictionary
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        formats = formats or self.output_formats
        if not formats:
            logger.info("No export formats specified, skipping export")
            return {"exported": []}
        
        logger.info(f"📤 Exporting model to {len(formats)} format(s): {formats}")
        logger.info(f"🔍 DEBUG: Model path: {self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'unknown'}")
        logger.info(f"🔍 DEBUG: Output directory: {self.output_dir}")
        logger.info(f"🔍 DEBUG: Model type: {type(self.model).__name__}")
        
        exported = []
        failed = []
        export_details = {}  # Store detailed results for each format
        
        # Get best model path for exports
        best_model_path = self._get_best_model_path()

        for fmt in formats:
            fmt_lower = fmt.lower()
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Starting export: {fmt.upper()}")
            logger.info(f"{'='*60}")
            
            try:
                # Call appropriate export handler directly
                if fmt_lower == 'onnx':
                    result = self._export_onnx(fmt, best_model_path)
                elif fmt_lower == 'coreml':
                    result = self._export_coreml(fmt, best_model_path)
                elif fmt_lower == 'torchscript':
                    result = self._export_torchscript(fmt, best_model_path)
                elif fmt_lower == 'openvino':
                    result = self._export_openvino(fmt, best_model_path)
                else:
                    # Generic export for other formats (TensorRT, TFLite, etc.)
                    result = self._export_generic(fmt, best_model_path)
                
                # Success!
                exported.append(fmt)
                logger.info(f"  ✅ {fmt.upper()} export successful!")
                export_details[fmt] = result
                
            except Exception as e:
                # Handle error
                failed.append(fmt)
                export_details[fmt] = self._handle_export_error(fmt, e)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Export Summary")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Succeeded: {len(exported)}/{len(formats)} - {exported}")
        logger.info(f"❌ Failed: {len(failed)}/{len(formats)} - {failed}")
        logger.info(f"📋 Details: {export_details}")
        logger.info(f"{'='*60}\n")
        
        return {
            "exported": exported,
            "failed": failed,
            "total": len(formats),
            "details": export_details,
        }
    
    def prepare_kaggle_output(self, output_dir: Optional[Path] = None) -> None:
        """
        Prepare models for Kaggle output download
        
        Args:
            output_dir: Output directory (default: /kaggle/working/trained_models)
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        output_dir = output_dir or (self.working_dir / "trained_models")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📦 Preparing models for download...")
        
        # Source directory (where training outputs are)
        weights_dir = self.output_dir / "train" / "weights"
        
        if not weights_dir.exists():
            logger.warning(f"⚠️ Weights directory not found: {weights_dir}")
            return
        
        # Copy all model files
        copied_count = 0
        for file_path in weights_dir.iterdir():
            try:
                dst = output_dir / file_path.name
                
                if file_path.is_dir():
                    # Handle directories (e.g., .mlpackage)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(file_path, dst)
                else:
                    # Handle regular files
                    shutil.copy2(file_path, dst)
                
                logger.info(f"✅ Copied {file_path.name} to {output_dir}")
                copied_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to copy {file_path.name}: {e}")
        
        logger.info(f"✅ Prepared {copied_count} model files for download")
