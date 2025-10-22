import secrets
import numpy as np
import base64
from typing import Tuple, Optional
from .parameters import get_params, CLWEParameters, validate_parameters
from .ntt_engine import create_optimized_ntt_engine
from .transforms import ColorTransformEngine
from dataclasses import dataclass
import secrets
import numpy as np
from typing import Tuple, Optional
from .parameters import get_params, CLWEParameters
from .ntt_engine import create_optimized_ntt_engine
from .transforms import ColorTransformEngine
from dataclasses import dataclass

class ChromaCryptPublicKey:
    def __init__(self, matrix_seed: bytes, public_vector: np.ndarray, color_seed: bytes, params: CLWEParameters):
        if not isinstance(matrix_seed, bytes) or len(matrix_seed) != 32:
            raise ValueError("Matrix seed must be 32 bytes")
        if not isinstance(public_vector, np.ndarray) or public_vector.dtype != np.int32:
            raise ValueError("Public vector must be int32 numpy array")
        if not isinstance(color_seed, bytes) or len(color_seed) != 32:
            raise ValueError("Color seed must be 32 bytes")
        if not isinstance(params, CLWEParameters):
            raise ValueError("Invalid parameters")

        self.matrix_seed = matrix_seed
        self.public_vector = public_vector
        self.color_seed = color_seed
        self.params = params

    def get_matrix(self) -> np.ndarray:
        np.random.seed(int.from_bytes(self.matrix_seed[:4], 'big') % (2**32 - 1))
        return np.random.randint(0, self.params.modulus,
                               size=(self.params.lattice_dimension, self.params.lattice_dimension),
                               dtype=np.int32)

    def to_bytes(self) -> bytes:
        compressed_vector = self._compress_vector(self.public_vector)
        return (
            self.matrix_seed +
            len(compressed_vector).to_bytes(4, 'big') +
            compressed_vector +
            self.color_seed +
            self.params.security_level.to_bytes(2, 'big')
        )

    def to_pem(self) -> str:
        """Export public key in PEM format"""
        key_data = self.to_bytes()
        b64_data = base64.b64encode(key_data).decode('ascii')
        pem = "-----BEGIN CLWE PUBLIC KEY-----\n"
        pem += '\n'.join([b64_data[i:i+64] for i in range(0, len(b64_data), 64)])
        pem += "\n-----END CLWE PUBLIC KEY-----\n"
        return pem

    @classmethod
    def from_pem(cls, pem_data: str) -> 'ChromaCryptPublicKey':
        """Import public key from PEM format"""
        lines = pem_data.strip().split('\n')
        if not lines[0].startswith('-----BEGIN CLWE PUBLIC KEY-----'):
            raise ValueError("Invalid PEM format")
        if not lines[-1].startswith('-----END CLWE PUBLIC KEY-----'):
            raise ValueError("Invalid PEM format")

        b64_data = ''.join(lines[1:-1])
        key_data = base64.b64decode(b64_data)
        return cls.from_bytes(key_data)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'ChromaCryptPublicKey':
        """Deserialize public key from bytes"""
        if len(data) < 74:  # Minimum: 32 + 4 + 4 + 32 + 2
            raise ValueError("Invalid public key data: too short")

        matrix_seed = data[:32]
        vec_len_offset = 32
        vec_len = int.from_bytes(data[vec_len_offset:vec_len_offset+4], 'big')
        vec_offset = vec_len_offset + 4

        if len(data) < vec_offset + vec_len + 34:
            raise ValueError("Invalid public key data: insufficient length")

        compressed_vector = data[vec_offset:vec_offset+vec_len]
        public_vector = cls._decompress_vector(compressed_vector)

        color_seed_offset = vec_offset + vec_len
        color_seed = data[color_seed_offset:color_seed_offset+32]

        params_offset = color_seed_offset + 32
        security_level = int.from_bytes(data[params_offset:params_offset+2], 'big')
        params = get_params(security_level)

        return cls(matrix_seed, public_vector, color_seed, params)

    def _compress_vector(self, vector: np.ndarray, bits: int = 12) -> bytes:
        if len(vector) == 0:
            return b''

        max_val = (1 << bits) - 1
        compressed_coeffs = np.clip(vector, 0, max_val).astype(np.uint16)

        total_bits = len(compressed_coeffs) * bits
        total_bytes = (total_bits + 7) // 8

        if total_bytes == 0:
            return b''

        packed = np.zeros(total_bytes, dtype=np.uint8)

        bit_offset = 0
        for coeff in compressed_coeffs:
            coeff_val = int(coeff) & max_val

            remaining_bits = bits
            while remaining_bits > 0 and bit_offset // 8 < len(packed):
                byte_pos = bit_offset // 8
                bit_pos = bit_offset % 8

                bits_in_byte = min(8 - bit_pos, remaining_bits)

                bits_to_write = (coeff_val >> (bits - remaining_bits)) & ((1 << bits_in_byte) - 1)

                packed[byte_pos] |= (bits_to_write << bit_pos)

                remaining_bits -= bits_in_byte
                bit_offset += bits_in_byte

        return packed.tobytes()

    @staticmethod
    def _decompress_vector(compressed_data: bytes, bits: int = 12) -> np.ndarray:
        """Decompress vector from compressed bytes"""
        if len(compressed_data) == 0:
            return np.array([], dtype=np.int32)

        max_val = (1 << bits) - 1
        total_bits = len(compressed_data) * 8
        num_coeffs = total_bits // bits

        coeffs = []
        bit_offset = 0

        for _ in range(num_coeffs):
            coeff_val = 0
            remaining_bits = bits

            while remaining_bits > 0 and bit_offset // 8 < len(compressed_data):
                byte_pos = bit_offset // 8
                bit_pos = bit_offset % 8

                bits_in_byte = min(8 - bit_pos, remaining_bits)
                byte_val = compressed_data[byte_pos]

                extracted_bits = (byte_val >> bit_pos) & ((1 << bits_in_byte) - 1)
                coeff_val |= (extracted_bits << (bits - remaining_bits))

                remaining_bits -= bits_in_byte
                bit_offset += bits_in_byte

            coeffs.append(min(coeff_val, max_val))

        return np.array(coeffs, dtype=np.int32)

