import httpx
from typing import Optional
from ..config import config
from ..services.numerology import numerology

# Описание входных данных для каждого типа расчёта
CALC_INPUT_DESCRIPTIONS = {
    "life_path": "📅 Использована **только дата рождения**",
    "soul": "👤 Использовано **только имя**",
    "personality": "👤 Использовано **только имя**",
    "destiny": "👤 Использовано **только имя**",
    "birthday": "📅 Использована **только дата рождения**",
}

CALC_TYPE_NAMES = {
    "life_path": "Число Жизненного Пути",
    "soul": "Число Души",
    "destiny": "Число Судьбы",
    "personality": "Число Личности",
    "birthday": "Число Дня Рождения",
}


class LLMService:
    def __init__(self):
        self.api_url = config.LLM_API_URL
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL
        print(f"[LLM] init: url={self.api_url}, key={'***' + self.api_key[-4:] if self.api_key else 'ПУСТО'}, model={self.model}", flush=True)

    def get_calc_input_description(self, calc_type: str, birth_date=None, full_name=None) -> str:
        """Return a human-readable description of which inputs are used for a calculation.

        For date-based calculations (life_path, birthday), shows the full
        digit-by-digit calculation breakdown when birth_date is provided.
        """
        # Try to generate a calculation breakdown for date-based calculations
        if birth_date is not None:
            breakdown = numerology.get_calc_breakdown(calc_type, birth_date, full_name or "")
            if breakdown:
                return breakdown

        # Fall back to generic descriptions
        return CALC_INPUT_DESCRIPTIONS.get(calc_type, "📅👤 Используются дата рождения и имя")

    def get_calc_type_name(self, calc_type: str) -> str:
        """Return a human-readable name for a calculation type"""
        return CALC_TYPE_NAMES.get(calc_type, calc_type)

    async def interpret_number(self, calc_type: str, number: int, birth_date, full_name: str) -> str:
        """Generate a short AI interpretation of a single numerology number"""
        input_desc = self.get_calc_input_description(calc_type, birth_date, full_name)
        type_name = self.get_calc_type_name(calc_type)

        if not self.api_key:
            return self._get_fallback_interpretation(calc_type, number, input_desc)

        prompt = (
            f"Ты — опытный нумеролог. Дай краткую, но содержательную расшифровку.\n\n"
            f"Человек: {full_name}, дата рождения: {birth_date}\n"
            f"Тип расчёта: {type_name}\n"
            f"Число: {number}\n\n"
            f"Напиши 3-5 предложений: что означает это число, "
            f"какие сильные стороны даёт, и один конкретный совет. "
            f"Без воды, по делу. Используй эзотерический стиль."
        )

        async with httpx.AsyncClient() as client:
            print(f"[LLM] запрос к {self.api_url}, модель={self.model}, ключ={'есть' if self.api_key else 'НЕТ'}", flush=True)
            try:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                    },
                    timeout=30.0,
                )
                print(f"[LLM] статус: {response.status_code}", flush=True)
                if response.status_code == 200:
                    ai_text = response.json()["choices"][0]["message"]["content"]
                    return f"{input_desc}\n\n{ai_text}"
                else:
                    print(f"[LLM] ошибка: {response.text[:200]}", flush=True)
            except Exception as e:
                print(f"[LLM] исключение: {e}", flush=True)
        return self._get_fallback_interpretation(calc_type, number, input_desc)

    def _get_fallback_interpretation(self, calc_type: str, number: int, input_desc: str = "") -> str:
        interpretations = {
            "life_path": {
                1: "Число Пути 1 — ты лидер по натуре. Твоя сила в самостоятельности и решительности. Совет: доверяй своей интуиции при принятии решений.",
                2: "Число Пути 2 — ты дипломат и чувствуешь других людей. Твоя сила в эмпатии и умении объединять. Совет: не забывай о своих границах.",
                3: "Число Пути 3 — ты творческая натура с яркой энергией. Твоя сила в самовыражении и оптимизме. Совет: направь творчество в конкретное русло.",
                4: "Число Пути 4 — ты строитель и организатор. Твоя сила в надёжности и системности. Совет: не бойся мечтать смелее.",
                5: "Число Пути 5 — ты искатель приключений и свободы. Твоя сила в адаптивности и энергии. Совет: найди баланс между свободой и стабильностью.",
                6: "Число Пути 6 — ты опора для близких. Твоя сила в заботе и гармонии. Совет: учись принимать помощь от других.",
                7: "Число Пути 7 — ты мыслитель и философ. Твоя сила в глубине анализа и интуиции. Совет: не замыкайся в себе, делись открытиями.",
                8: "Число Пути 8 — ты амбициозный стратег. Твоя сила в целеустремлённости и умении управлять. Совет: помни о балансе материального и духовного.",
                9: "Число Пути 9 — ты гуманист с широким сердцем. Твоя сила в сострадании и мудрости. Совет: начни с малого — помоги одному человеку.",
                11: "Мастер-число 11 — ты несёшь высшую духовную миссию. Твоя сила в интуиции и вдохновении. Совет: доверяй внутреннему голосу.",
                22: "Мастер-число 22 — ты мастер-строитель, способен менять мир. Твоя сила в масштабном видении. Совет: начни реализовывать свои большие планы.",
                33: "Мастер-число 33 — ты учитель и целитель. Твоя сила в безусловной любви. Совет: делись мудростью, но не забывай о себе.",
            },
            "soul": {
                1: "Число Души 1 — глубинная потребность в лидерстве и самовыражении.",
                2: "Число Души 2 — потребность в гармонии и глубоких связях с людьми.",
                3: "Число Души 3 — потребность в творчестве и радости.",
                4: "Число Души 4 — потребность в стабильности и порядке.",
                5: "Число Души 5 — потребность в свободе и приключениях.",
                6: "Число Души 6 — потребность в любви и заботе о близких.",
                7: "Число Души 7 — потребность в познании и уединении.",
                8: "Число Души 8 — потребность в успехе и признании.",
                9: "Число Души 9 — потребность в служении и помощи другим.",
            },
            "destiny": {
                1: "Число Судьбы 1 — твоя миссия: стать лидером и первопроходцем.",
                2: "Число Судьбы 2 — твоя миссия: объединять и сглаживать конфликты.",
                3: "Число Судьбы 3 — твоя миссия: вдохновлять и радовать мир.",
                4: "Число Судьбы 4 — твоя миссия: строить прочные основы.",
                5: "Число Судьбы 5 — твоя миссия: нести перемены и свободу.",
                6: "Число Судьбы 6 — твоя миссия: создавать гармонию вокруг.",
                7: "Число Судьбы 7 — твоя миссия: искать истину и делиться мудростью.",
                8: "Число Судьбы 8 — твоя миссия: достигать высот успеха.",
                9: "Число Судьбы 9 — твоя миссия: служить человечеству.",
            },
        }

        calc_interps = interpretations.get(calc_type, {})
        result = calc_interps.get(number, f"Число {number} несёт в себе уникальную энергию, которая проявляется через твою личность.")
        if input_desc:
            return f"{input_desc}\n\n{result}"
        return result

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
- Жизненный путь: {numbers['life_path']} (из даты рождения)
- Душа: {numbers['soul']} (из имени)
- Личность: {numbers['personality']} (из имени)
- Судьба: {numbers['destiny']} (из имени)
- День рождения: {numbers['birthday']} (из даты рождения)

