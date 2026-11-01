# ============================================================================
# Cheminformatics Virtual Laboratory (Flask Edition - Non-Streamlit)
# Developed by Varshini A & Vismitha Parasa — SRM Institute of Science and Technology
# ============================================================================

import os
import io
import json
import base64
import hashlib
from io import BytesIO

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    send_from_directory,
    Response,
)
import pandas as pd
import numpy as np
from PIL import Image as PILImage

# RDKit imports
from rdkit import Chem
from rdkit.Chem import (
    Descriptors,
    AllChem,
    rdMolDescriptors,
    Lipinski,
    Crippen,
    rdchem,
    QED,
)
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit import DataStructs

# Safe 2D Drawing for Headless & Serverless Environments (e.g. Vercel)
try:
    from rdkit.Chem import Draw
    HAS_RDKIT_DRAW = True
except (ImportError, Exception):
    HAS_RDKIT_DRAW = False

try:
    from rdkit.Chem.Draw import rdMolDraw2D
    HAS_RDKIT_MOLDRAW2D = True
except (ImportError, Exception):
    HAS_RDKIT_MOLDRAW2D = False

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Matplotlib for static 3D images
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)

# ============================================================================
# EXAMPLE MOLECULES DATABASE
# ============================================================================
EXAMPLE_MOLECULES = {
    "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "Caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "Paracetamol": "CC(=O)NC1=CC=C(O)C=C1",
    "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "Glucose": "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)O)O)O)O)O",
    "Ethanol": "CCO",
    "Acetic Acid": "CC(=O)O",
    "Benzene": "c1ccccc1",
    "Penicillin G": "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@@H]1C(=O)O",
    "Cholesterol": "C(CCCC(C)C)CCC1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C",
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def validate_smiles(smiles):
    """Validate a SMILES string and return the molecule object or None."""
    if not smiles or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        return mol
    except Exception:
        return None


def get_mol_2d_image(mol, size=(400, 400)):
    """Generate a 2D image of the molecule as PIL Image if Draw module is available."""
    if mol is None or not HAS_RDKIT_DRAW:
        return None
    try:
        img = Draw.MolToImage(mol, size=size)
        return img
    except Exception:
        return None


def get_mol_2d_image_bytes(mol, size=(400, 400)):
    """Generate a 2D image of the molecule as PNG bytes."""
    img = get_mol_2d_image(mol, size)
    if img is None:
        return None
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def get_mol_2d_svg(mol, width=400, height=400):
    """Generate 2D vector SVG using rdMolDraw2D (zero OS C-lib dependency, runs cleanly on Vercel)."""
    if mol is None or not HAS_RDKIT_MOLDRAW2D:
        return None
    try:
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception:
        return None


def generate_3d_coords(mol):
    """Generate 3D coordinates for a molecule."""
    if mol is None:
        return None
    try:
        mol_3d = Chem.AddHs(mol)
        result = AllChem.EmbedMolecule(mol_3d, AllChem.ETKDG())
        if result == -1:
            result = AllChem.EmbedMolecule(mol_3d, randomSeed=42)
        if result == 0:
            AllChem.MMFFOptimizeMolecule(mol_3d)
        return mol_3d
    except Exception:
        return None


def mol_to_molblock(mol_3d):
    """Convert 3D molecule to SDF/Mol block format string for 3Dmol.js viewer."""
    if mol_3d is None:
        return ""
    try:
        return Chem.MolToMolBlock(mol_3d)
    except Exception:
        return ""


