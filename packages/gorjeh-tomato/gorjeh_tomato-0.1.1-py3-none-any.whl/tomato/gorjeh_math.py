# tomato/gorjeh_math.py

import math

class GorjehMath:
    """
    یک کلاس برای محاسبات هندسی در پکیج tomato.
    """
    
    PI = math.pi
    
    def __init__(self):
        """ساختمان ساز کلاس."""
        pass

    @staticmethod
    def circle_area(radius: float) -> float:
        """
        مساحت دایره را بر اساس شعاع (radius) محاسبه می‌کند.
        فرمول: مساحت = PI * شعاع^2
        
        آرگومان‌ها:
        - radius: شعاع دایره (عدد صحیح یا اعشاری). باید مثبت باشد.
        
        بازگشت:
        - مساحت دایره (عدد اعشاری).
        """
        # بررسی نوع ورودی
        if not isinstance(radius, (int, float)):
            raise TypeError("شعاع (radius) باید یک عدد (Integer یا Float) باشد.")
        
        # بررسی مقدار ورودی
        if radius < 0:
            raise ValueError("شعاع نمی‌تواند منفی باشد.")
            
        area = GorjehMath.PI * (radius ** 2)
        return area