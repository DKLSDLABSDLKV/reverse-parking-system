"""
Standalone Camera Calibration Tool
===================================
Dedicated script for camera calibration without running full parking assist system.

Use this to:
1. Quickly calibrate your camera
2. Find optimal focal length
3. Validate calibration with test distances
4. Document camera specifications

Author: Anonymous
Date: February 2026
"""

import cv2
import numpy as np
from ultralytics import YOLO
import json
from datetime import datetime


class CameraCalibrationTool:
    """Standalone tool for camera calibration."""
    
    def __init__(self, yolo_model: str = 'yolov8m.pt'):
        """Initialize calibration tool."""
        print("="*70)
        print("CAMERA CALIBRATION TOOL - Standalone")
        print("="*70)
        print("\nLoading YOLO model...")
        self.model = YOLO(yolo_model)
        self.focal_length = None
        self.calibration_data = {}
    
    def step1_measure_object_width(self) -> float:
        """Step 1: Get reference object width."""
        print("\n" + "="*70)
        print("STEP 1: REFERENCE OBJECT WIDTH")
        print("="*70)
        
        print("\nCommon reference objects and their widths:")
        print("  - Person (shoulder width):   0.45 meters")
        print("  - Car door:                  0.80 meters")
        print("  - Standard door frame:       0.90 meters")
        print("  - Full car width:            1.80 meters")
        print("  - Truck bed:                 2.50 meters")
        
        while True:
            try:
                width = float(input("\nEnter reference object width in meters: "))
                if width <= 0:
                    print("❌ Width must be positive")
                    continue
                print(f"✓ Reference width set to {width}m")
                return width
            except ValueError:
                print("❌ Invalid input. Enter a number.")
    
    def step2_position_object(self, object_width: float) -> float:
        """Step 2: Get distance to reference object."""
        print("\n" + "="*70)
        print("STEP 2: MEASURE DISTANCE")
        print("="*70)
        
        print("\nIMPORTANT: Measure from camera lens CENTER to object CENTER")
        print("Recommended: Start with 5 meters")
        
        while True:
            try:
                distance = float(input("\nEnter distance to object in meters: "))
                if distance <= 0:
                    print("❌ Distance must be positive")
                    continue
                print(f"✓ Distance set to {distance}m")
                
                # Show what we expect
                print(f"\nExpected measurement:")
                print(f"  Object width: {object_width}m")
                print(f"  Distance: {distance}m")
                print(f"  (Focal length will be calculated once captured)")
                
                # Store for later
                self.calibration_data['object_width'] = object_width
                self.calibration_data['distance'] = distance
                
                return distance
            except ValueError:
                print("❌ Invalid input. Enter a number.")
    
    def step3_capture_reference(self, camera_id: int = 0) -> float:
        """Step 3: Capture and measure reference object."""
        print("\n" + "="*70)
        print("STEP 3: CAPTURE REFERENCE OBJECT")
        print("="*70)
        
        print("\nInstructions:")
        print("1. Position reference object at marked distance")
        print("2. Keep object perpendicular to camera (facing directly)")
        print("3. Ensure good lighting")
        print("4. Press SPACE to capture")
        print("5. Press 'q' to quit this step")
        
        cap = cv2.VideoCapture(camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        bounding_box_width = None
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Cannot read from camera")
                    break
                
                # Draw instructions on frame
                cv2.putText(frame, "CALIBRATION CAPTURE MODE", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(frame, "Press SPACE to capture, 'q' to quit", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Distance: {self.calibration_data.get('distance', '?')}m", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                cv2.putText(frame, f"Object Width: {self.calibration_data.get('object_width', '?')}m", 
                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                
                if bounding_box_width:
                    cv2.putText(frame, f"Captured! Box Width: {bounding_box_width:.1f}px", 
                               (10, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                cv2.imshow("Camera Calibration Capture", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):  # Space key
                    bounding_box_width = self._detect_and_measure(frame)
                    if bounding_box_width:
                        print(f"\n✓ Captured! Bounding box width: {bounding_box_width:.2f} pixels")
                        break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        if not bounding_box_width:
            print("❌ No object captured")
            return None
        
        self.calibration_data['bounding_box_width'] = bounding_box_width
        return bounding_box_width
    
    def _detect_and_measure(self, frame) -> float:
        """Detect object and return bounding box width."""
        try:
            results = self.model(frame, conf=0.5, verbose=False)
            
            if results[0].boxes:
                # Get largest detection
                boxes = results[0].boxes
                largest_box = max(boxes, key=lambda x: (x.xyxy[0][2] - x.xyxy[0][0]))
                x1, y1, x2, y2 = largest_box.xyxy[0]
                
                # Calculate width
                width = float(x2 - x1)
                
                # Draw on frame for reference
                frame_copy = frame.copy()
                cv2.rectangle(frame_copy, (int(x1), int(y1)), (int(x2), int(y2)), 
                             (0, 255, 0), 2)
                cv2.putText(frame_copy, f"Width: {width:.1f}px", 
                           (int(x1), int(y1) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow("Detection Result", frame_copy)
                cv2.waitKey(1500)
                cv2.destroyWindow("Detection Result")
                
                return width
        except Exception as e:
            print(f"❌ Detection error: {e}")
        
        return None
    
    def step4_calculate_focal_length(self) -> float:
        """Step 4: Calculate focal length."""
        print("\n" + "="*70)
        print("STEP 4: CALCULATE FOCAL LENGTH")
        print("="*70)
        
        object_width = self.calibration_data.get('object_width')
        distance = self.calibration_data.get('distance')
        bbox_width = self.calibration_data.get('bounding_box_width')
        
        if not all([object_width, distance, bbox_width]):
            print("❌ Missing calibration data")
            return None
        
        # Formula: F = (W × D) / w
        focal_length = (object_width * distance) / (bbox_width + 1e-6)
        
        print(f"\nCalculation:")
        print(f"  Focal Length = (Object Width × Distance) / Bounding Box Width")
        print(f"  F = ({object_width}m × {distance}m) / {bbox_width:.2f}px")
        print(f"  F = {object_width * distance:.2f} / {bbox_width:.2f}")
        print(f"  F = {focal_length:.2f} pixels")
        
        print(f"\n✓ FOCAL LENGTH: {focal_length:.2f} pixels")
        print(f"  (Rounded: {round(focal_length)})")
        
        self.focal_length = focal_length
        self.calibration_data['focal_length'] = focal_length
        
        return focal_length
    
    def step5_verify_calibration(self, camera_id: int = 0):
        """Step 5: Verify calibration with test distances."""
        print("\n" + "="*70)
        print("STEP 5: VERIFY CALIBRATION")
        print("="*70)
        
        if not self.focal_length:
            print("⚠️ Skipping verification (no focal length)")
            return
        
        print("\nThis step tests calibration accuracy at different distances.")
        print("For each test, position object at exact distance and press SPACE.")
        
        test_distances = [2.0, 3.0, 5.0, 8.0]
        results = []
        
        cap = cv2.VideoCapture(camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        try:
            for test_distance in test_distances:
                print(f"\n{'─'*70}")
                print(f"TEST: Position object at {test_distance}m")
                print(f"{'─'*70}")
                
                captured = False
                while not captured:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Instructions
                    cv2.putText(frame, f"TEST DISTANCE: {test_distance}m", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.putText(frame, "Press SPACE to test, 'q' to skip remaining", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    
                    cv2.imshow("Verification Test", frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        captured = True
                        print(f"⊘ Skipped remaining tests")
                        break
                    elif key == ord(' '):
                        # Measure
                        bbox_width = self._detect_and_measure(frame)
                        if bbox_width:
                            # Calculate estimated distance
                            object_width = self.calibration_data['object_width']
                            estimated_distance = (object_width * self.focal_length) / bbox_width
                            error = abs(estimated_distance - test_distance) / test_distance * 100
                            
                            results.append({
                                'actual': test_distance,
                                'estimated': estimated_distance,
                                'error': error,
                                'bbox_width': bbox_width
                            })
                            
                            print(f"  Actual: {test_distance}m")
                            print(f"  Estimated: {estimated_distance:.2f}m")
                            print(f"  Error: {error:.1f}%", end="")
                            if error < 10:
                                print(" ✓ Excellent")
                            elif error < 20:
                                print(" ✓ Good")
                            elif error < 30:
                                print(" ⚠️ Acceptable")
                            else:
                                print(" ❌ Poor - Recalibrate")
                            
                            captured = True
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Summary
        if results:
            print(f"\n{'='*70}")
            print("VERIFICATION SUMMARY")
            print(f"{'='*70}")
            
            errors = [r['error'] for r in results]
            avg_error = np.mean(errors)
            
            print(f"\nTests Completed: {len(results)}")
            print(f"Average Error: {avg_error:.1f}%")
            
            if avg_error < 10:
                print("Status: ✓ EXCELLENT - Calibration is very accurate")
            elif avg_error < 15:
                print("Status: ✓ GOOD - Calibration is good")
            elif avg_error < 25:
                print("Status: ⚠️ ACCEPTABLE - Calibration works")
            else:
                print("Status: ❌ POOR - Recalibrate with better setup")
    
    def step6_save_calibration(self):
        """Step 6: Save calibration results."""
        print("\n" + "="*70)
        print("STEP 6: SAVE CALIBRATION")
        print("="*70)
        
        if not self.focal_length:
            print("❌ No focal length to save")
            return
        
        # Add metadata
        self.calibration_data['timestamp'] = datetime.now().isoformat()
        self.calibration_data['tool_version'] = '1.0'
        
        # Save to JSON
        filename = f"camera_calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
        
        print(f"\n✓ Calibration saved to: {filename}")
        
        # Print usage instructions
        print("\n" + "="*70)
        print("TO USE THIS CALIBRATION:")
        print("="*70)
        print(f"\nIn parking.py, update:")
        print(f"\nclass ParkingConfig:")
        print(f"    FOCAL_LENGTH = {round(self.focal_length)}")
        print(f"\nOr use the exact value: {self.focal_length:.2f}")
        print("="*70)
        
        # Save to a Python snippet
        code_filename = f"focal_length_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(code_filename, 'w') as f:
            f.write(f"# Camera Calibration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Object Width: {self.calibration_data.get('object_width')}m\n")
            f.write(f"# Distance: {self.calibration_data.get('distance')}m\n")
            f.write(f"# Bounding Box Width: {self.calibration_data.get('bounding_box_width')}px\n\n")
            f.write(f"FOCAL_LENGTH = {round(self.focal_length)}\n")
        
        print(f"✓ Python code snippet saved to: {code_filename}")
    
    def run_full_calibration(self, camera_id: int = 0):
        """Run complete calibration process."""
        try:
            # Step 1
            object_width = self.step1_measure_object_width()
            if not object_width:
                return
            
            # Step 2
            distance = self.step2_position_object(object_width)
            if not distance:
                return
            
            # Step 3
            bbox_width = self.step3_capture_reference(camera_id)
            if not bbox_width:
                return
            
            # Step 4
            focal_length = self.step4_calculate_focal_length()
            if not focal_length:
                return
            
            # Step 5
            choice = input("\nVerify calibration with test distances? (y/n): ").lower()
            if choice == 'y':
                self.step5_verify_calibration(camera_id)
            
            # Step 6
            self.step6_save_calibration()
            
            print("\n" + "="*70)
            print("✓ CALIBRATION COMPLETE")
            print("="*70)
        
        except KeyboardInterrupt:
            print("\n⚠️ Calibration cancelled by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("Camera Calibration Tool - Smart Parking Assist")
    print("="*70 + "\n")
    
    tool = CameraCalibrationTool()
    tool.run_full_calibration()


if __name__ == "__main__":
    main()