def generate_static_3d_image(mol_3d, style="ball_and_stick"):
    """Generate a static matplotlib 3D image of the molecule for PDF or preview."""
    if mol_3d is None:
        return None
    try:
        conf = mol_3d.GetConformer()
        atom_positions = []
        atom_symbols = []
        for i in range(mol_3d.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            atom_positions.append([pos.x, pos.y, pos.z])
            atom_symbols.append(mol_3d.GetAtomWithIdx(i).GetSymbol())

        atom_positions = np.array(atom_positions)

        color_map = {
            "C": "#404040",
            "N": "#3050F8",
            "O": "#FF0D0D",
            "S": "#FFFF30",
            "P": "#FF8000",
            "F": "#90E050",
            "Cl": "#1FF01F",
            "Br": "#A62929",
            "I": "#940094",
            "H": "#CCCCCC",
        }

        fig = plt.figure(figsize=(5, 4), dpi=120)
        ax = fig.add_subplot(111, projection="3d")

        for i, (pos, sym) in enumerate(zip(atom_positions, atom_symbols)):
            c = color_map.get(sym, "#808080")
            s = 30 if sym == "H" else 80
            if style == "space_filling":
                s *= 3
            ax.scatter(*pos, c=c, s=s, edgecolors="black", linewidths=0.5, alpha=0.9)

        if style != "space_filling":
            for bond in mol_3d.GetBonds():
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()
                p1 = atom_positions[i]
                p2 = atom_positions[j]
                lw = 1.5 if style == "wireframe" else 2.5
                ax.plot(
                    [p1[0], p2[0]],
                    [p1[1], p2[1]],
                    [p1[2], p2[2]],
                    color="gray",
                    linewidth=lw,
                    alpha=0.7,
                )

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("3D Molecular Structure", fontsize=10)

        ax.grid(True, alpha=0.3)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None


def count_sigma_pi_bonds(mol):
    """Count sigma and pi bonds in a molecule."""
    if mol is None:
        return 0, 0
    sigma = 0
    pi = 0
    for bond in mol.GetBonds():
        bt = bond.GetBondType()
        if bt == Chem.rdchem.BondType.SINGLE:
            sigma += 1
        elif bt == Chem.rdchem.BondType.DOUBLE:
            sigma += 1
            pi += 1
        elif bt == Chem.rdchem.BondType.TRIPLE:
            sigma += 1
            pi += 2
        elif bt == Chem.rdchem.BondType.AROMATIC:
            sigma += 1
            pi += 0.5
    return int(sigma), round(pi)


def calculate_all_properties(mol):
    """Calculate a comprehensive set of 21 molecular properties."""
    if mol is None:
        return {}

    sigma, pi = count_sigma_pi_bonds(mol)

    props = {
        "Molecular Formula": rdMolDescriptors.CalcMolFormula(mol),
        "Molecular Weight (g/mol)": round(Descriptors.MolWt(mol), 3),
        "Exact Mass": round(Descriptors.ExactMolWt(mol), 4),
        "LogP": round(Descriptors.MolLogP(mol), 3),
        "TPSA (Å²)": round(Descriptors.TPSA(mol), 2),
        "Number of Atoms": mol.GetNumAtoms(),
        "Number of Heavy Atoms": mol.GetNumHeavyAtoms(),
        "Number of Bonds": mol.GetNumBonds(),
        "σ (Sigma) Bonds": sigma,
        "π (Pi) Bonds": pi,
        "H-Bond Donors": Descriptors.NumHDonors(mol),
        "H-Bond Acceptors": Descriptors.NumHAcceptors(mol),
        "Rotatable Bonds": Descriptors.NumRotatableBonds(mol),
        "Aromatic Rings": Descriptors.NumAromaticRings(mol),
        "Number of Rings": Descriptors.RingCount(mol),
        "Fraction Csp3": round(Descriptors.FractionCSP3(mol), 3),
        "Molar Refractivity": round(Crippen.MolMR(mol), 3),
        "Number of Radical Electrons": Descriptors.NumRadicalElectrons(mol),
        "Number of Valence Electrons": Descriptors.NumValenceElectrons(mol),
        "Formal Charge": Chem.GetFormalCharge(mol),
        "Complexity (BertzCT)": round(Descriptors.BertzCT(mol), 2),
    }
    return props


def get_interpretation(props):
    """Generate interpretation text based on property values."""
    lines = []
    mw = props.get("Molecular Weight (g/mol)", 0)
    logp = props.get("LogP", 0)
    tpsa = props.get("TPSA (Å²)", 0)
    hbd = props.get("H-Bond Donors", 0)
    hba = props.get("H-Bond Acceptors", 0)
    rb = props.get("Rotatable Bonds", 0)

    if mw <= 500:
        lines.append(f"Molecular Weight ({mw:.1f} g/mol): Within Lipinski's limit (≤500), favorable for oral absorption.")
    else:
        lines.append(f"Molecular Weight ({mw:.1f} g/mol): Exceeds Lipinski's limit (>500), may have reduced oral bioavailability.")

    if logp < 0:
        lines.append(f"LogP ({logp:.2f}): Negative value indicates the molecule is hydrophilic (water-loving), suggesting good aqueous solubility.")
    elif logp <= 5:
        lines.append(f"LogP ({logp:.2f}): Within acceptable range (≤5), indicating balanced lipophilicity for membrane permeation.")
    else:
        lines.append(f"LogP ({logp:.2f}): Exceeds Lipinski's limit (>5), suggesting high lipophilicity and possible poor solubility.")

    if tpsa < 60:
        lines.append(f"TPSA ({tpsa:.1f} Å²): Low polarity, suggesting good cell membrane permeability but potentially low aqueous solubility.")
    elif tpsa <= 140:
        lines.append(f"TPSA ({tpsa:.1f} Å²): Moderate polarity, favorable for oral bioavailability.")
    else:
        lines.append(f"TPSA ({tpsa:.1f} Å²): High polarity (>140), may have difficulty crossing cell membranes.")

    if hbd <= 5:
        lines.append(f"H-Bond Donors ({hbd}): Within Lipinski's limit (≤5).")
    else:
        lines.append(f"H-Bond Donors ({hbd}): Exceeds Lipinski's limit (>5).")

    if hba <= 10:
        lines.append(f"H-Bond Acceptors ({hba}): Within Lipinski's limit (≤10).")
    else:
        lines.append(f"H-Bond Acceptors ({hba}): Exceeds Lipinski's limit (>10).")

    if rb <= 10:
        lines.append(f"Rotatable Bonds ({rb}): Good molecular flexibility for binding.")
    else:
        lines.append(f"Rotatable Bonds ({rb}): High flexibility (>10), may reduce binding selectivity.")

    violations = 0
    if mw > 500: violations += 1
    if logp > 5: violations += 1
    if hbd > 5: violations += 1
    if hba > 10: violations += 1

    if violations == 0:
        lines.append(f"\n✅ Lipinski Rule of 5: PASS (0 violations) — Molecule is predicted to be orally active.")
    elif violations == 1:
        lines.append(f"\n⚠️ Lipinski Rule of 5: {violations} violation — Molecule may still be orally bioavailable.")
    else:
        lines.append(f"\n❌ Lipinski Rule of 5: {violations} violations — Molecule is predicted to have poor oral bioavailability.")

    return "\n".join(lines)


def lipinski_violations(mol):
    """Count Lipinski Rule of 5 violations."""
    if mol is None:
        return 4
    v = 0
    if Descriptors.MolWt(mol) > 500: v += 1
    if Descriptors.MolLogP(mol) > 5: v += 1
    if Descriptors.NumHDonors(mol) > 5: v += 1
    if Descriptors.NumHAcceptors(mol) > 10: v += 1
    return v


# ============================================================================
# PDF GENERATION — 10-PAGE COMPREHENSIVE EXPERIMENT REPORT
# ============================================================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        logo_path = os.path.join(BASE_DIR, "assets", "srm_logo.png")

        if self._pageNumber > 1:
            if os.path.exists(logo_path):
                try:
                    self.drawImage(logo_path, 1.4 * cm, 29.7 * cm - 1.55 * cm, width=2.6 * cm, height=1.25 * cm, mask="auto", preserveAspectRatio=True)
                except Exception:
                    pass
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#2e8b57"))
            self.drawString(4.3 * cm, 29.7 * cm - 0.95 * cm, "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#555555"))
            self.drawString(4.3 * cm, 29.7 * cm - 1.35 * cm, "Cheminformatics Virtual Laboratory — Student Molecular Analysis Report")
            self.drawRightString(21.0 * cm - 1.4 * cm, 29.7 * cm - 1.15 * cm, "TIRUCHIRAPPALLI CAMPUS")
            self.setStrokeColor(colors.HexColor("#2e8b57"))
            self.setLineWidth(0.8)
            self.line(1.4 * cm, 29.7 * cm - 1.6 * cm, 21.0 * cm - 1.4 * cm, 29.7 * cm - 1.6 * cm)

        self.setStrokeColor(colors.HexColor("#bdc3c7"))
        self.setLineWidth(0.5)
        self.line(1.4 * cm, 1.2 * cm, 21.0 * cm - 1.4 * cm, 1.2 * cm)
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(1.4 * cm, 0.8 * cm, "Department of Cybersecurity • Varshini A & Vismitha Parasa • SRMIST Trichy")
        self.drawRightString(21.0 * cm - 1.4 * cm, 0.8 * cm, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def get_interpretation_compact(props, mol):
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    rb = Descriptors.NumRotatableBonds(mol)

    viol = 0
    if mw > 500: viol += 1
    if logp > 5: viol += 1
    if hbd > 5: viol += 1
    if hba > 10: viol += 1

    lines = []
    if viol == 0:
        lip_txt = "Compliant (0 violations) — Drug-like candidate"
    else:
        lip_txt = f"{viol} violation(s) detected"
    lines.append(f"<b>Bioavailability & Lipinski Rule:</b> {lip_txt} (MW: {mw:.1f}, LogP: {logp:.2f}, HBD: {hbd}, HBA: {hba}).")

    if tpsa <= 140:
        pol_txt = "Optimal for cellular permeability"
    else:
        pol_txt = "High polarity, may hinder membrane transport"
    lines.append(f"<b>Polarity & Permeation:</b> TPSA is {tpsa:.1f} Å² ({pol_txt}). Rotatable bonds: {rb} (conformational flexibility).")

    if logp < 0:
        sol_txt = "hydrophilic character favorable for aqueous solubility"
    elif logp <= 5:
        sol_txt = "balanced lipophilicity for physiological membranes"
    else:
        sol_txt = "lipophilic character with potential solubility limits"
    lines.append(f"<b>Solubility Profile:</b> LogP of {logp:.2f} indicates {sol_txt}.")
    return lines


def build_pdf_report(student_name, reg_no, molecules_data, style_3d="ball_and_stick"):
    """Build a comprehensive 10-page multi-molecule PDF report."""
    cohort_defaults = [
        ("Aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O"),
        ("Caffeine", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"),
        ("Paracetamol", "CC(=O)NC1=CC=C(O)C=C1"),
        ("Ibuprofen", "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"),
        ("Glucose", "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)O)O)O)O)O"),
        ("Ethanol", "CCO"),
        ("Benzene", "c1ccccc1"),
    ]

    working_molecules = list(molecules_data)
    current_smiles_set = {m.get("smiles") for m in working_molecules}

    for dname, dsmi in cohort_defaults:
        if len(working_molecules) >= 7:
            break
        if dsmi not in current_smiles_set:
            dmol = validate_smiles(dsmi)
            if dmol:
                dprops = calculate_all_properties(dmol)
                working_molecules.append({
                    "name": dname,
                    "smiles": dsmi,
                    "mol": dmol,
                    "properties": dprops,
                    "interpretation": get_interpretation(dprops),
                })
                current_smiles_set.add(dsmi)

    cohort_7 = working_molecules[:7]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.4 * cm,
    )
    styles = getSampleStyleSheet()

    tbl_pstyle = ParagraphStyle("tblp", fontSize=6.8, leading=8.5)
    tbl_hstyle = ParagraphStyle("tblh", fontSize=7, leading=8.5, textColor=colors.white)

    story = []
    logo_path = os.path.join(BASE_DIR, "assets", "srm_logo.png")

    # PAGE 1: TITLE & COVER
    if os.path.exists(logo_path):
        logo_rl = RLImage(logo_path, width=4.6 * cm, height=2.3 * cm)
    else:
        logo_rl = Paragraph("<b>SRM LOGO</b>", ParagraphStyle("no_logo", fontSize=12))

    header_tbl = Table([
        [
            logo_rl,
            Table([
                [Paragraph("<b>SRM INSTITUTE OF SCIENCE AND TECHNOLOGY</b>", ParagraphStyle("H1", fontSize=14, leading=17, textColor=colors.HexColor("#1b4d32")))],
                [Paragraph("<b>TIRUCHIRAPPALLI CAMPUS</b>", ParagraphStyle("H2", fontSize=10.5, leading=13, textColor=colors.HexColor("#2e8b57")))],
                [Paragraph("FACULTY OF ENGINEERING AND TECHNOLOGY • DEPARTMENT OF CYBERSECURITY", ParagraphStyle("H3", fontSize=8, leading=10, textColor=colors.HexColor("#555555")))],
                [Paragraph("<b>CHEMINFORMATICS VIRTUAL LABORATORY</b>", ParagraphStyle("H4", fontSize=9.5, leading=12, textColor=colors.HexColor("#2e8b57")))],
            ], colWidths=[13.4 * cm])
        ]
    ], colWidths=[4.8 * cm, 13.4 * cm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4 * mm))

    title_tbl = Table([
        [Paragraph("<b>MULTI-MOLECULE STUDENT ANALYSIS & RESEARCH REPORT</b>", ParagraphStyle("DT", alignment=TA_CENTER, fontSize=12, leading=15, textColor=colors.white))]
    ], colWidths=[18.2 * cm])
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2e8b57")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 4 * mm))

    student_data = [
        [Paragraph("<b>Student Name</b>", ParagraphStyle("c1", fontSize=8.5, textColor=colors.white)), Paragraph("<b>Registration No.</b>", ParagraphStyle("c2", fontSize=8.5, textColor=colors.white)), Paragraph("<b>Email ID</b>", ParagraphStyle("c3", fontSize=8.5, textColor=colors.white))],
        [Paragraph(f"<b>{student_name}</b>", ParagraphStyle("s1", fontSize=8.5)), Paragraph(str(reg_no), ParagraphStyle("s2", fontSize=8.5)), Paragraph("va3375@srmist.edu.in", ParagraphStyle("s3", fontSize=8.5))],
        [Paragraph("<b>Vismitha Parasa</b>", ParagraphStyle("s4", fontSize=8.5)), Paragraph("RA2611030050047", ParagraphStyle("s5", fontSize=8.5)), Paragraph("vp8717@srmist.edu.in", ParagraphStyle("s6", fontSize=8.5))],
    ]
    std_tbl = Table(student_data, colWidths=[6.0 * cm, 5.2 * cm, 7.0 * cm])
    std_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b4d32")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f6")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(std_tbl)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("<b>Laboratory Experiment Abstract</b>", ParagraphStyle("absh", fontSize=10, leading=12, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 1.5 * mm))
    story.append(Paragraph(
        "This laboratory report compiles a systematic cheminformatics study conducted using computational tools including RDKit, 3Dmol.js, Matplotlib, and Flask. A curated cohort of seven representative organic compounds (Aspirin, Caffeine, Paracetamol, Ibuprofen, Glucose, Ethanol, and Benzene) was evaluated across 21 molecular descriptors encompassing structural, topological, electronic, and physicochemical dimensions. Conformer models were optimized using the Merck Molecular Force Field (MMFF94) following distance geometry embedding (ETKDG). Drug-likeness and membrane permeability were assessed using Lipinski’s Rule of Five and Veber criteria, establishing a comprehensive reference for virtual screening and structure-property correlation.",
        ParagraphStyle("absb", fontSize=8, leading=11, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("<b>Report Structure & Table of Contents (10 Pages)</b>", ParagraphStyle("toch", fontSize=10, leading=12, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 1.5 * mm))
    toc_data = [
        [Paragraph("<b>Page</b>", ParagraphStyle("tc1", fontSize=7.5, textColor=colors.white)), Paragraph("<b>Section / Compound</b>", ParagraphStyle("tc2", fontSize=7.5, textColor=colors.white)), Paragraph("<b>Analytical Scope</b>", ParagraphStyle("tc3", fontSize=7.5, textColor=colors.white))],
        [Paragraph("Page 1", ParagraphStyle("t1", fontSize=7.5)), Paragraph("Title & Student Metadata", ParagraphStyle("t2", fontSize=7.5)), Paragraph("Executive Overview, Methodology, Objectives", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 2", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 1: {cohort_7[0].get('name', 'Compound 1')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 3", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 2: {cohort_7[1].get('name', 'Compound 2')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 4", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 3: {cohort_7[2].get('name', 'Compound 3')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 5", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 4: {cohort_7[3].get('name', 'Compound 4')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 6", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 5: {cohort_7[4].get('name', 'Compound 5')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 7", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 6: {cohort_7[5].get('name', 'Compound 6')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 8", ParagraphStyle("t1", fontSize=7.5)), Paragraph(f"Compound 7: {cohort_7[6].get('name', 'Compound 7')}", ParagraphStyle("t2", fontSize=7.5)), Paragraph("2D/3D Conformation, 21 Descriptors, Bioavailability", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 9", ParagraphStyle("t1", fontSize=7.5)), Paragraph("Comparative Analysis", ParagraphStyle("t2", fontSize=7.5)), Paragraph("Multi-Molecule Matrix, Lipinski Space Scatter Chart", ParagraphStyle("t3", fontSize=7.5))],
        [Paragraph("Page 10", ParagraphStyle("t1", fontSize=7.5)), Paragraph("Summary & Sign-off", ParagraphStyle("t2", fontSize=7.5)), Paragraph("Technological Stack, Code Script, Evaluation Signatures", ParagraphStyle("t3", fontSize=7.5))],
    ]
    toc_tbl = Table(toc_data, colWidths=[2.2 * cm, 5.5 * cm, 10.5 * cm])
    toc_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e8b57")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f6")]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())

    # PAGES 2 to 8: 7 MOLECULES
    mol_objects_for_page9 = []

    for idx, minfo in enumerate(cohort_7, 1):
        cname = minfo.get("name", f"Compound {idx}")
        csmi = minfo.get("smiles", "")
        cmol = minfo.get("mol")
        cprops = minfo.get("properties") or calculate_all_properties(cmol)
        interp_lines = get_interpretation_compact(cprops, cmol)

        mol_objects_for_page9.append((cname, csmi, cmol, cprops))

        story.append(Paragraph(f"<b>Molecule {idx} of 7: {cname}</b> &nbsp;&nbsp;|&nbsp;&nbsp; SMILES: <code>{csmi}</code>", ParagraphStyle("mh", fontSize=10.5, leading=13, textColor=colors.HexColor("#1b4d32"))))
        story.append(Spacer(1, 1.5 * mm))

        img2d_buf = get_mol_2d_image_bytes(cmol, size=(280, 210))
        cmol_3d = generate_3d_coords(cmol)
        img3d_buf = generate_static_3d_image(cmol_3d, style=style_3d)

        img2d_cell = RLImage(img2d_buf, width=7.2 * cm, height=4.6 * cm) if img2d_buf else Paragraph(f"<b>2D Structure:</b><br/><code>{csmi}</code>", ParagraphStyle("no_2d", fontSize=8, alignment=TA_CENTER))
        img3d_cell = RLImage(img3d_buf, width=7.2 * cm, height=4.6 * cm) if img3d_buf else Paragraph("<b>3D Model Conformer</b>", ParagraphStyle("no_3d", fontSize=8, alignment=TA_CENTER))

        img_row = Table([
            [Paragraph("<b>2D Chemical Structure</b>", ParagraphStyle("l1", alignment=TA_CENTER, fontSize=7.5)), Paragraph("<b>3D Molecular Model (Conformer)</b>", ParagraphStyle("l2", alignment=TA_CENTER, fontSize=7.5))],
            [img2d_cell, img3d_cell]
        ], colWidths=[9.1 * cm, 9.1 * cm])
        img_row.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(img_row)
        story.append(Spacer(1, 1.5 * mm))

        items = list(cprops.items())
        half = (len(items) + 1) // 2
        c1_items = items[:half]
        c2_items = items[half:]

        p_rows = [[
            Paragraph("<b>Descriptor</b>", tbl_hstyle), Paragraph("<b>Value</b>", tbl_hstyle),
            Paragraph("<b>Descriptor</b>", tbl_hstyle), Paragraph("<b>Value</b>", tbl_hstyle),
        ]]
        for i in range(half):
            p1, v1 = c1_items[i]
            p2, v2 = c2_items[i] if i < len(c2_items) else ("", "")
            p_rows.append([
                Paragraph(str(p1), tbl_pstyle), Paragraph(str(v1), tbl_pstyle),
                Paragraph(str(p2), tbl_pstyle), Paragraph(str(v2), tbl_pstyle),
            ])

        ptbl = Table(p_rows, colWidths=[5.0 * cm, 4.1 * cm, 5.0 * cm, 4.1 * cm])
        ptbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e8b57")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bdc3c7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f6")]),
            ("TOPPADDING", (0, 0), (-1, -1), 1.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(ptbl)
        story.append(Spacer(1, 2 * mm))

        story.append(Paragraph("<b>Cheminformatics & Pharmacological Interpretation:</b>", ParagraphStyle("inh", fontSize=8.5, leading=10, textColor=colors.HexColor("#1b4d32"))))
        story.append(Spacer(1, 1 * mm))
        for iline in interp_lines:
            story.append(Paragraph(iline, ParagraphStyle("inb", fontSize=7.2, leading=9.2, alignment=TA_JUSTIFY)))
            story.append(Spacer(1, 0.5 * mm))

        story.append(PageBreak())

    # PAGE 9: COMPARATIVE ANALYSIS
    story.append(Paragraph("<b>Comparative Structure–Property Analysis (7 Molecules)</b>", ParagraphStyle("cph", fontSize=12, leading=15, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "A multi-compound matrix correlating molecular weight, lipophilicity (LogP), topological polar surface area (TPSA), hydrogen bond donor/acceptor counts, rotatable bonds, and Lipinski Rule of 5 violations across all analyzed structures.",
        ParagraphStyle("cpb", fontSize=7.8, leading=10.5, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 2.5 * mm))

    comp_headers = [
        Paragraph("<b>Compound</b>", tbl_hstyle), Paragraph("<b>MW (g/mol)</b>", tbl_hstyle),
        Paragraph("<b>LogP</b>", tbl_hstyle), Paragraph("<b>TPSA (Å²)</b>", tbl_hstyle),
        Paragraph("<b>HBD</b>", tbl_hstyle), Paragraph("<b>HBA</b>", tbl_hstyle),
        Paragraph("<b>Rot.B</b>", tbl_hstyle), Paragraph("<b>Arom.R</b>", tbl_hstyle),
        Paragraph("<b>Lipinski Viol.</b>", tbl_hstyle),
    ]
    comp_rows = [comp_headers]

    names_list, mw_list, logp_list = [], [], []
    for name, smi, mol, _ in mol_objects_for_page9:
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        rb = Descriptors.NumRotatableBonds(mol)
        ar = Descriptors.NumAromaticRings(mol)

        viol = 0
        if mw > 500: viol += 1
        if logp > 5: viol += 1
        if hbd > 5: viol += 1
        if hba > 10: viol += 1

        names_list.append(name)
        mw_list.append(mw)
        logp_list.append(logp)

        viol_text = "0 (Pass)" if viol == 0 else f"{viol} Viol."
        comp_rows.append([
            Paragraph(name, tbl_pstyle), Paragraph(f"{mw:.1f}", tbl_pstyle),
            Paragraph(f"{logp:.2f}", tbl_pstyle), Paragraph(f"{tpsa:.1f}", tbl_pstyle),
            Paragraph(str(hbd), tbl_pstyle), Paragraph(str(hba), tbl_pstyle),
            Paragraph(str(rb), tbl_pstyle), Paragraph(str(ar), tbl_pstyle),
            Paragraph(viol_text, tbl_pstyle),
        ])

    comp_tbl = Table(comp_rows, colWidths=[3.2 * cm, 2.0 * cm, 1.8 * cm, 2.0 * cm, 1.5 * cm, 1.5 * cm, 1.6 * cm, 1.8 * cm, 2.8 * cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e8b57")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f6")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(comp_tbl)
    story.append(Spacer(1, 3 * mm))

    fig, ax = plt.subplots(figsize=(6.8, 3.2), dpi=110)
    ax.scatter(mw_list, logp_list, s=70, c="#2e8b57", edgecolors="black", linewidths=0.5, zorder=3)
    for n, x, y in zip(names_list, mw_list, logp_list):
        ax.annotate(n, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7.5, fontweight="bold")
    ax.axhline(y=5, color="#c0392b", linestyle="--", linewidth=0.8, alpha=0.7, label="Lipinski Max LogP (5.0)")
    ax.axvline(x=500, color="#c0392b", linestyle="--", linewidth=0.8, alpha=0.7, label="Lipinski Max MW (500 g/mol)")
    ax.set_xlabel("Molecular Weight (g/mol)", fontsize=8)
    ax.set_ylabel("LogP (Octanol-Water Partition)", fontsize=8)
    ax.set_title("Lipinski Chemical Space: MW vs LogP Distribution", fontsize=9, fontweight="bold", color="#1b4d32")
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, loc="upper left")
    plt.tight_layout(pad=0.4)
    scatter_buf = BytesIO()
    fig.savefig(scatter_buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    scatter_buf.seek(0)

    scatter_img = RLImage(scatter_buf, width=13.0 * cm, height=6.0 * cm)
    scatter_tbl = Table([[scatter_img]], colWidths=[18.2 * cm])
    scatter_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(scatter_tbl)
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph(
        "<b>Scatter Chart Interpretation:</b> All seven compounds reside well within the Lipinski MW boundary (≤ 500 g/mol) and LogP boundary (≤ 5.0). Glucose demonstrates notable hydrophilicity (negative LogP) driven by five hydroxyl groups, whereas Aspirin, Paracetamol, and Ibuprofen occupy ideal oral drug-like space.",
        ParagraphStyle("scb", fontSize=7.2, leading=9.5, alignment=TA_JUSTIFY)
    ))
    story.append(PageBreak())

    # PAGE 10: METHODOLOGY, CODE & SIGN-OFF
    story.append(Paragraph("<b>Technological Architecture, References & Sign-off</b>", ParagraphStyle("p10h", fontSize=12, leading=15, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 2 * mm))

    tech_data = [
        [Paragraph("<b>Software Framework</b>", tbl_hstyle), Paragraph("<b>Role in Virtual Laboratory Pipeline</b>", tbl_hstyle)],
        [Paragraph("<b>RDKit (C++ / Python)</b>", tbl_pstyle), Paragraph("SMILES parsing, valence verification, 2D depictions, 21 descriptor calculations, ETKDG 3D embedding, MMFF94 force field geometry optimization.", tbl_pstyle)],
        [Paragraph("<b>3Dmol.js & WebGL</b>", tbl_pstyle), Paragraph("WebGL-accelerated interactive 3D molecular surface rendering directly inside modern web browser sessions.", tbl_pstyle)],
        [Paragraph("<b>Flask Web Server</b>", tbl_pstyle), Paragraph("High-performance Python web application server providing REST APIs, multi-page routing, and responsive client-server execution.", tbl_pstyle)],
        [Paragraph("<b>Matplotlib 3D (mplot3d)</b>", tbl_pstyle), Paragraph("Static rendering of 3D molecular conformers with atomic CPK color-mapping for high-resolution vector PDF export.", tbl_pstyle)],
        [Paragraph("<b>ReportLab Plus</b>", tbl_pstyle), Paragraph("Dynamic PDF generation with dual-pass NumberedCanvas pagination, custom grid flowables, and institutional headers.", tbl_pstyle)],
        [Paragraph("<b>Pandas & NumPy</b>", tbl_pstyle), Paragraph("Matrix computations for atomic coordinate transformations and CSV descriptor export.", tbl_pstyle)],
    ]
    tech_tbl = Table(tech_data, colWidths=[5.0 * cm, 13.2 * cm])
    tech_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e8b57")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f6")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tech_tbl)
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("<b>Core Python Script Execution:</b>", ParagraphStyle("csh", fontSize=8.5, leading=10, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 1 * mm))
    code_str = """from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem
# Parse molecule & calculate key descriptors
mol = Chem.MolFromSmiles('CC(=O)OC1=CC=CC=C1C(=O)O')
mw, logp = Descriptors.MolWt(mol), Descriptors.MolLogP(mol)
# Generate 3D conformer with ETKDG and optimize using MMFF94
mol_3d = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol_3d, AllChem.ETKDG())
AllChem.MMFFOptimizeMolecule(mol_3d)"""

    story.append(Paragraph(f'<font face="Courier" size="6.5">{code_str.replace(chr(10), "<br/>")}</font>', ParagraphStyle("csb", backColor=colors.HexColor("#f5f9f6"), borderColor=colors.HexColor("#2e8b57"), borderWidth=0.5, borderPadding=5, leading=8.5)))
    story.append(Spacer(1, 3.5 * mm))

    story.append(Paragraph("<b>Laboratory Conclusions & Learning Outcomes:</b>", ParagraphStyle("lch", fontSize=8.5, leading=10, textColor=colors.HexColor("#1b4d32"))))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        "Through this virtual experiment, we successfully integrated computational cheminformatics tools to model, calculate, and evaluate molecular architectures. Quantitative topological and electronic descriptors provided robust indicators of pharmacological viability. The project illustrates how modern in silico pipelines drastically reduce experimental screening costs while advancing molecular understanding.",
        ParagraphStyle("lcb", fontSize=7.2, leading=9.5, alignment=TA_JUSTIFY)
    ))
    story.append(Spacer(1, 4 * mm))

    sig_data = [
        [Paragraph("<b>Prepared & Submitted By:</b>", ParagraphStyle("sgh1", fontSize=7.5, textColor=colors.HexColor("#1b4d32"))), Paragraph("<b>Faculty Verification & Grade:</b>", ParagraphStyle("sgh2", fontSize=7.5, textColor=colors.HexColor("#1b4d32")))],
        [
            Paragraph("<b>Varshini A</b> (RA2611030050040)<br/><b>Vismitha Parasa</b> (RA2611030050047)<br/>Department of Cybersecurity, SRMIST Trichy", ParagraphStyle("sg1", fontSize=7.2, leading=9)),
            Paragraph("Evaluated by: ____________________________<br/>Marks / Grade: ________ / ________<br/>Signature & Date: ________________________", ParagraphStyle("sg2", fontSize=7.2, leading=9))
        ]
    ]
    sig_tbl = Table(sig_data, colWidths=[9.1 * cm, 9.1 * cm])
    sig_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#2e8b57")),
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#2e8b57")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f9f6")),
    ]))
    story.append(sig_tbl)

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf


