"""
Aegis AI Training Agent

Core agent functionality for distributed training:
- Firestore-based task queue monitoring
- Environment validation and dependency checking
- Dataset download and preparation
- Training execution with progress reporting
- Model upload and task completion
"""

# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
import os
from .headless_utils import setup_headless_environment
setup_headless_environment()
import sys
import time
import json
import psutil
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timezone
import logging

# Aegis Vision imports
from .trainer import YOLOTrainer
from .agent_auth import AgentAuthenticator, AgentAuthenticationError

logger = logging.getLogger(__name__)


class AgentCapabilities:
    """System capabilities detection"""
    
    @staticmethod
    def _detect_nvidia_gpu_via_smi() -> Dict[str, Any]:
        """Fallback GPU detection using nvidia-smi when PyTorch detection fails"""
        gpu_info = {
            "detected": False,
            "gpus": [],
            "driver_version": None,
            "cuda_version": None
        }
        
        try:
            # Try to get NVIDIA GPU information
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,memory.total,driver_version,compute_capability', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpu_info["detected"] = True
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 3:
                            try:
                                gpu_info["gpus"].append({
                                    "index": int(parts[0]),
                                    "name": parts[1],
                                    "memory": round(int(parts[2]) / 1024, 2),  # Convert MB to GB
                                    "compute_capability": parts[4] if len(parts) > 4 else "Unknown"
                                })
                            except (ValueError, IndexError):
                                pass
                
                # Get driver version
                if len(lines) > 0:
                    parts = lines[0].split(',')
                    if len(parts) >= 4:
                        gpu_info["driver_version"] = parts[3].strip()
            
            # Try to get CUDA version
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=compute_capability', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Alternative: check CUDA version from nvcc
            try:
                nvcc_result = subprocess.run(
                    ['nvcc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if nvcc_result.returncode == 0:
                    # Extract version from nvcc output
                    import re
                    match = re.search(r'release\s+([\d.]+)', nvcc_result.stdout)
                    if match:
                        gpu_info["cuda_version"] = match.group(1)
            except FileNotFoundError:
                pass
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            logger.debug(f"nvidia-smi detection failed: {e}")
        
        return gpu_info
    
    @staticmethod
    def _get_torch_cuda_info() -> Dict[str, Any]:
        """Get GPU information from PyTorch"""
        cuda_info = {
            "available": False,
            "version": None,
            "runtime_version": None,
            "device_count": 0,
            "devices": []
        }
        
        try:
            import torch
            
            if torch.cuda.is_available():
                cuda_info["available"] = True
                cuda_info["version"] = torch.version.cuda
                
                # Try to get runtime version
                try:
                    cuda_info["runtime_version"] = torch.version.cuda
                except:
                    pass
                
                cuda_info["device_count"] = torch.cuda.device_count()
                
                for i in range(torch.cuda.device_count()):
                    try:
                        props = torch.cuda.get_device_properties(i)
                        cuda_info["devices"].append({
                            "index": i,
                            "name": torch.cuda.get_device_name(i),
                            "memory": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2),
                            "compute_capability": f"{props.major}.{props.minor}",
                            "multi_processor_count": props.multi_processor_count
                        })
                    except Exception as e:
                        logger.debug(f"Failed to get device {i} properties: {e}")
                        
        except Exception as e:
            logger.debug(f"PyTorch CUDA detection failed: {e}")
        
        return cuda_info
    
    @staticmethod
    def detect() -> Dict[str, Any]:
        """
        Detect system capabilities using platform-specific GPU detectors.
        
        Detection strategy:
        - Linux/Windows: PyTorch CUDA → nvidia-smi → /proc filesystem
        - macOS: PyTorch MPS → CPU fallback
        """
        capabilities = {
            "platform": platform.system(),
            "pythonVersion": platform.python_version(),
            "totalMemoryGB": round(psutil.virtual_memory().total / (1024**3), 2),
            "availableMemoryGB": round(psutil.virtual_memory().available / (1024**3), 2),
            "totalStorageGB": round(psutil.disk_usage('/').total / (1024**3), 2),
            "availableStorageGB": round(psutil.disk_usage('/').free / (1024**3), 2),
            "cpuCount": psutil.cpu_count(),
            "hasGPU": False,
            "hasMPS": False,
            "cudaVersion": None,
            "cudaRuntimeVersion": None,
            "gpuInfo": [],
            "gpuDetectionMethod": None,
            "environment": AgentCapabilities._detect_environment(),
            "trainingFolder": str(Path.home() / ".aegis-vision" / "agent-work")
        }
        
        # Suppress PyTorch warnings
        try:
            import warnings
            warnings.filterwarnings('ignore', category=UserWarning, message='.*CUDA capability.*')
            warnings.filterwarnings('ignore', category=UserWarning, message='.*NumPy.*')
        except Exception:
            pass
        
        # Platform-specific detection
        system = platform.system()
        
        if system == "Darwin":
            # macOS: MPS or CPU
            AgentCapabilities._detect_macos_gpu(capabilities)
        elif system in ["Linux", "Windows"]:
            # Linux/Windows: CUDA (PyTorch → nvidia-smi → /proc)
            AgentCapabilities._detect_nvidia_gpu(capabilities)
        
        return capabilities
    
    @staticmethod
    def _detect_nvidia_gpu(capabilities: Dict[str, Any]) -> None:
        """
        Detect NVIDIA GPUs on Linux/Windows.
        
        Uses multi-method detection:
        1. PyTorch CUDA API
        2. nvidia-smi command
        3. /proc filesystem (Linux only)
        """
        try:
            # Try PyTorch first
            import torch
            
            if torch.cuda.is_available():
                capabilities["hasGPU"] = True
                capabilities["cudaVersion"] = torch.version.cuda
                capabilities["gpuDetectionMethod"] = "PyTorch"
                
                for i in range(torch.cuda.device_count()):
                    try:
                        props = torch.cuda.get_device_properties(i)
                        capabilities["gpuInfo"].append({
                            "name": torch.cuda.get_device_name(i),
                            "memory": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2),
                            "computeCapability": f"{props.major}.{props.minor}",
                            "index": i
                        })
                    except Exception as e:
                        logger.debug(f"Failed to get device {i} properties: {e}")
                        
                logger.debug(f"Detected {len(capabilities['gpuInfo'])} GPU(s) via PyTorch")
                return
                
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"PyTorch CUDA detection failed: {e}")
        
        # Fallback to nvidia-smi
        try:
            smi_result = AgentCapabilities._detect_nvidia_gpu_via_smi()
            
            if smi_result["detected"] and smi_result["gpus"]:
                capabilities["hasGPU"] = True
                capabilities["gpuDetectionMethod"] = "nvidia-smi"
                capabilities["cudaVersion"] = smi_result["cuda_version"]
                
                if smi_result["driver_version"]:
                    capabilities["nvidiaDriverVersion"] = smi_result["driver_version"]
                
                for gpu in smi_result["gpus"]:
                    capabilities["gpuInfo"].append({
                        "name": gpu["name"],
                        "memory": gpu["memory"],
                        "computeCapability": gpu["compute_capability"],
                        "index": gpu["index"]
                    })
                
                logger.debug(f"Detected {len(capabilities['gpuInfo'])} GPU(s) via nvidia-smi")
                return
                
        except Exception as e:
            logger.debug(f"nvidia-smi detection failed: {e}")
        
        # Fallback to /proc filesystem (Linux only)
        if platform.system() == "Linux":
            try:
                proc_result = AgentCapabilities._detect_nvidia_gpu_via_proc()
                
                if proc_result["detected"] and proc_result["gpus"]:
                    capabilities["hasGPU"] = True
                    capabilities["gpuDetectionMethod"] = "/proc filesystem"
                    
                    if proc_result["driver_version"]:
                        capabilities["nvidiaDriverVersion"] = proc_result["driver_version"]
                    if proc_result["cuda_version"]:
                        capabilities["cudaVersion"] = proc_result["cuda_version"]
                    
                    for gpu in proc_result["gpus"]:
                        capabilities["gpuInfo"].append({
                            "name": gpu["name"],
                            "memory": gpu["memory"],
                            "computeCapability": gpu["compute_capability"],
                            "index": gpu["index"]
                        })
                    
                    logger.debug(f"Detected {len(capabilities['gpuInfo'])} GPU(s) via /proc")
                    
            except Exception as e:
                logger.debug(f"/proc GPU detection failed: {e}")
    
    @staticmethod
    def _detect_macos_gpu(capabilities: Dict[str, Any]) -> None:
        """
        Detect GPU acceleration on macOS.
        
        Note: macOS does NOT support CUDA. Use MPS (Metal Performance Shaders)
        on Apple Silicon Macs instead.
        """
        try:
            import torch
            
            # Check for MPS support
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                capabilities["hasGPU"] = True
                capabilities["hasMPS"] = True
                capabilities["gpuDetectionMethod"] = "PyTorch MPS"
                capabilities["gpuInfo"] = [{
                    "name": "Apple Silicon (Metal Performance Shaders)",
                    "memory": 0,  # Shared memory, not separately reported
                    "computeCapability": "N/A",
                    "index": 0
                }]
                logger.debug("MPS acceleration available on Apple Silicon")
                return
                
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"MPS detection failed: {e}")
        
        # Check for Apple Silicon (even without PyTorch)
        try:
            machine = platform.machine().lower()
            if 'arm' in machine or 'aarch64' in machine:
                capabilities["hasMPS"] = True
                capabilities["gpuDetectionMethod"] = "System Architecture"
                logger.debug("Apple Silicon detected (MPS may be available with PyTorch 1.12+)")
                
        except Exception:
            pass
    
    @staticmethod
    def _detect_nvidia_gpu_via_proc() -> Dict[str, Any]:
        """
        Detect NVIDIA GPUs using /proc filesystem (Linux only).
        
        Used when nvidia-smi is not available (e.g., containers, minimal environments).
        """
        result = {
            "detected": False,
            "gpus": [],
            "driver_version": None,
            "cuda_version": None
        }
        
        try:
            from pathlib import Path
            import re
            
            # Check if NVIDIA driver is loaded
            proc_path = Path("/proc/driver/nvidia/version")
            if not proc_path.exists():
                return result
            
            # Read driver version
            with open(proc_path, 'r') as f:
                version_str = f.read()
                match = re.search(r'NVRM version: (\S+)', version_str)
                if match:
                    result["driver_version"] = match.group(1)
            
            # Check for GPU devices
            gpus_path = Path("/proc/driver/nvidia/gpus")
            if gpus_path.exists():
                result["detected"] = True
                
                for gpu_dir in sorted(gpus_path.iterdir()):
                    if gpu_dir.is_dir():
                        try:
                            gpu_index = int(gpu_dir.name)
                            result["gpus"].append({
                                "index": gpu_index,
                                "name": "NVIDIA GPU",
                                "memory": 0,
                                "compute_capability": "Unknown"
                            })
                        except (ValueError, IOError):
                            pass
            
            # Try to get CUDA version from nvcc
            try:
                nvcc_result = subprocess.run(
                    ['nvcc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if nvcc_result.returncode == 0:
                    match = re.search(r'release\s+([\d.]+)', nvcc_result.stdout)
                    if match:
                        result["cuda_version"] = match.group(1)
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"/proc GPU detection failed: {e}")
        
        return result
    
    @staticmethod
    def _detect_environment() -> Dict[str, Any]:
        """Detect Python environment type (conda, venv, or system)"""
        env_info = {
            "type": "system",  # default
            "name": None,
            "path": sys.prefix,
            "condaAvailable": False,
            "venvAvailable": True  # venv is built-in to Python 3.3+
        }
        
        # Check if in conda environment
        if os.environ.get('CONDA_DEFAULT_ENV'):
            env_info["type"] = "conda"
            env_info["name"] = os.environ.get('CONDA_DEFAULT_ENV')
            env_info["condaAvailable"] = True
        # Check if in venv
        elif hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            env_info["type"] = "venv"
            env_info["name"] = Path(sys.prefix).name
        
        # Check if conda is available (even if not currently in conda env)
        try:
            result = subprocess.run(['conda', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                env_info["condaAvailable"] = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return env_info


class PackageManager:
    """Manage package installation and environment setup"""
    
    @staticmethod
    def check_package_installed(package_name: str) -> Dict[str, Any]:
        """Check if a package is installed and get its version"""
        result = {
            "installed": False,
            "version": None,
            "error": None
        }
        
        try:
            if package_name == "torch" or package_name == "pytorch":
                import torch
                result["installed"] = True
                result["version"] = torch.__version__
            elif package_name == "ultralytics":
                import ultralytics
                result["installed"] = True
                result["version"] = ultralytics.__version__
            else:
                # Generic package check
                import importlib
                mod = importlib.import_module(package_name)
                result["installed"] = True
                result["version"] = getattr(mod, '__version__', 'unknown')
        except ImportError as e:
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def install_package(package_name: str, env_type: str = "current", env_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Install a package in the specified environment.
        
        Args:
            package_name: Package to install (e.g., 'torch', 'ultralytics')
            env_type: 'current', 'conda', or 'venv'
            env_name: Name of conda env or path to venv
            
        Returns:
            Dict with success status, output, and error
        """
        result = {
            "success": False,
            "output": "",
            "error": None
        }
        
        try:
            if env_type == "conda" and env_name:
                # Install in conda environment
                cmd = ["conda", "run", "-n", env_name, "pip", "install", package_name]
            elif env_type == "venv" and env_name:
                # Install in venv
                pip_path = Path(env_name) / "bin" / "pip"
                if not pip_path.exists():
                    pip_path = Path(env_name) / "Scripts" / "pip.exe"  # Windows
                cmd = [str(pip_path), "install", package_name]
            else:
                # Install in current environment
                cmd = [sys.executable, "-m", "pip", "install", package_name]
            
            logger.info(f"Installing {package_name} with command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            result["output"] = process.stdout
            result["success"] = process.returncode == 0
            
            if not result["success"]:
                result["error"] = process.stderr
                logger.error(f"Failed to install {package_name}: {process.stderr}")
            else:
                logger.info(f"Successfully installed {package_name}")
                
        except subprocess.TimeoutExpired:
            result["error"] = "Installation timeout (5 minutes exceeded)"
            logger.error(f"Installation timeout for {package_name}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Installation error for {package_name}: {e}")
        
        return result
    
    @staticmethod
    def create_conda_env(env_name: str, python_version: str = "3.10") -> Dict[str, Any]:
        """Create a new conda environment"""
        result = {
            "success": False,
            "output": "",
            "error": None
        }
        
        try:
            cmd = ["conda", "create", "-n", env_name, f"python={python_version}", "-y"]
            logger.info(f"Creating conda environment: {env_name}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            result["output"] = process.stdout
            result["success"] = process.returncode == 0
            
            if not result["success"]:
                result["error"] = process.stderr
                logger.error(f"Failed to create conda env: {process.stderr}")
            else:
                logger.info(f"Successfully created conda environment: {env_name}")
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error creating conda env: {e}")
        
        return result
    
    @staticmethod
    def create_venv(venv_path: str, python_executable: str = sys.executable) -> Dict[str, Any]:
        """Create a new virtual environment"""
        result = {
            "success": False,
            "output": "",
            "error": None
        }
        
        try:
            cmd = [python_executable, "-m", "venv", venv_path]
            logger.info(f"Creating venv at: {venv_path}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            result["output"] = process.stdout
            result["success"] = process.returncode == 0
            
            if not result["success"]:
                result["error"] = process.stderr
                logger.error(f"Failed to create venv: {process.stderr}")
            else:
                logger.info(f"Successfully created venv at: {venv_path}")
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error creating venv: {e}")
        
        return result


class PlatformResolver:
    """Intelligent platform detection and PyTorch setup"""
    
    @staticmethod
    def detect_hardware() -> Dict[str, Any]:
        """Detect available hardware acceleration"""
        import torch
        
        hardware_info = {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "has_cuda": False,
            "has_mps": False,
            "has_metal": False,
            "cuda_version": None,
            "recommended_torch_index": None,
            "recommended_install_cmd": None
        }
        
        # Check CUDA
        if torch.cuda.is_available():
            hardware_info["has_cuda"] = True
            hardware_info["cuda_version"] = torch.version.cuda
            hardware_info["recommended_torch_index"] = "cu118"  # Default to CUDA 11.8
        # Check MPS (Apple Silicon)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hardware_info["has_mps"] = True
            hardware_info["recommended_torch_index"] = "cpu"  # MPS works with CPU-built PyTorch
        # Check METAL (older macOS)
        elif platform.system() == "Darwin":
            hardware_info["has_metal"] = True
            hardware_info["recommended_torch_index"] = "cpu"
        else:
            hardware_info["recommended_torch_index"] = "cpu"
        
        return hardware_info
    
    @staticmethod
    def resolve_pytorch_install(env_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Intelligently resolve PyTorch installation for the current platform.
        
        Returns dict with success status, device type, and installation info
        """
        logger.info("🔍 Resolving PyTorch for platform...")
        
        system = platform.system()
        machine = platform.machine().lower()
        
        result = {
            "success": False,
            "device": None,
            "pytorch_installed": False,
            "package_spec": None,
            "install_cmd": None,
            "reason": None
        }
        
        # Check if PyTorch is already installed
        pkg_check = PackageManager.check_package_installed("torch")
        if pkg_check["installed"]:
            logger.info(f"✅ PyTorch already installed: {pkg_check['version']}")
            result["pytorch_installed"] = True
            
            # Detect which device is available
            try:
                import torch
                if torch.cuda.is_available():
                    result["device"] = "cuda"
                    result["reason"] = "CUDA available"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    result["device"] = "mps"
                    result["reason"] = "Apple MPS available"
                else:
                    result["device"] = "cpu"
                    result["reason"] = "Using CPU fallback"
                result["success"] = True
                return result
            except Exception as e:
                logger.warning(f"Failed to detect device: {e}")
                result["device"] = "cpu"
                result["success"] = True
                return result
        
        # PyTorch not installed - determine best variant for platform
        logger.info(f"📦 PyTorch not installed. Platform: {system} ({machine})")
        
        if system == "Darwin":
            # macOS
            if 'arm' in machine or 'aarch64' in machine:
                # Apple Silicon - use CPU build with MPS support
                logger.info("🍎 Apple Silicon detected - installing PyTorch with MPS support")
                result["package_spec"] = "torch torchvision torchaudio"
                result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio"
                result["device"] = "mps"
                result["reason"] = "Installing CPU variant with MPS acceleration"
            else:
                # Intel macOS
                logger.info("🍎 Intel macOS detected")
                result["package_spec"] = "torch torchvision torchaudio"
                result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio"
                result["device"] = "cpu"
                result["reason"] = "Installing CPU variant"
        
        elif system == "Linux":
            # Check for NVIDIA GPU
            try:
                result_nvidia = subprocess.run(
                    ['nvidia-smi'], 
                    capture_output=True, 
                    timeout=5
                )
                if result_nvidia.returncode == 0:
                    logger.info("🖥️  NVIDIA GPU detected - installing PyTorch with CUDA")
                    result["package_spec"] = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                    result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                    result["device"] = "cuda"
                    result["reason"] = "NVIDIA GPU with CUDA 11.8"
                else:
                    raise FileNotFoundError
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.info("💻 No NVIDIA GPU detected - using CPU")
                result["package_spec"] = "torch torchvision torchaudio"
                result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio"
                result["device"] = "cpu"
                result["reason"] = "CPU only"
        
        elif system == "Windows":
            # Check for NVIDIA GPU
            try:
                result_nvidia = subprocess.run(
                    ['nvidia-smi'], 
                    capture_output=True, 
                    timeout=5
                )
                if result_nvidia.returncode == 0:
                    logger.info("🖥️  NVIDIA GPU detected - installing PyTorch with CUDA")
                    result["package_spec"] = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                    result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                    result["device"] = "cuda"
                    result["reason"] = "NVIDIA GPU with CUDA 11.8"
                else:
                    raise FileNotFoundError
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.info("💻 No NVIDIA GPU detected - using CPU")
                result["package_spec"] = "torch torchvision torchaudio"
                result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio"
                result["device"] = "cpu"
                result["reason"] = "CPU only"
        
        else:
            # Unknown platform - fallback to CPU
            logger.warning(f"⚠️  Unknown platform: {system} - using CPU")
            result["package_spec"] = "torch torchvision torchaudio"
            result["install_cmd"] = f"{sys.executable} -m pip install torch torchvision torchaudio"
            result["device"] = "cpu"
            result["reason"] = "Unknown platform - CPU fallback"
        
        result["success"] = bool(result["install_cmd"])
        return result
    
    @staticmethod
    def install_pytorch_for_platform() -> Dict[str, Any]:
        """Install PyTorch appropriate for this platform"""
        resolution = PlatformResolver.resolve_pytorch_install()
        
        if resolution["pytorch_installed"]:
            logger.info(f"✅ PyTorch ready: device={resolution['device']}")
            return {
                "success": True,
                "device": resolution["device"],
                "reason": resolution["reason"]
            }
        
        if not resolution["install_cmd"]:
            return {
                "success": False,
                "error": "Could not determine PyTorch installation command"
            }
        
        logger.info(f"📦 Installing PyTorch: {resolution['reason']}")
        logger.info(f"   Command: {resolution['install_cmd']}")
        
        try:
            result = subprocess.run(
                resolution["install_cmd"],
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minutes timeout
            )
            
            logger.info(f"✅ PyTorch installed successfully for device: {resolution['device']}")
            return {
                "success": True,
                "device": resolution["device"],
                "reason": resolution["reason"]
            }
        
        except subprocess.TimeoutExpired:
            logger.error("❌ PyTorch installation timed out (10 minutes)")
            return {
                "success": False,
                "error": "Installation timeout",
                "device": resolution["device"]
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ PyTorch installation failed: {e.stderr}")
            return {
                "success": False,
                "error": e.stderr or str(e),
                "device": resolution["device"]
            }
        except Exception as e:
            logger.error(f"❌ PyTorch installation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "device": resolution["device"]
            }


class TrainingAgent:
    """
    Training agent that executes remote training tasks.
    
    The agent:
    1. Authenticates with Firebase using API key
    2. Registers itself in Firestore /agents/{agentId}
    3. Listens for tasks in /training_tasks collection
    4. Claims and executes tasks
    5. Reports progress and results back to Firestore
    """
    
    def __init__(
        self,
        authenticator: Optional[AgentAuthenticator] = None,
        work_dir: Optional[Path] = None
    ):
        """
        Initialize training agent.
        
        Args:
            authenticator: AgentAuthenticator instance (creates default if None)
            work_dir: Working directory for downloads and training
        """
        self.authenticator = authenticator or AgentAuthenticator()
        self.work_dir = work_dir or Path.home() / ".aegis-vision" / "agent-work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        self.agent_id = self.authenticator.get_agent_id()
        self.firestore_project = self.authenticator.get_firestore_project()
        
        # Firebase Admin SDK for all Firestore operations
        # Uses on_snapshot() for real-time listeners (cost-efficient, <1s latency)
        self.app: Optional[Any] = None
        self.db: Optional[Any] = None  # Admin SDK Firestore client
        
        # Agent state
        self.capabilities = AgentCapabilities.detect()
        self.running = False
        self.current_task: Optional[str] = None
        self.task_listener = None
        self.command_listener = None
        self.package_manager = PackageManager()
        self.detected_device = None # Initialize detected_device
        self.seen_task_ids: set = set()  # Track tasks already processed to prevent duplicates
        
        # Token management for Firestore Client
        self.id_token = None
        self.refresh_token = None
        self.token_expiry = 0
        
        logger.info(f"Agent initialized: {self.agent_id}")
        logger.info(f"Work directory: {self.work_dir}")
    
    def initialize_firebase(self) -> None:
        """Initialize Firestore using Firebase config from Cloud Function
        
        The authentication flow:
        1. Agent API key (permanent) → stored in agent-config.json
        2. Cloud Function validates API key → returns Firebase Web API key
        3. Custom token (1-hour expiry) → from AgentAuthenticator
        4. ID token (1-hour expiry) → exchanged using Firebase Web API key
        5. OAuth2 credentials → for Firestore access
        
        Benefits:
        - No manual Firebase API key configuration needed
        - Centralized key management in private backend repo
        - Easy key rotation without redeploying agents
        - Audit trail of which agents accessed configuration
        """
        try:
            from google.cloud import firestore
            from google.oauth2 import credentials as oauth_credentials
            import requests
            import time
            
            # Step 1: Get Firebase configuration from Cloud Function
            logger.info("Fetching Firebase configuration from Cloud Function...")
            firebase_config = self._get_firebase_config_from_cloud()
            
            if not firebase_config:
                raise Exception("Failed to fetch Firebase configuration from Cloud Function")
            
            firebase_api_key = firebase_config['firebaseConfig']['apiKey']
            logger.info("✅ Firebase Web API key retrieved from Cloud Function")
            
            # Step 2: Get custom token from authenticator
            logger.info("Authenticating with agent API key...")
            custom_token = self.authenticator.authenticate()
            
            # Step 3: Exchange custom token for ID token + refresh token
            logger.info("Exchanging custom token for OAuth2 credentials...")
            
            url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
            response = requests.post(url, json={
                'token': custom_token,
                'returnSecureToken': True
            }, params={'key': firebase_api_key}, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            data = response.json()
            self.id_token = data['idToken']
            self.refresh_token = data.get('refreshToken')  # Save for auto-refresh
            
            # ID tokens expire after 1 hour
            expires_in = int(data.get('expiresIn', 3600))
            self.token_expiry = time.time() + expires_in
            
            # Step 4: Create OAuth2 credentials from ID token
            creds = oauth_credentials.Credentials(token=self.id_token)
            
            # Step 5: Create Firestore client with custom credentials
            self.db = firestore.Client(
                project=self.firestore_project,
                credentials=creds
            )
            
            logger.info("✅ Firestore initialized successfully")
            logger.info("   Package: google-cloud-firestore")
            logger.info("   Authentication: Agent API key → Cloud Function → Firebase API key → Custom token → ID token")
            logger.info("   Token Refresh: Automatic using refresh token")
            logger.info("   Features: Real-time listeners (on_snapshot)")
            logger.info("   Security: Centralized API key management")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise AgentAuthenticationError(f"Firestore initialization failed: {e}")
    
    def _get_firebase_config_from_cloud(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Firebase configuration from Cloud Function with local caching.
        
        Caching strategy:
        - Cache config locally on first fetch
        - Reuse cache for all subsequent calls (no expiration)
        - Only refetch if authentication fails (lazy validation)
        - Manual cache clear via CLI if needed
        
        Returns:
            Firebase configuration dict or None if failed
        """
        # Try cache first
        cached_config = self._load_firebase_config_cache()
        if cached_config:
            return cached_config
        
        # Cache miss - fetch from Cloud Function
        try:
            import requests
            
            # Get agent API key from authenticator config
            api_key = self.authenticator.config.get('apiKey')
            if not api_key:
                raise ValueError("Agent API key not found in config")
            
            # Cloud Function endpoint
            base_url = os.environ.get(
                'AEGIS_CLOUD_FUNCTION_URL',
                'https://us-central1-aegis-vision-464501.cloudfunctions.net/aegis-vision-admin-api'
            )
            url = f"{base_url}/agent/firebase-config"
            
            # Make request with agent API key
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Requesting Firebase config from: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.error(f"Cloud Function returned {response.status_code}: {error_detail}")
                raise Exception(f"Cloud Function returned {response.status_code}")
            
            config = response.json()
            logger.info("✅ Firebase configuration received from Cloud Function")
            logger.info(f"   Agent ID: {config.get('agentInfo', {}).get('agentId', 'unknown')}")
            
            # Save to cache for future use
            self._save_firebase_config_cache(config)
            
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Firebase config from Cloud Function: {e}")
            raise
    
    def _get_cache_path(self) -> Path:
        """Get path to Firebase config cache file"""
        cache_dir = Path.home() / '.aegis-vision' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / 'firebase_config.json'
    
    def _load_firebase_config_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load Firebase config from local cache.
        
        Returns:
            Cached config dict or None if cache doesn't exist/invalid
        """
        try:
            cache_path = self._get_cache_path()
            if not cache_path.exists():
                logger.debug("No Firebase config cache found")
                return None
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Validate cache structure
            if 'firebaseConfig' not in cache_data or 'apiKey' not in cache_data['firebaseConfig']:
                logger.warning("Invalid cache structure, ignoring")
                return None
            
            logger.info("✅ Loaded Firebase config from cache")
            cached_at = cache_data.get('cached_at', 'unknown')
            logger.info(f"   Cached at: {cached_at}")
            logger.debug(f"   Cache path: {cache_path}")
            
            return cache_data
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
    
    def _save_firebase_config_cache(self, config: Dict[str, Any]) -> None:
        """
        Save Firebase config to local cache.
        
        Args:
            config: Firebase configuration dict from Cloud Function
        """
        try:
            cache_data = {
                **config,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'fetched_from': 'cloud-function',
                'version': '1.0'
            }
            
            cache_path = self._get_cache_path()
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"💾 Cached Firebase config to: {cache_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e} (not critical)")
    
    def _clear_firebase_config_cache(self) -> bool:
        """
        Clear cached Firebase configuration.
        Used when cache is detected as invalid (e.g., auth failures).
        
        Returns:
            True if cache was cleared, False if no cache existed
        """
        try:
            cache_path = self._get_cache_path()
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"🗑️  Cleared Firebase config cache: {cache_path}")
                return True
            else:
                logger.debug("No cache to clear")
                return False
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
            return False
    
    def register_agent(self) -> None:
        """Register agent in Firestore with startup validation"""
        try:
            # Validate training scripts before registering
            scripts_valid = self._validate_training_scripts()
            
            # Detect platform and hardware info
            hardware_info = PlatformResolver.detect_hardware()
            
            # Check if agent document already exists
            agent_ref = self.db.collection("agents").document(self.agent_id)
            existing_doc = agent_ref.get()
            
            if existing_doc.exists:
                # Agent re-registering (restart) - only update dynamic fields
                logger.info(f"Agent {self.agent_id} already registered, updating status...")
                agent_doc = {
                    "status": "online",
                    "lastSeen": "SERVER_TIMESTAMP",
                    "capabilities": self.capabilities,
                    "hardwareInfo": hardware_info,
                    "currentTask": None,
                    "heartbeat": "SERVER_TIMESTAMP",
                    "scriptsValid": scripts_valid,
                    "lastValidationAt": "SERVER_TIMESTAMP"
                }
            else:
                # First-time registration - include all fields
                logger.info(f"Registering new agent: {self.agent_id}")
                agent_doc = {
                    "agentId": self.agent_id,
                    "agentName": self.authenticator.config.get("agentName", f"Agent {self.agent_id[:8]}"),
                    "ownerUid": self.authenticator.config.get("ownerUid", ""),
                    "status": "online",
                    "lastSeen": "SERVER_TIMESTAMP",
                    "capabilities": self.capabilities,
                    "hardwareInfo": hardware_info,
                    "currentTask": None,
                    "heartbeat": "SERVER_TIMESTAMP",
                    "registeredAt": "SERVER_TIMESTAMP",  # Only set on first registration
                    "scriptsValid": scripts_valid,
                    "lastValidationAt": "SERVER_TIMESTAMP"
                }
            
            agent_ref.set(agent_doc, merge=True)
            
            logger.info(f"Agent registered successfully: {self.agent_id}")
            logger.info(f"  Hardware: {hardware_info.get('platform')} ({hardware_info.get('architecture')})")
            if hardware_info.get('has_cuda'):
                logger.info(f"  CUDA: {hardware_info.get('cuda_version')}")
            if hardware_info.get('has_mps'):
                logger.info("  MPS: Available (Apple Silicon)")
            
            if scripts_valid:
                logger.info("✅ Training scripts validated successfully")
            else:
                logger.warning("⚠️  Training scripts validation failed - agent will not accept tasks")
            
            # Clean up orphaned tasks from previous run
            self._recover_orphaned_tasks()
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise
    
    def _validate_training_scripts(self) -> bool:
        """
        Validate that training scripts exist and are executable
        
        Returns:
            True if scripts are valid, False otherwise
        """
        try:
            from pathlib import Path
            
            # Check for training_script.py
            script_path = Path(__file__).parent / "training_script.py"
            
            if not script_path.exists():
                logger.error(f"❌ Training script not found: {script_path}")
                return False
            
            # Check if file is readable
            if not script_path.is_file():
                logger.error(f"❌ Training script is not a file: {script_path}")
                return False
            
            # Try to read the script to ensure it's valid
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                    
                # Basic validation - check for main function
                if 'def main()' not in content:
                    logger.error("❌ Training script missing main() function")
                    return False
                    
                # Check for required imports
                required_imports = ['aegis_vision', 'YOLOTrainer']
                for imp in required_imports:
                    if imp not in content:
                        logger.warning(f"⚠️  Training script missing import: {imp}")
                
                logger.info(f"✅ Training script validated: {script_path}")
                logger.info(f"   Size: {len(content)} bytes")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to read training script: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Training script validation failed: {e}")
            return False
    
    def _recover_orphaned_tasks(self) -> None:
        """
        Recover tasks that were interrupted when agent crashed or stopped.
        Mark them as failed so they don't show as active.
        """
        try:
            logger.info("🔍 Checking for orphaned tasks from previous run...")
            
            # Find tasks assigned to this agent that are not in terminal state
            # NOTE: REST API client uses simplified query syntax without FieldFilter
            
            # Check for tasks in 'assigned' or 'running' state assigned to this agent
            active_statuses = ['assigned', 'running']
            
            for status in active_statuses:
                tasks_ref = self.db.collection("training_tasks").where(
                    "assignedTo", "==", self.agent_id
                ).where(
                    "status", "==", status
                )
                
                orphaned_tasks = list(tasks_ref.stream())
                
                if orphaned_tasks:
                    logger.warning(f"⚠️  Found {len(orphaned_tasks)} orphaned task(s) in '{status}' state")
                    
                    for task_doc in orphaned_tasks:
                        task_id = task_doc.id
                        task_data = task_doc.to_dict()
                        
                        logger.warning(f"⚠️  Recovering orphaned task: {task_id}")
                        logger.info(f"   Original status: {status}")
                        logger.info(f"   Created at: {task_data.get('createdAt', 'unknown')}")
                        
                        # Mark as failed with recovery message
                        try:
                            self.db.collection("training_tasks").document(task_id).update({
                                "status": "failed",
                                "error": "Agent interrupted - task was orphaned during agent restart",
                                "failedAt": "SERVER_TIMESTAMP",
                                "recoveredBy": self.agent_id,
                                "originalStatus": status,
                                "recoveryReason": "agent_restart"
                            })
                            
                            # Add log entry
                            self._append_log(
                                task_id, 
                                "warning", 
                                f"⚠️  Task recovered after agent restart - marked as failed. Original status: {status}"
                            )
                            
                            logger.info(f"✅ Task {task_id} marked as failed (orphaned recovery)")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to recover task {task_id}: {e}")
            
            # Also check local persistent state file if it exists
            self._clean_local_task_state()
            
            logger.info("✅ Orphaned task recovery complete")
            
        except Exception as e:
            logger.error(f"❌ Orphaned task recovery failed: {e}")
            # Don't raise - this is not critical for agent startup
    
    def _clean_local_task_state(self) -> None:
        """
        Clean up local persistent task state file.
        Remove any tasks that are in active state since agent just started.
        """
        try:
            state_file = self.work_dir / "task_state.json"
            
            if not state_file.exists():
                logger.info("ℹ️  No local task state file found - clean start")
                return
            
            logger.info(f"🔍 Checking local task state: {state_file}")
            
            import json
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            active_tasks = state_data.get('active_tasks', [])
            
            if active_tasks:
                logger.warning(f"⚠️  Found {len(active_tasks)} task(s) in local state")
                
                # Clear active tasks since agent just started
                state_data['active_tasks'] = []
                state_data['last_cleanup'] = datetime.now().isoformat()
                state_data['cleanup_reason'] = 'agent_restart'
                
                # Archive old active tasks
                if 'archived_tasks' not in state_data:
                    state_data['archived_tasks'] = []
                
                for task_id in active_tasks:
                    state_data['archived_tasks'].append({
                        'task_id': task_id,
                        'archived_at': datetime.now().isoformat(),
                        'reason': 'agent_restart'
                    })
                    logger.info(f"   Archived task from local state: {task_id}")
                
                # Write updated state
                with open(state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                
                logger.info("✅ Local task state cleaned up")
            else:
                logger.info("✅ Local task state is clean - no active tasks")
                
        except Exception as e:
            logger.warning(f"⚠️  Failed to clean local task state: {e}")
            # Don't raise - this is not critical
    
    def update_heartbeat(self) -> None:
        """Update agent heartbeat and refresh token if needed"""
        try:
            # Check if token needs refresh (5 minutes before expiry)
            import time
            if time.time() >= (self.token_expiry - 300):  # 5 minutes before expiry
                self._refresh_firebase_token()
            
            heartbeat_data = {
                "heartbeat": "SERVER_TIMESTAMP",
                "lastSeen": "SERVER_TIMESTAMP",
                "status": "training" if self.current_task else "online"
            }
            
            # Include detected device if available
            if self.detected_device:
                heartbeat_data["currentDevice"] = self.detected_device
            
            self.db.collection("agents").document(self.agent_id).update(heartbeat_data)
        except Exception as e:
            logger.warning(f"Failed to update heartbeat: {e}")
    
    def _refresh_firebase_token(self) -> None:
        """Refresh Firebase ID token using refresh token
        
        This is called automatically before the token expires.
        Gets Firebase API key from Cloud Function for security.
        """
        try:
            import requests
            import time
            from google.oauth2 import credentials as oauth_credentials
            
            logger.info("🔄 Refreshing Firebase token...")
            
            # Get Firebase API key from Cloud Function
            firebase_config = self._get_firebase_config_from_cloud()
            if not firebase_config:
                raise Exception("Failed to fetch Firebase configuration for token refresh")
            
            firebase_api_key = firebase_config['firebaseConfig']['apiKey']
            
            if self.refresh_token:
                # Try to refresh using refresh token first
                url = "https://securetoken.googleapis.com/v1/token"
                response = requests.post(url, json={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token
                }, params={'key': firebase_api_key}, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    self.id_token = data['id_token']
                    self.refresh_token = data['refresh_token']
                    
                    expires_in = int(data.get('expires_in', 3600))
                    self.token_expiry = time.time() + expires_in
                    
                    # Update Firestore client credentials
                    from google.cloud import firestore
                    creds = oauth_credentials.Credentials(token=self.id_token)
                    self.db = firestore.Client(
                        project=self.firestore_project,
                        credentials=creds
                    )
                    
                    logger.info("✅ Token refreshed successfully")
                    return
            
            # Fallback: Re-exchange custom token
            logger.info("Using fallback: re-exchanging custom token...")
            custom_token = self.authenticator.authenticate()
            
            url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
            response = requests.post(url, json={
                'token': custom_token,
                'returnSecureToken': True
            }, params={'key': firebase_api_key}, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            data = response.json()
            self.id_token = data['idToken']
            self.refresh_token = data.get('refreshToken')
            
            expires_in = int(data.get('expiresIn', 3600))
            self.token_expiry = time.time() + expires_in
            
            # Update Firestore client credentials
            from google.cloud import firestore
            creds = oauth_credentials.Credentials(token=self.id_token)
            self.db = firestore.Client(
                project=self.firestore_project,
                credentials=creds
            )
            
            logger.info("✅ Token refreshed successfully (via custom token)")
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh token: {e}")
            logger.error("Agent will continue but may lose Firestore access")
    
    def listen_for_tasks(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Listen for pending training tasks using real-time listeners.
        Only listens for tasks that are unassigned or assigned to this agent.
        
        Args:
            callback: Function to call when a task is available
        """
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name in ['ADDED', 'MODIFIED']:
                    task_data = change.document.to_dict()
                    task_id = change.document.id
                    
                    # Check if task is pending and either unassigned or assigned to this agent
                    if task_data.get('status') == 'pending':
                        assigned_to = task_data.get('assignedTo')
                        
                        # Only process if unassigned OR assigned to this agent
                        if not assigned_to or assigned_to == self.agent_id:
                            if self._can_handle_task(task_data):
                                logger.info(f"📋 Found pending task: {task_id}")
                                callback({**task_data, 'taskId': task_id})
                        else:
                            logger.debug(f"Skipping task {task_id} - assigned to different agent: {assigned_to}")
        
        # Query for pending tasks (includes both unassigned and tasks assigned to this agent)
        from google.cloud.firestore_v1 import FieldFilter
        query = self.db.collection("training_tasks").where(filter=FieldFilter("status", "==", "pending"))
        
        # Start listening
        self.task_listener = query.on_snapshot(on_snapshot)
        logger.info("✅ Started listening for training tasks (real-time)")
    
    def _can_handle_task(self, task: Dict[str, Any]) -> bool:
        """Check if agent can handle the task based on requirements"""
        config = task.get('config', {})
        
        # Check storage requirements (rough estimate: dataset + model)
        required_storage_gb = config.get('requiredStorageGB', 10)
        if self.capabilities['availableStorageGB'] < required_storage_gb:
            logger.warning(f"Insufficient storage: need {required_storage_gb}GB, have {self.capabilities['availableStorageGB']}GB")
            return False
        
        # Check memory requirements
        required_memory_gb = config.get('requiredMemoryGB', 8)
        if self.capabilities['totalMemoryGB'] < required_memory_gb:
            logger.warning(f"Insufficient memory: need {required_memory_gb}GB, have {self.capabilities['totalMemoryGB']}GB")
            return False
        
        # Check GPU requirements
        if config.get('requiresGPU', False) and not self.capabilities['hasGPU']:
            logger.warning("Task requires GPU but agent has none")
            return False
        
        return True
    
    def claim_task(self, task_id: str) -> bool:
        """
        Attempt to claim a task atomically.
        Uses optimistic locking: read current status, then update only if still pending.
        
        Only claims tasks that are:
        1. In 'pending' status, AND
        2. Either unassigned OR already assigned to this agent
        
        Args:
            task_id: Task ID to claim
            
        Returns:
            True if successfully claimed, False otherwise
        """
        try:
            task_ref = self.db.collection("training_tasks").document(task_id)
            
            # Read current task state
            snapshot = task_ref.get()
            if not snapshot.exists:
                logger.warning(f"Task {task_id} not found")
                return False
            
            task_data = snapshot.to_dict()
            
            # Check status
            if task_data.get('status') != 'pending':
                logger.debug(f"Task {task_id} no longer pending (status: {task_data.get('status')})")
                return False
            
            # Check assignment - only claim if unassigned or assigned to this agent
            assigned_to = task_data.get('assignedTo')
            if assigned_to and assigned_to != self.agent_id:
                logger.debug(f"Task {task_id} is assigned to different agent: {assigned_to}")
                return False
            
            # Attempt to claim (optimistic update)
            # If another agent claims between read and write, Firestore security rules
            # will prevent the update or we'll detect it in the verification below
            task_ref.update({
                'status': 'assigned',
                'assignedTo': self.agent_id,
                'assignedAt': "SERVER_TIMESTAMP"
            })
            
            # Verify we actually got it (double-check)
            updated_snapshot = task_ref.get()
            if updated_snapshot.exists:
                updated_data = updated_snapshot.to_dict()
                if updated_data.get('assignedTo') == self.agent_id:
                    logger.info(f"✅ Successfully claimed task: {task_id}")
                    self.current_task = task_id
                    
                    # Update agent status
                    self.db.collection("agents").document(self.agent_id).update({
                        "currentTask": {
                            "taskId": task_id,
                            "status": "assigned",
                            "startedAt": "SERVER_TIMESTAMP"
                        }
                    })
                    return True
                else:
                    logger.debug(f"Task {task_id} claimed by another agent: {updated_data.get('assignedTo')}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to claim task {task_id}: {e}")
            return False
    
    def listen_for_commands(self) -> None:
        """
        Listen for package management and configuration commands using real-time listeners.
        """
        def on_command_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name in ['ADDED', 'MODIFIED']:
                    command_data = change.document.to_dict()
                    command_id = change.document.id
                    
                    # Check if command is pending
                    if command_data.get('status') == 'pending':
                        logger.info(f"📦 Received command: {command_id} - {command_data.get('type')}")
                        self._handle_command(command_id, command_data)
        
        # Listen for commands addressed to this agent
        from google.cloud.firestore_v1 import FieldFilter
        query = self.db.collection("agent_commands") \
            .where(filter=FieldFilter("agentId", "==", self.agent_id)) \
            .where(filter=FieldFilter("status", "==", "pending"))
        
        # Start listening
        self.command_listener = query.on_snapshot(on_command_snapshot)
        logger.info("✅ Started listening for agent commands (real-time)")
    
    def _handle_command(self, command_id: str, command_data: Dict[str, Any]) -> None:
        """Handle a package management or configuration command"""
        try:
            command_type = command_data.get('type')
            params = command_data.get('params', {})
            
            # Update command status to processing
            self._update_command_status(command_id, "processing")
            
            result = None
            if command_type == "check_package":
                result = self.package_manager.check_package_installed(params.get('package'))
            elif command_type == "install_package":
                result = self.package_manager.install_package(
                    params.get('package'),
                    params.get('envType', 'current'),
                    params.get('envName')
                )
            elif command_type == "create_conda_env":
                result = self.package_manager.create_conda_env(
                    params.get('envName'),
                    params.get('pythonVersion', '3.10')
                )
            elif command_type == "create_venv":
                result = self.package_manager.create_venv(
                    params.get('venvPath'),
                    params.get('pythonExecutable', sys.executable)
                )
            elif command_type == "refresh_capabilities":
                # Re-detect capabilities
                self.capabilities = AgentCapabilities.detect()
                result = {"success": True, "capabilities": self.capabilities}
                # Update agent document with new capabilities
                self.db.collection("agents").document(self.agent_id).update({
                    "capabilities": self.capabilities
                })
            else:
                result = {"success": False, "error": f"Unknown command type: {command_type}"}
            
            # Update command with result
            self._update_command_status(command_id, "completed", result)
            logger.info(f"Command {command_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to handle command {command_id}: {e}")
            self._update_command_status(command_id, "failed", {"error": str(e)})
    
    def _update_command_status(self, command_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Update command status in Firestore"""
        try:
            update_data = {
                "status": status,
                "updatedAt": "SERVER_TIMESTAMP"
            }
            if result:
                update_data["result"] = result
            
            self.db.collection("agent_commands").document(command_id).update(update_data)
        except Exception as e:
            logger.error(f"Failed to update command status: {e}")
    
    def execute_task(self, task_id: str) -> None:
        """
        Execute a training task.
        
        Args:
            task_id: Task ID to execute
        """
        try:
            # Get task details
            task_doc = self.db.collection("training_tasks").document(task_id).get()
            if not task_doc.exists:
                raise ValueError(f"Task {task_id} not found")
            
            task_data = task_doc.to_dict()
            config = task_data['config']
            
            logger.info(f"Starting task execution: {task_id}")
            self._append_log(task_id, "info", f"Task claimed by agent {self.agent_id}")
            
            # DEBUG: Log what we received from Firestore
            self._append_log(task_id, "info", f"🔍 DEBUG: Received config from Firestore with keys: {list(config.keys())}")
            self._append_log(task_id, "info", f"🔍 DEBUG: config['epochs'] = {config.get('epochs', 'NOT FOUND')}")
            
            # Update status to running with additional metadata
            self._update_task_status(task_id, "running", {
                "assignedTo": self.agent_id,
                "agentName": self.authenticator.config.get("agentName", f"Agent {self.agent_id[:8]}"),
                "startedAt": "SERVER_TIMESTAMP",
                "trainingType": config.get('trainingType', 'agent_training'),  # agent_training vs kaggle
                "modelVariant": config.get('model', config.get('model_variant', 'yolo11n')),
                "totalEpochs": config.get('epochs', 100),
                "platform": self.capabilities.get('platform', 'unknown'),
                "device": self.detected_device or 'cpu',
            })
            
            # Validate environment
            self._append_log(task_id, "info", "Validating environment...")
            self._validate_environment(task_id, config)
            
            # Prepare dataset
            self._append_log(task_id, "info", "Preparing dataset...")
            dataset_dir = self._prepare_dataset(task_id, config)
            
            # Execute training using training script
            self._append_log(task_id, "info", "Starting training...")
            model_path, training_results = self._run_training_script(task_id, config, dataset_dir)
            
            # Upload model
            self._append_log(task_id, "info", "Uploading trained model...")
            model_url = self._upload_model(task_id, model_path)
            
            # Prepare completion data with training results
            completion_data = {
                "modelUrl": model_url,
                "completedAt": "SERVER_TIMESTAMP",
                "assignedTo": self.agent_id,
                "agentName": self.authenticator.config.get("agentName", f"Agent {self.agent_id[:8]}"),
                "trainingType": config.get('trainingType', 'agent_training'),
            }
            
            # Add training results if available
            if training_results:
                completion_data["trainingResults"] = training_results
                
                # Log key results
                if training_results.get('wandb_url'):
                    self._append_log(task_id, "info", f"📈 Wandb URL: {training_results['wandb_url']}")
                if training_results.get('kaggle_model_url'):
                    self._append_log(task_id, "info", f"🔗 Kaggle Model: {training_results['kaggle_model_url']}")
                if training_results.get('exported_formats'):
                    formats_str = ', '.join(training_results['exported_formats'])
                    self._append_log(task_id, "info", f"📦 Exported formats: {formats_str}")
            
            # Mark as completed with final metadata
            self._update_task_status(task_id, "completed", completion_data)
            
            self._append_log(task_id, "info", f"Task completed successfully! Model: {model_url}")
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self._append_log(task_id, "error", f"Task failed: {str(e)}")
            
            # Update with error status and metadata
            self._update_task_status(task_id, "failed", {
                "error": str(e),
                "assignedTo": self.agent_id,
                "agentName": self.authenticator.config.get("agentName", f"Agent {self.agent_id[:8]}"),
                "failedAt": "SERVER_TIMESTAMP",
                "trainingType": self.current_task_config.get('trainingType', 'agent_training') if hasattr(self, 'current_task_config') else 'agent_training',
            })
        
        finally:
            # Clear current task
            self.current_task = None
            
            # Remove from seen tasks to allow retry if it becomes pending again
            if task_id in self.seen_task_ids:
                self.seen_task_ids.remove(task_id)
            
            self.db.collection("agents").document(self.agent_id).update({
                "currentTask": None,
                "status": "online"
            })
    
    def _validate_environment(self, task_id: str, config: Dict[str, Any]) -> None:
        """Validate that environment meets requirements"""
        # 1. Proactively resolve and install PyTorch for this platform
        logger.info("🔧 Step 1: Validating PyTorch installation...")
        self._append_log(task_id, "info", "🔧 Step 1/3: Validating PyTorch installation...")
        
        pytorch_result = PlatformResolver.install_pytorch_for_platform()
        
        if not pytorch_result["success"]:
            error_msg = pytorch_result.get("error", "Unknown PyTorch installation error")
            logger.error(f"❌ PyTorch setup failed: {error_msg}")
            self._append_log(task_id, "error", f"❌ PyTorch setup failed: {error_msg}")
            raise RuntimeError(f"PyTorch installation failed: {error_msg}")
        
        device_type = pytorch_result.get("device", "cpu")
        reason = pytorch_result.get("reason", "")
        logger.info(f"✅ PyTorch ready: device={device_type} ({reason})")
        self._append_log(task_id, "info", f"✅ PyTorch ready: device={device_type}")
        self._append_log(task_id, "info", f"   Reason: {reason}")
        
        # Store detected device for later use in training
        self.detected_device = device_type
        
        # 2. Check YOLO installation
        logger.info("🔧 Step 2: Validating Ultralytics installation...")
        self._append_log(task_id, "info", "🔧 Step 2/3: Validating Ultralytics installation...")
        
        try:
            from ultralytics import YOLO
            logger.info("✅ Ultralytics (YOLO) is installed")
            self._append_log(task_id, "info", "✅ Ultralytics (YOLO) is installed")
        except ImportError:
            logger.error("❌ ultralytics not installed")
            self._append_log(task_id, "error", "❌ Ultralytics not installed. Run: pip install ultralytics")
            raise RuntimeError("ultralytics not installed. Run: pip install ultralytics")
        
        # 3. Check disk space
        logger.info("🔧 Step 3: Validating disk space...")
        self._append_log(task_id, "info", "🔧 Step 3/3: Validating disk space...")
        
        free_space_gb = psutil.disk_usage(str(self.work_dir)).free / (1024**3)
        required_space = config.get('requiredStorageGB', 10)
        
        if free_space_gb < required_space:
            error_msg = f"Insufficient disk space: {free_space_gb:.1f}GB available, {required_space}GB required"
            logger.error(error_msg)
            self._append_log(task_id, "error", f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        logger.info(f"✅ Disk space OK: {free_space_gb:.1f}GB available (need {required_space}GB)")
        self._append_log(task_id, "info", f"✅ Disk space OK: {free_space_gb:.1f}GB available")
        self._append_log(task_id, "info", "✅ Environment validation complete! Ready to train.")
        logger.info("✅ Environment validation complete")
    
    def _find_dataset_yaml(self, directory: Path) -> Optional[Path]:
        """
        Find dataset.yaml file in the directory or its subdirectories.
        
        Args:
            directory: Directory to search in
            
        Returns:
            Path to dataset.yaml if found, None otherwise
        """
        # Check root directory first
        yaml_path = directory / "dataset.yaml"
        if yaml_path.exists():
            return yaml_path
        
        # Check subdirectories (common for Kaggle datasets)
        for subdir in directory.iterdir():
            if subdir.is_dir():
                yaml_path = subdir / "dataset.yaml"
                if yaml_path.exists():
                    return yaml_path
                
                # Check one more level deep
                for subsubdir in subdir.iterdir():
                    if subsubdir.is_dir():
                        yaml_path = subsubdir / "dataset.yaml"
                        if yaml_path.exists():
                            return yaml_path
        
        return None
    
    def _download_kaggle_dataset(
        self, 
        task_id: str, 
        dataset_id: str, 
        target_dir: Path,
        config: Dict[str, Any]
    ) -> Path:
        """
        Download a single Kaggle dataset to target directory using Kaggle CLI.
        
        Args:
            task_id: Task ID for logging
            dataset_id: Kaggle dataset ID (username/dataset-name)
            target_dir: Directory to download dataset to
            config: Task config containing Kaggle credentials
            
        Returns:
            Path to downloaded dataset
        """
        import os
        import subprocess
        import time
        import json
        
        # Check if already downloaded
        if target_dir.exists() and any(target_dir.iterdir()):
            self._append_log(task_id, "info", f"✅ Using cached dataset: {dataset_id}")
            return target_dir
        
        # Download from Kaggle
        self._append_log(task_id, "info", f"📥 Downloading dataset from Kaggle: {dataset_id}")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Set up Kaggle credentials
            kaggle_username = config.get('kaggleUsername', config.get('kaggle_username'))
            kaggle_api_key = config.get('kaggleApiKey', config.get('kaggle_api_key'))
            
            # Prepare environment for CLI
            env = os.environ.copy()
            
            if kaggle_username and kaggle_api_key:
                env['KAGGLE_USERNAME'] = kaggle_username
                env['KAGGLE_KEY'] = kaggle_api_key
                self._append_log(task_id, "info", f"✅ Using Kaggle credentials from task config (user: {kaggle_username})")
            else:
                # Check if ~/.kaggle/kaggle.json exists as fallback
                kaggle_config_dir = Path.home() / ".kaggle"
                kaggle_json = kaggle_config_dir / "kaggle.json"
                
                if not kaggle_json.exists():
                    error_msg = (
                        "Kaggle credentials not found.\n\n"
                        "The task was submitted without Kaggle credentials, and no fallback credentials "
                        "were found in ~/.kaggle/kaggle.json\n\n"
                        "To fix this:\n"
                        "1. In the Aegis AI web app, go to Settings → Kaggle Credentials\n"
                        "2. Configure your Kaggle username and API key\n"
                        "3. Resubmit the training task\n\n"
                        "The credentials will be automatically included in the task config."
                    )
                    self._append_log(task_id, "error", error_msg)
                    raise ValueError(error_msg)
                
                self._append_log(task_id, "info", f"✅ Using Kaggle credentials from {kaggle_json}")
            
            # Parse dataset owner and name
            parts = dataset_id.split('/')
            if len(parts) != 2:
                raise ValueError(f"Invalid dataset ID format: {dataset_id}. Expected: username/dataset-name")
            
            owner, dataset_name = parts
            
            # Download dataset with progress monitoring using CLI
            self._append_log(task_id, "info", f"⬇️  Starting download: {owner}/{dataset_name}")
            self._append_log(task_id, "info", f"📂 Download location: {target_dir}")
            
            # Use Kaggle CLI for download (more reliable than Python API)
            # Download zip first, then extract separately to avoid CLI hanging issues
            self._append_log(task_id, "info", f"🔧 Using Kaggle CLI for download...")
            
            # Run kaggle datasets download command (without --unzip to avoid hanging)
            cmd = [
                "kaggle", "datasets", "download",
                "-d", dataset_id,
                "-p", str(target_dir)
                # Note: NOT using --unzip to avoid CLI hanging during extraction
            ]
            
            self._append_log(task_id, "info", f"📥 Running: {' '.join(cmd)}")
            self._append_log(task_id, "info", f"   Note: Will extract manually after download completes")
            
            # Start download process
            start_time = time.time()
            last_log_time = start_time
            last_size = 0
            
            try:
                # Start the download process with unbuffered output
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0,  # Unbuffered
                    universal_newlines=True
                )
                
                # Monitor progress with timeout
                import select
                import threading
                
                last_output_time = time.time()
                last_size_check = time.time()
                last_size = 0
                no_progress_count = 0
                
                def check_progress():
                    """Background thread to monitor directory size"""
                    nonlocal last_size, no_progress_count, last_size_check
                    while process.poll() is None:
                        time.sleep(10)
                        current_time = time.time()
                        if current_time - last_size_check >= 10:
                            try:
                                current_size = sum(
                                    f.stat().st_size 
                                    for f in target_dir.rglob('*') 
                                    if f.is_file()
                                )
                                
                                if current_size > last_size:
                                    size_mb = current_size / (1024 * 1024)
                                    size_gb = size_mb / 1024
                                    if size_gb >= 1:
                                        size_str = f"{size_gb:.2f} GB"
                                    else:
                                        size_str = f"{size_mb:.1f} MB"
                                    
                                    speed_mb = (current_size - last_size) / (1024 * 1024 * 10)
                                    self._append_log(task_id, "info", f"   📊 Downloaded: {size_str} ({speed_mb:.1f} MB/s)")
                                    last_size = current_size
                                    no_progress_count = 0
                                elif current_size > 0:
                                    no_progress_count += 1
                                    if no_progress_count >= 18:  # 3 minutes no progress
                                        self._append_log(task_id, "error", "Download stalled - no progress for 3 minutes")
                                        process.kill()
                                        return
                                
                                last_size_check = current_time
                            except:
                                pass
                
                # Start progress monitoring thread
                progress_thread = threading.Thread(target=check_progress, daemon=True)
                progress_thread.start()
                
                # Read output with timeout
                while process.poll() is None:
                    # Check if we have output available (non-blocking)
                    if process.stdout:
                        line = process.stdout.readline()
                        if line:
                            line = line.strip()
                            if line:
                                last_output_time = time.time()
                                # Log Kaggle CLI output
                                if "Downloading" in line or "%" in line:
                                    self._append_log(task_id, "info", f"   {line}")
                                elif "error" in line.lower() or "failed" in line.lower():
                                    self._append_log(task_id, "error", f"   {line}")
                                else:
                                    self._append_log(task_id, "info", f"   {line}")
                    
                    # Check for timeout (5 minutes without output)
                    if time.time() - last_output_time > 300:
                        self._append_log(task_id, "error", "Kaggle CLI timeout - no output for 5 minutes")
                        process.kill()
                        raise TimeoutError("Kaggle CLI hung - no output for 5 minutes")
                    
                    time.sleep(0.1)
                
                # Read any remaining output
                if process.stdout:
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            self._append_log(task_id, "info", f"   {line}")
                
                # Wait for process to complete
                return_code = process.wait(timeout=10)
                
                if return_code != 0:
                    error_msg = f"Kaggle CLI download failed with exit code {return_code}"
                    self._append_log(task_id, "error", error_msg)
                    self._append_log(task_id, "error", "Possible reasons:")
                    self._append_log(task_id, "error", "  1. Dataset doesn't exist or is private")
                    self._append_log(task_id, "error", "  2. Invalid Kaggle credentials")
                    self._append_log(task_id, "error", "  3. Network connectivity issues")
                    self._append_log(task_id, "error", f"  4. Dataset URL: https://www.kaggle.com/datasets/{dataset_id}")
                    raise RuntimeError(error_msg)
                
                # Find and extract the downloaded zip file
                import zipfile
                zip_files = list(target_dir.glob("*.zip"))
                
                if not zip_files:
                    raise ValueError(f"Download completed but no zip file found in: {target_dir}")
                
                zip_file = zip_files[0]
                zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
                self._append_log(task_id, "info", f"📦 Downloaded zip file: {zip_file.name} ({zip_size_mb:.1f} MB)")
                
                # Extract the zip file
                self._append_log(task_id, "info", f"📂 Extracting dataset...")
                extract_start = time.time()
                
                try:
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        # Get total uncompressed size
                        total_size = sum(info.file_size for info in zip_ref.infolist())
                        extracted_size = 0
                        last_progress_log = time.time()
                        
                        for member in zip_ref.infolist():
                            zip_ref.extract(member, target_dir)
                            extracted_size += member.file_size
                            
                            # Log progress every 10 seconds
                            if time.time() - last_progress_log >= 10:
                                progress = (extracted_size / total_size) * 100
                                self._append_log(task_id, "info", f"   📊 Extraction progress: {progress:.1f}%")
                                last_progress_log = time.time()
                    
                    # Remove the zip file after extraction
                    zip_file.unlink()
                    self._append_log(task_id, "info", f"✅ Extraction complete, removed zip file")
                    
                except Exception as e:
                    self._append_log(task_id, "error", f"Failed to extract zip file: {str(e)}")
                    raise
                
                extract_elapsed = time.time() - extract_start
                
                # Verify extraction
                if not any(f.is_file() and not f.name.endswith('.zip') for f in target_dir.rglob('*')):
                    raise ValueError(f"Extraction completed but no files found in: {target_dir}")
                
                # Calculate final size
                total_size = sum(
                    f.stat().st_size 
                    for f in target_dir.rglob('*') 
                    if f.is_file()
                )
                size_gb = total_size / (1024 * 1024 * 1024)
                total_elapsed = time.time() - start_time
                self._append_log(task_id, "info", f"✅ Successfully downloaded and extracted dataset: {dataset_id}")
                self._append_log(task_id, "info", f"   📊 Total size: {size_gb:.2f} GB")
                self._append_log(task_id, "info", f"   ⏱️  Download time: {int(total_elapsed - extract_elapsed)}s")
                self._append_log(task_id, "info", f"   ⏱️  Extract time: {int(extract_elapsed)}s")
                self._append_log(task_id, "info", f"   ⏱️  Total time: {int(total_elapsed)}s")
                
                return target_dir
                
            except subprocess.TimeoutExpired:
                process.kill()
                self._append_log(task_id, "error", "Download timed out")
                raise TimeoutError("Kaggle download timed out")
            
        except Exception as e:
            error_msg = f"Failed to download Kaggle dataset {dataset_id}: {str(e)}"
            self._append_log(task_id, "error", error_msg)
            raise ValueError(error_msg)
    
    def _download_huggingface_dataset(
        self, 
        task_id: str, 
        dataset_id: str, 
        target_dir: Path,
        config: Dict[str, Any]
    ) -> Path:
        """
        Download a HuggingFace dataset and convert to COCO format.
        
        Args:
            task_id: Task ID for logging
            dataset_id: HuggingFace dataset ID (org/dataset-name)
            target_dir: Directory to download dataset to
            config: Task config
            
        Returns:
            Path to downloaded dataset
        """
        import json
        from PIL import Image
        import io
        
        # Check if already downloaded
        if target_dir.exists() and any(target_dir.iterdir()):
            self._append_log(task_id, "info", f"✅ Using cached dataset: {dataset_id}")
            return target_dir
        
        # Download from HuggingFace
        self._append_log(task_id, "info", f"📥 Downloading dataset from HuggingFace: {dataset_id}")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Import HuggingFace datasets library
            try:
                from datasets import load_dataset
            except ImportError:
                error_msg = (
                    "HuggingFace datasets library not installed.\n"
                    "Please install it: pip install datasets"
                )
                self._append_log(task_id, "error", error_msg)
                raise ImportError(error_msg)
            
            self._append_log(task_id, "info", f"⬇️  Starting download: {dataset_id}")
            self._append_log(task_id, "info", f"📂 Download location: {target_dir}")
            
            start_time = time.time()
            
            # Load dataset (downloads automatically)
            self._append_log(task_id, "info", "🔧 Loading dataset from HuggingFace Hub...")
            dataset = load_dataset(dataset_id, split="train")
            
            download_time = time.time() - start_time
            self._append_log(task_id, "info", f"✅ Dataset loaded ({int(download_time)}s)")
            self._append_log(task_id, "info", f"📊 Total samples: {len(dataset)}")
            
            # Convert to COCO format
            self._append_log(task_id, "info", "🔄 Converting to COCO format...")
            convert_start = time.time()
            
            # Create directory structure
            images_dir = target_dir / "images"
            annotations_dir = target_dir / "annotations"
            images_dir.mkdir(parents=True, exist_ok=True)
            annotations_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize COCO structure
            coco_data = {
                "images": [],
                "annotations": [],
                "categories": []
            }
            
            # Track unique categories
            category_map = {}  # Maps category ID to COCO category
            next_category_id = 1
            annotation_id = 1
            
            # Process samples
            self._append_log(task_id, "info", f"📦 Processing {len(dataset)} samples...")
            
            for idx, sample in enumerate(dataset):
                try:
                    # Extract image
                    image = sample.get('image')
                    if image is None:
                        continue
                    
                    # Save image
                    image_filename = f"{sample.get('image_id', idx):012d}.jpg"
                    image_path = images_dir / image_filename
                    
                    # Convert PIL Image to file
                    if hasattr(image, 'save'):
                        image.save(image_path, 'JPEG', quality=95)
                    else:
                        # Handle other image formats
                        continue
                    
                    # Get image dimensions
                    width = sample.get('width', image.width if hasattr(image, 'width') else 640)
                    height = sample.get('height', image.height if hasattr(image, 'height') else 480)
                    
                    # Add image to COCO
                    coco_data["images"].append({
                        "id": sample.get('image_id', idx),
                        "file_name": image_filename,
                        "width": width,
                        "height": height
                    })
                    
                    # Process objects/annotations
                    objects = sample.get('objects', {})
                    if objects:
                        categories = objects.get('category', [])
                        bboxes = objects.get('bbox', [])
                        areas = objects.get('area', [])
                        bbox_ids = objects.get('bbox_id', [])
                        
                        for obj_idx, (category, bbox) in enumerate(zip(categories, bboxes)):
                            # Map category to COCO category ID
                            if category not in category_map:
                                category_map[category] = {
                                    "id": next_category_id,
                                    "name": f"class_{category}",
                                    "supercategory": "object"
                                }
                                next_category_id += 1
                            
                            # Add annotation
                            coco_data["annotations"].append({
                                "id": annotation_id,
                                "image_id": sample.get('image_id', idx),
                                "category_id": category_map[category]["id"],
                                "bbox": bbox,  # [x, y, width, height]
                                "area": areas[obj_idx] if obj_idx < len(areas) else (bbox[2] * bbox[3]),
                                "iscrowd": 0
                            })
                            annotation_id += 1
                    
                    # Progress update every 1000 samples
                    if (idx + 1) % 1000 == 0:
                        progress_pct = ((idx + 1) / len(dataset)) * 100
                        self._append_log(task_id, "info", f"   📊 Progress: {idx + 1}/{len(dataset)} ({progress_pct:.1f}%)")
                
                except Exception as e:
                    self._append_log(task_id, "warning", f"⚠️  Skipped sample {idx}: {str(e)}")
                    continue
            
            # Add categories to COCO data
            coco_data["categories"] = list(category_map.values())
            
            # Save COCO annotations
            annotations_file = annotations_dir / "instances_train.json"
            with open(annotations_file, 'w') as f:
                json.dump(coco_data, f)
            
            self._append_log(task_id, "info", f"✅ Saved {len(coco_data['images'])} images")
            self._append_log(task_id, "info", f"✅ Saved {len(coco_data['annotations'])} annotations")
            self._append_log(task_id, "info", f"✅ Found {len(coco_data['categories'])} categories")
            
            # Create data.yaml for YOLO
            yaml_content = f"""# HuggingFace dataset: {dataset_id}
# Converted to COCO format

path: {target_dir}
train: images
val: images

# Classes
nc: {len(coco_data['categories'])}
names: {[cat['name'] for cat in coco_data['categories']]}
"""
            
            yaml_path = target_dir / "data.yaml"
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)
            
            convert_time = time.time() - convert_start
            total_time = time.time() - start_time
            
            # Calculate final size
            total_size = sum(
                f.stat().st_size 
                for f in target_dir.rglob('*') 
                if f.is_file()
            )
            size_gb = total_size / (1024 * 1024 * 1024)
            
            self._append_log(task_id, "info", f"✅ Successfully downloaded and converted dataset: {dataset_id}")
            self._append_log(task_id, "info", f"   📊 Total size: {size_gb:.2f} GB")
            self._append_log(task_id, "info", f"   ⏱️  Download time: {int(download_time)}s")
            self._append_log(task_id, "info", f"   ⏱️  Convert time: {int(convert_time)}s")
            self._append_log(task_id, "info", f"   ⏱️  Total time: {int(total_time)}s")
            
            return target_dir
            
        except Exception as e:
            error_msg = f"Failed to download HuggingFace dataset {dataset_id}: {str(e)}"
            self._append_log(task_id, "error", error_msg)
            raise ValueError(error_msg)
    
    def _prepare_dataset(self, task_id: str, config: Dict[str, Any]) -> Path:
        """
        Prepare dataset(s) for training.
        
        Supports both single dataset (legacy) and multiple datasets (new).
        For multiple datasets, downloads each to a separate folder in the input directory.
        The training script will automatically discover and merge them.
        
        Args:
            task_id: Task ID for logging
            config: Task configuration
            
        Returns:
            Path to input directory containing dataset(s)
        """
        # NEW: Check if multiple datasets are provided
        datasets_config = config.get('datasets', [])
        
        if datasets_config and len(datasets_config) > 1:
            # Multiple datasets - download each to separate folder
            self._append_log(task_id, "info", f"🔀 Multiple datasets detected: {len(datasets_config)} datasets")
            self._append_log(task_id, "info", f"📊 Dataset preparation progress: 0/{len(datasets_config)} completed")
            
            # Create input directory for all datasets
            input_dir = self.work_dir / task_id / "input"
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Download each dataset
            for i, ds_config in enumerate(datasets_config):
                ds_source = ds_config.get('source', 'kaggle')
                ds_path = ds_config.get('path')
                ds_name = ds_config.get('name', f'dataset-{i+1}')
                
                self._append_log(task_id, "info", f"")  # Empty line for readability
                self._append_log(task_id, "info", f"{'='*60}")
                self._append_log(task_id, "info", f"📦 Dataset {i+1}/{len(datasets_config)}: {ds_name}")
                self._append_log(task_id, "info", f"{'='*60}")
                
                # Create dataset-specific directory
                # Use a sanitized name for the folder
                safe_name = ds_name.replace('/', '-').replace(' ', '-').lower()
                ds_dir = input_dir / safe_name
                
                if ds_source == 'kaggle':
                    if not ds_path:
                        raise ValueError(f"Kaggle dataset path not provided for dataset: {ds_name}")
                    
                    # For Kaggle datasets, use cache directory to avoid re-downloading
                    datasets_cache_dir = self.work_dir / "datasets"
                    datasets_cache_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Use dataset ID as folder name (replace / with -)
                    dataset_folder = ds_path.replace('/', '-')
                    dataset_cache_dir = datasets_cache_dir / dataset_folder
                    
                    # Download to cache
                    self._download_kaggle_dataset(task_id, ds_path, dataset_cache_dir, config)
                    
                    # Create symlink to cache in input directory
                    if not ds_dir.exists():
                        ds_dir.symlink_to(dataset_cache_dir, target_is_directory=True)
                    
                    # Calculate dataset size
                    try:
                        total_size = sum(f.stat().st_size for f in dataset_cache_dir.rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)
                        size_gb = size_mb / 1024
                        
                        if size_gb >= 1:
                            size_str = f"{size_gb:.2f} GB"
                        else:
                            size_str = f"{size_mb:.1f} MB"
                        
                        self._append_log(task_id, "info", f"✅ Dataset ready: {ds_name} ({size_str})")
                    except Exception as e:
                        self._append_log(task_id, "info", f"✅ Dataset ready: {ds_name}")
                    
                    # Update progress
                    self._append_log(task_id, "info", f"📊 Dataset preparation progress: {i+1}/{len(datasets_config)} completed")
                
                elif ds_source == 'huggingface':
                    if not ds_path:
                        raise ValueError(f"HuggingFace dataset path not provided for dataset: {ds_name}")
                    
                    # For HuggingFace datasets, use cache directory to avoid re-downloading
                    datasets_cache_dir = self.work_dir / "datasets"
                    datasets_cache_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Use dataset ID as folder name (replace / with -)
                    dataset_folder = ds_path.replace('/', '-')
                    dataset_cache_dir = datasets_cache_dir / dataset_folder
                    
                    # Download to cache
                    self._download_huggingface_dataset(task_id, ds_path, dataset_cache_dir, config)
                    
                    # Create symlink to cache in input directory
                    if not ds_dir.exists():
                        ds_dir.symlink_to(dataset_cache_dir, target_is_directory=True)
                    
                    # Calculate dataset size
                    try:
                        total_size = sum(f.stat().st_size for f in dataset_cache_dir.rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)
                        size_gb = size_mb / 1024
                        
                        if size_gb >= 1:
                            size_str = f"{size_gb:.2f} GB"
                        else:
                            size_str = f"{size_mb:.1f} MB"
                        
                        self._append_log(task_id, "info", f"✅ Dataset ready: {ds_name} ({size_str})")
                    except Exception as e:
                        self._append_log(task_id, "info", f"✅ Dataset ready: {ds_name}")
                    
                    # Update progress
                    self._append_log(task_id, "info", f"📊 Dataset preparation progress: {i+1}/{len(datasets_config)} completed")
                
                elif ds_source == 'local':
                    # Local dataset - copy or symlink
                    local_path = Path(ds_path)
                    if not local_path.exists():
                        raise ValueError(f"Local dataset not found: {ds_path}")
                    
                    if not ds_dir.exists():
                        ds_dir.symlink_to(local_path, target_is_directory=True)
                        self._append_log(task_id, "info", f"✅ Linked local dataset: {ds_name}")
                
                elif ds_source == 'url':
                    # URL dataset - download and extract
                    self._append_log(task_id, "info", f"📥 Downloading from URL: {ds_path}")
                    # TODO: Implement URL download
                    raise NotImplementedError("URL dataset source not yet implemented for multi-dataset training")
                
                else:
                    raise ValueError(f"Unknown dataset source: {ds_source}")
            
            # Final summary
            self._append_log(task_id, "info", f"")  # Empty line
            self._append_log(task_id, "info", f"{'='*60}")
            self._append_log(task_id, "info", f"✅ Dataset Preparation Complete")
            self._append_log(task_id, "info", f"{'='*60}")
            self._append_log(task_id, "info", f"📊 Total datasets: {len(datasets_config)}")
            
            # Calculate total size
            try:
                total_size = sum(
                    f.stat().st_size 
                    for ds_dir in input_dir.iterdir() 
                    if ds_dir.is_dir()
                    for f in ds_dir.rglob('*') 
                    if f.is_file()
                )
                total_gb = total_size / (1024 * 1024 * 1024)
                self._append_log(task_id, "info", f"💾 Total size: {total_gb:.2f} GB")
            except Exception:
                pass
            
            self._append_log(task_id, "info", f"📂 Input directory: {input_dir}")
            self._append_log(task_id, "info", f"🔄 Training script will automatically discover and merge datasets")
            self._append_log(task_id, "info", f"{'='*60}")
            
            return input_dir
        
        elif datasets_config and len(datasets_config) == 1:
            # Single dataset in new format - extract and use legacy path
            self._append_log(task_id, "info", "📦 Single dataset provided (new format)")
            ds_config = datasets_config[0]
            ds_source = ds_config.get('source', 'kaggle')
            ds_path = ds_config.get('path')
            
            # Use legacy single-dataset handling
            config['datasetSource'] = ds_source
            config['datasetPath'] = ds_path
            # Fall through to legacy handling below
        
        # LEGACY: Single dataset handling (backward compatibility)
        dataset_source = config.get('datasetSource', 'local')
        
        if dataset_source == 'local':
            dataset_path = Path(config.get('datasetPath', ''))
            if not dataset_path.exists():
                raise ValueError(f"Local dataset not found: {dataset_path}")
            return dataset_path
        
        elif dataset_source == 'kaggle':
            # Download dataset from Kaggle (legacy single dataset)
            dataset_id = config.get('datasetPath')
            if not dataset_id:
                raise ValueError("Kaggle dataset ID not provided")
            
            # Create dataset cache directory
            datasets_dir = self.work_dir / "datasets"
            datasets_dir.mkdir(parents=True, exist_ok=True)
            
            # Use dataset name as folder (replace / with -)
            dataset_folder = dataset_id.replace('/', '-')
            dataset_cache_dir = datasets_dir / dataset_folder
            
            # Use the extracted download method
            return self._download_kaggle_dataset(task_id, dataset_id, dataset_cache_dir, config)
        
        elif dataset_source == 'huggingface':
            # Download dataset from HuggingFace (legacy single dataset)
            dataset_id = config.get('datasetPath')
            if not dataset_id:
                raise ValueError("HuggingFace dataset ID not provided")
            
            # Create dataset cache directory
            datasets_dir = self.work_dir / "datasets"
            datasets_dir.mkdir(parents=True, exist_ok=True)
            
            # Use dataset name as folder (replace / with -)
            dataset_folder = dataset_id.replace('/', '-')
            dataset_cache_dir = datasets_dir / dataset_folder
            
            # Use the extracted download method
            return self._download_huggingface_dataset(task_id, dataset_id, dataset_cache_dir, config)
        
        elif dataset_source == 'url':
            # Download dataset from URL
            dataset_url = config.get('datasetUrl')
            if not dataset_url:
                raise ValueError("Dataset URL not provided")
            
            download_dir = self.work_dir / task_id / "dataset"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # TODO: Implement dataset download
            # For now, assume dataset is a zip file
            self._append_log(task_id, "info", f"Downloading dataset from {dataset_url}")
            
            # Use wget or requests to download
            import requests
            response = requests.get(dataset_url, stream=True)
            response.raise_for_status()
            
            zip_path = download_dir / "dataset.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_dir)
            
            return download_dir
        
        else:
            raise ValueError(f"Unknown dataset source: {dataset_source}")
    
    def _run_training_script(
        self, 
        task_id: str, 
        config: Dict[str, Any], 
        dataset_dir: Path
    ) -> Path:
        """Run training using the training script (same as Kaggle)"""
        import subprocess
        import json
        import os
        from pathlib import Path as PathlibPath
        
        # Create task working directory
        task_work_dir = self.work_dir / task_id
        task_work_dir.mkdir(parents=True, exist_ok=True)
        
        # Create input directory structure (mimic Kaggle)
        input_dir = task_work_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        # Symlink dataset to input directory
        dataset_link = input_dir / dataset_dir.name
        if not dataset_link.exists():
            dataset_link.symlink_to(dataset_dir, target_is_directory=True)
        
        # Create working directory
        working_dir = task_work_dir / "working"
        working_dir.mkdir(exist_ok=True)
        
        # Prepare training config
        # Use config values directly, log warning if critical fields missing
        if 'epochs' not in config:
            self._append_log(task_id, "warning", f"⚠️  'epochs' not in config, using default: 100")
        
        training_config = {
            'model_variant': config.get('model', config.get('model_variant', 'yolo11n')),
            'epochs': config.get('epochs', 100),
            'batch_size': config.get('batchSize', config.get('batch_size', 16)),
            'img_size': config.get('imgsz', config.get('img_size', 640)),
            'output_formats': config.get('outputFormats', config.get('output_formats', ['onnx'])),
            # Wandb configuration (API key will be passed via env var)
            'wandb_enabled': config.get('wandbEnabled', config.get('wandb_enabled', False)),
            'wandb_project': config.get('wandbProject', config.get('wandb_project', 'aegis-ai')),
            'wandb_entity': config.get('wandbEntity', config.get('wandb_entity', None)),
            'wandb_api_key': config.get('wandbApiKey', config.get('wandb_api_key', None)),
            # Kaggle upload configuration (credentials will be passed via env var)
            'kaggle_upload_enabled': config.get('kaggleUploadEnabled', config.get('kaggle_upload_enabled', False)),
            'kaggle_username': config.get('kaggleUsername', config.get('kaggle_username', None)),
            'kaggle_api_key': config.get('kaggleApiKey', config.get('kaggle_api_key', None)),
            'kaggle_model_slug': config.get('kaggleModelSlug', config.get('kaggle_model_slug', None)),
            'trainingType': config.get('trainingType', 'agent_training'),
            # Pass all optimization parameters
            'learning_rate': config.get('learning_rate', 0.01),
            'momentum': config.get('momentum', 0.937),
            'weight_decay': config.get('weight_decay', 0.0005),
            'warmup_epochs': config.get('warmup_epochs', 3),
            'early_stopping': config.get('early_stopping', {'patience': 50}),
            # Augmentation parameters
            'hsv_h': config.get('hsv_h', 0.015),
            'hsv_s': config.get('hsv_s', 0.7),
            'hsv_v': config.get('hsv_v', 0.4),
            'degrees': config.get('degrees', 0.0),
            'translate': config.get('translate', 0.1),
            'scale': config.get('scale', 0.5),
            'flipud': config.get('flipud', 0.0),
            'fliplr': config.get('fliplr', 0.5),
            'mosaic': config.get('mosaic', 1.0),
            'mixup': config.get('mixup', 0.0),
        }
        
        self._append_log(task_id, "info", f"📊 Training config: model={training_config['model_variant']}, epochs={training_config['epochs']}, batch_size={training_config['batch_size']}")
        
        # Write config to file (for local agents)
        config_file = input_dir / "training_config.json"
        with open(config_file, 'w') as f:
            json.dump(training_config, f, indent=2)
        
        self._append_log(task_id, "info", f"📝 Wrote training config to {config_file}")
        self._append_log(task_id, "info", f"🔍 DEBUG: Config file contains epochs={training_config['epochs']}")
        
        # Get training script path
        script_path = PathlibPath(__file__).parent / "training_script.py"
        if not script_path.exists():
            raise RuntimeError(f"Training script not found: {script_path}")
        
        self._append_log(task_id, "info", f"Using training script: {script_path}")
        self._append_log(task_id, "info", f"Dataset directory: {input_dir}")
        self._append_log(task_id, "info", f"Working directory: {working_dir}")
        
        # Set environment variables for agent mode
        env = os.environ.copy()
        env['AEGIS_AGENT_MODE'] = '1'
        env['AEGIS_INPUT_DIR'] = str(input_dir)
        env['AEGIS_WORKING_DIR'] = str(working_dir)
        
        # Fix for CUDA architecture errors on newer GPUs (H100, H200, GB10, etc.)
        # This prevents "nvrtc: error: invalid value for --gpu-architecture" errors
        if 'TORCH_CUDA_ARCH_LIST' not in env:
            # Support all common architectures from Volta (7.0) to Blackwell (9.0)
            # 7.0=Volta, 7.5=Turing, 8.0=Ampere, 8.6=RTX30, 8.9=RTX40, 9.0=H100/H200, 9.2=Blackwell
            arch_list = AgentTrainer._get_optimal_cuda_arch_list(training_config)
            env['TORCH_CUDA_ARCH_LIST'] = arch_list
            self._append_log(task_id, "info", f"🔧 Set TORCH_CUDA_ARCH_LIST for GPU compatibility: {arch_list}")
        
        # Disable PyTorch JIT/NVRTC compilation for unsupported GPUs
        # This forces PyTorch to use pre-compiled kernels only
        # env['PYTORCH_JIT'] = '0'
        # env['PYTORCH_NVFUSER_DISABLE'] = '1'
        # self._append_log(task_id, "info", "🚫 Disabled PyTorch JIT compilation (using pre-compiled kernels only)")
        
        # ✅ NEW: Pass config via environment variable (for remote agents)
        # This allows the training script to work without file-based config sharing
        env['AEGIS_TRAINING_CONFIG'] = json.dumps(training_config)
        self._append_log(task_id, "info", "✅ Training config embedded in environment variable")
        
        # Pass detected device to training script
        if self.detected_device:
            env['AEGIS_DEVICE'] = self.detected_device
            self._append_log(task_id, "info", f"Using device: {self.detected_device}")
        else:
            env['AEGIS_DEVICE'] = 'cpu'  # Fallback
            self._append_log(task_id, "info", "Using device: cpu (fallback)")
        
        # Pass Wandb API key if enabled
        if training_config.get('wandb_enabled') and training_config.get('wandb_api_key'):
            env['WANDB_API_KEY'] = training_config['wandb_api_key']
            self._append_log(task_id, "info", "✅ Wandb API key configured")
        
        # Pass Kaggle credentials if upload enabled
        if training_config.get('kaggle_upload_enabled'):
            if training_config.get('kaggle_username') and training_config.get('kaggle_api_key'):
                env['KAGGLE_USERNAME'] = training_config['kaggle_username']
                env['KAGGLE_KEY'] = training_config['kaggle_api_key']
                self._append_log(task_id, "info", "✅ Kaggle credentials configured")
        
        # Run training script
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output and capture JSON results
            stdout_lines = []
            json_capture = False
            json_lines = []
            training_results = None
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    stdout_lines.append(line)
                    print(line)  # Print to agent logs
                    
                    # Check for JSON markers
                    if '=== TRAINING_RESULTS_JSON ===' in line:
                        json_capture = True
                        self._append_log(task_id, "info", "📊 Capturing training results...")
                        continue
                    elif '=== END_TRAINING_RESULTS ===' in line:
                        json_capture = False
                        # Parse captured JSON
                        try:
                            json_str = '\n'.join(json_lines)
                            training_results = json.loads(json_str)
                            self._append_log(task_id, "info", "✅ Training results captured successfully")
                            logger.info(f"Training results: {training_results}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse training results JSON: {e}")
                            self._append_log(task_id, "warning", f"⚠️ Failed to parse training results: {e}")
                        continue
                    
                    # Capture JSON lines
                    if json_capture:
                        json_lines.append(line)
                    else:
                        # Log important lines to Firestore
                        if any(marker in line for marker in ['🚀', '✅', '❌', '📊', 'Epoch']):
                            self._append_log(task_id, "info", line)
            
            process.wait()
            
            if process.returncode != 0:
                raise RuntimeError(f"Training script failed with exit code {process.returncode}")
            
            self._append_log(task_id, "info", "Training script completed successfully")
            
        except Exception as e:
            self._append_log(task_id, "error", f"Training script error: {str(e)}")
            raise
        
        # Find the trained model
        # The trainer saves models to trained_models directory
        trained_models_dir = working_dir / "trained_models"
        
        # Look for best.pt in trained_models
        best_model = trained_models_dir / "best.pt"
        
        if best_model.exists():
            self._append_log(task_id, "info", f"Found trained model: {best_model}")
            return best_model, training_results
        
        # Fallback: Check in yolo training runs directory
        yolo_dataset_dir = working_dir / "yolo_dataset"
        runs_dir = yolo_dataset_dir / "runs" / "detect" / "train"
        best_model = runs_dir / "weights" / "best.pt"
        
        if best_model.exists():
            self._append_log(task_id, "info", f"Found trained model in runs: {best_model}")
            return best_model, training_results
        
        # Alternative: Check if runs is at working_dir level
        best_model = working_dir / "runs" / "detect" / "train" / "weights" / "best.pt"
        if best_model.exists():
            self._append_log(task_id, "info", f"Found trained model in runs: {best_model}")
            return best_model, training_results
        
        # List available files for debugging
        available_files = []
        if trained_models_dir.exists():
            available_files.extend([str(f.relative_to(working_dir)) for f in trained_models_dir.glob("*")])
        if runs_dir.exists():
            available_files.extend([str(f.relative_to(working_dir)) for f in runs_dir.glob("**/*") if f.is_file()])
        
        error_msg = f"Training completed but best model not found. Checked: {trained_models_dir}, {runs_dir}"
        if available_files:
            error_msg += f"\nAvailable files: {', '.join(available_files[:10])}"
        
        self._append_log(task_id, "error", error_msg)
        raise RuntimeError(error_msg)
    
    def _upload_model(self, task_id: str, model_path: Path) -> str:
        """Upload trained model to storage"""
        # TODO: Implement Firebase Storage upload
        # For now, return local path
        return str(model_path)
    
    def _update_task_status(
        self, 
        task_id: str, 
        status: str, 
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update task status in Firestore"""
        update_data = {"status": status}
        if extra_fields:
            update_data.update(extra_fields)
        
        try:
            self.db.collection("training_tasks").document(task_id).update(update_data)
            logger.info(f"✅ Task {task_id} status updated to: {status}")
        except Exception as e:
            logger.error(f"❌ Failed to update task {task_id} status to {status}: {e}")
            raise
    
    def _append_log(self, task_id: str, level: str, message: str) -> None:
        """Append log entry to task"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        # TODO: Implement array append for REST API
        # self.db.collection("training_tasks").document(task_id).update({
        #     "logs": ArrayUnion([log_entry])
        # })
        
        # Also log locally
        log_func = logger.info if level == "info" else logger.error
        log_func(f"[{task_id}] {message}")
    
    def start(self) -> None:
        """Start the agent daemon"""
        logger.info(f"Starting agent: {self.agent_id}")
        
        try:
            # Initialize Firebase Admin SDK
            self.initialize_firebase()
            
            # Register agent
            self.register_agent()
            
            # Start listening for tasks and commands (real-time)
            self.running = True
            
            def handle_task(task_data):
                task_id = task_data['taskId']
                if self.claim_task(task_id):
                    self.execute_task(task_id)
            
            self.listen_for_tasks(handle_task)
            self.listen_for_commands()
            
            # Heartbeat loop (real-time listeners active)
            logger.info("⚡ Real-time mode: 30-second heartbeat")
            logger.info("Agent started successfully. Press Ctrl+C to stop.")
            
            while self.running:
                self.update_heartbeat()
                time.sleep(30)  # Heartbeat every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("Shutting down agent...")
            self.stop()
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the agent daemon"""
        self.running = False
        
        # Update agent status to offline
        if self.db:
            try:
                self.db.collection("agents").document(self.agent_id).update({
                    "status": "offline",
                    "lastSeen": "SERVER_TIMESTAMP"
                })
            except Exception as e:
                logger.warning(f"Failed to update agent status: {e}")
        
        # Stop listeners (polling threads)
        if self.task_listener and hasattr(self.task_listener, 'join'):
            # It's a thread, wait for it to finish
            pass  # Thread will exit when self.running = False
        if self.command_listener and hasattr(self.command_listener, 'join'):
            # It's a thread, wait for it to finish
            pass  # Thread will exit when self.running = False
        
        logger.info("Agent stopped")
    
    @staticmethod
    def _get_optimal_cuda_arch_list(training_config: Dict[str, Any]) -> str:
        """
        Determine optimal CUDA architecture list based on detected GPUs
        and training configuration.
        
        Supports:
        - Volta (7.0): V100, Titan V
        - Turing (7.5): RTX 2080, RTX 2090, Titan RTX
        - Ampere (8.0-8.6): A100, RTX 3090, RTX 3080
        - Ada (8.9): RTX 4090, RTX 4080, L40S
        - Hopper (9.0-9.1): H100, H200
        - Blackwell (9.2): B100, B200
        
        Returns:
            Space-separated CUDA architecture list with +PTX flag for forward compatibility
        """
        try:
            # Default comprehensive list supporting all modern architectures
            # This includes +PTX for forward compatibility with future GPUs
            default_archs = "7.0 7.5 8.0 8.6 8.9 9.0 9.1 9.2+PTX"
            
            # Try to detect GPU compute capability from training config
            gpu_info = training_config.get('gpu_info', {})
            if isinstance(gpu_info, dict):
                compute_capability = gpu_info.get('compute_capability', '')
                if compute_capability:
                    try:
                        # Parse compute capability (e.g., "9.0" for H100)
                        major, minor = compute_capability.split('.')
                        major_ver = int(major)
                        minor_ver = int(minor)
                        
                        # If it's a newer architecture, include +PTX for future compatibility
                        if major_ver >= 9:
                            return f"{major_ver}.{minor_ver}+PTX"
                    except (ValueError, AttributeError):
                        pass
            
            return default_archs
        except Exception as e:
            logger.debug(f"Error determining optimal CUDA arch list: {e}")
            return "7.0 7.5 8.0 8.6 8.9 9.0 9.1 9.2+PTX"

