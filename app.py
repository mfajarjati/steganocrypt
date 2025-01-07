import streamlit as st
from PIL import Image
import numpy as np
import io

#Dvorak layout
DVO_LAYOUT = list("PYFGCRLAOEUIDHTNSQJKXBMWVZ")

#encrypt 
def encrypt_message(message, key):
    encrypted = []
    key = key % len(DVO_LAYOUT)
    for char in message.upper():
        if char in DVO_LAYOUT:
            idx = DVO_LAYOUT.index(char)
            encrypted_char = DVO_LAYOUT[(idx + key) % len(DVO_LAYOUT)]
            encrypted.append(encrypted_char)
        else:
            # Non-Dvorak characters are left unchanged or can be handled differently
            encrypted.append(char)
    return ''.join(encrypted)

#decrypt 
def decrypt_message(message, key):
    decrypted = []
    key = key % len(DVO_LAYOUT)
    for char in message.upper():
        if char in DVO_LAYOUT:
            idx = DVO_LAYOUT.index(char)
            decrypted_char = DVO_LAYOUT[(idx - key) % len(DVO_LAYOUT)]
            decrypted.append(decrypted_char)
        else:
            # Non-Dvorak characters are left unchanged or can be handled differently
            decrypted.append(char)
    return ''.join(decrypted)

#convert text to binary
def text_to_binary(text):
    return ''.join([format(ord(c), '08b') for c in text])

#convert binary to text
def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    try:
        text = ''.join([chr(int(c, 2)) for c in chars])
        return text
    except:
        return "" 

#embed binary data into image using LSB
def embed_data(image, binary_data):
    img = np.array(image)
    flat_img = img.flatten()
    
    if len(binary_data) > len(flat_img):
        raise ValueError("Data terlalu besar untuk disembunyikan dalam gambar.")
    
    # Create a copy to avoid modifying original array
    embedded_img = flat_img.copy()
    
    for i in range(len(binary_data)):
        # Get current pixel value
        pixel = int(embedded_img[i])
        
        # Clear the LSB
        pixel = pixel & 0xFE  # Clear last bit
        
        # Set the LSB according to our data
        if binary_data[i] == '1':
            pixel = pixel | 1
            
        # Ensure value stays within uint8 bounds
        embedded_img[i] = np.clip(pixel, 0, 255)
    
    # Reshape back to original dimensions
    return Image.fromarray(embedded_img.reshape(img.shape).astype(np.uint8))

# Function to extract binary data from image using LSB
def extract_data(image, num_bits):
    img = np.array(image)
    flat_img = img.flatten()
    binary_data = ''.join([str(pixel & 1) for pixel in flat_img[:num_bits]])
    return binary_data

# Streamlit App
def main():
    st.title("Enkripsi & Dekripsi Gambar dengan Caesar Cipher dan Steganografi")

    menu = ["Enkripsi", "Dekripsi"]
    choice = st.sidebar.selectbox("Pilih Mode", menu)

    if choice == "Enkripsi":
        st.header("Enkripsi Gambar")

        # Upload gambar
        uploaded_file = st.file_uploader("Unggah Gambar Grayscale", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            # Ensure proper grayscale conversion
            image = Image.open(uploaded_file).convert('L')
            img_array = np.array(image)
            
            # Validate image
            if img_array.dtype != np.uint8:
                st.error("Image must be 8-bit grayscale")
                return

            st.image(image, caption='Gambar Grayscale', use_container_width=True)

            # Input key
            key = st.number_input("Masukkan Key (integer)", min_value=1, max_value=25, value=3)

            # Input pesan
            message = st.text_input("Masukkan Pesan yang Ingin Dikirim")

            if st.button("Enkripsi dan Sembunyikan Pesan"):
                if message.strip() == "":
                    st.error("Pesan tidak boleh kosong!")
                else:
                    try:
                        # Tambahkan header dan delimiter
                        header = "MSG:"
                        delimiter = "#####"
                        final_plaintext = header + message + delimiter

                        # Enkripsi pesan 
                        encrypted_final_message = encrypt_message(final_plaintext, key)
                        #st.write(f"Pesan Terenkripsi: {encrypted_final_message}")

                        # Convert ke binary
                        binary_data = text_to_binary(encrypted_final_message)

                        # Embed data
                        embedded_image = embed_data(image, binary_data)
                        st.image(embedded_image, caption='Gambar dengan Pesan Tersembunyi', use_container_width=True)

                        # Download link
                        buf = io.BytesIO()
                        embedded_image.save(buf, format='PNG')
                        byte_im = buf.getvalue()
                        st.download_button(
                            label="Unduh Gambar Terenkripsi",
                            data=byte_im,
                            file_name="encrypted_image.png",
                            mime="image/png"
                        )
                        st.success("Pesan berhasil dienkripsi dan disembunyikan dalam gambar!")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")

    elif choice == "Dekripsi":
        st.header("Dekripsi Gambar")

        # Upload gambar
        uploaded_file = st.file_uploader("Unggah Gambar Terenkripsi (Grayscale)", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file).convert("L")  # Convert to grayscale
            st.image(image, caption='Gambar Terenkripsi', use_container_width=True)

            # Input key
            key = st.number_input("Masukkan Key yang Digunakan untuk Enkripsi", min_value=1, max_value=25, value=3)

            if st.button("Dekripsi Pesan"):
                try:
                    # Estimasi jumlah karakter maksimum
                    max_message_length = 100  # Sesuaikan jika perlu
                    header = "MSG:"
                    delimiter = "#####"
                    # Total characters to extract: header + message + delimiter
                    total_chars = len(header) + max_message_length + len(delimiter)
                    num_bits = 8 * total_chars

                    binary_data = extract_data(image, num_bits)

                    # Convert binary to text
                    extracted_encrypted_text = binary_to_text(binary_data)

                    # Dekripsi dengan key yang dimasukkan
                    decrypted_text = decrypt_message(extracted_encrypted_text, key)

                    # Cari header dan delimiter setelah dekripsi
                    if header in decrypted_text and delimiter in decrypted_text:
                        # Ekstrak pesan antara header dan delimiter
                        start = decrypted_text.find(header) + len(header)
                        end = decrypted_text.find(delimiter, start)
                        if end != -1:
                            decrypted_message = decrypted_text[start:end]
                            st.success("Dekripsi berhasil! Berikut pesan Anda:")
                            st.write(f"**Pesan Terdekripsi:** {decrypted_message}")
                        else:
                            st.error("Delimiter tidak ditemukan setelah dekripsi. Mungkin key salah atau gambar tidak berisi pesan yang dienkripsi.")
                    else:
                        st.error("Header atau delimiter tidak ditemukan setelah dekripsi. Mungkin key salah atau gambar tidak berisi pesan yang dienkripsi.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()
