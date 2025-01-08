import mss
import keyboard
import time
import pyautogui

def get_position_info():
    print("Move your mouse to the corners of your Trade Ideas window")
    print("Press 'p' to print position and monitor info")
    print("Press 'q' to quit")
    
    sct = mss.mss()
    
    while True:
        if keyboard.is_pressed('p'):
            x, y = pyautogui.position()  # Get mouse position using pyautogui
            print(f"\nMouse Position: x={x}, y={y}")
            
            # Print monitor info
            for i, monitor in enumerate(sct.monitors[1:], 1):  # Skip the "All in One" monitor
                print(f"\nMonitor {i}:")
                print(f"Left: {monitor['left']}")
                print(f"Top: {monitor['top']}")
                print(f"Width: {monitor['width']}")
                print(f"Height: {monitor['height']}")
                print(f"Scale: {monitor.get('scale', 1)}\n")
            
            time.sleep(0.5)
            
        elif keyboard.is_pressed('q'):
            break
        
        time.sleep(0.1)

if __name__ == "__main__":
    get_position_info()