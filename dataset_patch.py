
"""
Temporary patch to fix dataset filtering issues
"""

def patch_dataset_filtering():
    """Patch the dataset filtering to be less restrictive"""
    import sys
    from pathlib import Path
    
    # Try to import and patch tts_trainer
    try:
        import tts_trainer
        
        # Save original filtering method
        if hasattr(tts_trainer, 'GenshinVoiceDataset'):
            original_filter = tts_trainer.GenshinVoiceDataset._filter_dataset
            
            def relaxed_filter(self):
                """Relaxed filtering for debugging"""
                valid_indices = []
                
                for idx in range(min(100, len(self.dataset))):  # Limit to first 100 for testing
                    try:
                        sample = self.dataset[idx]
                        
                        # Check if sample has basic required fields
                        has_audio = 'audio' in sample and sample['audio'] is not None
                        has_text = 'text' in sample and sample['text'] and len(str(sample['text']).strip()) > 0
                        
                        if has_audio and has_text:
                            # Basic audio check
                            if isinstance(sample['audio'], dict):
                                if 'array' in sample['audio'] and sample['audio']['array']:
                                    if len(sample['audio']['array']) > 1000:  # At least 1000 samples
                                        valid_indices.append(idx)
                            
                    except Exception as e:
                        continue
                
                print(f"Relaxed filter found {len(valid_indices)} valid samples out of first 100")
                return valid_indices if valid_indices else [0, 1, 2]  # Force at least 3 samples
            
            # Apply patch
            tts_trainer.GenshinVoiceDataset._filter_dataset = relaxed_filter
            return True
            
    except Exception as e:
        print(f"Dataset patching failed: {e}")
        return False

if __name__ == "__main__":
    patch_dataset_filtering()
