"""
Regex patterns for extracting entities from receipt text
"""
import re

# Date patterns (Vietnamese and international formats)
DATE_PATTERNS = [
    r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # DD/MM/YYYY or DD-MM-YYYY
    r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',    # YYYY/MM/DD
    r'\b(\d{1,2})\s+(Th[áa]ng|T)\s+(\d{1,2})\s+(\d{4})\b',  # DD Tháng MM YYYY
]

# Amount patterns (Vietnamese currency)
AMOUNT_PATTERNS = [
    r'(?:T[ổo]ng|Total|Sum|TOTAL|T[OỔ]NG)[:\s]*([0-9,.]+)\s*(?:VN[ĐD]|đ|d)?',
    r'(?:Thanh to[áa]n|Payment|PAY)[:\s]*([0-9,.]+)\s*(?:VN[ĐD]|đ|d)?',
    r'([0-9,.]+)\s*(?:VN[ĐD]|đồng|dong)',
    r'(?:AMOUNT|Amount|S[ốo] ti[ềe]n)[:\s]*([0-9,.]+)',
]

# Phone number patterns
PHONE_PATTERNS = [
    r'\b(0\d{9,10})\b',  # Vietnamese phone: 0xxxxxxxxx
    r'\b(\+84\s?\d{9,10})\b',  # International format
    r'(?:Tel|Phone|ĐT|SDT)[:\s]*([0-9\s\-\.]+)',
]

# Merchant name patterns (common Vietnamese keywords)
MERCHANT_KEYWORDS = [
    r'(?:C[ửữ]a\s+h[àa]ng|Store|Shop)[:\s]*([A-Z\u00C0-\u1EF9][^\n]{5,50})',
    r'(?:Restaurant|Nh[àa]\s+h[àa]ng)[:\s]*([A-Z\u00C0-\u1EF9][^\n]{5,50})',
    r'(?:Si[êế]u\s+th[ịi]|Supermarket|Market)[:\s]*([A-Z\u00C0-\u1EF9][^\n]{5,50})',
    r'(?:C[ôo]ng\s+ty|Company)[:\s]*([A-Z\u00C0-\u1EF9][^\n]{5,50})',
]

# Item patterns (lines with quantity * price format)
ITEM_PATTERNS = [
    r'([A-Z\u00C0-\u1EF9][^\n]{3,40})\s+(\d+)\s*x\s*([0-9,.]+)',  # Item Qty x Price
    r'([A-Z\u00C0-\u1EF9][^\n]{3,40})\s+([0-9,.]+)\s*x\s*(\d+)',  # Item Price x Qty
    r'(\d+)\s*([A-Z\u00C0-\u1EF9][^\n]{3,40})\s+([0-9,.]+)',     # Qty Item Price
]

# Tax/VAT patterns
TAX_PATTERNS = [
    r'(?:VAT|Tax|Thu[ếe])[:\s]*([0-9,.]+)\s*%?',
    r'(?:Discount|Gi[ảa]m\s+gi[áa])[:\s]*([0-9,.]+)',
]

# Address patterns
ADDRESS_PATTERNS = [
    r'(?:[ĐD][ịi]a\s+ch[ỉi]|Address)[:\s]*([^\n]{10,100})',
    r'(\d+\s+[A-Z\u00C0-\u1EF9][^\n]{10,80})',
]

# Common receipt header/footer keywords to ignore
IGNORE_KEYWORDS = [
    'receipt', 'bill', 'invoice', 'h[óo]a\s*[đd][ơơ]n',
    'thank\s+you', 'c[ảa]m\s+[ơơ]n', 'tam\s+biet',
    'welcome', 'ch[àa]o\s+m[ừừ]ng', 'visit\s+again',
    'powered\s+by', 'software', 'version'
]

def clean_amount(amount_str: str) -> float:
    """
    Clean and parse amount string to float
    
    Args:
        amount_str: Amount string (e.g., "1,234,567.89" or "1.234.567,89")
        
    Returns:
        float: Parsed amount
    """
    if not amount_str:
        return 0.0
    
    # Remove spaces and common currency symbols
    cleaned = amount_str.strip().replace(' ', '').replace('đ', '').replace('VNĐ', '')
    
    # Handle Vietnamese format (1.234.567,89) vs international (1,234,567.89)
    # Count dots and commas
    dot_count = cleaned.count('.')
    comma_count = cleaned.count(',')
    
    if dot_count > 1 and comma_count == 0:
        # Vietnamese format: 1.234.567
        cleaned = cleaned.replace('.', '')
    elif dot_count > 1 and comma_count == 1:
        # Vietnamese format: 1.234.567,89
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif comma_count > 1:
        # International with thousand separators: 1,234,567.89
        cleaned = cleaned.replace(',', '')
    elif comma_count == 1 and dot_count == 0:
        # Could be Vietnamese decimal: 123,45
        cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def clean_phone(phone_str: str) -> str:
    """
    Clean and format phone number
    
    Args:
        phone_str: Raw phone string
        
    Returns:
        str: Cleaned phone number
    """
    if not phone_str:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_str)
    
    return cleaned


def clean_date(date_str: str) -> str:
    """
    Clean and standardize date format to YYYY-MM-DD
    
    Args:
        date_str: Raw date string
        
    Returns:
        str: Standardized date string (YYYY-MM-DD)
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    # Try different date formats
    formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
        '%Y/%m/%d', '%Y-%m-%d',
        '%m/%d/%Y', '%m-%d-%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return date_str  # Return original if parsing fails