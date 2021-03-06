"""
kryptomancer OpenSSL System Calls


"""

import os
import sys
import json
import datetime
import asyncio
import logging
import subprocess
import time
import kryptomancer

from time import sleep
from threading import Thread
from flask import Flask, redirect, url_for, request, render_template
from werkzeug import secure_filename
from . import openssl

UPLOADS_FOLDER = os.getcwd() + '/uploads'
OPENSSL_OUTPUT_FOLDER = os.getcwd() + '/openssl_out'
RSA_FOLDER = os.getcwd() + '/temp'

def generate_key( bytes, base64=None):
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key-file.txt")
    p = subprocess.Popen(['touch', key_dir]) # creating the output file before using it to prevent throwing errors
    p.wait()
    key_file = open(key_dir, 'w+')
    if base64 is None:

        print(base64, file=sys.stderr)
        p = subprocess.Popen(
            ['openssl', 'rand', '-hex', bytes],
            stdout=key_file
        )
    elif base64 is True:
        print(base64, file=sys.stderr)
        p = subprocess.Popen(
            ['openssl', 'rand', '-base64', bytes],
            stdout=key_file
        )

    p.wait()

    key_file = open(key_dir, 'r')

    key = key_file.read()

    data = {
        'key' : key.split('\n')[0]
    }
    os.remove(key_dir)

    return data

def generate_aes_key_iv( bytes ):
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key-file.txt")
    iv_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "iv-file.txt")
    #print(iv_dir, key_dir)
    p = subprocess.Popen(['touch', key_dir, iv_dir]) # creating the output file before using it to prevent throwing errors
    p.wait()

    key_file = open(key_dir, 'w+')
    iv_file = open(iv_dir, 'w+')
    #print(iv_file, key_file)

    p1 = subprocess.Popen(
        ['openssl', 'rand', '-hex', str(int(bytes))],
        stdout=key_file
    )
    p2 = subprocess.Popen(
        ['openssl', 'rand', '-hex', str(16)],
        stdout=iv_file
    )
    
    exit_codes = [p.wait() for p in [p1, p2]]

    key_file = open(key_dir, 'r')
    iv_file = open(iv_dir, 'r')
    #print(iv_file, key_file)

    iv = iv_file.read()
    key = key_file.read()
    print('IV ' + iv + 'Key ' + key)

    data = {
        'iv' : iv.split('\n')[0],
        'key' : key.split('\n')[0]
    }
    os.remove(key_dir)
    os.remove(iv_dir)
    return data

def generate_3des_key_iv():
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key-file.txt")
    iv_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "iv-file.txt")
    #print(iv_dir, key_dir)
    p = subprocess.Popen(['touch', key_dir, iv_dir]) # creating the output file before using it to prevent throwing errors
    p.wait()

    key_file = open(key_dir, 'w+')
    iv_file = open(iv_dir, 'w+')
    #print(iv_file, key_file)

    p1 = subprocess.Popen(
        ['openssl', 'rand', '-hex', str(24)],
        stdout=key_file
    )
    p2 = subprocess.Popen(
        ['openssl', 'rand', '-hex', str(8)],
        stdout=iv_file
    )
    
    exit_codes = [p.wait() for p in [p1, p2]]

    key_file = open(key_dir, 'r')
    iv_file = open(iv_dir, 'r')
    #print(iv_file, key_file)

    iv = iv_file.read()
    key = key_file.read()
    print('IV ' + iv + 'Key ' + key)

    data = {
        'iv' : iv.split('\n')[0],
        'key' : key.split('\n')[0]
    }
    os.remove(key_dir)
    os.remove(iv_dir)
    return data

def digest_file( input_file, hash_algorithm ):

    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, input_file+'.'+str(hash_algorithm))
    p = subprocess.Popen(['touch', key_dir]) # creating the output file before using it to prevent throwing errors
    p.wait()
    key_file = open(key_dir, 'w+')

    file_path = os.path.join(UPLOADS_FOLDER, input_file)
    hash = '-' + hash_algorithm

    p1 = subprocess.Popen(
        ['openssl', 'dgst', hash, file_path,],
        stdout=key_file
    )
    p1.wait()
    key_file = open(key_dir, 'r')

    digest = key_file.read().split('=')[1]

    print('Digest'+hash_algorithm+ ' ' + digest)

    data = {
        'hash' : digest
    }
    
    key_file.close()
    os.remove(key_dir)

    return data

