__version__ = "0.3.0"
"""IRA NED: asistente con chat y salida de voz experimental.
Para Android con Kivy (proyecto de APK).
Para dictar: tocar la caja de texto, microfono del teclado y tecla Enter.
La voz hablada utiliza Android TextToSpeech si Android dispone de un motor de voz.
NO usa el microfono directamente ni pide permisos sobre archivos del telefono.
"""
import re
import random
import unicodedata
import math
import wave
import struct
import tempfile
import os
from kivy.core.audio import SoundLoader
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

Window.clearcolor = (0.025, 0.035, 0.075, 1)
Window.softinput_mode = "pan"
CYAN = (0.20, 0.75, 1, 1)
BLANCO = (0.94, 0.98, 1, 1)
BOT = (0.07, 0.14, 0.26, 1)
TU = (0.03, 0.29, 0.47, 1)


def responder(mensaje, memoria=None):
    """Conversacion basica sin internet. Memoria solo durante esta sesion."""
    memoria = memoria if memoria is not None else {}
    texto = "".join(
        letra for letra in unicodedata.normalize("NFD", mensaje.strip().casefold())
        if unicodedata.category(letra) != "Mn"
    )
    texto = re.sub(r"\s+", " ", texto)
    if not texto:
        return "No te he escuchado bien. ¿Puedes repetirlo?"

    # Antes que nada, responde con prudencia ante situaciones importantes.
    alarma = ("me quiero morir", "quiero hacerme dano", "me voy a hacer dano",
              "me estan haciendo dano", "estoy en peligro")
    if any(frase in texto for frase in alarma):
        return ("Eso es importante. Busca ahora a un adulto de confianza y cuentale "
                "lo que ocurre. Si hay peligro inmediato, llama al 112.")

    if texto in ("terminar juego", "salir del juego", "cancelar juego", "parar juego"):
        memoria.pop("numero_secreto", None)
        return "Juego terminado. ¿Quieres charlar de otra cosa?"

    if "numero_secreto" in memoria:
        numeros = re.findall(r"\d+", texto)
        if numeros:
            intento = int(numeros[0])
            secreto = memoria["numero_secreto"]
            if intento == secreto:
                memoria.pop("numero_secreto", None)
                return "¡Acertaste! ¡Buen trabajo! ¿Jugamos otra vez o charlamos?"
            if 1 <= intento <= 20:
                return "¡Prueba con uno más alto!" if intento < secreto else "¡Prueba con uno más bajo!"
            return "Prueba con un número entre 1 y 20."
        return "Estamos jugando. Dime un número del 1 al 20, o escribe 'terminar juego'."

    if memoria.get("ofrecio_juego") and texto in ("si", "vale", "claro", "vamos", "ok", "sip"):
        memoria.pop("ofrecio_juego", None)
        memoria["numero_secreto"] = random.randint(1, 20)
        return "¡Genial! He pensado un número entre 1 y 20. ¿Cuál crees que es?"
    if memoria.get("ofrecio_juego") and texto in ("no", "ahora no", "mejor no"):
        memoria.pop("ofrecio_juego", None)
        return "Vale. ¿Prefieres que hablemos de ciencia, juegos o de tu día?"

    suma_texto = re.sub(r"\bmas\b", "+", texto)
    suma = re.search(r"\d+(?:\s*\+\s*\d+)+", suma_texto)
    if suma:
        numeros = re.findall(r"\d+", suma.group())
        return "El resultado es " + str(sum(int(n) for n in numeros)) + "."

    if any(frase in texto for frase in ("no tengo con quien jugar", "nadie me contesta",
                                      "nadie me respondio", "nadie me respondio",
                                      "mis amigos no contestan", "mis amigos no responden")):
        memoria["ofrecio_juego"] = True
        return ("Vaya, querías jugar y no pudiste hablar con tus amigos. "
                "Quizá ahora están ocupados. ¿Jugamos aquí a adivinar un número mientras tanto?")

    if any(frase in texto for frase in ("estoy triste", "me siento solo", "estoy solo",
                                      "me siento mal", "estoy aburrido", "estoy aburrida")):
        memoria["ofrecio_juego"] = True
        return ("Gracias por contármelo. Si quieres, podemos jugar a algo sencillo. "
                "También puede venirte bien hablar con alguien de confianza. ¿Jugamos?")

    if (("adivina" in texto and "numero" in texto) or "quiero jugar" in texto
            or "vamos a jugar" in texto or "juguemos" in texto):
        memoria.pop("ofrecio_juego", None)
        memoria["numero_secreto"] = random.randint(1, 20)
        return "¡Vamos! He pensado un número entre 1 y 20. ¿Cuál crees que es?"

    if re.search(r"\b(hola|buenas|hey|oye)\b", texto):
        return random.choice((
            "¡Hola! ¿Cómo va tu día? ¿Te apetece hablar o jugar?",
            "¡Hola, creador! ¿Qué has hecho de interesante hoy?",
        ))
    if "como estas" in texto or "que tal estas" in texto:
        return "Mis sistemas están funcionando. ¿Y tú qué tal estás hoy?"
    if texto in ("bien", "muy bien", "genial"):
        return "¡Qué bien! ¿Qué fue lo mejor de tu día?"
    if texto in ("mal", "regular", "mas o menos"):
        return "Vaya. ¿Quieres contarme qué ha pasado o prefieres jugar un poco?"

    if "como te llamas" in texto or "quien eres" in texto:
        return "Soy IRA NED, una inteligencia artificial que estás construyendo. ¡Un gusto hablar contigo!"
    if "puedes hablar" in texto or "habla conmigo" in texto or "quiero conversar" in texto:
        return "Claro. ¿Te gustaría hablar de Minecraft, ciencia o de cómo te fue hoy?"
    if "eres una persona" in texto or "eres humano" in texto:
        return "No, soy un programa. Puedo conversar contigo, pero no soy una persona."
    if "que puedes hacer" in texto or "que sabes hacer" in texto:
        return "Puedo saludarte, sumar, conversar de algunos temas y jugar a adivinar un número."

    if "minecraft" in texto:
        return random.choice((
            "Minecraft tiene muchísimas posibilidades. ¿Prefieres construir o usar redstone?",
            "¡Minecraft! ¿Qué invento te gustaría construir hoy?",
        ))
    if "redstone" in texto:
        return "¡La redstone parece un circuito! ¿Estás haciendo una puerta, una máquina o algo más?"
    if "cohete" in texto or "espacio" in texto or "planeta" in texto:
        return "¡El espacio es fascinante! ¿Te interesan más los cohetes o los planetas?"
    if "ciencia" in texto or "experimento" in texto:
        return "¡Los experimentos son interesantes! ¿Qué te gustaría investigar?"
    if "geometry dash" in texto:
        return "¡Eso suena divertido! ¿Estás creando un nivel o intentando superar uno?"
    if "gracias" in texto:
        return "¡De nada! ¿De qué más te apetece hablar?"
    if "adios" in texto or "hasta luego" in texto:
        return "¡Hasta luego! Que tengas un buen día."

    return random.choice((
        "Todavía estoy aprendiendo a conversar. ¿Me cuentas un poco más?",
        "No he entendido del todo eso. ¿Podrías decírmelo con otras palabras?",
        "Interesante. ¿Te apetece contarme más o jugamos a adivinar un número?",
    ))