# ============================================================================
# QUIZ QUESTIONS (24 total)
# ============================================================================
QUIZ_QUESTIONS = [
    {
        "q": "What does SMILES stand for?",
        "options": [
            "Simplified Molecular Input Line Entry System",
            "Standard Molecular Identification Line Entry System",
            "Simplified Molecular Identification Line Entry Specification",
            "Standard Molecular Input Line Entry Specification",
        ],
        "answer": 0,
    },
    {
        "q": "Which Python library is primarily used for cheminformatics tasks like parsing SMILES and calculating molecular descriptors?",
        "options": ["NumPy", "RDKit", "SciPy", "TensorFlow"],
        "answer": 1,
    },
    {
        "q": "What is the SMILES notation for benzene?",
        "options": ["C6H6", "c1ccccc1", "C=C=C=C=C=C", "CCCCCC"],
        "answer": 1,
    },
    {
        "q": "LogP is a measure of:",
        "options": [
            "Molecular weight",
            "Boiling point",
            "Partition coefficient (lipophilicity)",
            "Number of hydrogen bonds",
        ],
        "answer": 2,
    },
    {
        "q": "According to Lipinski's Rule of 5, the molecular weight should be:",
        "options": ["≤ 300", "≤ 400", "≤ 500", "≤ 600"],
        "answer": 2,
    },
    {
        "q": "TPSA stands for:",
        "options": [
            "Total Polar Surface Area",
            "Topological Polar Surface Analysis",
            "Total Polarity Surface Area",
            "Topological Polar Spatial Area",
        ],
        "answer": 0,
    },
    {
        "q": "Which 3D model represents atoms as spheres filling their van der Waals radii?",
        "options": ["Wireframe", "Ball and Stick", "Stick", "Space Filling"],
        "answer": 3,
    },
    {
        "q": "A molecule with LogP < 0 is considered:",
        "options": ["Lipophilic", "Hydrophilic", "Amphiphilic", "Neutral"],
        "answer": 1,
    },
    {
        "q": "The number of hydrogen bond donors allowed by Lipinski's Rule is:",
        "options": ["≤ 3", "≤ 5", "≤ 7", "≤ 10"],
        "answer": 1,
    },
    {
        "q": "Which of these is NOT a molecular descriptor?",
        "options": ["LogP", "TPSA", "HTML", "Molecular Weight"],
        "answer": 2,
    },
    {
        "q": "In SMILES notation, '=' represents:",
        "options": [
            "Single bond",
            "Double bond",
            "Triple bond",
            "Aromatic bond",
        ],
        "answer": 1,
    },
    {
        "q": "What is the purpose of the ETKDG method in RDKit?",
        "options": [
            "Calculate molecular weight",
            "Generate 3D conformer coordinates",
            "Parse SMILES strings",
            "Draw 2D structures",
        ],
        "answer": 1,
    },
    {
        "q": "In SMILES, '#' represents:",
        "options": [
            "A comment",
            "A triple bond",
            "An aromatic ring",
            "A branch",
        ],
        "answer": 1,
    },
    {
        "q": "Which descriptor measures the total surface area of polar atoms in a molecule?",
        "options": ["LogP", "Molar Refractivity", "TPSA", "BertzCT"],
        "answer": 2,
    },
    {
        "q": "The SMILES notation for ethanol is:",
        "options": ["C2H5OH", "CCO", "C=CO", "COC"],
        "answer": 1,
    },
    {
        "q": "Lipinski's Rule of 5 predicts:",
        "options": [
            "Chemical reactivity",
            "Oral bioavailability / drug-likeness",
            "Melting point",
            "UV absorption",
        ],
        "answer": 1,
    },
    {
        "q": "In a Ball-and-Stick model:",
        "options": [
            "Only bonds are shown",
            "Atoms are spheres connected by sticks representing bonds",
            "Atoms fill their van der Waals radii",
            "Only atoms are shown",
        ],
        "answer": 1,
    },
    {
        "q": "A sigma (σ) bond is formed by:",
        "options": [
            "Lateral overlap of orbitals",
            "Head-on overlap of orbitals",
            "No orbital overlap",
            "Electrostatic attraction only",
        ],
        "answer": 1,
    },
    {
        "q": "Which library is used for interactive 3D molecular visualization in the browser?",
        "options": ["Matplotlib", "py3Dmol", "Seaborn", "Plotly"],
        "answer": 1,
    },
    {
        "q": "How many hydrogen bond acceptors does Lipinski's Rule allow?",
        "options": ["≤ 5", "≤ 8", "≤ 10", "≤ 15"],
        "answer": 2,
    },
    {
        "q": "Molar Refractivity is related to:",
        "options": [
            "Molecular polarizability and volume",
            "Boiling point only",
            "Number of atoms only",
            "Electronegativity",
        ],
        "answer": 0,
    },
    {
        "q": "In SMILES, branches are denoted by:",
        "options": [
            "Square brackets []",
            "Parentheses ()",
            "Curly braces {}",
            "Angle brackets <>",
        ],
        "answer": 1,
    },
    {
        "q": "What does a high TPSA value (>140 Å²) suggest about a molecule?",
        "options": [
            "Excellent membrane permeability",
            "High lipophilicity",
            "Poor cell membrane permeability",
            "Low molecular weight",
        ],
        "answer": 2,
    },
    {
        "q": "The Fraction Csp3 descriptor indicates:",
        "options": [
            "The fraction of carbon atoms that are sp3 hybridized",
            "The fraction of hydrogen atoms",
            "The ratio of sigma to pi bonds",
            "The percentage of aromatic atoms",
        ],
        "answer": 0,
    },
    {
        "q": "MMFF in RDKit stands for:",
        "options": [
            "Molecular Mechanics Force Field",
            "Merck Molecular Force Field",
            "Modified Molecular Fragment Field",
            "Macro Molecular Functional Field",
        ],
        "answer": 1,
    },
]


