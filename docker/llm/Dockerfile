FROM ollama/ollama:latest

# Expose Ollama port
EXPOSE 11434

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_ORIGINS=*

# Create models directory
RUN mkdir -p /models

# Volume for model persistence
VOLUME ["/root/.ollama"]

# Start Ollama server
ENTRYPOINT ["/bin/ollama"]
CMD ["serve"]
