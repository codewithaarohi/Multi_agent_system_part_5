FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
	
	
# Copy AviationStack MCP server
COPY aviationstack-mcp ./aviationstack-mcp

# Install AviationStack MCP server
RUN pip install --no-cache-dir ./aviationstack-mcp	

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0"]