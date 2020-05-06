FROM python:3.7
RUN pip install --user cookiecutter
RUN pip install poetry
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /cookie
COPY . .

WORKDIR /

CMD ["bash"]
