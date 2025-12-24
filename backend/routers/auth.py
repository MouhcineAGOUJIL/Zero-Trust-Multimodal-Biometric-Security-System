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
    file: UploadFile = File(...),         # Face
    file_finger: UploadFile = File(None), # Fingerprint (Optional for now)
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

    # 2. Process Fingerprint (If provided)
    vault_json = None
    if file_finger:
        finger_bytes = await file_finger.read()
        finger_points = finger_service.extract_features(finger_bytes)
        if finger_points and len(finger_points) > 5:
            # We use the SAME secret_token for the vault? 
            # Or we could treat the secret token as the "key" locked inside the vault.
            # Here: We lock a separate "PIN" or the seed itself.
            # Let's lock a small constant signature (e.g., 12345) to prove we opened it.
            # For robustness, we'll just lock 'secret_token % 1000' (small int).
            secret_payload = secret_token % 1000
            
            vault_data = vault_service.lock(secret_payload, finger_points)
            vault_json = json.dumps(vault_data)
            print(f"[Enroll] Fingerprint Vault Created with {len(vault_data)} points")
        else:
            print("[Enroll] Fingerprint provided but low quality/no features")

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

    return {"id": new_user.id, "username": new_user.username, "message": "User enrolled (Multimodal)"}

@router.post("/verify", response_model=schemas.AuthResponse)
async def verify_user(
    request: Request,
    username: str = Form(...),
    file: UploadFile = File(...),
    file_finger: UploadFile = File(None),
    db: Session = Depends(database.get_db)
):
    # 1. Retrieve User
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed")
    template = db.query(models.BiometricTemplate).filter(models.BiometricTemplate.user_id == user.id).first()
    if not template:
        raise HTTPException(status_code=401, detail="No biometric data")

    # 2. Face Score
    image_bytes = await file.read()
    features = biometric_service.extract_features_from_buffer(image_bytes)
    score_face = 0.0
    if features is not None:
        live_biohash = biometric_service.generate_biohash(features, template.seed_token)
        is_match, distance = biometric_service.match_biohashes(live_biohash, template.biohash_data)
        # Convert distance (0=good, 1=bad) to Score (1=good, 0=bad)
        # Threshold is roughly 0.2
        if is_match:
            score_face = 1.0 # Binary pass for BioHash
        else:
            score_face = max(0, 1.0 - (distance * 2)) # Approximate

    # 3. Fingerprint Score
    score_finger = 0.0
    if file_finger and template.fingerprint_vault:
        finger_bytes = await file_finger.read()
        finger_points = finger_service.extract_features(finger_bytes)
        if finger_points:
            # Try Unlock
            vault_data = json.loads(template.fingerprint_vault)
            recovered_secret, vault_quality = vault_service.unlock(vault_data, finger_points)
            
            expected_secret = template.seed_token % 1000
            if recovered_secret == expected_secret:
                print(f"[Verify] Vault Unlocked! Secret matched.")
                score_finger = 1.0
            else:
                print(f"[Verify] Vault Failed. Recovered {recovered_secret} != {expected_secret}")
                score_finger = 0.0

    # 4. Fusion Strategy (Weighted Sum)
    # Weights: Face=0.6, Finger=0.4 (Face is our primary tech here)
    # If fingerprint is missing, we rely solely on face? 
    # Let's say: Final = (0.6 * Face) + (0.4 * Finger)
    # If finger not enrolled, renormalize? For now, static weights.
    
    if template.fingerprint_vault:
        final_biometric_score = (0.6 * score_face) + (0.4 * score_finger)
    else:
        final_biometric_score = score_face

    # 5. Context
    context_score = context_service.evaluate_context(user, request, user.trusted_ip)

    # 6. Final Decision
    # Threshold: 0.65
    decision = "DENY"
    if final_biometric_score >= 0.6 and context_score >= 0.7:
        decision = "ALLOW"
    
    message = f"Score: {final_biometric_score:.2f} (Face:{score_face} Finger:{score_finger}) Trust: {context_score}"
    
    context_service.log_access(db, user.id, request.client.host, context_score, decision)
    
    return {
        "authenticated": (decision == "ALLOW"),
        "username": user.username,
        "message": message
    }
