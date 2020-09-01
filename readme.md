# Triton Monitoring App

Monitoring/Log Viewing Browser app for Oxford Instruments Triton (and probabply newer Kelvinox) Fridges.
Works sowly on the log file, no tempering with the fridge control software required.

# Screenshot
![Screenshot of the app](https://github.com/reneotten/tritonMonitor/blob/master/doc/images/FridgeMonitor.PNG "Screenshot")

#Install (with conda virtual environment)
Create a virtual environment from the requirements.txt
```
conda create --name tritonmonitor_env --file requirements.txt
´´´
Launch the environment
```
conda activate tritonmonitor_env
´´´

# Usage
Create a settings file for your system using the python routine
```
python create_settings_file.py
´´´
after changing the "log_file" setting to the actual file path and choosing a file name for the file at the end of the document. 
Check if the names of the T-sensors are the same the one that are parsed into the dataframe (df) at the end of the "parse_triton_log" function in load_triton_log.py
In my case the "MC Plate" had to be changed and the "MC Plate T(K)" had to be changed as well (compare log-file triton200.json and triton201.json).
Activate the app using: 
```
python app.py --filename triton200.json --port 1234
```
`triton200.json` contains all Titles and channel names that vary from system to system and needs to be adopted. Two examples for two of our systems are included. Feel free to add more!



