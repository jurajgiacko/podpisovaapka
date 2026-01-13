import streamlit as st
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
import tempfile
from pathlib import Path
import json
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
    
    .sidebar .stRadio > div {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 0.5rem;
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
    
    .footer a {
        color: var(--accent-primary);
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# Create signatures directory
SIGNATURES_DIR = Path(__file__).parent / "saved_signatures"
SIGNATURES_DIR.mkdir(exist_ok=True)

# Helper functions for signature management
def save_signature(sig_img, name):
    """Save signature to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = SIGNATURES_DIR / filename
    sig_img.save(filepath, 'PNG')
    return filepath

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
if 'signature_color' not in st.session_state:
    st.session_state.signature_color = "#1A237E"
if 'signature_width' not in st.session_state:
    st.session_state.signature_width = 150
if 'signature_x' not in st.session_state:
    st.session_state.signature_x = None
if 'signature_y' not in st.session_state:
    st.session_state.signature_y = None

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
    
    uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed")

    if uploaded_file is not None:
        st.session_state.pdf_file = uploaded_file
        st.session_state.pdf_uploaded = True
        
        # Get number of pages
        pdf_reader = PdfReader(uploaded_file)
        num_pages = len(pdf_reader.pages)
        
        st.markdown(f"""
        <div class="success-box">
            <p>✅ <strong>{uploaded_file.name}</strong></p>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">📄 {num_pages} {'strana' if num_pages == 1 else 'strán' if num_pages < 5 else 'strán'}</p>
        </div>
        """, unsafe_allow_html=True)

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

    signature_method = st.radio(
        "",
        ["✏️ Nakresli podpis", "💾 Načítaj uložený podpis", "📁 Nahraj obrázok"],
        label_visibility="collapsed"
    )
    
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
        step=10,
        help="Nastav veľkosť podpisu pred umiestnením"
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
            <p style="color: var(--text-secondary);">Nakresli podpis alebo použi uložený</p>
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
        st.markdown("""
        <div class="signature-card">
            <h3>📄 Náhľad dokumentu</h3>
        </div>
        """, unsafe_allow_html=True)

        # Convert PDF page to image
        pdf_bytes = st.session_state.pdf_file.getvalue()

        # Open PDF with PyMuPDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = pdf_document[st.session_state.current_page]

        # Render page to image
        zoom = 1.5  # zoom factor for quality/performance balance
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        pdf_image = Image.open(io.BytesIO(img_data))
        
        # Store original PDF dimensions for coordinate conversion
        pdf_page_width = float(page.rect.width)
        pdf_page_height = float(page.rect.height)

        pdf_document.close()

        st.markdown("""
        <div class="info-box">
            <p>💡 Klikni na miesto, kde chceš umiestniť podpis</p>
        </div>
        """, unsafe_allow_html=True)

        # Canvas for placing signature
        canvas_result = st_canvas(
            fill_color="rgba(0, 212, 170, 0.2)",
            stroke_width=3,
            stroke_color="#00d4aa",
            background_image=pdf_image,
            update_streamlit=True,
            height=pdf_image.height,
            width=pdf_image.width,
            drawing_mode="point",
            point_display_radius=8,
            key="pdf_canvas",
        )

        # Store click position
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            if objects:
                last_point = objects[-1]
                st.session_state.signature_x = last_point["left"]
                st.session_state.signature_y = last_point["top"]
                
                st.markdown(f"""
                <div class="position-display">
                    📍 Pozícia: X={int(st.session_state.signature_x)}, Y={int(st.session_state.signature_y)}
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="signature-card">
            <h3>✍️ Tvoj podpis</h3>
        </div>
        """, unsafe_allow_html=True)

        if signature_method == "✏️ Nakresli podpis":
            # Color picker for signature
            st.session_state.signature_color = st.color_picker(
                "Farba podpisu",
                value=st.session_state.signature_color,
                key="sig_color_picker"
            )

            # Drawing canvas for signature
            signature_canvas = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=3,
                stroke_color=st.session_state.signature_color,
                background_color="#FFFFFF",
                height=150,
                width=350,
                drawing_mode="freedraw",
                key="signature_canvas",
            )

            if signature_canvas.image_data is not None:
                # Convert to PIL Image
                sig_img = Image.fromarray(signature_canvas.image_data.astype('uint8'), 'RGBA')

                # Crop to content
                bbox = sig_img.getbbox()
                if bbox:
                    sig_img = sig_img.crop(bbox)
                    st.session_state.signature_image = sig_img
                    st.session_state.signature_created = True

                    st.success("✅ Podpis pripravený")
                    
                    # Preview with current size
                    aspect_ratio = sig_img.height / sig_img.width
                    preview_width = min(st.session_state.signature_width, 300)
                    st.image(sig_img, caption=f"Náhľad ({st.session_state.signature_width}px)", width=preview_width)

                    # Save signature option
                    with st.expander("💾 Uložiť podpis"):
                        signature_name = st.text_input("Názov:", value="moj_podpis", key="sig_name")
                        if st.button("Uložiť", use_container_width=True):
                            save_signature(sig_img, signature_name)
                            st.success(f"✅ Podpis '{signature_name}' uložený!")
                            st.rerun()

        elif signature_method == "💾 Načítaj uložený podpis":
            saved_signatures = load_saved_signatures()

            if saved_signatures:
                signature_names = [sig.stem for sig in saved_signatures]
                selected_sig_name = st.selectbox(
                    "Vyber podpis",
                    signature_names,
                    key="saved_sig_select"
                )

                if selected_sig_name:
                    selected_sig_path = next(sig for sig in saved_signatures if sig.stem == selected_sig_name)

                    # Load and display
                    sig_img = Image.open(selected_sig_path)
                    if sig_img.mode != 'RGBA':
                        sig_img = sig_img.convert('RGBA')

                    st.session_state.signature_image = sig_img
                    st.session_state.signature_created = True

                    st.success("✅ Podpis načítaný")
                    
                    # Preview with current size
                    preview_width = min(st.session_state.signature_width, 300)
                    st.image(sig_img, caption=f"Náhľad ({st.session_state.signature_width}px)", width=preview_width)

                    if st.button("🗑️ Zmazať tento podpis", type="secondary", use_container_width=True):
                        selected_sig_path.unlink()
                        st.success(f"Podpis '{selected_sig_name}' zmazaný")
                        st.rerun()
            else:
                st.info("Zatiaľ nemáš žiadne uložené podpisy. Nakresli podpis a ulož ho!")

        else:  # Upload image
            uploaded_signature = st.file_uploader(
                "Nahraj obrázok podpisu",
                type=['png', 'jpg', 'jpeg'],
                key="signature_upload"
            )

            if uploaded_signature is not None:
                sig_img = Image.open(uploaded_signature)
                if sig_img.mode != 'RGBA':
                    sig_img = sig_img.convert('RGBA')

                st.session_state.signature_image = sig_img
                st.session_state.signature_created = True

                st.success("✅ Podpis nahraný")
                
                preview_width = min(st.session_state.signature_width, 300)
                st.image(sig_img, caption=f"Náhľad ({st.session_state.signature_width}px)", width=preview_width)

        st.divider()

        # Export section
        st.markdown("""
        <div class="signature-card">
            <h3>📥 Export</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.signature_created and st.session_state.signature_x is not None:
            # Show what the filename will be
            original_filename = st.session_state.pdf_file.name
            signed_filename = get_signed_filename(original_filename)
            
            st.markdown(f"""
            <div class="position-display" style="font-size: 0.8rem; width: 100%; word-break: break-all;">
                📄 {signed_filename}
            </div>
            """, unsafe_allow_html=True)
            
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

                            # Calculate position (adjust for PDF coordinates)
                            # PDF coordinates start from bottom-left
                            scale_x = page_width / pdf_image.width
                            scale_y = page_height / pdf_image.height

                            x = st.session_state.signature_x * scale_x
                            y = page_height - (st.session_state.signature_y * scale_y)

                            # Draw signature on canvas
                            can.drawImage(
                                tmp_sig.name,
                                x, y - sig_height,
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

        elif st.session_state.signature_created and st.session_state.signature_x is None:
            st.warning("⚠️ Klikni na miesto v dokumente, kde chceš umiestniť podpis")
        elif not st.session_state.signature_created:
            st.warning("⚠️ Najprv vytvor alebo nahraj podpis")

# Footer
st.markdown("""
<div class="footer">
    ✍️ PDF Podpisovač • Vytvorené s ❤️ pre jednoduché podpisovanie
</div>
""", unsafe_allow_html=True)
