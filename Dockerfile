FROM python:3.13-slim   

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files TO disk
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN pip install channels-redis
RUN pip install whitenoise 

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Expose port Daphne will run on
EXPOSE 8000 

# Run server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "base.asgi:application"]

