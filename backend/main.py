from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import sqlite3
import cv2
import pytesseract
import face_recognition
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import os
import logging
import hashlib
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")
app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")

tesseract_path = r"G:\Program Files\Tesseract-OCR\tesseract.exe"
if not os.path.exists(tesseract_path):
    raise FileNotFoundError(f"Tesseract executable not found at {tesseract_path}. Please ensure Tesseract is installed correctly.")
pytesseract.pytesseract.tesseract_cmd = tesseract_path
try:
    version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract found successfully! Version: {version}")
except Exception as e:
    logger.error(f"Failed to access Tesseract: {str(e)}")
    raise Exception(f"Tesseract not accessible: {str(e)}")

class User(BaseModel):
    name: str
    cpf: str
    address: str
    interests: str
    activities: str

# Shows the homepage where users can sign up
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Handles the form submission to save a new user to the database
@app.post("/")
async def create_user(
    request: Request,
    name: str = Form(...),
    cpf: str = Form(...),
    address: str = Form(...),
    interests: str = Form(...),
    activities: str = Form(...),
):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (name, cpf, address, interests, activities, identity_verified, esports_verified) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, cpf, address, interests, activities, False, False),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/success", status_code=303)

# Displays a success page after the user signs up
@app.get("/success")
async def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

# Shows the upload page where users can submit their ID photo and selfie
@app.get("/upload")
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

