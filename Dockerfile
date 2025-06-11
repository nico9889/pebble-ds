FROM python:3.13 AS build-deps

WORKDIR /opt/pebble-ds
RUN pip3 install uv && uv venv /opt/pebble-ds/.venv
RUN apt update && apt install libspeex-dev libspeexdsp-dev curl -y && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y

ENV PATH="/opt/pebble-ds/.venv/bin:/root/.cargo/bin:$PATH"
ENV VIRTUAL_ENV="/opt/pebble-ds/.venv"

COPY ./requirements.txt /opt/pebble-ds/requirements.txt
RUN uv pip install --no-cache-dir -r /opt/pebble-ds/requirements.txt

FROM python:3.13-slim

ARG USERNAME=dictation
ARG USER_UID=10000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# libspeex is required by pyspeex
# git is required by DeepFilterNet (for no good reasons at all)
RUN apt update && apt install libspeex-dev libspeexdsp-dev git -y

WORKDIR /opt/pebble-ds
COPY --from=build-deps /opt/pebble-ds/.venv /opt/pebble-ds/.venv
COPY ./ds /opt/pebble-ds/ds

ENV PATH="/opt/pebble-ds/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/pebble-ds/.venv"

RUN chown $USERNAME -R /opt/pebble-ds

USER $USERNAME

ENTRYPOINT ["gunicorn", "--threads", "4", "-b", "0.0.0.0:9001", "-w", "1", "ds:app"]

EXPOSE 9001