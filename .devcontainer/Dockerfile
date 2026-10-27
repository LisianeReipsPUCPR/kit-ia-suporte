# Kit IA para Centros de Suporte: o computador do laboratório.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04
# Docker com o armazenamento clássico (overlay2). O padrão novo (containerd) guarda cada
# programa duas vezes, compactado e descompactado, e o disco do Codespaces não comporta.
RUN mkdir -p /etc/docker \
 && printf '{\n  "features": { "containerd-snapshotter": false }\n}\n' > /etc/docker/daemon.json
