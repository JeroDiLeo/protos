FROM debian:12-slim
# passphrase NO de diccionario: se encuentra siguiendo pistas (HTTP + base64), no crackeando.
# la misma variable cifra la clave Y alimenta el header base64 del panel -> siempre en sync.
ARG PASSPHRASE=bloomCae2026
ENV KEY_PASSPHRASE=${PASSPHRASE}
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx openssh-server python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd \
    && ssh-keygen -A

# usuario pepito
RUN useradd -m -s /bin/bash pepito

# par de claves: privada CIFRADA con passphrase, va a /var/www/sec/mykey (web!)
RUN mkdir -p /var/www/sec /home/pepito/.ssh \
    && ssh-keygen -t rsa -b 2048 -N "$PASSPHRASE" -C "pepito@ej2" -f /tmp/mykey \
    && cp /tmp/mykey /var/www/sec/mykey \
    && cp /tmp/mykey.pub /home/pepito/.ssh/authorized_keys \
    && rm -f /tmp/mykey /tmp/mykey.pub \
    && chown -R pepito:pepito /home/pepito/.ssh \
    && chmod 700 /home/pepito/.ssh && chmod 600 /home/pepito/.ssh/authorized_keys

# contenido web + pista + flags
RUN printf '<!doctype html><title>google.com</title><pre>\n ctOS edge node (nginx)\n nada que ver aca... o si?\n pista: entra a /sec/  (el listado esta abierto)\n</pre>\n' > /var/www/index.html \
    && printf 'Dejé mi clave privada aca (mykey). Le puse passphrase, tranqui.\nLa passphrase NO esta en ningun archivo: la vas a encontrar en el\npanel de control interno (puerto 81, con Host: secrethost).\nMira los HEADERS de esa respuesta (modo verboso) y acordate de\ncomo se codifican las credenciales en Basic auth.\n            -- pepito\n' > /var/www/sec/pista.txt \
    && printf 'FLAG{ej2-ssh-login-pepito-ok}\n   Entraste por SSH con la clave expuesta por HTTP y la passphrase\n   que encontraste siguiendo las pistas. Bien ahi.\n' > /home/pepito/flag.txt \
    && chown pepito:pepito /home/pepito/flag.txt

COPY default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY control.py /opt/control.py
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 81 22
CMD ["/entrypoint.sh"]
