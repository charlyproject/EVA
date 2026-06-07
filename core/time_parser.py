import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("EVA")

class InputType(Enum):
    CHAT = "chat"
    VOICE = "voice"
    MIXED = "mixed"

class TimeContext(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    WORK_HOURS = "work_hours"
    WEEKEND = "weekend"

@dataclass
class TimeCandidate:
    datetime: datetime
    confidence: float
    source_pattern: str
    ambiguity_level: int
    context_hints: List[str]

@dataclass
class ParseResult:
    datetime: Optional[datetime]
    confidence: float
    suggestions: List[str]
    warnings: List[str]
    ambiguities: List[str]
    input_type: InputType

@dataclass
class UserContext:
    current_time: datetime
    timezone: str
    work_hours: Tuple[int, int]
    language: str
    recent_events: List[Dict]
    conversation_history: List[str]
    user_patterns: Dict[str, any]

class RobustBilingualTimeParser:
    def __init__(self, language_manager):
        self.language_manager = language_manager
        
        # Patrones optimizados para CHAT (entrada escrita)
        self.chat_patterns = {
            'es': {
                'time_formats': [
                    (r'(\d{1,2}):(\d{2})', 0.9, 'HH:MM'),                    # 18:30
                    (r'(\d{1,2})\.(\d{2})', 0.8, 'HH.MM'),                   # 18.30
                    (r'(\d{1,2})h(\d{2})', 0.8, 'HHhMM'),                    # 18h30
                    (r'(\d{4})', 0.7, 'HHMM'),                               # 1830
                    (r'(\d{1,2}) ?(am|pm)', 0.8, '12H'),                     # 6 PM
                    (r'(\d{1,2}):(\d{2}) ?(am|pm)', 0.9, '12H:MM'),          # 6:30 PM
                ],
                'natural_expressions': [
                    (r'seis y media de la tarde', lambda: 18.5, 0.9),
                    (r'ocho y cuarto de la mañana', lambda: 8.25, 0.9),
                    (r'nueve menos cuarto', lambda: 8.75, 0.8),
                    (r'mediodía', lambda: 12.0, 1.0),
                    (r'medianoche', lambda: 0.0, 1.0),
                    (r'al mediodía', lambda: 12.0, 1.0),
                    (r'a medianoche', lambda: 0.0, 1.0),
                    (r'por la mañana', lambda: 9.0, 0.6),
                    (r'por la tarde', lambda: 15.0, 0.6),
                    (r'por la noche', lambda: 20.0, 0.6),
                    (r'después del almuerzo', lambda: 14.0, 0.7),
                    (r'antes del almuerzo', lambda: 11.0, 0.7),
                ],
                'relative_time': [
                    (r'en (\d+) minutos?', lambda m: timedelta(minutes=int(m.group(1))), 0.9),
                    (r'en (\d+) horas?', lambda m: timedelta(hours=int(m.group(1))), 0.9),
                    (r'en media hora', lambda m: timedelta(minutes=30), 0.9),
                    (r'en un cuarto de hora', lambda m: timedelta(minutes=15), 0.9),
                    (r'ahora', lambda m: timedelta(0), 1.0),
                    (r'ya', lambda m: timedelta(0), 0.8),
                ]
            },
            'en': {
                'time_formats': [
                    (r'(\d{1,2}):(\d{2}) ?(am|pm)', 0.9, '12H:MM'),          # 6:30 PM
                    (r'(\d{1,2}) ?(am|pm)', 0.8, '12H'),                     # 6 PM
                    (r'(\d{1,2}):(\d{2})', 0.8, '24H:MM'),                   # 18:30
                    (r'(\d{4})', 0.6, 'HHMM'),                               # 1830
                ],
                'natural_expressions': [
                    (r'half past six', lambda: 18.5, 0.9),
                    (r'quarter past eight', lambda: 8.25, 0.9),
                    (r'quarter to nine', lambda: 8.75, 0.8),
                    (r'noon', lambda: 12.0, 1.0),
                    (r'midnight', lambda: 0.0, 1.0),
                    (r'at noon', lambda: 12.0, 1.0),
                    (r'at midnight', lambda: 0.0, 1.0),
                    (r'in the morning', lambda: 9.0, 0.6),
                    (r'in the afternoon', lambda: 15.0, 0.6),
                    (r'in the evening', lambda: 19.0, 0.6),
                    (r'after lunch', lambda: 14.0, 0.7),
                    (r'before lunch', lambda: 11.0, 0.7),
                ],
                'relative_time': [
                    (r'in (\d+) minutes?', lambda m: timedelta(minutes=int(m.group(1))), 0.9),
                    (r'in (\d+) hours?', lambda m: timedelta(hours=int(m.group(1))), 0.9),
                    (r'in half an hour', lambda m: timedelta(minutes=30), 0.9),
                    (r'in a quarter hour', lambda m: timedelta(minutes=15), 0.9),
                    (r'now', lambda m: timedelta(0), 1.0),
                    (r'right now', lambda m: timedelta(0), 1.0),
                ]
            }
        }
        
        # Patrones para VOZ (entrada hablada)
        self.voice_patterns = {
            'es': {
                'spoken_numbers': {
                    'cero': 0, 'una': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
                    'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
                    'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
                    'dieciséis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19,
                    'veinte': 20, 'veintiuno': 21, 'veintidós': 22, 'veintitrés': 23
                },
                'time_expressions': [
                    (r'(.*) y media', lambda m: self._parse_spoken_hour(m.group(1)) + 0.5, 0.9),
                    (r'(.*) y cuarto', lambda m: self._parse_spoken_hour(m.group(1)) + 0.25, 0.9),
                    (r'(.*) menos cuarto', lambda m: self._parse_spoken_hour(m.group(1)) - 0.25, 0.8),
                ]
            },
            'en': {
                'spoken_numbers': {
                    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
                    'twenty': 20, 'twenty-one': 21, 'twenty-two': 22, 'twenty-three': 23
                },
                'time_expressions': [
                    (r'half past (.*)', lambda m: self._parse_spoken_hour(m.group(1)) + 0.5, 0.9),
                    (r'quarter past (.*)', lambda m: self._parse_spoken_hour(m.group(1)) + 0.25, 0.9),
                    (r'quarter to (.*)', lambda m: self._parse_spoken_hour(m.group(1)) - 0.25, 0.8),
                ]
            }
        }
        
        # Patrones en español (legacy compatibility)
        self.es_patterns = {
            'relative_time': {
                r'en (\d+) minutos?': lambda m: timedelta(minutes=int(m.group(1))),
                r'en (\d+) horas?': lambda m: timedelta(hours=int(m.group(1))),
                r'en (\d+) días?': lambda m: timedelta(days=int(m.group(1))),
                r'en (\d+) semanas?': lambda m: timedelta(weeks=int(m.group(1))),
                r'mañana': lambda m: timedelta(days=1),
                r'pasado mañana': lambda m: timedelta(days=2),
                r'la próxima semana': lambda m: timedelta(days=7),
                r'el próximo mes': lambda m: timedelta(days=30),
            },
            'days': {
                'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
                'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
            },
            'months': {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            },
            'time_indicators': {
                'mañana': 'morning',
                'tarde': 'afternoon', 
                'noche': 'evening',
                'madrugada': 'dawn'
            },
            'day_references': {
                'hoy': 0,
                'mañana': 1,
                'pasado mañana': 2,
                'ayer': -1
            }
        }
        
        # Patrones en inglés
        self.en_patterns = {
            'relative_time': {
                r'in (\d+) minutes?': lambda m: timedelta(minutes=int(m.group(1))),
                r'in (\d+) hours?': lambda m: timedelta(hours=int(m.group(1))),
                r'in (\d+) days?': lambda m: timedelta(days=int(m.group(1))),
                r'in (\d+) weeks?': lambda m: timedelta(weeks=int(m.group(1))),
                r'tomorrow': lambda m: timedelta(days=1),
                r'day after tomorrow': lambda m: timedelta(days=2),
                r'next week': lambda m: timedelta(days=7),
                r'next month': lambda m: timedelta(days=30),
            },
            'days': {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            },
            'months': {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            },
            'time_indicators': {
                'morning': 'morning',
                'afternoon': 'afternoon',
                'evening': 'evening',
                'night': 'evening',
                'dawn': 'dawn'
            },
            'day_references': {
                'today': 0,
                'tomorrow': 1,
                'day after tomorrow': 2,
                'yesterday': -1
            }
        }

    def parse_time_expression(self, text: str) -> Optional[datetime]:
        """Parsea una expresión de tiempo en español o inglés"""
        text = text.lower().strip()
        
        try:
            # Detectar idioma basado en palabras clave
            is_spanish = self._detect_spanish(text)
            patterns = self.es_patterns if is_spanish else self.en_patterns
            
            # Intentar diferentes tipos de parsing
            result = (self._parse_relative_time(text, patterns) or
                     self._parse_specific_time(text, patterns) or
                     self._parse_day_reference(text, patterns) or
                     self._parse_date_time(text, patterns))
            
            if result:
                logger.debug(f"Parsed time '{text}' -> {result}")
                return result
            else:
                logger.warning(f"Could not parse time expression: '{text}'")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing time '{text}': {str(e)}")
            return None

    def _detect_spanish(self, text: str) -> bool:
        """Detecta si el texto está en español"""
        spanish_indicators = [
            'mañana', 'tarde', 'noche', 'hoy', 'ayer', 'próximo', 'próxima',
            'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
            'minutos', 'horas', 'días', 'semanas', 'en'
        ]
        
        english_indicators = [
            'tomorrow', 'today', 'yesterday', 'next', 'morning', 'afternoon', 'evening',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'minutes', 'hours', 'days', 'weeks', 'in'
        ]
        
        spanish_count = sum(1 for word in spanish_indicators if word in text)
        english_count = sum(1 for word in english_indicators if word in text)
        
        return spanish_count >= english_count

    def _parse_relative_time(self, text: str, patterns: Dict) -> Optional[datetime]:
        """Parsea tiempo relativo (en X minutos, in X hours)"""
        for pattern, handler in patterns['relative_time'].items():
            match = re.search(pattern, text)
            if match:
                delta = handler(match)
                return datetime.now() + delta
        return None

    def _parse_specific_time(self, text: str, patterns: Dict) -> Optional[datetime]:
        """Parsea hora específica (a las 15:30, at 3:30 PM)"""
        # Patrones de hora
        time_patterns = [
            r'a las (\d{1,2}):(\d{2})',  # a las 15:30
            r'a las (\d{1,2})',          # a las 15
            r'at (\d{1,2}):(\d{2})',     # at 3:30
            r'at (\d{1,2})',             # at 3
            r'(\d{1,2}):(\d{2})',        # 15:30
            r'(\d{1,2}) ?(am|pm)',       # 3 PM, 3PM
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) >= 2 and match.group(2).isdigit():
                        # Formato HH:MM
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                    elif len(match.groups()) >= 2 and match.group(2) in ['am', 'pm']:
                        # Formato 12 horas
                        hour = int(match.group(1))
                        minute = 0
                        if match.group(2) == 'pm' and hour != 12:
                            hour += 12
                        elif match.group(2) == 'am' and hour == 12:
                            hour = 0
                    else:
                        # Solo hora
                        hour = int(match.group(1))
                        minute = 0
                    
                    # Determinar fecha base
                    base_date = self._get_base_date(text, patterns)
                    
                    # Crear datetime
                    result = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Si la hora ya pasó hoy, mover a mañana
                    if result <= datetime.now() and base_date.date() == datetime.now().date():
                        result += timedelta(days=1)
                    
                    return result
                    
                except ValueError:
                    continue
        
        return None

    def _parse_day_reference(self, text: str, patterns: Dict) -> Optional[datetime]:
        """Parsea referencias de día (lunes, next friday)"""
        # Buscar día de la semana
        for day_name, day_num in patterns['days'].items():
            if day_name in text:
                return self._get_next_weekday(day_num, text, patterns)
        
        # Buscar referencias directas
        for ref, days_offset in patterns['day_references'].items():
            if ref in text:
                base_date = datetime.now() + timedelta(days=days_offset)
                # Si hay hora específica en el texto, parsearla
                time_part = self._extract_time_from_text(text)
                if time_part:
                    try:
                        hour, minute = time_part
                        return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    except Exception:
                        pass
                return base_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Default 9 AM
        
        return None

    def _parse_date_time(self, text: str, patterns: Dict) -> Optional[datetime]:
        """Parsea fecha y hora específica (15 de marzo a las 10:30)"""
        # Patrones de fecha
        date_patterns = [
            r'(\d{1,2}) de (\w+)',           # 15 de marzo
            r'(\d{1,2})/(\d{1,2})',          # 15/03
            r'(\d{1,2})-(\d{1,2})',          # 15-03
            r'(\w+) (\d{1,2})',              # March 15
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    day = int(match.group(1))
                    month_str = match.group(2)
                    
                    # Convertir mes
                    if month_str.isdigit():
                        month = int(month_str)
                    else:
                        month = patterns['months'].get(month_str.lower())
                        if not month:
                            continue
                    
                    year = datetime.now().year
                    
                    # Crear fecha base
                    base_date = datetime(year, month, day)
                    
                    # Buscar hora en el texto
                    time_part = self._extract_time_from_text(text)
                    if time_part:
                        hour, minute = time_part
                        return base_date.replace(hour=hour, minute=minute)
                    else:
                        return base_date.replace(hour=9, minute=0)  # Default 9 AM
                        
                except ValueError:
                    continue
        
        return None

    def _get_base_date(self, text: str, patterns: Dict) -> datetime:
        """Obtiene la fecha base para una expresión de tiempo"""
        # Buscar indicadores de día
        for ref, days_offset in patterns['day_references'].items():
            if ref in text:
                return datetime.now() + timedelta(days=days_offset)
        
        # Buscar día de la semana
        for day_name, day_num in patterns['days'].items():
            if day_name in text:
                return self._get_next_weekday_date(day_num)
        
        # Default: hoy
        return datetime.now()

    def _get_next_weekday(self, target_day: int, text: str, patterns: Dict) -> datetime:
        """Obtiene la próxima ocurrencia de un día de la semana"""
        today = datetime.now()
        days_ahead = target_day - today.weekday()
        
        # Si es el mismo día pero ya pasó la hora, ir a la próxima semana
        if days_ahead <= 0:
            days_ahead += 7
        
        # Si dice "próximo" o "next", forzar la próxima semana
        if any(word in text for word in ['próximo', 'próxima', 'next']):
            if days_ahead < 7:
                days_ahead += 7
        
        target_date = today + timedelta(days=days_ahead)
        
        # Buscar hora específica
        time_part = self._extract_time_from_text(text)
        if time_part:
            hour, minute = time_part
            return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return target_date.replace(hour=9, minute=0, second=0, microsecond=0)

    def _get_next_weekday_date(self, target_day: int) -> datetime:
        """Obtiene la fecha del próximo día de la semana especificado"""
        today = datetime.now()
        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def _extract_time_from_text(self, text: str) -> Optional[Tuple[int, int]]:
        """Extrae hora y minuto del texto"""
        time_patterns = [
            r'(\d{1,2}):(\d{2})',        # 15:30
            r'a las (\d{1,2}):(\d{2})',  # a las 15:30
            r'at (\d{1,2}):(\d{2})',     # at 3:30
            r'a las (\d{1,2})',          # a las 15
            r'at (\d{1,2})',             # at 3
            r'(\d{1,2}) ?(am|pm)',       # 3 PM
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) >= 2 and match.group(2).isdigit():
                        return (int(match.group(1)), int(match.group(2)))
                    elif len(match.groups()) >= 2 and match.group(2) in ['am', 'pm']:
                        hour = int(match.group(1))
                        if match.group(2) == 'pm' and hour != 12:
                            hour += 12
                        elif match.group(2) == 'am' and hour == 12:
                            hour = 0
                        return (hour, 0)
                    else:
                        return (int(match.group(1)), 0)
                except ValueError:
                    continue
        
        return None

    def parse_duration(self, text: str) -> Optional[timedelta]:
        """Parsea duración (2 horas, 30 minutes)"""
        duration_patterns = [
            (r'(\d+) horas?', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+) minutos?', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+) hours?', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+) minutes?', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+)h', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+)m', lambda m: timedelta(minutes=int(m.group(1)))),
        ]
        
        for pattern, handler in duration_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return handler(match)
        
        return None

    def extract_event_details(self, text: str) -> Dict:
        """Extrae detalles del evento del texto"""
        details = {
            'title': '',
            'start_time': None,
            'end_time': None,
            'duration': None,
            'category': 'personal',
            'location': '',
            'description': ''
        }
        
        # Parsear tiempo de inicio
        details['start_time'] = self.parse_time_expression(text)
        
        # Parsear duración
        details['duration'] = self.parse_duration(text)
        
        # Calcular tiempo de fin si hay duración
        if details['start_time'] and details['duration']:
            details['end_time'] = details['start_time'] + details['duration']
        
        # Extraer título (simplificado)
        # Remover palabras de tiempo y comando para obtener el título
        title_text = text
        time_words = ['en', 'a las', 'at', 'mañana', 'tomorrow', 'hoy', 'today', 
                     'próximo', 'next', 'programa', 'schedule', 'crear', 'create',
                     'recordatorio', 'reminder', 'evento', 'event']
        
        for word in time_words:
            title_text = re.sub(rf'\b{word}\b', '', title_text, flags=re.IGNORECASE)
        
        # Limpiar y extraer título
        title_text = re.sub(r'\d{1,2}:\d{2}', '', title_text)  # Remover horas
        title_text = re.sub(r'\d{1,2}/\d{1,2}', '', title_text)  # Remover fechas
        title_text = ' '.join(title_text.split())  # Limpiar espacios
        
        details['title'] = title_text.strip() or 'Evento'
        
        # Detectar categoría por palabras clave
        work_keywords = ['reunión', 'meeting', 'trabajo', 'work', 'oficina', 'office', 'cliente', 'client']
        medical_keywords = ['médico', 'doctor', 'hospital', 'cita médica', 'medical', 'dentista', 'dentist']
        personal_keywords = ['personal', 'familia', 'family', 'amigo', 'friend']
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in work_keywords):
            details['category'] = 'work'
        elif any(keyword in text_lower for keyword in medical_keywords):
            details['category'] = 'medical'
        elif any(keyword in text_lower for keyword in personal_keywords):
            details['category'] = 'personal'
        
        return details

    def format_datetime_natural(self, dt: datetime, language: str = None) -> str:
        """Formatea datetime de manera natural según el idioma"""
        if language is None:
            language = self.language_manager.current_lang
        
        now = datetime.now()
        
        if language == 'es':
            # Español
            days = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                     'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
            
            if dt.date() == now.date():
                return f"hoy a las {dt.strftime('%H:%M')}"
            elif dt.date() == (now + timedelta(days=1)).date():
                return f"mañana a las {dt.strftime('%H:%M')}"
            elif dt.date() == (now - timedelta(days=1)).date():
                return f"ayer a las {dt.strftime('%H:%M')}"
            else:
                day_name = days[dt.weekday()]
                if abs((dt.date() - now.date()).days) <= 7:
                    return f"{day_name} a las {dt.strftime('%H:%M')}"
                else:
                    month_name = months[dt.month - 1]
                    return f"{dt.day} de {month_name} a las {dt.strftime('%H:%M')}"
        else:
            # English
            if dt.date() == now.date():
                return f"today at {dt.strftime('%I:%M %p')}"
            elif dt.date() == (now + timedelta(days=1)).date():
                return f"tomorrow at {dt.strftime('%I:%M %p')}"
            elif dt.date() == (now - timedelta(days=1)).date():
                return f"yesterday at {dt.strftime('%I:%M %p')}"
            else:
                if abs((dt.date() - now.date()).days) <= 7:
                    return f"{dt.strftime('%A')} at {dt.strftime('%I:%M %p')}"
                else:
                    return f"{dt.strftime('%B %d')} at {dt.strftime('%I:%M %p')}"