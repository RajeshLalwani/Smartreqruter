# worker.Dockerfile
# Minimal, secure sandbox for SmartRecruit code execution

FROM python:3.10-slim

# Create a non-root user for execution
RUN useradd -m sandboxuser

# Set working directory
WORKDIR /home/sandboxuser/app

# Disable networking for security (handled by Docker SDK during run)
# But we also set up a basic environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Change ownership to the non-root user
RUN chown -R sandboxuser:sandboxuser /home/sandboxuser/app

# Switch to the non-root user
USER sandboxuser

# Default command: Sleep indefinitely so the SDK can exec commands
# Or we can just use the SDK to run a one-off command
CMD ["python3"]
