# 📐 Camera Calibration Guide - Smart Parking Assist

## Introduction

Camera calibration is the **most critical step** for accurate distance estimation. This guide provides step-by-step instructions for calibrating your camera for the Smart Parking Assist system.

---

## 🎯 What is Calibration?

### Why Calibration Matters

The distance estimation formula is:
```
Distance = (Known Object Width × Focal Length) / Perceived Width
```

**The focal length is specific to each camera.** Without calibration:
- Distance estimates will be wildly inaccurate
- System is essentially useless for real applications

### What Gets Calibrated

We're finding the **focal length (F)** in pixels, which depends on:
1. Camera lens specifications
2. Camera sensor size
3. Image resolution
4. Lens distortion

### Expected Accuracy After Calibration
- **Close range (0-3m)**: ±10-15% error
- **Medium range (3-10m)**: ±15-25% error
- **Far range (>10m)**: ±20-30% error

**Note:** Monocular (single camera) vision has inherent limitations. These accuracy levels are realistic and industry-standard.

---

## 🧮 Quick Method 1: Formula-Based Calibration

### For the Impatient ⏱️

If you just want to get started quickly:

**Typical focal length values:**
- **Smartphone camera**: 600-1000 pixels
- **-Standard USB webcam**: 500-900 pixels
- **High-end camera**: 1000-2000 pixels

**Use 800 pixels as starting point** and test for accuracy.

### Using Camera Specifications

**Step 1: Find Camera Specs**
```
Search for: "[Your Camera Model] specifications"
Look for:
- Lens focal length (mm) - e.g., 4mm
- Sensor size (mm) - e.g., 1/2.5"
- Resolution (pixels) - e.g., 1280x720
```

**Step 2: Convert Sensor Size**
```
Common sensor sizes:
1/4"   ≈ 3.2mm width
1/3.2" ≈ 4.0mm width
1/2.7" ≈ 4.7mm width
1/2.3" ≈ 5.8mm width
1/2"   ≈ 6.4mm width

Or search: "1/2.3 inch sensor width mm"
```

**Step 3: Calculate Focal Length**
```python
F = (f × W) / s

where:
  f = Lens focal length (mm) = 4mm
  W = Image width (pixels) = 1280
  s = Sensor width (mm) = 5.8mm

F = (4 × 1280) / 5.8
F = 5120 / 5.8
F ≈ 883 pixels
```

**Step 4: Update Configuration**
```python
# In parking.py
class ParkingConfig:
    FOCAL_LENGTH = 883  # Your calculated value
```

**Step 5: Test with known object**
```python
# Send a car at exactly 5 meters
# If system says 5m ± 0.5m, calibration is good
# If way off, try Method 2 (reference object)
```

---

## ✅ Method 2: Reference Object Calibration (Recommended)

### Why This Method?

✅ More accurate than formula-based  
✅ Accounts for lens distortion  
✅ Works for any camera  
✅ Interactive and intuitive  

### Prerequisites

**Equipment needed:**
- 📏 Measuring tape (at least 10 meters)
- 🚗 Reference object with known width:
  - **Car door**: ~80cm
  - **Person**: Shoulder width ~45cm
  - **Open door frame**: ~90cm
  - **Full car**: ~1.8m
- ☀️ Good lighting
- 📍 Clear, flat space (parking lot, empty road)
- 🖥️ Computer with camera

### Step-by-Step Procedure

#### **Setup Phase (5 minutes)**

1. **Choose Reference Object**
   ```
   Best choice: Person (45cm shoulder width)
   - Easy to measure
   - Available anywhere
   - Distinct boundaries for detection
   ```

2. **Mark Distance Points**
   ```
   In an empty lot or hallway:
   - Mark position 0m (camera position)
   - Mark position 3m (measuring from camera lens center)
   - Mark position 5m (ideal calibration distance)
   - Mark position 10m (optional, for verification)
   ```

3. **Mount Camera Stably**
   ```
   - Use tripod or fixed mount
   - Position at normal parking height (~0.5-1m above ground)
   - Don't move camera during calibration
   - Keep this position for actual use
   ```

