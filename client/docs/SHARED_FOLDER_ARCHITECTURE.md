# Shared Folder Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VISUAL AOI SYSTEM                                │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐                            ┌──────────────────────┐
│   CLIENT MACHINE     │                            │   SERVER MACHINE     │
│  (This Application)  │                            │  (10.100.27.156)     │
│                      │                            │                      │
│  ┌────────────────┐  │                            │  ┌────────────────┐  │
│  │ client_app_    │  │     HTTP API (JSON)       │  │  Server API    │  │
│  │ simple.py      │  │◄──────────────────────────┤  │  Flask/FastAPI │  │
│  │                │  │                            │  │                │  │
│  │ - GUI          │  │   POST /api/session/create │  │ - AI Models    │  │
│  │ - Camera Ctrl  │  ├───────────────────────────►│  │ - Barcode Det. │  │
│  │ - Workflows    │  │                            │  │ - OCR          │  │
│  │ - Results      │  │   POST /process_inspection │  │ - Comparison   │  │
│  └───────┬────────┘  │◄──────────────────────────┤  └───────┬────────┘  │
│          │           │                            │          │           │
│          │ uses      │                            │          │ uses      │
│          ▼           │                            │          ▼           │
│  ┌────────────────┐  │                            │  ┌────────────────┐  │
│  │ SharedFolder   │  │                            │  │ Processing     │  │
│  │ Manager        │  │                            │  │ Engine         │  │
│  │                │  │                            │  │                │  │
│  │ - save_image() │  │                            │  │ - process_roi()│  │
│  │ - get_path()   │  │                            │  │ - compare()    │  │
│  │ - cleanup()    │  │                            │  │ - detect()     │  │
│  └───────┬────────┘  │                            │  └───────┬────────┘  │
│          │           │                            │          │           │
└──────────┼───────────┘                            └──────────┼───────────┘
           │                                                   │
           │ reads/writes                                      │ reads/writes
           │                                                   │
           ▼                                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHARED FOLDER (File System)                           │
│              /mnt/visual-aoi-shared/                       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ sessions/                                                        │    │
│  │   └── {session_id}/                                             │    │
│  │       ├── input/     ◄─── Client writes captured images         │    │
│  │       │   ├── capture_F325_E1500.jpg                            │    │
│  │       │   ├── capture_F350_E2000.jpg                            │    │
│  │       │   └── metadata.json                                     │    │
│  │       │                                                          │    │
│  │       └── output/    ◄─── Server writes results                 │    │
│  │           ├── roi_1_captured.jpg                                │    │
│  │           ├── roi_1_golden.jpg                                  │    │
│  │           ├── roi_2_captured.jpg                                │    │
│  │           ├── results.json                                      │    │
│  │           └── ...                                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ golden_samples/                                                  │    │
│  │   └── {product_name}/                                           │    │
│  │       ├── roi_1_sample_1.jpg                                    │    │
│  │       ├── roi_1_sample_2.jpg                                    │    │
│  │       ├── roi_2_sample_1.jpg                                    │    │
│  │       └── ...                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ temp/                                                            │    │
│  │   └── client_{timestamp}/                                       │    │
│  │       └── temporary files (auto-cleanup after 24h)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

```
1. SESSION CREATION
   ┌─────────┐                           ┌─────────┐
   │ CLIENT  │   POST /api/session/create │ SERVER  │
   │         ├──────────────────────────►│         │
   │         │   {product_name: "xxx"}   │         │
   │         │◄──────────────────────────┤         │
   │         │   {session_id: "yyy"}     │         │
   └────┬────┘                           └─────────┘
        │
        │ SharedFolderManager.create_session_directories()
        ▼
   [Create input/ and output/ directories]


2. IMAGE CAPTURE
   ┌─────────┐                           ┌─────────┐
   │ CLIENT  │                           │ CAMERA  │
   │         │   Capture with F/E        │         │
   │         ├──────────────────────────►│         │
   │         │◄──────────────────────────┤         │
   │         │   Raw image data          │         │
   └────┬────┘                           └─────────┘
        │
        │ SharedFolderManager.save_captured_image()
        ▼
   [Save to sessions/{id}/input/capture_F{f}_E{e}.jpg]


3. INSPECTION PROCESSING
   ┌─────────┐                           ┌─────────┐
   │ CLIENT  │   POST /process_inspection │ SERVER  │
   │         ├──────────────────────────►│         │
   │         │   {session_id: "xxx",     │         │
   │         │    captured_images: [...]}│         │
   │         │                           │         │
   │         │                           └────┬────┘
   │         │                                │
   │         │                                │ Read from input/
   │         │                                │ Process ROIs
   │         │                                │ Save to output/
   │         │                                │
   │         │                           ┌────▼────┐
   │         │◄──────────────────────────┤         │
   │         │   {results: {...}}        │         │
   └────┬────┘                           └─────────┘
        │
        │ SharedFolderManager.read_results_json()
        │ SharedFolderManager.get_roi_image_path()
        ▼
   [Display results with images from output/]


4. GOLDEN SAMPLE MANAGEMENT
   ┌─────────┐                           ┌─────────┐
   │ CLIENT  │   POST /api/golden-sample │ SERVER  │
   │         ├──────────────────────────►│         │
   │         │   {product, roi_id, file} │         │
   │         │                           └────┬────┘
   │         │                                │
   │         │                                │ Save to golden_samples/
   │         │                           ┌────▼────┐
   │         │◄──────────────────────────┤         │
   │         │   {success: true}         │         │
   └─────────┘                           └─────────┘


5. SESSION CLEANUP
   ┌─────────┐
   │ CLIENT  │
   │         │   SharedFolderManager.cleanup_session()
   └────┬────┘
        │
        ▼
   [Delete sessions/{id}/input/  (keep output/ for history)]
```

