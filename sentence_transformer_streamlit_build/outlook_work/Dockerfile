# Use Windows Server Core as base
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Install Python (3.11 recommended for pywin32)
SHELL ["powershell", "-Command"]
RUN Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile python-installer.exe ; \
    Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0' -Wait ; \
    Remove-Item python-installer.exe -Force

# Verify Python
RUN python --version

# Set working directory
WORKDIR /app

# Copy project files
COPY app/ /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit when container starts
CMD ["streamlit", "run", "streamlit_final_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
