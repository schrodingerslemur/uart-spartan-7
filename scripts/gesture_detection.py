import cv2
import serial
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# Configuration
SERIAL_PORT = 'COM9'  # Change this to your desired port
BAUD_RATE = 115200
CAMERA_INDEX = 0

# Hand landmark connections for drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # Index
    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (5, 9), (9, 13), (13, 17)  # Palm
]

class HandGestureDetector:
    def __init__(self, serial_port, baud_rate):
        # Initialize MediaPipe Hand Landmarker
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.frame_timestamp = 0
        self.right = True
        
        # Initialize serial connection
        try:
            self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
            time.sleep(2)  # Wait for connection to establish
            print(f"Serial connection established on {serial_port}")
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            self.ser = None
        
        # Initialize camera
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise Exception("Could not open camera")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def draw_landmarks(self, image, hand_landmarks, w, h):
        """Draw hand landmarks and connections"""
        # Draw connections
        for connection in HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = hand_landmarks[start_idx]
            end = hand_landmarks[end_idx]
            
            start_point = (int(start.x * w), int(start.y * h))
            end_point = (int(end.x * w), int(end.y * h))
            
            cv2.line(image, start_point, end_point, (255, 255, 255), 2)
        
        # Draw landmarks
        for landmark in hand_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            cv2.circle(image, (x, y), 7, (255, 255, 255), 1)
    
    def get_hand_y_position(self, hand_landmarks, frame_height):
        """Get the Y position of the hand (using wrist landmark)"""
        wrist = hand_landmarks[0]  # Wrist is landmark 0
        y_pos = int(wrist.y * frame_height)
        return y_pos
    
    def send_uart_data(self, left_y, right_y):
        """Send 1-byte UART packet:
        MSB = direction (1=right, 0=left)
        lower 7 bits = magnitude (0–127)
        """
        if self.ser and self.ser.is_open:
            try:
                # Clamp to 7 bits
                left_val  = max(0, min(127, left_y))
                right_val = max(0, min(127, right_y))

                if self.right:
                    packet = (1 << 7) | right_val   # 1xxxxxxx
                else:
                    packet = (0 << 7) | left_val    # 0xxxxxxx

                self.ser.write(bytes([packet]))
                self.right = not self.right

            except Exception as e:
                print(f"UART transmission error: {e}")

    def run(self):
        """Main loop"""
        try:
            right = 1
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
                # Flip frame horizontally for mirror view
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe Image
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                # Detect hands with timestamp
                self.frame_timestamp += 1
                detection_result = self.detector.detect_for_video(mp_image, self.frame_timestamp)
                
                # Create split screen
                left_frame = frame[:, :w//2].copy()
                right_frame = frame[:, w//2:].copy()
                
                # TODO: right now max is 800: fix that to 500
                # TODO: increase to 9 bits
                left_y = 240  # Default center value
                right_y = 240
                
                # Process detected hands
                if detection_result.hand_landmarks:
                    for hand_landmarks in detection_result.hand_landmarks:
                        # Get Y position
                        y_pos = self.get_hand_y_position(hand_landmarks, h)
                        
                        # Determine which side of screen the hand is on
                        # Calculate average X position of all landmarks
                        avg_x = sum(landmark.x for landmark in hand_landmarks) / len(hand_landmarks)
                        
                        # If hand is on left side of screen (x < 0.5), it's the left hand
                        if avg_x < 0.5:
                            left_y = y_pos
                            # Draw on left frame
                            self.draw_landmarks(left_frame, hand_landmarks, w//2, h)
                            cv2.putText(left_frame, f"Left Hand Y: {left_y}", 
                                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                       0.7, (0, 255, 0), 2)
                        else:  # Hand is on right side of screen
                            right_y = y_pos
                            # Adjust x coordinates for right frame (subtract 0.5 to map to right half)
                            adjusted_landmarks = []
                            for lm in hand_landmarks:
                                adjusted_lm = type('obj', (object,), {
                                    'x': (lm.x - 0.5) * 2,  # Remap from [0.5,1] to [0,1]
                                    'y': lm.y,
                                    'z': lm.z
                                })()
                                adjusted_landmarks.append(adjusted_lm)
                            
                            # Draw on right frame
                            self.draw_landmarks(right_frame, adjusted_landmarks, w//2, h)
                            cv2.putText(right_frame, f"Right Hand Y: {right_y}", 
                                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                       0.7, (0, 255, 0), 2)
                
                # Add labels
                cv2.putText(left_frame, "LEFT HAND", (10, h-20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(right_frame, "RIGHT HAND", (10, h-20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Combine frames
                combined_frame = cv2.hconcat([left_frame, right_frame])
                
                # Send UART data
                left_y = int(((left_y/950) * 255) / 2)
                right_y = int(((right_y/950) * 255) / 2)
                self.send_uart_data(left_y, right_y)
                
                # Display UART data on frame
                cv2.putText(combined_frame, f"UART: L:{left_y:02x} R:{right_y:02x}", 
                           (w//2 - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 255), 2)
                
                # Display
                cv2.imshow('Hand Gesture Detection - Split Screen', combined_frame)
                
                # TODO: 16-bit for left and right
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    print("Hand Gesture Detection with UART Transmission")
    print("=" * 50)
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print("Press 'q' to quit")
    print("=" * 50)
    print("\nNeed hand_landmarker.task model file!")
    print("Download from:")
    print("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
    print("=" * 50)
    
    try:
        detector = HandGestureDetector(SERIAL_PORT, BAUD_RATE)
        detector.run()
    except FileNotFoundError:
        print("\nERROR: hand_landmarker.task model file not found!")
        print("Please download it from:")
        print("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
        print("And place it in the same directory as this script.")