# ============================================================================
# FLASK ROUTING & REST APIS
# ============================================================================
@app.route("/")
def index():
    ex_items = list(EXAMPLE_MOLECULES.items())
    return render_template(
        "index.html",
        example_molecules=EXAMPLE_MOLECULES,
        example_molecules_row1=ex_items[:5],
        example_molecules_row2=ex_items[5:],
        quiz_questions=QUIZ_QUESTIONS,
    )


@app.route("/assets/<path:filename>")
def serve_asset(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


@app.route("/api/validate", methods=["POST"])
def api_validate():
    data = request.get_json() or {}
    smiles = data.get("smiles", "")
    mol = validate_smiles(smiles)
    if mol is None:
        return jsonify({"valid": False, "error": "Invalid SMILES string"})
    
    sigma, pi = count_sigma_pi_bonds(mol)
    formula = rdMolDescriptors.CalcMolFormula(mol)
    return jsonify({
        "valid": True,
        "smiles": smiles,
        "formula": formula,
        "heavy_atoms": mol.GetNumHeavyAtoms(),
        "total_atoms": mol.GetNumAtoms(),
        "bonds": mol.GetNumBonds(),
        "sigma_bonds": sigma,
        "pi_bonds": pi,
        "aromatic_rings": Descriptors.NumAromaticRings(mol),
        "total_rings": Descriptors.RingCount(mol),
        "mw": round(Descriptors.MolWt(mol), 3),
        "exact_mass": round(Descriptors.ExactMolWt(mol), 4),
        "formal_charge": Chem.GetFormalCharge(mol),
    })


@app.route("/api/mol2d")
def api_mol2d():
    smiles = request.args.get("smiles", "")
    w = int(request.args.get("w", 400))
    h = int(request.args.get("h", 400))
    mol = validate_smiles(smiles)
    if mol is None:
        return Response(status=404)

    # 1. Try standard PNG via Draw.MolToImage
    buf = get_mol_2d_image_bytes(mol, size=(w, h))
    if buf:
        return send_file(buf, mimetype="image/png")

    # 2. Safe headless vector SVG via rdMolDraw2D (zero X11/libXrender dependency, runs cleanly on Vercel)
    svg_text = get_mol_2d_svg(mol, width=w, height=h)
    if svg_text:
        return Response(svg_text, mimetype="image/svg+xml")

    return Response("Could not render molecular structure", status=500)


@app.route("/api/mol3d", methods=["POST"])
def api_mol3d():
    data = request.get_json() or {}
    smiles = data.get("smiles", "")
    mol = validate_smiles(smiles)
    if mol is None:
        return jsonify({"success": False, "error": "Invalid SMILES"})
    
    mol_3d = generate_3d_coords(mol)
    if mol_3d is None:
        return jsonify({"success": False, "error": "Failed to generate 3D coordinates"})
    
    mol_block = mol_to_molblock(mol_3d)
    return jsonify({"success": True, "mol_block": mol_block})


@app.route("/api/mol3d_static")
def api_mol3d_static():
    smiles = request.args.get("smiles", "")
    style = request.args.get("style", "ball_and_stick")
    mol = validate_smiles(smiles)
    if mol is None:
        return Response(status=404)
    mol_3d = generate_3d_coords(mol)
    if mol_3d is None:
        return Response(status=500)
    buf = generate_static_3d_image(mol_3d, style=style)
    if buf is None:
        return Response(status=500)
    return send_file(buf, mimetype="image/png")


@app.route("/api/properties", methods=["POST"])
def api_properties():
    data = request.get_json() or {}
    smiles = data.get("smiles", "")
    mol = validate_smiles(smiles)
    if mol is None:
        return jsonify({"success": False, "error": "Invalid SMILES"})
    
    props = calculate_all_properties(mol)
    interp = get_interpretation(props)
    violations = lipinski_violations(mol)
    
    return jsonify({
        "success": True,
        "smiles": smiles,
        "properties": props,
        "interpretation": interp,
        "lipinski_violations": violations,
    })


@app.route("/api/properties_csv", methods=["POST"])
def api_properties_csv():
    data = request.get_json() or {}
    smiles = data.get("smiles", "")
    mol = validate_smiles(smiles)
    if mol is None:
        return Response("Invalid SMILES", status=400)
    
    props = calculate_all_properties(mol)
    df = pd.DataFrame(list(props.items()), columns=["Property", "Value"])
    csv_str = df.to_csv(index=False)
    
    safe_name = smiles[:20].replace("/", "_").replace("\\", "_")
    return Response(
        csv_str,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=molecular_properties_{safe_name}.csv"}
    )


@app.route("/api/single_pdf", methods=["POST"])
def api_single_pdf():
    data = request.get_json() or {}
    student_name = data.get("student_name", "Varshini A & Vismitha Parasa")
    reg_no = data.get("reg_no", "RA2611030050040 / RA2611030050047")
    smiles = data.get("smiles", "CC(=O)OC1=CC=CC=C1C(=O)O")
    style_3d = data.get("style_3d", "ball_and_stick")
    
    mol = validate_smiles(smiles)
    if mol is None:
        return Response("Invalid SMILES", status=400)
    
    props = calculate_all_properties(mol)
    interp = get_interpretation(props)
    
    mol_data = [{
        "name": "Target Molecule",
        "smiles": smiles,
        "mol": mol,
        "properties": props,
        "interpretation": interp,
    }]
    
    pdf_buf = build_pdf_report(student_name, reg_no, mol_data, style_3d=style_3d)
    safe_smi = smiles[:15].replace("/", "_").replace("\\", "_")
    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"molecular_report_{safe_smi}.pdf"
    )


