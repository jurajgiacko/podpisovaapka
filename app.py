import streamlit as st
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
from datetime import datetime
import base64

st.set_page_config(
    page_title="PDF Podpisovač",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0f0f0f;
        --bg-secondary: #1a1a1a;
        --bg-tertiary: #252525;
        --accent-primary: #00d4aa;
        --accent-secondary: #00a688;
        --accent-glow: rgba(0, 212, 170, 0.3);
        --text-primary: #ffffff;
        --text-secondary: #a0a0a0;
        --border-color: #333333;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0a1628 50%, var(--bg-primary) 100%);
        font-family: 'Outfit', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 3rem;
        background: linear-gradient(135deg, #00d4aa 0%, #00ffcc 50%, #00a688 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    .signature-card {
        background: linear-gradient(145deg, rgba(26, 26, 26, 0.9), rgba(15, 15, 15, 0.9));
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .signature-card h3 {
        color: var(--accent-primary);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(0, 166, 136, 0.05));
        border-left: 3px solid var(--accent-primary);
        padding: 1rem 1.5rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    .info-box p {
        color: var(--text-primary);
        margin: 0;
        font-size: 0.95rem;
    }
    
    .success-box {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.15), rgba(0, 166, 136, 0.08));
        border: 1px solid var(--accent-primary);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        color: #000000;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px var(--accent-glow);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px var(--accent-glow);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00d4aa, #00ffcc);
        color: #000000;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        width: 100%;
        padding: 1rem;
        font-size: 1.1rem;
    }
    
    .stSlider > div > div {
        background: var(--accent-primary);
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-right: 1px solid var(--border-color);
    }
    
    .step-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        border-radius: 50%;
        color: #000;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.75rem;
    }
    
    .step-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
        color: var(--text-primary);
        font-size: 1.1rem;
    }
    
    .position-display {
        background: var(--bg-tertiary);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: var(--accent-primary);
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    hr {
        border-color: var(--border-color);
        margin: 1.5rem 0;
    }
    
    .footer {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.85rem;
        padding: 2rem 0;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Create signatures directory
SIGNATURES_DIR = Path(__file__).parent / "saved_signatures"
SIGNATURES_DIR.mkdir(exist_ok=True)

# Helper functions
def load_saved_signatures():
    """Load list of saved signatures"""
    signatures = list(SIGNATURES_DIR.glob("*.png"))
    return sorted(signatures, key=lambda x: x.stat().st_mtime, reverse=True)

def get_signed_filename(original_filename):
    """Generate signed filename with _signed suffix"""
    if original_filename.lower().endswith('.pdf'):
        return original_filename[:-4] + '_signed.pdf'
    return original_filename + '_signed.pdf'

# Initialize session state
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
if 'signature_created' not in st.session_state:
    st.session_state.signature_created = False
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None
if 'signature_image' not in st.session_state:
    st.session_state.signature_image = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'signature_width' not in st.session_state:
    st.session_state.signature_width = 150

# Header
st.markdown("""
<div class="main-header">
    <h1>✍️ PDF Podpisovač</h1>
    <p>Jednoduché podpisovanie PDF dokumentov • Nahraj, podpíš, stiahni</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0;">
        <span class="step-indicator">1</span>
        <span class="step-title">Nahraj PDF</span>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Vyber PDF súbor", type=['pdf'], label_visibility="collapsed")

    if uploaded_file is not None:
        st.session_state.pdf_file = uploaded_file
        st.session_state.pdf_uploaded = True

        # Get number of pages
        pdf_reader = PdfReader(uploaded_file)
        num_pages = len(pdf_reader.pages)
        
        st.success(f"✅ **{uploaded_file.name}**")
        st.caption(f"📄 {num_pages} {'strana' if num_pages == 1 else 'strán'}")

        # Page selector
        if num_pages > 1:
            st.session_state.current_page = st.selectbox(
                "Vyber stranu na podpis",
                range(num_pages),
                format_func=lambda x: f"Strana {x + 1}"
            )

    st.divider()

    st.markdown("""
    <div style="padding: 0.5rem 0;">
        <span class="step-indicator">2</span>
        <span class="step-title">Vyber podpis</span>
    </div>
    """, unsafe_allow_html=True)

    # Load saved signatures
    saved_signatures = load_saved_signatures()
    
    if saved_signatures:
        signature_names = [sig.stem for sig in saved_signatures]
        selected_sig_name = st.selectbox(
            "Uložené podpisy",
            signature_names,
            key="saved_sig_select"
        )

        if selected_sig_name:
            selected_sig_path = next(sig for sig in saved_signatures if sig.stem == selected_sig_name)
            sig_img = Image.open(selected_sig_path)
            if sig_img.mode != 'RGBA':
                sig_img = sig_img.convert('RGBA')
            st.session_state.signature_image = sig_img
            st.session_state.signature_created = True
            st.image(sig_img, caption="Vybraný podpis", width=200)
    else:
        st.info("📁 Nahraj obrázok podpisu")
    
    # Upload signature option
    uploaded_signature = st.file_uploader(
        "Nahraj nový podpis (PNG)",
        type=['png', 'jpg', 'jpeg'],
        key="signature_upload"
    )

    if uploaded_signature is not None:
        sig_img = Image.open(uploaded_signature)
        if sig_img.mode != 'RGBA':
            sig_img = sig_img.convert('RGBA')
        st.session_state.signature_image = sig_img
        st.session_state.signature_created = True
        st.success("✅ Podpis nahraný!")
        st.image(sig_img, caption="Nahraný podpis", width=200)
    
    st.divider()
    
    # Signature size control
    st.markdown("""
    <div style="padding: 0.5rem 0;">
        <span class="step-indicator">3</span>
        <span class="step-title">Veľkosť podpisu</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.signature_width = st.slider(
        "Šírka podpisu (px)",
        min_value=50,
        max_value=400,
        value=st.session_state.signature_width,
        step=10
    )

# Main content
if not st.session_state.pdf_uploaded:
    st.markdown("""
    <div class="info-box">
        <p>👈 Začni nahratím PDF súboru v bočnom paneli</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="signature-card">
            <h3>📤 Nahraj</h3>
            <p style="color: var(--text-secondary);">Vyber PDF súbor, ktorý potrebuješ podpísať</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="signature-card">
            <h3>✍️ Podpíš</h3>
            <p style="color: var(--text-secondary);">Použi uložený podpis alebo nahraj nový</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="signature-card">
            <h3>⬇️ Stiahni</h3>
            <p style="color: var(--text-secondary);">Exportuj podpísaný dokument s _signed</p>
        </div>
        """, unsafe_allow_html=True)

else:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📄 Náhľad dokumentu")

        # Convert PDF page to image
        pdf_bytes = st.session_state.pdf_file.getvalue()

        # Open PDF with PyMuPDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = pdf_document[st.session_state.current_page]

        # Render page to image
        zoom = 1.5
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        pdf_image = Image.open(io.BytesIO(img_data))
        
        # Store dimensions
        pdf_page_width = float(page.rect.width)
        pdf_page_height = float(page.rect.height)
        display_width = pdf_image.width
        display_height = pdf_image.height

        pdf_document.close()

        # Display PDF
        st.image(pdf_image, use_container_width=True)
        
        st.markdown("""
        <div class="info-box">
            <p>💡 Použi slidery nižšie na umiestnenie podpisu</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("📍 Pozícia podpisu")
        
        if st.session_state.signature_created:
            # Show signature preview
            st.image(st.session_state.signature_image, caption=f"Veľkosť: {st.session_state.signature_width}px", width=min(st.session_state.signature_width, 250))
            
            st.divider()
            
            # Position sliders (as percentage of page)
            pos_x = st.slider(
                "Horizontálna pozícia (%)",
                min_value=0,
                max_value=100,
                value=50,
                help="0% = ľavý okraj, 100% = pravý okraj"
            )
            
            pos_y = st.slider(
                "Vertikálna pozícia (%)",
                min_value=0,
                max_value=100,
                value=80,
                help="0% = horný okraj, 100% = dolný okraj"
            )
            
        st.divider()

            # Show what the filename will be
            original_filename = st.session_state.pdf_file.name
            signed_filename = get_signed_filename(original_filename)
            
            st.caption(f"📄 Výstupný súbor: **{signed_filename}**")
            
            if st.button("✍️ Vytvoriť podpísané PDF", type="primary", use_container_width=True):
                try:
                    with st.spinner("Vytváram podpísané PDF..."):
                    # Create signed PDF
                    pdf_reader = PdfReader(io.BytesIO(st.session_state.pdf_file.getvalue()))
                    pdf_writer = PdfWriter()

                    # Get the page to sign
                    page = pdf_reader.pages[st.session_state.current_page]
                    page_width = float(page.mediabox.width)
                    page_height = float(page.mediabox.height)

                    # Create signature overlay
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(page_width, page_height))

                    # Resize signature
                    sig_img = st.session_state.signature_image
                    aspect_ratio = sig_img.height / sig_img.width
                    sig_width = st.session_state.signature_width
                    sig_height = int(sig_width * aspect_ratio)

                    # Save signature as temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_sig:
                        sig_img.save(tmp_sig.name, 'PNG')

                            # Calculate position from percentage
                            x = (pos_x / 100) * page_width - (sig_width / 2)
                            y = page_height - ((pos_y / 100) * page_height) - (sig_height / 2)
                            
                            # Clamp to page bounds
                            x = max(0, min(x, page_width - sig_width))
                            y = max(0, min(y, page_height - sig_height))

                        # Draw signature on canvas
                        can.drawImage(
                            tmp_sig.name,
                                x, y,
                            width=sig_width,
                            height=sig_height,
                            mask='auto'
                        )
                        can.save()

                        # Clean up temp signature file
                        Path(tmp_sig.name).unlink(missing_ok=True)

                    # Merge signature with PDF
                    packet.seek(0)
                    signature_pdf = PdfReader(packet)
                    page.merge_page(signature_pdf.pages[0])

                    # Add all pages to writer
                    for i, p in enumerate(pdf_reader.pages):
                        if i == st.session_state.current_page:
                            pdf_writer.add_page(page)
                        else:
                            pdf_writer.add_page(p)

                    # Save to bytes
                    output = io.BytesIO()
                    pdf_writer.write(output)
                    output.seek(0)

                        st.success("✅ PDF úspešne podpísané!")

                    # Download button
                    st.download_button(
                            label=f"⬇️ Stiahnuť {signed_filename}",
                        data=output,
                        file_name=signed_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"❌ Chyba: {str(e)}")
        else:
            st.warning("⚠️ Najprv vyber alebo nahraj podpis v bočnom paneli")

# Footer
st.markdown("""
<div class="footer">
    ✍️ PDF Podpisovač • Vytvorené s ❤️ pre jednoduché podpisovanie
</div>
""", unsafe_allow_html=True)
