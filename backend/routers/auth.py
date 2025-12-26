from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..services.biometric import BiometricService
from ..services.context import ContextService
from ..services.context import ContextService
# from ..services.fingerprint_proxy import FingerprintProxy # Replaced by CNN
from ..services.cnn_service import CNNService
from ..services.iom_service import IoMService
from ..services.palm_service import PalmService
import json
import numpy as np

router = APIRouter(
    prefix="/auth",
    tags=["Start"],
)

biometric_service = BiometricService()
context_service = ContextService()
# finger_service = FingerprintProxy()
cnn_service = CNNService() # Singleton
iom_service = IoMService(key_len=256)
palm_service = PalmService()

@router.post("/enroll", response_model=schemas.UserResponse)
async def enroll_user(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),         # Face
    file_finger: UploadFile = File(...),  # Fingerprint
    file_palm: UploadFile = File(None),   # Palm (Optional for now)
    db: Session = Depends(database.get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 1. Process Face
    image_bytes = await file.read()
    features = biometric_service.extract_features_from_buffer(image_bytes)
    if features is None:
        raise HTTPException(status_code=400, detail="No face detected")

    secret_token = biometric_service.generate_token()
    biohash_str = biometric_service.generate_biohash(features, secret_token)

    # 2. Process Fingerprint (CNN + IoM)
    finger_bytes = await file_finger.read()
    finger_features = cnn_service.extract_features(finger_bytes)
    
    if finger_features is None:
        raise HTTPException(status_code=400, detail="Fingerprint quality too low for CNN")

    iom_hash = iom_service.generate_iom_hash(finger_features, secret_token)

    # 3. Process Palm (ORB Feature Matching)
    palm_vault_json = None
    if file_palm:
        palm_bytes = await file_palm.read()
        palm_template = palm_service.create_template(palm_bytes)
        if palm_template:
            palm_vault_json = palm_template
            print(f"[Enroll] Palm Template Created (ORB).")
        else:
             print(f"[Enroll] Palm Template Creation Failed (No features).")
            


    # Finger Store
    vault_storage = {
        "helper_data": finger_features.tolist(),
        "iom_hash": iom_hash
    }
    vault_json = json.dumps(vault_storage)
    print(f"[Enroll] CNN-IoM Template Created (Multi).")

    # 4. Save
    client_ip = request.client.host
    new_user = models.User(username=username, trusted_ip=client_ip)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    new_template = models.BiometricTemplate(
        user_id=new_user.id,
        seed_token=secret_token,
        biohash_data=biohash_str,
        fingerprint_vault=vault_json,
        palm_vault=palm_vault_json # Explicit Palm Storage
    )
    db.add(new_template)
    db.commit()

    return {"id": new_user.id, "username": new_user.username, "message": "User enrolled (Multimodal Secured)"}

@router.post("/verify/face", response_model=schemas.AuthResponse)
async def verify_face(
    username: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()

    # 2. Face Check
    image_bytes = await file.read()
    features = biometric_service.extract_features_from_buffer(image_bytes)
    
    if features is None:
        return {"authenticated": False, "username": username, "message": "No face detected"}

    l_hash = biometric_service.generate_biohash(features, template.seed_token)
    is_match, score = biometric_service.match_biohashes(l_hash, template.biohash_data)

    status = "ACCESS GRANTED" if is_match else "ACCESS DENIED"
    return {
        "authenticated": is_match, 
        "username": username, 
        "message": f"{status} (Face) [Score: {score:.3f}]"
    }

@router.post("/verify/finger", response_model=schemas.AuthResponse)
async def verify_finger(
    username: str = Form(...),
    file_finger: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()
    
    # 2. Finger Check
    finger_bytes = await file_finger.read()
    query_features = cnn_service.extract_features(finger_bytes)
    
    if query_features is None or not template.fingerprint_vault:
        return {"authenticated": False, "username": username, "message": "Fingerprint data missing or poor quality"}

    stored_data = json.loads(template.fingerprint_vault)
    stored_hash = stored_data.get("iom_hash", "")
    
    query_hash = iom_service.generate_iom_hash(query_features, template.seed_token)
    
    is_match, score = iom_service.match_iom(query_hash, stored_hash)
    
    status = "ACCESS GRANTED" if is_match else "ACCESS DENIED"
    return {
        "authenticated": is_match, 
        "username": username, 
        "message": f"{status} (Finger) [Score: {score:.3f}]"
    }

@router.post("/verify/palm", response_model=schemas.AuthResponse)
async def verify_palm(
    username: str = Form(...),
    file_palm: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()
    
    if not template.palm_vault:
         return {"authenticated": False, "username": username, "message": "Palm not enrolled"}

    # 2. Palm Check via ORB
    palm_bytes = await file_palm.read()
    
    # PalmService handles deserialization and matching logic internally
    # It compares live ORB descriptors vs Stored ones
    is_match, score_count, msg = palm_service.verify(palm_bytes, template.palm_vault)
    
    status = "ACCESS GRANTED" if is_match else "ACCESS DENIED"
    return {
        "authenticated": is_match, 
        "username": username, 
        "message": f"{status} (Palm) [Keypoints: {score_count}]"
    }


@router.post("/verify/multimodal", response_model=schemas.AuthResponse)
async def verify_multimodal(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),         # Face
    file_finger: UploadFile = File(...),  # Finger
    file_palm: UploadFile = File(None),   # Palm (Optional)
    db: Session = Depends(database.get_db)
):
    return await verify_zerotrust(request, username, file, file_finger, db, file_palm=file_palm, strict_context=False)

@router.post("/verify/zerotrust", response_model=schemas.AuthResponse)
async def verify_zerotrust(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),
    file_finger: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    file_palm: UploadFile = File(None), # Add Palm argument
    strict_context: bool = True
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()
    
    # 2. Face
    image_bytes = await file.read()
    f_feats = biometric_service.extract_features_from_buffer(image_bytes)
    face_passed = False
    if f_feats is not None:
        l_hash = biometric_service.generate_biohash(f_feats, template.seed_token)
        is_m, _ = biometric_service.match_biohashes(l_hash, template.biohash_data)
        face_passed = is_m

    # 3. Finger
    finger_passed = False
    if file_finger and template.fingerprint_vault:
        f_bytes = await file_finger.read()
        f_feats = cnn_service.extract_features(f_bytes)
        if f_feats is not None:
            stored_data = json.loads(template.fingerprint_vault)
            stored_hash = stored_data.get("iom_hash", "")
            if stored_hash:
                query_hash = iom_service.generate_iom_hash(f_feats, template.seed_token)
                is_match, _ = iom_service.match_iom(query_hash, stored_hash)
                finger_passed = is_match

    # 4. Palm
    # 4. Palm
    palm_passed = False
    if file_palm and template.palm_vault:
        p_bytes = await file_palm.read()
        is_m, score, _ = palm_service.verify(p_bytes, template.palm_vault)
        palm_passed = is_m

    # 5. Context
    context_score = context_service.evaluate_context(user, request, user.trusted_ip)
    context_passed = (context_score >= 0.7) if strict_context else True
    
    # Logic: Face is MANDATORY. Finger/Palm are supplementary.
    # If Multimodal, require majority? Or AND?
    # Let's say: Face AND (Finger OR Palm) ?
    # Or strict: Face AND Finger AND Palm (if provided).
    # User said "Multimodal". Usually means Fusion.
    # Let's simple AND logic for now: True if all provided match.
    
    is_auth = face_passed and context_passed
    if file_finger: is_auth = is_auth and finger_passed
    if file_palm: is_auth = is_auth and palm_passed
    
    status = "ACCESS GRANTED" if is_auth else "ACCESS DENIED"
    details = f"Face:{face_passed} Finger:{finger_passed} Palm:{palm_passed} Trust:{context_score:.2f}"
    
    context_service.log_access(db, user.id, request.client.host, context_score, status)
    
    return {
        "authenticated": is_auth, 
        "username": username, 
        "message": f"{status} [{details}]"
    }
