# ============================================================
#   IMAGE ENCRYPTION TOOL
#   Uses: numpy, cv2, pycryptodome
#   Method: SHA-256 password hashing + XOR + Row/Col shuffle
# ============================================================

import cv2
import numpy as np
from Crypto.Hash import SHA256


# ------------------------------------------------------------
# STEP 1 — Turn the password into a usable key
# ------------------------------------------------------------

def generate_key(password):
    """
    Hashes the password with SHA-256 to produce 32 bytes.
    Those bytes are split into XOR values, row/col shifts,
    and a shuffle seed — so the same password always gives
    the exact same encryption behaviour.
    """

    # Hash the password → always gives 32 bytes for any input
    digest = SHA256.new(password.encode()).digest()

    # Convert those 32 bytes into a numpy array of integers (0-255)
    raw = np.frombuffer(digest, dtype=np.uint8)

    # Slice the 32 bytes into 3 key parts:
    xor_keys = list(raw[:8])                      # bytes  0–7  → XOR values
    shifts_y = [int(b) * 5 for b in raw[8:16]]   # bytes  8–15 → vertical shifts
    shifts_x = [int(b) * 5 for b in raw[16:24]]  # bytes 16–23 → horizontal shifts
    seed     = int.from_bytes(raw[24:28], 'big')  # bytes 24–27 → shuffle seed

    print("\n--- KEY GENERATED ---")
    print(f"  XOR keys : {xor_keys}")
    print(f"  Y shifts : {shifts_y}")
    print(f"  X shifts : {shifts_x}")
    print(f"  Seed     : {seed}")
    print("---------------------\n")

    return xor_keys, shifts_y, shifts_x, seed


# ------------------------------------------------------------
# STEP 2 — Shuffle rows and columns using the seed
# ------------------------------------------------------------

def shuffle_rows_and_cols(image, seed):
    """
    Randomly reorders rows and columns of the image.
    Same seed = same shuffle every time (needed for decryption).
    """

    rng = np.random.default_rng(seed)   # seeded RNG

    h, w  = image.shape[:2]
    row_order = rng.permutation(h)      # e.g. [3, 0, 4, 1, 2] for h=5
    col_order = rng.permutation(w)

    shuffled = image[row_order, :]      # reorder rows
    shuffled = shuffled[:, col_order]   # reorder columns

    return shuffled, row_order, col_order


def unshuffle_rows_and_cols(image, row_order, col_order):
    """
    Reverses the shuffle by computing inverse permutations.
    np.argsort gives us the 'undo' order.
    """

    inv_row = np.argsort(row_order)
    inv_col = np.argsort(col_order)

    unshuffled = image[inv_row, :]
    unshuffled = unshuffled[:, inv_col]

    return unshuffled


# ------------------------------------------------------------
# STEP 3 — XOR + Roll (your original idea, extended to 8 rounds)
# ------------------------------------------------------------

def xor_and_roll(image, xor_keys, shifts_y, shifts_x):
    """
    Runs 8 rounds of:
      1. XOR the entire image with a key value (flips bits)
      2. Roll (shift) the image vertically
      3. Roll (shift) the image horizontally
    """

    result = image.copy()

    for xk, sy, sx in zip(xor_keys, shifts_y, shifts_x):
        result = np.bitwise_xor(result, xk)           # flip bits
        result = np.roll(result, shift=sy, axis=0)    # shift rows down
        result = np.roll(result, shift=sx, axis=1)    # shift cols right

    return result


def reverse_xor_and_roll(image, xor_keys, shifts_y, shifts_x):
    """
    Reverses XOR+roll by going through the rounds backwards.
    - Roll with negative shift to undo
    - XOR again with same key (XOR is self-reversing)
    """

    result = image.copy()

    for xk, sy, sx in zip(reversed(xor_keys), reversed(shifts_y), reversed(shifts_x)):
        result = np.roll(result, shift=-sx, axis=1)   # undo horizontal roll
        result = np.roll(result, shift=-sy, axis=0)   # undo vertical roll
        result = np.bitwise_xor(result, xk)           # undo XOR

    return result


