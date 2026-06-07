# 📋 **GUÍA COMPLETA DE COMANDOS DE EVA**

## 🎯 **COMANDOS NATIVOS DEL SISTEMA EVA**

Esta documentación incluye **ÚNICAMENTE** los comandos nativos del sistema EVA, sin incluir configuraciones personalizadas específicas del usuario.

---

## 📁 **GESTIÓN DE ARCHIVOS**

### Lista de Archivos
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `lista archivos` | `list files` | Muestra archivos de la carpeta activa numerados del 1 al N |

**Detalles:**
- Ordena según configuración actual (nombre/creación/modificación)
- Muestra hasta 15 archivos numerados
- Recuerda la última carpeta abierta o usa la carpeta activa del explorador

### Ordenamiento de Archivos
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `ordena archivos` | `sort files` | Configura el método de ordenamiento de archivos |

**Opciones disponibles:**
1. Por nombre (alfabético)
2. Por fecha de creación (más reciente primero)
3. Por fecha de modificación (más reciente primero)

**Uso:** Comando → Opciones 1,2,3 → Seleccionar número

### Apertura de Archivos
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `abre archivo [número]` | `open file [number]` | Abre archivo específico por número de la lista |
| `abre [nombre]` | `open [name]` | Abre programa/carpeta/archivo por nombre o coincidencia |

**Ejemplos:**
- `abre archivo 1` - Abre el primer archivo de la lista
- `abre documento` - Busca archivos que contengan "documento"

---

## 🎵 **CONTROL MULTIMEDIA**

### Reproducción
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `pausa` | `pause` | Pausa/reanuda reproducción (toggle) |
| `reproduce` | `play` | Pausa/reanuda reproducción (toggle) |
| `para` | `stop` | Detiene reproducción completamente |

### Navegación
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `siguiente` | `next` | Siguiente pista/video |
| `anterior` | `previous` | Pista/video anterior |

### Control de Pantalla
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `pantalla completa` | `fullscreen` | Activa/desactiva modo pantalla completa |

### Volumen Multimedia
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `sube volumen multimedia` | `volume up multimedia` | Aumenta volumen del reproductor activo |
| `baja volumen multimedia` | `volume down multimedia` | Disminuye volumen del reproductor activo |
| `silencia multimedia` | `mute multimedia` | Silencia/activa reproductor activo |

**Reproductores compatibles:** VLC, MPC-HC, Kodi, reproductores estándar

---

## 🔊 **CONTROL DE VOLUMEN DEL SISTEMA**

### Volumen Básico
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `sube volumen` | `volume up` | Aumenta volumen del sistema |
| `baja volumen` | `volume down` | Disminuye volumen del sistema |
| `silencia` | `mute` | Silencia/activa audio del sistema |

### Volumen Específico
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `volumen [0-100]` | `volume [0-100]` | Establece volumen específico del sistema |

**Ejemplos:**
- `volumen 50` - Establece volumen al 50%
- `volume 0` - Silencia completamente
- `volumen 100` - Volumen máximo

---

## 🖥️ **CONTROL DEL SISTEMA**

### Comandos de Apagado (Requieren Confirmación)
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `apaga` | `shutdown` | Apagar sistema (requiere confirmación) |
| `reinicia` | `restart` | Reiniciar sistema (requiere confirmación) |
| `cierra sesión` | `logout` | Cerrar sesión del usuario (requiere confirmación) |

**Proceso de confirmación:**
1. Usuario dice comando (ej: `apaga`)
2. EVA solicita confirmación
3. Usuario responde `sí`/`yes` para confirmar o `no` para cancelar
4. EVA ejecuta con 5 segundos de espera

### Control de Ventanas
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `cierra ventana` | `close window` | Cierra ventana activa (Alt+F4) |

### Captura de Pantalla
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `captura pantalla` | `screenshot` | Toma captura de pantalla |
| `toma captura` | `take screenshot` | Toma captura de pantalla |

**Variantes adicionales:** `capture screen`

### Salir de EVA
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `salir` | `exit` | Cierra EVA completamente |

---

## 🪟 **CONTROL DE WINDOWS**

