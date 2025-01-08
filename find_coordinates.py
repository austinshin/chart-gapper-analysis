import pyautogui
import time
import keyboard

def find_coordinates():
    print("Coordinate Finder Tool")
    print("----------------------")
    print("Instructions:")
    print("1. Move your mouse to any corner of a window")
    print("2. Press 'c' to capture coordinates")
    print("3. Press 'q' to quit")
    print("\nStarting in 5 seconds... Move to your DAS Trader window")
    
    time.sleep(5)
    
    saved_coordinates = []
    
    while True:
        if keyboard.is_pressed('c'):
            x, y = pyautogui.position()
            saved_coordinates.append((x, y))
            print(f"\nCaptured position: x={x}, y={y}")
            time.sleep(0.5)  # Prevent multiple captures
            
        elif keyboard.is_pressed('q'):
            break
            
    print("\nAll captured coordinates:")
    for i, (x, y) in enumerate(saved_coordinates, 1):
        print(f"Point {i}: x={x}, y={y}")

if __name__ == "__main__":
    find_coordinates()