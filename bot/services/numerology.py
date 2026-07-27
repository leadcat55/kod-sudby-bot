from datetime import date
from typing import Dict, List, Tuple

class NumerologyEngine:
    """Core numerology calculation engine"""
    
    # Letter-to-number mapping (Pythagorean)
    LETTER_VALUES = {
        'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5, 'е': 6, 'ё': 7,
        'ж': 8, 'з': 9, 'и': 1, 'й': 2, 'к': 3, 'л': 4, 'м': 5,
        'н': 6, 'о': 7, 'п': 8, 'р': 9, 'с': 1, 'т': 2, 'у': 3,
        'ф': 4, 'х': 5, 'ц': 6, 'ч': 7, 'ш': 8, 'щ': 9, 'ъ': 0,
        'ы': 1, 'ь': 0, 'э': 2, 'ю': 3, 'я': 4
    }
    
    @staticmethod
    def reduce_to_single(n: int) -> int:
        """Reduce number to single digit (except master numbers 11, 22, 33)"""
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n
    
    @staticmethod
    def reduce_to_single_strict(n: int) -> int:
        """Strict reduction - always to single digit"""
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n
    
    def life_path_number(self, birth_date: date) -> int:
        """Число Жизненного Пути - сумма всех цифр даты рождения"""
        date_str = birth_date.strftime("%d%m%Y")
        total = sum(int(d) for d in date_str)
        return self.reduce_to_single(total)
    
    def soul_number(self, full_name: str) -> int:
        """Число Души - сумма гласных букв полного имени"""
        vowels = set('аеёиоуыэюя')
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c in vowels
        )
        return self.reduce_to_single(total)
    
    def personality_number(self, full_name: str) -> int:
        """Число Личности - сумма согласных букв полного имени"""
        vowels = set('аеёиоуыэюя')
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c.isalpha() and c not in vowels
        )
        return self.reduce_to_single(total)
    
    def destiny_number(self, full_name: str) -> int:
        """Число Судьбы - сумма всех букв полного имени"""
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c.isalpha()
        )
        return self.reduce_to_single(total)
    
    def birthday_number(self, birth_date: date) -> int:
        """Число Дня Рождения - день рождения"""
        return self.reduce_to_single(birth_date.day)
    
    def get_calc_breakdown(self, calc_type: str, birth_date: date, full_name: str = "") -> str:
        """Generate a human-readable calculation breakdown for a given calc type.
        
        For date-based calculations (life_path, birthday), shows the full
        digit-by-digit calculation, e.g.:
            14.09.1965 → 1+4+0+9+1+9+6+5 = 35 → 3+5 = 8
        
        Returns None for name-based calculations (soul, personality, destiny)
        or unknown calc types.
        """
        if calc_type == "life_path":
            date_display = birth_date.strftime("%d.%m.%Y")
            date_str = birth_date.strftime("%d%m%Y")
            digits = [int(d) for d in date_str]
            total = sum(digits)
            digits_str = "+".join(str(d) for d in digits)

            # Build reduction steps (stop at master numbers 11, 22, 33)
            parts = []
            current = total
            while current > 9 and current not in (11, 22, 33):
                digit_parts = [int(d) for d in str(current)]
                step_sum = sum(digit_parts)
                parts.append(f"{'+'.join(str(p) for p in digit_parts)} = {step_sum}")
                current = step_sum

            if parts:
                return f"{date_display} → {digits_str} = {total} → {' → '.join(parts)}"
            else:
                return f"{date_display} → {digits_str} = {total}"

        elif calc_type == "birthday":
            day = birth_date.day
            digits = [int(d) for d in str(day)]
            total = sum(digits)
            digits_str = "+".join(str(d) for d in digits)

            if total > 9:
                digit_parts = [int(d) for d in str(total)]
                step_str = "+".join(str(p) for p in digit_parts)
                return f"День {day} → {digits_str} = {total} → {step_str} = {sum(digit_parts)}"
            else:
                return f"День {day} → {digits_str} = {total}"

        return None

    def get_basic_numbers(self, birth_date: date, full_name: str) -> Dict[str, int]:
        """Get all basic numerology numbers"""
        return {
            "life_path": self.life_path_number(birth_date),
            "soul": self.soul_number(full_name),
            "personality": self.personality_number(full_name),
            "destiny": self.destiny_number(full_name),
            "birthday": self.birthday_number(birth_date)
        }
    
    def pythagorean_square(self, birth_date: date, full_name: str) -> Dict[str, List[int]]:
        """Calculate Pythagorean Square (Квадрат Пифагора)"""
        # Get birth date digits
        date_digits = [int(d) for d in birth_date.strftime("%d%m%Y")]
        
        # Get name value
        name_value = self.destiny_number(full_name)
        name_digits = [int(d) for d in str(name_value)] if name_value > 9 else [name_value]
        
        # First line: date of birth
        first_line = date_digits
        
        # Second line: sum of first line
        second_sum = sum(first_line)
        second_line = [int(d) for d in str(second_sum)] if second_sum > 9 else [second_sum]
        
        # Third line: difference between first digit of first line and sum of rest
        first_digit = first_line[0]
        rest_sum = sum(first_line[1:])
        third_value = abs(first_digit - rest_sum) if rest_sum > 0 else first_digit
        third_line = [int(d) for d in str(third_value)] if third_value > 9 else [third_value]
        
        # Fourth line: all digits together
        all_digits = first_line + second_line + third_line + name_digits
        
        # Count occurrences of each number (1-9)
        counts = {i: all_digits.count(i) for i in range(1, 10)}
        
        return {
            "first_line": first_line,
            "second_line": second_line,
            "third_line": third_line,
            "name_value": name_value,
            "counts": counts
        }
    
    def compatibility(self, birth1: date, name1: str, birth2: date, name2: str) -> Dict:
        """Calculate compatibility between two people"""
        numbers1 = self.get_basic_numbers(birth1, name1)
        numbers2 = self.get_basic_numbers(birth2, name2)
        
        # Simple compatibility score based on life path numbers
        diff = abs(numbers1["life_path"] - numbers2["life_path"])
        if diff == 0:
            score = 100
        elif diff <= 2:
            score = 85
        elif diff <= 4:
            score = 70
        elif diff <= 6:
            score = 55
        else:
            score = 40
        
        return {
            "person1": numbers1,
            "person2": numbers2,
            "compatibility_score": score,
            "description": self._get_compatibility_description(score)
        }
    
    def _get_compatibility_description(self, score: int) -> str:
        if score >= 90:
            return "Идеальная совместимость! Вы прекрасно дополняете друг друга."
        elif score >= 75:
            return "Хорошая совместимость. Есть потенциал для глубоких отношений."
        elif score >= 60:
            return "Средняя совместимость. Нужны усилия обоих партнёров."
        else:
            return "Сложная совместимость. Но это не преграда для любви!"

numerology = NumerologyEngine()
