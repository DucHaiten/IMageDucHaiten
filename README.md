---
license: openrail
language:
- en
---

# **IMageDucHaiten**

*Version:* `V1.1.1`

## **Table of Contents**

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Community and Support](#community-and-support)

## **Introduction**

**IMageDucHaiten** is a powerful tool, specifically designed to assist those working in artificial intelligence with the preparation of image data for training generative AI models. In version `V1.1.1`, **IMageDucHaiten** provides a suite of automated and flexible tools for processing, tagging, and captioning images, making the data preparation process more efficient and streamlined.

Whether you're an AI researcher, data engineer, or just someone who enjoys working with images, **IMageDucHaiten** can be an invaluable tool. While it excels at supporting AI data preparation, it is also accessible and beneficial to anyone looking to work with images effortlessly and effectively.

### **Key Features**

- **Image Converter**: Convert image formats to match the requirements of your AI model, supporting a wide range of formats such as PNG, JPG, GIF, BMP, and more.
- **Image Filter**: Filter and remove images that do not meet quality criteria such as size, resolution, ensuring a clean dataset for training.
- **Rotate & Flip**: Rotate and flip images to create various training data variations, enhancing dataset diversity.
- **Image Error Fix**: Automatically detect and fix errors in images, reducing the risk of using incomplete data.
- **Image To Tag**: Automatically tag images, optimizing the data labeling process for AI models.
- **Image To Caption**: Automatically generate captions, providing context to images, useful in image recognition and captioning tasks.
- **Photo Fantasy**: Create artistic effects on images, useful for data augmentation or enhancing creative content.
- **Shuffle Image**: Shuffle or sequence images to create a diverse dataset, suitable for analysis and modeling tasks.

**IMageDucHaiten** is not only ideal for AI training data preparation but also serves as a versatile application for all your image processing needs.

## **Installation**

To install and set up **IMageDucHaiten**, you have three options:

### **Option 1: Full Package Installation via Direct Download**

1. **Download the Full Package:**
   - Download the full package from the following link:
     [IMageDucHaiten_v1.1.1-Full.zip](https://huggingface.co/DucHaiten/IMageDucHaiten-Full/resolve/main/IMageDucHaiten_v1.1.1-Full.zip)

2. **Extract the Package:**
   - Extract the contents of the `.zip` file to your desired location.

3. **Install Visual Studio Code (if not installed):**
   - Download and install Visual Studio Code from [here](https://code.visualstudio.com/).
   - After installation, open Visual Studio Code.

4. **Activate the Virtual Environment:**
   - Open the extracted folder in Visual Studio Code by selecting **File > Open Folder** and navigate to the extracted folder.
   - Open the integrated terminal within Visual Studio Code by selecting **View > Terminal**.
   - Activate the pre-configured virtual environment:
     - On **Windows**:
       ```bash
       .\venv\Scripts\activate
       ```
     - On **macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

5. **Run the Application:**
   - After activating the virtual environment, you can start the application by running `python main.py` in the terminal.

### **Option 2: Full Package Installation via Git Clone**

1. **Install Git and Git LFS:**
   - Make sure you have Git installed on your system. If not, download and install it from [Git's official site](https://git-scm.com/downloads).
   - Install Git LFS (Large File Storage) by running the following command:
     ```bash
     git lfs install
     ```

2. **Clone the Repository:**
   - Use Git to clone the repository with all necessary files:
     ```bash
     git clone https://huggingface.co/DucHaiten/IMageDucHaiten
     ```

3. **Open the Project in Visual Studio Code:**
   - If you haven't installed Visual Studio Code, download and install it from [here](https://code.visualstudio.com/).
   - Open Visual Studio Code, then select **File > Open Folder** and navigate to the cloned folder.

4. **Activate the Virtual Environment:**
   - Open the integrated terminal by selecting **View > Terminal**.
   - Activate the virtual environment:
     - On **Windows**:
       ```bash
       .\venv\Scripts\activate
       ```
     - On **macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

5. **Run the Application:**
   - Start the application by running `python main.py` in the terminal.

### **Option 3: Manual Installation by Downloading Individual Files**

1. **Download the Files Manually:**
   - Download individual files and directories from the repository as needed.

2. **Set up a Virtual Environment:**
   - Create and activate a virtual environment:
     - On **Windows**:
       ```bash
       python -m venv venv
       .\venv\Scripts\activate
       ```
     - On **macOS/Linux**:
       ```bash
       python3 -m venv venv
       source venv/bin/activate
       ```

3. **Install Python Dependencies:**
   - Install the required Python packages using `requirements.txt`:
     ```bash
     pip install -r requirements.txt
     ```

4. **Install External Dependencies** (Ghostscript, ImageMagick, Visual C++ Redistributable):
   - Follow the instructions provided earlier to ensure all dependencies are properly installed.

5. **Open the Project in Visual Studio Code:**
   - If you haven't installed Visual Studio Code, download and install it from [here](https://code.visualstudio.com/).
   - Open Visual Studio Code, then select **File > Open Folder** and navigate to the project folder.

6. **Run the Application:**
   - Open the integrated terminal by selecting **View > Terminal**.
   - Activate the virtual environment, then start the application by running `python main.py` in the terminal.

## **Usage**

After completing the installation, you can run **IMageDucHaiten** using Visual Studio Code as follows:

### **1. Running the Application via Command Line (CMD)**

1. **Activate the Virtual Environment:**
   - On **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```
   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

2. **Run the Application:**
   - In the terminal, navigate to the folder where `main.py` is located.
   - Execute the following command to start the application:
     ```bash
     python main.py
     ```

### **2. Running the Application via Visual Studio Code**

1. **Open the Project in Visual Studio Code:**
   - Launch Visual Studio Code.
   - Open the project folder by selecting **File > Open Folder** and navigating to the folder where `main.py` is located.

2. **Activate the Virtual Environment:**
   - Open the integrated terminal within Visual Studio Code by selecting **View > Terminal**.
   - Activate the virtual environment:
     - On **Windows**:
       ```bash
       .\venv\Scripts\activate
       ```
     - On **macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

3. **Run the Application:**
   - In the terminal, start the application by running:
     ```bash
     python main.py
     ```

   - Alternatively, you can press **F5** to run the application with debugging.

### **Installing Visual Studio Code**

If you don't have Visual Studio Code installed, follow these steps:

1. **Download Visual Studio Code:**
   - Go to [Visual Studio Code's official site](https://code.visualstudio.com/).
   - Download the appropriate version for your operating system.

2. **Install Visual Studio Code:**
   - Run the installer and follow the on-screen instructions to complete the installation.

3. **Install the Python Extension:**
   - Open Visual Studio Code and go to the **Extensions** view by clicking on the square icon in the sidebar or pressing `Ctrl+Shift+X`.
   - Search for "Python" and install the extension provided by Microsoft.

After installing Visual Studio Code and the Python extension, you can follow the instructions above to run your application.

![Screenshot_1.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/Lfy93t29PfhazAAm9PzEi.png)
![Screenshot_2.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/-YdFtf3_-hCsjykh7XkDX.png)
![Screenshot_3.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/BLqDam81vkPpvWTKs9d42.png)
![Screenshot_4.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/cdhsBMhFMYzuEtNj2z4Tw.png)
![Screenshot_5.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/vtUoLEHhR5k5SIWwxEQDt.png)
![Screenshot_6.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/MEl_THxy-7IVjvLOtUa8P.png)
![Screenshot_7.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/ztbJOamnGoXVi49bJ0hqR.png)
![Screenshot_8.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/qw3osuCswU_8UaLqrshHY.png)
![Screenshot_9.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/fI-8nFHyWx3uGlss2bnpC.png)
![Screenshot_10.png](https://cdn-uploads.huggingface.co/production/uploads/630b58b279d18d5e53e3a5a9/3L644SpuP6lFj821PoViM.png)

## **Community and Support**

Join our community to stay updated, share your experiences, and get support from other users:

- **Discord Server**: Join our Discord community for discussions, support, and updates.
  - [Join Discord](https://discord.gg/vKEW6jqa49)

## **Support and Contributions**

If you find **IMageDucHaiten** useful and would like to support the project, consider making a donation or becoming a patron. Your contributions help in maintaining and improving the project:

- **PayPal**: You can make a one-time donation through PayPal.
  - [Donate via PayPal](https://www.paypal.com/paypalme/duchaiten)

- **Patreon**: Become a patron and support ongoing development with monthly contributions.
  - [Support on Patreon](https://www.patreon.com/duchaitenreal)

Thank you for your support!
