from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..services.biometric import BiometricService
from ..services.context import ContextService
from ..services.fingerprint_proxy import FingerprintProxy
from ..services.fuzzy_vault import FuzzyVault
import json

router = APIRouter(
    prefix="/auth",
    tags=["Start"],
)

biometric_service = BiometricService()
context_service = ContextService()
finger_service = FingerprintProxy()
vault_service = FuzzyVault()

@router.post("/enroll", response_model=schemas.UserResponse)
async def enroll_user(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),         # Face (Mandatory)
    file_finger: UploadFile = File(...),  # Fingerprint (Mandatory)
    db: Session = Depends(database.get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        print(f"[Enroll] Error: Username '{username}' already registered")
        raise HTTPException(status_code=400, detail="Username already registered")

    # 1. Process Face
    image_bytes = await file.read()
    features = biometric_service.extract_features_from_buffer(image_bytes)
    if features is None:
        print(f"[Enroll] Error: No face detected in uploaded image")
        raise HTTPException(status_code=400, detail="No face detected or image quality too low")

    secret_token = biometric_service.generate_token()
    biohash_str = biometric_service.generate_biohash(features, secret_token)

    # 2. Process Fingerprint (Mandatory)
    finger_bytes = await file_finger.read()
    finger_points = finger_service.extract_features(finger_bytes)
    
    if not finger_points:
        print(f"[Enroll] Error: Fingerprint feature extraction returned None or empty")
    elif len(finger_points) < 5:
        print(f"[Enroll] Error: Not enough minutiae found ({len(finger_points)} < 5)")
    
    if not finger_points or len(finger_points) < 5:
        raise HTTPException(status_code=400, detail="Fingerprint quality too low (not enough minutiae detected)")

    # Lock secret in Vault
    secret_payload = secret_token % 1000
    vault_data = vault_service.lock(secret_payload, finger_points)
    vault_json = json.dumps(vault_data)
    print(f"[Enroll] Fingerprint Vault Created with {len(vault_data)} points")

    # 3. Save
    client_ip = request.client.host
    new_user = models.User(username=username, trusted_ip=client_ip)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    new_template = models.BiometricTemplate(
        user_id=new_user.id,
        seed_token=secret_token,
        biohash_data=biohash_str,
        fingerprint_vault=vault_json
    )
    db.add(new_template)
    db.commit()

    return {"id": new_user.id, "username": new_user.username, "message": "User enrolled (Multimodal Strict)"}

@router.post("/verify", response_model=schemas.AuthResponse)
async def verify_user(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),
    file_finger: UploadFile = File(...), # Mandatory
    db: Session = Depends(database.get_db)
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed (User not found)")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()
    if not template:
        raise HTTPException(status_code=401, detail="No biometric data found")

    # 2. Face Check (BioHash)
    image_bytes = await file.read()
    features = biometric_service.extract_features_from_buffer(image_bytes)
    
    face_passed = False
    if features is not None:
        live_biohash = biometric_service.generate_biohash(features, template.seed_token)
        is_match, distance = biometric_service.match_biohashes(live_biohash, template.biohash_data)
        if is_match:
            face_passed = True
            print(f"[Verify] Face Match: YES (Dist: {distance:.4f})")
        else:
            print(f"[Verify] Face Match: NO (Dist: {distance:.4f})")

    # 3. Fingerprint Check (Fuzzy Vault)
    finger_bytes = await file_finger.read()
    finger_points = finger_service.extract_features(finger_bytes)
    
    finger_passed = False
    vault_quality = 0.0
    
    if finger_points and template.fingerprint_vault:
        vault_data = json.loads(template.fingerprint_vault)
        recovered_secret, vault_quality = vault_service.unlock(vault_data, finger_points)
        
        expected_secret = template.seed_token % 1000
        if recovered_secret == expected_secret:
            finger_passed = True
            print(f"[Verify] Vault Unlocked: YES")
        else:
             print(f"[Verify] Vault Unlocked: NO (Exp: {expected_secret}, Got: {recovered_secret})")
    
    # 4. Context Check
    context_score = context_service.evaluate_context(user, request, user.trusted_ip)

    # 5. STRICT DECISION LOGIC
    # Access = (Face OK) AND (Finger OK) AND (Trust OK)
    
    is_authenticated = face_passed and finger_passed and (context_score >= 0.7)
    
    status_msg = "ACCESS GRANTED" if is_authenticated else "ACCESS DENIED"
    details = f"Face:{'OK' if face_passed else 'FAIL'} | Finger:{'OK' if finger_passed else 'FAIL'} | Trust:{context_score}"
    
    # Log attempt
    context_service.log_access(db, user.id, request.client.host, context_score, status_msg)
    
    return {
        "authenticated": is_authenticated,
        "username": user.username,
        "message": f"{status_msg} [{details}]"
    }
