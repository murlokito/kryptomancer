"""
Kryptoflask Application Routes


"""

import os
import sys
import requests
import json
import datetime
import asyncio
import logging
import subprocess
import time
import kryptoflask


from time import sleep
from threading import Thread
from flask import Flask, redirect, url_for, request, render_template
from werkzeug import secure_filename

from . import routes
from kryptoflask.openssl import (
    generate_key_iv, generate_key, encrypt_file 
)

UPLOAD_FOLDER = os.getcwd() + '/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes.route('/')
def index():

    return render_template('index.html')

@routes.route('/crypter/generate_keys_from_selected_files', methods=['GET', 'POST']) 
def generate_keys_from_files():
    """
    Esta função serve a página do Crypter com chaves geradas para cada um dos ficheiros selecionados
    Retorna o nome do ficheiro e o seu conteudo
    """
    print('/crypter/generate_keys_from_selected_files', file=sys.stderr)
    files, enc = get_uploaded_files()
    selected_files = request.form.getlist('selected_files')
    if selected_files is not None:
        for file in selected_files:
            print(file, file=sys.stderr)
        enc_info = generate_keys_for_files(selected_files)
    else:
        selected_enc_files = request.form.getlist('selected_enc_files')
        if selected_enc_files is not None:
            for file in selected_enc_files:
                print(file, file=sys.stderr)
        else:
            return render_template('file_crypter.html', listdir=os.listdir(UPLOAD_FOLDER), enc_files=enc)

    return render_template('file_crypter.html', listdir=os.listdir(UPLOAD_FOLDER), enc_files=enc, enc_info=enc_info['data'])

@routes.route('/crypter/', methods=['GET', 'POST']) 
def crypter():
    """
    Esta função serve uma página com um form de upload de ficheiros
    Retorna o nome do ficheiro e o seu conteudo
    """
    print('crypter', file=sys.stderr)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            files, enc = get_uploaded_files()
            return render_template('file_crypter.html', listdir=files, enc_files=enc)
            
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            files, enc = get_uploaded_files()
            return render_template('file_crypter.html', name=filename, listdir=files, enc_files=enc )
        else:
            files, enc = get_uploaded_files()
            return render_template('file_crypter.html', error="File not supported.", listdir=files, enc_files=enc )
    else:
        files, enc = get_uploaded_files()

    return render_template('file_crypter.html', listdir=files, enc_files=enc)

@routes.route('/encrypt_file/', methods=['GET','POST'])
def encrypt():
    """
    Esta função é chamada quando o botão "Encrypt" da página "File_Crypter" é pressionado
    Retorna o nome dos ficheiros apagados
    """
    print('encrypt', file=sys.stderr)
    if request.method == 'POST':
        # check if the post request has the file part
        selected_files = request.form.getlist('selected_files')
        if selected_files is not None:
            print('------------ Files Selected:', file=sys.stderr)
            for file in selected_files:
                print(file, file=sys.stderr)
            enc_info = encrypt_list_of_files(selected_files)
            print('------------ Files Encrypted:', file=sys.stderr)
            for item in enc_info:
                print(item, file=sys.stderr)
        else:
            """selected_enc_files = request.form.getlist('selected_enc_files')
            if selected_enc_files is not None:
                for file in selected_enc_files:
                    print(file, file=sys.stderr)
            else:"""
            return render_template('file_crypter.html', listdir=os.listdir(UPLOAD_FOLDER), enc_info=enc_info['data'])
        files, enc = get_uploaded_files()
        return render_template('file_crypter.html', listdir=files, enc_files=enc, enc_info=enc_info['data'])

@routes.route('/password_generator/', methods=['GET'])
def password_generator():
    
    return render_template('password_gen.html', data = None)

@routes.route('/generate', methods=['GET', 'POST'])
@routes.route('/generate/<int:bits>', methods=['GET'])
def generate(bits=128):

    if request.method == 'POST':
        form = request.form.get("base64_encoding")
        if form:
            print(form, file=sys.stderr)
            data = generate_key( bytes= str(request.form['size']), base64=True)
        else:
            data = generate_key( bytes= str(request.form['size']))
    elif bits == 128 or bits == 256 or bits == 512 :
        data = generate_key_iv( bytes= str(int(bits/8)) )
    else:
        data = generate_key( bytes=str(bits))
    
    
    return render_template('password_gen.html',  data=data)

# Deleting files
@routes.route('/delete_file/', methods=['GET', 'POST'])
def delete_file():
    print('delete_file', file=sys.stderr)
    if request.method == 'POST':
        # check if the post request has the file part
        selected_files = request.form.getlist('selected_files')
        if selected_files is not None:
            print('------------ Files Selected:', file=sys.stderr)
            for f in selected_files:
                print(f,  file=sys.stderr)
                filename = os.path.join(UPLOAD_FOLDER, f)
                print(filename, file=sys.stderr)
                os.remove(filename)
                
        selected_enc_files = request.form.getlist('selected_enc_files')
        if selected_enc_files is not None:
            print('------------ Encrypted Files Selected:', file=sys.stderr)
            for f in selected_enc_files:
                print(f,  file=sys.stderr)
                filename = os.path.join(UPLOAD_FOLDER, f)
                print(filename, file=sys.stderr)
                os.remove(filename)

        files, enc = get_uploaded_files()
        return render_template('file_crypter.html', listdir=files, enc_files=enc, enc_info=[])

    files, enc = get_uploaded_files()
    return render_template('file_crypter.html', listdir=files, enc_files=enc, enc_info=[])

            

# Base 64 encoding
def encode_file(): 
    print("soon")

# Encrypts a list of files
def encrypt_list_of_files(files):
    print('encrypt_list_of_files', file=sys.stderr)
    if files == None:
        return []
    else:
        result = {}
        obj_list = []
        for f in files:
            obj = {}
            obj['filename'] = f
            data = generate_key_iv(bytes=str(16))
            obj['iv'] = data['iv']
            obj['key'] = data['key']
            print('ENCRYPTING FILE: '+str(f), file=sys.stderr)
            res = encrypt_file(f, obj['key'], obj['iv'])
            if 'ok' in res:
                print('ok', file=sys.stderr)
                obj_list.append(obj)
            elif 'error' in res:
                print('error', file=sys.stderr)
                pass
            #print(obj_list, file=sys.stderr)
        result['data'] = obj_list
        return result

def generate_keys_for_files(files):
    print('generate_keys_for_files', file=sys.stderr)
    if files == None:
        return []
    else:
        result = {}
        obj_list = []
        for f in files:
            obj = {}
            obj['filename'] = f
            data = generate_key_iv(bytes=str(16))
            obj['iv'] = data['iv']
            obj['key'] = data['key']
            obj_list.append(obj)
            print(obj_list, file=sys.stderr)
        result['data'] = obj_list
        return result

# Gets uploaded files and encrypted files, returns a tuple of lists (encrypted ones and non-encrypted)
def get_uploaded_files():
    listdir = os.listdir(UPLOAD_FOLDER)
    res = []
    enc = []
    for f in listdir:
        if '.dec' in f:
            enc.append(f)
        else:
            res.append(f)
    return res, enc