@app.route("/api/compare", methods=["POST"])
def api_compare():
    data = request.get_json() or {}
    input_text = data.get("input_text", "")
    lines = [l.strip() for l in input_text.strip().split("\n") if l.strip()]
    
    molecules = []
    invalid_lines = []
    
    for line in lines:
        if "," in line:
            parts = line.split(",", 1)
            name, smi = parts[0].strip(), parts[1].strip()
        else:
            smi = line.strip()
            name = f"Compound {len(molecules)+1}"
        
        mol = validate_smiles(smi)
        if mol:
            molecules.append({
                "name": name,
                "smiles": smi,
                "mol": mol,
                "mw": round(Descriptors.MolWt(mol), 2),
                "logp": round(Descriptors.MolLogP(mol), 2),
                "tpsa": round(Descriptors.TPSA(mol), 2),
                "hbd": Descriptors.NumHDonors(mol),
                "hba": Descriptors.NumHAcceptors(mol),
                "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
                "aromatic_rings": Descriptors.NumAromaticRings(mol),
                "heavy_atoms": mol.GetNumHeavyAtoms(),
                "fraction_csp3": round(Descriptors.FractionCSP3(mol), 3),
                "molar_refractivity": round(Crippen.MolMR(mol), 2),
                "lipinski_violations": lipinski_violations(mol),
            })
        else:
            invalid_lines.append(line)
            
    return jsonify({
        "molecules": [
            {k: v for k, v in m.items() if k != "mol"} for m in molecules
        ],
        "invalid_lines": invalid_lines,
    })


