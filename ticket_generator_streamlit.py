import streamlit as st
import os
import qrcode
from PIL import Image
import csv
import json
from datetime import datetime
import os
import uuid
import hashlib

# Constants
EVENT_TYPES = ["Independencia", "Dia de Muertos"]
BACKGROUND_IMAGE = "ticket_bg_independencia.png"  # Placeholder, replace with your own image
CSV_FILE = "tickets.csv"


def validate_inputs(event_type, date, adults, children):
    errors = []
    if event_type not in EVENT_TYPES:
        errors.append("Invalid event type.")
    try:
        adults = int(adults)
        if adults < 0:
            errors.append("Adults must be 0 or more.")
    except ValueError:
        errors.append("Adults must be an integer.")
    try:
        children = int(children)
        if children < 0:
            errors.append("Children must be 0 or more.")
    except ValueError:
        errors.append("Children must be an integer.")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        errors.append("Date must be in YYYY-MM-DD format.")
    return errors


def generate_token(event_type, date, adults, children):
    # Ensure token_id is unique in tickets.csv
    def token_id_exists(token_id):
        if not os.path.exists(CSV_FILE):
            return False
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('token_id') == token_id:
                    return True
        return False

    while True:
        token_id = str(uuid.uuid4())
        if not token_id_exists(token_id):
            break
    # Hash the token_id for QR code
    hashed_token = hashlib.sha256(token_id.encode()).hexdigest()
    return hashed_token, token_id


def save_ticket_info(hashed_token,token_id, event_type, date, adults, children, gen_time, filename, nombre):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        if not file_exists:
            writer.writerow(["hashed_token","token_id", "event_type", "date", "adults", "children", "generated_at", "ticket_filename", "nombre"])
        writer.writerow([
            hashed_token,
            token_id,
            event_type,
            date,
            adults,
            children,
            gen_time,
            filename,
            nombre
        ])