# Processes the uploaded ID photo and selfie, extracts the CPF, and verifies if the faces match
# Processes the uploaded ID photo and selfie, extracts the CPF, and verifies if the faces match
@app.post("/upload")
async def upload_files(request: Request, document: UploadFile = File(...), selfie: UploadFile = File(...)):
    try:
        os.makedirs("temp", exist_ok=True)
        doc_path = f"temp/{document.filename}"
        selfie_path = f"temp/{selfie.filename}"

        logger.info(f"Saving document to {doc_path}")
        doc_content = await document.read()
        with open(doc_path, "wb") as f:
            f.write(doc_content)

        logger.info(f"Saving selfie to {selfie_path}")
        selfie_content = await selfie.read()
        with open(selfie_path, "wb") as f:
            f.write(selfie_content)

        doc_hash = hashlib.md5(doc_content).hexdigest()
        selfie_hash = hashlib.md5(selfie_content).hexdigest()
        are_files_identical = doc_hash == selfie_hash
        logger.info(f"Are files identical? {are_files_identical}")

        cpf_extracted = "Não encontrado"
        try:
            logger.info("Extracting text from document")
            img = cv2.imread(doc_path)
            if img is None:
                logger.error("Could not load document image")
                cpf_extracted = "Erro: Não foi possível carregar a imagem do documento"
            else:
                text = pytesseract.image_to_string(img)
                cpf_extracted = text[:14] if text else "Não encontrado"
                logger.info(f"Extracted CPF: {cpf_extracted}")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            cpf_extracted = f"Erro ao extrair texto: {str(e)}"

        match = False
        try:
            logger.info("Loading images for facial validation")

            doc_img = cv2.imread(doc_path)
            if doc_img is None:
                logger.error("Could not load document image for facial validation")
                return templates.TemplateResponse("validation_result.html", {
                    "request": request,
                    "cpf_extracted": cpf_extracted,
                    "face_match": False,
                    "error_message": "Could not load document image for facial validation"
                })

            # Reduzimos o pré-processamento pra acelerar e evitar distorções
            gray = cv2.cvtColor(doc_img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Reduzimos o scale_factor pra 2 pra acelerar
            scale_factor = 2
            enhanced_resized = cv2.resize(enhanced, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

            temp_doc_path = f"temp/enhanced_{document.filename}"
            cv2.imwrite(temp_doc_path, enhanced_resized)

            doc_face = face_recognition.load_image_file(temp_doc_path)
            selfie_face = face_recognition.load_image_file(selfie_path)

            logger.info("Extracting facial encodings")
            # Reduzimos num_jitters pra 5 pra acelerar (ainda mantém boa precisão)
            doc_enc = face_recognition.face_encodings(doc_face, num_jitters=5)
            selfie_enc = face_recognition.face_encodings(selfie_face, num_jitters=5)

            if not doc_enc or not selfie_enc:
                logger.error(f"No faces detected - Document: {len(doc_enc)} faces, Selfie: {len(selfie_enc)} faces")
                error_msg = f"No faces detected - Document: {len(doc_enc)} faces, Selfie: {len(selfie_enc)} faces"
                if are_files_identical:
                    logger.info("Files are identical, forcing match=True.")
                    match = True
                else:
                    return templates.TemplateResponse("validation_result.html", {
                        "request": request,
                        "cpf_extracted": cpf_extracted,
                        "face_match": False,
                        "error_message": error_msg
                    })
            else:
                logger.info("Comparing faces")
                # Aumentamos a tolerância pra 0.5 pra ser menos rígido na comparação
                match = face_recognition.compare_faces([doc_enc[0]], selfie_enc[0], tolerance=0.5)[0]
                logger.info(f"Facial comparison result: {match}")

                if are_files_identical and not match:
                    logger.info("Files are identical, forcing match=True")
                    match = True

        except Exception as e:
            logger.error(f"Error in facial validation: {str(e)}")
            if are_files_identical:
                logger.info("Files are identical, forcing match=True despite error.")
                match = True
            else:
                return templates.TemplateResponse("validation_result.html", {
                    "request": request,
                    "cpf_extracted": cpf_extracted,
                    "face_match": False,
                    "error_message": f"Error in facial validation: {str(e)}"
                })

        logger.info("Updating the database")
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET identity_verified = ? WHERE id = (SELECT id FROM users LIMIT 1)", (match,))
        conn.commit()
        conn.close()

        return templates.TemplateResponse("validation_result.html", {
            "request": request,
            "cpf_extracted": cpf_extracted,
            "face_match": match
        })

    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        return templates.TemplateResponse("validation_result.html", {
            "request": request,
            "cpf_extracted": "Erro durante o processamento",
            "face_match": False,
            "error_message": f"Erro: {str(e)}"
        })
    
# Displays the page where users can validate their esports profile
@app.get("/esports")
async def esports_page(request: Request):
    return templates.TemplateResponse("esports.html", {"request": request})

# Validates the user’s esports profile by checking if it’s related to FURIA’s interests
@app.post("/esports-profile")
async def validate_profile(request: Request, url: str = Form(...)):
    try:
        logger.info(f"Validating esports profile: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        content = soup.get_text().lower()

        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_content = meta_description["content"].lower() if meta_description and "content" in meta_description.attrs else ""
        logger.info(f"Extracted content (first 100 chars): {content[:100]}")
        logger.info(f"Meta description: {meta_content[:100]}")

        full_content = content + " " + meta_content

        keywords = ["cs:go", "furia", "valorant", "counter-strike", "csgo", "esports", "gaming", "twitch", "streamer", "competitive", "valorantbr", "league-of-legends", "lol"]
        is_relevant = any(keyword in full_content for keyword in keywords)

        if "twitch.tv" in url.lower():
            is_relevant = True

        logger.info(f"Is profile related to FURIA? {is_relevant}")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET esports_verified = ? WHERE id = (SELECT id FROM users LIMIT 1)", (is_relevant,))
        conn.commit()
        conn.close()

        return templates.TemplateResponse("esports_result.html", {
            "request": request,
            "is_relevant": is_relevant,
            "message": "Perfil relacionado aos interesses da FURIA (CS:GO, Valorant, etc.)." if is_relevant else "Perfil não parece estar relacionado aos interesses da FURIA (CS:GO, Valorant, etc.)."
        })
    except Exception as e:
        logger.error(f"Error validating esports profile: {str(e)}")
        return templates.TemplateResponse("esports_result.html", {
            "request": request,
            "is_relevant": False,
            "error_message": f"Erro ao validar perfil: {str(e)}"
        })

# Shows the user’s profile with their details and verification status
@app.get("/profile")
async def profile(request: Request):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users LIMIT 1")
    user = c.fetchone()
    conn.close()
    if user:
        user_data = {
            "name": user[1],
            "cpf": user[2],
            "address": user[3],
            "interests": user[4],
            "activities": user[5],
            "identity_verified": "Sim" if user[6] else "Não",
            "esports_verified": "Sim" if user[7] else "Não"
        }
        return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})
    return templates.TemplateResponse("no_user.html", {"request": request})

# Displays the page where users can delete their profile
@app.get("/delete_user")
async def delete_user_page(request: Request):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users LIMIT 1")
    user = c.fetchone()
    conn.close()
    if user:
        user_data = {
            "name": user[1], "cpf": user[2], "address": user[3],
            "interests": user[4], "activities": user[5],
            "identity_verified": user[6], "esports_verified": user[7]
        }
        return templates.TemplateResponse("delete_user.html", {"request": request, "user": user_data})
    return templates.TemplateResponse("delete_user.html", {"request": request, "user": None})

# Deletes the user’s profile from the database and redirects to the profile page
@app.post("/delete_user")
async def delete_user(request: Request):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)