@app.route("/api/compare_csv", methods=["POST"])
def api_compare_csv():
    data = request.get_json() or {}
    molecules_data = data.get("molecules", [])
    if not molecules_data:
        return Response("No molecules data provided", status=400)
    
    df = pd.DataFrame(molecules_data)
    csv_str = df.to_csv(index=False)
    return Response(
        csv_str,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=molecule_comparison.csv"}
    )


@app.route("/api/advanced", methods=["POST"])
def api_advanced():
    data = request.get_json() or {}
    smiles_a = data.get("smiles_a", "")
    smiles_b = data.get("smiles_b", "")
    
    mol_a = validate_smiles(smiles_a)
    result = {"mol_a_valid": mol_a is not None}
    
    if mol_a:
        can_smi = Chem.MolToSmiles(mol_a, canonical=True, isomericSmiles=True)
        inchikey = Chem.MolToInchiKey(mol_a)
        inchi = Chem.MolToInchi(mol_a)
        sha256_hash = hashlib.sha256(can_smi.encode()).hexdigest()
        sha3_hash = hashlib.sha3_256(can_smi.encode()).hexdigest()
        md5_hash = hashlib.md5(can_smi.encode()).hexdigest()
        
        result["hashes"] = {
            "canonical_smiles": can_smi,
            "inchikey": inchikey,
            "inchi": inchi,
            "sha256": sha256_hash,
            "sha3_256": sha3_hash,
            "md5": md5_hash,
        }
        
        qed_score = float(QED.qed(mol_a))
        qed_props = QED.properties(mol_a)
        result["qed"] = {
            "score": round(qed_score, 3),
            "mw": round(qed_props.MW, 2),
            "logp": round(qed_props.ALOGP, 2),
            "hbd": qed_props.HBD,
            "hba": qed_props.HBA,
            "tpsa": round(qed_props.PSA, 2),
            "rotatable_bonds": qed_props.ROTB,
            "aromatic_rings": qed_props.AROM,
            "alerts": qed_props.ALERTS,
        }
        
        scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol_a)
        scaffold_smi = Chem.MolToSmiles(scaffold_mol)
        has_scaffold = scaffold_mol.GetNumAtoms() > 0
        result["scaffold"] = {
            "has_scaffold": has_scaffold,
            "scaffold_smiles": scaffold_smi if has_scaffold else None,
        }
        
    mol_b = validate_smiles(smiles_b)
    result["mol_b_valid"] = mol_b is not None
    
    if mol_a and mol_b:
        fp_a = Chem.RDKFingerprint(mol_a)
        fp_b = Chem.RDKFingerprint(mol_b)
        result["similarity"] = {
            "tanimoto": round(float(DataStructs.TanimotoSimilarity(fp_a, fp_b)), 4),
            "dice": round(float(DataStructs.DiceSimilarity(fp_a, fp_b)), 4),
            "cosine": round(float(DataStructs.CosineSimilarity(fp_a, fp_b)), 4),
        }
        
    return jsonify(result)


