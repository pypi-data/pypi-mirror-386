
# Example usage
if __name__ == "__main__":
    # Example 1: Register a new device
    try:
        import os
        
        mosquito_cert_dir = f"/etc/vyomcloudbridge/certs_mosquitto/"
        mosquito_cert_fname = "cert.pem"
        mosquito_cert_fpath = os.path.join(mosquito_cert_dir, mosquito_cert_fname)
        mosquito_pri_key_fname = "pri.key"
        mosquito_pri_key_fpath = os.path.join(mosquito_cert_dir, mosquito_pri_key_fname)
        mosquito_pub_key_fname = "pub.key"
        mosquito_pub_key_fpath = os.path.join(mosquito_cert_dir, mosquito_pub_key_fname)
        mosquito_ca_cert_fname = "ca_cert.crt"
        mosquito_ca_cert_fpath = os.path.join(mosquito_cert_dir, mosquito_ca_cert_fname)


        # TODO
        # create nested dir if not exist mosquito_cert_dir
        os.makedirs(mosquito_cert_dir, exist_ok=True)
        # Save files similar to AWS IoT example
        with open(mosquito_cert_fpath, "w") as f:
            f.write("-----BEGIN CERTIFICATE-----\nMIIDPDCCAiQCFC03EQrFMjDS57ts4C2I8SDeLDKEMA0GCSqGSIb3DQEBCwUAMFox\nCzAJBgNVBAYTAklOMRIwEAYDVQQIDAlLYXJuYXRha2ExEjAQBgNVBAcMCUJlbmdh\nbHVydTEPMA0GA1UECgwGVnlvbUlRMRIwEAYDVQQDDAlWeW9tSVEtQ0EwHhcNMjUw\nNzA0MTAwMjI2WhcNMjYwNzA0MTAwMjI2WjBbMQswCQYDVQQGEwJJTjESMBAGA1UE\nCAwJS2FybmF0YWthMRIwEAYDVQQHDAlCZW5nYWx1cnUxDzANBgNVBAoMBlZ5b21J\nUTETMBEGA1UEAwwKbWFjaGluZV8zMzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC\nAQoCggEBALspeQSor971uX24YyGpql0vdU2ANPlaIhN0vwHBsAYDtNEYfXBrhDJ/\ngz1C8j0UgwAJOTl9YJ/FdMz3kP3JROm8eSTVQf55Vrrv3+HDiu52fInbRLI3s4s5\n0mzMaraJ0bngeCAhAQtoOOPwG//eOxlSG9UaTnP1c2p73fiT6RmmwNX+Kjk6l5aY\nPldfQxIt254/p7D37/2APQvX0QsvOHy1TsG1a3jmMZ3ViMlaGZgUPeo1JU5E2Mbf\nuDfdx2xvy7mHm+zj1Ra90EW47BWIO4xwR2EjqWdgoXiaPOtLC3Pfc6fko+2Zv5y4\nGk+1qGuRJh8I6IEyEY/WLjc6ayplgskCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEA\nx3Lu3iHeLOZmvgnpxVozj5A+I8BZgo692G9HkZnY+To2cZU/Gobrsn8s8zRkRoE7\nU2sVSPgvpzaKAsgKge1wd2yjozKGEYNQBJM81Mp6Ad8kZ2++3Za+LWDwwk1ZQTXx\ncGcXAvNpxFFGR12CFW7hqvJakP9FfiqeCtDRdzkZ0WS5PODqBmaUYWoW69zTYAJy\nu+aTYyT9zYncyWwHkkNJI/fCUaKU+6z8MeEfOxxJ/BqdlvTHEpX+geV/pkkqvn1k\n65ljjJGq8przWKctRKAdFxVXgczdA1PrYW9r7lOa7lHrF/syft2xy0cq7iVtz7Gc\nSlKSWjv6JBReGB11agX0gA==\n-----END CERTIFICATE-----\n")

        with open(mosquito_pri_key_fpath, "w") as f:
            f.write("-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7KXkEqK/e9bl9\nuGMhqapdL3VNgDT5WiITdL8BwbAGA7TRGH1wa4Qyf4M9QvI9FIMACTk5fWCfxXTM\n95D9yUTpvHkk1UH+eVa679/hw4rudnyJ20SyN7OLOdJszGq2idG54HggIQELaDjj\n8Bv/3jsZUhvVGk5z9XNqe934k+kZpsDV/io5OpeWmD5XX0MSLdueP6ew9+/9gD0L\n19ELLzh8tU7BtWt45jGd1YjJWhmYFD3qNSVORNjG37g33cdsb8u5h5vs49UWvdBF\nuOwViDuMcEdhI6lnYKF4mjzrSwtz33On5KPtmb+cuBpPtahrkSYfCOiBMhGP1i43\nOmsqZYLJAgMBAAECggEAAZlDsMSygK7ZDCtEbxr6GvYQndfbG/vA6Y+h7gu2GDPb\ngIm7NvgEI6l8X0wwfrfevDC+YP2I+Y4ABs9g8q02CuHfdKJ85mwpthd3pX/V5cTA\n7ZO5s35pHABWo5oSma3CfkCRMunbqDnjFB3B73gtFkGusS3nWHNseyiRtDgQ0dvb\nntEyGL1AMltYjn26NiTBVW/GfBs+VjdGiDblDSUdfofVb3hDMSVhDV/DAf4xAIGW\nDpnsvs/dwqJy53Ddfj1iqBfYhKHsgxJ6FqLEHYygfiJAk3XRPnA7uzJ9UJear5J8\n0MqIdQg7koNqZey4MDvFdioOIKt5iOZTBYS7d6ieDQKBgQD1Bi9Y1Wk/i71ISQS1\nDWEBLA+P2X0pJNtWT6AejEhhPUaK8Y6KzHpIpsn9KarDHmOz/FN3JJ+E0gDJw0cq\n3OBfRrUqpHgjNcFmBw5YF7WOk9meIg2vp/5zf/C3+OfMOE0OxQzenqVYT6l36ZrA\n+TiAddI80yiL575UHXyUuOreMwKBgQDDi8DdIG9Tphdde1ZM9RWHlf2keMIwLrQb\njwYA84e0A6ZjjG0ACnT3KbVORiUM/MJMkIIJSXgRPDTXdSaxdReQuQR3d2md2cQA\nX2Jv/pS8uGhsSCS+o1xucAJ1uhWm9eP7q3Da0VZbQLclfXcjAmqHsO8yhypDW+EC\n32kPPq3nEwKBgQC/xwKB9i91hEs3a6daikk1oKXhgmn7LRTbvmDl6Aiyy0IOeDiI\nHLlNafZIxzcXlw6UjldJtomAbNofEU//lXesOuyLnsVFUcq4r6cjfhMlsEUxBxhN\nNyDqh+YCKLhM2Hg/qi2DhQqHT3qmF1p/1dDKgu11nBRtRIpszdN3mDCEjwKBgDzO\nSVO5kUSmoh9cifJ2R5KYzn2FW4UWEMV9DPXgxHLyq5vK/94CYmq1Gn7TixPlyRl7\n2iO/J8ncOeZBtJ179q73CW+Iv1vpamxfPMHsnR2uDjKVoG9zZvukcu9exPrc/V61\n6erxK3RGxGyw/gnx52R4XXkN1NOLT4XQKOAnsnXnAoGARABpPnmUHbKBwrvbfqbJ\nBQkjGs/hagN5BLd85hXawbwm20RRkTjpF4jjuJ3IpcRslfxHPZ6Hmyr5wfiKlBpT\nuAmNi1+s4Nhe3l0zT1CaWRR5C+/yrRKDQRLXzkkHNMtBCRTIYEMW3DD3XlOwNCtJ\nX20Ck7A0tPn1MSl9m6vr4jk=\n-----END PRIVATE KEY-----\n")

        with open(mosquito_pub_key_fpath, "w") as f:
            f.write("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuyl5BKiv3vW5fbhjIamq\nXS91TYA0+VoiE3S/AcGwBgO00Rh9cGuEMn+DPULyPRSDAAk5OX1gn8V0zPeQ/clE\n6bx5JNVB/nlWuu/f4cOK7nZ8idtEsjeziznSbMxqtonRueB4ICEBC2g44/Ab/947\nGVIb1RpOc/Vzanvd+JPpGabA1f4qOTqXlpg+V19DEi3bnj+nsPfv/YA9C9fRCy84\nfLVOwbVreOYxndWIyVoZmBQ96jUlTkTYxt+4N93HbG/LuYeb7OPVFr3QRbjsFYg7\njHBHYSOpZ2CheJo860sLc99zp+Sj7Zm/nLgaT7Woa5EmHwjogTIRj9YuNzprKmWC\nyQIDAQAB\n-----END PUBLIC KEY-----\n")

        with open(mosquito_ca_cert_fpath, "w") as f:
            f.write("-----BEGIN CERTIFICATE-----\nMIIDlTCCAn2gAwIBAgIUILjFfsKT8pjj4jDMHqZ9hE0xMbUwDQYJKoZIhvcNAQEL\nBQAwWjELMAkGA1UEBhMCSU4xEjAQBgNVBAgMCUthcm5hdGFrYTESMBAGA1UEBwwJ\nQmVuZ2FsdXJ1MQ8wDQYDVQQKDAZWeW9tSVExEjAQBgNVBAMMCVZ5b21JUS1DQTAe\nFw0yNTA3MDQwOTM5MDZaFw0zNTA3MDIwOTM5MDZaMFoxCzAJBgNVBAYTAklOMRIw\nEAYDVQQIDAlLYXJuYXRha2ExEjAQBgNVBAcMCUJlbmdhbHVydTEPMA0GA1UECgwG\nVnlvbUlRMRIwEAYDVQQDDAlWeW9tSVEtQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IB\nDwAwggEKAoIBAQDaa/GO6XdHBobTWJ37yDoZRV4L4vFoJVnGCFee9p2Jt9vItogX\n7l2G/4omt1ovcH2fpvX3jFe7xkK9HOtctMC+0arDaV2mfZhzXHPCHju/PwcFG6+h\nNpUmjzbcfyH+LPSHt+sTp8iKavLzTy4J4MAv94uSaFsLvI5jRgxyfO7M14EN4LV/\nc4vAEfvN37JfmlBvFbWu5YhXPiWjVSDIRyt20+6OUKd1aU9QBL54ugXmz63rHHzL\neRKeHdXmBLQIURym3d5juOml00myOP9dnQ7ovmBI/8J+W9PHrQLlh1+sz1illC1o\n38PCzLJrg3QGmb+2m8APWfsiMSNi+k9nHC4bAgMBAAGjUzBRMB0GA1UdDgQWBBSM\nAFC6aHffL0wETR1QpszyrH4TtzAfBgNVHSMEGDAWgBSMAFC6aHffL0wETR1Qpszy\nrH4TtzAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQBogReOWg6I\n72FdxHUy1LaGThl8Hk3DAsJTcLO51/V38UNhyBvEmEOwwBX59NSyt2A1eGGIEPsq\nvWEAHfIL/0dOs/l5eJtuPHazHuV6WSw3f1Zm557fd4pN8IBowBEFMQpao2owVg5i\nbLYXrZWUyjas+sG4tza2CCoqnWR9TXgLF6GE4trtixm9ccn7PG6PwB5z1whIjgb2\nfCxxfL0bG1HlS3R3lL+BLoqSVFo369R3ueY4O722GXnot1cqa76MP8Ir0qQz5QTq\nsHU8KPmydeAen8RNI7vd+ylQdByDedU3KAAYQGGX+8sbAecea3yhcoWNURL9qbte\nySjMt3Rr3TL5\n-----END CERTIFICATE-----\n")

        print(f"Certificate files saved")

    except Exception as e:
        print(f"Failed to register device: {e}")
