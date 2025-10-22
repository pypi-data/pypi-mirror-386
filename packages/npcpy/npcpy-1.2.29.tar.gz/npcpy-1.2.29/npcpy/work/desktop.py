

action_space = {
        "click": {"x": "int (0-100)", "y": "int (0-100)", "button": "left|right|middle (optional)"},
        "type": {"text": "string"},
        "key": {"keys": "list of key names or a single key string"},
        "scroll": {"direction": "up|down", "amount": "int (optional)"},
        "wait": {"duration": "float seconds"},
        "bash": {"command": "string"},
        "hotkey": {"keys": "list of keys to press simultaneously"},
        "drag": {"start_x": "int (0-100)", "start_y": "int (0-100)", "end_x": "int (0-100)", "end_y": "int (0-100)"},
        "quit": {"description": "Use this action when the main goal is 100% complete."},
    }
try:
    import pyautogui
except:
    print('could not import pyautogui')
import time
import subprocess

def perform_action(action):
    action_type = action.get("type")
    print(f"Action received: {action}")

    try:
        width, height = pyautogui.size()

        if action_type == "click":
            x = max(0, min(100, action.get("x", 50)))
            y = max(0, min(100, action.get("y", 50)))
            x_pixel = int(x * width / 100)
            y_pixel = int(y * height / 100)
            print(f"Moving to ({x_pixel}, {y_pixel}) then clicking.")
            pyautogui.moveTo(x_pixel, y_pixel, duration=0.2)
            pyautogui.click()
            return {"status": "success", "output": f"Clicked at ({x}, {y})."}

        elif action_type == "bash":
            command = action.get("command", "")
            print(f"Executing bash command: {command}")
            subprocess.Popen(command, shell=True)
            return {"status": "success", "output": f"Launched '{command}'."}
        
        elif action_type == "type":
            text_to_type = action.get("text", "")
            print(f"Typing text: {text_to_type}")
            pyautogui.typewrite(text_to_type)
            return {"status": "success", "output": "Typed text."}

        elif action_type == "key":
            keys_to_press = action.get("keys", [])
            if isinstance(keys_to_press, str):
                keys_to_press = [keys_to_press]
            print(f"Pressing key(s): {keys_to_press}")
            for k in keys_to_press:
                pyautogui.press(k.lower())
            return {"status": "success", "output": "Pressed key(s)."}

        elif action_type == "hotkey":
            keys = action.get("keys", [])
            print(f"Pressing hotkey: {keys}")
            pyautogui.hotkey(*keys)
            return {"status": "success", "output": "Pressed hotkey."}

        elif action_type == "wait":
            duration = action.get("duration", 1)
            print(f"Waiting for {duration} seconds")
            time.sleep(duration)
            return {"status": "success", "output": f"Waited for {duration}s."}
        
        else:
            return {"status": "error", "message": f"Unknown or malformed action: {action}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}