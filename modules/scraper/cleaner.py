import re
from datetime import datetime
from typing import Dict, Any, Optional

class DataCleaner:
    """Normalizes and cleans raw extracted data with high atomicity."""

    def extract_numeric(self, text: Optional[str]) -> Optional[int]:
        """Extracts the first integer found in a string (e.g., '16 weeks' -> 16)."""
        if not text:
            return None
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None

    def normalize_price(self, raw_price: Optional[str]) -> Dict[str, Any]:
        """Converts raw price to numeric amount, currency code, and formatted string."""
        if not raw_price:
            return {"amount": None, "currency": None, "display": None}
            
        numeric_part = re.sub(r'[^\d]', '', raw_price)
        amount = int(numeric_part) if numeric_part else None
        currency = "INR" if "₹" in raw_price else "USD" # Defaulting based on context
        
        return {
            "amount": amount,
            "currency": currency,
            "display": f"{currency} {amount:,}" if amount else None
        }

    def normalize_date(self, raw_date: Optional[str]) -> Optional[str]:
        """Converts dates like 'Mar 7' to YYYY-MM-DD ISO format."""
        if not raw_date:
            return None
            
        # Handle 'starts on Mar 7' or similar
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+', raw_date, re.IGNORECASE)
        if not date_match:
            return None
            
        clean_date_str = date_match.group(0)
        try:
            current_year = datetime.now().year
            date_obj = datetime.strptime(f"{clean_date_str} {current_year}", "%b %d %Y")
            
            # Heuristic: if date is > 6 months in past, it's likely next year
            if (datetime.now() - date_obj).days > 180:
                date_obj = date_obj.replace(year=current_year + 1)
                
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    def clean_text(self, text: Optional[str], remove_newlines: bool = True) -> Optional[str]:
        """Generic text cleaning for atomicity."""
        if not text:
            return None
        text = text.strip()
        if remove_newlines:
            text = " ".join(text.split())
        return text