4. **Ensure Good Lighting**
   ```
   - Natural daylight is best
   - Avoid harsh shadows
   - No glare on camera lens
   - Consistent lighting environment
   ```

#### **Interactive Calibration Phase (5-10 minutes)**

1. **Start Calibration Tool**
   ```bash
   python parking.py
   # Select option: "2. Calibrate with known object (Interactive)"
   ```

2. **Enter Object Dimensions**
   ```
   System asks: "Enter known object width in meters"
   # If using person: 0.45
   # If using door: 0.90
   # If using car: 1.8
   ```

3. **Enter Distance**
   ```
   System asks: "Enter object distance in meters"
   # Use: 5.0 (5 meters is ideal)
   # Measured from camera lens to object center
   ```

4. **Position Reference Object**
   ```
   - Stand/place object at marked 5m line
   - Keep perpendicular to camera (facing directly at it)
   - Wait for "CALIBRATION MODE" display
   - Keep position stable
   ```

5. **Capture Measurements**
   ```
   Calibration window shows:
   - Crosshair or detection indicator
   - Instructions: "Press 'c' to capture"
   
   When ready:
   - Press 'c'
   - System detects object
   - Measures bounding box width
   - Calculates focal length
   ```

6. **Review Calculation**
   ```
   System displays:
   "✓ Captured bounding box width: 150.45 pixels
    ✓ Calculated Focal Length: 600.23 pixels
    ✓ Use this value in ParkingConfig.FOCAL_LENGTH"
   ```

#### **Verification Phase (5-10 minutes)**

1. **Test at Multiple Distances**
   ```
   After initial calibration, test at:
   - 2 meters: Should read 2m ± 0.3m
   - 3 meters: Should read 3m ± 0.5m
   - 5 meters: Should read 5m ± 0.5m (calibration point)
   - 8 meters: Should read 8m ± 1.5m
   ```

2. **Measure Accuracy**
   ```
   For each test:
   1. Place object at exact distance
   2. Note system reading
   3. Calculate error: abs(actual - system) / actual × 100%
   
   Acceptable errors:
   - < 10% = Excellent calibration ✓
   - < 15% = Good calibration ✓
   - < 25% = Acceptable ✓
   - > 25% = Recalibrate with better setup
   ```

3. **Recalibrate if Needed**
   ```
   If error > 20%:
   1. Check reference object width is correct
   2. Verify camera hasn't moved
   3. Try different reference object
   4. Try different distance (3m or 8m)
   5. Ensure object is perpendicular to camera
   ```

4. **Final Validation**
   ```
   Once happy with accuracy:
   - Note the focal length value
   - Update ParkingConfig.FOCAL_LENGTH
   - Document calibration date and camera model
   - Don't move camera from this position
   ```

### Example Calibration Session

```
=== Calibration Session Log ===

Equipment:
- Camera: Built-in laptop webcam
- Reference Object: Person (person A)
- Shoulder Width: 45cm (0.45m) [measured with tape]
- Distance: 5 meters [measured with measuring tape]

System Output:
"Captured bounding box width: 135.2 pixels"
"Calculated Focal Length: 675.5 pixels"

Formula verification:
  Focal Length = (Width × Distance) / Perceived Width
  = (0.45m × 5m) / (Detected width in image)
  = 675.5 pixels ✓

Verification Tests:
  Distance 2m:  System says 2.1m  (Error: 5%)    ✓ Excellent
  Distance 3m:  System says 3.3m  (Error: 10%)   ✓ Good
  Distance 5m:  System says 4.9m  (Error: 2%)    ✓ Excellent
  Distance 8m:  System says 8.4m  (Error: 5%)    ✓ Excellent

Conclusion: Calibration successful!
FOCAL_LENGTH = 675.5 (rounded)
```

---

## 🎓 Method 3: Chessboard Calibration (Most Accurate)

### When to Use

- ✅ When highest accuracy needed
- ✅ When focal length calculation failed
- ✅ For final production systems
- ❌ Not necessary for parking assist (overkill)

### Brief Overview

```python
import cv2
import numpy as np

# Print chessboard pattern (8x6 or 9x7 squares)
# Take 20-30 photos of chessboard at different angles
# Run OpenCV calibration
# Get camera matrix, distortion coefficients
```

