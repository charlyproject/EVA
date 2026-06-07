import logging
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("EVA")

class SimpleCitaHandler:
    """Handler ultra-simple para comandos CITA - Con interfaz guiada"""
    
    def __init__(self, processor):
        self.processor = processor
        self.calendar_manager = None
        
        # SISTEMA DE ESTADOS CONVERSACIONALES
        self.user_states = {}  # {user_id: estado_actual}
        self.pending_citas = {}  # {user_id: datos_cita_parcial}
        
    def set_calendar_manager(self, calendar_manager):
        """Establece el gestor de calendario"""
        self.calendar_manager = calendar_manager
        
    def can_handle(self, text: str) -> bool:
        """Maneja comandos cita + sistema conversacional guiado - BILINGÜE"""
        text_lower = text.lower().strip()
        
        # SISTEMA CONVERSACIONAL: Si usuario está en proceso de crear cita
        user_id = "default"  # En una implementación real sería el ID del usuario
        if user_id in self.user_states:
            return True  # Capturar cualquier respuesta durante el proceso
        
        # Usar command_map centralizado para comandos de citas
        appointment_keywords_es = self.processor.command_map.get("appointment", {}).get("es", [])
        appointment_keywords_en = self.processor.command_map.get("appointment", {}).get("en", [])
        appointments_keywords_es = self.processor.command_map.get("appointments", {}).get("es", [])
        appointments_keywords_en = self.processor.command_map.get("appointments", {}).get("en", [])
        
        # COMANDOS BILINGÜES SOPORTADOS usando command_map
        all_appointment_keywords = appointment_keywords_es + appointment_keywords_en
        all_appointments_keywords = appointments_keywords_es + appointments_keywords_en
        
        # Verificar comandos de cita (singular)
        appointment_commands = any(
            text_lower == keyword or text_lower.startswith(f"{keyword} ")
            for keyword in all_appointment_keywords
        )
        
        # Verificar comandos de citas (plural)
        appointments_commands = any(
            text_lower == keyword or text_lower.startswith(f"{keyword} ") or 
            text_lower.startswith(f"{keyword} cancelar") or text_lower.startswith(f"{keyword} cancel")
            for keyword in all_appointments_keywords
        )
        
        return appointment_commands or appointments_commands
    
    def handle(self, text: str, chat_window) -> bool:
        """Manejo con sistema conversacional guiado"""
        if not self.calendar_manager:
            chat_window.add_message("❌ Sistema de citas no disponible", is_user=False)
            return True
            
        text_lower = text.lower().strip()
        user_id = "default"  # En implementación real sería ID único del usuario
        
        try:
            # SISTEMA CONVERSACIONAL: Si usuario está en proceso
            if user_id in self.user_states:
                return self._handle_conversational_state(text, chat_window, user_id)
            
            # 1. INICIAR PROCESO GUIADO: "cita" / "appointment"
            if text_lower == 'cita' or text_lower == 'appointment':
                return self._start_guided_cita_creation(chat_window, user_id)
            
            # 2. CREAR CITA DIRECTA: "cita X Y Z" / "appointment X Y Z"
            elif text_lower.startswith('cita '):
                command = text[5:].strip()  # Quitar 'cita '
                return self._create_cita(command, chat_window)
            elif text_lower.startswith('appointment '):
                command = text[12:].strip()  # Quitar 'appointment '
                return self._create_cita(command, chat_window)
            
            # 3. LISTAR CITAS: "citas"/"appointments" o "citas mañana"/"appointments tomorrow"
            elif text_lower == 'citas' or text_lower == 'appointments':
                return self._list_citas_today(chat_window)
            elif text_lower.startswith('citas ') and not text_lower.startswith('citas cancelar'):
                command = text[6:].strip()  # Quitar 'citas '
                return self._list_citas_date(command, chat_window)
            elif text_lower.startswith('appointments ') and not text_lower.startswith('appointments cancel'):
                command = text[13:].strip()  # Quitar 'appointments '
                return self._list_citas_date(command, chat_window)
            
            # 4. CANCELAR CITAS: "citas cancelar" / "appointments cancel"
            elif text_lower.startswith('citas cancelar'):
                command = text[14:].strip()  # Quitar 'citas cancelar'
                return self._cancel_cita(command, chat_window)
            elif text_lower.startswith('appointments cancel'):
                command = text[19:].strip()  # Quitar 'appointments cancel'
                return self._cancel_cita(command, chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error in simple cita handler: {str(e)}")
            chat_window.add_message("❌ Error en comando de citas", is_user=False)
            return True
    
    def _create_cita(self, command: str, chat_window) -> bool:
        """CREAR CITA: Parser ultra-simple"""
        try:
            # Extraer hora y título
            event_time = self._extract_time(command)
            event_title = self._extract_title(command)
            
            if not event_time:
                chat_window.add_message(
                    "❌ No entendí la hora.\n"
                    "💡 Formatos soportados (hora en HH:MM):\n"
                    "• cita médico hoy 12:30\n"
                    "• cita reunión mañana 15:00\n"
                    "• cita dentista viernes 09:15\n"
                    "• cita médico 22 de febrero 12:40\n"
                    "• cita reunión 15/03 14:30", 
                    is_user=False
                )
                return True
            
            if not event_title:
                event_title = "Evento"
            
            # Crear evento
            success = self.calendar_manager.create_event(
                title=event_title,
                start_time=event_time,
                end_time=event_time,
                category='personal',
                reminder_minutes=15
            )
            
            if success:
                date_str = event_time.strftime('%d/%m')
                time_str = event_time.strftime('%H:%M')
                chat_window.add_message(
                    f"✅ Cita creada: {event_title}\n"
                    f"📅 {date_str} a las {time_str}", 
                    is_user=False
                )
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    voice_msg = f"Cita creada: {event_title} para el {date_str} a las {time_str}"
                    self.processor.eva.speech.speak(voice_msg)
            else:
                chat_window.add_message("❌ Error creando cita", is_user=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating cita: {str(e)}")
            chat_window.add_message("❌ Error creando cita", is_user=False)
            return True
    
    def _list_citas_today(self, chat_window) -> bool:
        """LISTAR CITAS DE HOY"""
        try:
            today = datetime.now().date()
            events = self.calendar_manager.get_events_for_date(today)
            
            if not events:
                chat_window.add_message("📅 No tienes citas para hoy", is_user=False)
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    self.processor.eva.speech.speak("No tienes citas para hoy")
            else:
                agenda_text = "📅 Tus citas de hoy:\n"
                voice_text = "Tus citas de hoy: "
                
                for i, event in enumerate(events, 1):
                    time_str = event['start_time'].strftime('%H:%M')
                    agenda_text += f"{i}. {time_str} - {event['title']}\n"
                    voice_text += f"{event['title']} a las {time_str}. "
                
                chat_window.add_message(agenda_text.strip(), is_user=False)
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    self.processor.eva.speech.speak(voice_text)
            
            return True
            
        except Exception as e:
            logger.error(f"Error listing today's citas: {str(e)}")
            chat_window.add_message("❌ Error mostrando citas", is_user=False)
            return True
    
    def _list_citas_date(self, date_command: str, chat_window) -> bool:
        """LISTAR CITAS PARA FECHA ESPECÍFICA"""
        try:
            target_date = self._parse_date(date_command)
            
            if not target_date:
                chat_window.add_message(
                    "❌ No entendí la fecha.\n"
                    "💡 Ejemplos: citas mañana, citas hoy", 
                    is_user=False
                )
                return True
            
            events = self.calendar_manager.get_events_for_date(target_date)
            
            date_name = self._get_date_name(date_command)
            
            if not events:
                chat_window.add_message(f"📅 No tienes citas para {date_name}", is_user=False)
            else:
                agenda_text = f"📅 Tus citas de {date_name}:\n"
                
                for i, event in enumerate(events, 1):
                    time_str = event['start_time'].strftime('%H:%M')
                    agenda_text += f"{i}. {time_str} - {event['title']}\n"
                
                chat_window.add_message(agenda_text.strip(), is_user=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error listing citas for date: {str(e)}")
            chat_window.add_message("❌ Error mostrando citas", is_user=False)
            return True
    
    def _cancel_cita(self, command: str, chat_window) -> bool:
        """CANCELAR CITAS con opciones"""
        try:
            if not command.strip():
                # "citas cancelar" sin especificar - mostrar opciones
                return self._show_cancel_options(chat_window)
            
            # "citas cancelar X" - cancelar específico
            if command.isdigit():
                # "citas cancelar 1" - cancelar por número
                return self._cancel_by_number(int(command), chat_window)
            else:
                # "citas cancelar médico" - cancelar por nombre
                return self._cancel_by_name(command, chat_window)
            
        except Exception as e:
            logger.error(f"Error cancelling cita: {str(e)}")
            chat_window.add_message("❌ Error cancelando cita", is_user=False)
            return True
    
    def _show_cancel_options(self, chat_window) -> bool:
        """Mostrar opciones de citas para cancelar"""
        try:
            # Obtener citas de hoy y próximos días
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            today_events = self.calendar_manager.get_events_for_date(today)
            tomorrow_events = self.calendar_manager.get_events_for_date(tomorrow)
            
            all_events = today_events + tomorrow_events
            
            if not all_events:
                chat_window.add_message("📅 No tienes citas para cancelar", is_user=False)
                return True
            
            cancel_text = "📅 Citas que puedes cancelar:\n"
            
            for i, event in enumerate(all_events, 1):
                date_str = event['start_time'].strftime('%d/%m')
                time_str = event['start_time'].strftime('%H:%M')
                cancel_text += f"{i}. {date_str} {time_str} - {event['title']}\n"
            
            cancel_text += "\n💡 Para cancelar:\n"
            cancel_text += "• citas cancelar 1 (por número)\n"
            cancel_text += "• citas cancelar médico (por nombre)"
            
            chat_window.add_message(cancel_text, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error showing cancel options: {str(e)}")
            chat_window.add_message("❌ Error mostrando opciones", is_user=False)
            return True
    
    def _cancel_by_number(self, number: int, chat_window) -> bool:
        """Cancelar cita por número de la lista"""
        try:
            # Obtener lista actual de eventos
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            today_events = self.calendar_manager.get_events_for_date(today)
            tomorrow_events = self.calendar_manager.get_events_for_date(tomorrow)
            
            all_events = today_events + tomorrow_events
            
            if number < 1 or number > len(all_events):
                chat_window.add_message(f"❌ Número inválido. Tienes {len(all_events)} citas", is_user=False)
                return True
            
            event = all_events[number - 1]
            success = self.calendar_manager.cancel_event(event['id'])
            
            if success:
                chat_window.add_message(f"✅ Cita cancelada: {event['title']}", is_user=False)
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    self.processor.eva.speech.speak(f"Cita cancelada: {event['title']}")
            else:
                chat_window.add_message("❌ Error cancelando cita", is_user=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling by number: {str(e)}")
            chat_window.add_message("❌ Error cancelando cita", is_user=False)
            return True
    
    def _cancel_by_name(self, name: str, chat_window) -> bool:
        """Cancelar cita por nombre"""
        try:
            # Buscar eventos que coincidan
            matching_events = self.calendar_manager.find_events_by_title(name)
            
            if not matching_events:
                chat_window.add_message(f"❌ No encontré cita con '{name}'", is_user=False)
                return True
            
            if len(matching_events) > 1:
                # Múltiples coincidencias - mostrar opciones
                options_text = f"📅 Encontré varias citas con '{name}':\n"
                
                for i, event in enumerate(matching_events[:5], 1):
                    date_str = event['start_time'].strftime('%d/%m')
                    time_str = event['start_time'].strftime('%H:%M')
                    options_text += f"{i}. {date_str} {time_str} - {event['title']}\n"
                
                options_text += "\n💡 Di: citas cancelar 1 (para elegir)"
                chat_window.add_message(options_text, is_user=False)
                return True
            
            # Una sola coincidencia - cancelar directamente
            event = matching_events[0]
            success = self.calendar_manager.cancel_event(event['id'])
            
            if success:
                chat_window.add_message(f"✅ Cita cancelada: {event['title']}", is_user=False)
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    self.processor.eva.speech.speak(f"Cita cancelada: {event['title']}")
            else:
                chat_window.add_message("❌ Error cancelando cita", is_user=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling by name: {str(e)}")
            chat_window.add_message("❌ Error cancelando cita", is_user=False)
            return True
    
    def _extract_time(self, text: str) -> Optional[datetime]:
        """Parser MEJORADO - Soporta fechas específicas y formato HH:MM"""
        try:
            # FORMATO HORA: HH:MM (ej: 13:15, 09:30, 18:45)
            time_match = re.search(r'(\d{1,2}):(\d{2})', text)
            if not time_match:
                return None
                
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Validar hora (formato 24h)
            if hour > 23 or minute > 59:
                return None
            
            # DETERMINAR FECHA - MÚLTIPLES FORMATOS
            target_date = self._parse_date_from_text(text)
            
            return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
            
        except Exception:
            return None
    
    def _parse_date_from_text(self, text: str) -> datetime.date:
        """Parser de fechas mejorado - soporta múltiples formatos"""
        text_lower = text.lower()
        
        # 1. FECHAS ESPECÍFICAS: "22 de febrero", "15 de marzo"
        date_specific = self._parse_specific_date(text_lower)
        if date_specific:
            return date_specific
        
        # 2. FECHAS NUMÉRICAS: "22/02", "15/03"  
        date_numeric = self._parse_numeric_date(text_lower)
        if date_numeric:
            return date_numeric
        
        # 3. FECHAS RELATIVAS: "hoy"/"today", "mañana"/"tomorrow"
        if 'mañana' in text_lower or 'tomorrow' in text_lower:
            return (datetime.now() + timedelta(days=1)).date()
        elif 'hoy' in text_lower or 'today' in text_lower:
            return datetime.now().date()
        
        # 4. DÍAS DE SEMANA: "lunes", "martes", etc.
        weekday_date = self._parse_weekday(text_lower)
        if weekday_date:
            return weekday_date
        
        # 5. DEFAULT: hoy
        return datetime.now().date()
    
    def _parse_specific_date(self, text: str) -> Optional[datetime.date]:
        """Parser para fechas como '22 de febrero', '15 de marzo'"""
        try:
            # Meses en español
            months = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            
            # Patrón: "22 de febrero", "día 15 de marzo"
            pattern = r'(?:día\s+)?(\d{1,2})\s+de\s+(\w+)'
            match = re.search(pattern, text)
            
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                
                if month_name in months:
                    month = months[month_name]
                    year = datetime.now().year
                    
                    # Si la fecha ya pasó este año, usar el próximo año
                    target_date = datetime(year, month, day).date()
                    if target_date < datetime.now().date():
                        target_date = datetime(year + 1, month, day).date()
                    
                    return target_date
            
            return None
            
        except Exception:
            return None
    
    def _parse_numeric_date(self, text: str) -> Optional[datetime.date]:
        """Parser para fechas como '22/02', '15/03'"""
        try:
            # Patrón: DD/MM
            pattern = r'(\d{1,2})/(\d{1,2})'
            match = re.search(pattern, text)
            
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = datetime.now().year
                
                # Validar día y mes
                if 1 <= day <= 31 and 1 <= month <= 12:
                    # Si la fecha ya pasó este año, usar el próximo año
                    target_date = datetime(year, month, day).date()
                    if target_date < datetime.now().date():
                        target_date = datetime(year + 1, month, day).date()
                    
                    return target_date
            
            return None
            
        except Exception:
            return None
    
    def _parse_weekday(self, text: str) -> Optional[datetime.date]:
        """Parser para días de semana - BILINGÜE"""
        try:
            weekdays = {
                # Español
                'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3,
                'viernes': 4, 'sábado': 5, 'domingo': 6,
                # English
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            for day_name, target_weekday in weekdays.items():
                if day_name in text:
                    today = datetime.now().date()
                    current_weekday = today.weekday()
                    
                    # Calcular días hasta el próximo día de semana
                    days_ahead = target_weekday - current_weekday
                    if days_ahead <= 0:  # Si es hoy o ya pasó, próxima semana
                        days_ahead += 7
                    
                    return today + timedelta(days=days_ahead)
            
            return None
            
        except Exception:
            return None
    
    def _extract_title(self, text: str) -> str:
        """Extraer título del evento - BILINGÜE"""
        try:
            # Remover palabras de tiempo y fecha - BILINGÜE
            time_words = [
                # Español
                'hoy', 'mañana', 'ayer',
                'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
                # English
                'today', 'tomorrow', 'yesterday',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
            ]
            
            words = text.split()
            title_words = []
            
            for word in words:
                # Saltar números de tiempo (HH:MM)
                if ':' in word:
                    continue
                # Saltar fechas numéricas (DD/MM)
                if '/' in word and len(word) <= 5:
                    continue
                # Saltar palabras de tiempo/fecha
                if word.lower() in time_words:
                    continue
                title_words.append(word)
            
            title = ' '.join(title_words).strip()
            
            # Título por defecto según contexto
            if not title:
                return 'Event'  # Neutral para ambos idiomas
            
            return title
            
        except Exception:
            return 'Event'
    
    def _parse_date(self, date_command: str) -> Optional[datetime.date]:
        """Parser simple de fechas - BILINGÜE"""
        date_command = date_command.lower()
        
        # Fechas relativas bilingües
        if date_command in ['hoy', 'today']:
            return datetime.now().date()
        elif date_command in ['mañana', 'tomorrow']:
            return (datetime.now() + timedelta(days=1)).date()
        elif date_command in ['ayer', 'yesterday']:
            return (datetime.now() - timedelta(days=1)).date()
        
        return None
    
    def _get_date_name(self, date_command: str) -> str:
        """Obtener nombre legible de la fecha - BILINGÜE"""
        date_command = date_command.lower()
        
        # Detectar idioma del comando
        if 'today' in date_command or 'tomorrow' in date_command or 'yesterday' in date_command:
            # English
            if date_command in ['today']:
                return 'today'
            elif date_command in ['tomorrow']:
                return 'tomorrow'
            elif date_command in ['yesterday']:
                return 'yesterday'
        else:
            # Spanish
            if date_command in ['hoy']:
                return 'hoy'
            elif date_command in ['mañana']:
                return 'mañana'
            elif date_command in ['ayer']:
                return 'ayer'
        
        return date_command
    
    # ==========================================
    # SISTEMA CONVERSACIONAL GUIADO MEJORADO
    # ==========================================
    
    def _start_guided_cita_creation(self, chat_window, user_id: str) -> bool:
        """Inicia el proceso guiado de creación de cita - BILINGÜE"""
        try:
            # Detectar idioma actual
            current_lang = self.processor.language_manager.current_lang
            
            # Inicializar estado del usuario
            self.user_states[user_id] = "waiting_for_title"
            self.pending_citas[user_id] = {'language': current_lang}
            
            # Mensaje inicial según idioma
            if current_lang == 'es':
                chat_window.add_message(
                    "📅 Nueva Cita\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Introduzca el tema o asunto de la cita:\n\n"
                    "💡 Ejemplos: médico, reunión, dentista, compras", 
                    is_user=False
                )
            else:  # English
                chat_window.add_message(
                    "📅 New Appointment\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Enter the subject or topic of the appointment:\n\n"
                    "💡 Examples: doctor, meeting, dentist, shopping", 
                    is_user=False
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting guided cita creation: {str(e)}")
            error_msg = "❌ Error iniciando proceso de cita" if current_lang == 'es' else "❌ Error starting appointment process"
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _handle_conversational_state(self, text: str, chat_window, user_id: str) -> bool:
        """Maneja el flujo conversacional paso a paso"""
        try:
            current_state = self.user_states.get(user_id)
            
            if current_state == "waiting_for_title":
                return self._handle_title_input(text, chat_window, user_id)
            elif current_state == "waiting_for_date":
                return self._handle_date_input(text, chat_window, user_id)
            elif current_state == "waiting_for_time":
                return self._handle_time_input(text, chat_window, user_id)
            else:
                # Estado desconocido - limpiar y reiniciar
                self._clear_user_state(user_id)
                chat_window.add_message("❌ Proceso cancelado. Escriba 'cita' para empezar de nuevo.", is_user=False)
                return True
                
        except Exception as e:
            logger.error(f"Error in conversational state: {str(e)}")
            self._clear_user_state(user_id)
            chat_window.add_message("❌ Error en proceso. Escriba 'cita' para empezar de nuevo.", is_user=False)
            return True
    
    def _handle_title_input(self, text: str, chat_window, user_id: str) -> bool:
        """Maneja la entrada del título/tema de la cita - BILINGÜE"""
        try:
            text = text.strip()
            user_lang = self.pending_citas[user_id].get('language', 'es')
            
            # Validar entrada
            if not text or len(text) < 2:
                if user_lang == 'es':
                    chat_window.add_message(
                        "❌ Por favor, introduzca un tema válido.\n"
                        "💡 Ejemplos: médico, reunión, dentista", 
                        is_user=False
                    )
                else:  # English
                    chat_window.add_message(
                        "❌ Please enter a valid topic.\n"
                        "💡 Examples: doctor, meeting, dentist", 
                        is_user=False
                    )
                return True
            
            # Guardar título
            self.pending_citas[user_id]['title'] = text
            self.user_states[user_id] = "waiting_for_date"
            
            # Solicitar fecha según idioma
            if user_lang == 'es':
                chat_window.add_message(
                    f"📅 Cita: {text}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Introduzca la fecha:\n\n"
                    "💡 Formatos válidos:\n"
                    "• hoy\n"
                    "• mañana\n"
                    "• 22/02 (día/mes)\n"
                    "• viernes (próximo día)", 
                    is_user=False
                )
            else:  # English
                chat_window.add_message(
                    f"📅 Appointment: {text}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Enter the date:\n\n"
                    "💡 Valid formats:\n"
                    "• today\n"
                    "• tomorrow\n"
                    "• 22/02 (day/month)\n"
                    "• friday (next day)", 
                    is_user=False
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling title input: {str(e)}")
            return True
    
    def _handle_date_input(self, text: str, chat_window, user_id: str) -> bool:
        """Maneja la entrada de la fecha"""
        try:
            text = text.strip().lower()
            
            # Parsear fecha usando el sistema existente
            parsed_date = self._parse_date_from_text(text)
            
            if not parsed_date:
                chat_window.add_message(
                    "❌ Fecha no válida.\n"
                    "💡 Use: hoy, mañana, 22/02, viernes", 
                    is_user=False
                )
                return True
            
            # Validar que no sea en el pasado
            if parsed_date < datetime.now().date():
                chat_window.add_message(
                    "❌ No se pueden crear citas en el pasado.\n"
                    "💡 Use una fecha futura.", 
                    is_user=False
                )
                return True
            
            # Guardar fecha
            self.pending_citas[user_id]['date'] = parsed_date
            self.user_states[user_id] = "waiting_for_time"
            
            # Formatear fecha para mostrar
            date_str = self._format_date_display(parsed_date)
            title = self.pending_citas[user_id]['title']
            
            # Solicitar hora
            chat_window.add_message(
                f"📅 Cita: {title} - {date_str}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Introduzca la hora (formato 24h):\n\n"
                "💡 Ejemplos: 12:30, 09:15, 18:45", 
                is_user=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling date input: {str(e)}")
            return True
    
    def _handle_time_input(self, text: str, chat_window, user_id: str) -> bool:
        """Maneja la entrada de la hora y crea la cita"""
        try:
            text = text.strip()
            
            # Validar formato hora
            time_match = re.search(r'(\d{1,2}):(\d{2})', text)
            if not time_match:
                chat_window.add_message(
                    "❌ Formato de hora no válido.\n"
                    "💡 Use formato HH:MM (ej: 12:30, 09:15)", 
                    is_user=False
                )
                return True
            
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Validar hora
            if hour > 23 or minute > 59:
                chat_window.add_message(
                    "❌ Hora no válida.\n"
                    "💡 Use formato 24h (00:00 - 23:59)", 
                    is_user=False
                )
                return True
            
            # Crear datetime completo
            target_date = self.pending_citas[user_id]['date']
            event_time = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Validar que no sea en el pasado
            if event_time < datetime.now():
                chat_window.add_message(
                    "❌ No se pueden crear citas en el pasado.\n"
                    "💡 Use una hora futura.", 
                    is_user=False
                )
                return True
            
            # Crear la cita
            title = self.pending_citas[user_id]['title']
            success = self.calendar_manager.create_event(
                title=title,
                start_time=event_time,
                end_time=event_time,
                category='personal',
                reminder_minutes=15
            )
            
            if success:
                date_str = event_time.strftime('%d/%m/%Y')
                time_str = event_time.strftime('%H:%M')
                
                chat_window.add_message(
                    "✅ Cita creada exitosamente\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📋 Tema: {title}\n"
                    f"📅 Fecha: {date_str}\n"
                    f"🕐 Hora: {time_str}\n"
                    f"⏰ Recordatorio: 15 minutos antes", 
                    is_user=False
                )
                
                # Respuesta por voz
                if self.processor.eva and hasattr(self.processor.eva, 'speech'):
                    voice_msg = f"Cita creada: {title} para el {date_str} a las {time_str}"
                    self.processor.eva.speech.speak(voice_msg)
            else:
                chat_window.add_message("❌ Error creando la cita", is_user=False)
            
            # Limpiar estado del usuario
            self._clear_user_state(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling time input: {str(e)}")
            self._clear_user_state(user_id)
            chat_window.add_message("❌ Error creando cita", is_user=False)
            return True
    
    def _format_date_display(self, date: datetime.date) -> str:
        """Formatea fecha para mostrar de manera amigable"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            if date == today:
                return "hoy"
            elif date == tomorrow:
                return "mañana"
            else:
                return date.strftime('%d/%m/%Y')
                
        except Exception:
            return date.strftime('%d/%m/%Y')
    
    def _clear_user_state(self, user_id: str):
        """Limpia el estado conversacional del usuario"""
        try:
            if user_id in self.user_states:
                del self.user_states[user_id]
            if user_id in self.pending_citas:
                del self.pending_citas[user_id]
        except Exception as e:
            logger.error(f"Error clearing user state: {str(e)}")