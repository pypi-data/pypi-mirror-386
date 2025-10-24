# raspc-notif

A simple Python library that allows you to send custom notifications from your Raspberry Pi directly to the [RaspController](https://www.egalnetsoftwares.com/apps/raspcontroller/) mobile app.

This allows you to create custom scripts (e.g., monitoring temperature, checking for completed processes, security alerts) and receive real-time alerts on your phone.

---

## Requirements

Before you begin, please ensure you meet the following requirements:

1.  **RaspController PRO Version**
    The "Notifications" feature is only available in the **PRO version** of the RaspController application.

2.  **Registration & API Key**
    To send notifications from your Raspberry Pi to the app, you need to be registered.
    * Open the RaspController app on your mobile device.
    * Navigate to the “Raspberry Pi Notifications” section.
    * Register or Log in to the service.
    * Once logged in, take note of your **User API Key**. You will need this key for your Python script.

3.  **Internet Connection**
    To successfully send and receive notifications, both your Raspberry Pi and your mobile device (running RaspController) must be connected to the internet.

4.  **More informations**
    For complete information on using the library, advanced options, and all available features, please visit the official page: https://www.egalnetsoftwares.com/apps/raspcontroller/send_notifications/


---

## Documentation

For a detailed technical breakdown of all available classes, methods, and parameters within the ```raspc-notif``` library, you can access the full API reference documentation here:
https://www.egalnetsoftwares.com/files/raspcontroller/raspc_notif_lib_docs/

---

## Usage Example

Here is a basic example of how to use the `raspc-notif` library in your Python script. This example monitors the Raspberry Pi's CPU temperature and sends a high-priority notification if it exceeds 70°C.

```python
from raspc_notif import notif
from time import sleep
import subprocess

# ------------------------------------------------------------------
# IMPORTANT: Enter the User API Key you find in the RaspController app
# ------------------------------------------------------------------
sender = notif.Sender(apikey = "YOUR_API_KEY_HERE")

# Infinite loop to continuously get data
while True:
	
	# Gets data once every 5 seconds
	sleep(5)
	
	# Gets the CPU temperature
	try:
		cpu_temp_str = subprocess.check_output(["cat", "/sys/class/thermal/thermal_zone0/temp"]).decode("utf-8").strip()
		cpu_temp = float(cpu_temp_str) / 1000
	except Exception as e:
		print(f"Could not read temperature: {e}")
		continue
	
	# Check if the temperature exceeds a certain threshold
	if cpu_temp > 70:
		
		# Send notification to RaspController
		notif_message = f"The CPU has reached the temperature of {cpu_temp}^C"
		notification = notif.Notification("Attention!", notif_message, high_priority = True)
		
		print(f"Temperature threshold exceeded ({cpu_temp}^C). Sending notification...")
		result = sender.send_notification(notification)
		
		# Check if the submission was successful
		if result.status == notif.Result.SUCCESS:
			print(result.message)
		else:
			print(f"ERROR: {result.message}")
			
		# Wait 6 minutes before sending a notification again
		# This prevents spamming notifications
		if result.status != notif.Result.SOCKET_ERROR:
			sleep(60 * 6)

 ```

 **Note:** Remember to replace ```"YOUR_API_KEY_HERE"``` with the actual User API Key you got from the RaspController app.
