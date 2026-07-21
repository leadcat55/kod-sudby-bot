import httpx
from typing import Optional
from ..config import config
from ..services.numerology import numerology

class LLMService:
    def __init__(self):
        self.api_url = config.LLM_API_URL
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL
    
    async def generate_deep_analysis(self, birth_date, full_name: str) -> Optional[str]:
        """Generate deep numerology analysis using LLM"""
        if not self.api_key:
            return self._get_fallback_analysis(birth_date, full_name)
        
        numbers = numerology.get_basic_numbers(birth_date, full_name)
        square = numerology.pythagorean_square(birth_date, full_name)
        
        prompt = f"""Составь подробный нумерологический анализ на основе данных:
        
Дата рождения: {birth_date}
Имя: {full_name}

Числа:
- Жизненный путь: {numbers['life_path']}
- Душа: {numbers['soul']}
- Личность: {numbers['personality']}
- Судьба: {numbers['destiny']}

Квадрат Пифагора:
- Первая линия: {square['first_line']}
- Вторая линия: {square['second_line']}
- Третья линия: {square['third_line']}

Составь развёрнутый анализ (минимум 1000 слов) с разделами:
1. Общая характеристика личности
2. Таланты и способности
3. Карьера и финансы
4. Отношения и любовь
5. Здоровье
6. Жизненные уроки
7. Рекомендации на текущий год
8. Совместимость с другими числами

Используй эзотерический стиль, но с конкретными рекомендациями."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        return None
    
    def _get_fallback_analysis(self, birth_date, full_name: str) -> str:
        """Fallback analysis without LLM"""
        numbers = numerology.get_basic_numbers(birth_date, full_name)
        return f"""🔮 **Глубокий нумерологический анализ**

**Для:** {full_name}
**Дата рождения:** {birth_date}

---

**1. Общая характеристика**

Ваше Число Жизненного Пути — {numbers['life_path']}. Это определяет ваш основной жизненный сценарий...

**2. Таланты и способности**

Число Души {numbers['soul']} указывает на ваши глубинные таланты...

(Полный анализ доступен после интеграции с LLM API)

---

*Дисклеймер: Данный анализ носит развлекательный характер.*"""

llm = LLMService()