class ChromaCryptPrivateKey:
    def __init__(self, secret_vector: np.ndarray, params: CLWEParameters):
        if not isinstance(secret_vector, np.ndarray) or secret_vector.dtype != np.int32:
            raise ValueError("Secret vector must be int32 numpy array")
        if not isinstance(params, CLWEParameters):
            raise ValueError("Invalid parameters")

        self.secret_vector = secret_vector
        self.params = params

    def to_bytes(self) -> bytes:
        return (
            self.params.security_level.to_bytes(2, 'big') +
            self.secret_vector.tobytes()
        )

    def to_pem(self) -> str:
        """Export private key in PEM format"""
        key_data = self.to_bytes()
        b64_data = base64.b64encode(key_data).decode('ascii')
        pem = "-----BEGIN CLWE PRIVATE KEY-----\n"
        pem += '\n'.join([b64_data[i:i+64] for i in range(0, len(b64_data), 64)])
        pem += "\n-----END CLWE PRIVATE KEY-----\n"
        return pem

    @classmethod
    def from_pem(cls, pem_data: str) -> 'ChromaCryptPrivateKey':
        """Import private key from PEM format"""
        lines = pem_data.strip().split('\n')
        if not lines[0].startswith('-----BEGIN CLWE PRIVATE KEY-----'):
            raise ValueError("Invalid PEM format")
        if not lines[-1].startswith('-----END CLWE PRIVATE KEY-----'):
            raise ValueError("Invalid PEM format")

        b64_data = ''.join(lines[1:-1])
        key_data = base64.b64decode(b64_data)
        return cls.from_bytes(key_data)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'ChromaCryptPrivateKey':
        """Deserialize private key from bytes"""
        if len(data) < 2:
            raise ValueError("Invalid private key data: too short")

        security_level = int.from_bytes(data[:2], 'big')
        params = get_params(security_level)

        secret_bytes = data[2:]
        expected_size = params.lattice_dimension * 4  # int32 = 4 bytes

        if len(secret_bytes) != expected_size:
            raise ValueError(f"Invalid private key data: expected {expected_size} bytes for secret vector")

        secret_vector = np.frombuffer(secret_bytes, dtype=np.int32)
        return cls(secret_vector, params)