Квадрат Пифагора:
- Первая линия: {square['first_line']} (из даты рождения)
- Вторая линия: {square['second_line']}
- Третья линия: {square['third_line']}
- Число имени: {square['name_value']} (из имени)

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
        square = numerology.pythagorean_square(birth_date, full_name)
        return f"""🔮 **Глубокий нумерологический анализ**

**Для:** {full_name}
**Дата рождения:** {birth_date}

---

**Как рассчитаны числа:**
- Жизненный путь: {numbers['life_path']} — из даты рождения
- Душа: {numbers['soul']} — из имени
- Личность: {numbers['personality']} — из имени
- Судьба: {numbers['destiny']} — из имени
- День рождения: {numbers['birthday']} — из даты рождения

**1. Общая характеристика**

Ваше Число Жизненного Пути — {numbers['life_path']}. Это определяет ваш основной жизненный сценарий и карьерные векторы.

**2. Таланты и способности**

Число Души {numbers['soul']} указывает на ваши глубинные таланты и внутренние желания.
Число Личности {numbers['personality']} показывает, как вас воспринимают окружающие.

**3. Карьера и финансы**

Число Судьбы {numbers['destiny']} определяет вашу судьбоносную миссию в этом мире.

**4. Отношения и любовь**

Ваши числа указывают на подход к отношениям и потребности в партнёрстве.

**5. Здоровье**

Обратите внимание на энергетические паттерны, связанные с вашими числами.

**6. Жизненные уроки**

Число Жизненного Пути {numbers['life_path']} несёт важный урок для вашего роста.

**7. Рекомендации**

Работайте с вашими сильными сторонами, основанными на числах {numbers['life_path']} и {numbers['soul']}.

**8. Квадрат Пифагора**

Первая линия: {square['first_line']}
Вторая линия: {square['second_line']}
Третья линия: {square['third_line']}
Число имени: {square['name_value']}

---

*Дисклеймер: Данный анализ носит развлекательный характер.*"""

llm = LLMService()
