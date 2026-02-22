from django.core.management.base import BaseCommand
from repuestocontrol.core.models import Configuracion, Usuario
from repuestocontrol.inventario.models import Marca, Modelo, Categoria, Repuesto
from repuestocontrol.ventas.models import Cliente, Venta, DetalleVenta
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed initial data for the application"

    def handle(self, *args, **options):
        # Crear configuración por defecto
        self.stdout.write("Creating default configuration...")
        if not Configuracion.objects.exists():
            Configuracion.objects.create(
                razon_social="REPuestos ECUADOR CIA. LTDA.",
                nombre_comercial="Repuestos Ecuador",
                ruc="1792345678001",
                direccion_matriz="Av. Principal 123, Quito, Ecuador",
                direccion_sucursal="Av. Principal 123, Quito, Ecuador",
                telefono="022341234",
                email="info@repuestosecuador.com",
                establecimiento="001",
                punto_emision="001",
                secuencia_factura=1,
                iva_tarifa=12.00,
                obligado_contabilidad=True,
                tipo_contribuyente="sociedad",
                regimen_tributario="general",
                contribuyente_especial=False,
                ambiente="1",  # Pruebas
                tipo_emision="1",  # Normal
                activo=True,
            )
            self.stdout.write(self.style.SUCCESS("Default configuration created"))

        self.stdout.write("Creating superuser...")
        if not Usuario.objects.filter(username="admin").exists():
            Usuario.objects.create_superuser(
                username="admin",
                email="admin@repuestocontrol.com",
                password="admin123",
                first_name="Administrador",
                rol=Usuario.Rol.ADMINISTRADOR,
            )
            self.stdout.write(self.style.SUCCESS("Superuser created: admin / admin123"))

        if not Usuario.objects.filter(username="vendedor").exists():
            Usuario.objects.create_user(
                username="vendedor",
                email="vendedor@repuestocontrol.com",
                password="vendedor123",
                first_name="Juan",
                last_name="Pérez",
                telefono="0991234567",
                rol=Usuario.Rol.VENDEDOR,
            )
            self.stdout.write(
                self.style.SUCCESS("Vendedor created: vendedor / vendedor123")
            )

        self.stdout.write("Creating categories...")
        categorias = [
            "Motor",
            "Frenos",
            "Suspensión",
            "Eléctrico",
            "Carrocería",
            "Interior",
            "Transmisión",
            "Refrigeración",
            "Llantas",
            "Accesorios",
        ]
        for nombre in categorias:
            Categoria.objects.get_or_create(nombre=nombre)

        self.stdout.write("Creating brands...")
        marcas_data = [
            ("Toyota", "Japón"),
            ("Chevrolet", "EE.UU."),
            ("Hyundai", "Corea del Sur"),
            ("Nissan", "Japón"),
            ("Kia", "Corea del Sur"),
            ("Ford", "EE.UU."),
            ("Mazda", "Japón"),
            ("Suzuki", "Japón"),
            ("Honda", "Japón"),
            ("Volkswagen", "Alemania"),
            ("Renault", "Francia"),
            ("Mitsubishi", "Japón"),
        ]
        for nombre, pais in marcas_data:
            Marca.objects.get_or_create(nombre=nombre, pais=pais)

        self.stdout.write("Creating models...")
        marcas = Marca.objects.all()
        toyota = marcas.get(nombre="Toyota")
        chevrolet = marcas.get(nombre="Chevrolet")
        hyundai = marcas.get(nombre="Hyundai")
        nissan = marcas.get(nombre="Nissan")
        kia = marcas.get(nombre="Kia")
        honda = marcas.get(nombre="Honda")
        ford = marcas.get(nombre="Ford")

        modelos_data = [
            (toyota, "Corolla", 2014, 2024),
            (toyota, "Hilux", 2016, 2024),
            (toyota, "Yaris", 2018, 2024),
            (toyota, "RAV4", 2019, 2024),
            (chevrolet, "Spark", 2016, 2022),
            (chevrolet, "Aveo", 2013, 2018),
            (chevrolet, "Captiva", 2008, 2021),
            (chevrolet, "TrailBlazer", 2020, 2024),
            (hyundai, "Tucson", 2016, 2024),
            (hyundai, "Accent", 2018, 2022),
            (hyundai, "Santa Fe", 2019, 2024),
            (nissan, "Sentra", 2017, 2024),
            (nissan, "X-Trail", 2020, 2024),
            (kia, "Sportage", 2018, 2024),
            (kia, "Rio", 2017, 2022),
            (honda, "Civic", 2018, 2024),
            (ford, "Explorer", 2019, 2024),
            (ford, "Ranger", 2020, 2024),
        ]
        for marca, nombre, anio_inicio, anio_fin in modelos_data:
            Modelo.objects.get_or_create(
                marca=marca, nombre=nombre, anio_inicio=anio_inicio, anio_fin=anio_fin
            )

        self.stdout.write("Creating sample parts...")
        motor = Categoria.objects.get(nombre="Motor")
        brakes = Categoria.objects.get(nombre="Frenos")
        suspension = Categoria.objects.get(nombre="Suspensión")
        electrico = Categoria.objects.get(nombre="Eléctrico")
        cuerpo = Categoria.objects.get(nombre="Carrocería")
        transmision = Categoria.objects.get(nombre="Transmisión")
        refrigeracion = Categoria.objects.get(nombre="Refrigeración")

        modelos = Modelo.objects.all()
        corolla = modelos.get(marca=toyota, nombre="Corolla")
        spark = modelos.get(marca=chevrolet, nombre="Spark")
        tucson = modelos.get(marca=hyundai, nombre="Tucson")
        sportage = modelos.get(marca=kia, nombre="Sportage")
        sentra = modelos.get(marca=nissan, nombre="Sentra")
        civic = modelos.get(marca=honda, nombre="Civic")

        repuestos_data = [
            (
                "FIL-001",
                "Filtro de aceite",
                motor,
                toyota,
                corolla,
                5.00,
                12.00,
                25,
                10,
                "bodega_a",
            ),
            (
                "FIL-002",
                "Filtro de aire",
                motor,
                toyota,
                corolla,
                4.00,
                10.00,
                30,
                10,
                "bodega_a",
            ),
            (
                "FIL-003",
                "Filtro de combustible",
                motor,
                chevrolet,
                spark,
                6.00,
                15.00,
                20,
                8,
                "bodega_a",
            ),
            (
                "FIL-004",
                "Filtro de aire",
                motor,
                hyundai,
                tucson,
                5.50,
                12.00,
                18,
                8,
                "bodega_a",
            ),
            (
                "FIL-005",
                "Filtro de aceite",
                motor,
                honda,
                civic,
                6.00,
                14.00,
                22,
                10,
                "bodega_a",
            ),
            (
                "PAD-001",
                "Pastillas de freno",
                brakes,
                toyota,
                corolla,
                15.00,
                35.00,
                15,
                5,
                "bodega_b",
            ),
            (
                "PAD-002",
                "Pastillas de freno",
                brakes,
                hyundai,
                tucson,
                18.00,
                40.00,
                12,
                5,
                "bodega_b",
            ),
            (
                "PAD-003",
                "Pastillas de freno",
                brakes,
                nissan,
                sentra,
                16.00,
                38.00,
                14,
                5,
                "bodega_b",
            ),
            (
                "BAL-001",
                "Amortiguador",
                suspension,
                chevrolet,
                spark,
                25.00,
                55.00,
                8,
                3,
                "bodega_c",
            ),
            (
                "BAL-002",
                "Amortiguador",
                suspension,
                hyundai,
                tucson,
                30.00,
                65.00,
                10,
                3,
                "bodega_c",
            ),
            (
                "BAL-003",
                "Amortiguador",
                suspension,
                kia,
                sportage,
                28.00,
                60.00,
                9,
                3,
                "bodega_c",
            ),
            (
                "BOM-001",
                "Bomba de agua",
                motor,
                toyota,
                corolla,
                20.00,
                45.00,
                6,
                3,
                "bodega_a",
            ),
            (
                "BOM-002",
                "Bomba de Frenos",
                brakes,
                chevrolet,
                spark,
                22.00,
                48.00,
                5,
                2,
                "bodega_b",
            ),
            (
                "BUJ-001",
                "Bujía",
                electrico,
                toyota,
                corolla,
                2.00,
                5.00,
                50,
                20,
                "estante_1",
            ),
            (
                "BUJ-002",
                "Bujía",
                electrico,
                chevrolet,
                spark,
                2.50,
                6.00,
                45,
                15,
                "estante_1",
            ),
            (
                "BUJ-003",
                "Bujía",
                electrico,
                honda,
                civic,
                3.00,
                7.00,
                40,
                15,
                "estante_1",
            ),
            (
                "DIS-001",
                "Disco de freno",
                brakes,
                toyota,
                corolla,
                12.00,
                28.00,
                18,
                5,
                "bodega_b",
            ),
            (
                "DIS-002",
                "Disco de freno",
                brakes,
                hyundai,
                tucson,
                14.00,
                32.00,
                16,
                5,
                "bodega_b",
            ),
            (
                "COR-001",
                "Correa de distribución",
                motor,
                toyota,
                corolla,
                18.00,
                42.00,
                7,
                3,
                "bodega_a",
            ),
            (
                "COR-002",
                "Correa de distribución",
                motor,
                nissan,
                sentra,
                20.00,
                45.00,
                6,
                3,
                "bodega_a",
            ),
            (
                "ALT-001",
                "Alternador",
                electrico,
                hyundai,
                tucson,
                45.00,
                95.00,
                4,
                2,
                "estante_2",
            ),
            (
                "ALT-002",
                "Alternador",
                electrico,
                kia,
                sportage,
                48.00,
                100.00,
                3,
                2,
                "estante_2",
            ),
            (
                "ARR-001",
                "Arrastre",
                suspension,
                chevrolet,
                spark,
                8.00,
                18.00,
                14,
                5,
                "bodega_c",
            ),
            (
                "ARR-002",
                "Arrastre",
                suspension,
                toyota,
                corolla,
                10.00,
                22.00,
                12,
                4,
                "bodega_c",
            ),
            (
                "LUZ-001",
                "Luz piloto LED",
                electrico,
                toyota,
                corolla,
                5.00,
                12.00,
                40,
                15,
                "estante_1",
            ),
            (
                "LUZ-002",
                "Luz de freno",
                electrico,
                hyundai,
                tucson,
                6.00,
                14.00,
                35,
                12,
                "estante_1",
            ),
            (
                "RAD-001",
                "Radiador",
                refrigeracion,
                toyota,
                corolla,
                35.00,
                75.00,
                4,
                2,
                "bodega_d",
            ),
            (
                "RAD-002",
                "Radiador",
                refrigeracion,
                honda,
                civic,
                40.00,
                85.00,
                3,
                2,
                "bodega_d",
            ),
            (
                "EMB-001",
                "Embrague",
                transmision,
                toyota,
                corolla,
                55.00,
                120.00,
                3,
                2,
                "bodega_e",
            ),
            (
                "EMB-002",
                "Embrague",
                transmision,
                nissan,
                sentra,
                50.00,
                110.00,
                4,
                2,
                "bodega_e",
            ),
            (
                "JUE-001",
                "Juego de boceles",
                motor,
                toyota,
                corolla,
                8.00,
                18.00,
                25,
                10,
                "bodega_a",
            ),
            (
                "JUE-002",
                "Juego de boceles",
                motor,
                chevrolet,
                spark,
                7.00,
                16.00,
                20,
                8,
                "bodega_a",
            ),
            (
                "PAR-001",
                "Parachoques",
                cuerpo,
                toyota,
                corolla,
                45.00,
                95.00,
                3,
                2,
                "bodega_f",
            ),
            (
                "PAR-002",
                "Parachoques",
                cuerpo,
                hyundai,
                tucson,
                55.00,
                120.00,
                2,
                1,
                "bodega_f",
            ),
            (
                "ESPE-001",
                "Espejo retrovisor",
                cuerpo,
                kia,
                sportage,
                15.00,
                35.00,
                10,
                4,
                "bodega_f",
            ),
            (
                "LIM-001",
                "Limpiadores",
                cuerpo,
                toyota,
                corolla,
                8.00,
                18.00,
                30,
                12,
                "estante_3",
            ),
            (
                "LIM-002",
                "Limpiadores",
                cuerpo,
                hyundai,
                tucson,
                9.00,
                20.00,
                28,
                10,
                "estante_3",
            ),
            (
                "BAT-001",
                "Batería 12V",
                electrico,
                toyota,
                corolla,
                35.00,
                75.00,
                8,
                3,
                "estante_2",
            ),
            (
                "BAT-002",
                "Batería 12V",
                electrico,
                chevrolet,
                spark,
                32.00,
                70.00,
                10,
                4,
                "estante_2",
            ),
            (
                "SEN-001",
                "Sensor de oxígeno",
                electrico,
                toyota,
                corolla,
                18.00,
                42.00,
                6,
                3,
                "estante_1",
            ),
            (
                "SEN-002",
                "Sensor de temperatura",
                electrico,
                honda,
                civic,
                12.00,
                28.00,
                8,
                3,
                "estante_1",
            ),
            (
                "DIR-001",
                "Bomba de dirección",
                suspension,
                hyundai,
                tucson,
                40.00,
                85.00,
                4,
                2,
                "bodega_c",
            ),
            (
                "CAJ-001",
                "Caja de dirección",
                suspension,
                chevrolet,
                spark,
                55.00,
                120.00,
                3,
                2,
                "bodega_c",
            ),
        ]

        for datos in repuestos_data:
            Repuesto.objects.get_or_create(
                codigo=datos[0],
                defaults={
                    "nombre": datos[1],
                    "categoria": datos[2],
                    "marca": datos[3],
                    "modelo": datos[4],
                    "precio_compra": datos[5],
                    "precio_venta": datos[6],
                    "stock_actual": datos[7],
                    "stock_minimo": datos[8],
                    "ubicacion": datos[9],
                    "activo": True,
                },
            )

        self.stdout.write("Creating clients...")
        clientes_data = [
            (
                "Juan Carlos García",
                "0912345678",
                "0991234567",
                "juan.garcia@email.com",
                "Av. Amazonas 123, Quito",
                "cedula",
            ),
            (
                "María Elena López",
                "0923456789",
                "0982345678",
                "maria.lopez@email.com",
                "Av. 10 de Agosto 456, Guayaquil",
                "cedula",
            ),
            (
                "Pedro Antonio Ramírez",
                "0934567890",
                "0973456789",
                "pedro.ramirez@email.com",
                "Calle principal 789, Cuenca",
                "cedula",
            ),
            (
                "Ana Lucía González",
                "0945678901",
                "0964567890",
                "ana.gonzalez@email.com",
                "Av. Eloy Alfaro 321, Quito",
                "cedula",
            ),
            (
                "Carlos Eduardo Martínez",
                "0956789012",
                "0955678901",
                "carlos.martinez@email.com",
                "Av. Cristóbal Colón 654, Guayaquil",
                "cedula",
            ),
            (
                "Laura Patricia Silva",
                "0967890123",
                "0946789012",
                "laura.silva@email.com",
                "Calle Nueva 987, Quito",
                "cedula",
            ),
            (
                "Miguel Ángel Torres",
                "0978901234",
                "0937890123",
                "miguel.torres@email.com",
                "Av. Oriental 147, Cuenca",
                "cedula",
            ),
            (
                "Sofia Cristina Ruiz",
                "0989012345",
                "0928901234",
                "sofia.ruiz@email.com",
                "Av. del Estadio 258, Guayaquil",
                "cedula",
            ),
            (
                "Diego Fernando López",
                "0990123456",
                "0919012345",
                "diego.lopez@email.com",
                "Calle 10 369, Quito",
                "cedula",
            ),
            (
                "Andrea Vanessa Cárdenas",
                "0911234567",
                "0990123456",
                "andrea.cardenas@email.com",
                "Av. González Suárez 741, Quito",
                "cedula",
            ),
        ]
        for nombre, cedula, telefono, email, direccion, tipo_id in clientes_data:
            Cliente.objects.get_or_create(
                cedula=cedula,
                defaults={
                    "nombre": nombre,
                    "telefono": telefono,
                    "email": email,
                    "direccion": direccion,
                    "tipo_identificacion": tipo_id,
                },
            )

        self.stdout.write("Creating sales...")
        admin_user = Usuario.objects.get(username="admin")
        config = Configuracion.get_config()
        clientes = Cliente.objects.all()
        repuestos_list = Repuesto.objects.all()[:20]

        ventas_data = [
            (clientes[0], "Efectivo", 0),
            (clientes[1], "Transferencia", 10.00),
            (clientes[2], "Efectivo", 5.00),
            (clientes[3], "Tarjeta", 15.00),
            (clientes[4], "Transferencia", 0),
        ]

        for i, (cliente, metodo_pago, descuento) in enumerate(ventas_data):
            secuencial = config.secuencia_factura + i
            numero_factura = f"001-001-{str(secuencial).zfill(9)}"

            venta = Venta.objects.create(
                numero=f"VT-{timezone.now().year}{str(i + 1).zfill(6)}",
                numero_factura=numero_factura,
                secuencia_factura=secuencial,
                cliente=cliente,
                vendedor=admin_user,
                metodo_pago=metodo_pago,
                descuento=descuento,
                estado_sri="autorizada",
                estado=Venta.Estado.COMPLETADA,
            )

            subtotal = 0
            for j in range(2):
                repuesto = repuestos_list[(i + j) % len(repuestos_list)]
                cantidad = j + 1
                detalle = DetalleVenta.objects.create(
                    venta=venta,
                    repuesto=repuesto,
                    cantidad=cantidad,
                    precio_unitario=repuesto.precio_venta,
                    subtotal=cantidad * repuesto.precio_venta,
                )
                subtotal += detalle.subtotal

            venta.subtotal_12 = subtotal
            venta.subtotal_0 = 0
            from decimal import Decimal

            venta.iva = (subtotal - Decimal(str(descuento))) * Decimal("0.12")
            venta.total = subtotal + venta.iva - Decimal(str(descuento))
            venta.save()

        # Actualizar secuencial
        config.secuencia_factura += len(ventas_data)
        config.save()

        self.stdout.write(self.style.SUCCESS("Seed data created successfully!"))