# ------------------------------------------------------------
# STEP 4 — Full encrypt / decrypt pipeline
# ------------------------------------------------------------

def encrypt(image, password):
    xor_keys, shifts_y, shifts_x, seed = generate_key(password)

    # 1. Shuffle rows and columns
    shuffled, row_order, col_order = shuffle_rows_and_cols(image, seed)

    # 2. XOR + roll
    encrypted = xor_and_roll(shuffled, xor_keys, shifts_y, shifts_x)

    # Save row/col order so decrypt can reverse the shuffle
    return encrypted, row_order, col_order, xor_keys, shifts_y, shifts_x


def decrypt(encrypted, password):
    # 1. Get the keys and seed back from the password
    xor_keys, shifts_y, shifts_x, seed = generate_key(password)

    # 2. Re-create the exact same row and col orders!
    rng = np.random.default_rng(seed)
    h, w = encrypted.shape[:2]
    row_order = rng.permutation(h)
    col_order = rng.permutation(w)

    # 3. Reverse XOR + roll
    unrolled = reverse_xor_and_roll(encrypted, xor_keys, shifts_y, shifts_x)

    # 4. Unshuffle rows and columns using the re-created orders
    decrypted = unshuffle_rows_and_cols(unrolled, row_order, col_order)

    return decrypted


# ------------------------------------------------------------
# STEP 5 — Show results
# ------------------------------------------------------------

def show_results(original, encrypted, decrypted):
    """Displays original, encrypted, and decrypted side by side."""

    # Normalize encrypted so it's visible (not all black/white)
    enc_display = cv2.normalize(encrypted, None, 0, 255, cv2.NORM_MINMAX)

    combined = np.hstack([original, enc_display, decrypted])
    cv2.imshow("Original  |  Encrypted  |  Decrypted", combined)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

if __name__ == "__main__":
    print("=============================")
    print("    IMAGE ENCRYPTION TOOL    ")
    print("=============================")
    
    action = input("Would you like to (E)ncrypt or (D)ecrypt? ").strip().upper()

    match action:
        case "E":
            # --- ENCRYPT MODE ---
            path = input("Enter the image path to encrypt: ").strip()
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

            if image is None:
                print("Error: Image not found. Check the file path.")
                exit()

            print(f"Image loaded: {image.shape[1]}x{image.shape[0]} px")

            password = input("Create a password: ").strip()
            if not password:
                print("Error: Password cannot be empty.")
                exit()

            # Perform Encryption
            # We don't even need to catch the row_order/col_order returns anymore
            encrypted, *_ = encrypt(image, password)
            
            # Save ONLY the encrypted image
            cv2.imwrite("encrypted.png", encrypted)
            
            print("[✓] Encrypted image securely saved as 'encrypted.png'")
            print("[!] Do not forget your password, or this image is gone forever!")

        case "D":
            # --- DECRYPT MODE ---
            path = input("Enter the encrypted image path (e.g., encrypted.png): ").strip()
            encrypted = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

            if encrypted is None:
                print("Error: Encrypted image not found.")
                exit()

            # Ask for password
            entered_password = input("Enter password to decrypt: ").strip()
            
            # Perform Decryption
            # If the password is wrong, it will just generate garbage data instead of crashing!
            decrypted = decrypt(encrypted, entered_password)
            
            # Save and display
            cv2.imwrite("decrypted.png", decrypted)
            print("[✓] Decryption attempted and saved as 'decrypted.png'")
            
            # Show the encrypted vs decrypted side by side
            enc_display = cv2.normalize(encrypted, None, 0, 255, cv2.NORM_MINMAX)
            combined = np.hstack([enc_display, decrypted])
            cv2.imshow("Encrypted  |  Decrypted", combined)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        case _:
            # --- INVALID INPUT ---
            print("Invalid option. Please run the script again and type 'E' or 'D'.")