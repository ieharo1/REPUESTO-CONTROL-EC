# RepuestoControl EC

Sistema de gestión e inventario profesional para tiendas de repuestos automotrices en Ecuador.

---

## 📸 Screenshots

### Login
![Login](static/images/login.png)

### Dashboard
![Dashboard](static/images/home.png)

---

## 📋 Descripción

RepuestoControl EC es una aplicación web desarrollada con Django 5+ y PostgreSQL, diseñada para gestionar el inventario, ventas y métricas de tiendas de repuestos automotrices.

---

## 🏗️ Funcionalidades Principales

- **Gestión de Marcas** - CRUD completo de marcas compatibles
- **Gestión de Modelos** - Modelos relacionados con marcas
- **Gestión de Repuestos** - Código, nombre, precios, stock, ubicación
- **Inventario Inteligente** - Alertas de stock bajo, control de inventario
- **Módulo de Ventas** - Creación de ventas, control de stock, múltiples métodos de pago
- **Dashboard y Métricas** - Productos más vendidos, ingresos, stock crítico
- **Catálogo Público** - Vista pública sin login para clientes
- **Modo Oscuro/Claro** - Tema adaptativo
- **Diseño Responsivo** - Compatible con móviles y escritorio
- **Facturación Electrónica SRI** - Generación XML, firma digital, autorización, PDF RIDE, email automático

---

## 🛠️ Stack Tecnológico

- Python 3.12
- Django 6.0
- PostgreSQL 17
- Bootstrap 5 (CDN)
- Docker
- HTML5 / CSS / JavaScript
- ReportLab (PDF)
- Zeep (SOAP)
- xmlsec (Firma digital)

---

## 🚀 Configuración con Docker

```bash
# Iniciar la aplicación
docker-compose up --build -d

# La aplicación estará disponible en:
# http://localhost:8000

# Panel de administración:
# http://localhost:8000/admin

# Catálogo público:
# http://localhost:8000/catalogo/
```

### Credenciales por defecto

- **Usuario:** admin
- **Contraseña:** admin123

---

# 📦 Facturación Electrónica Ecuador - Producción

Este proyecto incluye un módulo completo de facturación electrónica que cumple con todas las normativas del SRI (Servicio de Rentas Internas) de Ecuador.

## 🔧 Características

- ✅ Generación de clave de acceso (49 dígitos)
- ✅ Validación de identificación (cédula, RUC)
- ✅ Validación XSD oficial
- ✅ Firma digital XAdES-BES
- ✅ Conexión SOAP con Web Services del SRI
- ✅ Autorización en ambiente PRUEBAS y PRODUCCIÓN
- ✅ Generación de PDF RIDE profesional
- ✅ Envío automático de email con XML y PDF
- ✅ Control secuencial robusto
- ✅ Múltiples tarifas de IVA (12%, 14%, 15%, 0%)
- ✅ Múltiples formas de pago

---

## 📋 Configuración Inicial

### 1. Variables de Entorno

Copia el archivo `.env.example` a `.env` y configura:

```bash
# Básico
SECRET_KEY=tu-secret-key-aqui
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com

# Base de datos
DB_NAME=repuestocontrol
DB_USER=postgres
DB_PASSWORD=tu-contraseña
DB_HOST=localhost

# Email (Gmail o servidor corporativo)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
EMAIL_USE_TLS=True

# Facturación electrónica
SRI_TIMEOUT=60
SRI_REINTENTOS=3
```

### 2. Certificado Digital

1. Obtén un certificado digital válido de una autoridad certificadora reconocida en Ecuador
2. Convierte tu certificado a formato `.p12` (PKCS12)
3. Sube el certificado desde el panel de administración en Configuración > Certificado Digital
4. Ingresa la contraseña del certificado

### 3. Configuración de Empresa

Desde el panel de administración, configura:

- Razón Social
- RUC (13 dígitos)
- Dirección Matriz
- Dirección Sucursal
- Teléfono y Email
- Establecimiento (001)
- Punto de Emisión (001)
- Tarifa IVA (12%, 14%, 15%)
- Ambiente: PRUEBAS o PRODUCCIÓN

---

## 🧪 Prueba en Ambiente de Pruebas

### Ambiente Pruebas SRI

El SRI proporciona un ambiente de pruebas en:
- **URL:** https://celcer.sri.gob.ec/comprobanteselectronicosws/

### Pasos para probar:

1. **Configura el ambiente en PRUEBAS:**
   - Ve a Configuración > Editar
   - Selecciona "Pruebas" en Ambiente

