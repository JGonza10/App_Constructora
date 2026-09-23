import os

import click
from flask import Flask
from config import Config
from .extensions import db, bcrypt, csrf, login_manager, limiter, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar."

    @login_manager.user_loader
    def load_user(id_compuesto):
        from .models import Usuario, ClienteAcceso
        tipo, _, raw_id = id_compuesto.partition(":")
        if tipo == "usuario":
            return db.session.get(Usuario, int(raw_id))
        if tipo == "cliente":
            return db.session.get(ClienteAcceso, int(raw_id))
        return None

    from .auth import auth_bp
    from .portal import portal_bp
    from .main import main_bp
    from .clientes import clientes_bp
    from .levantamientos import levantamientos_bp
    from .cotizaciones import cotizaciones_bp
    from .obras import obras_bp
    from .usuarios import usuarios_bp
    from .trabajadores import trabajadores_bp
    from .catalogo import catalogo_bp
    from .equipo import equipo_bp
    from .subcontratistas import subcontratistas_bp
    from .plantillas import plantillas_bp
    from .auditoria import auditoria_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp, url_prefix="/portal")
    app.register_blueprint(main_bp)
    app.register_blueprint(clientes_bp, url_prefix="/clientes")
    app.register_blueprint(levantamientos_bp, url_prefix="/levantamientos")
    app.register_blueprint(cotizaciones_bp, url_prefix="/cotizaciones")
    app.register_blueprint(obras_bp, url_prefix="/obras")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(trabajadores_bp, url_prefix="/trabajadores")
    app.register_blueprint(catalogo_bp, url_prefix="/catalogo")
    app.register_blueprint(equipo_bp, url_prefix="/equipo")
    app.register_blueprint(subcontratistas_bp, url_prefix="/subcontratistas")
    app.register_blueprint(plantillas_bp, url_prefix="/plantillas")
    app.register_blueprint(auditoria_bp, url_prefix="/auditoria")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(403)
    def prohibido(_e):
        from flask import render_template
        return render_template("error.html", codigo=403, mensaje="No tienes permiso para ver esto."), 403

    @app.errorhandler(404)
    def no_encontrado(_e):
        from flask import render_template
        return render_template("error.html", codigo=404, mensaje="No encontramos lo que buscabas."), 404

    @app.errorhandler(500)
    def error_interno(e):
        from flask import render_template
        app.logger.exception(e)
        return render_template("error.html", codigo=500, mensaje="Algo salió mal de nuestro lado. Ya quedó registrado."), 500

    @app.cli.command("init-db")
    def init_db():
        """Crea todas las tablas si no existen (no borra datos existentes)."""
        with app.app_context():
            db.create_all()
        print("Tablas creadas/verificadas.")

    @app.cli.command("crear-admin")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    @click.option("--nombre", default="Administrador")
    @click.option("--rol", default="admin", type=click.Choice(["admin", "supervisor", "empleado"]))
    def crear_admin(email, password, nombre, rol):
        """Crea un usuario interno, o le actualiza nombre/rol/password si el
        email ya existe. Idempotente a proposito: sirve tanto para el primer
        arranque (no hay ruta web sin sesion para crear al primer admin) como
        para restablecer una contrasena sin pasar por seed.py (que borra todo)."""
        from .models import Usuario
        with app.app_context():
            usuario = Usuario.query.filter_by(email=email.lower().strip()).first()
            if usuario:
                usuario.nombre = nombre
                usuario.rol = rol
                usuario.activo = True
                usuario.set_password(password)
                db.session.commit()
                print(f"Usuario '{email}' actualizado (rol={rol}).")
            else:
                usuario = Usuario(nombre=nombre, email=email.lower().strip(), rol=rol)
                usuario.set_password(password)
                db.session.add(usuario)
                db.session.commit()
                print(f"Usuario '{email}' creado (rol={rol}).")

    @app.cli.command("vencer-pagos")
    def vencer_pagos_cli():
        """Corre a mano el mismo job que el scheduler ejecuta a diario."""
        from .tareas_programadas import marcar_pagos_vencidos, avisar_documentos_por_vencer
        with app.app_context():
            n = marcar_pagos_vencidos()
            m = avisar_documentos_por_vencer()
        print(f"{n} pago(s) marcados como vencidos. {m} documento(s) avisados por vencer.")

    _iniciar_scheduler(app)

    return app


def _es_comando_cli_distinto_de_run():
    """create_app() corre tambien cuando se invoca `flask --app wsgi <comando>`
    (db init, crear-admin, init-db, etc.), porque esos comandos se registran
    dentro de la propia funcion — sin este chequeo, cualquier comando de
    mantenimiento arrancaria tambien el scheduler."""
    import sys
    ejecutable = os.path.basename(sys.argv[0] or "").lower()
    return ejecutable.startswith("flask") and (len(sys.argv) < 2 or sys.argv[1] != "run")


def _iniciar_scheduler(app):
    """Job diario que vence pagos de cliente atrasados. Se salta en tests, en
    comandos de mantenimiento (`flask db ...`, `flask crear-admin`, etc.) y en
    el proceso 'padre' del recargador de `flask run --debug` (si no, corre
    duplicado: uno en el padre y otro en el hijo que si sirve peticiones)."""
    if app.config.get("TESTING"):
        return
    if os.environ.get("SCHEDULER_ENABLED", "true").lower() == "false":
        return
    if _es_comando_cli_distinto_de_run():
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    from apscheduler.schedulers.background import BackgroundScheduler
    from .tareas_programadas import marcar_pagos_vencidos, avisar_documentos_por_vencer

    def _job():
        with app.app_context():
            marcar_pagos_vencidos()
            avisar_documentos_por_vencer()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_job, "cron", hour=6, minute=0, id="vencer_pagos_cliente")
    scheduler.start()