### WiFi
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `activa wifi` | `enable wifi` | Activa adaptador WiFi del sistema |
| `desactiva wifi` | `disable wifi` | Desactiva adaptador WiFi del sistema |
| `estado wifi` | `wifi status` | Muestra estado WiFi y red conectada |

### Bluetooth
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `activa bluetooth` | `enable bluetooth` | Activa Bluetooth del sistema |
| `desactiva bluetooth` | `disable bluetooth` | Desactiva Bluetooth del sistema |
| `estado bluetooth` | `bluetooth status` | Muestra estado actual del Bluetooth |

### Brillo (Laptops)
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `sube brillo` | `brightness up` | Aumenta brillo de pantalla |
| `baja brillo` | `brightness down` | Disminuye brillo de pantalla |
| `brillo [0-100]` | `brightness [0-100]` | Establece brillo específico |

**Ejemplos:**
- `brillo 70` - Establece brillo al 70%
- `brightness 50` - Establece brillo al 50%

---

## 🔍 **BÚSQUEDA**

### Búsqueda Web
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `busca [término]` | `search [term]` | Realiza búsqueda en Google |

**Ejemplos:**
- `busca python programming` - Busca "python programming" en Google
- `search weather madrid` - Busca "weather madrid" en Google

---

## 🤖 **IA Y CONVERSACIÓN**

### Conversación con IA
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `eva [pregunta]` | `eva [question]` | Inicia conversación con IA local (Ollama) |

**Ejemplos:**
- `eva explícame qué es Python`
- `eva help me with math problems`
- `eva resume este texto: [contenido]`

### Gestión de Modelos
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `modelo` | `model` | Muestra modelos de IA disponibles y permite cambiar |

**Selección de modelos:**
- Comando `modelo` → Lista opciones → Responder `1`, `2`, o `3`
- También acepta: `uno`, `dos`, `tres` (español) o `one`, `two`, `three` (inglés)

---

## 📄 **ANÁLISIS DE DOCUMENTOS**

### Resumen de Documentos
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `resume [archivo]` | `resume [file]` | Analiza y genera resumen de documentos |

**Formatos soportados:**
- `.pdf` - Documentos PDF
- `.txt` - Archivos de texto plano
- `.md` - Archivos Markdown
- `.csv` - Archivos CSV
- `.json` - Archivos JSON
- `.docx` - Documentos Microsoft Word
- `.odt` - Documentos OpenDocument

**Ejemplos:**
- `resume documento.pdf`
- `resume informe.docx`
- `resume data.csv`

---

## 📅 **GESTIÓN DE CITAS**

### Creación de Citas
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `cita` | `appointment` | Inicia proceso guiado de creación de cita |
| `cita [tema] [fecha] [hora]` | `appointment [topic] [date] [time]` | Crea cita directamente |

### Consulta de Citas
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `citas` | `appointments` | Lista citas de hoy |
| `citas [fecha]` | `appointments [date]` | Lista citas de fecha específica |

### Cancelación de Citas
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `citas cancelar` | `appointments cancel` | Muestra opciones para cancelar citas |
| `citas cancelar [número]` | `appointments cancel [number]` | Cancela cita por número |
| `citas cancelar [nombre]` | `appointments cancel [name]` | Cancela cita por nombre/tema |

**Formatos de fecha soportados:**
- `hoy` / `today`
- `mañana` / `tomorrow`
- `22/02` (día/mes)
- `22 de febrero`
- `viernes` (próximo día de semana)
- `monday`, `tuesday`, etc.

**Formato de hora:** `HH:MM` (24 horas)
- Ejemplos: `12:30`, `09:15`, `18:45`

---

## 🎤 **DICTADO**

### Sistema de Dictado
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `dictado` | `dictation` | Inicia sistema de dictado inteligente |

**Funcionamiento:**
- Convierte voz a texto en tiempo real
- Comando `finalizar dictado` / `finish dictation` para terminar

---

## 📚 **AYUDA Y DOCUMENTACIÓN**

### Ayuda General
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `ayuda` | `help` | Muestra menú principal de ayuda |
| `comandos` | `commands` | Lista completa de comandos disponibles |
| `manual` | `manual` | Manual detallado de EVA |

