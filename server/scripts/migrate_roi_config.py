#!/usr/bin/env python3
"""
Migration script to convert ROI configuration from array format to object format.

Array format (old):
[1, 1, [x1, y1, x2, y2], 305, 1200, null, "opencv", 0, 1, null, false]

Object format (new):
{
  "idx": 1,
  "type": 1,
  "coords": [x1, y1, x2, y2],
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": null,
  "feature_method": "opencv",
  "rotation": 0,
  "device_location": 1,
  "expected_text": null,
  "is_device_barcode": false
}
"""

import os
import json
import glob
import shutil
from datetime import datetime


def array_to_object(roi_array):
    """Convert ROI array to object format."""
    # Handle different array lengths (legacy formats)
    roi_obj = {}
    
    if len(roi_array) >= 1:
        roi_obj['idx'] = roi_array[0]
    if len(roi_array) >= 2:
        roi_obj['type'] = roi_array[1]
    if len(roi_array) >= 3:
        roi_obj['coords'] = roi_array[2]
    if len(roi_array) >= 4:
        roi_obj['focus'] = roi_array[3]
    if len(roi_array) >= 5:
        roi_obj['exposure'] = roi_array[4]
    if len(roi_array) >= 6:
        roi_obj['ai_threshold'] = roi_array[5]
    if len(roi_array) >= 7:
        roi_obj['feature_method'] = roi_array[6]
    if len(roi_array) >= 8:
        roi_obj['rotation'] = roi_array[7]
    if len(roi_array) >= 9:
        roi_obj['device_location'] = roi_array[8]
    if len(roi_array) >= 10:
        roi_obj['expected_text'] = roi_array[9]
    if len(roi_array) >= 11:
        roi_obj['is_device_barcode'] = roi_array[10]
    
    # Fill in defaults for missing fields
    roi_obj.setdefault('focus', 305)
    roi_obj.setdefault('exposure', 1200)
    roi_obj.setdefault('ai_threshold', None)
    roi_obj.setdefault('feature_method', 'opencv')
    roi_obj.setdefault('rotation', 0)
    roi_obj.setdefault('device_location', 1)
    roi_obj.setdefault('expected_text', None)
    roi_obj.setdefault('is_device_barcode', None)
    
    return roi_obj


def migrate_config_file(file_path, dry_run=True):
    """Migrate a single ROI config file."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check if already in object format
        if data and isinstance(data[0], dict):
            print(f"  ✓ Already in object format (idx: {data[0].get('idx', 'N/A')})")
            return True
        
        # Convert arrays to objects
        converted = []
        for roi in data:
            if isinstance(roi, list):
                converted.append(array_to_object(roi))
            else:
                converted.append(roi)  # Already object format
        
        print(f"  → Converted {len(converted)} ROIs from array to object format")
        
        if not dry_run:
            # Backup original file
            backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            print(f"  → Backup created: {backup_path}")
            
            # Write converted data
            with open(file_path, 'w') as f:
                json.dump(converted, f, indent=2)
            print(f"  ✓ File updated successfully")
        else:
            print(f"  → Would create backup and update file")
            # Show first ROI as example
            if converted:
                print(f"  → Example (first ROI):")
                print(f"     {json.dumps(converted[0], indent=6)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate ROI configurations from array to object format')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without modifying files (default: True)')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes (disables dry-run)')
    parser.add_argument('--product', type=str,
                       help='Migrate specific product only (e.g., 20003548)')
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_dir = os.path.join(project_root, 'config', 'products')
    
    print("=" * 70)
    print("ROI Configuration Migration Tool")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'APPLY CHANGES'}")
    print(f"Config directory: {config_dir}")
    
    # Find all ROI config files
    if args.product:
        pattern = os.path.join(config_dir, args.product, f'rois_config_{args.product}.json')
        config_files = glob.glob(pattern)
    else:
        pattern = os.path.join(config_dir, '*', 'rois_config_*.json')
        config_files = glob.glob(pattern)
    
    print(f"Found {len(config_files)} config file(s)")
    
    if not config_files:
        print("\n✗ No config files found!")
        return
    
    # Migrate each file
    success_count = 0
    fail_count = 0
    
    for config_file in sorted(config_files):
        if migrate_config_file(config_file, dry_run):
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"Total files: {len(config_files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files were modified")
        print("To apply changes, run with --apply flag:")
        print(f"  python3 {os.path.basename(__file__)} --apply")
    else:
        print("\n✓ Migration complete!")
        print("Backup files created with .backup_TIMESTAMP extension")


if __name__ == '__main__':
    main()
