FROM debian:12-slim
# EXTRA: variante del Ej2. La passphrase NO esta en un header: quedo sniffeada
# en una captura (Basic auth). El alumno hace Follow TCP Stream + base64.
ARG PASSPHRASE=wr3nchKey2026
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx openssh-server ca-certificates \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd && ssh-keygen -A

RUN useradd -m -s /bin/bash pepito

RUN mkdir -p /var/www/sec /home/pepito/.ssh \
    && ssh-keygen -t rsa -b 2048 -N "$PASSPHRASE" -C "pepito@ej6" -f /tmp/mykey \
    && cp /tmp/mykey /var/www/sec/mykey \
    && cp /tmp/mykey.pub /home/pepito/.ssh/authorized_keys \
    && rm -f /tmp/mykey /tmp/mykey.pub \
    && chown -R pepito:pepito /home/pepito/.ssh \
    && chmod 700 /home/pepito/.ssh && chmod 600 /home/pepito/.ssh/authorized_keys

RUN printf '<!doctype html><title>ej6</title><pre>\n ctOS edge node (nginx)\n pista: mira /sec/  (listado abierto)\n</pre>\n' > /var/www/index.html \
    && printf 'Guarde mi clave privada aca (mykey) con passphrase.\nTambien quedo una captura de red (captura.pcapng) de cuando me\nautentique contra el panel. Abrila en Wireshark, segui el TCP stream\ny fijate el header Authorization (Basic auth, esta en base64).\n            -- pepito\n' > /var/www/sec/pista.txt \
    && printf 'FLAG{ej6-pcap-basicauth-ssh-ok}\n   Sacaste la passphrase de un Basic auth sniffeado en el pcap. Crack.\n' > /home/pepito/flag.txt \
    && chown pepito:pepito /home/pepito/flag.txt

COPY captura.pcapng /var/www/sec/captura.pcapng
COPY default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 80 22
CMD ["/entrypoint.sh"]
