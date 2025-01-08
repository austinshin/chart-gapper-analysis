import mss
import time
from PIL import Image
import numpy as np

def test_monitors():
    with mss.mss() as sct:
        # Print detailed information about each monitor
        print("\nMonitor Information:")
        for i, monitor in enumerate(sct.monitors):
            print(f"\nMonitor {i}:")
            for key, value in monitor.items():
                print(f"{key}: {value}")
            
            # Take a test screenshot of each monitor
            try:
                print(f"\nTaking test screenshot of Monitor {i}...")
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image for analysis
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                print(f"Actual screenshot dimensions: {img.size}")
                print(f"Raw pixel data dimensions: {screenshot.width}x{screenshot.height}")
                
                # Save the test screenshot
                output_file = f"monitor_{i}_test.png"
                img.save(output_file)
                print(f"Saved test screenshot as: {output_file}")
                
            except Exception as e:
                print(f"Error capturing monitor {i}: {e}")
            
            print("-" * 50)

if __name__ == "__main__":
    print("Starting monitor test...")
    test_monitors()
    print("\nTest complete. Check the saved screenshots and monitor information above.")