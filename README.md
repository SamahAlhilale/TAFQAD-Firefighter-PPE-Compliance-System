# TAQFAD: AI-Driven PPE Detection System for Firefighters

## Introduction
Firefighters operate in high-risk environments where incomplete or improperly worn Personal Protective Equipment (PPE) can lead to severe injuries or fatalities. Manual compliance checks are slow, error-prone, and inefficient.

To address this, we present **TAQFAD**, the first AI-driven PPE detection system in Saudi Arabia. This system leverages **YOLOv10 and YOLOv11** to analyze firefighter images and videos in real time. Trained on an annotated dataset, **YOLOv11 outperformed YOLOv10** with a higher **mAP@0.5 (0.646 vs. 0.586)** and **11% faster training**, ensuring superior accuracy and efficiency.

The system provides **instant alerts** for PPE violations, enhancing safety and compliance within firefighting operations.

---

## Getting Started
To set up and run TAQFAD, follow the steps below:

### Step 1: Download the Model
The trained model weights (`safety_equipment_best.pt`) are available for download via Google Drive. Please visit the following link to download the model:

➡ **[Download Model Weights](https://drive.google.com/file/d/1N9G3AgsdyNjsvWkf9SDJn5GkssO0wTFE/view?usp=drive_link)** 

Once downloaded, place `safety_equipment_best.pt` in the project directory.

---


### Step 2: Set Up the Virtual Environment

It is recommended to use a virtual environment to manage dependencies. Follow these steps to create and activate a virtual environment:

#### **For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### **For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```


### Step 3: Install Dependencies
Ensure that you have Python installed (preferably Python 3.8+). Then, install the required dependencies by running:

```bash
pip install -r requirements.txt
```



### Step 4: Your project directory should have the following structure:
``` 
TAQFAD/
│-- _pycache_/
│-- venv/
│-- Background2.jpg
│-- Background3.jpg
│-- firebase_credentials.json
│-- Logo2.png
│-- MainCode.py
│-- requirements.txt
│-- safety_equipment_best.pt  # Ensure this file is downloaded
│-- style.css
```

- MainCode.py - The main script for running the AI detection system.
- requirements.txt - List of dependencies required to run the project.
- safety_equipment_best.pt - The trained YOLO model for PPE detection.
- style.css - Custom CSS for UI styling.
- firebase_credentials.json - Firebase authentication file.
- Background2.jpg, Background3.jpg, Logo2.png - UI assets.

### Step 5:  Run the Streamlit Application
After installing the dependencies and downloading the model, launch the Streamlit app by running:
```
streamlit run MainCode.py
```

---

## Contact
For questions or support, please reach out to:
- Samah Alhilale | samahalhilale@outlook.com
- Razan Alqurashi | razant1425@gmail.com
- Bashayer Khan | bbss891@gmail.com
- Asrar Khadawurdi | asrar.y.k2003@gmail.com

