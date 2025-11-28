FROM python:3.13-slim AS builder

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

FROM python:3.13-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/paper-fetch /usr/local/bin/paper-fetch
COPY --from=builder /usr/local/bin/paper-fetch-gui /usr/local/bin/paper-fetch-gui
COPY --from=builder /usr/local/bin/paper-fetch-mcp /usr/local/bin/paper-fetch-mcp

# Copy source code for GUI (Streamlit needs the file path)
# Actually, if installed via pip, the source is in site-packages.
# But for Streamlit run, we might need to locate the file.
# We will handle this in the entrypoint or wrapper.

ENTRYPOINT ["paper-fetch"]
CMD ["--help"]