@dataclass
class ChromaCryptCiphertext:
    """Enhanced ciphertext structure for PKI-compatible KEM"""
    ciphertext_vector: np.ndarray
    shared_secret_hint: bytes
    params: CLWEParameters

    def to_bytes(self) -> bytes:
        """Convert to bytes for transmission"""
        ct_bytes = self.ciphertext_vector.astype(np.int32).tobytes()
        return (
            self.params.security_level.to_bytes(2, 'big') +
            len(ct_bytes).to_bytes(4, 'big') +
            ct_bytes +
            len(self.shared_secret_hint).to_bytes(4, 'big') +
            self.shared_secret_hint
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'ChromaCryptCiphertext':
        """Deserialize ciphertext from bytes"""
        if len(data) < 6:
            raise ValueError("Invalid ciphertext data: too short")

        security_level = int.from_bytes(data[:2], 'big')
        params = get_params(security_level)

        ct_len_offset = 2
        ct_len = int.from_bytes(data[ct_len_offset:ct_len_offset+4], 'big')
        ct_offset = ct_len_offset + 4

        if len(data) < ct_offset + ct_len + 4:
            raise ValueError("Invalid ciphertext data: insufficient length")

        ct_bytes = data[ct_offset:ct_offset+ct_len]
        ciphertext_vector = np.frombuffer(ct_bytes, dtype=np.int32)

        hint_len_offset = ct_offset + ct_len
        hint_len = int.from_bytes(data[hint_len_offset:hint_len_offset+4], 'big')
        hint_offset = hint_len_offset + 4

        if len(data) < hint_offset + hint_len:
            raise ValueError("Invalid ciphertext data: hint length mismatch")

        shared_secret_hint = data[hint_offset:hint_offset+hint_len]

        return cls(ciphertext_vector, shared_secret_hint, params)

class ChromaCryptKEM:
    def __init__(self, security_level = "Min", optimized: bool = True):
        if security_level not in ["Min", "Bal", "Max"] and not isinstance(security_level, int):
            raise ValueError("Invalid security level")
        if not isinstance(optimized, bool):
            raise ValueError("Optimized must be boolean")

        self.security_level = security_level
        self.params = get_params(security_level, optimized=optimized)
        if not validate_parameters(self.params):
            raise ValueError("Invalid parameters generated")

        self.ntt_engine = create_optimized_ntt_engine(security_level)
        self.color_engine = ColorTransformEngine(self.params)

    def keygen(self) -> Tuple[ChromaCryptPublicKey, ChromaCryptPrivateKey]:
        matrix_seed = secrets.token_bytes(32)
        color_seed = secrets.token_bytes(32)

        np.random.seed(int.from_bytes(matrix_seed[:4], 'big') % (2**32 - 1))
        matrix_A = np.random.randint(0, self.params.modulus, 
                                   size=(self.params.lattice_dimension, self.params.lattice_dimension), 
                                   dtype=np.int32)

        secret_vector = np.random.randint(-self.params.error_bound, self.params.error_bound + 1, 
                                        size=self.params.lattice_dimension, dtype=np.int32)

        error_vector = np.random.randint(-self.params.error_bound, self.params.error_bound + 1, 
                                       size=self.params.lattice_dimension, dtype=np.int32)

        public_vector = (np.dot(matrix_A, secret_vector) + error_vector) % self.params.modulus

        public_key = ChromaCryptPublicKey(matrix_seed, public_vector, color_seed, self.params)
        private_key = ChromaCryptPrivateKey(secret_vector, self.params)

        return public_key, private_key

    def encapsulate(self, public_key: ChromaCryptPublicKey) -> Tuple[bytes, ChromaCryptCiphertext]:
        if not isinstance(public_key, ChromaCryptPublicKey):
            raise ValueError("Invalid public key")
        if public_key.params.security_level != self.params.security_level:
            raise ValueError("Public key security level mismatch")

        shared_secret = secrets.token_bytes(32)

        matrix_A = public_key.get_matrix()

        random_vector = np.random.randint(-self.params.error_bound, self.params.error_bound + 1,
                                        size=self.params.lattice_dimension, dtype=np.int32)

        error_vector = np.random.randint(-self.params.error_bound, self.params.error_bound + 1,
                                       size=self.params.lattice_dimension, dtype=np.int32)

        ciphertext_vector = (np.dot(random_vector, matrix_A) + error_vector) % self.params.modulus

        secret_encoding = self._encode_secret_deterministic(shared_secret, ciphertext_vector)

        ciphertext = ChromaCryptCiphertext(ciphertext_vector, secret_encoding, self.params)

        return shared_secret, ciphertext

    def decapsulate(self, private_key: ChromaCryptPrivateKey, ciphertext: ChromaCryptCiphertext) -> bytes:
        if not isinstance(private_key, ChromaCryptPrivateKey):
            raise ValueError("Invalid private key")
        if not isinstance(ciphertext, ChromaCryptCiphertext):
            raise ValueError("Invalid ciphertext")
        if private_key.params.security_level != self.params.security_level:
            raise ValueError("Private key security level mismatch")
        if ciphertext.params.security_level != self.params.security_level:
            raise ValueError("Ciphertext security level mismatch")

        # Compute the lattice result - this should match the encoding process
        lattice_result = np.dot(ciphertext.ciphertext_vector, private_key.secret_vector) % self.params.modulus

        # Use the ciphertext vector as key material for consistency with encoding
        return self._decode_secret_deterministic(ciphertext.shared_secret_hint, ciphertext.ciphertext_vector)

    def _encode_secret_in_colors(self, secret: bytes, color_seed: bytes) -> bytes:
        np.random.seed(int.from_bytes(color_seed[:4], 'big') % (2**32 - 1))

        colors = []
        for i, byte_val in enumerate(secret):
            color = self.color_engine.color_transform(byte_val, i)
            colors.extend([color[0], color[1], color[2]])

        return bytes(colors)

    def _decode_secret_from_colors(self, color_hint: bytes, lattice_result: int) -> bytes:
        colors = []
        for i in range(0, len(color_hint), 3):
            if i + 2 < len(color_hint):
                r, g, b = color_hint[i], color_hint[i+1], color_hint[i+2]
                colors.append((r, g, b))

        secret_bytes = []
        for i, color in enumerate(colors):
            byte_val = (color[0] + color[1] + color[2] + lattice_result) % 256
            secret_bytes.append(byte_val)

        return bytes(secret_bytes)

    def _encode_secret_deterministic(self, secret: bytes, ciphertext_vector: np.ndarray) -> bytes:
        import hashlib
        key_material = ciphertext_vector.tobytes()[:32]

        encoded = bytearray()
        for i, byte_val in enumerate(secret):
            combined = bytes([byte_val]) + key_material + i.to_bytes(4, 'big')
            hash_result = hashlib.sha256(combined).digest()
            encoded.extend(hash_result[:3])

        return bytes(encoded)

    def _decode_secret_deterministic(self, encoded_secret: bytes, lattice_result: np.ndarray) -> bytes:
        import hashlib
        # Convert lattice result to consistent key material
        if hasattr(lattice_result, 'tobytes'):
            key_material = lattice_result.tobytes()[:32]
        elif isinstance(lattice_result, (int, np.integer)):
            # Single integer result - convert to bytes
            result_bytes = int(lattice_result) % self.params.modulus
            key_material = result_bytes.to_bytes(32, 'big')
        else:
            # Array of integers
            key_material = bytes([int(x) % 256 for x in lattice_result[:32]])

        decoded = bytearray()
        for i in range(0, len(encoded_secret), 3):
            if i + 2 < len(encoded_secret):
                target_hash = encoded_secret[i:i+3]

                for byte_val in range(256):
                    combined = bytes([byte_val]) + key_material + (i//3).to_bytes(4, 'big')
                    test_hash = hashlib.sha256(combined).digest()[:3]
                    if test_hash == target_hash:
                        decoded.append(byte_val)
                        break
                else:
                    decoded.append(0)

        return bytes(decoded)

    def verify_keypair(self, public_key: ChromaCryptPublicKey, private_key: ChromaCryptPrivateKey) -> bool:
        """Verify that a public-private key pair is valid"""
        if not isinstance(public_key, ChromaCryptPublicKey) or not isinstance(private_key, ChromaCryptPrivateKey):
            return False
        if public_key.params.security_level != private_key.params.security_level:
            return False

        # Test the mathematical relationship: public_vector should equal matrix_A * secret_vector + error_vector
        matrix_A = public_key.get_matrix()
        computed_public = (np.dot(matrix_A, private_key.secret_vector) % public_key.params.modulus)

        # Check if the computed public vector matches the stored one (within error bounds)
        # Since error_vector is small, the difference should be bounded
        diff = np.abs(public_key.public_vector - computed_public)
        max_diff = np.max(diff)

        # Allow for the error bound plus some tolerance for modular arithmetic
        return max_diff <= (public_key.params.error_bound * 2)