
"""
Windows compatibility patch for DataLoader multiprocessing issues
"""

import platform
import torch
from torch.utils.data import DataLoader

def patch_dataloader_for_windows():
    """Patch DataLoader creation to avoid Windows multiprocessing issues"""
    
    def safe_dataloader(*args, **kwargs):
        """Safe DataLoader that works on Windows"""
        # Force single-threaded on Windows
        if platform.system() == "Windows":
            kwargs['num_workers'] = 0
            kwargs['multiprocessing_context'] = None
            kwargs['persistent_workers'] = False
        
        # Remove problematic arguments
        problematic_args = ['prefetch_factor', 'generator']
        for arg in problematic_args:
            kwargs.pop(arg, None)
        
        return DataLoader(*args, **kwargs)
    
    return safe_dataloader

def apply_windows_patches():
    """Apply all Windows-specific patches"""
    import sys
    
    # Patch torch multiprocessing
    if platform.system() == "Windows":
        import torch.multiprocessing as mp
        try:
            mp.set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # Already set
        
        # Set environment variables for Windows
        import os
        os.environ['PYTHONHASHSEED'] = '0'
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    
    print("Windows compatibility patches applied")
    return True

if __name__ == "__main__":
    apply_windows_patches()
