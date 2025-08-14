
# Generador de Boletos Digitales para Eventos

Esta aplicación en Python permite generar boletos digitales para eventos con códigos QR.

## Características
- Selección de tipo de evento ("Independencia", "Día de Muertos")
- Selección de fecha (por defecto hoy)
- Campos para adultos, niños y nombre (opcional)
- Genera un código QR seguro y lo coloca en una imagen de fondo personalizada
- Guarda la información del boleto en un archivo CSV y la imagen del boleto en formato PNG
- Validación de entradas y administración de boletos
- Escaneo y validación de QR desde la app (compatible con móvil)
- Acceso protegido por login de administrador

## Requisitos
- Python 3.8+
- streamlit
- qrcode
- Pillow
- streamlit-qrcode-scanner

## Instalación
1. Instala las dependencias:
   ```sh
   pip install streamlit qrcode Pillow streamlit-qrcode-scanner
   ```

## Uso
1. Ejecuta la aplicación con Streamlit:
   ```sh
   streamlit run ticket_generator_streamlit.py
   ```
2. Ingresa con el usuario y contraseña de administrador (Definido en las variables de entorno: TICKET_ADMIN_USER y TICKET_ADMIN_PASS)

## Notas
- Personaliza las imágenes de fondo (`ticket_bg_independencia.png`, `ticket_bg_muertos.png`) para cada evento.
- El archivo CSV (`tickets.csv`) se crea automáticamente en el directorio del script.
