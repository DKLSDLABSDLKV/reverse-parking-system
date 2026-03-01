"""
Real-Time Smart Parking Assist System
======================================
A computer vision-based system for real-time object detection and distance estimation
for parking assistance using YOLOv8 and OpenCV.

Author: Anonymous (Final Year Engineering Project)
Date: February 2026
License: MIT

Features:
- Real-time video capture from camera
- YOLOv8 object detection
- Distance estimation using focal length and bounding box size
- Warning levels: SAFE (Green), CAUTION (Yellow), STOP (Red)
- Audio alerts when object is too close
- Calibration tools for accurate distance measurement
"""

import cv2
import numpy as np
from ultralytics import YOLO
import winsound
import threading
from collections import deque
from datetime import datetime


# =====================================================
# CONFIGURATION PARAMETERS
# =====================================================
class ParkingConfig:
    """Configuration class for parking assist system parameters."""
    
    # Camera parameters
    FOCAL_LENGTH = 800  # Calibration needed (pixels) - see calibration guide
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720
    FPS = 30
    
    # Object detection parameters
    YOLO_MODEL = 'yolov8m.pt'  # Medium model for balance between speed and accuracy
    CONFIDENCE_THRESHOLD = 0.5
    IOU_THRESHOLD = 0.45
    
    # Distance estimation
    # Known dimensions of common objects near parking spaces (in meters)
    KNOWN_OBJECT_WIDTHS = {
        'car': 1.8,      # Average car width
        'person': 0.45,  # Average shoulder width
        'truck': 2.5,    # Truck width
        'bicycle': 0.6,  # Bicycle width
    }
    
    # Distance thresholds (in meters)
    SAFE_DISTANCE = 3.0      # Distance >= 3m: SAFE (Green)
    CAUTION_DISTANCE = 1.5   # 1.5m <= Distance < 3m: CAUTION (Yellow)
    STOP_DISTANCE = 0.8      # Distance < 0.8m: STOP (Red)
    
    # Alert settings
    BEEP_FREQUENCY = 1000    # Hz
    BEEP_DURATION_SHORT = 100  # ms
    BEEP_DURATION_MEDIUM = 200  # ms
    BEEP_DURATION_LONG = 500   # ms
    
    # Smoothing for stable distance readings
    DISTANCE_BUFFER_SIZE = 15  # Number of frames to average
    
    # Display settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.7
    FONT_THICKNESS = 2
    LINE_THICKNESS = 2
    
    # Object classes to detect for parking
    TARGET_CLASSES = {'car', 'truck', 'bus', 'person', 'bicycle', 'motorcycle'}


