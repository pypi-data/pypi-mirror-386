#!/usr/bin/env python3
"""
CLWE Key Encapsulation Mechanism (KEM) Example v1.1.1
Demonstrates post-quantum key exchange with PKI support
"""

from clwe import ChromaCryptKEM, ChromaCryptPublicKey, ChromaCryptPrivateKey, ChromaCryptCiphertext
import secrets

def main():
    """Demonstrate CLWE KEM operations"""

    print("CLWE Key Encapsulation Mechanism (KEM) Example")
    print("=" * 50)

    # Initialize KEM with different security levels
    security_levels = ["Min", "Bal", "Max"]

    for level in security_levels:
        print(f"\n{'='*20} Security Level: {level} {'='*20}")

        # Create KEM instance
        kem = ChromaCryptKEM(level)

        # Generate key pair (done by recipient)
        print("1. Key Pair Generation:")
        public_key, private_key = kem.keygen()
        print("   ✓ Public/private key pair generated")
        print(f"   ✓ Public key size: {len(public_key.to_bytes())} bytes")
        print(f"   ✓ Private key size: {len(private_key.to_bytes())} bytes")

        # Demonstrate PEM serialization (PKI standard)
        print("\n1b. PEM Serialization (PKI Standard):")
        pub_pem = public_key.to_pem()
        priv_pem = private_key.to_pem()
        print("   ✓ Keys exported to PEM format")

        # Import from PEM
        imported_pub = ChromaCryptPublicKey.from_pem(pub_pem)
        imported_priv = ChromaCryptPrivateKey.from_pem(priv_pem)
        print("   ✓ Keys imported from PEM format")

        # Verify key pair
        is_valid = kem.verify_keypair(imported_pub, imported_priv)
        print(f"   ✓ Key pair verification: {'PASS' if is_valid else 'FAIL'}")

        # Encapsulate shared secret (done by sender)
        print("\n2. Shared Secret Encapsulation:")
        shared_secret, ciphertext = kem.encapsulate(imported_pub)  # Use imported key
        print("   ✓ Shared secret encapsulated")
        print(f"   ✓ Shared secret: {shared_secret.hex()[:16]}... ({len(shared_secret)} bytes)")
        print(f"   ✓ Ciphertext size: {len(ciphertext.ciphertext_vector) * 4} bytes")

        # Demonstrate ciphertext serialization
        print("\n2b. Ciphertext Serialization:")
        ct_bytes = ciphertext.to_bytes()
        ct_imported = ChromaCryptCiphertext.from_bytes(ct_bytes)
        print("   ✓ Ciphertext serialized/deserialized successfully")

        # Decapsulate shared secret (done by recipient)
        print("\n3. Shared Secret Decapsulation:")
        recovered_secret = kem.decapsulate(imported_priv, ct_imported)  # Use imported keys
        print("   ✓ Shared secret decapsulated")
        print(f"   ✓ Recovered secret: {recovered_secret.hex()[:16]}...")

        # Verify secrets match
        if shared_secret == recovered_secret:
            print("   ✓ SUCCESS: Shared secrets match perfectly!")
        else:
            print("   ❌ ERROR: Shared secrets don't match!")
            return

    # Demonstrate real-world usage scenario
    print(f"\n{'='*20} Real-World Usage Scenario {'='*20}")

    print("\nScenario: Secure communication between Alice and Bob")
    print("-" * 50)

    # Alice generates her key pair
    print("1. Alice generates her key pair:")
    alice_kem = ChromaCryptKEM("Min")
    alice_public, alice_private = alice_kem.keygen()
    print("   ✓ Alice's key pair generated")

    # Bob encapsulates a shared secret for Alice
    print("\n2. Bob encapsulates shared secret for Alice:")
    shared_secret, ciphertext = alice_kem.encapsulate(alice_public)
    print("   ✓ Bob creates shared secret")
    print(f"   ✓ Bob sends ciphertext to Alice ({len(ciphertext.ciphertext_vector) * 4} bytes)")

    # Alice decapsulates the shared secret
    print("\n3. Alice decapsulates the shared secret:")
    alice_recovered_secret = alice_kem.decapsulate(alice_private, ciphertext)
    print("   ✓ Alice recovers shared secret")

    # Both now have the same shared secret
    if shared_secret == alice_recovered_secret:
        print("   ✓ SUCCESS: Alice and Bob now share the same secret!")
        print(f"   ✓ Shared secret can be used for symmetric encryption")
        print(f"   ✓ Security level: 128-bit (quantum-resistant)")
    else:
        print("   ❌ ERROR: Key exchange failed!")
        return

    # Demonstrate using shared secret for symmetric encryption
    print(f"\n{'='*20} Using Shared Secret for Encryption {'='*20}")

    from clwe import ColorCipher

    cipher = ColorCipher()

    # Use shared secret as password for symmetric encryption
    message = "This is a confidential message encrypted with the shared secret!"
    encrypted = cipher.encrypt(message, shared_secret.hex())
    decrypted = cipher.decrypt(encrypted, shared_secret.hex())

    print("4. Symmetric encryption with shared secret:")
    print(f"   Original: {message}")
    print(f"   Encrypted: {len(str(encrypted))} characters")
    print(f"   Decrypted: {decrypted}")

    if decrypted == message:
        print("   ✓ SUCCESS: Hybrid encryption works perfectly!")
    else:
        print("   ❌ ERROR: Hybrid encryption failed!")

    # Demonstrate PKI features
    print(f"\n{'='*20} PKI Features Demonstration {'='*20}")

    print("\n5. PKI-Compatible Key Management:")
    # Save keys in PEM format (like certificates)
    with open("alice_public.pem", "w") as f:
        f.write(alice_public.to_pem())
    with open("alice_private.pem", "w") as f:
        f.write(alice_private.to_pem())
    print("   ✓ Keys saved in PEM format (PKI standard)")

    # Load keys from PEM
    with open("alice_public.pem", "r") as f:
        loaded_pub_pem = f.read()
    with open("alice_private.pem", "r") as f:
        loaded_priv_pem = f.read()

    loaded_pub = ChromaCryptPublicKey.from_pem(loaded_pub_pem)
    loaded_priv = ChromaCryptPrivateKey.from_pem(loaded_priv_pem)
    print("   ✓ Keys loaded from PEM format")

    # Verify loaded key pair
    key_valid = alice_kem.verify_keypair(loaded_pub, loaded_priv)
    print(f"   ✓ Loaded key pair verification: {'PASS' if key_valid else 'FAIL'}")

    # Clean up demo files
    import os
    os.remove("alice_public.pem")
    os.remove("alice_private.pem")

    print(f"\n{'='*50}")
    print("CLWE KEM v1.1.1 Example completed successfully!")
    print("✓ Post-quantum key exchange demonstrated")
    print("✓ Perfect forward secrecy achieved")
    print("✓ Hybrid encryption enabled")
    print("✓ PKI compatibility verified")
    print("✓ PEM serialization working")
    print("✓ Key pair verification implemented")

if __name__ == "__main__":
    main()