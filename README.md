# 🧪 Cheminformatics Virtual Laboratory

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?logo=flask&logoColor=white)
![RDKit](https://img.shields.io/badge/RDKit-Cheminformatics-2e8b57)
![3Dmol.js](https://img.shields.io/badge/3Dmol.js-WebGL_3D-orange)
![ReportLab](https://img.shields.io/badge/ReportLab-PDF_Engine-red)
![License](https://img.shields.io/badge/License-MIT-green)

**An interactive virtual laboratory for molecular modeling, drug-likeness evaluation, structural analysis, and cryptographic chemical cybersecurity.**

*Developed at SRM Institute of Science and Technology, Tiruchirappalli Campus*  
*Department of Cybersecurity • Faculty of Engineering and Technology*

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Module Highlights](#-module-highlights)
  - [1. 🏠 Home & Molecule Showcase](#1--home--molecule-showcase)
  - [2. 📖 Theory & Conceptual Foundations](#2--theory--conceptual-foundations)
  - [3. 🔬 Real-Time Molecular Visualization (2D & 3D)](#3--real-time-molecular-visualization-2d--3d)
  - [4. 📊 Molecular Properties & Descriptors](#4--molecular-properties--descriptors)
  - [5. 📈 Structure–Property Analysis & Comparison](#5--structureproperty-analysis--comparison)
  - [6. 🚀 Cybersecurity & Advanced Cheminformatics](#6--cybersecurity--advanced-cheminformatics)
  - [7. 📝 Assessment Quiz (24 Questions)](#7--assessment-quiz-24-questions)
  - [8. 📄 Automated 10-Page Laboratory PDF Report](#8--automated-10-page-laboratory-pdf-report)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [API Reference](#-api-reference)
- [Developers & Institutional Affiliation](#-developers--institutional-affiliation)
- [License](#-license)

---

## 🌟 Overview

The **Cheminformatics Virtual Laboratory** is a comprehensive educational and research web platform. It eliminates the traditional requirement of specialized local molecular modeling software by bringing **RDKit**, **WebGL-based 3Dmol.js rendering**, and **ReportLab publishing** directly into any modern web browser.

Built without relying on rigid dashboard wrappers, the platform uses a high-performance **Flask REST API** backend paired with a reactive, mobile-responsive **HTML5/CSS3/JavaScript** frontend. It enables students, chemists, and cybersecurity researchers to study molecular structures, calculate physicochemical descriptors, evaluate Lipinski bioavailability criteria, inspect core scaffolds, and verify molecular integrity using cryptographic digests.

---

## ✨ Key Features

- **Zero-Install Client Experience**: Run 2D structure sketching, 3D conformer generation, and chemical calculations in real-time within the browser.
- **21 Molecular Descriptors**: Automatically computes MW, exact mass, LogP, TPSA, formal charge, H-bond donors/acceptors, rotatable bonds, BertzCT complexity, sigma/pi bond counts, aromaticity, and Fraction Csp3.
- **Drug-Likeness & Lipinski Compliance**: Instant automated checks for Lipinski's Rule of 5 violations and Veber criteria.
- **Advanced 3D WebGL Visualization**: Rotate, zoom, pan, and toggle between Ball-and-Stick, Stick, Space-Filling (CPK), and Wireframe models, plus optional van der Waals (VDW) surface visualization.
- **Intersection of Cybersecurity & Chemistry**: Tamper-proof molecular fingerprinting using SHA-256, SHA3-256, MD5, and IUPAC InChIKey to demonstrate data integrity in computational chemistry databases.
- **Automated 10-Page Official Lab PDF Report**: Dual-pass `NumberedCanvas` engine that builds an institutional 10-page research laboratory document complete with high-resolution conformers, comparative scatter charts, and faculty signature grids.
- **100% Offline Capable**: Bundled with local JS assets for air-gapped laboratory computer environments.

---

## 🔍 Module Highlights

### 1. 🏠 Home & Molecule Showcase
- Responsive welcome portal with institutional headers and SRM logo.
- Interactive showcase of 10 common organic compounds (Aspirin, Caffeine, Paracetamol, Ibuprofen, Glucose, Ethanol, Acetic Acid, Benzene, Penicillin G, Cholesterol) with rendered 2D topologies and SMILES line notations.
- Cross-tab synchronized student session state.

### 2. 📖 Theory & Conceptual Foundations
- **Cheminformatics Core**: Virtual screening, ADMET profiling, and SAR principles.
- **SMILES Syntax**: Comprehensive rules reference table (bonds, branches, rings, chirality) and interactive card examples.
- **Descriptor Metrics**: Explanations of polar surface area (TPSA), lipophilicity (LogP), and saturation indices.
- **3D Molecular Models**: Interactive side-by-side comparison of 4 representation models (Ball & Stick, Stick, CPK, Wireframe) loaded with WebGL.

### 3. 🔬 Real-Time Molecular Visualization (2D & 3D)
- Instant SMILES validation and valence verification.
- High-definition 2D structure depiction.
- Heavy atom, sigma bond ($\sigma$), pi bond ($\pi$), and ring topology counts.
- Real-time 3D coordinate generation via RDKit's ETKDG distance geometry and MMFF94 force field optimization.

### 4. 📊 Molecular Properties & Descriptors
- Full 21-descriptor statistical table.
- 6 key pharmacological metrics cards (LogP, TPSA, HBD, HBA, Rotatable Bonds, Aromatic Rings).
- One-click CSV descriptor export.
- Single-compound vector PDF report generation.
- Static Matplotlib 3D render preview.

### 5. 📈 Structure–Property Analysis & Comparison
- Batch comparison across custom user-entered molecules.
- Comprehensive 13-column comparative matrix.
- Interactive bar charts for comparative metric exploration powered by Chart.js.
- Lipinski Chemical Space scatter plot (Molecular Weight vs LogP) with cutoff boundaries.
- Categorized Lipinski violation feedback badges.

### 6. 🚀 Cybersecurity & Advanced Cheminformatics
- **Cryptographic Hashes**: SHA-256, SHA3-256, and MD5 digests derived from canonicalized SMILES to detect unauthorized molecular alterations.
- **InChI & InChIKey**: Standardized 27-character fixed-length hashed IUPAC digital representations.
- **QED Drug-Likeness Score**: Continuous desirability profiling (0.0 to 1.0) integrating 8 physicochemical properties (Bickerton et al., Nature Chemistry 2012).
- **Bemis-Murcko Scaffold Deconstruction**: Automatic stripping of non-cyclic substituents to isolate core ring architectures and linkers.
- **Molecular Similarity Engine**: Pairwise Tanimoto, Dice, and Cosine similarity coefficient computations using topological Morgan/Daylight bit fingerprints.

### 7. 📝 Assessment Quiz (24 Questions)
- 24 cheminformatics and structural chemistry multiple-choice questions.
- Automated server-side grading with percentage scoring and responsive progress indicator.
- Detailed breakdown highlighting missed questions, student choices, and correct answers.

### 8. 📄 Automated 10-Page Laboratory PDF Report
- Generates an official, submission-ready 10-page academic laboratory document:
  - **Page 1**: Executive cover, institutional typography, student metadata, experiment abstract, and Table of Contents.
  - **Pages 2–8**: Dedicated single-page analytical dossiers for 7 compounds (side-by-side 2D structure + 3D conformer, 21-descriptor grid, pharmacological interpretation).
  - **Page 9**: Multi-compound correlation matrix and Lipinski chemical space scatter plot.
  - **Page 10**: Pipeline technological stack summary, script execution walkthrough, learning outcomes, and formal faculty evaluation sign-off block.

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend** | Python 3.9+, Flask, Jinja2, Werkzeug |
| **Cheminformatics** | RDKit (MolFromSmiles, Descriptors, AllChem, Crippen, QED, MurckoScaffold, DataStructs) |
| **Frontend** | Vanilla JavaScript (ES6+), HTML5, Custom Responsive CSS3 |
| **3D Graphics** | WebGL, 3Dmol.js |
| **Data & Charts** | Chart.js (UMD), NumPy, Pandas |
| **PDF Publishing** | ReportLab (Platypus, NumberedCanvas, TableStyle, Flowables), Matplotlib |

---

## 📁 Project Structure

```plaintext
Chem-Lab/
├── app.py                      # Main Flask application and REST API endpoints
├── app_streamlit.py            # Original Streamlit version (kept for reference)
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── assets/
│   ├── srm_logo.png            # SRMIST institutional emblem
│   └── srm_logo_white_bg.png   # Alternative logo asset
├── static/
│   ├── css/
│   │   └── style.css           # Institutional green theme & mobile responsive styles
│   └── js/
│       ├── 3Dmol-min.js        # Local WebGL 3D molecular viewer engine
│       ├── chart.umd.min.js    # Local Chart.js engine
│       └── app.js              # Application state & client interactions
└── templates/
    └── index.html              # Multi-module single page application template
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have **Python 3.9** or newer installed:
```bash
python --version
```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/cheminformatics-virtual-lab.git
   cd cheminformatics-virtual-lab
   ```

2. **Create and activate a virtual environment** *(recommended)*:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open in browser**:
   Navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 📡 API Reference

| Endpoint | Method | Payload / Query | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | — | Serves the main application interface |
| `/api/validate` | `POST` | `{"smiles": "..."}` | Validates SMILES and returns atom/bond summary |
| `/api/mol2d` | `GET` | `?smiles=...&w=...&h=...` | Streams high-resolution 2D PNG depiction |
| `/api/mol3d` | `POST` | `{"smiles": "..."}` | Generates optimized 3D conformer MolBlock |
| `/api/mol3d_static` | `GET` | `?smiles=...&style=...` | Streams static Matplotlib 3D plot |
| `/api/properties` | `POST` | `{"smiles": "..."}` | Computes all 21 molecular descriptors |
| `/api/properties_csv` | `POST` | `{"smiles": "..."}` | Exports single-molecule descriptors as CSV |
| `/api/single_pdf` | `POST` | `{"smiles": "...", ...}` | Downloads single-molecule analysis PDF |
| `/api/compare` | `POST` | `{"input_text": "..."}` | Computes comparative metrics for compound list |
| `/api/compare_csv` | `POST` | `{"molecules": [...]}` | Exports comparative table as CSV |
| `/api/advanced` | `POST` | `{"smiles_a": "...", "smiles_b": "..."}` | Returns hashes, QED, Murcko scaffold, and similarity |
| `/api/quiz/submit` | `POST` | `{"answers": {...}}` | Grades quiz responses and returns detailed review |
| `/api/final_pdf` | `POST` | `{"student_name": "...", ...}` | Compiles and streams the complete 10-page PDF report |

---

## 👩‍💻 Developers & Institutional Affiliation

| Contributor | Registration Number | Email | Role |
| :--- | :--- | :--- | :--- |
| **Varshini A** | `RA2611030050040` | [va3375@srmist.edu.in](mailto:va3375@srmist.edu.in) | Full-Stack & Cheminformatics Developer |
| **Vismitha Parasa** | `RA2611030050047` | [vp8717@srmist.edu.in](mailto:vp8717@srmist.edu.in) | Full-Stack & Cheminformatics Developer |

**Department of Cybersecurity**  
Faculty of Engineering and Technology  
**SRM Institute of Science and Technology, Tiruchirappalli Campus**  
Tiruchirappalli, Tamil Nadu, India

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute for academic and research purposes.
