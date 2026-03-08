# Wybieramy oficjalny obraz ROS 2 Jazzy jako bazę
FROM ros:jazzy-ros-base

# Ustawienie zmiennych, aby instalator nie wymagał klikania
ENV DEBIAN_FRONTEND=noninteractive

# 1. Instalacja podstawowych narzędzi, pkg-config, rapidjson i gstreamer
RUN apt-get update && apt-get install -y \
    git wget curl build-essential cmake gnupg pkg-config \
    python3-pip python3-dev python3-venv \
    rapidjson-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalacja pymavlink (bazowe paczki, których już używałeś)
RUN pip3 install --break-system-packages pymavlink future lxml pexpect

# 3. Dodanie repozytorium Gazebo
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# 4. Instalacja Gazebo Harmonic i mostków ROS
RUN apt-get update && apt-get install -y \
    gz-harmonic \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    libgz-sim8-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 5. ArduPilot (Dzięki temu, że nic wyżej się nie zmieniło, Docker weźmie to z cache!)
RUN git clone --depth 1 https://github.com/ArduPilot/ardupilot.git && \
    cd ardupilot && \
    git submodule update --init --recursive

RUN cd ardupilot && \
    ./waf configure --board sitl && \
    ./waf sub

# 6. Wtyczka ArduPilot Gazebo (To również weźmie z cache!)
RUN git clone https://github.com/ArduPilot/ardupilot_gazebo.git && \
    cd ardupilot_gazebo && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo && \
    make -j$(nproc)

# 7. SZYBKA INSTALACJA MAVProxy NA KOŃCU (Wykorzystanie cache na maksa)
RUN pip3 install --break-system-packages MAVProxy

# 8. Ustawienie zmiennych środowiskowych (w tym ARDUPILOT_HOME dla skryptu kolegi)
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/workspace/ardupilot_gazebo/build
ENV PATH=/workspace/ardupilot/build/sitl/bin:${PATH}
ENV ARDUPILOT_HOME=/workspace/ardupilot

RUN mkdir /workspace/ardupilot/Tools/Frame_params/Sub
RUN mv /workspace/BS_oceans/scripts/bluerov2-4_0_0.params /workspace/ardupilot/Tools/Frame_params/Sub
# 9. Automatyczne ładowanie środowiska ROS 2
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Wyłączenie modułu terenu w MAVProxy (zapobiega zawieszaniu symulacji)
RUN echo "module unload terrain" > /root/.mavinit.scr

CMD ["bash"]