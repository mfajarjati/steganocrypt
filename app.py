import streamlit as st
from PIL import Image
import numpy as np
import io

# Konfigurasi halaman
st.set_page_config(
    page_title="Kelompok 4: Enkripsi & Dekripsi Gambar",
    page_icon="🔒",
    layout="wide"
)

# Dvorak layout
DVO_LAYOUT = list("PYFGCRLAOEUIDHTNSQJKXBMWVZ")
ALLOWED_CHARS = set(DVO_LAYOUT) 

# validation function
def validate_message(message):
    if not message:
        return False, "Pesan tidak boleh kosong!"
    
    invalid_chars = [c for c in message.upper() if not c.isalpha()]
    if invalid_chars:
        return False, f"Error: Karakter tidak valid! Hanya huruf alfabet yang diperbolehkan.\nKarakter yang tidak valid: {', '.join(set(invalid_chars))}"
    return True, ""

# calculate_mse functions
def calculate_mse(original_image, modified_image):
    # Convert PIL images to numpy arrays
    img1 = np.array(original_image)
    img2 = np.array(modified_image)
    
    # Ensure both are float32/float64 for precise calculation
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    # Calculate MSE
    mse = np.mean(np.square(img1 - img2))
    
    return mse

# calculate_psnr functions
def calculate_psnr(original_image, modified_image):
    mse = calculate_mse(original_image, modified_image)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    return 20 * np.log10(max_pixel / np.sqrt(mse))

# Encrypt
def encrypt_message(message, key):
    encrypted = []
    key = key % len(DVO_LAYOUT)
    for char in message.upper():
        if char in DVO_LAYOUT:
            idx = DVO_LAYOUT.index(char)
            encrypted_char = DVO_LAYOUT[(idx + key) % len(DVO_LAYOUT)]
            encrypted.append(encrypted_char)
        else:
            encrypted.append(char)
    return ''.join(encrypted)

def is_grayscale(image):
    img_array = np.array(image)
    if len(img_array.shape) == 2:
        return True
    if len(img_array.shape) == 3:
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        return np.array_equal(r, g) and np.array_equal(g, b)
    return False

# Decrypt
def decrypt_message(message, key):
    decrypted = []
    key = key % len(DVO_LAYOUT)
    for char in message.upper():
        if char in DVO_LAYOUT:
            idx = DVO_LAYOUT.index(char)
            decrypted_char = DVO_LAYOUT[(idx - key) % len(DVO_LAYOUT)]
            decrypted.append(decrypted_char)
        else:
            decrypted.append(char)
    return ''.join(decrypted)

# Convert text to binary
def text_to_binary(text):
    return ''.join([format(ord(c), '08b') for c in text])

# Convert binary to text
def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    try:
        text = ''.join([chr(int(c, 2)) for c in chars])
        print(f"Extracted text: {text}")  # Debug
        return text
    except:
        print("Error converting binary to text")  # Debug
        return ""

# Embed binary data into image using LSB
def embed_data(image, binary_data):
    # Convert to numpy array and ensure uint8 type
    img = np.array(image, dtype=np.uint8)
    flat_img = img.flatten()
    
    if len(binary_data) > len(flat_img):
        raise ValueError("Data terlalu besar untuk disembunyikan dalam gambar.")
    
    # Create a copy to avoid modifying original array
    embedded = flat_img.copy()
    
    for i in range(len(binary_data)):
        # Clear the LSB and set it to the message bit
        # Use bitwise operations to ensure values stay within bounds
        embedded[i] = (embedded[i] & 0xFE) | (int(binary_data[i]) & 0x01)
    
    # Reshape back to original dimensions
    embedded_img = embedded.reshape(img.shape)
    
    # Ensure output is uint8 and properly bounded
    embedded_img = np.clip(embedded_img, 0, 255).astype(np.uint8)
    
    return Image.fromarray(embedded_img)

# Extract binary data from image using LSB
def extract_data(image, num_bits):
    img = np.array(image)
    flat_img = img.flatten()
    binary_data = ''.join([str(pixel & 1) for pixel in flat_img[:num_bits]])
    print(f"Extracted binary length: {len(binary_data)}")  # Debug
    return binary_data

