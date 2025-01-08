import mss
import time as time_module
from datetime import datetime, time
import os
import keyboard
import pytz
import shutil
import pandas as pd
import threading
import tkinter as tk
from tkinter import ttk
import pystray
from PIL import Image, ImageDraw
import win32com.client
import winreg
import sys
import pyautogui
import numpy as np

class DASTradingAutomator:
    def __init__(self, screenshot_dir="screenshots", export_dir="exports", obsidian_vault_path=None):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        self.screenshot_dir = os.path.join(application_path, screenshot_dir)
        self.export_dir = os.path.join(application_path, export_dir)
        self.obsidian_vault_path = obsidian_vault_path or os.path.expanduser("~/Sync/Obsidian/01. Daytrading/Journal")
        
        print(f"Application path: {application_path}")
        print(f"Screenshot directory will be: {self.screenshot_dir}")
        
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.obsidian_vault_path, exist_ok=True)
        
        self.screenshot_files = []
        
        # Regular window regions
        self.regions = {
            'account_summary': {'top': 243, 'left': 2336, 'width': 884, 'height': 154},
            'positions_open': {'top': 420, 'left': 2331, 'width': 903, 'height': 267},
            'positions_closed': {'top': 691, 'left': 2331, 'width': 902, 'height': 268},
            'trade_ideas': {'top': -1488, 'left': 3440, 'width': 3840, 'height': 2160}
        }

        # Position window configuration
        self.position_config = {
            'window': {
                'top': 695,
                'left': 2330,
                'width': 898,    # 3228 - 2330
                'height': 261    # 956 - 695
            },
            'first_position': {
                'x': 2403,
                'y': 736
            },
            'vertical_spacing': 16,  # Average spacing between positions
            'max_positions': 15
        }
        
        # Updated chart region from coordinates
        self.chart_region = {
            'top': 179,
            'left': 91,
            'width': 2225,   # 2316 - 91
            'height': 1019   # 1198 - 179
        }

    def check_position_exists(self, sct, x, y):
        """Check if a position exists at the given coordinates using the 30% threshold method"""
        try:
            regions = {
                'number': {'left': x - 30, 'top': y - 5, 'width': 30, 'height': 15},
                'symbol': {'left': x + 20, 'top': y - 5, 'width': 60, 'height': 15},
                'price': {'left': x + 90, 'top': y - 5, 'width': 60, 'height': 15}
            }
            
            for name, region in regions.items():
                screenshot = sct.grab(region)
                pixels = np.array(screenshot)
                non_black_pixels = np.sum(pixels > 30) / pixels.size
                
                print(f"Region {name} non-black ratio: {non_black_pixels:.2%}")
                
                if non_black_pixels <= 0.30:
                    print(f"Region {name} below threshold: {non_black_pixels:.2%}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error checking position: {e}")
            return False

    def take_screenshot(self):
        current_date = datetime.now()
        date_str = current_date.strftime("%Y-%m-%d")
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        
        date_screenshot_dir = os.path.join(self.screenshot_dir, date_str)
        os.makedirs(date_screenshot_dir, exist_ok=True)
        
        screenshot_files = []
        
        try:
            print("\nTaking screenshots...")
            print(f"Saving to directory: {date_screenshot_dir}")
            
            with mss.mss() as sct:
                for region_name, region in self.regions.items():
                    print(f"Capturing {region_name}...")
                    filename = os.path.abspath(os.path.join(date_screenshot_dir, f"das_trader_{region_name}_{timestamp}.png"))
                    print(f"Saving to: {filename}")
                    
                    try:
                        mss_region = {
                            "top": region['top'],
                            "left": region['left'],
                            "width": region['width'],
                            "height": region['height']
                        }
                        print(f"Region details: {mss_region}")
                        
                        screenshot = sct.grab(mss_region)
                        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
                        
                        screenshot_files.append((region_name, filename))
                        print(f"✓ Successfully saved {region_name}")
                        
                        time_module.sleep(0.5)
                        
                    except Exception as e:
                        print(f"✗ Error capturing {region_name}: {e}")
                        print(f"Error type: {type(e)}")
        
        except Exception as e:
            print(f"Error during screenshot process: {str(e)}")
            print(f"Error type: {type(e)}")
            
        self.screenshot_files.extend(screenshot_files)
        return screenshot_files

    def take_position_screenshots(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_files = []
        
        try:
            print("\nCapturing chart screenshots for each position...")
            
            current_date = datetime.now()
            date_str = current_date.strftime("%Y-%m-%d")
            date_screenshot_dir = os.path.join(self.screenshot_dir, date_str)
            os.makedirs(date_screenshot_dir, exist_ok=True)
            
            with mss.mss() as sct:
                positions_found = 0
                for i in range(self.position_config['max_positions']):
                    check_x = self.position_config['first_position']['x']
                    check_y = self.position_config['first_position']['y'] + (i * self.position_config['vertical_spacing'])
                    
                    if check_y >= self.position_config['window']['top'] + self.position_config['window']['height']:
                        print("Reached end of window")
                        break
                    
                    print(f"\nChecking position {i+1} at y={check_y}")
                    if self.check_position_exists(sct, check_x, check_y):
                        positions_found += 1
                        print(f"✓ Valid position {positions_found} found")
                        
                        try:
                            pyautogui.doubleClick(check_x, check_y)
                            print(f"Double clicked position {positions_found} at y={check_y}")
                            
                            time_module.sleep(1)
                            
                            filename = os.path.abspath(os.path.join(
                                date_screenshot_dir, 
                                f"das_trader_chart_position_{positions_found}_{timestamp}.png"
                            ))
                            
                            screenshot = sct.grab(self.chart_region)
                            mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
                            
                            screenshot_files.append((f'chart_position_{positions_found}', filename))
                            print(f"✓ Saved chart for position {positions_found}")
                            
                        except Exception as e:
                            print(f"✗ Error capturing position {positions_found}: {e}")
                            break
                        
                        time_module.sleep(0.5)
                    else:
                        print(f"No valid position found at y={check_y}")
                    
                print(f"\nTotal valid positions processed: {positions_found}")
        
        except Exception as e:
            print(f"Error during position screenshots: {str(e)}")
            print(f"Error type: {type(e)}")
        
        self.screenshot_files.extend(screenshot_files)
        return screenshot_files

    def create_obsidian_note(self, screenshot_files):
        try:
            current_date = datetime.now()
            year_str = current_date.strftime("%Y")
            month_name = f"{current_date.strftime('%B')} {year_str}"
            date_str = current_date.strftime("%Y-%m-%d")
            
            print(f"\nCreating note for date: {date_str}")
            month_folder = os.path.join(self.obsidian_vault_path, month_name)
            day_folder = os.path.join(month_folder, date_str)
            
            os.makedirs(day_folder, exist_ok=True)
            attachments_dir = os.path.join(day_folder, 'attachments')
            os.makedirs(attachments_dir, exist_ok=True)
            
            note_filename = os.path.join(day_folder, f"{date_str}.md")
            
            # Validate and organize screenshots
            valid_screenshots = []
            for region_name, screenshot_file in screenshot_files:
                if os.path.exists(screenshot_file):
                    valid_screenshots.append((region_name, screenshot_file))
                    print(f"Processing: {screenshot_file}")
                    screenshot_filename = os.path.basename(screenshot_file)
                    new_path = os.path.join(attachments_dir, screenshot_filename)
                    shutil.copy2(screenshot_file, new_path)
                else:
                    print(f"Warning: Screenshot not found: {screenshot_file}")
            
            # Separate position screenshots from regular screenshots
            regular_shots = [(name, file) for name, file in valid_screenshots if not name.startswith('chart_position')]
            position_shots = [(name, file) for name, file in valid_screenshots if name.startswith('chart_position')]
            
            with open(note_filename, 'w') as f:
                # Write frontmatter
                f.write('---\n')
                f.write(f'date: {date_str}\n')
                f.write(f'time: {current_date.strftime("%H:%M:%S")}\n')
                f.write('type: trading-session\n')
                f.write('cssclass: two-column\n')
                f.write('---\n\n')
                
                # Title
                f.write(f'# Trading Session - {date_str}\n\n')
                
                # Market Overview section
                f.write('## Market Overview\n')
                for name, file in regular_shots:
                    filename = os.path.basename(file)
                    f.write(f'![[attachments/{filename}|1000]]\n')
                    f.write('- \n\n')
                
                # Positions section with two-column layout
                if position_shots:
                    f.write('\n## Positions\n\n')
                    for name, file in position_shots:
                        position_num = name.split('_')[-1]
                        filename = os.path.basename(file)

                        f.write(f'> ![[attachments/{filename}|1000]]\n')
                        f.write('> \n')
                        f.write(f'# Position {position_num} Notes\n')
                        f.write('Ticker:\n')
                        f.write('R:\n')
                        f.write('Gap % premarket:\n')
                        f.write('Float:\n')
                        f.write('Market Cap:\n')
                        f.write('Volume traded:\n')
                        f.write('Catalyst:\n')
                        f.write('Strategy:\n')
                        f.write('Notes:\n')
                        f.write('\n')
                
                # Additional Notes section
                f.write('\n## Additional Notes\n')
                f.write('- \n\n')
                
                # Tags
                f.write('\n#trading #market-analysis #das-trader\n')
            
            print(f"Created note: {note_filename}")
            return note_filename
            
        except Exception as e:
            print(f"Error creating Obsidian note: {str(e)}")
            print(f"Error type: {type(e)}")
            return None

    def is_screenshot_time(self):
        pst = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(pst).time()
        target_time = time(13, 35)
        return (current_time.hour == target_time.hour and 
                current_time.minute == target_time.minute)

class DASTradingSystemTray:
    def __init__(self):
        print("Initializing System Tray Application")
        self.automator = DASTradingAutomator(
            obsidian_vault_path=os.path.expanduser("~/Sync/Obsidian/01. Daytrading/Journal")
        )
        self.monitoring_active = False
        self.monitor_thread = None
        self.setup_tray()

    def create_tray_icon(self):
        icon_size = 64
        image = Image.new('RGB', (icon_size, icon_size), color='white')
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill='blue')
        return image

    def setup_tray(self):
        menu_items = [
            pystray.MenuItem('Capture All (Screenshots + Positions + Note)', self.capture_all),
            pystray.MenuItem('Take Screenshots', self.take_screenshots),
            pystray.MenuItem('Take Position Screenshots', self.take_position_screenshots),
            pystray.MenuItem('Create Note', self.create_note),
            pystray.MenuItem('Toggle Monitoring', self.toggle_monitoring),
            pystray.MenuItem('Settings', self.show_settings),
            pystray.MenuItem('Exit', self.quit_application)
        ]
        
        self.icon = pystray.Icon(
            'DAS Trader Tool',
            self.create_tray_icon(),
            'DAS Trader Tool',
            menu=pystray.Menu(*menu_items)
        )

    def capture_all(self):
        print("Starting full capture sequence...")
        
        def full_capture():
            # Take regular screenshots
            self.automator.take_screenshot()
            time_module.sleep(0.5)
            
            # Take position screenshots
            self.automator.take_position_screenshots()
            time_module.sleep(0.5)
            
            # Create note
            self.automator.create_obsidian_note(self.automator.screenshot_files)
            print("Full capture sequence completed")
        
        threading.Thread(target=full_capture, daemon=True).start()

    def take_screenshots(self):
        print("Manual screenshot triggered from tray")
        threading.Thread(target=self.automator.take_screenshot, daemon=True).start()
                         
    def take_position_screenshots(self):
        print("Manual position screenshots triggered from tray")
        threading.Thread(target=self.automator.take_position_screenshots, daemon=True).start()

    def create_note(self):
        print("Manual note creation triggered from tray")
        threading.Thread(
            target=self.automator.create_obsidian_note,
            args=(self.automator.screenshot_files,),
            daemon=True
        ).start()

    def toggle_monitoring(self):
        if not self.monitoring_active:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        print("Starting monitoring")
        self.monitoring_active = True
        
        def monitor_thread():
            while self.monitoring_active:
                try:
                    if self.automator.is_screenshot_time():
                        print("Automatic screenshot time reached")
                        self.take_screenshots()
                        self.create_note()
                        time_module.sleep(60)
                    time_module.sleep(1)
                except Exception as e:
                    print(f"Monitor error: {str(e)}")
        
        self.monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        print("Stopping monitoring")
        self.monitoring_active = False

    def show_settings(self):
        settings_window = tk.Tk()
        settings_window.title("Settings")
        settings_window.geometry("300x200")
        
        ttk.Label(settings_window, text="Capture Time (PST):").pack(pady=5)
        time_entry = ttk.Entry(settings_window)
        time_entry.insert(0, "13:35")
        time_entry.pack(pady=5)
        
        ttk.Button(settings_window, text="Save", command=settings_window.destroy).pack(pady=10)

    def quit_application(self):
        print("Quitting application")
        self.stop_monitoring()
        self.icon.stop()

def add_to_startup():
    try:
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = os.path.abspath(__file__)
        
        print(f"Adding to startup: {app_path}")
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(
            key,
            "DASTradingTool",
            0,
            winreg.REG_SZ,
            f'"{app_path}"'
        )
        
        winreg.CloseKey(key)
        print("Successfully added to startup")
        return True
    except Exception as e:
        print(f"Error adding to startup: {str(e)}")
        return False

def main():
    print("Starting DAS Trader Tool")
    add_to_startup()
    app = DASTradingSystemTray()
    app.icon.run()

if __name__ == "__main__":
    main()