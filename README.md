# Youtube-Analytics-Dashboard
The YouTube Analytics Dashboard is a Streamlit app that uses the YouTube Data API to fetch real-time channel data like views, likes, and comments. It visualizes metrics using Plotly charts bar, line, radar, and pie for engagement insights, allowing filtering by playlist, date range, and video count.

Steps to build the project
cd "C:\Users\Downloads\DssaProject\.venv" 
PS C:\Users\Downloads\DssaProject\.venv> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
PS C:\Users\Downloads\DssaProject\.venv> .\Scripts\Activate.ps1
(.venv) PS C:\Users\Downloads\DssaProject\.venv> python -m pip install streamlit
(.venv) PS C:\Users\Downloads\DssaProject\.venv> python -m pip install plotly    
(.venv) PS C:\Users\Downloads\DssaProject\.venv> python -m pip install google-api-python-
(.venv) PS C:\Users\Downloads\DssaProject\.venv> streamlit run main.py