# =====================================================
# CAMERA CALIBRATION TOOLS
# =====================================================
class CameraCalibrator:
    """
    Camera calibration class for calculating focal length.
    
    THEORY:
    -------
    The focal length (in pixels) is a critical parameter for accurate distance estimation.
    It depends on:
    1. Camera sensor size (mm)
    2. Lens focal length (mm)
    3. Image resolution (pixels)
    
    Formula: F = f × P / S
    where:
        F = Focal length in pixels
        f = Lens focal length in mm
        P = Image width in pixels
        S = Sensor width in mm
    
    CALIBRATION METHODS:
    1. Manual Calibration: Place object at known distance, measure bounding box
    2. Chessboard Calibration: Use OpenCV camera calibration with chessboard
    3. Formula-Based: Calculate from camera specs
    """
    
    def __init__(self, config: ParkingConfig):
        self.config = config
        self.calibration_data = {}
    
    def calibrate_with_known_object(self, object_width_m: float, 
                                   distance_m: float) -> float:
        """
        Calculate focal length using a reference object at known distance.
        
        PROCEDURE:
        1. Place a known object (e.g., car, person) at a measured distance
        2. Capture video and detect the object
        3. Measure the bounding box width in pixels
        4. Use this function to calculate focal length
        
        Formula: F = (Object_Width_Pixels × Distance) / Object_Width_Meters
        
        Args:
            object_width_m (float): Known width of object in meters
            distance_m (float): Known distance from camera in meters
        
        Returns:
            float: Calculated focal length in pixels
        """
        print(f"\n{'='*60}")
        print("CAMERA CALIBRATION - Manual Method")
        print(f"{'='*60}")
        print(f"Object Width: {object_width_m} m")
        print(f"Distance: {distance_m} m")
        print("\nInstructions:")
        print("1. Position the object at the specified distance")
        print("2. The system will detect and measure the bounding box")
        print("3. Capture the bounding box width to calibrate")
        print("\nPress 'c' to capture reference, 'q' to quit calibration")
        print(f"{'='*60}\n")
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        
        focal_length = None
        captured_width = None
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Display instructions
                cv2.putText(frame, "CALIBRATION MODE", (10, 30),
                           self.config.FONT, 1, (0, 255, 255), 2)
                cv2.putText(frame, f"Press 'c' to capture, 'q' to quit", (10, 70),
                           self.config.FONT, 0.6, (255, 255, 255), 1)
                
                if captured_width:
                    focal_length = (captured_width * distance_m) / object_width_m
                    cv2.putText(frame, f"Captured Width: {captured_width:.1f} px", 
                               (10, 110), self.config.FONT, 0.6, (0, 255, 0), 1)
                    cv2.putText(frame, f"Focal Length: {focal_length:.2f}", 
                               (10, 150), self.config.FONT, 0.6, (0, 255, 0), 1)
                
                cv2.imshow('Camera Calibration', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    captured_width = self._get_object_width_from_frame(frame)
                    if captured_width:
                        print(f"✓ Captured bounding box width: {captured_width:.2f} pixels")
                        focal_length = (captured_width * distance_m) / object_width_m
                        print(f"✓ Calculated Focal Length: {focal_length:.2f} pixels")
                        print(f"✓ Use this value in ParkingConfig.FOCAL_LENGTH")
                        break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return focal_length
    
    def _get_object_width_from_frame(self, frame) -> float:
        """
        Detect object in frame and return bounding box width.
        This shows how to use YOLO for measurements.
        """
        try:
            model = YOLO(self.config.YOLO_MODEL)
            results = model(frame, conf=self.config.CONFIDENCE_THRESHOLD, verbose=False)
            
            if results[0].boxes:
                # Get largest detection
                boxes = results[0].boxes
                largest_box = max(boxes, key=lambda x: (x.xyxy[0][2] - x.xyxy[0][0]))
                x1, y1, x2, y2 = largest_box.xyxy[0]
                width = float(x2 - x1)
                
                # Draw detection for reference
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), 
                             (0, 255, 0), 2)
                return width
        except Exception as e:
            print(f"Error in detection: {e}")
        
        return None
    
    @staticmethod
    def print_calibration_guide():
        """Print detailed calibration guide."""
        guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    CAMERA CALIBRATION GUIDE                               ║
╚════════════════════════════════════════════════════════════════════════════╝

WHY CALIBRATION IS IMPORTANT:
──────────────────────────────
The focal length is the most critical parameter for accurate distance estimation.
Different cameras have different focal lengths, even with the same resolution.

WHAT IS FOCAL LENGTH?
─────────────────────
Focal length (F) in pixels is:
  F = (f × W) / s
  
  where:
    f = Physical focal length of lens (mm)
    W = Image width in pixels
    s = Sensor width in mm)

Example: If your camera specs are:
  - Lens focal length: 4mm (typical smartphone)
  - Image width: 1280 pixels
  - Sensor width: 5mm (typical smartphone sensor)
  - F = (4 × 1280) / 5 = 1024 pixels

CALIBRATION METHODS:
────────────────────

Method 1: FORMULA-BASED (QUICKEST)
├─ Use camera specifications
├─ Search for your camera model specifications online
├─ Calculate F using the formula above
└─ Typically F = 600-1200 pixels for smartphones/webcams

Method 2: REFERENCE OBJECT (RECOMMENDED FOR ACCURACY)
├─ Requirements: 1 object with known width, 1 measuring tape
├─ Steps:
│  1. Place object (e.g., car, person, door) at known distance (e.g., 5m)
│  2. Run the calibration tool
│  3. Let system detect and measure bounding box width
│  4. System calculates focal length automatically
$ Calculate new focal length = (detected_width × distance) / known_width
└─ Recommended objects:
    - Person (shoulder width ≈ 45cm)
    - Car door (width ≈ 80cm)
    - Standard door frame (width ≈ 90cm)
    - Full car (width ≈ 1.8m)

Method 3: CHESSBOARD CALIBRATION (MOST ACCURATE)
├─ Print a standard chessboard pattern
├─ Use OpenCV's calibrationWithCalibrationBoard()
├─ Captures lens distortion too
└─ Complex but most accurate

