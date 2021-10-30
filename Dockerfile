FROM python:3.8-slim
RUN pip install cookiecutter poetry pre-commit
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /cookie
COPY . .

WORKDIR /

CMD ["bash"]