## SharedFolderManager Class Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   SharedFolderManager                          │
├────────────────────────────────────────────────────────────────┤
│ Attributes:                                                    │
│   - base_path: Path                                           │
│   - sessions_path: Path                                       │
│   - golden_samples_path: Path                                 │
│   - temp_path: Path                                          │
├────────────────────────────────────────────────────────────────┤
│ Methods:                                                       │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Connection                                           │     │
│ │  + check_server_connection() -> bool                │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Directory Management                                 │     │
│ │  + get_session_directory(session_id) -> Path        │     │
│ │  + get_session_input_directory(session_id) -> Path  │     │
│ │  + get_session_output_directory(session_id) -> Path │     │
│ │  + create_session_directories(session_id)           │     │
│ │    -> Tuple[Path, Path]                             │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Image Operations                                     │     │
│ │  + save_captured_image(session_id, data, filename,  │     │
│ │    metadata) -> Path                                │     │
│ │  + read_roi_image(session_id, filename) -> bytes    │     │
│ │  + get_roi_image_path(session_id, filename) -> Path │     │
│ │  + read_golden_image(session_id, filename) -> bytes │     │
│ │  + get_golden_image_path(session_id, filename)      │     │
│ │    -> Path                                           │     │
│ │  + list_session_images(session_id, directory)       │     │
│ │    -> List[str]                                      │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Results Management                                   │     │
│ │  + read_results_json(session_id, filename) -> Dict  │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Golden Samples                                       │     │
│ │  + get_golden_samples_directory(product_name)       │     │
│ │    -> Path                                           │     │
│ │  + list_golden_samples(product_name, roi_id)        │     │
│ │    -> List[str]                                      │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                               │
│ ┌─────────────────────────────────────────────────────┐     │
│ │ Maintenance                                          │     │
│ │  + cleanup_session(session_id, keep_output) -> bool │     │
│ │  + create_temp_directory(prefix) -> Path            │     │
│ │  + cleanup_temp_directories(max_age_hours) -> int   │     │
│ │  + get_disk_usage() -> Dict[str, int]               │     │
│ └─────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────┘
```

## Usage Patterns

### Pattern 1: Inspection Session Lifecycle

```
START
  │
  ├─► create_session_directories()
  │
  ├─► (loop) save_captured_image()  [for each ROI group]
  │
  ├─► [Server processes images]
  │
  ├─► read_results_json()
  │
  ├─► (loop) get_roi_image_path()  [for each ROI result]
  │
  └─► cleanup_session(keep_output=True)
END
```

### Pattern 2: Golden Sample Management

```
START
  │
  ├─► list_golden_samples(product_name)
  │
  ├─► (for each sample)
  │   └─► get_golden_samples_directory() + filename
  │       └─► Display/Process sample
  │
  └─► [User can add new samples via server API]
END
```

### Pattern 3: Maintenance Routine

```
START (Daily/Weekly)
  │
  ├─► cleanup_temp_directories(max_age_hours=24)
  │
  ├─► get_disk_usage()
  │   └─► Check if usage > threshold
  │       └─► Alert or cleanup old sessions
  │
  └─► Log statistics
END
```

## Error Handling Flow

```
┌─────────────────┐
│ Client calls    │
│ SFM method      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Path exists?    ├─NO──►│ Log warning  │
└────────┬────────┘      │ Return None  │
         │ YES           └──────────────┘
         ▼
┌─────────────────┐      ┌──────────────┐
│ Readable?       ├─NO──►│ Log error    │
└────────┬────────┘      │ Return None  │
         │ YES           └──────────────┘
         ▼
┌─────────────────┐      ┌──────────────┐
│ Perform         ├─ERR─►│ Log error    │
│ operation       │      │ Raise/Return │
└────────┬────────┘      └──────────────┘
         │ SUCCESS
         ▼
┌─────────────────┐
│ Log success     │
│ Return result   │
└─────────────────┘
```

## Directory Lifecycle

```
                        [Session Created]
                              │
                              ▼
                    ┌─────────────────┐
                    │ sessions/       │
                    │   {session_id}/ │
                    │     ├─ input/   │
                    │     └─ output/  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    [Client              [Server            [Client
     saves              processes           reads
     images]            images]             results]
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Inspection      │
                    │ Complete        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Options:        │
                    │ 1. Keep output  │
                    │    (history)    │
                    │ 2. Delete all   │
                    │    (cleanup)    │
                    └─────────────────┘
```

---

**Legend:**
- `┌─┐` Box/Container
- `│` Vertical connection
- `─` Horizontal connection
- `►` Arrow/Flow direction
- `◄` Bidirectional flow
- `▼` Downward flow