def hmac_file( input_file, hash_algorithm, key ):

    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key-file.txt")
    p = subprocess.Popen(['touch', key_dir]) # creating the output file before using it to prevent throwing errors
    p.wait()
    key_file = open(key_dir, 'w+')

    file_path = os.path.join(UPLOADS_FOLDER, input_file)
    hash = '-' + hash_algorithm

    p1 = subprocess.Popen(
        ['openssl', 'dgst', hash, '-hmac', key, file_path,],
        stdout=key_file
    )
    p1.wait()
    key_file = open(key_dir, 'r')

    hmac = key_file.read().split('=')[1]

    print('HMAC'+hash_algorithm+ ' ' + hmac)

    data = {
        'hmac' : hmac
    }

    key_file.close()
    os.remove(key_dir)

    return data


"""
Generates keys for symmetric file encryption and saves them in a file to be encrypted with RSA
Returns:
    generated keys,
    name of the file to be encrypted with RSA (containing the keys)
"""
def keys_for_RSA_session( input_file ):
    output_filename = input_file.split('.')[0]+".keys"
    output_file = os.path.join(OPENSSL_OUTPUT_FOLDER, output_filename )
    p = subprocess.Popen(['touch', output_file]) # creating the output file before using it to prevent throwing errors
    p.wait()
    data = generate_aes_key_iv(32)

    key_file = open(output_file, 'w+')

    key_file.write(input_file+".enc\n"+data['iv']+"\n"+ data['key'])

    data['key_filename'] = output_filename

    return data


"""
CIFRAR O FICHEIRO SECRET.KEY PARA SECRET.RSA UTILIZANDO A CHAVE PUBLICA DE ALGUÉM:
	-> openssl rsautl -encrypt -in secret.key -out secret.rsa -inkey alguem-pk.pem -pubin
"""

