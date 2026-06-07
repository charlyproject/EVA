import os
import sqlite3
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger("EVA")

class CalendarManager:
    def __init__(self, config, language_manager):
        self.config = config
        self.language_manager = language_manager
        self.eva = None  # Se establecerá después de la inyección
        
        # Configurar rutas
        data_dir = config.get("paths", {}).get("data", os.path.join(os.getenv('APPDATA'), 'EVA', 'data'))
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "calendar.db")
        
        # Cache para optimización
        self._today_cache = None
        self._cache_date = None
        self._cache_timestamp = 0
        self._cache_timeout = 300  # 5 minutos
        
        # Inicializar base de datos
        self.init_db()
        
        # Iniciar hilo de notificaciones
        self.notification_thread = threading.Thread(target=self._notification_loop, daemon=True)
        self.notification_thread.start()
        
        # Iniciar hilo de limpieza
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def init_db(self):
        """Inicializa la base de datos del calendario"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Tabla principal de eventos
            c.execute('''CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                category TEXT DEFAULT 'personal',
                recurrence_rule TEXT,
                reminder_minutes INTEGER DEFAULT 15,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT FALSE,
                is_cancelled BOOLEAN DEFAULT FALSE
            )''')
            
            # Tabla de notificaciones
            c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                notification_time DATETIME NOT NULL,
                is_sent BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
            )''')
            
            # Índices para optimización
            c.execute('CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_events_category ON events(category)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(date(start_time))')
            c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_time ON notifications(notification_time, is_sent)')
            
            conn.commit()
            conn.close()
            logger.info("Calendar database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing calendar database: {str(e)}")

    def create_event(self, title: str, start_time: datetime, end_time: datetime = None, 
                    category: str = 'personal', description: str = '', location: str = '',
                    reminder_minutes: int = 15, recurrence_rule: str = None) -> bool:
        """Crea un nuevo evento en el calendario"""
        try:
            if end_time is None:
                end_time = start_time
                
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Insertar evento
            c.execute('''INSERT INTO events 
                        (title, description, start_time, end_time, category, 
                         reminder_minutes, location, recurrence_rule)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, description, start_time.isoformat(), end_time.isoformat(),
                      category, reminder_minutes, location, recurrence_rule))
            
            event_id = c.lastrowid
            
            # Crear notificación si se requiere
            if reminder_minutes > 0:
                notification_time = start_time - timedelta(minutes=reminder_minutes)
                if notification_time > datetime.now():
                    c.execute('''INSERT INTO notifications (event_id, notification_time)
                                VALUES (?, ?)''', (event_id, notification_time.isoformat()))
            
            conn.commit()
            conn.close()
            
            # Limpiar cache
            self._clear_cache()
            
            logger.info(f"Event created: {title} at {start_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return False

    def get_events_for_date(self, target_date: datetime.date) -> List[Dict]:
        """Obtiene eventos para una fecha específica"""
        try:
            # Verificar cache para hoy
            if target_date == datetime.now().date():
                cached_events = self._get_cached_today_events()
                if cached_events is not None:
                    return cached_events
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute('''SELECT * FROM events 
                        WHERE date(start_time) = ? 
                        AND is_cancelled = FALSE
                        ORDER BY start_time''', (target_date.isoformat(),))
            
            events = []
            for row in c.fetchall():
                event = dict(row)
                event['start_time'] = datetime.fromisoformat(event['start_time'])
                if event['end_time']:
                    event['end_time'] = datetime.fromisoformat(event['end_time'])
                events.append(event)
            
            conn.close()
            
            # Actualizar cache si es para hoy
            if target_date == datetime.now().date():
                self._update_today_cache(events)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events for date {target_date}: {str(e)}")
            return []

    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Obtiene eventos próximos en los siguientes N días"""
        try:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute('''SELECT * FROM events 
                        WHERE start_time BETWEEN ? AND ?
                        AND is_cancelled = FALSE
                        ORDER BY start_time''', 
                     (start_date.isoformat(), end_date.isoformat()))
            
            events = []
            for row in c.fetchall():
                event = dict(row)
                event['start_time'] = datetime.fromisoformat(event['start_time'])
                if event['end_time']:
                    event['end_time'] = datetime.fromisoformat(event['end_time'])
                events.append(event)
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []

    def update_event(self, event_id: int, **kwargs) -> bool:
        """Actualiza un evento existente"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Construir query dinámicamente
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['title', 'description', 'category', 'location', 'reminder_minutes']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
                elif field in ['start_time', 'end_time'] and isinstance(value, datetime):
                    update_fields.append(f"{field} = ?")
                    values.append(value.isoformat())
            
            if not update_fields:
                return False
                
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(event_id)
            
            query = f"UPDATE events SET {', '.join(update_fields)} WHERE id = ?"
            c.execute(query, values)
            
            conn.commit()
            conn.close()
            
            # Limpiar cache
            self._clear_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating event {event_id}: {str(e)}")
            return False

    def cancel_event(self, event_id: int) -> bool:
        """Cancela un evento"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''UPDATE events SET is_cancelled = TRUE, updated_at = ?
                        WHERE id = ?''', (datetime.now().isoformat(), event_id))
            
            # Cancelar notificaciones pendientes
            c.execute('''UPDATE notifications SET is_sent = TRUE
                        WHERE event_id = ? AND is_sent = FALSE''', (event_id,))
            
            conn.commit()
            conn.close()
            
            # Limpiar cache
            self._clear_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling event {event_id}: {str(e)}")
            return False

    def find_events_by_title(self, title_pattern: str) -> List[Dict]:
        """Busca eventos por título (búsqueda fuzzy)"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Búsqueda con LIKE para coincidencias parciales
            c.execute('''SELECT * FROM events 
                        WHERE title LIKE ? 
                        AND is_cancelled = FALSE
                        AND start_time >= datetime('now', '-1 day')
                        ORDER BY start_time''', 
                     (f'%{title_pattern}%',))
            
            events = []
            for row in c.fetchall():
                event = dict(row)
                event['start_time'] = datetime.fromisoformat(event['start_time'])
                if event['end_time']:
                    event['end_time'] = datetime.fromisoformat(event['end_time'])
                events.append(event)
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error finding events by title '{title_pattern}': {str(e)}")
            return []

    def check_conflicts(self, start_time: datetime, end_time: datetime, exclude_event_id: int = None) -> List[Dict]:
        """Verifica conflictos de horario"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = '''SELECT * FROM events 
                      WHERE is_cancelled = FALSE
                      AND ((start_time <= ? AND end_time > ?) OR 
                           (start_time < ? AND end_time >= ?) OR
                           (start_time >= ? AND end_time <= ?))'''
            params = [start_time.isoformat(), start_time.isoformat(),
                     end_time.isoformat(), end_time.isoformat(),
                     start_time.isoformat(), end_time.isoformat()]
            
            if exclude_event_id:
                query += ' AND id != ?'
                params.append(exclude_event_id)
                
            c.execute(query, params)
            
            conflicts = []
            for row in c.fetchall():
                event = dict(row)
                event['start_time'] = datetime.fromisoformat(event['start_time'])
                if event['end_time']:
                    event['end_time'] = datetime.fromisoformat(event['end_time'])
                conflicts.append(event)
            
            conn.close()
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {str(e)}")
            return []

    def _get_cached_today_events(self) -> Optional[List[Dict]]:
        """Obtiene eventos de hoy desde cache si está válido"""
        current_time = time.time()
        today = datetime.now().date()
        
        if (self._today_cache is not None and 
            self._cache_date == today and 
            current_time - self._cache_timestamp < self._cache_timeout):
            return self._today_cache
        return None

    def _update_today_cache(self, events: List[Dict]):
        """Actualiza el cache de eventos de hoy"""
        self._today_cache = events
        self._cache_date = datetime.now().date()
        self._cache_timestamp = time.time()

    def _clear_cache(self):
        """Limpia el cache"""
        self._today_cache = None
        self._cache_date = None
        self._cache_timestamp = 0

    def _notification_loop(self):
        """Hilo para verificar y enviar notificaciones"""
        while True:
            try:
                self._check_pending_notifications()
                time.sleep(30)  # Verificar cada 30 segundos
            except Exception as e:
                logger.error(f"Error in notification loop: {str(e)}")
                time.sleep(60)

    def _check_pending_notifications(self):
        """Verifica y envía notificaciones pendientes"""
        try:
            now = datetime.now()
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Obtener notificaciones pendientes
            c.execute('''SELECT n.id, n.event_id, n.notification_time, e.title, e.start_time
                        FROM notifications n
                        JOIN events e ON n.event_id = e.id
                        WHERE n.is_sent = FALSE 
                        AND n.notification_time <= ?
                        AND e.is_cancelled = FALSE''', (now.isoformat(),))
            
            for row in c.fetchall():
                notification_id = row['id']
                event_title = row['title']
                event_time = datetime.fromisoformat(row['start_time'])
                
                # Calcular minutos hasta el evento
                minutes_until = int((event_time - now).total_seconds() / 60)
                
                # Enviar notificación
                if self.eva and hasattr(self.eva, 'speech'):
                    reminder_text = self.language_manager.get_text("calendar.event_reminder").format(
                        title=event_title,
                        minutes=max(0, minutes_until)
                    )
                    self.eva.speech.speak(reminder_text)
                
                if self.eva and hasattr(self.eva, 'chat_window'):
                    self.eva.chat_window.add_message(f"⏰ {reminder_text}", is_user=False)
                
                # Marcar como enviada
                c.execute('UPDATE notifications SET is_sent = TRUE WHERE id = ?', (notification_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking notifications: {str(e)}")

    def _cleanup_loop(self):
        """Hilo para limpieza de datos antiguos"""
        while True:
            try:
                # Limpiar eventos completados de hace más de 30 días
                cutoff_date = datetime.now() - timedelta(days=30)
                self._cleanup_old_events(cutoff_date)
                time.sleep(86400)  # Una vez al día
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                time.sleep(3600)

    def _cleanup_old_events(self, cutoff_date: datetime):
        """Limpia eventos antiguos completados"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Eliminar eventos completados antiguos
            c.execute('''DELETE FROM events 
                        WHERE is_completed = TRUE 
                        AND end_time < ?''', (cutoff_date.isoformat(),))
            
            # Eliminar notificaciones enviadas antiguas
            c.execute('''DELETE FROM notifications 
                        WHERE is_sent = TRUE 
                        AND notification_time < ?''', (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up old events before {cutoff_date}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old events: {str(e)}")

    def get_stats(self) -> Dict:
        """Obtiene estadísticas del calendario"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Total de eventos
            c.execute('SELECT COUNT(*) FROM events WHERE is_cancelled = FALSE')
            total_events = c.fetchone()[0]
            
            # Eventos de hoy
            today = datetime.now().date()
            c.execute('SELECT COUNT(*) FROM events WHERE date(start_time) = ? AND is_cancelled = FALSE', 
                     (today.isoformat(),))
            today_events = c.fetchone()[0]
            
            # Eventos próximos (7 días)
            next_week = datetime.now() + timedelta(days=7)
            c.execute('SELECT COUNT(*) FROM events WHERE start_time BETWEEN ? AND ? AND is_cancelled = FALSE',
                     (datetime.now().isoformat(), next_week.isoformat()))
            upcoming_events = c.fetchone()[0]
            
            conn.close()
            
            return {
                'total_events': total_events,
                'today_events': today_events,
                'upcoming_events': upcoming_events
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar stats: {str(e)}")
            return {'total_events': 0, 'today_events': 0, 'upcoming_events': 0}