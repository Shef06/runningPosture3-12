# Ghost Vision Feature - Implementation Summary

## Overview
The "Ghost Vision" feature has been successfully implemented to allow users to overlay a semi-transparent silhouette of the best baseline video onto their running video for immediate visual comparison of posture.

## Features Implemented

### 1. Backend Modifications (`backend/pose_engine.py`)

#### Segmentation Enabled
- Modified `PoseEngine.__init__()` to accept `enable_segmentation` parameter (default: `True`)
- Updated MediaPipe Pose initialization to enable segmentation mask extraction

#### Ghost Silhouette Extraction
- Added `_extract_ghost_silhouette()` method that:
  - Takes a video frame and its segmentation mask
  - Processes the mask to extract a clean body silhouette
  - Applies morphological operations to clean up the mask
  - Finds and draws the body contour
  - Creates an RGBA image with the silhouette in cyan/blue color on transparent background
  - Returns a semi-transparent overlay image

#### Ghost Frame Generation
- Added `generate_ghost_frames()` method that:
  - Processes a baseline video frame-by-frame
  - Extracts segmentation masks using MediaPipe
  - Generates ghost silhouette images for each frame
  - Saves frames as PNG files (with transparency support) in the ghost_frames folder
  - Returns metadata about generated frames

### 2. Backend API Endpoints (`backend/app.py`)

#### Ghost Frame Serving
- **`GET /api/ghost_frame/<filename>`**: Serves individual ghost frame images (PNG with transparency)
- **`GET /api/ghost_frame_by_number/<frame_number>`**: Returns ghost frame URL for a specific frame number (used for synchronization)

#### Baseline Creation Enhancement
- Modified `/api/create_baseline` endpoint to:
  - Identify the "best" baseline video (one with minimum deviation from mean)
  - Generate ghost frames from the best baseline video after processing all 5 videos
  - Store ghost frame metadata in the baseline JSON
  - Return `ghost_vision_available` flag and frame count to frontend

#### Configuration
- Added `GHOST_FRAMES_FOLDER` to `backend/config.py`
- Folder is automatically created during app initialization

### 3. Frontend Components

#### Store Enhancement (`frontend/src/lib/stores/analysisStore.js`)
- Added `ghostVisionEnabled` state variable
- Added `setGhostVision(enabled)` method to toggle Ghost Vision

#### Results Step UI (`frontend/src/lib/components/steps/ResultsStep.svelte`)
- Added Ghost Vision toggle section that appears when ghost frames are available
- Includes:
  - Toggle switch for enabling/disabling Ghost Vision
  - Visual indicator when overlay is active
  - Descriptive text explaining the feature
- Toggle communicates state changes to the store

#### Ghost Vision Overlay Component (`frontend/src/lib/components/GhostVisionOverlay.svelte`)
- New standalone component for rendering ghost overlay
- Features:
  - Synchronizes with video playback
  - Calculates current frame number based on video time
  - Fetches appropriate ghost frame from backend API
  - Renders ghost silhouette with 50% opacity
  - Automatically scales to match video dimensions
  - Handles video play/pause/seek events
  - Clears overlay when disabled or video paused

#### Video Holder Integration (`frontend/src/lib/components/VideoHolder.svelte`)
- Integrated GhostVisionOverlay component into skeleton video display
- Added reference binding to skeleton video element
- Conditionally renders overlay when Ghost Vision is enabled

### 4. Styling

#### Toggle Switch
- Modern iOS-style toggle switch with smooth animations
- Color changes: gray (off) → cyan (on)
- Hover effects for better UX

#### Ghost Overlay
- Semi-transparent cyan/blue silhouette
- Smooth fade-in/fade-out transitions
- Positioned exactly over video content
- Non-interactive (pointer-events: none)

## Technical Details

### Frame Synchronization
- Ghost frames are named sequentially: `ghost_frame_XXXXXX.png` (6-digit frame number)
- Frontend calculates frame number: `frameNumber = floor(videoTime * fps)`
- Default FPS is 30 (should match baseline video FPS)
- Frames are cached in memory to reduce API calls
- Missing frames (no pose detected) result in no overlay (graceful degradation)

### Image Processing
- Segmentation masks are binarized (threshold at 127)
- Morphological operations clean up noise
- Contour detection finds the largest body contour
- RGBA images support transparency
- PNG format preserves alpha channel

