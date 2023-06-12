import rsa, json, os


def main():
    
    public_key, private_key = rsa.newkeys(2048)
    
    #write keys to files
    with open("public_key.pem", "wb") as f:
        f.write(public_key.save_pkcs1())
    with open("private_key.pem", "wb") as f:
        f.write(private_key.save_pkcs1())
    
    
if __name__ == "__main__":

    main()

        
    