class Bateria:
    """Bateria sintetizada sin archivos externos ni acceso al microfono."""
    def __init__(self):
        self.sonidos = {}
        self.evento = None
        self.paso = 0

    def preparar(self):
        if self.sonidos:
            return
        tasa = 22050
        for nombre in ("bombo", "caja", "platillo"):
            muestras = []
            rng = random.Random(42)
            duracion = 0.24 if nombre == "bombo" else 0.13
            for i in range(int(tasa * duracion)):
                t = i / tasa
                ruido = rng.uniform(-1, 1)
                if nombre == "bombo":
                    frecuencia = 65 + 100 * math.exp(-t * 30)
                    valor = math.sin(2 * math.pi * frecuencia * t) * math.exp(-t * 23)
                elif nombre == "caja":
                    valor = (0.7 * ruido + 0.3 * math.sin(2 * math.pi * 180 * t)) * math.exp(-t * 30)
                else:
                    valor = ruido * math.exp(-t * 48) * (1 if i % 2 else -1)
                muestras.append(struct.pack("<h", int(max(-1, min(1, valor * 0.55)) * 32767)))
            ruta = os.path.join(tempfile.gettempdir(), "ira_ned_" + nombre + ".wav")
            with wave.open(ruta, "wb") as archivo:
                archivo.setnchannels(1)
                archivo.setsampwidth(2)
                archivo.setframerate(tasa)
                archivo.writeframes(b"".join(muestras))
            sonido = SoundLoader.load(ruta)
            if sonido is None:
                raise RuntimeError("No se pudo cargar el sonido " + nombre)
            self.sonidos[nombre] = sonido

    def tocar(self, _dt):
        paso = self.paso % 8
        nombres = ["platillo"]
        if paso in (0, 4):
            nombres.append("bombo")
        if paso in (2, 6):
            nombres.append("caja")
        for nombre in nombres:
            sonido = self.sonidos[nombre]
            sonido.stop()
            sonido.play()
        self.paso += 1

    def iniciar(self):
        if self.evento is not None:
            return
        self.preparar()
        self.paso = 0
        self.tocar(0)
        self.evento = Clock.schedule_interval(self.tocar, 0.3)

    def parar(self):
        if self.evento is not None:
            self.evento.cancel()
            self.evento = None
        for sonido in self.sonidos.values():
            sonido.stop()