### Performance Considerations
- Ghost frames are generated once during baseline creation
- Frames are cached on backend (static files)
- Frontend caches loaded images to avoid reloading
- Only fetches new frames when frame number changes
- Lightweight PNG files (transparency only where needed)

## User Workflow

1. **Create Baseline**: User uploads 5 baseline videos
   - Backend processes all videos
   - Identifies best video (minimum deviation)
   - Generates ghost frames from best video
   - Stores ghost frames in `backend/ghost_frames/`

2. **Analyze User Video**: User uploads their running video
   - Backend analyzes and returns results with skeleton video
   - Frontend displays results with skeleton video

3. **Enable Ghost Vision**: In ResultsStep, user toggles Ghost Vision
   - Toggle appears only if ghost frames are available
   - When enabled, ghost silhouette overlays video
   - Silhouette moves in sync with video playback

4. **Visual Comparison**: User watches video with overlay
   - Semi-transparent cyan silhouette shows "perfect" baseline posture
   - User's actual video plays underneath
   - Visual differences immediately apparent (e.g., trunk lean, arm position)

## File Structure

```
backend/
├── pose_engine.py          # Modified: segmentation + ghost frame generation
├── app.py                  # Modified: ghost frame endpoints + baseline enhancement
├── config.py               # Modified: added GHOST_FRAMES_FOLDER
└── ghost_frames/           # New: stores generated ghost frame PNGs

frontend/src/lib/
├── components/
│   ├── GhostVisionOverlay.svelte   # New: ghost overlay component
│   ├── VideoHolder.svelte          # Modified: integrated ghost overlay
│   └── steps/
│       └── ResultsStep.svelte      # Modified: added ghost vision toggle UI
└── stores/
    └── analysisStore.js            # Modified: added ghostVisionEnabled state
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ghost_frame/<filename>` | GET | Serve ghost frame image by filename |
| `/api/ghost_frame_by_number/<frame_number>` | GET | Get ghost frame URL for specific frame number |
| `/api/create_baseline` | POST | Enhanced to generate ghost frames |

## Color Scheme

- **Ghost Silhouette**: Cyan/Aqua (#00FFFF)
- **Toggle Active**: Cyan (#00FFFF)
- **Toggle Inactive**: Gray (rgba(255,255,255,0.2))
- **Opacity**: 50% (0.5) for ghost overlay

## Future Enhancements

Possible improvements for future versions:

1. **Adjustable Opacity**: Allow user to adjust ghost opacity (30%-70%)
2. **Color Options**: Multiple ghost colors (cyan, green, purple)
3. **Multiple Baselines**: Compare against different baseline profiles
4. **Gait Cycle Alignment**: Sync based on gait cycle phase rather than time
5. **Side-by-Side View**: Option to show baseline and user videos side-by-side
6. **Frame-by-Frame Comparison**: Pause and compare specific frames
7. **Heatmap Overlay**: Show deviation intensity as color heatmap

## Testing Checklist

- [x] Backend generates ghost frames during baseline creation
- [x] Ghost frames are saved as PNG with transparency
- [x] Best baseline video is correctly identified
- [x] API endpoints serve ghost frames correctly
- [x] Toggle UI appears in ResultsStep when ghost frames available
- [x] Toggle switches ghost overlay on/off
- [x] Ghost overlay synchronizes with video playback
- [x] Ghost overlay scales correctly with video dimensions
- [x] Ghost overlay pauses when video pauses
- [x] Ghost overlay seeks when video seeks
- [x] Ghost overlay has appropriate opacity (50%)
- [x] No console errors during ghost vision operation

## Known Limitations

1. Ghost frames are generated at 30 FPS (configurable in future)
2. Ghost frames use static color (cyan) - not customizable yet
3. Frame synchronization assumes constant FPS
4. Requires segmentation data (MediaPipe Pose with segmentation enabled)
5. Ghost frames stored locally (not suitable for cloud deployment without modification)

## Conclusion

The Ghost Vision feature successfully provides an intuitive visual comparison tool for runners to see how their posture deviates from optimal baseline form. The semi-transparent overlay allows simultaneous viewing of actual video and ideal silhouette, making postural differences immediately apparent.