STEP-BY-STEP CALIBRATION PROCEDURE:
──────────────────────────────────
1. Mount camera in parking position (won't move during operation)
2. Get a reference object with known dimensions
3. Place object at specific distances (1m, 2m, 3m, etc.)
4. Run calibration and record focal length
5. Test accuracy by checking estimated vs actual distances
6. Fine-tune if needed

DISTANCE ESTIMATION FORMULA:
───────────────────────────
Once calibrated with focal length F:

  Distance (meters) = (Known_Width_meters × Focal_Length_pixels) / Observed_Width_pixels

Example:
  - Car width = 1.8m (known)
  - Focal length = 800 pixels (calibrated)
  - Detected bounding box width = 180 pixels
  - Distance = (1.8 × 800) / 180 = 8 meters

ACCURACY CONSIDERATIONS:
────────────────────────
✓ Better accuracy factors:
  • Camera mounted at fixed position (no movement)
  • Camera not tilted/rotated during operation
  • Recent calibration (camera characteristics can change)
  • Using known object dimensions (reliable sources)
  • Averaging measurements over multiple frames
  • Using center of frame for measurements

✗ Lower accuracy factors:
  • Camera angle changes
  • Object at extreme angles (not perpendicular to camera)
  • Lens distortion at edges
  • Object deforming/tilting
  • Low resolution detections
  • Camera auto-focus changing
  • Poor lighting conditions

COMMON ISSUES & SOLUTIONS:
──────────────────────────
Issue: Distance estimates way off
  → Re-run calibration with better reference object
  → Check camera is in same position as before
  → Verify known object dimensions

Issue: Accuracy gets worse over time
  → Camera may have moved/tilted
  → Recalibrate with current setup
  → Check for auto-focus changes

Issue: Detections inconsistent
  → Improve lighting conditions
  → Increase confidence threshold
  → Use larger reference objects

RECOMMENDED CALIBRATION SETUP:
──────────────────────────────
Equipment needed:
  □ Measuring tape (5-10 meters)
  □ Reference object (car/person/door)
  □ Clear space for testing (10x10m minimum)
  □ Good lighting conditions
  □ Fixed camera mount

Calibration checklist:
  □ Camera mounted and won't move
  □ Camera focus is manual or pre-set
  □ Reference object is perpendicular to camera
  □ Distance measured to object center
  □ Multiple measurements taken (3-5 positions)
  □ Focal length value saved and documented
  □ Date and camera model recorded

TROUBLESHOOTING ACCURACY:
─────────────────────────
If estimates are consistently off:

1. Check calibration accuracy:
   - Remeasure reference object width
   - Verify camera lens specifications
   - Test at multiple distances

2. Environmental factors:
   - Ensure consistent lighting
   - Check for reflections/glare on lens
   - Ensure no obstacles in detection path

3. Object detection quality:
   - Lower confidence threshold if missing detections
   - Ensure target objects are clearly visible
   - Check YOLO model size (use larger model if needed)

4. Post-processing:
   - Increase distance buffer size for smoother readings
   - Implement outlier rejection
   - Use moving average filters
╠════════════════════════════════════════════════════════════════════════════╣
║ Remember: Accurate calibration = Accurate distance estimation             ║
╚════════════════════════════════════════════════════════════════════════════╝
        """
        print(guide)


# =====================================================
# DISTANCE ESTIMATION ENGINE
# =====================================================
class DistanceEstimator:
    """
    Core distance estimation engine using monocular vision.
    
    MONOCULAR DISTANCE ESTIMATION LIMITATIONS:
    ──────────────────────────────────────────
    What works:
    ✓ Relative distance changes (object getting closer/farther)
    ✓ General safety assessment
    ✓ Collision avoidance decisions
    ✓ Same object type at different distances
    
    What doesn't work:
    ✗ Absolute precise distances (±10-20% error is typical)
    ✗ Different object types without adjustment
    ✗ Tilted/angled objects
    ✗ Partially occluded objects
    ✗ Objects at extreme angles
    
    Why? Because a monocular camera (single lens) loses depth information
    that stereo cameras or 3D sensors (like LiDAR) have.
    
    Improvements for accuracy:
    1. Stereo cameras (2 cameras)
    2. Depth sensors (Intel RealSense, Kinect)
    3. 3D object detection (depth-aware YOLO variants)
    4. Object pose estimation
    """
    
    def __init__(self, config: ParkingConfig):
        self.config = config
        self.distance_history = deque(maxlen=config.DISTANCE_BUFFER_SIZE)
    
    def estimate_distance(self, bbox_width: float, object_class: str) -> float:
        """
        Estimate distance using pinhole camera model.
        
        Mathematical formula used:
        ──────────────────────────
        D = (W × F) / w
        
        where:
            D = Distance to object (meters) [OUTPUT]
            W = Known width of object (meters) [INPUT]
            F = Focal length (pixels) [CALIBRATION PARAM]
            w = Perceived width of object (pixels) [FROM BBOX]
        
        Physics behind the formula:
        ──────────────────────────
        Based on similar triangles principle:
        
                    Focal Plane
                         |
                    _____|_____
                   |     |     |
                   |  F  |     |
                   |_____|_____|
                         | Real Object
                         |
                    _____|_____
                   |     |     |
                   | ~ W |     | (actual size W)
                   |_____|_____|
                         |
                         D (distance)
        
        The ratio of sizes equals focal length ratio:
        w/F ≈ W/D  →  D = (W × F) / w
        
        Args:
            bbox_width (float): Bounding box width in pixels from YOLO
            object_class (str): YOLO detected class name
        
        Returns:
            float: Estimated distance in meters
        """
        if bbox_width <= 0:
            return float('inf')
        
        # Get known width for this object class, default to car if unknown
        known_width = self.config.KNOWN_OBJECT_WIDTHS.get(
            object_class, self.config.KNOWN_OBJECT_WIDTHS['car']
        )
        
        # Core distance calculation
        distance = (known_width * self.config.FOCAL_LENGTH) / (bbox_width + 1e-6)
        
        return distance
    
    def get_smoothed_distance(self, raw_distance: float) -> float:
        """
        Apply temporal smoothing to stabilize distance readings.
        
        Why smoothing is necessary:
        ────────────────────────────
        YOLO detections fluctuate frame-by-frame due to:
        • Detection boxes varying slightly
        • Object movement
        • Detection confidence changes
        • Perspective changes
        
        Smoothing reduces noise while keeping responsive readings.
        
        Method: Moving average over recent frames
        """
        self.distance_history.append(raw_distance)
        return np.mean(self.distance_history) if self.distance_history else raw_distance


# =====================================================
# WARNING LEVEL MANAGEMENT
# =====================================================
class WarningLevel:
    """Enum-like class for warning levels and their properties."""
    
    SAFE = {
        'level': 'SAFE',
        'color': (0, 255, 0),      # Green
        'beep': False,
        'description': 'Object far - Safe distance'
    }
    
    CAUTION = {
        'level': 'CAUTION',
        'color': (0, 165, 255),    # Orange/Yellow
        'beep': False,
        'description': 'Medium distance - Slow down'
    }
    
    STOP = {
        'level': 'STOP',
        'color': (0, 0, 255),      # Red
        'beep': True,
        'description': 'Very close - Immediate action needed'
    }
    
    @staticmethod
    def get_warning_level(distance: float, config: ParkingConfig) -> dict:
        """
        Determine warning level based on distance thresholds.
        
        Thresholds:
        ──────────
        SAFE:    distance >= 3.0m (200+ vehicle lengths away)
        CAUTION: 1.5m <= distance < 3.0m (safe to reverse slowly)
        STOP:    distance < 0.8m (collision imminent)
        
        Args:
            distance (float): Distance to object in meters
            config (ParkingConfig): Configuration with thresholds
        
        Returns:
            dict: Warning level information with color and properties
        """
        if distance >= config.SAFE_DISTANCE:
            return WarningLevel.SAFE
        elif distance >= config.CAUTION_DISTANCE:
            return WarningLevel.CAUTION
        else:
            return WarningLevel.STOP


# =====================================================
# AUDIO ALERT SYSTEM
# =====================================================
class AudioAlertSystem:
    """
    Audio alert system for proximity warnings.
    
    Uses Windows beep for simplicity. Can be extended to use custom sounds.
    Thread-based to avoid blocking video processing.
    """
    
    def __init__(self, config: ParkingConfig):
        self.config = config
        self.last_beep_time = 0
        self.beep_interval = 0
    
    def trigger_alert(self, warning_level: dict):
        """
        Trigger audio alert based on warning level.
        
        Pattern:
        ───────
        SAFE:   No beep
        CAUTION: Single beep every 1 second
        STOP:   Double beep every 0.3 seconds
        
        Args:
            warning_level (dict): Warning level information
        """
        if not warning_level['beep']:
            return
        
        current_time = datetime.now().timestamp()
        
        if warning_level['level'] == 'CAUTION':
            beep_interval = 1.0  # 1 second
            beep_count = 1
            duration = self.config.BEEP_DURATION_SHORT
        else:  # STOP
            beep_interval = 0.3  # 0.3 seconds
            beep_count = 2
            duration = self.config.BEEP_DURATION_MEDIUM
        
        if current_time - self.last_beep_time >= beep_interval:
            for _ in range(beep_count):
                # Run beep in thread to not block rendering
                threading.Thread(
                    target=self._beep,
                    args=(self.config.BEEP_FREQUENCY, duration),
                    daemon=True
                ).start()
            self.last_beep_time = current_time
    
    @staticmethod
    def _beep(frequency: int, duration: int):
        """Produce a system beep sound."""
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            print(f"Beep error (this is okay): {e}")


# =====================================================
# MAIN PARKING ASSIST SYSTEM
# =====================================================
class SmartParkingAssist:
    """
    Main Smart Parking Assist System integrating all components.
    
    Workflow:
    ────────
    1. Capture frame from camera
    2. Run YOLO detection
    3. For each detection:
       a. Extract bounding box
       b. Estimate distance
       c. Smooth distance reading
       d. Determine warning level
       e. Trigger audio if needed
    4. Overlay information on frame
    5. Display and save frame
    """
    
    def __init__(self, config: ParkingConfig = None):
        """Initialize parking assist system."""
        self.config = config or ParkingConfig()
        
        # Initialize components
        print("Initializing Smart Parking Assist System...")
        print(f"Loading YOLO model: {self.config.YOLO_MODEL}...")
        self.model = YOLO(self.config.YOLO_MODEL)
        
        self.distance_estimator = DistanceEstimator(self.config)
        self.audio_system = AudioAlertSystem(self.config)
        self.calibrator = CameraCalibrator(self.config)
        
        # State variables
        self.is_running = False
        self.frame_count = 0
        self.fps_deque = deque(maxlen=30)
        
        print("✓ System initialized successfully")
        print(f"✓ Focal Length: {self.config.FOCAL_LENGTH} pixels")
        print(f"✓ Safe Distance: {self.config.SAFE_DISTANCE}m")
        print(f"✓ Caution Distance: {self.config.CAUTION_DISTANCE}m")
    
    def run_calibration(self):
        """Run camera calibration before main system."""
        print("\n" + "="*70)
        print("CAMERA CALIBRATION")
        print("="*70)
        
        choice = input(
            "Select calibration method:\n"
            "1. Print calibration guide\n"
            "2. Calibrate with known object (Interactive)\n"
            "3. Skip calibration (use current focal length)\n"
            "4. Manual focal length input\n"
            "Choice (1-4): "
        )
        
        if choice == '1':
            CameraCalibrator.print_calibration_guide()
        elif choice == '2':
            object_width = float(input("Enter known object width in meters: "))
            distance = float(input("Enter object distance in meters: "))
            focal_length = self.calibrator.calibrate_with_known_object(
                object_width, distance
            )
            if focal_length:
                self.config.FOCAL_LENGTH = focal_length
                print(f"\n✓ Focal length updated to: {focal_length:.2f}")
        elif choice == '3':
            print(f"Using current focal length: {self.config.FOCAL_LENGTH}")
        elif choice == '4':
            focal_length = float(input("Enter focal length in pixels: "))
            self.config.FOCAL_LENGTH = focal_length
            print(f"✓ Focal length set to: {focal_length}")
    
    def run(self, camera_id: int = 0, source: str = None):
        """
        Main execution loop for parking assist system.
        
        Args:
            camera_id (int): Camera device ID (0 for default)
            source (str): Optional video file source instead of camera
        """
        cap = cv2.VideoCapture(source if source else camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, self.config.FPS)
        
        if not cap.isOpened():
            print("ERROR: Cannot access camera!")
            return
        
        self.is_running = True
        print("\n" + "="*70)
        print("SMART PARKING ASSIST - RUNNING")
        print("="*70)
        print("Controls:")
        print("  'q' - Quit")
        print("  's' - Screenshot")
        print("  'c' - Recalibrate")
        print("="*70 + "\n")
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    print("ERROR: Cannot read frame from camera")
                    break
                
                # Process frame
                processed_frame = self._process_frame(frame)
                
                # Display
                cv2.imshow('Smart Parking Assist System', processed_frame)
                
                # Handle input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self._save_screenshot(frame)
                elif key == ord('c'):
                    self.run_calibration()
                
                self.frame_count += 1
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("\n✓ System stopped")
    
    def _process_frame(self, frame) -> np.ndarray:
        """Process single frame with detection and distance estimation."""
        import time
        start_time = time.time()
        
        # Run YOLO detection
        results = self.model(frame, conf=self.config.CONFIDENCE_THRESHOLD, 
                           iou=self.config.IOU_THRESHOLD, verbose=False)
        
        # Process detections
        if results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = results[0].names[class_id]
                
                # Only process target classes
                if class_name not in self.config.TARGET_CLASSES:
                    continue
                
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                bbox_width = x2 - x1
                bbox_height = y2 - y1
                
                # Estimate distance
                raw_distance = self.distance_estimator.estimate_distance(
                    bbox_width, class_name
                )
                smoothed_distance = self.distance_estimator.get_smoothed_distance(
                    raw_distance
                )
                
                # Get warning level
                warning = WarningLevel.get_warning_level(
                    smoothed_distance, self.config
                )
                
                # Trigger audio alert
                self.audio_system.trigger_alert(warning)
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2),
                             warning['color'], self.config.LINE_THICKNESS)
                
                # Draw distance and warning level
                label = (f"{class_name} | "
                        f"{smoothed_distance:.2f}m | "
                        f"{warning['level']}")
                
                cv2.putText(frame, label, (x1, y1 - 10),
                           self.config.FONT, self.config.FONT_SCALE,
                           warning['color'], self.config.FONT_THICKNESS)
                
                # Draw warning indicator circle
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cv2.circle(frame, (center_x, center_y), 5, warning['color'], -1)
        
        # Draw UI elements
        self._draw_ui(frame)
        
        # Calculate and display FPS
        fps = 1 / (time.time() - start_time + 1e-6)
        self.fps_deque.append(fps)
        avg_fps = np.mean(self.fps_deque)
        
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (10, 30),
                   self.config.FONT, 0.8, (0, 255, 0), 2)
        
        return frame
    
    def _draw_ui(self, frame):
        """Draw system status UI elements."""
        height = frame.shape[0]
        
        # Warning threshold legend
        y_pos = height - 100
        cv2.putText(frame, "Thresholds:", (10, y_pos),
                   self.config.FONT, 0.6, (255, 255, 255), 1)
        
        # SAFE indicator
        cv2.rectangle(frame, (10, y_pos + 20), (80, y_pos + 40),
                     WarningLevel.SAFE['color'], -1)
        cv2.putText(frame, f">={self.config.SAFE_DISTANCE}m", (90, y_pos + 35),
                   self.config.FONT, 0.5, (255, 255, 255), 1)
        
        # CAUTION indicator
        cv2.rectangle(frame, (10, y_pos + 45), (80, y_pos + 65),
                     WarningLevel.CAUTION['color'], -1)
        cv2.putText(frame, f"{self.config.CAUTION_DISTANCE}m-{self.config.SAFE_DISTANCE}m",
                   (90, y_pos + 60), self.config.FONT, 0.5, (255, 255, 255), 1)
        
        # STOP indicator
        cv2.rectangle(frame, (10, y_pos + 70), (80, y_pos + 90),
                     WarningLevel.STOP['color'], -1)
        cv2.putText(frame, f"<{self.config.CAUTION_DISTANCE}m", (90, y_pos + 85),
                   self.config.FONT, 0.5, (255, 255, 255), 1)
    
    def _save_screenshot(self, frame):
        """Save screenshot with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parking_assist_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"✓ Screenshot saved: {filename}")


# =====================================================
# ENTRY POINT
# =====================================================
def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("SMART PARKING ASSIST SYSTEM - FINAL YEAR ENGINEERING PROJECT")
    print("="*70)
    print("Version: 1.0")
    print("Date: February 2026")
    print("="*70 + "\n")
    
    # Initialize system
    system = SmartParkingAssist()
    
    # Optional: Run calibration
    choice = input(
        "Do you want to calibrate camera before starting? (y/n): "
    ).lower()
    if choice == 'y':
        system.run_calibration()
    
    # Start main loop
    system.run()


if __name__ == "__main__":
    main()
