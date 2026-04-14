from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/api/status")
def get_status():
	return {
		"status": "online",
		"server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	}