### Implementation

[Too complex for this guide. See:](https://docs.opencv.org/4.x/dc/dbb/tutorial_calibration.html)

---

## 🔧 Troubleshooting Calibration

### Problem 1: "Focal length seems wrong - distance estimates way off"

**Symptoms:**
- Says 2m when object is 5m away
- Says 10m when object is nearby
- Consistent scale error

**Solutions:**
```
1. Verify reference object width:
   - Person shoulder width: Measure with tape (usually 42-50cm)
   - Car width: Look up model (usually 1.7-1.9m)
   - Door width: Standard is 90cm
   
2. Verify distance measurement:
   - Measure from camera lens center to object center
   - Not from ground to object
   - Use measuring tape, not visual estimation
   - Double-check with phone measurement app
   
3. Test calibration:
   - Place object at EXACT calibration distance
   - System should read very close to that distance
   - If not, recalibrate
   
4. Try different reference:
   - Maybe person detection is poor
   - Try car or door frame instead
   - YOLO must detect it clearly
```

### Problem 2: "Detection not working - can't calibrate"

**Symptoms:**
- "No detection found" message
- Calibration window shows nothing
- Bounding box width = 0

**Solutions:**
```
1. Improve lighting:
   - Move to brighter area
   - Avoid shadows and glare
   - Use daylight, not artificial light
   
2. Move closer:
   - YOLO needs clear, large detection
   - Move reference object closer if far
   - Minimum 1 meter distance recommended
   
3. Lower confidence threshold:
   - Edit: CONFIDENCE_THRESHOLD = 0.4  (instead of 0.5)
   - More detections but some false positives
   
4. Check camera focus:
   - Ensure camera is in focus
   - Clean lens with soft cloth
   - Try auto-focus or manual focus
```

### Problem 3: "Focal length calculated but tests show large errors"

**Symptoms:**
- Calibration says 800px focal length
- But testing shows 50% errors
- Consistent offset in all tests

**Solutions:**
```
1. Camera might have moved:
   - Check camera hasn't tilted/moved since calibration
   - Recalibrate with camera in exact same position
   
2. Reference object might be wrong:
   - If using person, shoulder width varies (40-55cm)
   - Measure actual width with tape measure
   - Write down exact width used
   
3. Object might be tilted:
   - Person must face camera directly
   - Not at angle
   - Not leaning
   
4. Lens might have auto-focus:
   - Focus distance changes focal length
   - Set camera to manual focus
   - Focus on object distance (e.g., 5m)
   - Lock focus during calibration
   
5. Try different distance:
   - Calibrate at 3m instead of 5m
   - Sometimes better results at different distances
```

### Problem 4: "Consistent sign error - always overestimates/underestimates"

**Symptoms:**
- Always reads double the distance
- Always reads half the distance
- Consistent ratio error

**Solutions:**
```
1. Check formula is correct:
   Distance = (Object_Width × Focal_Length) / Perceived_Width
   
2. Verify object width units:
   - Must be in METERS
   - 45cm = 0.45m, not 45m
   - 1.8m = 1.8, not 180
   
3. Check YOLO bounding box:
   - Verify bounding box includes entire object
   - Not too tight (cutting off edges)
   - Not too loose (including background)
   
4. Recalculate with known values:
   - If person is 0.45m wide
   - Bounding box is 180 pixels
   - Distance is 5m
   - Then: F = (0.45 × 5) / 180 = 0.0125 × 180 = 2.25?
   - Should be: F = (345) / (180 pixels) ≈ 675 pixels
```

---

## 📋 Calibration Checklist

Before you start:
- [ ] Have measuring tape ready
- [ ] Know reference object width
- [ ] Clear space (10×10 meters min)
- [ ] Good lighting conditions
- [ ] Camera mounted stably
- [ ] Python and dependencies installed
- [ ] No other applications using camera

During calibration:
- [ ] Reference object is perpendicular to camera
- [ ] Distance measured from lens center
- [ ] Object detected clearly (YOLO sees it)
- [ ] Multiple test distances validated
- [ ] Errors less than 20% on average
- [ ] Focal length value documented

After calibration:
- [ ] Updated ParkingConfig.FOCAL_LENGTH
- [ ] Noted calibration date
- [ ] Recorded camera model/specs
- [ ] Disabled auto-focus (if possible)
- [ ] Camera position marked/fixed
- [ ] Tested on sample video (if available)

---

## 📊 Calibration Results Log

Use this template to record your calibration:

```
═══════════════════════════════════════════════
        CAMERA CALIBRATION REPORT
═══════════════════════════════════════════════

Date: ______________
Camera Model: ______________
Resolution: ________ × ________
Lens Focal Length (mm): ______________
Sensor Size: ______________

CALIBRATION METHOD: [ ] Formula [ ] Reference Object [ ] Chessboard

REFERENCE OBJECT CALIBRATION:
  Object Type: ______________
  Object Width (meters): ______________
  Actual Distance (meters): ______________
  Detected Bounding Box Width (pixels): ______________
  Calculated Focal Length (pixels): ______________

VERIFICATION TESTS:
  Distance: 2m    System Reading: ____m   Error: ____%  [ ]
  Distance: 3m    System Reading: ____m   Error: ____%  [ ]
  Distance: 5m    System Reading: ____m   Error: ____%  [ ]
  Distance: 8m    System Reading: ____m   Error: ____%  [ ]

Average Error: ____%
Status: [ ] ✓ Good  [ ] ⚠️ Acceptable  [ ] ❌ Needs Redo

FINAL FOCAL LENGTH VALUE: _____________ pixels

To use: Update ParkingConfig.FOCAL_LENGTH = _______

Notes: ________________________________________________
       ________________________________________________

═══════════════════════════════════════════════
```

---

## 🚀 Next Steps After Calibration

1. **Update Code**
   ```python
   # parking.py
   class ParkingConfig:
       FOCAL_LENGTH = YOUR_CALIBRATED_VALUE
   ```

2. **Test System**
   ```bash
   python parking.py
   # Skip calibration on startup
   # Test with real objects at known distances
   ```

3. **Monitor and Refine**
   ```
   - First week: Observe distance readings
   - If consistently off: Fine-tune focal length
   - Every 3 months: Re-calibrate (camera may drift)
   ```

4. **Document Setup**
   ```
   Save:
   - Camera position (photo, coordinates)
   - Calibration date and values
   - Reference object dimensions
   - Environmental conditions
   - For future reference/troubleshooting
   ```

---

## 🎓 Learning More

### Recommended Reading
- Pinhole Camera Model: Wikipedia
- Camera Calibration: OpenCV docs
- Focal Length: Physics textbooks

### Related Concepts
- Lens distortion
- Intrinsic camera parameters
- Extrinsic camera parameters
- Pose estimation

### Advanced Techniques
- Stereo calibration (2 cameras)
- Fisheye camera calibration
- Radial distortion correction

---

## 📞 FAQ

**Q: Do I really need to calibrate?**
A: Yes. Without calibration, distance estimates will be inaccurate by 50-200%.

**Q: How long does calibration take?**
A: 15-30 minutes first time, 5 minutes for verification.

**Q: Can I calibrate at different distance?**
A: Yes. Works at any distance, but 3-5 meters is simplest.

**Q: Will calibration stay valid over time?**
A: Yes, until camera is moved or lens is changed. Recalibrate if results drift.

**Q: Can I use any object for calibration?**
A: Any object with known width. Rigid objects (doors) > soft objects (fabrics).

**Q: What if I don't know object dimensions?**
A: Measure with measuring tape first. Critical for accuracy.

**Q: Can one calibration work for multiple cameras?**
A: No. Each camera needs its own calibration. Different specs = different focal length.

**Q: Is ±20% error acceptable?**
A: Yes, for parking assistance. Good enough to prevent collisions.

**Q: What if my camera has auto-focus?**
A: Disable it if possible. Or always focus at object distance.

---

## 🏁 Conclusion

Proper calibration is the foundation of accurate distance estimation. Spend 30 minutes here, save months of debugging later.

Once calibrated, your Smart Parking Assist system will provide reliable distance measurements for safe parking operations.

**Good luck! 🚗**

---

Last Updated: February 27, 2026  
Version: 1.0
