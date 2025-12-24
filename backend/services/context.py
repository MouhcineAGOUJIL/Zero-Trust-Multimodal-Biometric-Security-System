from datetime import datetime
from fastapi import Request
from .. import models

class ContextService:
    def __init__(self):
        pass

    def evaluate_context(self, user: models.User, request: Request, trusted_ip: str = None) -> float:
        """
        Calculates a Trust Score from 0.0 to 1.0 based on context.
        """
        score = 1.0
        current_ip = request.client.host
        
        # Factor 1: IP Address Check
        # If trusted_ip is stored, compare it.
        if trusted_ip:
            if current_ip != trusted_ip:
                print(f"[Context] IP Mismatch! Trusting {trusted_ip}, took {current_ip}")
                score -= 0.3
            else:
                print(f"[Context] IP Match ({current_ip}). Trust Maintained.")
        else:
            # First time seeing this factor? Neutral.
            pass

        # Factor 2: Time of Day (Simulated Business Hours)
        # High Risk: Midnight to 6 AM
        current_hour = datetime.now().hour
        if 0 <= current_hour < 6:
            print(f"[Context] High Risk Time ({current_hour}h). Penalty applied.")
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