# Streamlit App
def main():
    # Informasi kelompok
    st.sidebar.markdown("## Kelompok 4")

    st.title("🔒 Enkripsi & Dekripsi Gambar dengan Caesar Cipher dan Steganografi")

    # Initialize session state
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "key_input" not in st.session_state:
        st.session_state.key_input = None

    menu = ["Enkripsi", "Dekripsi"]
    choice = st.sidebar.selectbox("Pilih Mode", menu, key="page_selector")

    # Reset state on page change
    if st.session_state.page_selector != st.session_state.get("last_page"):
        st.session_state.uploaded_file = None
        st.session_state.key_input = None
        st.session_state.last_page = st.session_state.page_selector

    if choice == "Enkripsi":
        st.header("Enkripsi Gambar")

        # Upload gambar
        uploaded_file = st.file_uploader("Unggah Gambar", type=["png", "jpg", "jpeg"], key="enkripsi_file")
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            image = Image.open(uploaded_file) # Convert to grayscale
            st.image(image, caption='Gambar Grayscale', use_container_width=True)
            
            if not is_grayscale(image):
                st.error("Mohon upload gambar grayscale! Gambar berwarna tidak dapat diproses.")
                st.stop()

            # Input key
            key = st.number_input("Masukkan Key", value=3, step=1, key="enkripsi_key")
            st.session_state.key_input = key

            # Input pesan
            message = st.text_input("Masukkan Pesan yang Ingin disisipkan")

            if st.button("Enkripsi"):
                is_valid, error_msg = validate_message(message)
                if not is_valid:
                    # st.error(error_msg)
                    st.warning("⚠️ Hanya huruf alfabet (A-Z) yang diperbolehkan!")
                else:
                    try:
                        header = "MSG:"
                        delimiter = "#####"
                        final_plaintext = header + message + delimiter

                        encrypted_final_message = encrypt_message(final_plaintext, key)
                        binary_data = text_to_binary(encrypted_final_message)
                        embedded_image = embed_data(image, binary_data)
                        
                        st.success("Pesan berhasil dienkripsi dan disembunyikan dalam gambar!")

                        buf = io.BytesIO()
                        embedded_image.save(buf, format='PNG')
                        byte_im = buf.getvalue()
                        st.markdown('<style>div.stDownloadButton {margin-bottom: 40px;}</style>', unsafe_allow_html=True)
                        st.download_button(
                        label="Unduh Gambar Terenkripsi",
                        data=byte_im,
                        file_name="encrypted_image.png",
                        mime="image/png"
                            )
                        with st.expander("Lihat Detail Metrik Kualitas Gambar"):
                            # Calculate MSE and PSNR
                            mse_value = calculate_mse(image, embedded_image)
                            psnr_value = calculate_psnr(image, embedded_image)

                            # Display metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    label="Mean Square Error (MSE)", 
                                    value=f"{mse_value:.10f}"
                                )
                            with col2:
                                st.metric(
                                    label="Peak Signal-to-Noise Ratio (PSNR)", 
                                    value=f"{psnr_value:.2f} dB"
                                )

                            # Add metrics info
                            st.info("""
                                💡 Interpretasi Metrik:
                                - MSE lebih rendah = Distorsi lebih kecil
                                - PSNR lebih tinggi = Kualitas gambar lebih baik
                                - PSNR > 30dB umumnya dianggap berkualitas baik
                            """)

                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")

    elif choice == "Dekripsi":
        st.header("Dekripsi Gambar")

        # Upload gambar
        uploaded_file = st.file_uploader("Unggah Gambar", type=["png", "jpg", "jpeg"], key="dekripsi_file")
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            image = Image.open(uploaded_file)  # Convert to grayscale
            st.image(image, caption='Gambar Terenkripsi', use_container_width=True)

            # Input key
            key = st.number_input("Masukkan Key", value=3, step=1, key="dekripsi_key")
            st.session_state.key_input = key

            if st.button("Dekripsi"):
                try:
                    max_message_length = 1000  # Increased from 100
                    header = "MSG:"
                    delimiter = "#####"
                    total_chars = len(header) + max_message_length + len(delimiter)
                    num_bits = 8 * total_chars


                    binary_data = extract_data(image, num_bits)
                    extracted_encrypted_text = binary_to_text(binary_data)
                    decrypted_text = decrypt_message(extracted_encrypted_text, key)

                    if header in decrypted_text and delimiter in decrypted_text:
                        start = decrypted_text.find(header) + len(header)
                        end = decrypted_text.find(delimiter, start)
                        if end != -1:
                            decrypted_message = decrypted_text[start:end]
                            st.markdown(
                                f"""
                                <style>
                                .decrypted-message {{
                                    padding: 15px;
                                    border-radius: 10px;
                                    border: 2px solid #4CAF50;
                                    margin: 10px 0;
                                }}
                                
                                /* For dark theme */
                                [data-theme="dark"] .decrypted-message {{
                                    background-color: rgba(38, 39, 48, 0.9);
                                    color: white;
                                }}
                                
                                /* For light theme */
                                [data-theme="light"] .decrypted-message {{
                                    background-color: rgba(255, 255, 255, 0.9);
                                    color: black;
                                }}
                                </style>
                                
                                <div class="decrypted-message" style="text-align: center;">
                                    <h3 style="color:#4CAF50;">Dekripsi Berhasil!</h3>
                                    <p style="font-size: 16px;"><strong>Pesan:</strong> {decrypted_message}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.error("Key salah atau gambar tidak berisi pesan yang dienkripsi.")
                    else:
                        st.error("Key salah atau gambar tidak berisi pesan yang dienkripsi.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

    # Footer
    st.markdown(
        """
        <style>
        footer {
            visibility: hidden;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f9f9f9;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: #666;
        }
        </style>
        <div class="footer">
            Dibuat dengan ❤️ oleh Kelompok 4 TEKKOM UPI
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
