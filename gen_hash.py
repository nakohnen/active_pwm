import bcrypt
from getpass import getpass

def main():
    # Prompt the user for a password twice for verification
    password = getpass("Enter your password: ")
    password_verification = getpass("Confirm your password: ")
    
    # Check if the passwords match
    if password != password_verification:
        print("Passwords do not match. Please try again.")
        return
    
    # Convert the password to bytes, if not already done
    password_bytes = password.encode('utf-8')
    
    # Generate the hash
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    # Save the hash to a file
    with open('pw_hash.txt', 'wb') as f:
        f.write(hashed)
    
    print("Password hash generated and saved to pw_hash.txt")

if __name__ == "__main__":
    main()