### Ayuda Específica
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `ayuda [tema]` | `help [topic]` | Ayuda específica sobre un tema |

**Temas disponibles:**
- `volumen` / `volume` - Ayuda sobre control de volumen
- `multimedia` / `music` - Ayuda sobre control multimedia
- `archivos` / `files` - Ayuda sobre gestión de archivos
- `sistema` / `system` - Ayuda sobre control del sistema
- `windows` / `wifi` / `bluetooth` / `brillo` / `brightness`
- `ia` / `ai` / `eva` / `ollama` - Ayuda sobre IA

---

## 🔧 **COMANDOS DE CONFIGURACIÓN**

### Actualizaciones
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `verificar actualizaciones` | `check updates` | Verifica actualizaciones disponibles de EVA |
| `buscar actualizaciones` | `check for updates` | Verifica actualizaciones disponibles de EVA |
| `comprobar actualizaciones` | `update eva` | Verifica actualizaciones disponibles de EVA |

---

## ✅ **COMANDOS DE CONFIRMACIÓN**

### Respuestas de Confirmación
| **Español** | **English** | **Función** |
|-------------|-------------|-------------|
| `sí` | `yes` | Confirma acción pendiente |
| `si` | `y` | Confirma acción pendiente |
| `no` | `no` | Cancela acción pendiente |
| `cancelar` | `cancel` | Cancela acción pendiente |
| - | `n` | Cancela acción pendiente |

---

## 🔢 **COMANDOS NUMÉRICOS**

### Selección por Número
| **Comando** | **Función** |
|-------------|-------------|
| `1`, `2`, `3` | Selección de modelo de IA |
| `uno`, `dos`, `tres` | Selección de modelo de IA (español) |
| `one`, `two`, `three` | Selección de modelo de IA (inglés) |
| `primero`, `segundo`, `tercero` | Selección de modelo de IA (español ordinal) |
| `first`, `second`, `third` | Selección de modelo de IA (inglés ordinal) |

### Ordenamiento de Archivos
| **Comando** | **Función** |
|-------------|-------------|
| `1` | Ordenar por nombre (alfabético) |
| `2` | Ordenar por fecha de creación |
| `3` | Ordenar por fecha de modificación |

---

## ⌨️ **ATAJOS DE TECLADO NATIVOS**

### Atajos del Sistema
| **Combinación** | **Función** |
|-----------------|-------------|
| `Ctrl+Alt+E` | Activar/Mostrar EVA |
| `Ctrl+Alt+C` | Mostrar ventana de chat |
| `Ctrl+Alt+H` | Ocultar ventana de chat |
| `Ctrl+Alt+Q` | Salir de EVA |

**Nota:** Los usuarios pueden configurar atajos adicionales a través del panel de configuración.

---

## 🎯 **COMANDOS PERSONALIZABLES**

EVA permite a los usuarios configurar comandos personalizados a través del **Panel de Configuración**:

### 🌐 **Sitios Web Personalizados**
- **Función:** `abre [nombre_sitio]`
- **Configuración:** Panel → Comandos Personalizados → Sitios Web
- **Ejemplo:** Usuario configura "youtube" → `abre youtube`

### 📂 **Carpetas Personalizadas**
- **Función:** `abre [nombre_carpeta]`
- **Configuración:** Panel → Comandos Personalizados → Carpetas
- **Ejemplo:** Usuario configura "documentos" → `abre documentos`

### 💻 **Programas Personalizados**
- **Función:** `abre [nombre_programa]`
- **Configuración:** Panel → Comandos Personalizados → Programas
- **Ejemplo:** Usuario configura "notepad" → `abre notepad`

### ⚡ **Atajos Personalizados**
- **Función:** `[nombre_atajo]`
- **Configuración:** Panel → Base de Conocimiento → Atajos Personalizados
- **Ejemplo:** Usuario configura "trabajo" → Ejecuta múltiples comandos