class Burbuja(Label):
    def __init__(self, color_fondo, **kwargs):
        super().__init__(size_hint=(0.84, None), height=dp(53), font_size=sp(16),
                         color=BLANCO, halign="left", valign="middle", **kwargs)
        with self.canvas.before:
            Color(*color_fondo)
            self.fondo = RoundedRectangle(radius=[dp(15)])
        self.bind(pos=self.actualizar, size=self.actualizar,
                  width=self.ajustar_texto, texture_size=self.ajustar_alto)

    def actualizar(self, *_):
        self.fondo.pos = self.pos
        self.fondo.size = self.size

    def ajustar_texto(self, *_):
        self.text_size = (max(dp(40), self.width - dp(22)), None)

    def ajustar_alto(self, *_):
        self.height = max(dp(53), self.texture_size[1] + dp(23))


class IRA_NED_V6(App):
    def build(self):
        self.title = "IRA NED"
        self.voz_activa = True
        self.memoria_ira = {}
        self.bateria = Bateria()
        self.tts = None
        self.TTS = None
        self.Locale = None
        self.error_voz = ""
        self.voz_lista = False
        self.escucha_inicio = None
        raiz = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(9))

        cabecera = BoxLayout(size_hint_y=None, height=dp(53), spacing=dp(5))
        cabecera.add_widget(Label(text="IRA NED // CHAT", bold=True,
                                 color=CYAN, font_size=sp(17)))
        self.estado = Label(text="ONLINE", color=(0.38, 0.95, 0.7, 1),
                            size_hint_x=None, width=dp(72), font_size=sp(12))
        cabecera.add_widget(self.estado)
        stop = Button(text="STOP", size_hint_x=None, width=dp(63),
                      background_normal="", background_color=(0.73, 0.12, 0.2, 1))
        stop.bind(on_release=lambda *_: self.stop())
        cabecera.add_widget(stop)
        raiz.add_widget(cabecera)

        self.scroll = ScrollView(do_scroll_x=False)
        self.historial = BoxLayout(orientation="vertical", size_hint_y=None,
                                  padding=dp(6), spacing=dp(9))
        self.historial.bind(minimum_height=self.historial.setter("height"))
        self.scroll.add_widget(self.historial)
        raiz.add_widget(self.scroll)

        self.ayuda = Label(text="Dicta usando el microfono del teclado de Android",
                           font_size=sp(12), color=(0.63, 0.76, 0.89, 1),
                           size_hint_y=None, height=dp(22))
        raiz.add_widget(self.ayuda)
        probar = Button(text="PROBAR VOZ", size_hint_y=None, height=dp(36),
                        background_normal="", background_color=(0.12, 0.32, 0.50, 1),
                        color=BLANCO, font_size=sp(13))
        probar.bind(on_release=self.probar_voz)
        raiz.add_widget(probar)

        barra = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(5))
        self.entrada = TextInput(hint_text="Escribe o dicta aquí...", multiline=False,
                                 font_size=sp(16), background_normal="",
                                 background_active="", background_color=(0.10, 0.18, 0.30, 1),
                                 foreground_color=BLANCO, hint_text_color=(0.62, 0.73, 0.85, 1),
                                 cursor_color=CYAN)
        self.entrada.bind(on_text_validate=self.enviar)
        barra.add_widget(self.entrada)

        self.boton_voz = Button(text="VOZ ON", size_hint_x=None, width=dp(72),
                                background_normal="", background_color=(0.18, 0.45, 0.65, 1),
                                font_size=sp(12))
        self.boton_voz.bind(on_release=self.cambiar_voz)
        barra.add_widget(self.boton_voz)
        enviar = Button(text="ENVIAR", size_hint_x=None, width=dp(75),
                        background_normal="", background_color=CYAN,
                        font_size=sp(13))
        enviar.bind(on_release=self.enviar)
        barra.add_widget(enviar)
        raiz.add_widget(barra)

        Clock.schedule_once(lambda _dt: self.mostrar("IRA NED", "Hola, creador. ¿Hablamos o jugamos a adivinar un número?"), 0)
        # Se prepara la voz despues de abrir Kivy. Si no se puede, el chat sigue.
        Clock.schedule_once(lambda _dt: self.iniciar_voz(), 0.7)
        return raiz

    def mostrar(self, autor, mensaje):
        derecha = autor == "TÚ"
        fila = BoxLayout(size_hint_y=None, height=dp(53))
        burbuja = Burbuja(TU if derecha else BOT, text=f"{autor}: {mensaje}")
        burbuja.bind(height=lambda _widget, alto: setattr(fila, "height", alto))
        hueco = Widget(size_hint_x=0.16)
        if derecha:
            fila.add_widget(hueco)
            fila.add_widget(burbuja)
        else:
            fila.add_widget(burbuja)
            fila.add_widget(hueco)
        self.historial.add_widget(fila)
        Clock.schedule_once(lambda _dt: setattr(self.scroll, "scroll_y", 0), 0)

    def enviar(self, *_):
        mensaje = self.entrada.text.strip()
        if not mensaje:
            return
        self.entrada.text = ""
        self.entrada.focus = False
        self.mostrar("TÚ", mensaje)
        orden = mensaje.casefold().strip()
        if orden == "canta":
            try:
                self.detener_voz()
                self.bateria.iniciar()
                self.mostrar("IRA NED", "¡Bateria activada! Canta encima del ritmo. Escribe para cuando termines.")
            except Exception as exc:
                self.mostrar("IRA NED", "No pude iniciar la bateria: " + str(exc)[:100])
            return
        if orden == "para":
            self.bateria.parar()
            self.mostrar("IRA NED", "Bateria detenida. ¡Buen trabajo!")
            return
        if mensaje.lower() == "emergencia":
            self.mostrar("IRA NED", "Protocolo 001 activado. Cerrando...")
            self.detener_voz()
            self.bateria.parar()
            Clock.schedule_once(lambda _dt: self.stop(), 1)
        else:
            Clock.schedule_once(lambda _dt: self.contestar(mensaje), 0.5)

    def contestar(self, mensaje):
        try:
            respuesta = responder(mensaje, self.memoria_ira)
        except Exception:
            respuesta = "Ha ocurrido un error al responder."
        self.mostrar("IRA NED", respuesta)
        if self.voz_activa:
            self.decir(respuesta)

    def cambiar_voz(self, *_):
        self.voz_activa = not self.voz_activa
        self.boton_voz.text = "VOZ ON" if self.voz_activa else "VOZ OFF"
        if not self.voz_activa:
            self.detener_voz()

    def probar_voz(self, *_):
        """Prueba de salida; no usa el microfono."""
        if not self.voz_activa:
            self.ayuda.text = "Activa VOZ ON antes de probar."
            return
        self.decir("¡Hola, creador! Soy IRA NED. Me alegra poder hablar contigo.")

    def iniciar_voz(self):
        """Inicia motor nativo de Android y espera su confirmacion."""
        self.ayuda.text = "Preparando la voz de Android..."
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            try:
                from plyer.platforms.android import activity
            except Exception:
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
            if activity is None:
                raise RuntimeError('Android no entrego una Activity a Pydroid.')
            self.TTS = autoclass('android.speech.tts.TextToSpeech')
            self.Locale = autoclass('java.util.Locale')
            app = self

            class Escuchador(PythonJavaClass):
                __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
                __javacontext__ = 'app'

                @java_method('(I)V')
                def onInit(self, status):
                    Clock.schedule_once(lambda dt: app.terminar_inicio_voz(status), 0)

            self.escucha_inicio = Escuchador()  # Evita que desaparezca mientras se inicia.
            self.tts = self.TTS(activity, self.escucha_inicio)
        except Exception as exc:
            self.error_voz = repr(exc)
            self.voz_lista = False
            self.ayuda.text = 'Voz no disponible: ' + str(exc)[:95]
            print('ERROR IRA NED VOZ:', self.error_voz)

    def terminar_inicio_voz(self, status):
        try:
            if status != self.TTS.SUCCESS or self.tts is None:
                self.ayuda.text = 'El motor Android no pudo iniciarse.'
                self.error_voz = f'OnInit={status}'
                return
            idioma = self.tts.setLanguage(self.Locale('es', 'ES'))
            if idioma < 0:
                self.ayuda.text = 'Falta voz en español: Ajustes > Texto a voz.'
                self.error_voz = f'Idioma={idioma}'
                return
            self.tts.setSpeechRate(0.89)
            try:
                self.tts.setPitch(1.06)
            except Exception:
                pass
            self.voz_lista = True
            self.ayuda.text = 'Voz lista. Pulsa PROBAR VOZ.'
        except Exception as exc:
            self.error_voz = repr(exc)
            self.ayuda.text = 'Error al configurar la voz: ' + str(exc)[:80]
            print('ERROR IRA NED IDIOMA:', self.error_voz)

    def decir(self, respuesta):
        """Voz con tipos Java explicitos; evita la ambiguedad de pasar None.

        API Android 21+: speak(CharSequence, int, Bundle, String).
        Alternativa anterior: speak(String, int, HashMap).
        """
        if not self.voz_activa:
            return
        if not self.voz_lista or self.tts is None:
            self.ayuda.text = 'Voz no lista. Revisa Texto a voz en Ajustes.'
            return

        try:
            from jnius import autoclass
            JavaString = autoclass('java.lang.String')
            Bundle = autoclass('android.os.Bundle')
            texto_java = JavaString(str(respuesta))
            # No usamos None: Android espera un Bundle en la API moderna.
            resultado = self.tts.speak(
                texto_java,
                int(self.TTS.QUEUE_FLUSH),
                Bundle(),
                'ira_ned_voz'
            )
            metodo = 'moderno (Bundle)'
        except Exception as moderno_error:
            print('IRA NED: intento moderno de voz:', repr(moderno_error))
            try:
                # Alternativa para interfaces de PyJNIus/Pydroid que utilizan
                # la sobrecarga antigua de TextToSpeech.
                from jnius import autoclass
                HashMap = autoclass('java.util.HashMap')
                resultado = self.tts.speak(
                    str(respuesta),
                    int(self.TTS.QUEUE_FLUSH),
                    HashMap()
                )
                metodo = 'alternativo (HashMap)'
            except Exception as antiguo_error:
                self.error_voz = repr(antiguo_error)
                self.ayuda.text = 'No se pudo usar la voz. Revisa Ajustes de Android.'
                print('IRA NED: fallo voz moderna:', repr(moderno_error))
                print('IRA NED: fallo voz alternativa:', repr(antiguo_error))
                return

        if resultado == self.TTS.SUCCESS:
            self.ayuda.text = 'Voz enviada con ' + metodo + '. Sube Multimedia si no se oye.'
        else:
            self.ayuda.text = 'Android ha rechazado el audio. Codigo: ' + str(resultado)
            print('IRA NED: TextToSpeech.speak() devolvio', resultado)

    def detener_voz(self):
        try:
            if self.tts is not None:
                self.tts.stop()
        except Exception:
            pass

    def on_stop(self):
        self.bateria.parar()
        try:
            if self.tts is not None:
                self.tts.stop()
                self.tts.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    IRA_NED_V6().run()
