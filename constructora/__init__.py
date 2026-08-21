from flask import Flask
from config import Config
from .extensions import db, bcrypt, csrf, login_manager, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp, url_prefix="/portal")
    app.register_blueprint(main_bp)
    app.register_blueprint(clientes_bp, url_prefix="/clientes")
    app.register_blueprint(levantamientos_bp, url_prefix="/levantamientos")
    app.register_blueprint(cotizaciones_bp, url_prefix="/cotizaciones")
    app.register_blueprint(obras_bp, url_prefix="/obras")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(trabajadores_bp, url_prefix="/trabajadores")

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

    return app