### 🎹 **Hotkeys Personalizados**
- **Función:** Combinaciones de teclas personalizadas
- **Configuración:** Panel → Comandos Personalizados → Atajos de Teclado
- **Ejemplo:** Usuario configura `Ctrl+Alt+N` → Acción específica

---

## 🔄 **VARIANTES DE PRONUNCIACIÓN**

EVA incluye un sistema de variantes para mejorar el reconocimiento de voz:

### Variantes Configurables
Los usuarios pueden añadir variantes de pronunciación en el panel de configuración para mejorar el reconocimiento de comandos personalizados.

**Ejemplo de configuración:**
- Comando: "google"
- Variantes: "guguel", "gugle", "gogel"

---

## 🎛️ **FILOSOFÍA DE COMANDOS DE EVA**

### Principios de Diseño
1. **1 Comando = 1 Función:** Cada comando tiene una función específica y única
2. **Comandos Exactos:** Los comandos deben pronunciarse exactamente como están definidos
3. **Bilingüe Nativo:** Todos los comandos funcionan en español e inglés
4. **Confirmación de Seguridad:** Comandos peligrosos requieren confirmación explícita
5. **Contexto Inteligente:** EVA recuerda configuraciones y carpetas activas

### Ejemplos de Precisión
- ✅ `apaga` - Funciona
- ❌ `apagar` - NO funciona
- ✅ `shutdown` - Funciona
- ❌ `shut down` - NO funciona

### Sistema de Confirmación
Para comandos críticos del sistema:
1. Usuario dice comando peligroso
2. EVA solicita confirmación
3. Usuario confirma con `sí`/`yes` o cancela con `no`
4. EVA ejecuta con tiempo de espera de seguridad

---

## 💡 **CONSEJOS DE USO**

### Mejores Prácticas
1. **Usa comandos exactos** - EVA es preciso con la sintaxis
2. **Aprovecha el bilingüismo** - Cambia entre español e inglés libremente
3. **Configura comandos personalizados** - Adapta EVA a tu flujo de trabajo
4. **Usa la ayuda contextual** - `ayuda [tema]` para información específica
5. **Aprovecha el contexto** - EVA recuerda tu última carpeta y configuraciones

### Solución de Problemas
- Si un comando no funciona, verifica la sintaxis exacta
- Usa `comandos` para ver la lista completa
- Usa `ayuda [tema]` para ayuda específica sobre un área
- Verifica que Ollama esté instalado para funciones de IA

---

## 📊 **RESUMEN ESTADÍSTICO**

### Comandos Nativos Totales
- **Gestión de Archivos:** 4 comandos principales
- **Control Multimedia:** 8 comandos
- **Control de Volumen:** 4 comandos
- **Control del Sistema:** 6 comandos
- **Control de Windows:** 9 comandos
- **Búsqueda:** 1 comando
- **IA y Conversación:** 2 comandos principales
- **Análisis de Documentos:** 1 comando (múltiples formatos)
- **Gestión de Citas:** 6 comandos principales
- **Dictado:** 1 comando
- **Ayuda:** 4 comandos principales
- **Configuración:** 3 comandos
- **Confirmación:** 5 respuestas
- **Numéricos:** 12 variantes
- **Atajos de Teclado:** 4 nativos

**Total: 70+ comandos nativos únicos** con soporte bilingüe completo y capacidades de personalización extensas.

---

## 🔗 **INTEGRACIÓN Y COMPATIBILIDAD**

### Sistemas Operativos
- **Windows 11** (Nativo)
- **Windows 10** (Compatible)

### Software Compatible
- **Ollama** (IA local)
- **VLC Media Player** (Control multimedia)
- **MPC-HC** (Control multimedia)
- **Kodi** (Control multimedia)
- **Navegadores web** (Búsquedas y sitios)
- **Exploradores de archivos** (Gestión de archivos)

### Requisitos
- **Ollama instalado** (para funciones de IA)
- **Micrófono** (para comandos de voz)
- **Altavoces/Auriculares** (para respuestas TTS)
- **Conexión a internet** (para búsquedas web y actualizaciones)

---

*Documento generado automáticamente basado en el análisis completo del código fuente de EVA*
*Versión: 2.0 | Fecha: 2025*