def rsa_encrypt(input_file, key_file):
    file_path = os.path.join(OPENSSL_OUTPUT_FOLDER, input_file)
    key_file = os.path.join(RSA_FOLDER, key_file)
    enc_file = os.path.join(UPLOADS_FOLDER,  input_file + ".rsaenc")
    p = subprocess.Popen(['touch', enc_file]) # creating the output file before using it to prevent throwing errors
    p.wait()


    print("openssl rsautl -encrypt -in " + file_path +" -out " +enc_file + " -inkey "+key_file + " -pubin", file=sys.stderr )

    try:
        p = subprocess.Popen(
                    ['openssl', 'rsautl', '-encrypt', '-in', file_path, '-out', enc_file, '-inkey', key_file, '-pubin'],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
        p.wait()
        return {'ok':'ok'}
    except:
        print('Failed to encrypt: ' + str(file_path), file=sys.stderr)
        return {'error':'failed'}

"""
DECIFRAR O FICHEIRO SECRET.RSA PARA SECRET-2.KEY UTILIZANDO A MINHA CHAVE PRIVADA
	-> openssl rsautl -decrypt -in secret.rsa -out secret-2.key -inkey pk-and-sk.pem
"""

def rsa_decrypt(input_file, key_file):
    file_path = os.path.join(UPLOADS_FOLDER, input_file)
    key_file = os.path.join(RSA_FOLDER, key_file)
    dec_file = os.path.join(UPLOADS_FOLDER,  input_file + ".rsadec")
    p = subprocess.Popen(['touch', dec_file]) # creating the output file before using it to prevent throwing errors
    p.wait()


    print("openssl rsautl -decrypt -in " + file_path +" -out " +dec_file + " -inkey "+key_file, file=sys.stderr )

    try:
        p = subprocess.Popen(
                    ['openssl', 'rsautl', '-decrypt', '-in', file_path, '-out', dec_file, '-inkey', key_file],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
        p.wait()

        dec_ = open(dec_file, 'r')
        read = dec_.read()

        filename = read.split('\n', 1)[0]
        
        return {'ok':'Decrypt OK', 'session_file' : filename}
        
    except:
        print('Failed to decrypt: ' + str(file_path), file=sys.stderr)
        return {'error':'failed'}



def encrypt_file( input_file, key, iv, cipher = None, base64=None):
    file_path = os.path.join(UPLOADS_FOLDER, input_file)
    enc_file = os.path.join(UPLOADS_FOLDER,  input_file + ".enc")
    p = subprocess.Popen(['touch', enc_file]) # creating the output file before using it to prevent throwing errors
    p.wait()

    if cipher is not None:
        print('Cipher selected: ' + cipher, file=sys.stderr)
        input_cipher = '-' + cipher
        print('Encrypting file: ' + str(file_path) +'\nWith Key:  ' +str(key) + 'And IV:   ' +str(iv), file=sys.stderr)
        try:
            if base64 is not None:
                p = subprocess.Popen(
                    ['openssl', 'enc', input_cipher, '-e', '-a', '-in', file_path, '-out', enc_file, '-K', key, '-iv', iv],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
            else:
                p = subprocess.Popen(
                    ['openssl', 'enc', input_cipher, '-e', '-in', file_path, '-out', enc_file, '-K', key, '-iv', iv],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
            p.wait()
            return {'ok':'ok'}
        except:
            print('Failed to encrypt: ' + str(file_path), file=sys.stderr)
            return {'error':'failed'}


def decrypt_file( input_file, key, iv, cipher = None, base64=None ):
    file_path = os.path.join(UPLOADS_FOLDER, input_file)
    dec_file = os.path.join(UPLOADS_FOLDER, input_file.rsplit('.', 1)[0] + ".dec")
    p = subprocess.Popen(['touch', dec_file]) # creating the output file before using it to prevent throwing errors
    p.wait()

    if cipher is not None:
        print('Cipher selected: ' + cipher, file=sys.stderr)
        input_cipher = '-' + cipher
        print('Decrypting file: ' + str(file_path) +'\nWith Key:  ' +str(key) + 'And IV:   ' +str(iv), file=sys.stderr)
        try:
            if base64 is not None:
                p = subprocess.Popen(
                    ['openssl', 'enc', input_cipher, '-d', '-a', '-in', file_path, '-out', dec_file, '-K', key, '-iv', iv],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
            else:
                p = subprocess.Popen(
                    ['openssl', 'enc', input_cipher, '-d', '-in', file_path, '-out', dec_file, '-K', key, '-iv', iv],
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE
                )
                
            p.wait()

            original_file = os.path.join(UPLOADS_FOLDER, input_file.rsplit('.', 1)[0])
            stat_original = os.stat(original_file)
            stat_dec = os.stat(dec_file)
            if stat_original.st_size == stat_dec.st_size:
                return {'ok':'Decrypt OK'}
            else:
                return {'error': 'Decrypt Failed'}
        except:
            print('Failed to decrypt: ' + str(file_path), file=sys.stderr)
            return {'error':'failed'}


#openssl genrsa -out mykey.pem
#will actually produce a public - private key pair. The pair is stored in the generated mykey.pem file.
def generate_rsa( sk_file  ):
    sk_path = os.path.join(RSA_FOLDER, sk_file + '.pem')
    pk_path = os.path.join(RSA_FOLDER, sk_path.split('.')[0] + '.pub')
    p = subprocess.Popen(['touch', pk_path, sk_path]) # creating the output file before using it to prevent throwing errors
    p.wait()
    try:
            
        p = subprocess.Popen(
                ['openssl', 'genrsa', '-out', sk_path],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )
                
        p.wait()

        #openssl rsa -in mykey.pem -pubout -out mykey.pub
        #will extract the public key and print that out. Here is a link to a page that describes this better.

        p = subprocess.Popen(
                ['openssl', 'rsa', '-in', sk_path, '-pubout', '-out', pk_path ],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )
                
        p.wait()
        return {'ok':'ok'}
    except:
        print('Failed to encrypt: ' + str(sk_path), file=sys.stderr)
        return {'error':'failed'}


# openssl rsa -in teste1.pem.pub -pubin (to view PK)
# or
# openssl rsa -in teste1.pem (to view SK)
#this function will receive a .pem file and extract the PK/SK to show the user in the app
def view_key_from_pem( input_file ):
    input_file_path = os.path.join(RSA_FOLDER, input_file) #concat input file name and temp folder path
    split = input_file.split('.')[-1] #check file extension
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key."+split) #concat output file name and openssl's output folder path

    key_file = open(key_dir, 'w+')
    print(input_file_path, file=sys.stderr)
    
    if split == 'pem':
        try:            
            p = subprocess.Popen(
                    ['openssl', 'rsa', '-in', input_file_path],
                    stdout=key_file
                )
                    
            p.wait()
        except:
            print('Failed to extract SK from: ' + str(input_file_path), file=sys.stderr)
            return {'error':'failed'}
    elif split == 'pub':
        try:            
            p = subprocess.Popen(
                    ['openssl', 'rsa', '-in', input_file_path, '-pubin', ],
                    stdout=key_file
                )
                    
            p.wait()
        except:
            print('Failed to extract PK from: ' + str(input_file_path), file=sys.stderr)
            return {'error':'failed'}

    key_file = open(key_dir, 'r')

    key = key_file.read()
    if 'pem' in split:
        data = {
            'sk' : key
        }
    elif 'pub' in split:
        data = {
            'pk' : key
        }
    os.remove(key_dir)
    return data

# openssl dgst -HASH -sign PRIVATE_KEY FILE_TO_SIGN > FILE.SIG
# openssl dgst -sha256 -sign /private-key-file.pem file-to-sign > file.sig
def sign_file_with_private_key( file_to_verify, private_key_file , hash_algorithm):
    input_file_path = os.path.join(UPLOADS_FOLDER, file_to_verify) #concat input file name and uploads folder path
    private_key_file_path = os.path.join(RSA_FOLDER, private_key_file) #concat private key file name and temp folder path
    output_file_path = os.path.join(UPLOADS_FOLDER, file_to_verify+".sig")#concat output file name and uploads folder path
    p = subprocess.Popen(['touch', output_file_path]) # creating the output file before using it to prevent throwing errors
    p.wait()
    split = private_key_file.split('.')[-1] #get PK file extension used for assertion in signing procedure
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key."+split) #concat output file name and openssl's output folder path


    key_file = open(key_dir, 'w+')
    print(input_file_path, file=sys.stderr)

    hash = '-' + hash_algorithm
    print("openssl dgst " + hash + " -sign " + private_key_file_path +" -out " +output_file_path + " "+input_file_path )
    
    if split == 'pem':
        try:
            p1 = subprocess.Popen(
                ['openssl', 'dgst', hash, '-sign', private_key_file_path, '-out', output_file_path, input_file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p1.wait()

            return {'ok':'ok'}

        except:
            return {'error':'failed_to_sign'}

    else:
        return {'error':'invalid_pk_file'}



# openssl dgst -HASH -verify PUBLIC_KEY_TO_VERIFY -signature SIGNED_FILE_TO_VERIFY FILE_TO_VERIFY > VERIFICATION_RESULT
# openssl dgst -sha256 -verify /private-key-file.pem.pub -signature /file.sig file-to-sign > verif_result.txt

def verify_file_with_public_key( file_to_verify, public_key_file, signed_file, hash_algorithm ):
    signed_file_path = os.path.join(UPLOADS_FOLDER, signed_file) #concat signed file name and uploads folder path
    input_file_path = os.path.join(UPLOADS_FOLDER, file_to_verify) #concat input file name and uploads folder path
    public_key_file_path = os.path.join(RSA_FOLDER, public_key_file) #concat public key file name and temp folder path
    output_file_path = os.path.join(UPLOADS_FOLDER, file_to_verify+".ver")#concat output file name and uploads folder path
    p = subprocess.Popen(['touch', output_file_path]) # creating the output file before using it to prevent throwing errors
    p.wait()
    split = public_key_file.split('.')[-1] #get PK file extension used for assertion in signing procedure
    key_dir=os.path.join(OPENSSL_OUTPUT_FOLDER, "key."+split) #concat output file name and openssl's output folder path

    key_file = open(key_dir, 'w+')
    print(input_file_path, file=sys.stderr)

    hash = '-' + hash_algorithm
    print("openssl dgst " + hash + " -sign " + public_key_file_path +" -signature " + signed_file_path + " -out " +output_file_path + " "+input_file_path )
    

    if split == 'pub':
        try:
            p1 = subprocess.Popen(
                ['openssl', 'dgst', hash, '-verify', public_key_file_path, '-signature', signed_file_path, '-out', output_file_path, input_file_path ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p1.wait()

            output_file = open(output_file_path, 'r')
            status = output_file.read()
            output_file.close()
            os.remove(output_file_path)
            if 'OK' in status:
                return {'ok': status}
            else:
                return {'error': status}

        except:
            return {'error':'failed_to_verify'}

    else:
        return {'error':'invalid_pk_file'}


