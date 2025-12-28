from datetime import datetime
from fastapi import Request
from .. import models

class ContextService:
    def __init__(self):
        pass

    def evaluate_context(self, user: models.User, request: Request, 
                         trusted_ip: str = None, 
                         device_id: str = None, 
                         region: str = None,
                         mock_hour: int = None) -> float:
        """
        Calculates a Trust Score from 0.0 to 1.0 based on context.
        """
        score = 1.0
        current_ip = request.client.host
        
        # Factor 1: IP Address Check (Penalty: 0.31)
        if trusted_ip:
            if current_ip != trusted_ip:
                print(f"[Context] IP Mismatch! Trusting {trusted_ip}, took {current_ip}")
                score -= 0.31
            else:
                pass # print(f"[Context] IP Match ({current_ip}).")
        
        # Factor 2: Device ID Check (Penalty: 0.5) - Critical Factor
        if user.trusted_device_id and device_id:
            if device_id != user.trusted_device_id:
                 print(f"[Context] Device Mismatch! Trusting {user.trusted_device_id}, Got {device_id}")
                 score -= 0.5
            else:
                 pass # Match
        elif user.trusted_device_id and not device_id:
             print("[Context] Device ID missing but required.")
             score -= 0.3
             
        # Factor 3: Region Check (Penalty: 0.5)
        if user.home_region and region:
            if region != user.home_region:
                print(f"[Context] Region Mismatch! Trusting {user.home_region}, Got {region}")
                score -= 0.5
        
        # Factor 4: Time of Day (Simulated Business Hours) - Penalty 0.2
        current_hour = mock_hour if mock_hour is not None else datetime.now().hour
        if 0 <= current_hour < 6:
            # print(f"[Context] High Risk Time ({current_hour}h).")
            score -= 0.2
            
        # Clamp score
        return max(0.0, score)

    def log_access(self, db, user_id, ip, score, decision):
        new_log = models.AccessLog(
            user_id=user_id,
            ip_address=ip,
            trust_score=str(score),
            decision=decision
        )
        db.add(new_log)
        db.commit()
