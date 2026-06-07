# ============================================================
# ollama_integration.py — VERS'+'IÓN LIBRE (sin restricciones)
# - Sistema premium eliminado completamente.
# - Selecci'+'ón de modelo din'+'ámica via `ollama list`.
# - Sin l'+'ímite de modelos: se muestran todos los instalados.
# ============================================================
import logging
import subprocess
import os
import json
import time
import threading

try:
    from core.error_handler import handle_ollama_error, handle_memory_error
except ImportError:
    def handle_ollama_error(error, context):
        return {"action": "log_only"}
    def handle_memory_error(error, context):
        return {"action": "log_only"}

OLLAMA_API_TIMEOUT = 180
OLLAMA_LIST_TIMEOUT = 15
MODEL_CACHE_TTL = 60

logger = logging.getLogger("EVA")


def safe_import_cache():
    """Importa el cache de forma segura."""
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.smart_cache import ollama_cache
        return ollama_cache
    except ImportError:
        logger.debug("Cache no disponible")
        return None


class OllamaIntegration:
    def __init__(self, config):
        self.config = config["ollama"]
        self.main_config = config
        from core.dynamic_path_resolver import dynamic_path_resolver
        self.base_dir = dynamic_path_resolver.get_path('base')
        self.models_dir = dynamic_path_resolver.get_path('models', 'ollama', 'models')

        import shutil
        ollama_exe = shutil.which("ollama")
        if not ollama_exe:
            ollama_exe = dynamic_path_resolver.get_path('ollama')
        if not ollama_exe or not os.path.exists(ollama_exe):
            raise RuntimeError("Ollama no esta disponible en el sistema")
        self.ollama_path = ollama_exe
        self.env = os.environ.copy()
        self.env["OLLAMA_HOST"] = "127.0.0.1:11434"
        self.env["OLLAMA_ORIGINS"] = "*"
        self.session_active = False
        self.last_activity = time.time()
        self.session_timeout = 300
        self.model = self.config.get("model", "qwen3:4b")
        self.current_model = self.model
        self._cached_installed_models = []
        self._cached_models_ts = 0
        self._default_personality = {
            "name": {"es": "EVA", "en": "EVA"},
            "system_prompt": {
                "es": "Eres EVA, un asistente personal. Responde de forma natural y directa.",
                "en": "You are EVA, a personal assistant. Respond naturally and directly.",
            },
            "temperature": 0.7,
            "max_tokens": 300,
        }
        self.model_personalities = {}
        self._clear_ollama_cache()
        self.monitoring_thread = threading.Thread(target=self._monitor_session, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"OllamaIntegration iniciado - modelo activo: {self.model}")
    def _get_current_language(self):
        try:
            lang = self.main_config.get("language", "es")
            return lang if lang in ("es", "en") else "es"
        except Exception:
            return "es"

    def _detect_question_language(self, question):
        try:
            q = question.lower().strip()
            en_words = {"who","what","how","when","where","why","are","is","can","do","does","will",
                        "would","could","should","you","good","bad","hello","hi","thanks","thank","please"}
            es_words = {"quien","que","como","cuando","donde","por","eres","es","puedes","hola",
                        "gracias","favor","ayuda","dime","explica","describe","bien","mal","bueno","malo"}
            words = set(q.split())
            en_sc = len(words & en_words)
            es_sc = len(words & es_words)
            es_sc += sum(q.count(c) for c in "naeiouu") * 0  # placeholder
            es_sc += q.count("n~") + q.count("a'") + q.count("e'") + q.count("i'") + q.count("o'") + q.count("u'")
            if en_sc > es_sc:
                return "en"
            elif es_sc > en_sc:
                return "es"
            return self._get_current_language()
        except Exception:
            return self._get_current_language()

    # ------------------------------------------------------------------
    # MODELOS INSTALADOS - `ollama list` dinamico
    # ------------------------------------------------------------------

    def get_installed_models(self, force_refresh=False):
        """
        Ejecuta `ollama list` y devuelve lista de nombres de modelos instalados.
        Cache de 60 segundos para evitar llamadas excesivas.
        """
        now = time.time()
        if not force_refresh and self._cached_installed_models and (now - self._cached_models_ts) < MODEL_CACHE_TTL:
            return self._cached_installed_models

        try:
            result = subprocess.run(
                [self.ollama_path, "list"],
                capture_output=True, text=True, timeout=OLLAMA_LIST_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            models = []
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                for line in lines[1:]:  # Saltar cabecera NAME ID SIZE MODIFIED
                    parts = line.split()
                    if parts:
                        name = parts[0].strip()
                        if name:
                            models.append(name)
            if models:
                self._cached_installed_models = models
                self._cached_models_ts = now
                logger.info(f"Modelos instalados: {models}")
            else:
                logger.warning("ollama list no devolvio modelos")
                if not self._cached_installed_models:
                    self._cached_installed_models = [self.model]
        except subprocess.TimeoutExpired:
            logger.error("Timeout en `ollama list`")
            if not self._cached_installed_models:
                self._cached_installed_models = [self.model]
        except Exception as e:
            logger.error(f"Error en `ollama list`: {e}")
            if not self._cached_installed_models:
                self._cached_installed_models = [self.model]

        return self._cached_installed_models

    @property
    def available_models(self):
        """Dict {"1": "modelo1", "2": "modelo2", ...} construido dinamicamente."""
        models = self.get_installed_models()
        return {str(i + 1): name for i, name in enumerate(models)}

    def list_models(self):
        """
        Devuelve lista numerada de todos los modelos instalados (ollama list).
        Sin limite ni restricciones de ningun tipo.
        """
        models = self.get_installed_models(force_refresh=True)
        if not models:
            return "No se encontraron modelos. Ejecuta `ollama pull <modelo>` para instalar uno."
        lines = ["Modelos disponibles:\n"]
        for i, name in enumerate(models, start=1):
            marker = " (activo)" if name == self.current_model else ""
            lines.append(f"  {i}. {name}{marker}")
        lines.append("\nEscribe el numero para seleccionar el modelo.")
        return "\n".join(lines)

    def change_model(self, selection):
        """
        Cambia el modelo activo.
        selection puede ser un numero ("1","2",...) o un nombre ("qwen3:4b").
        Persiste el cambio en paths.json.
        """
        lang = self._get_current_language()
        models = self.get_installed_models()
        new_model = None

        # Intentar como numero
        try:
            idx = int(str(selection).strip()) - 1
            if 0 <= idx < len(models):
                new_model = models[idx]
        except ValueError:
            pass

        # Intentar como nombre
        if new_model is None:
            sel = str(selection).strip().lower()
            for m in models:
                if m.lower() == sel or m.lower().startswith(sel):
                    new_model = m
                    break

        if new_model is None:
            total = len(models)
            if lang == "es":
                return f"Seleccion no valida. Elige un numero del 1 al {total}."
            return f"Invalid selection. Choose a number from 1 to {total}."

        self.model = new_model
        self.current_model = new_model
        self.config["model"] = new_model
        self._save_model_to_config(new_model)
        logger.info(f"Modelo cambiado a: {new_model}")
        if lang == "es":
            return f"Modelo cambiado a: {new_model}"
        return f"Model changed to: {new_model}"

    def _save_model_to_config(self, model_name):
        """Persiste el modelo elegido en config/paths.json."""
        config_path = os.path.join(self.base_dir, "config", "paths.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if "ollama" not in cfg:
                    cfg["ollama"] = {}
                cfg["ollama"]["model"] = model_name
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4, ensure_ascii=False)
                logger.info(f"Modelo '{model_name}' guardado en paths.json")
        except Exception as e:
            logger.error(f"Error guardando modelo en config: {e}")

    # ------------------------------------------------------------------
    # Personalidad
    # ------------------------------------------------------------------

    def _get_personality(self, model_name):
        return self.model_personalities.get(model_name, self._default_personality)

    def get_current_personality(self):
        p = self._get_personality(self.model)
        return {"model": self.model, "name": p.get("name", "EVA"),
                "temperature": p.get("temperature", 0.7), "max_tokens": p.get("max_tokens", 300)}

    def customize_personality(self, model_name, custom_prompt=None, temperature=None, max_tokens=None):
        if model_name not in self.model_personalities:
            import copy
            self.model_personalities[model_name] = copy.deepcopy(self._default_personality)
        if custom_prompt:
            self.model_personalities[model_name]["system_prompt"] = custom_prompt
        if temperature is not None:
            self.model_personalities[model_name]["temperature"] = temperature
        if max_tokens is not None:
            self.model_personalities[model_name]["max_tokens"] = max_tokens
        return f"Personalidad de {model_name} actualizada"

    # ------------------------------------------------------------------
    # Ejecucion de consultas
    # ------------------------------------------------------------------

    def _ensure_models_dir(self):
        logger.debug(f"Directorio de modelos: {self.models_dir}")

    def _clear_ollama_cache(self):
        try:
            cache = safe_import_cache()
            if cache and hasattr(cache, "_memory_cache"):
                keys = list(cache._memory_cache.keys())
                for k in keys:
                    try:
                        del cache._memory_cache[k]
                    except Exception:
                        pass
                logger.info(f"Cache limpiado: {len(keys)} entradas")
        except Exception as e:
            logger.debug(f"Error limpiando cache: {e}")

    def _cleanup_session(self):
        try:
            self.session_active = False
        except Exception as e:
            logger.debug(f"Error limpiando sesion: {e}")

    def _monitor_session(self):
        while True:
            try:
                time.sleep(30)
                if self.session_active and (time.time() - self.last_activity) > self.session_timeout:
                    logger.info("Sesion Ollama inactiva - limpiando")
                    self._cleanup_session()
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                time.sleep(60)

    def _ensure_ollama_server(self):
        try:
            import requests
            try:
                r = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
                if r.status_code == 200:
                    return
            except Exception:
                pass
            logger.info("Iniciando servidor Ollama...")
            subprocess.Popen([self.ollama_path, "serve"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            for _ in range(10):
                time.sleep(1)
                try:
                    r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1)
                    if r.status_code == 200:
                        logger.info("Servidor Ollama iniciado")
                        return
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error iniciando Ollama: {e}")

    def _get_num_predict(self, model=None):
        """
        Devuelve el número de tokens a generar según el modelo.
        Los modelos con thinking (qwen3, deepseek-r1, etc.) necesitan
        muchos más tokens porque generan primero el bloque <think>
        y luego la respuesta final.
        """
        if model is None:
            model = self.current_model
        model_lower = (model or "").lower()
        # Modelos conocidos con razonamiento interno (<think>)
        thinking_models = ["qwen3", "deepseek-r1", "qwq", "marco-o1", "skywork-o1"]
        # nothink = versión sin thinking, usar tokens normales
        nothink_keywords = ["nothink", "no-think", "nothin"]
        is_nothink = any(kw in model_lower for kw in nothink_keywords)
        is_thinking = any(kw in model_lower for kw in thinking_models) and not is_nothink
        if is_thinking:
            # 4096 tokens: suficiente para el bloque <think> + respuesta final
            logger.debug(f"Modelo thinking detectado ({model}): num_predict=4096")
            return 4096
        # Modelos normales: 1024 tokens (más que los 300 anteriores, sin pasarse)
        return 1024

    def _execute_ollama(self, prompt, model=None):
        try:
            self.last_activity = time.time()
            self.session_active = True
            self._ensure_ollama_server()
            if not model:
                model = self.current_model
            import requests
            p = self._get_personality(model)
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": p.get("temperature", 0.7), "num_predict": self._get_num_predict(model)},
            }
            response = requests.post("http://127.0.0.1:11434/api/generate", json=data, timeout=OLLAMA_API_TIMEOUT)
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                if text.startswith("[EVA]:"):
                    text = text[6:].strip()
                return text
            logger.error(f"Ollama API error {response.status_code}")
            return "Error procesando la consulta con Ollama"
        except Exception as e:
            logger.error(f"Error ejecutando Ollama: {e}")
            return f"Error: {e}"

    def process_query(self, text, chat_window):
        try:
            lang = self._get_current_language()
            p = self._get_personality(self.current_model)
            sys_prompt = p.get("system_prompt", {})
            if isinstance(sys_prompt, dict):
                sys_prompt = sys_prompt.get(lang, "")
            full_prompt = f"{sys_prompt}\n\nUsuario: {text}\nEVA:" if sys_prompt else text
            response = self._execute_ollama(full_prompt, self.current_model)
            msg = response if response and response.strip() else "No pude generar respuesta."
            chat_window.add_message(msg, is_user=False)
        except Exception as e:
            logger.error(f"Error en process_query: {e}")
            chat_window.add_message(f"Error: {e}", is_user=False)

    def process_conversation(self, question):
        try:
            lang = self._detect_question_language(question)
            p = self._get_personality(self.model)
            sys_prompt = p.get("system_prompt", {})
            if isinstance(sys_prompt, dict):
                sys_prompt = sys_prompt.get(lang, "")
            user_label = "Usuario" if lang == "es" else "User"
            asst_label = "Asistente" if lang == "es" else "Assistant"
            full_prompt = f"{sys_prompt}\n\n{user_label}: {question}\n{asst_label}:" if sys_prompt else question

            import hashlib
            cache_key = hashlib.md5(f"{self.model}:{sys_prompt}:{lang}:{question}".encode()).hexdigest()
            try:
                cache = safe_import_cache()
                if cache:
                    cached = cache.get(cache_key)
                    if cached:
                        self.last_activity = time.time()
                        self.session_active = True
                        return cached
            except Exception:
                pass

            response = self._execute_ollama(full_prompt, self.model)
            if response and "Error" not in response:
                try:
                    cache = safe_import_cache()
                    if cache:
                        cache.set(cache_key, response, ttl=3600.0)
                except Exception:
                    pass
            return response
        except Exception as e:
            handle_ollama_error(e, "Procesamiento de conversacion")
            return f"Error procesando conversacion: {e}"

    def download_model(self, model_name):
        try:
            result = subprocess.run([self.ollama_path, "pull", model_name],
                capture_output=True, text=True, timeout=600,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if result.returncode == 0:
                self._cached_installed_models = []
                return f"Modelo {model_name} descargado"
            return f"Error descargando {model_name}: {result.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def list_available_models(self):
        try:
            result = subprocess.run([self.ollama_path, "list"],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def unload_model(self):
        try:
            self._cleanup_session()
        except Exception as e:
            logger.error(f"Error liberando modelo: {e}")

    def cleanup(self):
        try:
            self._cleanup_session()
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")

    def _cleanup_after_ollama(self):
        try:
            self.unload_model()
            # VRAM: delegado a Ollama
        except Exception as e:
            handle_memory_error(e, "Limpieza despues de Ollama")