@app.route("/api/quiz/submit", methods=["POST"])
def api_quiz_submit():
    data = request.get_json() or {}
    user_answers = data.get("answers", {})  # { "0": 1, ... }
    
    score = 0
    total = len(QUIZ_QUESTIONS)
    wrong = []
    
    for i, q in enumerate(QUIZ_QUESTIONS):
        corr_idx = q["answer"]
        corr_opt = q["options"][corr_idx]
        user_val = user_answers.get(str(i))
        
        is_correct = False
        user_display = "(No answer)"
        if user_val is not None:
            user_opt_idx = int(user_val)
            if 0 <= user_opt_idx < len(q["options"]):
                user_display = q["options"][user_opt_idx]
                if user_opt_idx == corr_idx:
                    is_correct = True
        
        if is_correct:
            score += 1
        else:
            wrong.append({
                "index": i + 1,
                "question": q["q"],
                "your_answer": user_display,
                "correct_answer": corr_opt,
            })
            
    pct = round((score / total) * 100, 1)
    return jsonify({
        "score": score,
        "total": total,
        "percentage": pct,
        "wrong": wrong,
    })


@app.route("/api/final_pdf", methods=["POST"])
def api_final_pdf():
    data = request.get_json() or {}
    student_name = data.get("student_name", "Varshini A & Vismitha Parasa")
    reg_no = data.get("reg_no", "RA2611030050040 / RA2611030050047")
    smiles_text = data.get("smiles_text", "")
    style_3d = data.get("style_3d", "ball_and_stick")
    
    if not student_name or not reg_no:
        return Response("Student Name and Registration Number are required", status=400)
    
    lines = [s.strip() for s in smiles_text.strip().split("\n") if s.strip()]
    if not lines:
        return Response("At least one SMILES string is required", status=400)
    
    molecules_data = []
    for i, line in enumerate(lines):
        if "," in line:
            parts = line.split(",", 1)
            cname = parts[0].strip()
            csmi = parts[1].strip()
        else:
            csmi = line.strip()
            cname = f"Compound {i+1}"
            
        mol = validate_smiles(csmi)
        if mol:
            props = calculate_all_properties(mol)
            interp = get_interpretation(props)
            molecules_data.append({
                "name": cname,
                "smiles": csmi,
                "mol": mol,
                "properties": props,
                "interpretation": interp,
            })
            
    if not molecules_data:
        return Response("No valid molecules found to include in report", status=400)
    
    pdf_buf = build_pdf_report(student_name, reg_no, molecules_data, style_3d=style_3d)
    safe_reg = reg_no.replace("/", "_").replace("\\", "_").replace(" ", "_")
    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Student_Report_{safe_reg}.pdf"
    )


if __name__ == "__main__":
    print("=" * 70)
    print("Cheminformatics Virtual Laboratory running on Flask!")
    print("Serving on http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=False)
