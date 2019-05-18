#FROM debian:stretch-slim

FROM python:3

# Install, update & upgrade packages
# Create user for the server
# This also creates the home directory we later need
# Clean TMP, apt-get cache and other stuff to make the image smaller
# Create Directory for SteamCMD
# Download SteamCMD
# Extract and delete archive
RUN set -x \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends --no-install-suggests \
		lib32stdc++6 \
		lib32gcc1 \
		wget \
		ca-certificates \
	&& useradd -m steam \
	&& su steam -c \
		"mkdir -p /home/steam/steamcmd \
		&& cd /home/steam/steamcmd \
		&& wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxf -" \
        && apt-get clean autoclean \
        && apt-get autoremove -y \
        && rm -rf /var/lib/{apt,dpkg,cache,log}/

USER steam

# Add missing library
# Run Steamcmd and install CS16
RUN until ./home/steam/steamcmd/steamcmd.sh +login anonymous \
+force_install_dir /home/steam/cs16-dedicated \
+app_update 90 -beta beta validate \
+quit; do echo "trying again"; done

RUN ./home/steam/steamcmd/steamcmd.sh +login anonymous \
+force_install_dir /home/steam/cs16-dedicated \
+app_update 70 -beta beta validate \
+quit || true;

RUN ./home/steam/steamcmd/steamcmd.sh +login anonymous \
+force_install_dir /home/steam/cs16-dedicated \
+app_update 10 -beta beta validate \
+quit || true;

RUN ./home/steam/steamcmd/steamcmd.sh +login anonymous \
+force_install_dir /home/steam/cs16-dedicated \
+app_update 90 -beta beta validate \
+app_set_config 90 mod cstrike \
+app_update 90 mod cstrike validate \
+quit
#+quit; do echo "trying again"; done

RUN { \
echo '@ShutdownOnFailedCommand 1'; \
echo '@NoPromptForPassword 1'; \
echo 'login anonymous'; \
echo 'force_install_dir /home/steam/cs16-dedicated/'; \
echo 'app_set_config 90 mod cstrike'; \
echo 'app_update 90 mod cstrike validate'; \
echo 'quit'; \
} > /home/steam/cs16-dedicated/cs16_update.txt

#RUN cd /home/steam/cs16-dedicated/cs16 && \ 
# curl https://cm2.network/cs16/cfg.tar.gz -o cfg.tar.gz && \
#tar -xf cfg.tar.gz && rm cfg.tar.gz

#ENV SRCDS_FPSMAX=300 SRCDS_TICKRATE=128 SRCDS_PORT=27015 SRCDS_TV_PORT=27020 SRCDS_MAXPLAYERS=14 SRCDS_TOKEN=0 SRCDS_RCONPW="changeme" SRCDS_PW="changeme"

#VOLUME /home/steam/cs16-dedicated

# Set Entrypoint; Technically 2 steps: 1. Update server, 2. Start server

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY *.py ./

WORKDIR /home/steam/cs16-dedicated/
COPY steam.cert ./

CMD [ "python", "/usr/src/app/run.py" ]

#ENTRYPOINT ./home/steam/steamcmd/steamcmd.sh +login anonymous +force_install_dir /home/steam/cs16-dedicated +app_set_config 90 mod cstrike +app_update 90 mod cstrike +quit && \
#cd /home/steam/cs16-dedicated/ && ./hlds_run -game cstrike -console -autoupdate -steam_dir /home/steam/steamcmd/ -steamcmd_script /home/steam/cs16-dedicated/cs16_update.txt -ip 0.0.0.0 -port 27015 +rcon_password veryhardpassword +maxplayers 8 +map de_dust +sv_rcon_maxfailures 100000000 +sv_rcon_minfailures 10000000 +sv_rcon_banpenalty 0 +sv_rcon_minfailuretime 0 -insecure -net_showpackets 1

#ENTRYPOINT ./home/steam/steamcmd/steamcmd.sh +login anonymous +force_install_dir /home/steam/cs16-dedicated +app_update 740 +quit && \
#./home/steam/cs16-dedicated/hlds_run -game cstrike -console -autoupdate -steam_dir /home/steam/steamcmd/ -steamcmd_script /home/steam/cs16-dedicated/cs16_update.txt -usercon +fps_max $SRCDS_FPSMAX -tickrate $SRCDS_TICKRATE -port $SRCDS_PORT -tv_port $SRCDS_TV_PORT -maxplayers_override $SRCDS_MAXPLAYERS +game_type 0 +game_mode 1 +mapgroup mg_active +map de_dust2 +sv_setsteamaccount $SRCDS_TOKEN +rcon_password $SRCDS_RCONPW +sv_password $SRCDS_PW +sv_region $SRCDS_REGION

# Expose ports
#EXPOSE 27015 27020 27005 51840
