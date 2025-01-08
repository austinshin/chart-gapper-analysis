import pyautogui
import time
import keyboard
import mss
import numpy as np
from PIL import Image, ImageGrab

def analyze_region(sct, x, y):
    """Analyze a region and show why it would or wouldn't be counted as a position"""
    try:
        # Define regions to check (all relative to x,y point)
        regions = {
            'number': {'left': x - 30, 'top': y - 5, 'width': 30, 'height': 15},
            'symbol': {'left': x, 'top': y - 5, 'width': 60, 'height': 15},
            'price': {'left': x + 70, 'top': y - 5, 'width': 60, 'height': 15}
        }
        
        results = {}
        
        for name, region in regions.items():
            screenshot = sct.grab(region)
            pixels = np.array(screenshot)
            
            # Calculate various metrics
            avg_value = np.mean(pixels)
            non_white_pixels = np.sum(pixels < 240) / pixels.size
            
            results[name] = {
                'avg_value': avg_value,
                'non_white_ratio': non_white_pixels,
                'is_content': non_white_pixels > 0.1  # More than 10% non-white pixels
            }
        
        # Print analysis
        print("\n--- Position Analysis ---")
        for name, data in results.items():
            print(f"\n{name.upper()} REGION:")
            print(f"Average pixel value: {data['avg_value']:.2f}")
            print(f"Non-white pixel ratio: {data['non_white_ratio']:.2%}")
            print(f"Contains content: {data['is_content']}")
        
        # Make final determination
        is_position = sum(data['is_content'] for data in results.values()) >= 2
        print(f"\nFINAL VERDICT: {'IS' if is_position else 'NOT'} a position")
        print("------------------")
        
        return is_position
        
    except Exception as e:
        print(f"Error analyzing region: {e}")
        return False

def test_detection():
    print("Position Detection Test Tool")
    print("---------------------------")
    print("Controls:")
    print("  't' - Test current mouse position")
    print("  'c' - Continuously test current position")
    print("  's' - Stop continuous testing")
    print("  'q' - Quit")
    
    continuous = False
    last_pos = None
    
    with mss.mss() as sct:
        while True:
            current_pos = pyautogui.position()
            
            if keyboard.is_pressed('t'):
                x, y = current_pos
                print(f"\nTesting position at: x={x}, y={y}")
                analyze_region(sct, x, y)
                time.sleep(0.5)
                
            elif keyboard.is_pressed('c'):
                print("\nStarting continuous testing - press 's' to stop")
                continuous = True
                time.sleep(0.5)
                
            elif keyboard.is_pressed('s'):
                continuous = False
                print("\nStopped continuous testing")
                time.sleep(0.5)
                
            elif keyboard.is_pressed('q'):
                break
            
            if continuous:
                if current_pos != last_pos:
                    x, y = current_pos
                    print(f"\nMouse at: x={x}, y={y}")
                    analyze_region(sct, x, y)
                    last_pos = current_pos
            
            time.sleep(0.1)

if __name__ == "__main__":
    print("\nStarting in 3 seconds...")
    print("Move your mouse over positions to test detection")
    time.sleep(3)
    test_detection()