def create_ticket_image(token, output_filename,event_type,adults, children,nombre):
    # Generate QR code with hashed token_id
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(token)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # Determine background image based on event type in token
    try:
        print("EVENT TYPE")
        print(event_type)

        if event_type == "Independencia":
            bg_file = "ticket_bg_independencia.png"
            print("[TicketGen] Using Independence background")
        elif event_type == "Dia de Muertos":
            print("[TicketGen] Using Dia de Muertos background")
            bg_file = "ticket_bg_muertos.png"
        else:
            bg_file = BACKGROUND_IMAGE
    except Exception as e:
        print(e)
        bg_file = BACKGROUND_IMAGE

    # Load background
    if not os.path.exists(bg_file):
        # Create a placeholder background if not found
        bg = Image.new("RGBA", (600, 400), (255, 255, 255, 255))
    else:
        bg = Image.open(bg_file).convert("RGBA")

    # Make QR code 30% bigger
    qr_w, qr_h = qr_img.size
    new_qr_w = int(qr_w * 1.5)
    new_qr_h = int(qr_h * 1.5)
    qr_img = qr_img.resize((new_qr_w, new_qr_h), Image.LANCZOS)
    qr_w, qr_h = qr_img.size
    bg_w, bg_h = bg.size

    # Adjust QR code position for 'Independencia' event
    pos_x = (bg_w - qr_w) // 2
    pos_y = (bg_h - qr_h) // 2
    if event_type == "Independencia":
        pos_y = min(bg_h - qr_h, pos_y + 550)  # Move 40px down, but not out of bounds
    pos = (pos_x, pos_y)
    bg.paste(qr_img, pos, qr_img)

    # Draw adults/children count and nombre (if present) under QR code
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(bg)
        # Try to use a truetype font if available, else default
        font = None
        font_found = False
        font_candidates = [
            "arial.ttf",  # Windows
            "/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]
        for font_path in font_candidates:
            try:
                font = ImageFont.truetype(font_path, 28)
                font_found = True
                break
            except Exception:
                continue
        if not font_found:
            font = ImageFont.load_default()

        # Compose lines to draw
        lines = [f"Adultos: {adults}  Niños: {children}"]
        if nombre and str(nombre).strip():
            lines.append(f"{nombre}")

        # Draw each line, stacking vertically
        total_height = 0
        line_sizes = []
        for line in lines:
            try:
                bbox = draw.textbbox((0,0), line, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except Exception:
                text_w, text_h = draw.textsize(line, font=font)
            line_sizes.append((text_w, text_h))
            total_height += text_h
        total_height += (len(lines)-1)*4  # 4px spacing between lines

        # Start drawing below QR code
        start_y = pos[1] + qr_h + 10
        if start_y + total_height > bg_h:
            start_y = bg_h - total_height - 10

        # Draw background rectangle for all lines
        max_width = max(w for w, h in line_sizes)
        rect_x0 = (bg_w - max_width)//2 - 8
        rect_y0 = start_y - 4
        rect_x1 = (bg_w + max_width)//2 + 8
        rect_y1 = start_y + total_height + 4
        draw.rectangle([(rect_x0, rect_y0), (rect_x1, rect_y1)], fill=(255,255,255,220))

        # Draw each line
        y = start_y
        for i, line in enumerate(lines):
            text_w, text_h = line_sizes[i]
            text_x = (bg_w - text_w) // 2
            draw.text((text_x, y), line, fill=(0,0,0), font=font)
            y += text_h + 4
    except Exception as e:
        print(f"[TicketGen] Failed to draw text: {e}")

    bg.save(output_filename)



# --- LOGIN HANDLER ---
def login_window():
    import streamlit as st
    import os
    # Get credentials from environment variables
    ADMIN_USER = os.environ.get("TICKET_ADMIN_USER")
    ADMIN_PASS = os.environ.get("TICKET_ADMIN_PASS")
    if 'login_success' not in st.session_state:
        st.session_state['login_success'] = False
    if not st.session_state['login_success']:
        st.title("Iniciar sesión - Administrador")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state['login_success'] = True
                st.success("Acceso concedido.")
            else:
                st.error("Usuario o contraseña incorrectos.")
        st.stop()

def main():
    login_window()

    tab = st.sidebar.radio(
        "Selecciona una opción:",
        ("Generar Ticket", "Validar código QR", "Administrar tickets"),
        index=0
    )

    if tab == "Administrar tickets":
        st.header("Administrar registro de tickets")
        # Show table of tickets.csv (hide hashed_token)
        import pandas as pd
        if os.path.exists(CSV_FILE):
            try:
                df = pd.read_csv(CSV_FILE, delimiter=';')
                if 'hashed_token' in df.columns:
                    df = df.drop(columns=['hashed_token'])
                if 'token_id' in df.columns:
                    df = df.drop(columns=['token_id'])
                # Move 'nombre' to the first column if present
                cols = list(df.columns)
                if 'nombre' in cols:
                    cols.insert(0, cols.pop(cols.index('nombre')))
                    df = df[cols]
                st.subheader("Base de datos de tickets (solo lectura)")
                st.dataframe(df, use_container_width=True, hide_index=True)
                # Show totals grouped by event_type
                if 'event_type' in df.columns and 'adults' in df.columns and 'children' in df.columns:
                    # Try both possible column names for compatibility
                    adults_col = 'adults' if 'adults' in df.columns else 'adultos'
                    children_col = 'children' if 'children' in df.columns else 'niños'
                    summary = df.groupby('event_type')[[adults_col, children_col]].sum().reset_index()
                    st.markdown("**Total de boletos vendidos:**")
                    table_md = "Evento | adultos | niños\n---|---|---\n"
                    for _, row in summary.iterrows():
                        table_md += f"{row['event_type']} | {row[adults_col]} | {row[children_col]}\n"
                    st.markdown(table_md)
            except Exception as e:
                st.warning(f"No se pudo mostrar la tabla: {e}")
        st.divider()      
        st.write("Descarga o sube la lista de tickets.")
        # Download button
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                st.download_button("Descargar tickets.csv", f, file_name="tickets.csv", mime="text/csv")
        else:
            st.info("No existe tickets.csv aún.")
        # Upload button
        uploaded = st.file_uploader("Subir nuevo tickets.csv", type=["csv"])
        if uploaded is not None:
            st.warning("¿Seguro que deseas sobrescribir la lista de tickets? Se hará un respaldo antes de sobrescribir.")
            if st.button("Confirmar y sobrescribir"): 
                # Make backup
                import shutil
                backup_folder = "backup"
                os.makedirs(backup_folder, exist_ok=True)
                if os.path.exists(CSV_FILE):
                    backup_path = os.path.join(backup_folder, f"tickets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                    shutil.copy2(CSV_FILE, backup_path)
                    st.info(f"Respaldo guardado en {backup_path}")
                # Overwrite
                with open(CSV_FILE, "wb") as f:
                    f.write(uploaded.read())
                st.success("tickets.csv sobrescrito correctamente.")
                st.experimental_rerun()
        st.stop()
    elif tab == "Generar Ticket":    
        st.title("Generador de tickets digitales")
        st.write("Genera tickets digitales para eventos con códigos QR.")

        nombre = st.text_input("Nombre (opcional)")
        event_type = st.selectbox("Evento", EVENT_TYPES)
        date = st.date_input("Día de compra", value=datetime.now()).strftime("%Y-%m-%d")
        adults = st.number_input("Número de Adultos", min_value=0, value=1, step=1)
        children = st.number_input("Número of niños", min_value=0, value=0, step=1)

        if st.button("Generar Ticket"):
            errors = validate_inputs(event_type, date, adults, children)
            if errors:
                st.error("\n".join(errors))
            else:
                hashed_token, token_id = generate_token(event_type, date, adults, children)
                gen_time = datetime.now().isoformat()
                # Determine folder by event type
                folder = f"tickets/{event_type}/"
                os.makedirs(folder, exist_ok=True)
                filename = os.path.join(folder, f"ticket_{event_type}_{date}_{gen_time.replace(':','-').replace('.','-')}.png")
                create_ticket_image(hashed_token, filename,event_type,adults,children,nombre)
                save_ticket_info(hashed_token,token_id, event_type, date, adults, children, gen_time, filename, nombre)
                st.success(f"Ticket generado y guardado como {filename}\n Token ID: {token_id}")
                if os.path.exists(filename):
                    st.image(filename, caption="Ticket Generado", use_container_width=True)
                    with open(filename, "rb") as img_file:
                        btn = st.download_button(
                            label="Descargar",
                            data=img_file,
                            file_name=os.path.basename(filename),
                            mime="image/png"
                        )

    elif tab == "Validar código QR":
        st.header("Validación de código QR")
        st.write("Escanear un código QR de ticket para validar contra los tickets emitidos.")
        from streamlit_qrcode_scanner import qrcode_scanner
        qr_code = qrcode_scanner(key='qrcode_scanner')
        if qr_code:
            st.info(f"QR detectado: {qr_code}")
            # Check if hash matches any token_id in tickets.csv
            found = False
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile, delimiter=';')
                    for row in reader:
                        token_id = row.get('token_id')
                        if token_id and hashlib.sha256(token_id.encode()).hexdigest() == qr_code:
                            found = True
                            st.success(f"Ticket válido! Detalles: {row}")
                            break
            if not found:
                st.error("Ticket NO encontrado o invalido!")

if __name__ == "__main__":
    main()