2. **Crea una venta:**
   - Ve a Ventas > Crear
   - Agrega productos
   - Finaliza la venta

3. **Autoriza la factura:**
   - Ve a Ventas > Detalle de la venta
   - Haz clic en "Autorizar Factura"
   - Espera la respuesta del SRI

4. **Verifica el estado:**
   - La factura debe mostrar estado "AUTORIZADO"
   - Descarga el XML y PDF

---

## 🚀 Paso a Producción

### Importante

**ANTES de pasar a producción:**

1. ✅ Obtén un certificado digital de producción válido
2. ✅ Verifica que el RUC esté habilitado para facturación electrónica
3. ✅ Configura el ambiente en "PRODUCCIÓN"
4. ✅ Configura el email SMTP
5. ✅ Realiza pruebas en ambiente de pruebas
6. ✅ Cambia `DEBUG=False` en `.env`

### Cambiar a Producción:

```bash
# Edita el archivo .env
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Reinicia la aplicación
docker-compose restart
```

---

## 📊 Estados de Facturación

| Estado | Descripción |
|--------|-------------|
| PENDIENTE | Factura creada, sin enviar |
| XML_GENERADO | XML generado |
| VALIDADO | Pasó validación XSD |
| FIRMADO | Certificado aplicado |
| ENVIADO_SRI | Enviado al SRI |
| AUTORIZADO | Aprobado por el SRI |
| DEVUELTO | Rechazado (revisar errores) |
| ERROR | Error en el proceso |

---

## 📁 Estructura del Proyecto

```
Django-APP/
├── repuestocontrol/
│   ├── core/                   # Usuarios y autenticación
│   │   ├── sri.py             # Generación XML, clave acceso
│   │   ├── firma_digital.py   # Firma XAdES-BES
│   │   ├── sri_ws.py          # Web Services SOAP
│   │   ├── validacion_xsd.py  # Validación XSD
│   │   ├── generador_pdf.py   # PDF RIDE
│   │   ├── email_comprobantes.py  # Envío email
│   │   ├── control_secuencial.py  # Secuenciales
│   │   └── procesamiento_sri.py   # Proceso completo
│   ├── inventario/            # Gestión de repuestos
│   ├── ventas/                # Módulo de ventas
│   ├── dashboard/             # Métricas y estadísticas
│   ├── catalogo_publico/      # Catálogo público
│   ├── settings.py           # Configuración
│   └── urls.py               # Rutas principales
├── templates/                # Templates base
├── static/                   # Archivos estáticos
├── docker-compose.yml        # Docker compose
├── Dockerfile               # Imagen Docker
├── requirements.txt          # Dependencias
└── .env.example            # Variables de entorno
```

---

## 🔒 Seguridad en Producción

El proyecto incluye:

- ✅ Variables sensibles en `.env`
- ✅ DEBUG=False en producción
- ✅ Cookies seguras (HttpOnly, Secure)
- ✅ Protección CSRF activa
- ✅ SSL/HTTPS forzado
- ✅ Headers de seguridad
- ✅ Logs estructurados
- ✅ Validación de datos

---

## 📝 Testing

```bash
# Ejecutar tests
pytest repuestocontrol/core/tests/ -v

# Tests específicos de facturación
pytest repuestocontrol/core/tests/test_facturacion.py -v
```

---

## ⚠️ Solución de Problemas

### Error: "Certificado no encontrado"
- Verifica que el certificado esté subido en Configuración

### Error: "Validación XSD falló"
- Revisa que el XML cumpla con el esquema SRI

### Error: "Timeout conexión SRI"
- Aumenta el valor de SRI_TIMEOUT en .env

### Error: "Email no enviado"
- Verifica la configuración SMTP
- Para Gmail, usa una "App Password" (no tu contraseña)

---

## 📧 Configuración Email

### Gmail
1. Habilita verificación en 2 pasos
2. Genera una "App Password" en seguridad
3. Usa esa contraseña en EMAIL_HOST_PASSWORD

### Servidor Corporativo
```bash
EMAIL_HOST=smtp.tuempresa.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-usuario
EMAIL_HOST_PASSWORD=tu-contraseña
```

---

## 👨‍💻 Desarrollado por Isaac Esteban Haro Torres

**Ingeniero en Sistemas · Full Stack · Automatización · Data**

- 📧 Email: zackharo1@gmail.com
- 📱 WhatsApp: 098805517
- 💻 GitHub: https://github.com/ieharo1
- 🌐 Portafolio: https://ieharo1.github.io/portafolio-isaac.haro/

---

## 📄 Licencia

© 2026 Isaac Esteban Haro Torres - Todos los derechos reservados.
